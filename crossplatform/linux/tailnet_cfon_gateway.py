#!/usr/bin/env python3
"""On-demand, owner-limited CFON exit over an existing Tailscale tailnet.

Nothing starts on import or login. A user must explicitly start a unit, which
binds only to this host's own Tailscale IPv4, accepts one authorized peer IPv4,
and permits SOCKS5 remote-DNS HTTPS CONNECT for configured DNS suffixes only.
It never alters default routes, DNS, browsers, Tailscale ACLs or CFON itself.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import os
import pathlib
import re
import select
import socket
import socketserver
import subprocess
import sys
import tempfile
import time

from selective_tunnel import parse_domains, DEFAULT_DOMAINS

STATE = pathlib.Path.home() / ".local" / "share" / "FreeNetHub"
OWNER = STATE / "tailnet_cfon_gateway.json"
UNIT = pathlib.Path.home() / ".config" / "systemd" / "user" / "freenethub-tailnet-cfon.service"
UNIT_NAME = UNIT.name
MARKER = "# FreeNetHub-owned, explicit-only, tailnet CFON shared egress"
PORT = 19551
UPSTREAM_PORT = 19414
TAILNET = ipaddress.ip_network("100.64.0.0/10")
LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MAX_SESSIONS = 16
MAX_LIFETIME_MINUTES = 60
MAX_IDLE_SEC = 60


class TailnetError(ValueError):
    pass


def tailnet_ip(ip):
    try:
        a = ipaddress.ip_address(ip)
        if a.version != 4 or a not in TAILNET:
            raise TailnetError("TAILNET_PRIVATE_IPV4_REQUIRED")
        return str(a)
    except (ValueError, TypeError) as exc:
        raise TailnetError("TAILNET_PRIVATE_IPV4_REQUIRED") from exc


def verify_peers(bind, peer, status):
    """Demand exact live Tailscale self/peer identities, not unauthenticated LAN."""
    bind, peer = tailnet_ip(bind), tailnet_ip(peer)
    if bind == peer:
        raise TailnetError("TAILNET_SELF_PEER_CONFLICT")
    if not isinstance(status, dict) or status.get("BackendState") != "Running":
        raise TailnetError("TAILNET_NOT_RUNNING")
    owner = status.get("Self") or {}
    if bind not in (owner.get("TailscaleIPs") or []) or owner.get("Online") is False:
        raise TailnetError("TAILNET_BIND_NOT_OWNED")
    peers = status.get("Peer") or {}
    if not any(peer in (p.get("TailscaleIPs") or []) and p.get("Online") is True
               for p in peers.values() if isinstance(p, dict)):
        raise TailnetError("TAILNET_PEER_NOT_ONLINE")
    return bind, peer


def windows_peers():
    ts = tailscale_status()
    if ts.get("BackendState") != "Running":
        raise TailnetError("TAILNET_NOT_RUNNING")
    rows = []
    for peer in (ts.get("Peer") or {}).values():
        if not isinstance(peer, dict) or peer.get("Online") is not True:
            continue
        if str(peer.get("OS") or "").lower() != "windows":
            continue
        for ip in peer.get("TailscaleIPs") or []:
            try: validated = tailnet_ip(ip)
            except TailnetError: continue
            rows.append({"ip": validated, "name": str(peer.get("HostName") or "Windows")[:64]})
    return rows


def tailscale_status():
    try:
        r = subprocess.run(["tailscale", "status", "--json"], text=True,
                           capture_output=True, timeout=8, check=True)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise TailnetError("TAILNET_STATUS_UNAVAILABLE") from exc


def _atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600 if path == OWNER else 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(raw); file.flush(); os.fsync(file.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _owned_cfon(serving=False):
    """Verify accepted owner; systemd mount isolation needs a birthtime fallback.

    Parent/start MUST verify executable via core._warpplus_owner (full /proc exe).
    ProtectSystem/PrivateTmp in user units can deny /proc/<pid>/exe readlink.
    Only the already owned unit's serving context may then rely on an exact
    same-UID PID start tick + strict owner record/path/permissions check.
    """
    import freenet_hub_linux_r37 as core
    if core.legacy.session().get("mode") != "CFON":
        raise TailnetError("FNH_CFON_SESSION_REQUIRED")
    if core._warpplus_owner("CFON") and core._port_open(UPSTREAM_PORT):
        return True
    if not serving or not core._port_open(UPSTREAM_PORT):
        raise TailnetError("FNH_CFON_OWNED_SOCKS_REQUIRED")
    recpath = core.WARPPLUS_RUNTIME / "CFON" / "owner.json"
    try:
        if not recpath.is_file() or recpath.is_symlink() or recpath.stat().st_mode & 0o077:
            raise TailnetError("FNH_CFON_OWNER_PERMISSIONS_INVALID")
        data = json.loads(recpath.read_text(encoding="utf-8"))
        if (data.get("mode") != "CFON" or int(data.get("port") or -1) != UPSTREAM_PORT
                or str(data.get("exe")) != str(core.WARPPLUS_BIN)):
            raise TailnetError("FNH_CFON_OWNER_RECORD_INVALID")
        pid = int(data["pid"])
        proc = pathlib.Path("/proc") / str(pid)
        if proc.stat().st_uid != os.getuid():
            raise TailnetError("FNH_CFON_PID_UID_MISMATCH")
        start = (proc / "stat").read_text().split()[21]
        if start != str(data["start"]):
            raise TailnetError("FNH_CFON_PID_BIRTH_CHANGED")
        try:
            live_exe = os.readlink(proc / "exe")
        except PermissionError:
            # Expected in a protected user unit; parent verified exact exe.
            pass
        else:
            if live_exe != str(core.WARPPLUS_BIN):
                raise TailnetError("FNH_CFON_EXECUTABLE_CHANGED")
        return True
    except (OSError, KeyError, ValueError, IndexError, json.JSONDecodeError) as exc:
        raise TailnetError("FNH_CFON_OWNERSHIP_NOT_PROVABLE") from exc


def _socks_ready():
    with socket.create_connection(("127.0.0.1", UPSTREAM_PORT), timeout=2) as c:
        c.settimeout(2)
        c.sendall(b"\x05\x01\x00")
        if _exact(c, 2) != b"\x05\x00":
            raise TailnetError("FNH_CFON_SOCKS_UNHEALTHY")


def _exact(sock, size):
    found = b""
    while len(found) != size:
        segment = sock.recv(size - len(found))
        if not segment:
            raise TailnetError("SOCKS_TRUNCATED")
        found += segment
    return found


def _safe_host(host, domains):
    try:
        host = host.decode("ascii").lower().rstrip(".")
    except UnicodeError as exc:
        raise TailnetError("TAILNET_HOST_NOT_DNS") from exc
    if not 0 < len(host) <= 253:
        raise TailnetError("TAILNET_HOST_INVALID")
    labels = host.split(".")
    if not 2 <= len(labels) <= 12 or any(not LABEL.fullmatch(x) for x in labels):
        raise TailnetError("TAILNET_HOST_INVALID")
    if not any(host == d or host.endswith("." + d) for d in domains):
        raise TailnetError("TAILNET_TARGET_NOT_ALLOWED")
    return host


def _reply(conn, result):
    conn.sendall(bytes([5, result, 0, 1]) + b"\x00" * 6)


def _read_request(conn, domains):
    """Answer the peer's SOCKS5 greeting, then enforce DNS:443 and allowlist."""
    if _exact(conn, 1) != b"\x05":
        raise TailnetError("TAILNET_SOCKS_VERSION")
    n = _exact(conn, 1)[0]
    if not 1 <= n <= 8:
        raise TailnetError("TAILNET_METHOD_COUNT_INVALID")
    methods = _exact(conn, n)
    if 0 not in methods:
        conn.sendall(b"\x05\xff")
        raise TailnetError("TAILNET_NOAUTH_REQUIRED")
    conn.sendall(b"\x05\x00")
    header = _exact(conn, 4)
    if header != b"\x05\x01\x00\x03":
        _reply(conn, 7)
        raise TailnetError("TAILNET_ONLY_CONNECT_REMOTE_DNS")
    n = _exact(conn, 1)[0]
    if n < 3:
        _reply(conn, 8)
        raise TailnetError("TAILNET_HOST_LENGTH")
    rawhost = _exact(conn, n)
    port = int.from_bytes(_exact(conn, 2), "big")
    if port != 443:
        _reply(conn, 2)
        raise TailnetError("TAILNET_HTTPS_ONLY")
    try:
        host = _safe_host(rawhost, domains)
    except TailnetError:
        _reply(conn, 2)
        raise
    return host.encode("ascii"), port


