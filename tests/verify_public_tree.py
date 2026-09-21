from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent.parent

def h(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def verify_manifest(base,manifest,key):
    m=json.loads(manifest.read_text(encoding="utf-8-sig"))
    failures=[]
    for row in m[key]:
        rel=row.get("file",row.get("name"))
        p=base/rel
        if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or h(p)!=row["sha256"].upper():
            failures.append(rel)
    return m,failures

am=json.loads((R/"app"/"manifest.json").read_text(encoding="utf-8-sig"))
appbad=[]
for row in am["code"]:
    p=R/"app"/row["file"]
    if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or h(p)!=row["sha256"].upper():
        appbad.append(row["file"])
ET.parse(R/"app"/"View.xaml")

gm,gatewaybad=verify_manifest(R/"gateway",R/"gateway"/"manifest.json","files")
cm,crossbad=verify_manifest(R/"crossplatform",R/"crossplatform"/"MANIFEST.json","files")
wm,winbad=verify_manifest(R/"windows"/"standalone",R/"windows"/"standalone"/"MANIFEST.json","files")
rel=json.loads((R/"RELEASE.json").read_text(encoding="utf-8-sig"))
checks={
 "engineSha256":R/"app"/"engine.py",
 "uiSha256":R/"app"/"FreeNetHub.ps1",
 "viewSha256":R/"app"/"View.xaml",
 "desktopShellSha256":R/"windows"/"standalone"/"FreeNetHub.exe",
 "gatewayManifestSha256":R/"gateway"/"manifest.json",
 "crossPlatformManifestSha256":R/"crossplatform"/"MANIFEST.json",
}
relbad=[k for k,p in checks.items() if h(p)!=rel[k].upper()]
ev=R/rel["acceptanceEvidence"]
if not ev.is_file():
    relbad.append("acceptanceEvidence")
else:
    ej=json.loads(ev.read_text(encoding="utf-8-sig"))
    if ej.get("version")!="4.2.0" or ej.get("status")!="ACCEPTED_WINDOWS_4.2_SOFTWARE_RELEASE":
        relbad.append("acceptanceEvidenceContent")
forbidden=[]
for p in R.rglob("*"):
    if not p.is_file() or ".git" in p.parts:
        continue
    relp=p.relative_to(R).as_posix()
    low=relp.lower()
    if low=="app/dependencies.json" or low.startswith("gateway/runtime/") or low.startswith("backup/") or low.startswith("delivery/") or (low.startswith("data/") and low!="data/.gitkeep") or (low.startswith("jobs/") and low!="jobs/.gitkeep"):
        forbidden.append(relp)
publicbad=[]
pm_path=R/"PUBLIC_MANIFEST.json"
if pm_path.is_file():
    pm=json.loads(pm_path.read_text(encoding="utf-8-sig"))
    listed=set()
    for row in pm["files"]:
        relp=row["file"]
        listed.add(relp)
        fp=R/relp
        if not fp.is_file() or fp.stat().st_size!=int(row["bytes"]) or h(fp)!=row["sha256"].upper():
            publicbad.append(relp)
    actual={p.relative_to(R).as_posix() for p in R.rglob("*") if p.is_file() and ".git" not in p.parts and p.name!="PUBLIC_MANIFEST.json"}
    if listed!=actual:
        publicbad.extend(sorted(listed^actual))
else:
    publicbad.append("PUBLIC_MANIFEST.json")

result={
 "publicManifest":"PASS" if not publicbad else "FAIL","publicManifestBad":publicbad,
 "appManifest":"PASS" if not appbad else "FAIL","appBad":appbad,
 "gatewayManifest":"PASS" if not gatewaybad else "FAIL","gatewayBad":gatewaybad,
 "crossPlatformManifest":"PASS" if not crossbad else "FAIL","crossPlatformBad":crossbad,
 "windowsPackageManifest":"PASS" if not winbad else "FAIL","windowsPackageBad":winbad,
 "releaseHashes":"PASS" if not relbad else "FAIL","releaseHashBad":relbad,
 "forbiddenRuntimeArtifacts":"PASS" if not forbidden else "FAIL","forbidden":forbidden,
}
print(json.dumps(result,indent=2))
sys.exit(0 if not any((publicbad,appbad,gatewaybad,crossbad,winbad,relbad,forbidden)) else 1)
