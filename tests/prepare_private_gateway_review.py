"""Build an isolated NONRELEASE R54 package with accepted V463 Gateway sources.

Run only after prepare_r54_isolated.py in a detached R53-base worktree.
Never mutates the owner's active app, routes, published assets or accepted R54 draft.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

SOURCE_GATEWAY_SHA = "B37B9EFCD4DFBAE1AB30D008016B3AE39F1A0261879019534FE18BCE1B083D47"
BASE_SHA = "e4112be36d6cce97863c59a5dbe6a5d0bcdf5786"
REVIEW_NAME = "FreeNetHub_4.3.10_R54_V473_GATEWAY_REVIEW_DO_NOT_RELEASE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main(stage: Path) -> None:
    source = Path(__file__).resolve().parents[1]
    stage = stage.resolve(strict=True)
    if not stage.name.startswith("fnh-r54-v473-"):
        raise RuntimeError("V473_DISPOSABLE_STAGE_NAME_REQUIRED")
    if subprocess.check_output(["git", "-C", str(stage), "rev-parse", "HEAD"], text=True).strip() != BASE_SHA:
        raise RuntimeError("BASE_SHA_NOT_PINNED")
    manifest = source / "gateway/manifest.json"
    if sha(manifest) != SOURCE_GATEWAY_SHA:
        raise RuntimeError("V463_GATEWAY_MANIFEST_NOT_PINNED")
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if len(m["files"]) != 17:
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
    script.write_text(text.replace(before, "OutputBaseFilename=" + REVIEW_NAME), encoding="utf-8")
    if sha(stage / "gateway/manifest.json") != SOURCE_GATEWAY_SHA:
        raise RuntimeError("GATEWAY_MANIFEST_POSTCHECK_FAILED")
    if json.loads(release.read_text(encoding="utf-8"))["gatewayManifestSha256"] != SOURCE_GATEWAY_SHA:
        raise RuntimeError("RELEASE_CHAIN_POSTCHECK_FAILED")
    print("V473_PRIVATE_GATEWAY_STAGE_PREP_PASS", len(m["files"]), SOURCE_GATEWAY_SHA)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_private_gateway_review.py <disposable-stage>")
    main(Path(sys.argv[1]))
