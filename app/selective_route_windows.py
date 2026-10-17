#!/usr/bin/env python3
"""Opt-in WinINet/PAC-aware selective domain proxy for FreeNetHub.

User-only internet settings; no TUN, route, DNS, WinHTTP or elevated service.
Existing FreeNetHub provider ownership and HTTPS are verified by engine.py before enable.
No request is sent to the merchant or login endpoints during activation.
"""
from __future__ import annotations

import hashlib
import ipaddress
import http.server
import json
import os
import pathlib
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import importlib.util

APP = pathlib.Path(__file__).resolve().parent
_BH = importlib.util.spec_from_file_location("fnh_selective_http_bridge", APP / "selective_http_bridge.py")
if _BH is None or _BH.loader is None:
    raise ImportError("SELECTIVE_HTTP_BRIDGE_MISSING")
bridge = importlib.util.module_from_spec(_BH)
_BH.loader.exec_module(bridge)
ROOT = APP.parent
STATE = ROOT / "data" / "selective_windows"
POLICY = STATE / "policy.json"
PAC_FILE = STATE / "route.pac"
PORT = 19416
BRIDGE_PORT = 19417
URL = f"http://127.0.0.1:{PORT}/route.pac"
BRAVE_STRIPE_DOMAINS = ("brave.com", "bravesoftware.com", "stripe.com", "stripe.network")
# Explicit, audit-friendly Google ecosystem set. Do not wildcard arbitrary google.*:
# an unrelated domain could otherwise be proxied without user consent.
GOOGLE_DOMAINS = (
    'google.com',
    'googleapis.com',
    'googleusercontent.com',
    'gstatic.com',
    'googlevideo.com',
    'ggpht.com',
    'gvt1.com',
    'gvt2.com',
    'gvt3.com',
    'g.co',
    'goo.gl',
    'appspot.com',
    'firebaseapp.com',
    'firebaseio.com',
    'google.co.uk',
    'google.de',
    'google.co.in',
    'google.com.au',
    'google.ca',
    'google.fr',
    'google.co.jp',
    'google.ir',
    'youtube.com',
    'youtu.be',
    'ytimg.com',
    'youtube-nocookie.com',
    'blogspot.com',
    'blogger.com',
    'recaptcha.net',
    'doubleclick.net',
)
DEFAULT_DOMAINS = "\n".join(BRAVE_STRIPE_DOMAINS + GOOGLE_DOMAINS)
# A newly selected hostname is opt-in: PAC cannot inspect HTTP status codes
# and neither 403 nor a proxy 302 can establish account authorization.

KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
MUTATED_VALUES = ("AutoConfigURL", "ProxyEnable")
LABEL = "FNH_SELECTIVE_WINDOWS_1"
LABEL_BYTES = LABEL.encode("ascii")
DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class SelectiveError(ValueError):
    pass


def normalize_domains(value):
    if not isinstance(value, str):
        raise SelectiveError("SELECTIVE_DOMAINS_INVALID")
    rows = []
    for token in re.split(r"[\s,;]+", value.strip()):
        if not token:
            continue
        host = token.lower()
        if host.startswith("*."):
            host = host[2:]
        host = host.rstrip(".")
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise SelectiveError("SELECTIVE_DOMAIN_INVALID") from exc
        labels = host.split(".")
        if len(labels) < 2 or len(labels) > 12 or len(host) > 253 or any(
            not DOMAIN_LABEL.fullmatch(x) for x in labels
        ):
            raise SelectiveError("SELECTIVE_DOMAIN_INVALID")
        if host.endswith((".local", ".internal", ".localhost", ".invalid", ".test")):
            raise SelectiveError("SELECTIVE_LOCAL_DOMAIN_DENIED")
        if all(x.isdigit() for x in labels):
            raise SelectiveError("SELECTIVE_IP_DENIED")
        if len(labels) == 2 and labels[0] in ("co", "com", "org", "net", "gov", "ac", "edu") and len(labels[1]) == 2:
            raise SelectiveError("SELECTIVE_PUBLIC_SUFFIX_DENIED")
        if all(label.isdigit() for label in labels):
            raise SelectiveError("SELECTIVE_IP_DENIED")
        if host not in rows:
            rows.append(host)
        if len(rows) > 64:
            raise SelectiveError("SELECTIVE_DOMAIN_LIMIT")
    if not rows:
        raise SelectiveError("SELECTIVE_DOMAINS_EMPTY")
    return rows


