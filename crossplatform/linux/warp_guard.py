#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
import time

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
        tmp.write_text(json.dumps({
            "mode": None,
            "provider": None,
            "detail": {},
            "updated": time.time(),
        }, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, session_path)
    except Exception:
        pass

time.sleep(seconds)

if keep.exists():
    log.write_text("KEEP " + token + "\n", encoding="utf-8")
    try:
        keep.unlink()
    except Exception:
        pass
    raise SystemExit(0)

if not trial_is_current():
    log.write_text("STALE_NO_ACTION " + token + "\n", encoding="utf-8")
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
    log.write_text(f"AUTO_DISCONNECT rc={p.returncode}\n{p.stdout}", encoding="utf-8")
except Exception as e:
    log.write_text("AUTO_DISCONNECT_ERROR " + repr(e) + "\n", encoding="utf-8")