def _connect_owned_upstream(rawhost, port):
    c = socket.create_connection(("127.0.0.1", UPSTREAM_PORT), timeout=4)
    try:
        c.settimeout(10)
        c.sendall(b"\x05\x01\x00")
        if _exact(c, 2) != b"\x05\x00":
            raise TailnetError("TAILNET_UPSTREAM_AUTH_FAILED")
        c.sendall(b"\x05\x01\x00\x03" + bytes([len(rawhost)]) + rawhost + port.to_bytes(2, "big"))
        hdr = _exact(c, 4)
        if hdr[:1] != b"\x05" or hdr[1:3] != b"\x00\x00":
            raise TailnetError("TAILNET_UPSTREAM_UNAVAILABLE")
        if hdr[3] == 1:
            _exact(c, 4)
        elif hdr[3] == 4:
            _exact(c, 16)
        elif hdr[3] == 3:
            _exact(c, _exact(c, 1)[0])
        else:
            raise TailnetError("TAILNET_BAD_UPSTREAM_REPLY")
        _exact(c, 2)
        return c
    except Exception:
        c.close()
        raise


def exchange(conn, domains):
    remote = None
    try:
        conn.settimeout(10)
        hostname, port = _read_request(conn, domains)
        remote = _connect_owned_upstream(hostname, port)
        _reply(conn, 0)
        conn.settimeout(MAX_IDLE_SEC)
        remote.settimeout(MAX_IDLE_SEC)
        last = time.monotonic()
        while time.monotonic() - last < MAX_IDLE_SEC:
            ready, _, _ = select.select((conn, remote), (), (), 3)
            for src in ready:
                data = src.recv(32768)
                if not data:
                    return
                (remote if src is conn else conn).sendall(data)
                last = time.monotonic()
    except (OSError, TailnetError):
        if remote is None:
            try: _reply(conn, 1)
            except OSError: pass
    finally:
        try: conn.close()
        except OSError: pass
        if remote is not None: remote.close()


