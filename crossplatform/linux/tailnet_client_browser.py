#!/usr/bin/env python3
"""Explicit browser-scoped Tailscale CFON peer client.

No system PAC, DNS, route, VPN, or GNOME settings are ever changed.
A private Firefox profile uses a file: PAC, with no DIRECT fallback for
explicitly selected domains. The peer must be online in the current tailnet.
"""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import tempfile
import time
import urllib.parse

import freenet_hub_linux as legacy
import selective_tunnel as selective
import tailnet_cfon_gateway as gateway

PORT = gateway.PORT
PROFILE_NAME = "firefox-tailnet-r25"
PAC_NAME = "tailnet-selective.pac"
SOCKS_TIMEOUT = 4
TARGET_LIMIT = 2048


class ClientError(ValueError):
    pass


def _peer_ip(value):
    try:
        ip = ipaddress.ip_address(value)
    except (TypeError, ValueError) as exc:
        raise ClientError("TAILNET_CLIENT_INVALID_PEER_IP") from exc
    if (ip.version != 4 or ip not in ipaddress.ip_network("100.64.0.0/10")
            or isinstance(value, bool)):
        raise ClientError("TAILNET_CLIENT_PEER_NOT_PRIVATE_TAILSCALE")
    return str(ip)


def _linux_online_peer(value, ts=None):
    ip = _peer_ip(value)
    state = gateway.tailscale_status() if ts is None else ts
    if state.get("BackendState") != "Running":
        raise ClientError("TAILNET_CLIENT_TAILSCALE_NOT_RUNNING")
    self_ips = [x for x in (state.get("Self") or {}).get("TailscaleIPs", [])
                if isinstance(x, str) and x.startswith("100.")]
    if len(self_ips) != 1:
        raise ClientError("TAILNET_CLIENT_SELF_IP_UNVERIFIABLE")
    gateway.verify_peers(self_ips[0], ip, state)
    match = [entry for entry in (state.get("Peer") or {}).values()
             if isinstance(entry, dict) and entry.get("Online") is True
             and str(entry.get("OS") or "").lower() == "linux"
             and ip in (entry.get("TailscaleIPs") or [])]
    if len(match) != 1:
        raise ClientError("TAILNET_CLIENT_LINUX_PEER_IDENTITY_UNVERIFIED")
    return {"ip": ip, "name": str(match[0].get("HostName") or "Linux")[:64]}


def discover():
    """Read-only; never choose ambiguous peers or modify a saved session."""
    try:
        ts = gateway.tailscale_status()
        if ts.get("BackendState") != "Running":
            raise ClientError("TAILNET_CLIENT_TAILSCALE_NOT_RUNNING")
        peers = {}
        seen_ipv4 = set()
        for entry in (ts.get("Peer") or {}).values():
            if not isinstance(entry, dict) or entry.get("Online") is not True:
                continue
            if str(entry.get("OS") or "").lower() != "linux":
                continue
            for ip in entry.get("TailscaleIPs") or ():
                if isinstance(ip, str) and ip.startswith("100."):
                    if ip in seen_ipv4:
                        raise ClientError("TAILNET_CLIENT_DUPLICATE_PEER_IDENTITY")
                    seen_ipv4.add(ip)
                try:
                    row = _linux_online_peer(ip, ts)
                except (ClientError, gateway.TailnetError, ValueError):
                    continue
                if row["ip"] in peers:
                    raise ClientError("TAILNET_CLIENT_DUPLICATE_PEER_IDENTITY")
                peers[row["ip"]] = row
        return {"ok": True, "peers": list(peers.values()),
                "settingsChanged": False, "systemProxyChanged": False}
    except (ClientError, gateway.TailnetError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc), "settingsChanged": False}


def _domains(raw):
    try:
        if isinstance(raw, (list, tuple)):
            if not all(isinstance(item, str) for item in raw):
                raise ClientError("TAILNET_CLIENT_DOMAIN_POLICY_INVALID")
            raw = "\n".join(raw)
        return selective.parse_domains(raw)
    except (ValueError, TypeError) as exc:
        raise ClientError("TAILNET_CLIENT_DOMAIN_POLICY_INVALID") from exc


def _recv(sock, n):
    result = b""
    while len(result) < n:
        part = sock.recv(n - len(result))
        if not part:
            raise ClientError("TAILNET_CLIENT_SOCKS_REPLY_TRUNCATED")
        result += part
    return result