def merge_domains(current, extra):
    """Merge explicitly selected suffixes; preserve custom entries and ordering."""
    existing = normalize_domains(current) if str(current).strip() else []
    addition = normalize_domains(extra)
    return normalize_domains("\n".join(existing + addition))


def host_from_url(text):
    """Paste a public HTTPS URL/host; never store paths, queries or login tokens."""
    if not isinstance(text, str) or not (0 < len(text.strip()) <= 2048):
        raise SelectiveError("SELECTIVE_SITE_URL_INVALID")
    text = text.strip()
    if any(ch in text for ch in ("\r", "\n", "\t", "\\", " ")):
        raise SelectiveError("SELECTIVE_SITE_URL_INVALID")
    if "://" not in text:
        text = "https://" + text
    u = urllib.parse.urlsplit(text)
    try:
        valid_port = u.port is None or u.port == 443
        host = u.hostname or ""
    except ValueError as exc:
        raise SelectiveError("SELECTIVE_SITE_URL_INVALID") from exc
    if u.scheme != "https" or not host or u.username or u.password or not valid_port:
        raise SelectiveError("SELECTIVE_SITE_HTTPS_PUBLIC_HOST_REQUIRED")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise SelectiveError("SELECTIVE_IP_TARGET_DENIED")
    return normalize_domains(host)[0]


def diagnose_403_site(text, proxy_port, proxy_host="127.0.0.1", method="CFON"):
    """Unsigned, no-cookie HEAD to the public origin only; never inspect user traffic.

    This is a diagnostic/suggestion, not transparent replay or automatic
    interception. Authentication, project permissions and path-specific 403s
    cannot be determined by this privacy-preserving origin-only request.
    """
    host = host_from_url(text)
    try:
        proxy_host = bridge.validate_proxy_host(str(method).upper(), proxy_host, proxy_port)
    except bridge.BridgeError as exc:
        raise SelectiveError(str(exc)) from exc

    def check(proxy):
        args = ["curl", "--silent", "--show-error", "--head",
                "--max-time", "8", "--max-redirs", "0",
                "--output", os.devnull, "--write-out", "%{http_code}"]
        if proxy:
            args += ["--noproxy", "", "--socks5-hostname", f"{proxy_host}:{proxy_port}"]
        else:
            args += ["--noproxy", "*"]
        args.append("https://" + host + "/")
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=11)
            status = result.stdout.strip()
            return int(status) if result.returncode == 0 and status.isdecimal() and len(status) == 3 else 0
        except (OSError, subprocess.SubprocessError):
            return 0

    direct, tunneled = check(False), check(True)
    suggested = direct == 403 and tunneled in (200, 201, 202, 204, 301, 302, 303, 307, 308)
    verdict = ("REGIONAL_403_IMPROVED" if suggested else
               "BOTH_ROUTES_FORBIDDEN" if direct == 403 and tunneled == 403 else
               "TUNNEL_FORBIDDEN" if tunneled == 403 else
               "PROBE_INCONCLUSIVE" if not direct or not tunneled else
               "NO_UNAUTHENTICATED_ORIGIN_403")
    return {"ok": True, "host": host, "directCode": direct,
            "tunnelCode": tunneled, "suggestAdd": suggested, "verdict": verdict,
            "pathTested": "/", "authenticated": False, "settingsChanged": False}


