#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parent.parent
BACK=R/"delivery"/"private_evidence_20260928"
FILES=[
 "evidence/R22_INSTALLED_PRODUCT_SMOKE_20260928.json",
 "evidence/R22_INSTALLER_QUALIFICATION_ACCEPTANCE_20260928.json",
 "evidence/R23_INSTALLED_PRODUCT_SMOKE_20260928.json",
 "evidence/R24_INSTALLED_PRODUCT_SMOKE_20260928.json",
 "evidence/R25_INSTALLED_PRODUCT_SMOKE_20260928.json",
 "evidence/R27_INSTALLED_PRODUCT_SMOKE_20260928.json",
]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
def writej(p,o): pathlib.Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
BACK.mkdir(parents=True,exist_ok=True)
for rel in FILES:
 p=R/rel
 if not p.is_file(): continue
 shutil.copy2(p,BACK/p.name)
 j=load(p)
 root=str(j.get("installRoot") or "")
 marker="\\AppData\\Local\\"
 if marker in root:
  suffix=root.split(marker,1)[1]
  j["installRoot"]="%LOCALAPPDATA%\\"+suffix
 writej(p,j)
r22=R/"evidence"/"R22_FINAL_ACCEPTANCE_20260928.json"
j=load(r22)
j["installer"]["qualificationEvidenceSha256"]=sha(R/"evidence"/"R22_INSTALLER_QUALIFICATION_ACCEPTANCE_20260928.json")
j["installer"]["installedSmokeEvidenceSha256"]=sha(R/"evidence"/"R22_INSTALLED_PRODUCT_SMOKE_20260928.json")
writej(r22,j)
print(json.dumps({
 "status":"PASS",
 "backupDir":str(BACK),
 "r22QualificationSha256":j["installer"]["qualificationEvidenceSha256"],
 "r22SmokeSha256":j["installer"]["installedSmokeEvidenceSha256"],
 "r22FinalSha256":sha(r22),
 "r27SmokeSha256":sha(R/"evidence"/"R27_INSTALLED_PRODUCT_SMOKE_20260928.json")
},indent=2))
