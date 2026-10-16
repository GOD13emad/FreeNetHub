#!/usr/bin/env python3
"""User-consented, domain-selective SOCKS5 routing for proxy-aware Linux apps.

No TUN, iptables, DNS, global routing or browser profile mutation is performed.
The sole external setting is GNOME's per-user PAC URL, with ownership/rollback.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

STATE = pathlib.Path.home() / ".local" / "share" / "FreeNetHub"
DATA = STATE / "selective"
POLICY = DATA / "policy.json"
PAC_FILE = DATA / "route.pac"
SERVICE = pathlib.Path.home() / ".config" / "systemd" / "user" / "freenethub-selective-pac.service"
PORT = 19416
URL = f"http://127.0.0.1:{PORT}/route.pac"
DEFAULT_DOMAINS = "brave.com\nbravesoftware.com\nstripe.com\nstripe.network"
UNIT_MARKER = "# FreeNetHub-owned selective domain proxy PAC service"
DOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class SelectiveError(Exception):
    pass


def parse_domains(value):
    """Canonicalize only DNS suffixes, never JavaScript, IP ranges or URL paths."""
    if not isinstance(value, str):
        raise ValueError("SELECTIVE_DOMAINS_NOT_TEXT")
    parts = re.split(r"[,\s;]+", value.strip())
    result = []
    for raw in parts:
        if not raw:
            continue
        domain = raw.lower().strip()
        if domain.startswith("*."):
            domain = domain[2:]
        if domain.endswith("."):
            domain = domain[:-1]
        try:
            domain = domain.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("SELECTIVE_DOMAIN_INVALID") from exc
        labels = domain.split(".")
        if not 2 <= len(labels) <= 12 or len(domain) > 253 or any(not DOMAIN_RE.fullmatch(x) for x in labels):
            raise ValueError("SELECTIVE_DOMAIN_INVALID: " + raw[:80])
        if domain.endswith((".local", ".internal", ".localhost", ".invalid", ".test")) or domain.startswith("localhost."):
            raise ValueError("SELECTIVE_LOCAL_DOMAIN_DENIED")
        if all(x.isdigit() for x in labels):
            raise ValueError("SELECTIVE_IP_DENIED")
        # Broad public suffixes or wildcards would tunnel far more than intended.
        if len(labels) == 2 and labels[0] in ("co", "com", "org", "net", "gov", "ac", "edu") and len(labels[1]) == 2:
            raise ValueError("SELECTIVE_PUBLIC_SUFFIX_DENIED")
        if domain not in result:
            result.append(domain)
        if len(result) > 64:
            raise ValueError("SELECTIVE_DOMAIN_LIMIT")
    if not result:
        raise ValueError("SELECTIVE_DOMAINS_EMPTY")
    return result


def pac_script(domains, port):
    hosts = parse_domains("\n".join(domains))
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("SELECTIVE_PROXY_PORT_INVALID")
    return (
        "// FreeNetHub selective domain-only SOCKS5 PAC. No DIRECT fallback for selected domains.\n"
        "function FindProxyForURL(url, host) {\n"
        "  host = host.toLowerCase().replace(/\\.$/, '');\n"
        "  var domains = " + json.dumps(hosts, ensure_ascii=True, separators=(",", ":")) + ";\n"
        "  for (var i = 0; i < domains.length; i++) {\n"
        "    if (host === domains[i] || dnsDomainIs(host, '.' + domains[i])) {\n"
        f"      return 'SOCKS5 127.0.0.1:{port}';\n"
        "    }\n"
        "  }\n"
        "  return 'DIRECT';\n"
        "}\n"
    )


def _command(args, timeout=8):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)


def _setting(name):
    out = _command(["gsettings", "get", "org.gnome.system.proxy", name]).stdout.strip()
    if len(out) < 2 or out[0] != "'" or out[-1] != "'":
        raise SelectiveError("GNOME_PROXY_READ_UNSUPPORTED")
    return out[1:-1].replace("\\'", "'")


def _set_setting(name, value):
    _command(["gsettings", "set", "org.gnome.system.proxy", name, value])


def _atomic(path, value, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as f:
            f.write(value if isinstance(value, bytes) else value.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read_policy():
    try:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1:
            raise SelectiveError("SELECTIVE_STATE_CORRUPT")
        return data
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise SelectiveError("SELECTIVE_STATE_CORRUPT") from exc


def _write_policy(data):
    _atomic(POLICY, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _service_text():
    helper = str(pathlib.Path(__file__).resolve())
    # systemd service paths must be literal and cannot contain unescaped specifiers.
    if any(c in helper for c in ('"', "\n", "\r", "%", "\\")):
        raise SelectiveError("SELECTIVE_SERVICE_PATH_UNSAFE")
    return (
        f"{UNIT_MARKER}\n"
        "[Unit]\nDescription=FreeNetHub loopback selective PAC server\n"
        "[Service]\nType=simple\n"
        f'ExecStart=/usr/bin/python3 "{helper}" serve\n'
        "Restart=on-failure\nRestartSec=2\nNoNewPrivileges=yes\n"
        "PrivateTmp=yes\nProtectSystem=full\nRestrictAddressFamilies=AF_INET AF_UNIX\n"
        "[Install]\nWantedBy=default.target\n"
    )


def _service_ctl(*args):
    _command(["systemctl", "--user", *args], timeout=10)


def pac_url(content):
    # Change URL when the PAC content changes: GNOME/libproxy may cache the
    # compiled script for an unchanged URL even when no-store is advertised.
    return URL + "?v=" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _pac_online(expected):
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(pac_url(expected), timeout=2) as reply:
            return (
                reply.status == 200
                and reply.headers.get("X-FreeNetHub-PAC") == "1"
                and reply.read(32768) == expected.encode("utf-8")
            )
    except (OSError, urllib.error.URLError):
        return False


def _probe(port):
    """Verifies a real local SOCKS5 path, without submitting credentials/payment."""
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise SelectiveError("SELECTIVE_PROXY_PORT_INVALID")
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
    except OSError as exc:
        raise SelectiveError("SELECTIVE_PROXY_NOT_LISTENING") from exc
    try:
        r = _command([
            "curl", "-4", "-sS", "-L", "--max-time", "9",
            "--socks5-hostname", f"127.0.0.1:{port}", "-o", "/dev/null",
            "-w", "%{http_code}", "https://www.cloudflare.com/cdn-cgi/trace",
        ], timeout=12)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SelectiveError("SELECTIVE_PROXY_UNREACHABLE") from exc
    if r.stdout.strip() != "200":
        raise SelectiveError("SELECTIVE_PROXY_HEALTH_FAILED")


def status():
    data = _read_policy()
    enabled = bool(data.get("enabled"))
    try:
        mode, url = _setting("mode"), _setting("autoconfig-url")
    except Exception as exc:
        return {"ok": False, "enabled": enabled, "error": "GNOME_PROXY_UNAVAILABLE", "detail": type(exc).__name__}
    owned_url = str(data.get("pacUrl") or URL)
    bound = mode == "auto" and url == owned_url
    healthy = bool(enabled and bound and PAC_FILE.is_file()
                   and _pac_online(PAC_FILE.read_text(encoding="utf-8")))
    return {
        "ok": healthy if enabled else not bound,
        "enabled": enabled,
        "bound": bound,
        "healthy": healthy,
        "domains": list(data.get("domains") or []),
        "method": data.get("method"),
        "proxyPort": data.get("proxyPort"),
        "pacUrl": owned_url,
        "error": ("SELECTIVE_PROXY_SETTINGS_DRIFT" if enabled and not bound else
                  "SELECTIVE_PAC_UNAVAILABLE" if enabled and not healthy else
                  "SELECTIVE_PROXY_FOREIGN" if bound and not enabled else ""),
    }


def apply(domains, proxy_port, method):
    hosts = parse_domains(domains)
    if not isinstance(proxy_port, int):
        raise ValueError("SELECTIVE_PROXY_PORT_INVALID")
    if str(method).upper() not in ("CFON", "WARP", "GOOL", "TOR", "NODE", "CUSTOM"):
        raise ValueError("SELECTIVE_METHOD_INVALID")
    new_pac = pac_script(hosts, proxy_port)
    new_url = pac_url(new_pac)
    previous = _read_policy()
    active_url = str(previous.get("pacUrl") or URL)
    old_mode, old_url = _setting("mode"), _setting("autoconfig-url")
    # Never adopt or overwrite an existing FreeNetHub route whose ownership has
    # been lost; this is not a general-purpose system proxy reset operation.
    if previous.get("enabled"):
        if old_mode != "auto" or old_url != active_url:
            raise SelectiveError("SELECTIVE_PROXY_SETTINGS_DRIFT")
        restore = previous["previous"]
    else:
        if old_mode == "auto" and (old_url == URL or old_url.startswith(URL + "?v=")):
            raise SelectiveError("SELECTIVE_PROXY_FOREIGN")
        restore = {"mode": old_mode, "url": old_url}
    if old_mode not in ("none", "auto", "manual") or len(old_url) > 4096:
        raise SelectiveError("GNOME_PROXY_BASELINE_INVALID")
    _probe(proxy_port)  # fail before any mutation
    if previous.get("enabled") and previous.get("domains") == hosts and previous.get("proxyPort") == proxy_port and previous.get("method") == method and status()["ok"]:
        return {"ok": True, "state": "unchanged", "domains": hosts, "proxyPort": proxy_port, "method": method}

    unit = _service_text()
    if SERVICE.exists() and SERVICE.read_text(encoding="utf-8") != unit:
        raise SelectiveError("SELECTIVE_SERVICE_NOT_OWNED")
    old_pac = PAC_FILE.read_bytes() if PAC_FILE.exists() else None
    created_service = not SERVICE.exists()
    changed_proxy = False
    try:
        if created_service:
            _atomic(SERVICE, unit, 0o644)
        _atomic(PAC_FILE, new_pac)
        _service_ctl("daemon-reload")
        _service_ctl("enable", "--now", SERVICE.name)
        for _ in range(15):
            if _pac_online(new_pac):
                break
            time.sleep(0.2)
        else:
            raise SelectiveError("SELECTIVE_PAC_SERVER_NOT_READY")
        # URL first while preserving prior mode until the last write.
        _set_setting("autoconfig-url", new_url)
        changed_proxy = True
        _set_setting("mode", "auto")
        if _setting("autoconfig-url") != new_url or _setting("mode") != "auto":
            raise SelectiveError("GNOME_PROXY_APPLY_UNVERIFIED")
        data = {
            "schema": 1, "enabled": True, "domains": hosts,
            "method": str(method).upper(), "proxyPort": proxy_port,
            "previous": restore, "pacUrl": new_url,
            "pacSha256": hashlib.sha256(new_pac.encode()).hexdigest(),
        }
        _write_policy(data)
        return {"ok": True, "state": "enabled", "domains": hosts, "proxyPort": proxy_port, "method": method}
    except Exception:
        if changed_proxy and _setting("autoconfig-url") == new_url:
            try:
                _set_setting("autoconfig-url", old_url)
                _set_setting("mode", old_mode)
            except Exception:
                pass
        if old_pac is None:
            PAC_FILE.unlink(missing_ok=True)
        else:
            _atomic(PAC_FILE, old_pac)
        if not previous.get("enabled"):
            try:
                _service_ctl("disable", "--now", SERVICE.name)
            except Exception:
                pass
        if created_service:
            SERVICE.unlink(missing_ok=True)
            try:
                _service_ctl("daemon-reload")
            except Exception:
                pass
        raise


def disable():
    data = _read_policy()
    if not data.get("enabled"):
        return {"ok": True, "state": "already-disabled"}
    # Fail closed when a different application/user has changed settings.
    if _setting("mode") != "auto" or _setting("autoconfig-url") != data.get("pacUrl"):
        return {"ok": False, "error": "SELECTIVE_PROXY_SETTINGS_DRIFT"}
    old = data.get("previous") or {}
    mode, url = old.get("mode"), old.get("url")
    if mode not in ("none", "auto", "manual") or not isinstance(url, str) or len(url) > 4096:
        return {"ok": False, "error": "SELECTIVE_ROLLBACK_STATE_INVALID"}
    # Restore the prior setting first. Preserve server while it may be in use.
    try:
        _set_setting("autoconfig-url", url)
        _set_setting("mode", mode)
        if _setting("mode") != mode or _setting("autoconfig-url") != url:
            raise SelectiveError("SELECTIVE_ROLLBACK_UNVERIFIED")
        data["enabled"] = False
        data["previous"] = None
        _write_policy(data)
        _service_ctl("disable", "--now", SERVICE.name)
        return {"ok": True, "state": "disabled", "restored": True}
    except Exception as exc:
        return {"ok": False, "error": "SELECTIVE_DISABLE_PARTIAL", "detail": type(exc).__name__}


class _PACHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Host") not in (f"127.0.0.1:{PORT}", "127.0.0.1"):
            self.send_error(404)
            return
        try:
            content = PAC_FILE.read_bytes()
        except OSError:
            self.send_error(503)
            return
        if self.path != "/route.pac?v=" + hashlib.sha256(content).hexdigest()[:16]:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
        self.send_header("X-FreeNetHub-PAC", "1")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args):
        pass


def serve():
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), _PACHandler).serve_forever()


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "serve":
        serve()
    elif len(sys.argv) == 2 and sys.argv[1] == "status":
        print(json.dumps(status(), ensure_ascii=False))
    else:
        raise SystemExit("Usage: selective_tunnel.py {serve|status}")
