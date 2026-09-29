#!/usr/bin/env python3
import hashlib,json,pathlib,os,sys
R=pathlib.Path(__file__).resolve().parent.parent
I=pathlib.Path(os.environ["LOCALAPPDATA"])/"Programs"/"FreeNetHub"
def h(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
out={"status":"PASS","errors":[]}
try:
    rel=json.loads((I/"RELEASE.json").read_text(encoding="utf-8-sig"))
    out["installedRevision"]=rel.get("releaseRevision")
    if rel.get("releaseRevision")!="4.2.0-local-r38-direct-method": out["errors"].append("REVISION")
    rt=json.loads((I/"INSTALL_RUNTIME_STATUS.json").read_text(encoding="utf-8-sig"))
    out["runtimeStatus"]=rt.get("status")
    if rt.get("status")!="PASS": out["errors"].append("RUNTIME")
    am=json.loads((R/"app"/"manifest.json").read_text(encoding="utf-8-sig"))
    bad=[]
    for x in am["code"]:
        s=R/"app"/x["file"]; i=I/"app"/x["file"]
        if not s.exists() or not i.exists() or h(s)!=h(i) or h(s)!=x["sha256"].upper(): bad.append(x["file"])
    out["appFiles"]=len(am["code"]);out["appMismatches"]=bad
    if bad: out["errors"].append("APP_PARITY")
    gm=json.loads((R/"gateway"/"manifest.json").read_text(encoding="utf-8-sig"))
    badg=[]
    for x in gm["files"]:
        s=R/"gateway"/x["file"]; i=I/"gateway"/x["file"]
        if not s.exists() or not i.exists() or h(s)!=h(i) or h(s)!=x["sha256"].upper(): badg.append(x["file"])
    out["gatewayFiles"]=len(gm["files"]);out["gatewayMismatches"]=badg
    if badg: out["errors"].append("GATEWAY_PARITY")
    out["releaseParity"]=h(R/"RELEASE.json")==h(I/"RELEASE.json")
    if not out["releaseParity"]: out["errors"].append("RELEASE_PARITY")
except Exception as e:
    out["errors"].append(type(e).__name__+":"+str(e))
if out["errors"]: out["status"]="FAIL"
print(json.dumps(out,indent=2))
sys.exit(0 if out["status"]=="PASS" else 20)