def pac(domains, proxy_port):
    if not isinstance(proxy_port, int) or not (1024 <= proxy_port <= 65535):
        raise SelectiveError("SELECTIVE_PORT_INVALID")
    domains = normalize_domains("\n".join(domains))
    return (
        "// Windows-compatible HTTPS HTTP CONNECT bridge to owned SOCKS5.\n"
        f"// Owned SOCKS5 provider port {proxy_port}.\n"
        "function FindProxyForURL(url, host) {\n"
        "  host = host.toLowerCase().replace(/\\.$/, '');\n"
        "  var allowed = " + json.dumps(domains, separators=(",", ":")) + ";\n"
        "  for (var n=0; n<allowed.length; n++) {\n"
        "    if (host === allowed[n] || dnsDomainIs(host, '.' + allowed[n])) {\n"
        f"      return 'PROXY 127.0.0.1:{BRIDGE_PORT}';\n"
        "    }\n"
        "  }\n"
        "  return 'DIRECT';\n"
        "}\n"
    )


def pac_url(source):
    return URL + "?v=" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content if isinstance(content, bytes) else content.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _load_state():
    try:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1:
            raise SelectiveError("SELECTIVE_STATE_CORRUPT")
        return data
    except FileNotFoundError:
        return {}
    except (ValueError, OSError) as exc:
        raise SelectiveError("SELECTIVE_STATE_CORRUPT") from exc


def _write_state(value):
    _atomic(POLICY, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _require_windows():
    if os.name != "nt":
        raise SelectiveError("SELECTIVE_WINDOWS_ONLY")


def _snapshot():
    _require_windows()
    import winreg

    values = {}
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_READ) as reg:
        for name in MUTATED_VALUES:
            try:
                v, kind = winreg.QueryValueEx(reg, name)
                if not isinstance(v, (int, str)):
                    raise SelectiveError("SELECTIVE_REGISTRY_VALUE_UNSUPPORTED")
                values[name] = {"present": True, "value": v, "kind": int(kind)}
            except FileNotFoundError:
                values[name] = {"present": False}
    return values


def _write_value(name, snapshot):
    _require_windows()
    import winreg

    if name not in MUTATED_VALUES:
        raise SelectiveError("SELECTIVE_REGISTRY_TARGET_UNSAFE")
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_READ | winreg.KEY_WRITE) as reg:
        if snapshot.get("present"):
            winreg.SetValueEx(reg, name, 0, int(snapshot["kind"]), snapshot["value"])
        else:
            try:
                winreg.DeleteValue(reg, name)
            except FileNotFoundError:
                pass


def _restore(values):
    if not isinstance(values, dict) or set(values) != set(MUTATED_VALUES):
        raise SelectiveError("SELECTIVE_SNAPSHOT_INVALID")
    for name in MUTATED_VALUES:
        val = values[name]
        if not isinstance(val, dict) or not isinstance(val.get("present"), bool):
            raise SelectiveError("SELECTIVE_SNAPSHOT_INVALID")
        if val["present"] and (
            type(val.get("value")) not in (str, int)
            or not isinstance(val.get("kind"), int)
        ):
            raise SelectiveError("SELECTIVE_SNAPSHOT_INVALID")
    for name in MUTATED_VALUES:
        _write_value(name, values[name])


def _notify():
    _require_windows()
    import ctypes

    wininet = ctypes.WinDLL("wininet", use_last_error=True)
    for code in (39, 37):  # INTERNET_OPTION_SETTINGS_CHANGED, INTERNET_OPTION_REFRESH
        ok = wininet.InternetSetOptionW(None, code, None, 0)
        if not ok:
            raise SelectiveError("SELECTIVE_WININET_REFRESH_UNVERIFIED")


