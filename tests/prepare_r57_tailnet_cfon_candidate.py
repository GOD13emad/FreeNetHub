#!/usr/bin/env python3
"""Create an isolated, versioned Windows R57 candidate, never an R53 overwrite.

The source checkout and previous public release remain read-only. The generated
directory is intentionally external to the repository. Run on a disposable CI
runner; no installer, network or user settings are changed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile


VERSION = "4.3.13"
REVISION = "4.3.13-r57-tailnet-cfon-selective-routing"
INSTALLER = "FreeNetHub_4.3.13_R57_SELECTIVE_Setup.exe"
APP_ID = "AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}"
PINNED_HELPER = "98BD0A564EA8055960D3A5B6C8CB3B5737DA391D88846F7562621B8E8DC1656C"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def parse_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_one(value, old, new):
    if value.count(old) != 1:
        raise ValueError("R57_UNEXPECTED_INSTALLER_PRESTATE: " + old)
    return value.replace(old, new)


def prepare(source_root: Path, destination: Path, expected_sha: str):
    source_root = source_root.resolve(strict=True)
    # An allowed staging destination must have a predictable name and live
    # below the runner's explicit temp authority, not inside a user's install.
    runner_tmp = os.environ.get("RUNNER_TEMP")
    if not runner_tmp:
        raise ValueError("R57_RUNNER_TEMP_REQUIRED")
    dest_parent = destination.parent.resolve(strict=True)
    root = Path(runner_tmp).resolve(strict=True)
    if dest_parent != root:
        raise ValueError("R57_STAGE_MUST_USE_RUNNER_TEMP")
    if destination.name != "fnh-r57-selective-stage" or destination.exists():
        raise ValueError("R57_STAGE_PREEXISTS_OR_WRONG_NAME")
    if len(expected_sha) != 40 or not re.fullmatch("[a-f0-9]{40}", expected_sha):
        raise ValueError("R57_EXPECTED_SHA_INVALID")
    got = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip()
    if got != expected_sha:
        raise ValueError("R57_SOURCE_SHA_MISMATCH")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=source_root).strip():
        raise ValueError("R57_SOURCE_NOT_CLEAN")

    code = parse_json(source_root / "app" / "manifest.json")
    release = parse_json(source_root / "RELEASE.json")
    if (code.get("version"), code.get("coreVersion")) != ("4.3.9", "4.3.9-r53-inno-root-guard"):
        raise ValueError("R57_APP_BASELINE_NOT_R53")
    if (release.get("version"), release.get("releaseRevision")) != ("4.3.9", "4.3.9-r53-inno-root-guard"):
        raise ValueError("R57_RELEASE_BASELINE_NOT_R53")
    if not {"selective_route_windows.py", "selective_http_bridge.py"}.issubset({r["file"] for r in code["code"]}):
        raise ValueError("R57_MISSING_SELECTIVE_CODE")

    stage_created = False
    fd, temp_tar = tempfile.mkstemp(prefix="fnh-r57-source-", suffix=".tar", dir=dest_parent)
    os.close(fd)
    try:
        subprocess.run(["git", "archive", "--format=tar", "--output", temp_tar, "HEAD"],
                       cwd=source_root, check=True)
        destination.mkdir()
        stage_created = True
        with tarfile.open(temp_tar, "r") as archive:
            for member in archive.getmembers():
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or member.issym() or member.islnk():
                    raise ValueError("R57_UNSAFE_GIT_ARCHIVE_MEMBER")
            archive.extractall(path=destination, filter="data")

        stage_app = destination / "app" / "manifest.json"
        staged_manifest = parse_json(stage_app)
        for row in staged_manifest["code"]:
            file = destination / "app" / str(row["file"])
            blob = file.read_bytes()
            if len(blob) != row["bytes"] or sha(blob) != str(row["sha256"]):
                raise ValueError("R57_SOURCE_MANIFEST_BAD_" + str(row["file"]))
        frozen_helper = destination / "windows" / "installer" / "Prepare-Upgrade.ps1"
        if sha(frozen_helper.read_bytes()) != PINNED_HELPER:
            raise ValueError("R57_HISTORIC_HELPER_MUTATED")

        if "WIN_SELECTIVE_TAILNET_CFON_R57_SOURCE_CANDIDATE_NOT_RELEASED" not in staged_manifest.get("scope",""):
            raise ValueError("R57_SOURCE_GOOGLE_403_SCOPE_MISSING")
        staged_manifest["version"] = VERSION
        staged_manifest["coreVersion"] = REVISION
        staged_manifest["scope"] = (
            staged_manifest["scope"].replace(
                "WIN_SELECTIVE_TAILNET_CFON_R57_SOURCE_CANDIDATE_NOT_RELEASED",
                "WIN_SELECTIVE_R57_ISOLATED_NOT_PUBLIC"
            )
        )
        write_json(stage_app, staged_manifest)
        staged_release = parse_json(destination / "RELEASE.json")
        staged_release["version"] = VERSION
        staged_release["releaseRevision"] = REVISION
        staged_release["status"] = "R57_WINDOWS_ISOLATED_UNSIGNED_NOT_PUBLIC"
        staged_release["installerStatus"] = "R57_ISOLATED_CANDIDATE_FOR_CI_ONLY"
        staged_release["installerSha256"] = None
        staged_release["appManifestSha256"] = sha(stage_app.read_bytes())
        staged_release["windowsSelectiveSourceCandidate"]["status"] = "ISOLATED_R57_CANDIDATE_NOT_PUBLIC"
        staged_release["windowsSelectiveSourceCandidate"]["installer"] = "PENDING_EXACT_BINARY_FRESH_UPGRADE_ROLLBACK"
        staged_release["windowsSelectiveSourceCandidate"]["sourceHeadSha"] = expected_sha
        if "WINDOWS_SELECTIVE_HTTPS_CONNECT_PAC" not in staged_release.get("scope", []):
            staged_release["scope"].append("WINDOWS_SELECTIVE_HTTPS_CONNECT_PAC")
        write_json(destination / "RELEASE.json", staged_release)

        spec = destination / "windows" / "installer" / "FreeNetHub.iss"
        iss = spec.read_text(encoding="utf-8")
        if APP_ID not in iss or "PrivilegesRequired=lowest" not in iss:
            raise ValueError("R57_INSTALLER_AUTHORITY_CHANGED")
        if "ExtractTemporaryFile('Prepare-SelectiveUpgrade.ps1')" not in iss:
            raise ValueError("R57_SELECTIVE_ROLLBACK_GUARD_MISSING")
        if "ExtractTemporaryFile('Prepare-Upgrade.ps1')" not in iss:
            raise ValueError("R57_FROZEN_ROLLBACK_GUARD_MISSING")
        edits = (
            ('#define MyAppVersion "4.3.9"', f'#define MyAppVersion "{VERSION}"'),
            (r"OutputDir=..\..\delivery\github_v4.3.9",
             r"OutputDir=..\..\delivery\release_candidate_v4.3.13"),
            ("OutputBaseFilename=FreeNetHub_4.3.9_R53_Setup",
             f"OutputBaseFilename={INSTALLER.removesuffix('.exe')}"),
            ("VersionInfoVersion=4.3.9.0", "VersionInfoVersion=4.3.13.0"),
            ("VersionInfoDescription=FreeNet Hub 4.3.9 R53 same-AppId install root fail-closed guard",
             "VersionInfoDescription=FreeNet Hub 4.3.13 R57 scoped PAC domain selective candidate"),
        )
        for old, new in edits:
            iss = replace_one(iss, old, new)
        spec.write_text(iss, encoding="utf-8")

        prepared = {
            "schema": 1, "status": "ISOLATED_SOURCE_CANDIDATE",
            "sourceSHA": expected_sha, "version": VERSION, "revision": REVISION,
            "installer": INSTALLER, "publicRelease": False, "publisherSigned": False,
            "immutableHelperSha256": PINNED_HELPER,
            "appManifestSha256": sha(stage_app.read_bytes()),
            "releaseSha256": sha((destination / "RELEASE.json").read_bytes()),
        }
        # Persist every asserted field before emitting the receipt: callers must
        # not mistake a stdout-only PASS for persisted source verification.
        prepared["installerBoundCodeHashes"] = "PASS"
        write_json(destination / "R57_ISOLATED_BUILD_SOURCE.json", prepared)
        return prepared
    except Exception:
        if stage_created:
            import shutil
            shutil.rmtree(destination)
        raise
    finally:
        Path(temp_tar).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    result = prepare(Path(__file__).resolve().parents[1],
                     Path(args.stage), args.source_sha)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
