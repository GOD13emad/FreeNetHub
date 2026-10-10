#!/usr/bin/env python3
"""Fail-closed, read-only Inno payload ownership/license inventory.
This does NOT certify source licenses, exports, driver trust, or SignPath admission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
EXTS = {".exe", ".dll", ".ocx", ".sys", ".ps1", ".psm1", ".psd1"}
UPSTREAM_HINTS = {
    "app/directdns/": "LICENSE-ctrld.txt",
    "app/directdpi/tools/": "LICENSE-zapret.txt",
    "windows/runtime/": None,
}
SOURCE = re.compile(r'^\s*Source:\s*"([^"]+)"', re.IGNORECASE)


def contained(path: Path) -> Path:
    path = path.resolve(strict=True)
    path.relative_to(ROOT.resolve(strict=True))
    if not path.is_file() or path.is_symlink():
        raise ValueError("UNSAFE_PACKAGE_FILE")
    return path


def scanned_files() -> list[str]:
    iss = ROOT / "windows/installer/FreeNetHub.iss"
    section = ""
    found = set()
    for line in iss.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line.lower()
        if section != "[files]":
            continue
        match = SOURCE.match(line)
        if not match:
            continue
        raw = match.group(1).replace("\\", "/")
        if "*" in raw:
            if raw.count("*") != 1 or not raw.endswith("/*"):
                raise ValueError("UNSUPPORTED_PACKAGE_WILDCARD: " + raw)
            base = (iss.parent / raw[:-2]).resolve(strict=True)
            base.relative_to(ROOT.resolve(strict=True))
            for p in base.rglob("*"):
                if p.is_file() and p.suffix.lower() in EXTS:
                    found.add(contained(p).relative_to(ROOT).as_posix())
        else:
            p = contained(iss.parent / raw)
            if p.suffix.lower() in EXTS:
                found.add(p.relative_to(ROOT).as_posix())
    if not found:
        raise ValueError("INNO_CODE_INVENTORY_EMPTY")
    return sorted(found)


def classify(path: str) -> dict:
    third_party = (
        path.startswith("app/directdns/")
        or path.startswith("app/directdpi/tools/")
        or path.startswith("windows/runtime/")
    )
    companion = None
    if third_party:
        for prefix, license_file in UPSTREAM_HINTS.items():
            if path.startswith(prefix):
                if prefix == "app/directdns/":
                    companion = "app/directdns/" + str(license_file)
                elif prefix == "app/directdpi/tools/":
                    companion = "app/directdpi/" + str(license_file)
                break
    p = ROOT / path
    row = {
        "path": path,
        "ownership": "UPSTREAM_REVIEW_REQUIRED" if third_party else "FIRST_PARTY_CANDIDATE",
        "bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest().upper(),
        "licenseNoticeCandidate": companion,
        "noticeExists": bool(companion and (ROOT / companion).is_file()),
        "legalPermission": "UNVERIFIED" if third_party else "SOURCE_RIGHTS_UNCONFIRMED",
    }
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError("REFUSE_TO_WRITE_INSIDE_SOURCE_TREE")
    if output.exists():
        raise ValueError("REFUSE_BLIND_OVERWRITE")
    entries = [classify(p) for p in scanned_files()]
    upstream = [p for p in entries if p["ownership"] == "UPSTREAM_REVIEW_REQUIRED"]
    licenses = [name for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md") if (ROOT / name).is_file()]
    report = {
        "schema": 1,
        "scope": "EXACT_Inno_Files_section_source_payload",
        "result": "OSS_SIGNPATH_ELIGIBILITY_HOLD",
        "projectWideLicenseCandidates": licenses,
        "licenseApprovedByRightsOwner": False,
        "artifactCount": len(entries),
        "upstreamCount": len(upstream),
        "unreviewedUpstreamCount": len(upstream),
        "hardGates": [
            "PUBLISHER_IRAN_RESIDENCY_ELIGIBILITY_UNKNOWN",
            "OWNER_APPROVED_OSI_LICENSE_NOT_ESTABLISHED",
            "ALL_UPSTREAM_LICENSE_RIGHTS_NOT_VALIDATED",
            "SOURCE_TO_BINARY_REPRODUCIBILITY_NOT_PROVEN",
            "SIGNPATH_FOUNDATION_ACCEPTANCE_NOT_RECEIVED",
            "SIGNED_INSTALLER_SAC_NOT_TESTED",
        ],
        "limitations": [
            "Inno Source globs evaluated against tracked checkout, not installed runtime or on-demand downloads",
            "Notice file presence is NOT proof of an OSI license or legal redistribution approval",
            "Third-party binaries may legally be shipped unsigned if properly OSS licensed under Foundation rules; must not re-sign their upstream binaries",
            "SHA256 and file extensions are not malware/AV or kernel trust attestations",
        ],
        "artifacts": entries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "artifacts": len(entries), "upstream": len(upstream), "licenseCandidates": licenses}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, UnicodeError) as exc:
        print("SIGNPATH_INVENTORY_AUDIT_FAILED:", str(exc), file=sys.stderr)
        raise SystemExit(1)