def _health(token):
    if not token:
        return False
    addr = f"http://127.0.0.1:{PORT}/health?key=" + urllib.parse.quote(token)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(addr, timeout=2) as response:
            return response.status == 200 and response.read(64) == LABEL_BYTES
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _pac_ready(source):
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(pac_url(source), timeout=2) as response:
            return (
                response.status == 200 and
                response.headers.get("X-FreeNetHub-PAC") == "1" and
                response.read(16384) == source.encode("utf-8")
            )
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _bridge_health(token):
    if not token:
        return False
    url = f"http://127.0.0.1:{BRIDGE_PORT}/health?key=" + urllib.parse.quote(token)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=2) as response:
            return response.status == 200 and response.read(64) == bridge.HEALTH_BODY
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _start_service(token):
    if _health(token) and _bridge_health(token):
        return
    if not token:
        raise SelectiveError("SELECTIVE_TOKEN_MISSING")
    for listen_port in (PORT, BRIDGE_PORT):
        try:
            with socket.create_connection(("127.0.0.1", listen_port), timeout=0.5):
                raise SelectiveError("SELECTIVE_PORT_FOREIGN")
        except (ConnectionRefusedError, TimeoutError, OSError):
            pass
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen([sys.executable, str(pathlib.Path(__file__).resolve()), "serve"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, cwd=str(ROOT),
                     creationflags=flags, close_fds=True)
    for _ in range(40):
        if _health(token) and _bridge_health(token):
            return
        time.sleep(0.1)
    raise SelectiveError("SELECTIVE_SERVER_START_FAILED")


def _stop_service(token):
    if not _health(token):
        return not _bridge_health(token)
    url = f"http://127.0.0.1:{PORT}/shutdown?key=" + urllib.parse.quote(token)
    try:
        req = urllib.request.Request(url, method="POST", data=b"")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=2) as response:
            accepted=response.status == 200 and response.read(64) == LABEL_BYTES
        if not accepted:
            return False
        # Do not allow uninstall to race either owned PAC or CONNECT listener.
        for _ in range(30):
            if not _health(token) and not _bridge_health(token):
                return True
            time.sleep(0.1)
        return False
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _check_local_socks(port):
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise SelectiveError("SELECTIVE_PORT_INVALID")
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2) as sock:
            sock.settimeout(2)
            sock.sendall(b"\x05\x01\x00")
            if sock.recv(2) != b"\x05\x00":
                raise SelectiveError("SELECTIVE_SOCKS5_HANDSHAKE_FAILED")
    except OSError as exc:
        raise SelectiveError("SELECTIVE_SOCKS5_UNREACHABLE") from exc


def _check_tailnet_socks(host, port):
    try:
        host = bridge.validate_proxy_host("TAILNET", host, port)
        with socket.create_connection((host, port), timeout=3) as sock:
            sock.settimeout(3)
            sock.sendall(b"\x05\x01\x00")
            if sock.recv(2) != b"\x05\x00":
                raise SelectiveError("TAILNET_PEER_SOCKS5_UNAVAILABLE")
    except (OSError, bridge.BridgeError) as exc:
        raise SelectiveError("TAILNET_CFON_NOT_REACHABLE") from exc


def _active_registry(pac_url):
    # Verify ownership of *both* values the feature writes, including types.
    return {
        "AutoConfigURL": {"present": True, "value": pac_url, "kind": 1},
        "ProxyEnable": {"present": True, "value": 0, "kind": 4},
    }


def status():
    _require_windows()
    state = _load_state()
    settings = _snapshot()
    current_url = settings["AutoConfigURL"]
    actual = current_url.get("value") if current_url.get("present") else ""
    enabled = state.get("enabled") is True
    if state.get("inFlight"):
        return {
            "ok": False, "enabled": enabled, "pending": True,
            "healthy": False, "bound": False,
            "error": "SELECTIVE_PENDING_RECOVERY_REQUIRED",
        }
    bound = enabled and settings == _active_registry(state.get("pacUrl"))
    orphan = not enabled and isinstance(actual, str) and (actual == URL or actual.startswith(URL + "?v="))
    healthy = bool(bound and _health(state.get("serverToken", ""))
                   and _bridge_health(state.get("serverToken", ""))
                   and PAC_FILE.is_file() and _pac_ready(PAC_FILE.read_text(encoding="utf-8")))
    if healthy and state.get("method") == "TAILNET":
        try:
            _check_tailnet_socks(state.get("proxyHost"), state.get("proxyPort"))
        except SelectiveError:
            healthy = False
    return {
        "ok": healthy if enabled else not orphan, "enabled": enabled,
        "healthy": healthy, "bound": bound,
        "domains": state.get("domains") or [], "method": state.get("method") or "",
        "proxyPort": state.get("proxyPort"),
        "proxyHost": state.get("proxyHost", "127.0.0.1"),
        "error": ("SELECTIVE_WINDOWS_ORPHAN_PAC" if orphan else
                  "SELECTIVE_WINDOWS_PROXY_DRIFT" if enabled and not bound else
                  "SELECTIVE_WINDOWS_PAC_UNAVAILABLE" if enabled and not healthy else ""),
    }