def _connect_check(ip, domain):
    """Unauthenticated domain-name SOCKS5 CONNECT to the exact selected host.

    Does not send cookies, paths, request headers, account tokens or credentials.
    Host DNS resolution, when needed, belongs to the remote SOCKS peer.
    """
    wire = domain.encode("ascii")
    if len(wire) > 253:
        raise ClientError("TAILNET_CLIENT_DOMAIN_TOO_LONG")
    try:
        with socket.create_connection((ip, PORT), timeout=SOCKS_TIMEOUT) as sock:
            sock.settimeout(SOCKS_TIMEOUT)
            sock.sendall(b"\x05\x01\x00")
            if _recv(sock, 2) != b"\x05\x00":
                raise ClientError("TAILNET_CLIENT_SOCKS_AUTH_REFUSED")
            sock.sendall(b"\x05\x01\x00\x03" + bytes([len(wire)]) +
                         wire + b"\x01\xbb")
            header = _recv(sock, 4)
            if header[0] != 5 or header[1] != 0 or header[2] != 0:
                raise ClientError("TAILNET_CLIENT_DOMAIN_CONNECT_REFUSED")
            if header[3] == 1:
                _recv(sock, 6)
            elif header[3] == 4:
                _recv(sock, 18)
            elif header[3] == 3:
                length = _recv(sock, 1)[0]
                _recv(sock, length + 2)
            else:
                raise ClientError("TAILNET_CLIENT_SOCKS_ATYP_INVALID")
    except (OSError, TimeoutError) as exc:
        raise ClientError("TAILNET_CLIENT_PEER_UNREACHABLE") from exc


def preflight(peer, domains, ts=None):
    try:
        row = _linux_online_peer(peer, ts)
        hosts = _domains(domains)
        _connect_check(row["ip"], hosts[0])
        return {"ok": True, "mode": "TAILNET", "peer": row,
                "probeHost": hosts[0], "domains": hosts, "scope": "BROWSER",
                "settingsChanged": False, "systemProxyChanged": False}
    except (ClientError, gateway.TailnetError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc), "mode": "TAILNET",
                "settingsChanged": False}


def pac_source(peer, domains):
    """Generate only a pinned peer SOCKS5 policy. No DIRECT selected fallback."""
    ip = _peer_ip(peer)
    names = _domains(domains)
    return (
        "// FreeNetHub R25 private Firefox-only PAC; selected domains fail closed.\n"
        "function FindProxyForURL(url, host) {\n"
        "  host = String(host).toLowerCase().replace(/\\.$/, '');\n"
        "  var domains = " + json.dumps(names, ensure_ascii=True, separators=(",", ":")) + ";\n"
        "  for (var i = 0; i < domains.length; ++i) {\n"
        "    if (host === domains[i] || dnsDomainIs(host, '.' + domains[i])) {\n"
        f"      return 'SOCKS5 {ip}:{PORT}';\n"
        "    }\n"
        "  }\n"
        "  return 'DIRECT';\n"
        "}\n"
    )


def _target(raw, names):
    url = raw or ("https://" + names[0] + "/")
    if (not isinstance(url, str) or not (1 <= len(url) <= TARGET_LIMIT)
            or any(x in url for x in ("\r", "\n", "\t", "\\", " ", '"'))):
        raise ClientError("TAILNET_CLIENT_BROWSER_URL_INVALID")
    try:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.port not in (None, 443)
                or parsed.username or parsed.password or parsed.fragment):
            raise ClientError("TAILNET_CLIENT_HTTPS_SELECTED_URL_REQUIRED")
        hostname = selective.host_from_url(url)
    except (ValueError, TypeError) as exc:
        raise ClientError("TAILNET_CLIENT_BROWSER_URL_INVALID") from exc
    if not any(hostname == x or hostname.endswith("." + x) for x in names):
        raise ClientError("TAILNET_CLIENT_BROWSER_HOST_NOT_SELECTED")
    return url


def _atomic(path, value):
    if path.exists() and (not path.is_file() or path.is_symlink()):
        raise ClientError("TAILNET_CLIENT_PROFILE_FILE_UNTRUSTED")
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _profile():
    root = legacy.firefox_profile_root()
    profile = root / PROFILE_NAME
    if profile.is_symlink() or (profile.exists() and not profile.is_dir()):
        raise ClientError("TAILNET_CLIENT_PROFILE_PATH_UNTRUSTED")
    profile.mkdir(mode=0o700, exist_ok=True)
    if profile.stat().st_uid != os.getuid():
        raise ClientError("TAILNET_CLIENT_PROFILE_NOT_OWNED")
    os.chmod(profile, 0o700)
    return profile


