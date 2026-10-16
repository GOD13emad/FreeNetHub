"""Fail-closed release-line classifier for CI; keeps historical R53 tests intact."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
LINES={
    "R53": ("4.3.9","4.3.9-r53-inno-root-guard","4.3.9"),
    "R55": ("4.3.11","4.3.11-r55-native-status-review","4.3.11"),
}
def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8-sig"))
def sha(rel):
    return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest().upper()
def classify(root_release, app, iss):
    version=root_release["version"]
    revision=root_release["releaseRevision"]
    match=[name for name, v in LINES.items() if (version,revision)==v[:2]]
    if len(match)!=1:
        raise ValueError("UNRECOGNIZED_RELEASE_LINE_FAIL_CLOSED")
    line=match[0]
    if app["version"]!=version or app["coreVersion"]!=revision:
        raise ValueError("APP_RELEASE_VERSION_DRIFT")
    if f'#define MyAppVersion "{version}"' not in iss:
        raise ValueError("INNO_VERSION_DRIFT")
    if "AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}" not in iss:
        raise ValueError("INSTALLER_APPID_DRIFT")
    if "PrivilegesRequired=lowest" not in iss or "RestartApplications=no" not in iss:
        raise ValueError("INSTALLER_PRIVILEGE_POLICY_DRIFT")
    if line=="R55":
        if root_release["status"]!="R55_PRIVATE_CANDIDATE_NOT_FOR_RELEASE":
            raise ValueError("R55_MUST_REMAIN_UNRELEASED")
        if root_release["installerStatus"]!="R55_PRIVATE_UNSIGNED_UNTESTED":
            raise ValueError("R55_INSTALLER_STATUS_DRIFT")
        if root_release["acceptanceEvidence"]!="evidence/V519_R55_PRIVATE_CANDIDATE.json":
            raise ValueError("R55_EVIDENCE_POINTER_DRIFT")
        if len(load("gateway/manifest.json")["files"])!=18:
            raise ValueError("R55_GATEWAY_COUNT_DRIFT")
        if "PRIVATE_REVIEW_DO_NOT_RELEASE" not in iss:
            raise ValueError("R55_OUTPUT_MUST_REMAIN_PRIVATE")
    if sha("app/manifest.json")!=root_release["appManifestSha256"]:
        raise ValueError("APP_MANIFEST_CHAIN_DRIFT")
    if sha("gateway/manifest.json")!=root_release["gatewayManifestSha256"]:
        raise ValueError("GATEWAY_MANIFEST_CHAIN_DRIFT")
    return line

def main():
    release=load("RELEASE.json")
    app=load("app/manifest.json")
    iss=(ROOT/"windows/installer/FreeNetHub.iss").read_text(encoding="utf-8-sig")
    line=classify(release,app,iss)
    if len(sys.argv)==3 and sys.argv[1]=="--expected" and sys.argv[2]!=line:
        raise SystemExit(f"WRONG_LINE_EXPECTED_{sys.argv[2]}_ACTUAL_{line}")
    if len(sys.argv) not in (1,3):
        raise SystemExit("usage: verify_release_line.py [--expected R53|R55]")
    print(line)
if __name__=="__main__":
    main()
