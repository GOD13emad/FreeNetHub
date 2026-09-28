#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent

def canonical_bytes(rel: str) -> bytes:
    rel=pathlib.PurePosixPath(rel).as_posix()
    p=R/rel
    oid=subprocess.check_output(["git","hash-object","-w",f"--path={rel}",str(p)],cwd=R,text=True).strip()
    return subprocess.check_output(["git","cat-file","blob",oid],cwd=R)

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
        data=canonical_bytes(rel)
        files.append({"file":rel,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()})
pm={"schema":3,"version":"4.2.0-local-r28-final","source":"git-clean-filtered-candidate","files":sorted(files,key=lambda r:r["file"].lower())}
(R/"PUBLIC_MANIFEST.json").write_text(json.dumps(pm,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":"PASS","files":len(files),"sha256":hashlib.sha256((R/"PUBLIC_MANIFEST.json").read_bytes()).hexdigest().upper()},indent=2))