def enable(domains, port, method, proxy_host="127.0.0.1"):
    _require_windows()
    method = str(method or "").upper()
    if method not in ("NODE", "WARP", "GOOL", "CFON", "TOR", "WEBTUNNEL", "OBFS4", "TAILNET"):
        raise SelectiveError("SELECTIVE_METHOD_NOT_SUPPORTED")
    try:
        proxy_host = bridge.validate_proxy_host(method, proxy_host, port)
    except bridge.BridgeError as exc:
        raise SelectiveError(str(exc)) from exc
    domains = normalize_domains(domains)
    source = pac(domains, port)
    url = pac_url(source)
    previous = _load_state()
    if previous.get("inFlight"):
        raise SelectiveError("SELECTIVE_PENDING_RECOVERY_REQUIRED")
    snapshot = _snapshot()
    actual = snapshot["AutoConfigURL"].get("value") if snapshot["AutoConfigURL"]["present"] else ""
    if previous.get("enabled"):
        if snapshot != _active_registry(previous.get("pacUrl")):
            raise SelectiveError("SELECTIVE_WINDOWS_PROXY_DRIFT")
        restore = previous["previous"]
        token = previous["serverToken"]
    else:
        if actual and str(actual).startswith(URL):
            raise SelectiveError("SELECTIVE_WINDOWS_FOREIGN_OR_ORPHAN_PAC")
        restore = snapshot
        token = secrets.token_hex(24)
    if (previous.get("enabled") and previous.get("domains") == domains
        and previous.get("proxyPort") == port
        and previous.get("proxyHost", "127.0.0.1") == proxy_host
        and previous.get("method") == method and status()["healthy"]):
        return {"ok": True, "state": "unchanged", "method": method, "domains": domains,
                "proxyHost": proxy_host}
    if method == "TAILNET":
        _check_tailnet_socks(proxy_host, port)
    else:
        _check_local_socks(port)
    old_pac = PAC_FILE.read_bytes() if PAC_FILE.exists() else None
    changed = False
    try:
        _atomic(PAC_FILE, source)
        # Prepare the local owner token before starting a background process.
        pending = dict(previous, schema=1, enabled=bool(previous.get("enabled")),
                       serverToken=token, previous=restore,
                       proxyHost=proxy_host, proxyPort=port, method=method,
                       pacUrl=url, inFlight=True)
        _write_state(pending)
        _start_service(token)
        if not _pac_ready(source) or not _bridge_health(token):
            raise SelectiveError("SELECTIVE_PAC_OR_CONNECT_BRIDGE_NOT_READY")
        _write_value("AutoConfigURL", {"present": True, "value": url, "kind": 1})
        changed = True
        _write_value("ProxyEnable", {"present": True, "value": 0, "kind": 4})
        _notify()
        if _snapshot() != _active_registry(url):
            raise SelectiveError("SELECTIVE_WININET_APPLY_UNVERIFIED")
        _write_state(dict(schema=1, enabled=True, domains=domains,
                          proxyPort=port, proxyHost=proxy_host,
                          method=method, pacUrl=url,
                          serverToken=token, previous=restore))
        return {"ok": True, "state": "enabled", "method": method,
                "domains": domains, "proxyPort": port, "proxyHost": proxy_host}
    except Exception:
        if changed:
            try:
                _restore(snapshot)
                _notify()
            except Exception:
                pass
        if old_pac is None:
            PAC_FILE.unlink(missing_ok=True)
        else:
            _atomic(PAC_FILE, old_pac)
        if not previous.get("enabled"):
            _stop_service(token)
        _write_state(previous if previous else {"schema": 1, "enabled": False})
        raise


