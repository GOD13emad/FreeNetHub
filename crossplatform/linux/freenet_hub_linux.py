#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import secrets
import shutil
import signal
import socket
import string
import subprocess
import time
import uuid
import zipfile

APP = "FreeNet Hub"
VERSION = "4.2.0-linux.8"
STATE = pathlib.Path.home() / ".local" / "share" / "FreeNetHub"
EVIDENCE = STATE / "evidence"
TOR_STATE = STATE / "tor"
TOR_OWNER = TOR_STATE / "owner.json"
TOR_LAST_MODE = TOR_STATE / "last_mode.txt"
BRIDGES = STATE / "bridges_obfs4.txt"
SNOWFLAKE_BRIDGES = STATE / "bridges_snowflake.txt"
SESSION = STATE / "session.json"
CONSOLE = STATE / "console.json"
SOCKS_PORT = 9909
TOR_DIRECT_TIMEOUT = 90
TOR_AUTO_DIRECT_TIMEOUT = 30
TOR_TRANSPORT_TIMEOUT = 120
CONSOLE_WIFI_PROTO = "rsn"
CONSOLE_WIFI_PMF = "disable"
WARP_GUARD_SECONDS = 60
CONSOLE_NAME = "FreeNetHub-Console"

def ensure_dirs():
    for p in (STATE, EVIDENCE, TOR_STATE):
        p.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(p, 0o700)
        except OSError:
            pass

def executable(name: str):
    p = shutil.which(name)
    if p:
        return p
    q = STATE / "runtime" / "usr" / "bin" / name
    return str(q) if q.exists() else None

def exists(name: str):
    return executable(name) is not None

