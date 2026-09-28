#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=R)
files=[]
for x in raw.decode("utf-8").split("\0"):
    if not x:
        continue
    rel=pathlib.PurePosixPath(x).as_posix()
    if rel=="PUBLIC_MANIFEST.json":
        continue
    p=R/rel
    if p.is_file():
        data=p.read_bytes()
        files.append({"file":rel,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()})
pm={"schema":3,"version":"4.2.0-local-r28-final","source":"working-tree-public-candidate","files":sorted(files,key=lambda r:r["file"].lower())}
(R/"PUBLIC_MANIFEST.json").write_text(json.dumps(pm,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":"PASS","files":len(files),"sha256":hashlib.sha256((R/"PUBLIC_MANIFEST.json").read_bytes()).hexdigest().upper()},indent=2))
