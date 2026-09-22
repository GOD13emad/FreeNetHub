#!/usr/bin/env python3
import importlib.util, json, os, pathlib, stat, subprocess, sys, tempfile

root=pathlib.Path(__file__).resolve().parent
p=root/"freenet_hub_linux.py"
spec=importlib.util.spec_from_file_location("fnh_private_state",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

with tempfile.TemporaryDirectory(prefix="fnh-private-") as td:
    base=pathlib.Path(td)/"FreeNetHub"
    old=(m.STATE,m.EVIDENCE,m.TOR_STATE,m.SESSION)
    m.STATE=base
    m.EVIDENCE=base/"evidence"
    m.TOR_STATE=base/"tor"
    m.SESSION=base/"session.json"
    try:
        m.ensure_dirs()
        m.set_session("WARP_TRIAL","system",{"guard_token":"dummy-token"})
        modes={
            "state":stat.S_IMODE(m.STATE.stat().st_mode),
            "evidence":stat.S_IMODE(m.EVIDENCE.stat().st_mode),
            "tor":stat.S_IMODE(m.TOR_STATE.stat().st_mode),
            "session":stat.S_IMODE(m.SESSION.stat().st_mode),
        }
    finally:
        m.STATE,m.EVIDENCE,m.TOR_STATE,m.SESSION=old

with tempfile.TemporaryDirectory(prefix="fnh-guard-") as td:
    d=pathlib.Path(td)
    keep=d/"keep.ok"; log=d/"guard.log"; session=d/"session.json"
    keep.write_text("confirmed\n",encoding="utf-8")
    session.write_text(json.dumps({"mode":"WARP_TRIAL","detail":{"guard_token":"dummy-token"}}),encoding="utf-8")
    subprocess.run([sys.executable,str(root/"warp_guard.py"),"dummy-token","0",str(keep),str(log)],check=True,timeout=10)
    guard_mode=stat.S_IMODE(log.stat().st_mode)

out={
    "ok":modes=={"state":0o700,"evidence":0o700,"tor":0o700,"session":0o600} and guard_mode==0o600,
    "modes":{k:oct(v) for k,v in modes.items()},
    "guard_log":oct(guard_mode),
}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["ok"] else 2)