def run(args, timeout=20, env=None):
    try:
        return subprocess.run(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return subprocess.CompletedProcess(args, 124, out, err + "\nTIMEOUT")

def atomic_json(path: pathlib.Path, value):
    ensure_dirs()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    os.chmod(path, 0o600)

def load_json(path: pathlib.Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default

def set_session(mode=None, provider=None, detail=None):
    data = {
        "mode": mode,
        "provider": provider,
        "detail": detail or {},
        "updated": time.time(),
    }
    atomic_json(SESSION, data)
    return data

def session():
    return load_json(SESSION, {"mode": None, "provider": None, "detail": {}, "updated": None})

def trace(proxy=None, timeout=15):
    curl = executable("curl")
    if not curl:
        return {"ok": False, "error": "curl missing"}
    args = [curl, "-4", "--max-time", str(timeout), "-fsS"]
    if proxy:
        args += ["--proxy", proxy]
    args += ["https://www.cloudflare.com/cdn-cgi/trace"]
    p = run(args, timeout + 3)
    if p.returncode:
        return {"ok": False, "error": (p.stderr or p.stdout).strip(), "returncode": p.returncode}
    d = {}
    for line in p.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k] = v
    return {"ok": True, "trace": d}

def identity(pid: int):
    try:
        proc = pathlib.Path(f"/proc/{pid}")
        return {
            "pid": pid,
            "exe": os.readlink(proc / "exe"),
            "start": (proc / "stat").read_text().split()[21],
        }
    except Exception:
        return None

def tor_owner():
    try:
        rec = json.loads(TOR_OWNER.read_text(encoding="utf-8"))
        cur = identity(int(rec["pid"]))
        if cur and all(str(cur[k]) == str(rec[k]) for k in ("pid", "exe", "start")):
            return rec
    except Exception:
        pass
    return None

def stop_pid(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except Exception:
        return False
    for _ in range(50):
        if identity(pid) is None:
            return True
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except Exception:
        pass
    for _ in range(20):
        if identity(pid) is None:
            return True
        time.sleep(0.05)
    return identity(pid) is None

def listener_pid(port: int):
    ss = executable("ss")
    if not ss:
        return None
    try:
        p = run([ss, "-ltnp", f"sport = :{port}"], 5)
        m = re.search(r"pid=(\d+)", (p.stdout or "") + (p.stderr or ""))
        return int(m.group(1)) if m else None
    except Exception:
        return None

def recover_stale_project_listener():
    pid = listener_pid(SOCKS_PORT)
    if not pid:
        return {"ok": True, "state": "free"}
    rec = tor_owner()
    if rec and int(rec.get("pid", 0)) == pid:
        return {"ok": False, "error": "project Tor already running", "pid": pid, "owned": True}
    try:
        ident = identity(pid)
        cmd = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        tor = executable("tor")
        trusted = bool(ident and tor and pathlib.Path(ident["exe"]).resolve() == pathlib.Path(tor).resolve())
        local_cfg = str(TOR_STATE.resolve()) in cmd and "torrc-" in cmd
        if trusted and local_cfg:
            stopped = stop_pid(pid)
            try:
                TOR_OWNER.unlink(missing_ok=True)
            except Exception:
                pass
            return {"ok": bool(stopped), "state": "recovered-stale-project-listener" if stopped else "recovery-failed", "pid": pid}
    except Exception:
        pass
    return {"ok": False, "error": "SOCKS port occupied by foreign or unproven process", "pid": pid}

def bridge_lines(path=BRIDGES):
    try:
        return [
            x.strip()
            for x in path.read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.lstrip().startswith("#")
        ]
    except Exception:
        return []

def normalize_snowflake_bridge(line: str):
    parts = line.split()
    out = []
    for token in parts:
        if token.startswith("front="):
            value = token.split("=", 1)[1]
            if "," in value:
                token = "front=" + value.split(",", 1)[0]
        out.append(token)
    return " ".join(out)

def bootstrap_percent(log_path: pathlib.Path):
    try:
        pct = 0
        for line in log_path.read_text(errors="replace").splitlines():
            if "Bootstrapped " in line:
                s = line.split("Bootstrapped ", 1)[1].split("%", 1)[0]
                if s.isdigit():
                    pct = max(pct, int(s))
        return pct
    except Exception:
        return 0

def launch_tor(mode: str, timeout: float):
    ensure_dirs()
    tor = executable("tor")
    if not tor:
        return {"ok": False, "mode": mode, "error": "tor executable missing"}
    guard = recover_stale_project_listener()
    if not guard.get("ok"):
        return {"ok": False, "mode": mode, "error": guard.get("error", "SOCKS port unavailable"), "listener": guard}
    data = TOR_STATE / f"data-{mode}"
    data.mkdir(exist_ok=True)
    log_path = TOR_STATE / f"tor-{mode}.log"
    torrc = TOR_STATE / f"torrc-{mode}"
    lines = [
        f"SocksPort 127.0.0.1:{SOCKS_PORT}",
        f"DataDirectory {data}",
        "AvoidDiskWrites 1",
    ]
    if mode == "obfs4":
        obfs = executable("obfs4proxy")
        bridges = bridge_lines(BRIDGES)
        if not obfs:
            return {"ok": False, "mode": mode, "error": "obfs4proxy missing"}
        if not bridges:
            return {"ok": False, "mode": mode, "error": "no obfs4 bridges configured"}
        lines += ["UseBridges 1", f"ClientTransportPlugin obfs4 exec {obfs}"]
        lines += [f"Bridge {b}" for b in bridges]
    elif mode == "snowflake":
        snow = executable("snowflake-client")
        bridges = [normalize_snowflake_bridge(b) for b in bridge_lines(SNOWFLAKE_BRIDGES)]
        if not snow:
            return {"ok": False, "mode": mode, "error": "snowflake-client missing"}
        if not bridges:
            return {"ok": False, "mode": mode, "error": "no snowflake bridges configured"}
        lines += ["UseBridges 1", f"ClientTransportPlugin snowflake exec {snow}"]
        lines += [f"Bridge {b}" for b in bridges]
    torrc.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log = open(log_path, "wb", buffering=0)
    p = subprocess.Popen(
        [tor, "-f", str(torrc)],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,
        close_fds=True,
    )
    deadline = time.time() + timeout
    pct = 0
    while time.time() < deadline:
        if p.poll() is not None:
            log.close()
            return {"ok": False, "mode": mode, "error": "tor exited during startup", "bootstrap": pct}
        pct = bootstrap_percent(log_path)
        if pct >= 100:
            ident = identity(p.pid)
            if ident:
                atomic_json(TOR_OWNER, ident | {"started": time.time(), "mode": mode, "bootstrap": 100})
                TOR_LAST_MODE.write_text(mode, encoding="utf-8")
            log.close()
            return {
                "ok": True,
                "state": "running",
                "mode": mode,
                "bootstrap": 100,
                "proxy": f"socks5h://127.0.0.1:{SOCKS_PORT}",
            }
        time.sleep(0.25)
    stop_pid(p.pid)
    log.close()
    return {"ok": False, "mode": mode, "error": "bootstrap timeout", "bootstrap": pct}

def tor_status():
    rec = tor_owner()
    if not rec:
        return {"ok": True, "state": "stopped", "proxy": f"socks5h://127.0.0.1:{SOCKS_PORT}"}
    t = trace(f"socks5h://127.0.0.1:{SOCKS_PORT}", 12)
    return {
        "ok": bool(t.get("ok")),
        "state": "running",
        "mode": rec.get("mode"),
        "pid": rec.get("pid"),
        "bootstrap": rec.get("bootstrap"),
        "egress": t,
    }

def start_tor(force_mode=None):
    rec = tor_owner()
    if rec:
        t = trace(f"socks5h://127.0.0.1:{SOCKS_PORT}", 12)
        if t.get("ok"):
            set_session("TOR", rec.get("mode"), {"proxy": f"socks5h://127.0.0.1:{SOCKS_PORT}"})
            return {
                "ok": True,
                "state": "already-running",
                "mode": rec.get("mode"),
                "proxy": f"socks5h://127.0.0.1:{SOCKS_PORT}",
                "egress": t,
            }
        stop_tor()
    if force_mode in ("direct", "obfs4", "snowflake"):
        modes = [force_mode]
    else:
        preferred = ""
        try:
            preferred = TOR_LAST_MODE.read_text().strip()
        except Exception:
            pass
        available = ["direct", "obfs4"]
        if bridge_lines(SNOWFLAKE_BRIDGES) and exists("snowflake-client"):
            available.insert(0, "snowflake")
        modes = ([preferred] + [m for m in available if m != preferred]) if preferred in available else available
    attempts = []
    for mode in modes:
        if mode == "direct":
            timeout = TOR_DIRECT_TIMEOUT if force_mode == "direct" else TOR_AUTO_DIRECT_TIMEOUT
        else:
            timeout = TOR_TRANSPORT_TIMEOUT
        x = launch_tor(mode, timeout)
        attempts.append({k: v for k, v in x.items() if k != "log_tail"})
        if x.get("ok"):
            t = trace(x["proxy"], 20)
            if t.get("ok"):
                x["egress"] = t
                x["attempts"] = attempts
                set_session("TOR", mode, {"proxy": x["proxy"]})
                return x
            rec = tor_owner()
            if rec:
                stop_pid(int(rec["pid"]))
            try:
                TOR_OWNER.unlink(missing_ok=True)
            except Exception:
                pass
            attempts[-1]["egress_error"] = t.get("error", "egress failed")
    return {"ok": False, "state": "failed", "attempts": attempts}

def stop_tor():
    rec = tor_owner()
    if not rec:
        return {"ok": True, "state": "not-owned"}
    stopped = stop_pid(int(rec["pid"]))
    if stopped:
        try:
            TOR_OWNER.unlink(missing_ok=True)
        except Exception:
            pass
        s = session()
        if s.get("mode") == "TOR":
            set_session()
    return {"ok": stopped, "state": "stopped" if stopped else "stop-timeout", "mode": rec.get("mode")}

def warp_status():
    cli = executable("warp-cli")
    if not cli:
        return {"ok": False, "error": "warp-cli missing"}
    p = run([cli, "--accept-tos", "status"], 12)
    text = (p.stdout + p.stderr).strip()
    return {
        "ok": p.returncode == 0,
        "text": text,
        "connected": "Connected" in text and "Disconnected" not in text,
        "returncode": p.returncode,
    }

def ensure_warp_registration():
    cli = executable("warp-cli")
    if not cli:
        return {"ok": False, "error": "warp-cli missing"}
    p = run([cli, "--accept-tos", "registration", "show"], 12)
    if p.returncode == 0:
        return {"ok": True, "state": "existing"}
    p = run([cli, "--accept-tos", "registration", "new"], 30)
    if p.returncode:
        return {
            "ok": False,
            "error": "registration failed or timed out",
            "detail": (p.stdout + p.stderr).strip(),
            "returncode": p.returncode,
        }
    return {"ok": True, "state": "created"}

def start_warp_guard():
    ensure_dirs()
    guard = STATE / "warp_guard.py"
    if not guard.exists():
        return {"ok": False, "error": "warp guard missing"}
    token = uuid.uuid4().hex
    keep = STATE / f"warp_keep_{token}.ok"
    log = STATE / f"warp_guard_{token}.log"
    subprocess.Popen(
        [executable("python3") or "python3", str(guard), token, str(WARP_GUARD_SECONDS), str(keep), str(log)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {"ok": True, "token": token, "keep": str(keep), "log": str(log), "seconds": WARP_GUARD_SECONDS}

def warp_connect_safe():
    cli = executable("warp-cli")
    if not cli:
        return {"ok": False, "error": "warp-cli missing"}
    current = warp_status()
    if current.get("connected"):
        t = trace(timeout=10)
        if t.get("ok") and (t.get("trace") or {}).get("warp") == "on":
            set_session("WARP_EXTERNAL", "system", {"owned": False})
            return {"ok": True, "state": "already-connected-external", "warp": "on", "trace": t, "needs_keep": False, "owned": False}
    reg = ensure_warp_registration()
    if not reg.get("ok"):
        return {"ok": False, "stage": "registration", "registration": reg}
    guard = start_warp_guard()
    if not guard.get("ok"):
        return {"ok": False, "stage": "guard", "error": guard.get("error")}
    p = run([cli, "--accept-tos", "connect"], 20)
    if p.returncode:
        return {"ok": False, "stage": "connect", "error": (p.stdout + p.stderr).strip(), "guard": guard}
    last = {}
    for _ in range(15):
        time.sleep(1)
        last = trace(timeout=8)
        if last.get("ok") and (last.get("trace") or {}).get("warp") == "on":
            set_session("WARP_TRIAL", "system", {"guard_token": guard["token"]})
            return {
                "ok": True,
                "state": "trial-connected",
                "warp": "on",
                "trace": last,
                "guard": guard,
                "needs_keep": True,
            }
    return {
        "ok": False,
        "stage": "e2e",
        "error": "trace did not show warp=on; guard will auto-disconnect",
        "trace": last,
        "guard": guard,
    }

def warp_keep(token: str):
    t = trace(timeout=10)
    if not (t.get("ok") and (t.get("trace") or {}).get("warp") == "on"):
        return {"ok": False, "error": "WARP is not end-to-end connected", "trace": t}
    keep = STATE / f"warp_keep_{token}.ok"
    keep.write_text("confirmed\n", encoding="utf-8")
    set_session("WARP", "system", {"guard_token": token})
    return {"ok": True, "state": "persistent", "warp": "on", "trace": t, "token": token}

def warp_disconnect():
    cli = executable("warp-cli")
    if not cli:
        return {"ok": False, "error": "warp-cli missing"}
    current = session()
    token = (current.get("detail") or {}).get("guard_token") if current.get("mode") == "WARP_TRIAL" else None
    if token:
        try:
            (STATE / f"warp_keep_{token}.ok").write_text("cancelled-after-manual-disconnect\n", encoding="utf-8")
        except Exception:
            pass
    p = run([cli, "--accept-tos", "disconnect"], 20)
    last = {}
    for _ in range(10):
        time.sleep(0.5)
        last = trace(timeout=8)
        if last.get("ok") and (last.get("trace") or {}).get("warp") != "on":
            set_session()
            return {"ok": True, "state": "disconnected", "trace": last, "text": (p.stdout + p.stderr).strip()}
    return {"ok": False, "state": "disconnect-unverified", "trace": last, "text": (p.stdout + p.stderr).strip()}

def current_status():
    s = session()
    mode = s.get("mode")
    if mode in ("WARP", "WARP_TRIAL", "WARP_EXTERNAL"):
        w = warp_status()
        t = trace(timeout=10)
        return {
            "ok": bool(w.get("connected") and t.get("ok") and (t.get("trace") or {}).get("warp") == "on"),
            "mode": mode,
            "provider": "WARP",
            "scope": "SYSTEM",
            "status": w,
            "trace": t,
        }
    if mode == "TOR":
        t = tor_status()
        return {"ok": bool(t.get("ok")), "mode": mode, "provider": "TOR", "scope": "BROWSER", "tor": t}
    if mode == "DIRECT":
        t = trace(timeout=10)
        return {"ok": bool(t.get("ok")), "mode": mode, "provider": "DIRECT", "scope": "BROWSER", "trace": t}
    return {
        "ok": True,
        "mode": None,
        "provider": None,
        "warp": warp_status(),
        "tor": tor_status(),
        "trace": trace(timeout=8),
    }

def _disconnect_owned_system_warp():
    current = session()
    if current.get("mode") in ("WARP", "WARP_TRIAL"):
        w = warp_status()
        if w.get("connected"):
            return warp_disconnect()
        set_session()
    return {"ok": True, "state": "no-owned-system-warp"}


def disable_full_system():
    """Turn off only FreeNet Hub-owned system WARP; never stop external WARP."""
    return _disconnect_owned_system_warp()


def connect_mode(mode: str, full_system: bool = False):
    mode = (mode or "AUTO").upper()

    if full_system:
        if mode not in ("AUTO", "WARP"):
            return {
                "ok": False,
                "error": "FULL_SYSTEM_WARP_ONLY",
                "selected": mode,
                "scope": "SYSTEM",
            }
        stop_tor()
        r = warp_connect_safe()
        r["selected"] = "WARP"
        r["scope"] = "SYSTEM"
        return r

    # Browser-only scope is the safe default. Never start system WARP here.
    _disconnect_owned_system_warp()

    if mode == "DIRECT":
        stop_tor()
        t = trace()
        if t.get("ok"):
            set_session("DIRECT", "direct", {"scope": "BROWSER"})
        return {"ok": bool(t.get("ok")), "mode": "DIRECT", "scope": "BROWSER", "trace": t}

    if mode == "WARP":
        return {
            "ok": False,
            "error": "WARP_BROWSER_ONLY_UNAVAILABLE",
            "selected": "WARP",
            "scope": "BROWSER",
            "detail": (
                "Cloudflare WARP Local Proxy did not establish a usable local proxy on this network. "
                "Use AUTO/Tor/obfs4/Snowflake for browser-only, or enable Full System for WARP."
            ),
        }

    if mode == "TOR":
        r = start_tor("direct")
        r["selected"] = "TOR"
        r["scope"] = "BROWSER"
        return r

    if mode == "OBFS4":
        r = start_tor("obfs4")
        r["selected"] = "OBFS4"
        r["scope"] = "BROWSER"
        return r

    if mode == "SNOWFLAKE":
        r = start_tor("snowflake")
        r["selected"] = "SNOWFLAKE"
        r["scope"] = "BROWSER"
        return r

    if mode == "AUTO":
        t = start_tor()
        t["selected"] = "TOR"
        t["scope"] = "BROWSER"
        t["attempts"] = [{"provider": "TOR", "ok": t.get("ok"), "mode": t.get("mode")}]
        return t

    return {"ok": False, "error": f"unsupported mode: {mode}", "scope": "BROWSER"}

def stop_all():
    current = session()
    results = {"tor": stop_tor()}
    w = warp_status()
    if w.get("connected") and current.get("mode") in ("WARP", "WARP_TRIAL"):
        results["warp"] = warp_disconnect()
    elif w.get("connected"):
        results["warp"] = {"ok": True, "state": "left-connected-not-owned"}
    else:
        results["warp"] = {"ok": True, "state": "already-disconnected"}
    set_session()
    return {"ok": all(bool(v.get("ok")) for v in results.values()), "results": results}

def verify_current():
    return current_status()

def firefox_profile_root():
    snap_common = pathlib.Path.home() / "snap" / "firefox" / "common"
    if snap_common.is_dir() and pathlib.Path("/snap/firefox/current").exists():
        root = snap_common / "FreeNetHub"
    else:
        root = STATE
    root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass
    return root


def firefox_profile(proxy=False):
    base = firefox_profile_root() / "firefox-tunneled"
    base.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(base, 0o700)
    except OSError:
        pass
    prefs = [
        'user_pref("browser.shell.checkDefaultBrowser", false);',
        'user_pref("browser.startup.homepage", "about:blank");',
        'user_pref("datareporting.healthreport.uploadEnabled", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
    ]
    if proxy:
        prefs += [
            'user_pref("network.proxy.type", 1);',
            'user_pref("network.proxy.socks", "127.0.0.1");',
            f'user_pref("network.proxy.socks_port", {SOCKS_PORT});',
            'user_pref("network.proxy.socks_version", 5);',
            'user_pref("network.proxy.socks_remote_dns", true);',
            'user_pref("network.proxy.no_proxies_on", "localhost, 127.0.0.1");',
        ]
    else:
        prefs += ['user_pref("network.proxy.type", 0);']
    user_js = base / "user.js"
    user_js.write_text("\n".join(prefs) + "\n", encoding="utf-8")
    try:
        os.chmod(user_js, 0o600)
    except OSError:
        pass
    return base


def project_firefox_pids(profile):
    want = str(pathlib.Path(profile))
    rows = []
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            args = [x.decode(errors="replace") for x in (p / "cmdline").read_bytes().split(b"\0") if x]
        except Exception:
            continue
        if not args:
            continue
        if want in args and pathlib.Path(args[0]).name == "firefox":
            rows.append(int(p.name))
    return rows


def process_live(pid):
    stat = pathlib.Path(f"/proc/{int(pid)}/stat")
    if not stat.exists():
        return False
    try:
        parts = stat.read_text(encoding="utf-8", errors="replace").split()
        return len(parts) > 2 and parts[2] != "Z"
    except Exception:
        return False


def stop_project_firefox(profile):
    pids = project_firefox_pids(profile)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    end = time.time() + 5
    while time.time() < end:
        alive = [pid for pid in pids if process_live(pid)]
        if not alive:
            return {"ok": True, "stopped": pids, "forced": []}
        time.sleep(0.15)
    alive = [pid for pid in pids if process_live(pid)]
    forced = []
    for pid in alive:
        try:
            os.kill(pid, signal.SIGKILL)
            forced.append(pid)
        except (ProcessLookupError, PermissionError):
            pass
    end = time.time() + 2
    while time.time() < end:
        still = [pid for pid in alive if process_live(pid)]
        if not still:
            return {"ok": True, "stopped": pids, "forced": forced}
        time.sleep(0.1)
    still = [pid for pid in alive if process_live(pid)]
    return {"ok": not still, "stopped": [pid for pid in pids if pid not in still], "forced": forced, "busy": still}


def open_browser(url="https://www.cloudflare.com/cdn-cgi/trace"):
    firefox = executable("firefox")
    if not firefox:
        return {"ok": False, "error": "firefox missing"}
    s = session()
    mode = s.get("mode")
    if not mode:
        return {"ok": False, "error": "CONNECT_FIRST"}
    proxy = mode == "TOR"
    if proxy:
        ts = tor_status()
        if not ts.get("ok"):
            return {"ok": False, "error": "TOR_NOT_READY", "tor": ts}
    if mode in ("WARP", "WARP_TRIAL", "WARP_EXTERNAL"):
        tr = trace(timeout=10)
        if not (tr.get("ok") and (tr.get("trace") or {}).get("warp") == "on"):
            return {"ok": False, "error": "WARP_NOT_READY", "trace": tr}
    prof = firefox_profile(proxy=proxy)
    legacy = STATE / "firefox-tunneled"
    if legacy != prof:
        old = stop_project_firefox(legacy)
        if not old.get("ok"):
            return {"ok": False, "error": "LEGACY_BROWSER_BUSY", "pids": old.get("busy", [])}
    stopped = stop_project_firefox(prof)
    if not stopped.get("ok"):
        return {"ok": False, "error": "BROWSER_BUSY_CLOSE_REQUIRED", "pids": stopped.get("busy", [])}
    env = os.environ.copy()
    subprocess.Popen(
        [firefox, "--no-remote", "--new-instance", "--profile", str(prof), url],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    atomic_json(STATE / "browser_route.json", {"schema": 1, "mode": mode, "scope": "SYSTEM" if mode in ("WARP", "WARP_TRIAL", "WARP_EXTERNAL") else "BROWSER", "proxy": proxy, "profile": str(prof), "launched": time.time()})
    return {"ok": True, "browser": "firefox", "profile": str(prof), "mode": mode, "proxy": proxy, "restarted": bool(stopped.get("stopped"))}

def default_route():
    p = run([executable("ip") or "ip", "route", "show", "default"], 5)
    return (p.stdout + p.stderr).strip()

def interfaces():
    p = run([executable("ip") or "ip", "-br", "link"], 5)
    return p.stdout.strip().splitlines()

def inventory():
    ensure_dirs()
    versions = {}
    for name, args in {
        "warp": [executable("warp-cli") or "warp-cli", "--version"],
        "tor": [executable("tor") or "tor", "--version"],
        "obfs4proxy": [executable("obfs4proxy") or "obfs4proxy", "-version"],
        "snowflake": [executable("snowflake-client") or "snowflake-client", "-version"],
        "python": [executable("python3") or "python3", "--version"],
    }.items():
        if executable(args[0]) or pathlib.Path(args[0]).exists():
            p = run(args, 8)
            versions[name] = (p.stdout + p.stderr).strip().splitlines()[:2]
        else:
            versions[name] = ["missing"]
    return {
        "ok": True,
        "version": VERSION,
        "session": session(),
        "versions": versions,
        "default_route": default_route(),
        "interfaces": interfaces(),
        "warp": warp_status(),
        "tor": tor_status(),
        "bridges": len(bridge_lines(BRIDGES)),
        "snowflake_bridges": len(bridge_lines(SNOWFLAKE_BRIDGES)),
        "remote_commander": run(["systemctl", "--user", "is-active", "chatgpt-remote-commander.service"], 5).stdout.strip(),
    }

def doctor():
    direct = trace(timeout=12)
    dns = run(["getent", "ahosts", "www.google.com"], 8)
    youtube = run([executable("curl") or "curl", "-4", "--max-time", "12", "-L", "-o", "/dev/null", "-sS", "-w", "%{http_code}", "https://www.youtube.com/generate_204"], 15)
    return {
        "ok": bool(direct.get("ok") and dns.returncode == 0),
        "direct": direct,
        "dns_ok": dns.returncode == 0,
        "dns_sample": dns.stdout.splitlines()[:4],
        "youtube_http": youtube.stdout.strip(),
        "youtube_reachable": youtube.returncode == 0 and youtube.stdout.strip() in ("200", "204"),
        "default_route": default_route(),
    }

def speed_sample():
    curl = executable("curl")
    if not curl:
        return {"ok": False, "error": "curl missing"}
    s = session()
    if not s.get("mode"):
        return {"ok": False, "error": "CONNECT_FIRST"}
    args = [curl, "-4", "--max-time", "30", "-L", "-o", "/dev/null", "-sS", "-w", "%{speed_download}", "https://speed.cloudflare.com/__down?bytes=2000000"]
    if s.get("mode") == "TOR":
        args[1:1] = ["--proxy", f"socks5h://127.0.0.1:{SOCKS_PORT}"]
    p = run(args, 35)
    try:
        bps = float(p.stdout.strip())
    except Exception:
        bps = 0.0
    return {"ok": p.returncode == 0 and bps > 0, "bytes_per_second": bps, "mbps": round(bps * 8 / 1_000_000, 2), "mode": s.get("mode")}

def update_status():
    p = run(["apt-cache", "policy", "cloudflare-warp", "tor", "obfs4proxy"], 15)
    return {"ok": p.returncode == 0, "text": p.stdout.strip()}

def nm_connection_uuids(name=CONSOLE_NAME):
    nmcli = executable("nmcli")
    if not nmcli:
        return []
    p = run([nmcli, "-t", "-f", "NAME,UUID", "connection", "show"], 8)
    if p.returncode:
        return []
    out = []
    for line in p.stdout.splitlines():
        parts = line.rsplit(":", 1)
        if len(parts) == 2 and parts[0] == name and parts[1]:
            out.append(parts[1])
    return out


def console_owned_uuid(cfg=None):
    cfg = load_json(CONSOLE, {}) if cfg is None else cfg
    expected = str(cfg.get("connection_uuid") or "")
    return expected if expected and expected in nm_connection_uuids(str(cfg.get("connection_name") or CONSOLE_NAME)) else None


def nm_connection_profile(uuid):
    nmcli = executable("nmcli")
    if not nmcli or not uuid:
        return None
    fields = [
        "connection.id",
        "connection.interface-name",
        "802-11-wireless.mode",
        "802-11-wireless.ssid",
        "802-11-wireless-security.key-mgmt",
        "802-11-wireless-security.psk",
        "ipv4.method",
        "ipv4.addresses",
        "ipv6.method",
    ]
    p = run([nmcli, "--show-secrets", "-g", ",".join(fields), "connection", "show", "uuid", uuid], 8)
    if p.returncode:
        return None
    values = p.stdout.rstrip("\n").splitlines()
    if len(values) != len(fields):
        return None
    return dict(zip(fields, values))


def migrate_legacy_console_profile(cfg=None):
    cfg = load_json(CONSOLE, {}) if cfg is None else dict(cfg)
    if not cfg or cfg.get("connection_uuid"):
        return console_owned_uuid(cfg)
    existing = nm_connection_uuids(CONSOLE_NAME)
    if len(existing) != 1:
        return None
    uuid = existing[0]
    profile = nm_connection_profile(uuid)
    if not profile:
        return None
    expected = {
        "connection.id": CONSOLE_NAME,
        "connection.interface-name": str(cfg.get("device") or ""),
        "802-11-wireless.mode": "ap",
        "802-11-wireless.ssid": str(cfg.get("ssid") or CONSOLE_NAME),
        "802-11-wireless-security.key-mgmt": "wpa-psk",
        "802-11-wireless-security.psk": str(cfg.get("password") or ""),
        "ipv4.method": "shared",
        "ipv6.method": "disabled",
    }
    if not expected["connection.interface-name"] or not expected["802-11-wireless-security.psk"]:
        return None
    if any(profile.get(k) != v for k, v in expected.items()):
        return None
    if "192.168.77.1/24" not in profile.get("ipv4.addresses", ""):
        return None
    cfg.update({
        "created_by": APP,
        "connection_name": CONSOLE_NAME,
        "connection_uuid": uuid,
    })
    atomic_json(CONSOLE, cfg)
    try:
        os.chmod(CONSOLE, 0o600)
    except Exception:
        pass
    return uuid


def console_status():
    nmcli = executable("nmcli")
    if not nmcli:
        return {"ok": False, "error": "nmcli missing"}
    p = run([nmcli, "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"], 8)
    rows = []
    for line in p.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) == 4:
            rows.append({"device": parts[0], "type": parts[1], "state": parts[2], "connection": parts[3]})
    default = default_route()
    uplink = None
    parts = default.split()
    if "dev" in parts:
        try:
            uplink = parts[parts.index("dev") + 1]
        except Exception:
            pass
    candidates = [r for r in rows if r["device"] != uplink and r["type"] in ("wifi", "ethernet") and not r["device"].startswith("p2p-")]
    cfg = load_json(CONSOLE, {})
    uuids = nm_connection_uuids()
    owned_uuid = console_owned_uuid(cfg)
    return {
        "ok": True,
        "uplink": uplink,
        "devices": rows,
        "candidates": candidates,
        "configured": bool(cfg),
        "config": {k: v for k, v in cfg.items() if k != "password"},
        "connection_exists": bool(uuids),
        "connection_count": len(uuids),
        "connection_owned": bool(owned_uuid),
        "connection_uuid": owned_uuid,
    }


def valid_console_password(value):
    return isinstance(value, str) and 8 <= len(value) <= 63


def apply_console_profile_policy(uuid, cfg):
    nmcli = executable("nmcli")
    if not nmcli or not uuid or not cfg:
        return {"ok": False, "error": "CONSOLE_PROFILE_CONFIG_MISSING"}
    password = str(cfg.get("password") or "")
    if not valid_console_password(password):
        return {"ok": False, "error": "CONSOLE_PASSWORD_INVALID"}
    dev = str(cfg.get("device") or "")
    ssid = str(cfg.get("ssid") or CONSOLE_NAME)
    if not dev:
        return {"ok": False, "error": "CONSOLE_DEVICE_MISSING"}
    p = run([
        nmcli, "connection", "modify", "uuid", uuid,
        "connection.interface-name", dev,
        "connection.autoconnect", "no",
        "802-11-wireless.ssid", ssid,
        "802-11-wireless.mode", "ap",
        "ipv4.method", "shared",
        "ipv4.addresses", "192.168.77.1/24",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.proto", CONSOLE_WIFI_PROTO,
        "wifi-sec.pmf", CONSOLE_WIFI_PMF,
        "wifi-sec.psk", password,
        "ipv6.method", "disabled",
    ], 20)
    if p.returncode:
        return {"ok": False, "error": (p.stdout + p.stderr).strip()}
    return {"ok": True, "connection_uuid": uuid}


def console_prepare():
    nmcli = executable("nmcli")
    if not nmcli:
        return {"ok": False, "error": "nmcli missing"}
    st = console_status()
    if not st.get("ok") or not st.get("candidates"):
        return {"ok": False, "error": "NO_SECONDARY_ADAPTER", "status": st}
    candidate = next((r for r in st["candidates"] if r["type"] == "wifi"), st["candidates"][0])
    dev = candidate["device"]
    typ = candidate["type"]
    if typ != "wifi":
        return {"ok": False, "error": "ONLY_WIFI_HOTSPOT_AUTOMATION_AVAILABLE", "candidate": candidate}
    old_cfg = load_json(CONSOLE, {})
    existing = nm_connection_uuids()
    owned_uuid = console_owned_uuid(old_cfg)
    migrated = False
    if existing and not owned_uuid:
        owned_uuid = migrate_legacy_console_profile(old_cfg)
        migrated = bool(owned_uuid)
        if migrated:
            old_cfg = load_json(CONSOLE, {})
    if existing and not owned_uuid:
        return {"ok": False, "error": "CONSOLE_PROFILE_NAME_OCCUPIED_UNOWNED", "connection_count": len(existing)}
    alphabet = string.ascii_letters + string.digits
    existing_password = old_cfg.get("password") if owned_uuid else None
    password = existing_password if valid_console_password(existing_password) else "".join(secrets.choice(alphabet) for _ in range(14))
    ssid = CONSOLE_NAME
    created = False
    if not owned_uuid:
        p = run([
            nmcli, "connection", "add", "type", "wifi", "ifname", dev,
            "con-name", CONSOLE_NAME, "autoconnect", "no", "ssid", ssid,
        ], 20)
        if p.returncode:
            return {"ok": False, "error": (p.stdout + p.stderr).strip()}
        after = nm_connection_uuids()
        new = [u for u in after if u not in existing]
        if len(new) != 1:
            return {"ok": False, "error": "CONSOLE_PROFILE_UUID_UNPROVEN", "new_profile_count": len(new)}
        owned_uuid = new[0]
        created = True
    policy_cfg = {
        "device": dev,
        "ssid": ssid,
        "password": password,
    }
    policy = apply_console_profile_policy(owned_uuid, policy_cfg)
    if not policy.get("ok"):
        if created:
            run([nmcli, "connection", "delete", "uuid", owned_uuid], 10)
        return policy
    cfg = {
        "created_by": APP,
        "connection_name": CONSOLE_NAME,
        "connection_uuid": owned_uuid,
        "device": dev,
        "type": typ,
        "ssid": ssid,
        "password": password,
        "gateway": "192.168.77.1",
        "client_ip": "192.168.77.2",
        "subnet": "192.168.77.0/24",
    }
    atomic_json(CONSOLE, cfg)
    try:
        os.chmod(CONSOLE, 0o600)
    except Exception:
        pass
    return {
        "ok": True,
        "state": "prepared",
        "config": {k: v for k, v in cfg.items() if k != "password"},
        "physical_validation": False,
        "connection_owned": True,
        "legacy_profile_migrated": migrated,
    }


def console_start():
    nmcli = executable("nmcli")
    cfg = load_json(CONSOLE, {})
    if not nmcli or not cfg:
        return {"ok": False, "error": "CONSOLE_NOT_PREPARED"}
    owned_uuid = console_owned_uuid(cfg) or migrate_legacy_console_profile(cfg)
    if not owned_uuid:
        return {"ok": False, "error": "CONSOLE_PROFILE_NOT_OWNED"}
    cfg = load_json(CONSOLE, {})
    policy = apply_console_profile_policy(owned_uuid, cfg)
    if not policy.get("ok"):
        return policy
    t = trace(timeout=10)
    if not (t.get("ok") and (t.get("trace") or {}).get("warp") == "on"):
        return {"ok": False, "error": "PC_WARP_NOT_ON", "trace": t}
    p = run([nmcli, "connection", "up", "uuid", owned_uuid], 30)
    if p.returncode:
        return {"ok": False, "error": (p.stdout + p.stderr).strip()}
    time.sleep(2)
    dev = cfg.get("device", "wlp2s0")
    detail = run([nmcli, "-g", "GENERAL.STATE,GENERAL.CONNECTION,IP4.ADDRESS", "device", "show", dev], 8)
    forward = pathlib.Path("/proc/sys/net/ipv4/ip_forward").read_text().strip() if pathlib.Path("/proc/sys/net/ipv4/ip_forward").exists() else "unknown"
    detail_text = (detail.stdout + detail.stderr).strip()
    ready = detail.returncode == 0 and CONSOLE_NAME in detail_text and "192.168.77.1/24" in detail_text and forward == "1"
    return {
        "ok": ready,
        "state": "hotspot-up" if ready else "hotspot-unverified",
        "config": {k: v for k, v in cfg.items() if k != "password"},
        "network_manager": detail_text,
        "ipv4_forward": forward,
        "physical_validation": False,
        "warning": "Physical console DHCP/UDP/country validation remains required.",
    }


def console_stop():
    nmcli = executable("nmcli")
    cfg = load_json(CONSOLE, {})
    if not nmcli:
        return {"ok": False, "error": "nmcli missing"}
    if not cfg:
        return {"ok": True, "state": "not-prepared"}
    owned_uuid = console_owned_uuid(cfg) or migrate_legacy_console_profile(cfg)
    if not owned_uuid:
        return {"ok": False, "error": "CONSOLE_PROFILE_NOT_OWNED"}
    p = run([nmcli, "connection", "down", "uuid", owned_uuid], 20)
    text = (p.stdout + p.stderr).strip()
    low = text.lower()
    already_inactive = (
        "not active" in low
        or "not an active connection" in low
        or "no active connection provided" in low
    )
    return {
        "ok": p.returncode == 0 or already_inactive,
        "state": "stopped" if p.returncode == 0 else ("already-inactive" if already_inactive else "stop-failed"),
        "text": text,
        "connection_uuid": owned_uuid,
    }

def export_report():
    ensure_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    payload = {
        "product": APP,
        "version": VERSION,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": inventory(),
        "current_status": current_status(),
        "console_status": console_status(),
    }
    json_path = EVIDENCE / f"FreeNetHub_Support_{stamp}.json"
    atomic_json(json_path, payload)
    zip_path = EVIDENCE / f"FreeNetHub_Support_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(json_path, json_path.name)
    return {"ok": True, "json": str(json_path), "zip": str(zip_path)}

def import_obfs4(path):
    src = pathlib.Path(path)
    if not src.is_file():
        return {"ok": False, "error": "file missing"}
    lines = [x.strip() for x in src.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    valid = [x for x in lines if x.startswith("obfs4 ") and " cert=" in x and " iat-mode=" in x]
    if not valid:
        return {"ok": False, "error": "no valid obfs4 bridge lines"}
    ensure_dirs()
    BRIDGES.write_text("\n".join(valid) + "\n", encoding="utf-8")
    os.chmod(BRIDGES, 0o600)
    return {"ok": True, "count": len(valid)}

def import_snowflake(path):
    src = pathlib.Path(path)
    if not src.is_file():
        return {"ok": False, "error": "file missing"}
    lines = [x.strip() for x in src.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    valid = [x for x in lines if x.startswith("snowflake ") and " url=" in x]
    if not valid:
        return {"ok": False, "error": "no valid snowflake bridge lines"}
    ensure_dirs()
    SNOWFLAKE_BRIDGES.write_text("\n".join(valid) + "\n", encoding="utf-8")
    os.chmod(SNOWFLAKE_BRIDGES, 0o600)
    return {"ok": True, "count": len(valid)}

def app_snapshot():
    st = current_status()
    tr = st.get("trace") or (st.get("tor") or {}).get("egress") or {}
    trace_data = tr.get("trace") or {}
    return {
        "ok": bool(st.get("ok")),
        "mode": st.get("mode"),
        "provider": st.get("provider"),
        "country": trace_data.get("loc"),
        "ip": trace_data.get("ip"),
        "warp": trace_data.get("warp"),
        "details": st,
    }

if __name__ == "__main__":
    ensure_dirs()
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
