#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent.parent

def run(*args: str, binary: bool=False):
    return subprocess.check_output(["git",*args],cwd=R,text=not binary,encoding=None if binary else "utf-8")

def blob(rel: str) -> bytes:
    rel=pathlib.PurePosixPath(rel).as_posix()
    return run("show",":"+rel,binary=True)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def write_json(path: pathlib.Path,obj) -> None:
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def stage(rel: str) -> None:
    subprocess.check_call(["git","add","--",rel],cwd=R)

def verify_index_manifest() -> list:
    pm=json.loads(blob("PUBLIC_MANIFEST.json").decode("utf-8-sig"))
    listed={r["file"] for r in pm["files"]}
    tracked={pathlib.PurePosixPath(x).as_posix() for x in run("ls-files","-z","--cached").split("\0") if x}
    tracked.discard("PUBLIC_MANIFEST.json")
    bad=[]
    if listed!=tracked:
        bad.append({"setDifference":sorted(listed^tracked)})
    for row in pm["files"]:
        b=blob(row["file"])
        if len(b)!=int(row["bytes"]) or digest(b)!=str(row["sha256"]).upper():
            bad.append({"file":row["file"],"actualBytes":len(b),"expectedBytes":row["bytes"],"actualSha256":digest(b),"expectedSha256":row["sha256"]})
    return bad

def main() -> int:
    rel=json.loads(blob("RELEASE.json").decode("utf-8-sig"))
    checks={
        "engineSha256":"app/engine.py",
        "uiSha256":"app/FreeNetHub.ps1",
        "viewSha256":"app/View.xaml",
        "nodeHubSha256":"app/nodehub.py",
        "appManifestSha256":"app/manifest.json",
        "desktopShellSha256":"windows/standalone/FreeNetHub.exe",
        "gatewayManifestSha256":"gateway/manifest.json",
        "crossPlatformManifestSha256":"crossplatform/MANIFEST.json",
    }
    for key,path in checks.items():
        rel[key]=digest(blob(path))
    ev=str(rel.get("acceptanceEvidence") or "")
    if not ev:
        raise SystemExit("ACCEPTANCE_EVIDENCE_MISSING")
    ej=json.loads(blob(ev).decode("utf-8-sig"))
    if ej.get("version")!=rel.get("version") or ej.get("status")!=rel.get("status"):
        raise SystemExit("ACCEPTANCE_EVIDENCE_CONTENT_MISMATCH")
    write_json(R/"RELEASE.json",rel);stage("RELEASE.json")
    tracked=[pathlib.PurePosixPath(x).as_posix() for x in run("ls-files","-z","--cached").split("\0") if x and x!="PUBLIC_MANIFEST.json"]
    rows=[]
    for path in sorted(tracked,key=str.lower):
        b=blob(path);rows.append({"file":path,"bytes":len(b),"sha256":digest(b)})
    write_json(R/"PUBLIC_MANIFEST.json",{"schema":3,"version":rel["releaseRevision"],"source":"git-index-canonical","files":rows});stage("PUBLIC_MANIFEST.json")
    bad=verify_index_manifest()
    sealed=json.loads(blob("RELEASE.json").decode("utf-8-sig"))
    release_bad=[key for key,path in checks.items() if str(sealed.get(key,"")).upper()!=digest(blob(path))]
    result={"status":"PASS" if not bad and not release_bad else "FAIL","files":len(rows),"releaseBad":release_bad,"publicBad":bad,"releaseRevision":sealed.get("releaseRevision"),"publicManifestSha256":digest(blob("PUBLIC_MANIFEST.json"))}
    print(json.dumps(result,indent=2))
    return 0 if result["status"]=="PASS" else 1
if __name__=="__main__":
    raise SystemExit(main())
