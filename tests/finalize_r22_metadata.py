#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
STATUS="ACCEPTED_WINDOWS_4.2_R22_COUNTRY_SHADOWHUB"
REV="4.2.0-public-r22-country-shadowhub-final"
INSTALLER=R/"delivery"/"github_v4.2.0"/"FreeNetHub_4.2.0_R22_Country_ShadowHub_Setup.exe"
EVIDENCE=R/"evidence"/"R22_FINAL_ACCEPTANCE_20260928.json"
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def wj(p,o): pathlib.Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def row(rel):
 p=R/rel
 return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
def candidates():
 raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=R)
 out=[]
 for x in raw.decode("utf-8").split("\0"):
  if not x: continue
  rel=pathlib.PurePosixPath(x).as_posix(); p=R/rel
  if rel!="PUBLIC_MANIFEST.json" and p.is_file(): out.append(rel)
 return sorted(set(out),key=str.lower)
def main():
 if not INSTALLER.is_file() or not EVIDENCE.is_file(): raise SystemExit("R22_FINAL_INPUT_MISSING")
 ev=json.loads(EVIDENCE.read_text(encoding="utf-8-sig"))
 if ev.get("status")!=STATUS: raise SystemExit("R22_FINAL_EVIDENCE_STATUS")
 ih=sha(INSTALLER)
 if ih!="214B05E0A48B75C66275F914BFF571A70EE478F6D84F48B132063AD362AF9CDF": raise SystemExit("R22_INSTALLER_HASH_DRIFT")
 rel=json.loads((R/"RELEASE.json").read_text(encoding="utf-8-sig"))
 rel["releaseRevision"]=REV
 rel["status"]=STATUS
 rel["installerSha256"]=ih
 rel["installerStatus"]="R22_BUILT_INSTALLED_SMOKE_ACCEPTED"
 rel["acceptanceEvidence"]="evidence/R22_FINAL_ACCEPTANCE_20260928.json"
 rel.setdefault("r22",{})["installerAcceptance"]="PASS"
 rel["r22"]["installedBytesMatchSource"]=True
 rel["r22"]["installedUiSmoke"]="PASS"
 rel["r22"]["atRestNetwork"]="PASS"
 wj(R/"RELEASE.json",rel)
 wj(R/"PUBLIC_MANIFEST.json",{"schema":3,"version":REV,"source":"git-candidate-working-tree","files":[row(x) for x in candidates()]})
 print(json.dumps({"status":"PASS","installerSha256":ih,"releaseSha256":sha(R/"RELEASE.json"),"publicManifestSha256":sha(R/"PUBLIC_MANIFEST.json"),"evidenceSha256":sha(EVIDENCE)},indent=2))
if __name__=="__main__": main()