class _Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 4


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.server.policy()
        if self.client_address[0] != data["peer"]:
            self.request.close()
            return
        if not self.server.allow_session():
            self.request.close()
            return
        try:
            exchange(self.request, data["domains"])
        finally:
            self.server.end_session()


def _load():
    try:
        value = json.loads(OWNER.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schema") != 1:
            raise TailnetError("TAILNET_OWNER_STATE_INVALID")
        return value
    except FileNotFoundError:
        return {}


def _unit_text(bind, peer, limit_minutes):
    src = str(pathlib.Path(__file__).resolve())
    if any(c in src for c in ('"', "\r", "\n", "%", "\\")):
        raise TailnetError("TAILNET_SERVICE_PATH_UNSAFE")
    return (
        MARKER + "\n[Unit]\nDescription=FreeNetHub explicit peer-only CFON Tailnet egress\n"
        "[Service]\nType=simple\n"
        f'ExecStart=/usr/bin/python3 "{src}" serve {bind} {peer} {limit_minutes}\n'
        "Restart=no\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectSystem=full\n"
        "RestrictAddressFamilies=AF_INET AF_UNIX\n"
        f"RuntimeMaxSec={limit_minutes * 60}\n"
    )


def _port_open(ip=PORT):
    sock = socket.socket()
    sock.settimeout(0.4)
    try:
        return sock.connect_ex(ip) == 0
    finally:
        sock.close()


def status():
    record = _load()
    if not record:
        return {"ok": True, "enabled": False, "active": False}
    try:
        bind = tailnet_ip(record["bind"])
        peer = tailnet_ip(record["peer"])
        expires = float(record["expiresAt"])
    except (KeyError, ValueError, TypeError):
        return {"ok": False, "error": "TAILNET_OWNER_STATE_CORRUPT"}
    try:
        proc = subprocess.run(["systemctl", "--user", "is-active", UNIT_NAME],
                              text=True, capture_output=True, timeout=5)
        active = proc.stdout.strip() == "active"
    except (OSError, subprocess.SubprocessError):
        active = False
    up = False
    try: up = _port_open((bind, PORT))
    except OSError: pass
    return {"ok": True, "enabled": bool(record.get("enabled")), "active": active and up,
            "bind": bind, "peer": peer, "port": PORT,
            "expiresAt": expires, "expired": time.time() >= expires,
            "domains": list(record.get("domains") or [])}


def start(peer, domains=DEFAULT_DOMAINS, limit_minutes=30):
    if type(limit_minutes) is not int or not 1 <= limit_minutes <= MAX_LIFETIME_MINUTES:
        raise TailnetError("TAILNET_TTL_INVALID")
    ts = tailscale_status()
    ips = [x for x in (ts.get("Self") or {}).get("TailscaleIPs", [])
           if isinstance(x, str) and x.startswith("100.")]
    if len(ips) != 1:
        raise TailnetError("TAILNET_SELF_IPV4_AMBIGUOUS")
    bind, peer = verify_peers(ips[0], peer, ts)
    _owned_cfon()
    _socks_ready()
    names = parse_domains(domains)
    if UNIT.is_file() and MARKER not in UNIT.read_text(encoding="utf-8"):
        raise TailnetError("TAILNET_UNIT_FOREIGN")
    current = status()
    if current.get("active") or (current.get("enabled") and not current.get("expired")):
        raise TailnetError("TAILNET_PREVIOUS_GATEWAY_MUST_BE_STOPPED")
    if _port_open((bind, PORT)):
        raise TailnetError("TAILNET_PORT_ALREADY_BOUND")
    old = UNIT.read_bytes() if UNIT.exists() else None
    config = _unit_text(bind, peer, limit_minutes)
    try:
        _atomic(OWNER, json.dumps({
            "schema": 1, "enabled": True, "bind": bind, "peer": peer,
            "domains": names, "expiresAt": time.time() + limit_minutes * 60,
        }, ensure_ascii=False) + "\n")
        _atomic(UNIT, config)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=8)
        subprocess.run(["systemctl", "--user", "start", UNIT_NAME], check=True, timeout=9)
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if status().get("active"):
                return {"ok": True, "state": "active", "bind": bind, "peer": peer,
                        "port": PORT, "expiresAt": _load()["expiresAt"],
                        "domains": len(names)}
            time.sleep(.2)
        raise TailnetError("TAILNET_GATEWAY_START_UNVERIFIED")
    except Exception:
        subprocess.run(["systemctl", "--user", "stop", UNIT_NAME], timeout=6, check=False)
        if old is None: UNIT.unlink(missing_ok=True)
        else: UNIT.write_bytes(old)
        subprocess.run(["systemctl", "--user", "daemon-reload"], timeout=5, check=False)
        # Never leave a state file claiming that an unverified server is active.
        rec = _load()
        rec["enabled"] = False
        _atomic(OWNER, json.dumps(rec) + "\n")
        raise


