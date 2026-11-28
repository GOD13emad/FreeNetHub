"""Historical R34 diagnostic, now verified TLS only.

The old unverified no-SNI comparison is retained in Git history, not executed.
A successful TLS result requires both a trusted certificate and matching host.
No-SNI results from older runs are not comparable to this verified-only probe.
Importing this module performs no network I/O.
"""
import json
import socket
import ssl
import time

LOCAL = "192.168.20.5"
HOSTS = ["www.youtube.com", "www.google.com", "chatgpt.com"]


def probe(host):
    row = {"host": host, "mode": "sni"}
    try:
        ips = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        ip = ips[0][4][0]
    except Exception as exc:
        return {"host": host, "resolveError": type(exc).__name__ + ": " + str(exc)}
    row["ip"] = ip
    start = time.monotonic()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw:
            raw.settimeout(4)
            raw.bind((LOCAL, 0))
            raw.connect((ip, 443))
            row["tcp"] = True
            ctx = ssl.create_default_context()
            if not ctx.check_hostname or ctx.verify_mode != ssl.CERT_REQUIRED:
                raise RuntimeError("TLS verification policy unavailable")
            with ctx.wrap_socket(raw, server_hostname=host) as conn:
                row["tlsVersion"] = conn.version()
                row["cipher"] = conn.cipher()[0]
                row["tls"] = True
    except Exception as exc:
        row["tls"] = False
        row["error"] = type(exc).__name__ + ": " + str(exc)
    row["seconds"] = round(time.monotonic() - start, 3)
    return row


if __name__ == "__main__":
    print(json.dumps([probe(host) for host in HOSTS], indent=2))
