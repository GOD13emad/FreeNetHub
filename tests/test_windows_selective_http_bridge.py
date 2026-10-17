#!/usr/bin/env python3
"""Zero-credential / zero-external-network CONNECT-to-SOCKS5 bridge tests."""
import pathlib
import socket
import sys
import threading
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
import selective_http_bridge as bridge


def exact(sock, n):
    parts = []
    while n:
        b = sock.recv(n)
        if not b:
            raise RuntimeError("TEST_SOCKS_UNEXPECTED_EOF")
        parts.append(b)
        n -= len(b)
    return b"".join(parts)


class FakeSocks5:
    def __init__(self, refuse=False):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.listener.settimeout(6)
        self.port = self.listener.getsockname()[1]
        self.refuse = refuse
        self.address = None
        self.error = None
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            client, _ = self.listener.accept()
            with client:
                client.settimeout(6)
                assert exact(client, 3) == b"\x05\x01\x00"
                client.sendall(b"\x05\xff" if self.refuse else b"\x05\x00")
                if self.refuse:
                    return
                header = exact(client, 4)
                assert header == b"\x05\x01\x00\x03", header
                name = exact(client, exact(client, 1)[0]).decode("ascii")
                port = int.from_bytes(exact(client, 2), "big")
                self.address = (name, port)
                client.sendall(b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x00")
                data = client.recv(16384)
                if data:
                    client.sendall(b"UPSTREAM_ACK:" + data)
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.listener.close()

    def finish(self):
        self.thread.join(timeout=7)
        assert not self.thread.is_alive(), "fake SOCKS5 handshake timed out"
        assert self.error is None, self.error


def response(client):
    data = b""
    while b"\r\n\r\n" not in data:
        block = client.recv(4096)
        if not block:
            break
        data += block
        assert len(data) < 8192
    return data


class BridgeTests(unittest.TestCase):
    def test_tailnet_proxy_requires_explicit_mode_and_shared_private_ipv4(self):
        self.assertEqual(
            bridge.validate_proxy_host("TAILNET","100.100.42.1",19551),
            "100.100.42.1")
        self.assertEqual(
            bridge.validate_proxy_host("CFON","127.0.0.1",19414),"127.0.0.1")
        for mode, host, port in (
            ("CFON","100.100.42.1",19551),
            ("TAILNET","127.0.0.1",19551),
            ("TAILNET","8.8.8.8",19551),
            ("TAILNET","192.168.20.6",19551),
            ("TAILNET","100.100.42.1",19414),
            ("TAILNET","evil.example",19551),
            ("TAILNET","fd7a:115c:a1e0::1",19551),
        ):
            with self.subTest(mode=mode,host=host,port=port), self.assertRaises(bridge.BridgeError):
                bridge.validate_proxy_host(mode,host,port)

    def test_target_whitelist_enforces_HTTPS(self):
        allow = ["brave.com", "stripe.com"]
        self.assertEqual(bridge.normalize_connect_target("account.brave.com:443", allow),
                         ("account.brave.com", 443))
        self.assertEqual(bridge.normalize_connect_target("STRIPE.COM:443", allow),
                         ("stripe.com", 443))
        for bad in ("www.google.com:443", "evilbrave.com:443", "brave.com:80",
                    "brave.com:0", "127.0.0.1:443", "[::1]:443",
                    "brave.com:443/evil", "x@brave.com:443", "bücher.brave.com:443",
                    "brave.com:443:443"):
            with self.subTest(bad=bad), self.assertRaises(bridge.BridgeError):
                bridge.normalize_connect_target(bad, allow)

    def test_connect_uses_remote_domain_over_owned_socks_not_direct(self):
        fake = FakeSocks5()
        state = {"schema": 1, "enabled": True, "inFlight": False,
                 "domains": ["brave.com", "stripe.com"], "proxyPort": fake.port,
                 "serverToken": "test_only_owner"}
        server = bridge.server(0, lambda: state)
        host, port = server.server_address
        self.assertEqual(host, "127.0.0.1")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with socket.create_connection((host, port), timeout=6) as client:
                client.settimeout(6)
                client.sendall(b"CONNECT account.brave.com:443 HTTP/1.1\r\nHost: account.brave.com:443\r\n\r\n")
                self.assertIn(b"200 Connection Established", response(client))
                client.sendall(b"SAMPLE_TLS_PAYLOAD")
                self.assertEqual(client.recv(16384), b"UPSTREAM_ACK:SAMPLE_TLS_PAYLOAD")
            fake.finish()
            self.assertEqual(fake.address, ("account.brave.com", 443))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def test_foreign_target_and_plain_http_are_rejected(self):
        state = {"schema": 1, "enabled": True, "inFlight": False,
                 "domains": ["stripe.com"], "proxyPort": 65534,
                 "serverToken": "test_only_owner"}
        server = bridge.server(0, lambda: state)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            for url in (b"www.google.com:443", b"checkout.stripe.com:80"):
                with socket.create_connection(server.server_address, timeout=3) as client:
                    client.settimeout(4)
                    client.sendall(b"CONNECT " + url + b" HTTP/1.1\r\nHost: " + url + b"\r\n\r\n")
                    self.assertIn(b"502", response(client))
            with socket.create_connection(server.server_address, timeout=3) as client:
                client.settimeout(4)
                client.sendall(b"GET /health?key=test_only_owner HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data = response(client)
                if bridge.HEALTH_BODY not in data:
                    data += client.recv(4096)
                self.assertIn(bridge.HEALTH_BODY, data)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def test_socks_reject_is_no_direct_fallback(self):
        fake = FakeSocks5(refuse=True)
        state = {"schema": 1, "enabled": True, "inFlight": False,
                 "domains": ["brave.com"], "proxyPort": fake.port,
                 "serverToken": "test_only_owner"}
        server = bridge.server(0, lambda: state)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with socket.create_connection(server.server_address, timeout=3) as client:
                client.settimeout(5)
                client.sendall(b"CONNECT account.brave.com:443 HTTP/1.1\r\nHost: account.brave.com:443\r\n\r\n")
                self.assertIn(b"502", response(client))
            fake.finish()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