def stop():
    data = _load()
    if not data:
        return {"ok": True, "state": "already-off"}
    if UNIT.is_file() and MARKER not in UNIT.read_text(encoding="utf-8"):
        return {"ok": False, "error": "TAILNET_UNIT_FOREIGN"}
    subprocess.run(["systemctl", "--user", "stop", UNIT_NAME], timeout=7, check=True)
    bind = tailnet_ip(data.get("bind"))
    if _port_open((bind, PORT)):
        return {"ok": False, "error": "TAILNET_LISTENER_STILL_ACTIVE"}
    data["enabled"] = False
    _atomic(OWNER, json.dumps(data, ensure_ascii=False) + "\n")
    return {"ok": True, "state": "stopped", "upstreamPreserved": True}


def serve(bind, peer, minutes):
    bind, peer = verify_peers(bind, peer, tailscale_status())
    _owned_cfon(serving=True)
    data = _load()
    if not data.get("enabled") or data.get("bind") != bind or data.get("peer") != peer:
        raise TailnetError("TAILNET_GATEWAY_NOT_OWNED")
    if not isinstance(data.get("domains"), list):
        raise TailnetError("TAILNET_DOMAIN_LIST_INVALID")
    names = parse_domains("\n".join(data["domains"]))
    deadline = min(float(data["expiresAt"]), time.time() + minutes * 60)
    import threading
    session_sem = threading.BoundedSemaphore(MAX_SESSIONS)
    with _Server((bind, PORT), _Handler) as srv:
        srv.timeout = 1
        srv.policy = lambda: {"peer": peer, "domains": names}
        srv.allow_session = lambda: session_sem.acquire(blocking=False)
        srv.end_session = session_sem.release
        while time.time() < deadline:
            try:
                _owned_cfon(serving=True)
                srv.handle_request()
            except (TailnetError, OSError):
                break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("status", "serve"))
    parser.add_argument("bind", nargs="?")
    parser.add_argument("peer", nargs="?")
    parser.add_argument("minutes", nargs="?", type=int)
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps(status(), ensure_ascii=False))
    else:
        if not all((args.bind, args.peer, args.minutes)):
            parser.error("bind, peer, minutes required")
        serve(args.bind, args.peer, args.minutes)


if __name__ == "__main__":
    main()
