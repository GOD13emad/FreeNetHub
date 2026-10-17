"""Prepare the NONRELEASE R55 candidate in a dedicated one-writer worktree only.
The public R53 and accepted owner R54 lines, their evidence, and the active
installation must never be overwritten by this script.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

BASE = "406447b8ca7793064b15dab8cf4420bed4a4684d"
R54_VERSION = "4.3.10"
R54_REVISION = "4.3.10-r54-update-cache-retention"
VERSION = "4.3.11"
REVISION = "4.3.11-r55-native-status-review"
APPID = "AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}"
SOURCE_CONTROLLER = "33B90ABB4ABE725C28150086E348C97C73726BD006E3AF5E63066D107F7DC498"
V519_CONTROLLER = "E850C849EC5F6A062F7D4E5ADE5D625B907A299F35DCF413514183F77FA9D38E"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def write_json(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

def main(root):
    root = root.resolve(strict=True)
    if root.name != "fnh-r55-v519-private-review":
        raise RuntimeError("ISOLATED_R55_ROOT_REQUIRED")
    rev = subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"], text=True).strip()
    if rev != BASE:
        raise RuntimeError("BASE_COMMIT_CHANGED")
    release_path = root / "RELEASE.json"
    app_path = root / "app/manifest.json"
    gateway_path = root / "gateway/manifest.json"
    inno_path = root / "windows/installer/FreeNetHub.iss"
    candidate_evidence = root / "evidence/V519_R55_PRIVATE_CANDIDATE.json"
    if candidate_evidence.exists():
        raise RuntimeError("CANDIDATE_ALREADY_PREPARED")
    release = json.loads(release_path.read_text(encoding="utf-8-sig"))
    app = json.loads(app_path.read_text(encoding="utf-8-sig"))
    gateway = json.loads(gateway_path.read_text(encoding="utf-8-sig"))
    iss = inno_path.read_text(encoding="utf-8-sig")
    if not (release["version"] == app["version"] == R54_VERSION and
            release["releaseRevision"] == app["coreVersion"] == R54_REVISION):
        raise RuntimeError("R54_RELEASE_PRESTATE_CHANGED")
    if sha(root/"gateway/gateway_control.ps1") != V519_CONTROLLER:
        raise RuntimeError("V519_CONTROLLER_NOT_SEALED")
    if len(gateway["files"]) != 18:
        raise RuntimeError("R54_GATEWAY_FILE_SET_CHANGED")
    expected = {r["file"] for r in gateway["files"]}
    if "dns_guard_watchdog.ps1" not in expected:
        raise RuntimeError("NATIVE_WATCHDOG_NOT_IN_GATEWAY_MANIFEST")
    for item in gateway["files"]:
        f = root/"gateway"/item["file"]
        # Only the explicitly patched controller's manifest entry may differ
        if item["file"] != "gateway_control.ps1" and (f.stat().st_size != item["bytes"] or sha(f) != item["sha256"]):
            raise RuntimeError("R54_GATEWAY_SOURCE_MISMATCH:"+item["file"])
        item["bytes"] = f.stat().st_size
        item["sha256"] = sha(f)
    for row in app["code"]:
        f = root/"app"/row["file"]
        if f.stat().st_size != row["bytes"] or sha(f) != row["sha256"]:
            raise RuntimeError("R54_APP_CODE_MISMATCH:"+row["file"])
    if APPID not in iss or "PrivilegesRequired=lowest" not in iss or "RestartApplications=no" not in iss:
        raise RuntimeError("INNO_SAFETY_IDENTITY_CHANGED")
    swaps = {
        '#define MyAppVersion "4.3.10"':'#define MyAppVersion "4.3.11"',
        r'OutputDir=..\..\delivery\release_candidate_v4.3.10':r'OutputDir=..\..\delivery\release_candidate_v4.3.11',
        'OutputBaseFilename=FreeNetHub_4.3.10_R54_V481_GATEWAY_REVIEW_DO_NOT_RELEASE':'OutputBaseFilename=FreeNetHub_4.3.11_R55_V519_PRIVATE_REVIEW_DO_NOT_RELEASE',
        'VersionInfoVersion=4.3.10.0':'VersionInfoVersion=4.3.11.0',
        'VersionInfoDescription=FreeNet Hub 4.3.10 R54 bounded installer-cache retention':'VersionInfoDescription=FreeNet Hub 4.3.11 R55 native status private review'
    }
    for old,new in swaps.items():
        if iss.count(old) != 1:
            raise RuntimeError("INNO_ANCHOR_CHANGED:"+old)
        iss = iss.replace(old,new)
    # All preconditions above must pass before writes.
    app["version"] = VERSION
    app["coreVersion"] = REVISION
    app["scope"] = "R55_TRUE_NATIVE_STATUS+" + app["scope"]
    gateway_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(app_path, app)
    write_json(gateway_path, gateway)
    release["version"] = VERSION
    release["releaseRevision"] = REVISION
    release["status"] = "R55_PRIVATE_CANDIDATE_NOT_FOR_RELEASE"
    release["installerStatus"] = "R55_PRIVATE_UNSIGNED_UNTESTED"
    release["acceptanceEvidence"] = "evidence/V519_R55_PRIVATE_CANDIDATE.json"
    release["appManifestSha256"] = sha(app_path)
    release["gatewayManifestSha256"] = sha(gateway_path)
    release["installerSha256"] = None
    write_json(release_path, release)
    inno_path.write_text(iss, encoding="utf-8", newline="\n")
    rec = {
      "schema":1, "status":"R55_PRIVATE_CANDIDATE_NOT_FOR_RELEASE", "verificationStatus":"ISOLATED_REVIEW_ACCEPTANCE_PENDING",
      "version":VERSION, "revision":REVISION, "baseSHA":BASE,
      "acceptedOwnerR54":R54_REVISION, "controllerSha256":sha(root/"gateway/gateway_control.ps1"),
      "gatewayManifestSha256":sha(gateway_path), "appManifestSha256":sha(app_path),
      "fixedAppId":"BCE83A4E-8897-4D52-A650-BB67A2BB8142",
      "unsigned":True,"publicRelease":False,"installedOwnerMutation":False,
      "openGates":["isolated_build","fresh_install","R54_upgrade","rollback","CI","WiFi_DNS53","signing"]
    }
    write_json(candidate_evidence, rec)
    print(json.dumps({"status":"R55_PRIVATE_METADATA_PREPARED_NOT_ACCEPTED",
        "revision":REVISION,"appManifest":sha(app_path),"gatewayManifest":sha(gateway_path),
        "installer":(root/"windows/installer/FreeNetHub.iss").name}, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_r55_private.py <isolated-root>")
    main(Path(sys.argv[1]))