def _user_js(pac):
    # Firefox officially accepts a file: URL for automatic proxy configuration.
    # Hide DNS-prefetch/speculative connections from this dedicated profile.
    return "\n".join((
        'user_pref("browser.shell.checkDefaultBrowser", false);',
        'user_pref("browser.startup.homepage", "about:blank");',
        'user_pref("network.proxy.type", 2);',
        f'user_pref("network.proxy.autoconfig_url", "{pac.as_uri()}");',
        'user_pref("network.proxy.socks_remote_dns", true);',
        'user_pref("network.dns.disablePrefetch", true);',
        'user_pref("network.prefetch-next", false);',
        'user_pref("network.predictor.enabled", false);',
        'user_pref("network.http.speculative-parallel-limit", 0);',
        'user_pref("network.proxy.failover_direct", false);',
        'user_pref("datareporting.healthreport.uploadEnabled", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
        "",
    ))


def launch(peer, domains, url=None):
    # Verify before writing anything or opening a new Firefox process.
    check = preflight(peer, domains)
    if not check.get("ok"):
        return check
    names = check["domains"]
    try:
        target = _target(url, names)
        firefox = legacy.executable("firefox")
        if not firefox:
            raise ClientError("TAILNET_CLIENT_FIREFOX_MISSING")
        profile = _profile()
        if legacy.project_firefox_pids(profile):
            raise ClientError("TAILNET_CLIENT_BROWSER_PROFILE_BUSY")
        script = pac_source(check["peer"]["ip"], names)
        pac = profile / PAC_NAME
        userjs = profile / "user.js"
        for x in (pac, userjs):
            if x.is_symlink() or (x.exists() and (
                    not x.is_file() or x.stat().st_uid != os.getuid())):
                raise ClientError("TAILNET_CLIENT_EXISTING_PROFILE_FILE_UNTRUSTED")
        before = {x: x.read_text(encoding="utf-8") if x.exists() else None
                  for x in (pac, userjs)}
        uncertain_live_process = False
        try:
            _atomic(pac, script)
            _atomic(userjs, _user_js(pac))
            proc = subprocess.Popen(
                [firefox, "--no-remote", "--new-instance",
                 "--profile", str(profile), target],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True,
            )
            pids = []
            for _ in range(50):
                time.sleep(.1)
                pids = legacy.project_firefox_pids(profile)
                if pids or proc.poll() is not None:
                    break
            if not pids:
                uncertain_live_process = proc.poll() is None
                raise ClientError("TAILNET_CLIENT_BROWSER_LAUNCH_UNCERTAIN"
                                  if uncertain_live_process
                                  else "TAILNET_CLIENT_BROWSER_LAUNCH_UNVERIFIED")
        except Exception:
            # A process still running with unknown outcome MUST retain its
            # fail-closed PAC. Reverting policy under a live browser is unsafe.
            if not uncertain_live_process:
                for path, value in before.items():
                    if value is None:
                        path.unlink(missing_ok=True)
                    else:
                        _atomic(path, value)
            raise
        return {"ok": True, "mode": "TAILNET", "scope": "BROWSER_SELECTIVE",
                "profile": str(profile), "pids": pids, "peer": check["peer"],
                "domains": names, "systemProxyChanged": False,
                "networkRouteChanged": False, "browserLaunched": True}
    except (ClientError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc), "mode": "TAILNET",
                "systemProxyChanged": False}


def stop_browser():
    """Explicit stop affects only the dedicated browser profile."""
    profile = legacy.firefox_profile_root() / PROFILE_NAME
    if not profile.exists():
        return {"ok": True, "state": "already-off", "scope": "BROWSER"}
    if profile.is_symlink() or not profile.is_dir():
        return {"ok": False, "error": "TAILNET_CLIENT_PROFILE_PATH_UNTRUSTED"}
    result = legacy.stop_project_firefox(profile)
    return {"ok": bool(result.get("ok")),
            "state": ("stopped" if result.get("stopped") else "already-off")
                     if result.get("ok") else "stop-failed",
            "scope": "BROWSER", "systemProxyChanged": False}
