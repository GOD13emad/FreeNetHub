#!/usr/bin/env python3
import pathlib, subprocess, sys, time
token=sys.argv[1]; seconds=int(sys.argv[2]); keep=pathlib.Path(sys.argv[3]); log=pathlib.Path(sys.argv[4])
time.sleep(seconds)
if keep.exists():
    log.write_text("KEEP "+token+"\n",encoding="utf-8")
    raise SystemExit(0)
try:
    p=subprocess.run(["warp-cli","--accept-tos","disconnect"],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20)
    log.write_text("AUTO_DISCONNECT rc=%s\n%s"%(p.returncode,p.stdout),encoding="utf-8")
except Exception as e:
    log.write_text("AUTO_DISCONNECT_ERROR "+repr(e)+"\n",encoding="utf-8")
