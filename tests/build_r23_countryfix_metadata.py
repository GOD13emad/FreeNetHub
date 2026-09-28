#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def row(base,rel):
 p=pathlib.Path(base)/rel
 return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
def main():
 appfiles=["engine.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico"]
 out={"version":"4.2.0","scope":"BROWSER_PROXY_DEFAULT+OPTIONAL_PC_TUNNEL+CONSOLE_GATEWAY+NODE_HUB","code":[row(R/"app",x) for x in appfiles],"coreVersion":"4.0-scope-ui4-country-strict-actual-exit-r23"}
 (R/"app"/"manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
 print(json.dumps({"status":"PASS","engineSha256":sha(R/"app"/"engine.py"),"appManifestSha256":sha(R/"app"/"manifest.json")},indent=2))
if __name__=="__main__": main()
