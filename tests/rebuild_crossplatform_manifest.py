#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
B=R/"crossplatform"

def canonical_bytes(rel):
    rel=pathlib.PurePosixPath(rel).as_posix()
    p=R/rel
    oid=subprocess.check_output(["git","hash-object","-w",f"--path={rel}",str(p)],cwd=R,text=True).strip()
    return subprocess.check_output(["git","cat-file","blob",oid],cwd=R)

raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard","crossplatform"],cwd=R)
rows=[]
for rel in raw.decode("utf-8").split("\0"):
    if not rel: continue
    p=R/rel
    inner=p.relative_to(B).as_posix()
    if inner=="MANIFEST.json" or "__pycache__" in p.parts or not p.is_file(): continue
    data=canonical_bytes(rel)
    rows.append({"file":inner,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()})
m={"schema":1,"version":"4.3.7-crossplatform-r51-linux-r18","files":sorted(rows,key=lambda x:x["file"].lower())}
(B/"MANIFEST.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
data=canonical_bytes("crossplatform/MANIFEST.json")
print(json.dumps({"status":"PASS","files":len(rows),"manifestCanonicalSha256":hashlib.sha256(data).hexdigest().upper()}))