def disable():
    _require_windows()
    state = _load_state()
    if not state.get("enabled") and not state.get("inFlight"):
        return {"ok": True, "state": "already-disabled"}
    active = _snapshot()
    actual = active["AutoConfigURL"].get("value") if active["AutoConfigURL"]["present"] else ""
    restore = state.get("previous")
    if state.get("inFlight") and active == restore:
        # Interrupted before the external registry write: only the owned
        # temporary server/state needs cleanup. Do not modify foreign settings.
        stopped = _stop_service(state.get("serverToken", ""))
        if not stopped:
            return {"ok": False, "error": "SELECTIVE_OWNED_SERVER_STILL_ACTIVE"}
        state["enabled"] = False
        state["inFlight"] = False
        state["previous"] = None
        _write_state(state)
        return {"ok": True, "state": "disabled", "restored": True, "serverStopped": True}
    if active != _active_registry(state.get("pacUrl")):
        return {"ok": False, "error": "SELECTIVE_WINDOWS_PROXY_DRIFT"}
    try:
        _restore(restore)
        _notify()
        if _snapshot() != restore:
            raise SelectiveError("SELECTIVE_WININET_RESTORE_UNVERIFIED")
        state["enabled"] = False
        state["inFlight"] = False
        state["previous"] = None
        _write_state(state)
        stopped = _stop_service(state.get("serverToken", ""))
        return {"ok": stopped, "state": "disabled", "restored": True,
                "serverStopped": stopped}
    except Exception as exc:
        return {"ok": False, "error": "SELECTIVE_WINDOWS_RESTORE_INCOMPLETE",
                "detail": type(exc).__name__}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Host") not in (f"127.0.0.1:{PORT}", "127.0.0.1"):
            self.send_error(404)
            return
        try:
            state = _load_state()
        except SelectiveError:
            self.send_error(503)
            return
        token = str(state.get("serverToken") or "")
        if self.path == "/health?key=" + token and token:
            body = LABEL_BYTES
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        try:
            source = PAC_FILE.read_bytes()
        except OSError:
            self.send_error(503)
            return
        if self.path != "/route.pac?v=" + hashlib.sha256(source).hexdigest()[:16]:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
        self.send_header("X-FreeNetHub-PAC", "1")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Length", str(len(source)))
        self.end_headers()
        self.wfile.write(source)

    def do_POST(self):
        token = str(_load_state().get("serverToken") or "")
        if token and self.path == "/shutdown?key=" + token:
            self.send_response(200)
            self.send_header("Content-Length", str(len(LABEL_BYTES)))
            self.end_headers()
            self.wfile.write(LABEL_BYTES)
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_error(404)

    def log_message(self, *_args):
        pass


def serve():
    _require_windows()
    bridge_listener = bridge.server(BRIDGE_PORT, _load_state)
    pac_listener = None
    bridge_started = False
    try:
        pac_listener = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
        worker = threading.Thread(target=bridge_listener.serve_forever, daemon=True)
        worker.start()
        bridge_started = True
        pac_listener.serve_forever()
    finally:
        if pac_listener is not None:
            pac_listener.server_close()
        if bridge_started:
            bridge_listener.shutdown()
        bridge_listener.server_close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("serve", "status"):
        raise SystemExit("Usage: selective_route_windows.py [serve|status]")
    if sys.argv[1] == "serve":
        serve()
    else:
        print(json.dumps(status(), ensure_ascii=False))
