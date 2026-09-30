#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
B=R/"crossplatform"
raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard","crossplatform"],cwd=R)
rows=[]
for rel in raw.decode("utf-8").split("\0"):
    if not rel: continue
    p=R/rel
    inner=p.relative_to(B).as_posix()
    if inner=="MANIFEST.json" or "__pycache__" in p.parts or not p.is_file(): continue
    rows.append({"file":inner,"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest().upper()})
m={"schema":1,"version":"4.2.0-crossplatform-r40-linux-r13","files":sorted(rows,key=lambda x:x["file"].lower())}
(B/"MANIFEST.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":"PASS","files":len(rows),"manifestSha256":hashlib.sha256((B/"MANIFEST.json").read_bytes()).hexdigest().upper()}))
