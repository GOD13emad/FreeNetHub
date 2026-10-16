"""Build an isolated NONRELEASE R54 package with V485 hash-pinned Gateway sources.

Run only after prepare_r54_isolated.py in a detached R53-base worktree.
Never mutates the owner's active app, routes, published assets or accepted R54 draft.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

SOURCE_GATEWAY_SHA = "3FEE796C3C94B88CE77B1078683A56166A19B8F060F5866CDA2E8D62E3350028"
BASE_SHA = "e4112be36d6cce97863c59a5dbe6a5d0bcdf5786"
REVIEW_NAME = "FreeNetHub_4.3.10_R54_V481_GATEWAY_REVIEW_DO_NOT_RELEASE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main(stage: Path) -> None:
    source = Path(__file__).resolve().parents[1]
    stage = stage.resolve(strict=True)
    if not stage.name.startswith("fnh-r54-v481-"):
        raise RuntimeError("V481_DISPOSABLE_STAGE_NAME_REQUIRED")
    if subprocess.check_output(["git", "-C", str(stage), "rev-parse", "HEAD"], text=True).strip() != BASE_SHA:
        raise RuntimeError("BASE_SHA_NOT_PINNED")
    manifest = source / "gateway/manifest.json"
    if sha(manifest) != SOURCE_GATEWAY_SHA:
        raise RuntimeError("V485_GATEWAY_MANIFEST_NOT_PINNED")
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if len(m["files"]) != 18:
        raise RuntimeError("GATEWAY_FILE_COUNT_CHANGED")
    for e in m["files"]:
        rel = Path(e["file"])
        if rel.is_absolute() or ".." in rel.parts:
            raise RuntimeError("GATEWAY_TRAVERSAL_REJECTED")
        src = source / "gateway" / rel
        dst = stage / "gateway" / rel
        if len(src.read_bytes()) != e["bytes"] or sha(src) != e["sha256"]:
            raise RuntimeError("GATEWAY_AUTHORITY_CHANGED:" + e["file"])
        dst.write_bytes(src.read_bytes())
        if sha(dst) != e["sha256"]:
            raise RuntimeError("GATEWAY_STAGE_COPY_CHANGED")
    (stage / "gateway/manifest.json").write_bytes(manifest.read_bytes())
    release = stage / "RELEASE.json"
    obj = json.loads(release.read_text(encoding="utf-8"))
    if obj["version"] != "4.3.10" or obj["releaseRevision"] != "4.3.10-r54-update-cache-retention":
        raise RuntimeError("NOT_VERSIONED_R54")
    obj["gatewayManifestSha256"] = SOURCE_GATEWAY_SHA
    release.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    script = stage / "windows/installer/FreeNetHub.iss"
    text = script.read_text(encoding="utf-8")
    before = "OutputBaseFilename=FreeNetHub_4.3.10_R54_Setup"
    if text.count(before) != 1:
        raise RuntimeError("INNO_OUTPUT_ANCHOR_CHANGED")
    # R54 baseline Inno has an explicit Gateway file list (not a glob).
    # Only patch the disposable NONRELEASE stage to include the newly
    # hash-pinned DNS watchdog; never mutate the public R53 installer source.
    stop_line = r'Source: "..\..\gateway\stop_elevated.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion'
    watchdog_line = stop_line.replace("stop_elevated.ps1", "dns_guard_watchdog.ps1")
    if text.count(stop_line) != 1 or "dns_guard_watchdog.ps1" in text:
        raise RuntimeError("INNO_GATEWAY_WATCHDOG_ENTRY_ANCHOR_CHANGED")
    if not any(e["file"] == "dns_guard_watchdog.ps1" for e in m["files"]):
        raise RuntimeError("DNS_WATCHDOG_NOT_IN_GATEWAY_MANIFEST")
    text = text.replace(stop_line, stop_line + "\n" + watchdog_line)
    text = text.replace(before, "OutputBaseFilename=" + REVIEW_NAME)
    script.write_text(text, encoding="utf-8")
    if watchdog_line not in script.read_text(encoding="utf-8"):
        raise RuntimeError("PRIVATE_INNO_WATCHDOG_NOT_PACKAGED")
    if sha(stage / "gateway/manifest.json") != SOURCE_GATEWAY_SHA:
        raise RuntimeError("GATEWAY_MANIFEST_POSTCHECK_FAILED")
    if json.loads(release.read_text(encoding="utf-8"))["gatewayManifestSha256"] != SOURCE_GATEWAY_SHA:
        raise RuntimeError("RELEASE_CHAIN_POSTCHECK_FAILED")
    print("V481_PRIVATE_GATEWAY_STAGE_PREP_PASS", len(m["files"]), SOURCE_GATEWAY_SHA)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_private_gateway_review.py <disposable-stage>")
    main(Path(sys.argv[1]))
