from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent.parent
M=json.loads((R/"app"/"manifest.json").read_text(encoding="utf-8-sig"))
bad=[]
for row in M["code"]:
    p=R/"app"/row["file"]
    h=hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else ""
    if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or h!=row["sha256"].upper(): bad.append(row["file"])
ET.parse(R/"app"/"View.xaml")
cp=json.loads((R/"crossplatform"/"MANIFEST.json").read_text(encoding="utf-8-sig"))
badcp=[]
for row in cp["files"]:
    p=R/"crossplatform"/row["file"]
    h=hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else ""
    if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or h!=row["sha256"].upper(): badcp.append(row["file"])
wm=json.loads((R/"windows"/"standalone"/"MANIFEST.json").read_text(encoding="utf-8-sig"))
badwin=[]
for row in wm["files"]:
    p=R/"windows"/"standalone"/row["name"]
    h=hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else ""
    if not p.is_file() or p.stat().st_size!=int(row["bytes"]) or h!=row["sha256"].upper(): badwin.append(row["name"])
rel=json.loads((R/"RELEASE.json").read_text(encoding="utf-8-sig"))
badrel=[]
checks={"engineSha256":R/"app"/"engine.py","uiSha256":R/"app"/"FreeNetHub.ps1","viewSha256":R/"app"/"View.xaml","desktopShellSha256":R/"windows"/"standalone"/"FreeNetHub.exe"}
for key,fp in checks.items():
    if hashlib.sha256(fp.read_bytes()).hexdigest().upper()!=rel[key].upper():badrel.append(key)
result={"appManifest":"PASS" if not bad else "FAIL","appBad":bad,"crossPlatformManifest":"PASS" if not badcp else "FAIL","crossPlatformBad":badcp,"windowsPackageManifest":"PASS" if not badwin else "FAIL","windowsPackageBad":badwin,"releaseHashes":"PASS" if not badrel else "FAIL","releaseHashBad":badrel}
print(json.dumps(result,indent=2))
sys.exit(0 if not bad and not badcp and not badwin and not badrel else 1)
