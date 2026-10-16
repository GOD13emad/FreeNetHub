#!/usr/bin/env python3
"""Loopback-only, HTTPS CONNECT -> SOCKS5 domain tunnel for Windows PAC clients.

Unlike Chromium's SOCKS5 PAC extension, the ordinary PROXY directive is
understood by both Windows WinINet clients and Chromium. The bridge must never
open a DIRECT connection to a requested destination. No credential logging.
"""
from __future__ import annotations

import http.server
import ipaddress
import re
import select
import socket
import threading

HEALTH_BODY = b"FNH_SELECT_HTTP_BRIDGE_1"
MAX_CONNECTIONS = 48
HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
CLIENT_IDLE_TIMEOUT = 70
_CONNECT_LIMIT = threading.BoundedSemaphore(MAX_CONNECTIONS)


class BridgeError(Exception):
    pass


def _read_exact(sock, count):
    chunks = []
    while count:
        block = sock.recv(count)
        if not block:
            raise BridgeError("SOCKS5_UNEXPECTED_EOF")
        chunks.append(block)
        count -= len(block)
    return b"".join(chunks)


def socks5_connect(port, hostname, dest_port=443):
    """Ask the owned local SOCKS5 proxy to resolve hostname remotely."""
    if type(port) is not int or not 1024 <= port <= 65535:
        raise BridgeError("INVALID_SOCKS5_PORT")
    if type(hostname) is not str or not hostname or len(hostname) > 253:
        raise BridgeError("INVALID_SOCKS5_HOST")
    host = hostname.encode("ascii")
    if len(host) > 255 or dest_port != 443:
        raise BridgeError("INVALID_SOCKS5_TARGET")
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=8)
        sock.settimeout(16)
        sock.sendall(b"\x05\x01\x00")
        if _read_exact(sock, 2) != b"\x05\x00":
            raise BridgeError("SOCKS5_AUTH_NEGOTIATION_FAILED")
        sock.sendall(b"\x05\x01\x00\x03" + bytes([len(host)]) + host + dest_port.to_bytes(2, "big"))
        header = _read_exact(sock, 4)
        if header[0] != 5 or header[1] != 0 or header[2] != 0:
            raise BridgeError("SOCKS5_REMOTE_CONNECT_FAILED")
        if header[3] == 1:
            _read_exact(sock, 4)
        elif header[3] == 4:
            _read_exact(sock, 16)
        elif header[3] == 3:
            _read_exact(sock, _read_exact(sock, 1)[0])
        else:
            raise BridgeError("SOCKS5_INVALID_RESPONSE")
        _read_exact(sock, 2)
        return sock
    except (OSError, UnicodeError, BridgeError):
        if "sock" in locals():
            sock.close()
        raise


def normalize_connect_target(authority, allowed_domains):
    """Allow a host:443 only for exact/suffix DNS domains selected by user."""
    if type(authority) is not str or len(authority) > 270 or "/" in authority or "@" in authority:
        raise BridgeError("INVALID_CONNECT_AUTHORITY")
    if authority.count(":") != 1:
        raise BridgeError("CONNECT_HOST_AND_PORT_REQUIRED")
    host, port = authority.rsplit(":", 1)
    host = host.lower().rstrip(".")
    if port != "443" or len(host) > 253 or host.startswith(".") or host.endswith("."):
        raise BridgeError("CONNECT_HTTPS_ONLY")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise BridgeError("CONNECT_IP_LITERAL_DENIED")
    labels = host.split(".")
    if len(labels) < 2 or any(not lbl or len(lbl) > 63 for lbl in labels):
        raise BridgeError("INVALID_CONNECT_HOST")
    for label in labels:
        if not HOST_LABEL.fullmatch(label):
            raise BridgeError("INVALID_CONNECT_DNS")
    if not isinstance(allowed_domains, list) or len(allowed_domains) > 64:
        raise BridgeError("INVALID_DOMAIN_POLICY")
    if not any(host == dom or host.endswith("." + dom) for dom in allowed_domains if isinstance(dom, str)):
        raise BridgeError("CONNECT_HOST_NOT_ALLOWED")
    return host, 443


def relay_tcp(client, upstream):
    """Bounded bidirectional relay with no direct destination socket fallback."""
    client.settimeout(CLIENT_IDLE_TIMEOUT)
    upstream.settimeout(CLIENT_IDLE_TIMEOUT)
    sockets = (client, upstream)
    while True:
        readable, _, _ = select.select(sockets, (), (), CLIENT_IDLE_TIMEOUT)
        if not readable:
            return
        for sock in readable:
            data = sock.recv(32768)
            if not data:
                return
            destination = upstream if sock is client else client
            destination.sendall(data)


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FreeNetHubHTTPSBridge/1"
    sys_version = ""

    def do_GET(self):
        self.close_connection = True
        policy = self.server.read_policy()
        token = policy.get("serverToken")
        if isinstance(token, str) and token and self.path == "/health?key=" + token:
            self.send_response(200)
            self.send_header("Content-Length", str(len(HEALTH_BODY)))
            self.end_headers()
            self.wfile.write(HEALTH_BODY)
        else:
            self.send_error(405, "HTTPS CONNECT only")

    def do_CONNECT(self):
        self.close_connection = True
        if not _CONNECT_LIMIT.acquire(blocking=False):
            self.send_error(503, "Bridge busy")
            return
        upstream = None
        try:
            policy = self.server.read_policy()
            if (policy.get("enabled") is not True or policy.get("inFlight") or
                    not policy.get("serverToken")):
                raise BridgeError("BRIDGE_NOT_ACTIVE")
            host, port = normalize_connect_target(self.path, policy.get("domains"))
            upstream = socks5_connect(policy.get("proxyPort"), host, port)
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.wfile.flush()
            self.close_connection = True
            relay_tcp(self.connection, upstream)
        except (OSError, BridgeError):
            if upstream is None:
                # No reachable SOCKS5 means no direct connection, ever.
                try:
                    self.send_error(502, "Selected tunnel unavailable")
                except OSError:
                    pass
        finally:
            if upstream is not None:
                upstream.close()
            _CONNECT_LIMIT.release()

    def log_message(self, *_args):
        pass


def server(port, read_policy):
    # Port 0 requests an OS-assigned ephemeral loopback test listener.
    if type(port) is not int or (port != 0 and not 1024 <= port <= 65535):
        raise BridgeError("INVALID_BRIDGE_PORT")
    listener = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    listener.read_policy = read_policy
    return listener
