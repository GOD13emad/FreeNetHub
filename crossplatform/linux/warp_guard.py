#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
import time

os.umask(0o077)

def private_write(path, text):
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)

token = sys.argv[1]
seconds = int(sys.argv[2])
keep = pathlib.Path(sys.argv[3])
log = pathlib.Path(sys.argv[4])
state_dir = keep.parent
session_path = state_dir / "session.json"

def read_session():
    try:
        return json.loads(session_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def trial_is_current():
    current = read_session()
    return current.get("mode") == "WARP_TRIAL" and (current.get("detail") or {}).get("guard_token") == token

def clear_trial_session():
    try:
        if not trial_is_current():
            return
        tmp = session_path.with_suffix(".json.tmp")
        private_write(tmp, json.dumps({
            "mode": None,
            "provider": None,
            "detail": {},
            "updated": time.time(),
        }, indent=2) + "\n")
        os.replace(tmp, session_path)
        os.chmod(session_path, 0o600)
    except Exception:
        pass

deadline = time.monotonic() + seconds
while time.monotonic() < deadline:
    if keep.exists():
        private_write(log, "KEEP " + token + "\n")
        try:
            keep.unlink()
        except Exception:
            pass
        raise SystemExit(0)
    time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))

if keep.exists():
    private_write(log, "KEEP " + token + "\n")
    try:
        keep.unlink()
    except Exception:
        pass
    raise SystemExit(0)

if not trial_is_current():
    private_write(log, "STALE_NO_ACTION " + token + "\n")
    raise SystemExit(0)

try:
    p = subprocess.run(
        ["warp-cli", "--accept-tos", "disconnect"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
    )
    clear_trial_session()
    private_write(log, f"AUTO_DISCONNECT rc={p.returncode}\n{p.stdout}")
except Exception as e:
    private_write(log, "AUTO_DISCONNECT_ERROR " + repr(e) + "\n")
