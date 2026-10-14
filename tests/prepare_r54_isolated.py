"""Prepare versioned R54 release-line metadata only in a detached, clean, exact-base worktree.
This script does NOT install, sign, publish, or change the accepted R53 tree.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

EXPECTED = "e4112be36d6cce97863c59a5dbe6a5d0bcdf5786"
VERSION = "4.3.10"
REVISION = "4.3.10-r54-update-cache-retention"


def main(root: Path) -> None:
    root = root.resolve(strict=True)
    assert root.name.startswith("fnh-r54-") or root.name == "FNH_R54_ISOLATED", "ISOLATION_ROOT_REQUIRED"
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    assert git("rev-parse", "HEAD") == EXPECTED, "SOURCE_SHA_CHANGED"
    assert not git("status", "--porcelain"), "STAGING_MUST_BE_CLEAN"
    manifest = root / "app/manifest.json"
    release = root / "RELEASE.json"
    inno = root / "windows/installer/FreeNetHub.iss"
    a = json.loads(manifest.read_text(encoding="utf-8-sig"))
    r = json.loads(release.read_text(encoding="utf-8-sig"))
    script = inno.read_text(encoding="utf-8-sig")
    assert a["version"] == r["version"] == "4.3.9"
    assert a["coreVersion"] == r["releaseRevision"] == "4.3.9-r53-inno-root-guard"
    assert "#define MyAppVersion \"4.3.9\"" in script
    assert "AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}" in script
    assert "PrivilegesRequired=lowest" in script
    assert "RestartApplications=no" in script
    for row in a["code"]:
        f = root / "app" / row["file"]
        assert f.stat().st_size == row["bytes"], "APP_SIZE_MISMATCH:" + row["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest().upper() == row["sha256"], "APP_SHA_MISMATCH:" + row["file"]
    a["version"] = VERSION
    a["coreVersion"] = REVISION
    a["scope"] = "R54_UPDATE_CACHE_GC_FAILCLOSED+" + a["scope"]
    manifest.write_text(json.dumps(a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest().upper()
    r["version"] = VERSION
    r["releaseRevision"] = REVISION
    r["status"] = "R54_UNSIGNED_WINDOWS_INSTALLER_RELEASE_LINE"
    r["installerStatus"] = "R54_UNSIGNED_VERSIONED_INSTALLER"
    r["acceptanceEvidence"] = "evidence/V449_R54_RELEASE_METADATA_20261014.json"
    r["appManifestSha256"] = manifest_sha
    release.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    replacements = {
        '#define MyAppVersion "4.3.9"': '#define MyAppVersion "4.3.10"',
        r'OutputDir=..\..\delivery\github_v4.3.9': r'OutputDir=..\..\delivery\release_candidate_v4.3.10',
        "OutputBaseFilename=FreeNetHub_4.3.9_R53_Setup": "OutputBaseFilename=FreeNetHub_4.3.10_R54_Setup",
        "VersionInfoVersion=4.3.9.0": "VersionInfoVersion=4.3.10.0",
        "VersionInfoDescription=FreeNet Hub 4.3.9 R53 same-AppId install root fail-closed guard":
            "VersionInfoDescription=FreeNet Hub 4.3.10 R54 bounded installer-cache retention"
    }
    for old, new in replacements.items():
        assert script.count(old) == 1, "INNO_PRESTATE_UNEXPECTED:" + old
        script = script.replace(old, new)
    inno.write_text(script, encoding="utf-8")
    receipt = {
        "schema": 1, "date": "2026-10-14", "status": "UNSIGNED_R54_RELEASE_LINE_SOURCE_CANDIDATE",
        "sourceSHA": EXPECTED, "version": VERSION, "revision": REVISION,
        "appManifestSha256": manifest_sha, "engineSha256": r["engineSha256"],
        "fixedAppId": "BCE83A4E-8897-4D52-A650-BB67A2BB8142",
        "scope": "Source transformation only. Inno build, real fresh install, R53 upgrade, rollback separate."
    }
    evidence = root / "evidence/V449_R54_RELEASE_METADATA_20261014.json"
    evidence.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    assert r["appManifestSha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest().upper()
    print("R54_ISOLATED_METADATA_AND_SOURCE_HASHES_PASS", len(a["code"]), manifest_sha)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_r54_isolated.py <clean detached worktree path>")
    main(Path(sys.argv[1]))
