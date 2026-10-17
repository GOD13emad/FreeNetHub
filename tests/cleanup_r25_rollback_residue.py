#!/usr/bin/env python3
"""Inspect, quarantine, or restore the exact R25-only module after R21/R24 rollback.

Separate user-local helper; never modify accepted R21/R24/R25 packages or
perform a downgrade. Default mode is read-only. Mutations require an idle,
exact-SHA, owner-owned R21 or R24 installation and do not delete file bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import zipfile

import cleanup_r24_rollback_residue as prior

R25_SHA = "4F035E158F9580F1ACA0554ED1FAE6DC45F6D74FD02F686744433CF35E75AD22"
R25_VERSION = "4.2.0-linux.25-r58"
R25_RELEASE = "LINUX_4.2.0_R25_R58_PEER_BROWSER_SELECTIVE"
R24_RELEASE = "LINUX_4.2.0_R24_R57_OWNER_TAILNET_CFON"
MODULE = "tailnet_client_browser.py"
STORE = ".r25-to-old-orphan-quarantine"
SCHEMA = 1
BASES = {
    "R21": (prior.R21_VERSION, prior.R21_RELEASE, prior.R21_SHA),
    "R24": (prior.R24_VERSION, R24_RELEASE, prior.R24_SHA),
}


def frozen_r25(path: Path) -> dict[str, str]:
    if not prior.file_owned(path) or prior.sha(path) != R25_SHA:
        raise prior.Refusal("R25_FROZEN_ZIP_SHA_FAILED")
    with zipfile.ZipFile(path) as archive:
        prefix = "FreeNetHub_4.2.0_Linux_R25/"
        names = archive.namelist()
        if (archive.testzip() is not None or len(names) != len(set(names))
                or any(not x.startswith(prefix) or ".." in Path(x).parts
                       for x in names)):
            raise prior.Refusal("R25_ZIP_MEMBERS_UNTRUSTED")
        manifest = json.loads(archive.read(prefix + "PACKAGE_MANIFEST.json"))
        if manifest.get("version") != R25_VERSION or manifest.get("release") != R25_RELEASE:
            raise prior.Refusal("R25_MANIFEST_VERSION_UNEXPECTED")
        members: dict[str, str] = {}
        for entry in manifest["files"]:
            name, h = entry["file"], entry["sha256"]
            if (name in members or name in ("..", ".") or "/" in name
                    or "\\" in name or not prior.HEX.fullmatch(h)):
                raise prior.Refusal("R25_MANIFEST_INVALID_PATH_OR_HASH")
            if hashlib.sha256(archive.read(prefix + name)).hexdigest().upper() != h.upper():
                raise prior.Refusal("R25_MANIFEST_FILE_HASH_MISMATCH")
            members[name] = h.upper()
        if MODULE not in members:
            raise prior.Refusal("R25_EXCLUSIVE_MODULE_NOT_FOUND")
        return members


def installed_old(app: Path, r21: dict[str, str], r24: dict[str, str]) -> str:
    """Match installed version *and* the immutable base package's code bytes."""
    metadata, index = app / "INSTALL.json", app / "INSTALL.sha256"
    if not prior.file_owned(metadata) or not prior.file_owned(index):
        raise prior.Refusal("INSTALLED_BASE_METADATA_MISSING_OR_FOREIGN")
    info = json.loads(metadata.read_text(encoding="utf-8"))
    rev = next((x for x, (version, release, _) in BASES.items()
                if info.get("version") == version and info.get("release") == release),
               None)
    if rev is None or info.get("integrity_manifest") != "INSTALL.sha256":
        raise prior.Refusal("INSTALLED_VERSION_NOT_PINNED_R21_OR_R24")
    source = r21 if rev == "R21" else r24
    hashes: dict[str, str] = {}
    for line in index.read_text(encoding="ascii").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or not prior.HEX.fullmatch(parts[0]):
            raise prior.Refusal("INSTALLED_SOURCE_INDEX_MALFORMED")
        name = parts[1]
        if (not name or name in hashes or Path(name).is_absolute()
                or "\\" in name or any(p in ("..", ".") for p in Path(name).parts)):
            raise prior.Refusal("INSTALLED_INDEX_PATH_UNTRUSTED")
        target = app / name
        if not prior.file_owned(target) or prior.sha(target) != parts[0].upper():
            raise prior.Refusal("INSTALLED_SOURCE_HASH_MISMATCH_" + name)
        hashes[name] = parts[0].upper()
    required = prior.R21_CODE + (
        ("selective_tunnel.py", "tailnet_cfon_gateway.py") if rev == "R24" else ()
    )
    if any(hashes.get(name) != source.get(name) for name in required):
        raise prior.Refusal("INSTALLED_BASE_NOT_EXACT_FROZEN_SOURCE")
    if MODULE in hashes or MODULE in source:
        raise prior.Refusal("R25_ONLY_MODULE_MISDECLARED")
    return rev


def ensure_no_peer_browser(app: Path) -> None:
    """Guard the R25 profile even when a frozen older session says idle."""
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            raw = (process / "cmdline").read_bytes()
        except OSError:
            continue
        # Only a Firefox executable with the dedicated-profile argument or
        # a Python interpreter executing our installed module is an owner.
        # A parent `bash -c` string mentioning the name is *not* evidence.
        args = [x for x in raw.decode("utf-8", "replace").split("\x00") if x]
        if not args:
            continue
        executable = Path(args[0]).name.lower()
        own_firefox = ("firefox" in executable and
                       any("firefox-tailnet-r25" in x for x in args[1:]))
        own_module = (executable.startswith("python") and
                      any(str(app) in x and MODULE in x for x in args[1:]))
        if own_firefox or own_module:
            raise prior.Refusal("R25_PEER_BROWSER_OR_MODULE_PROCESS_ACTIVE")


def snapshot(app: Path, expected: str, base: str, base_sha: str):
    vault = app / STORE
    receipt = {
        "schema": SCHEMA, "target": base, "targetSHA256": base_sha,
        "R25SHA256": R25_SHA, "module": MODULE, "moduleSHA256": expected,
    }
    if vault.exists() or vault.is_symlink():
        if not prior.directory_owned(vault) or vault.stat().st_mode & 0o077:
            raise prior.Refusal("R25_QUARANTINE_DIRECTORY_UNTRUSTED")
        track = vault / "receipt.json"
        if not prior.file_owned(track) or json.loads(track.read_text()) != receipt:
            raise prior.Refusal("R25_QUARANTINE_RECEIPT_CONFLICT")
        if any(p.name not in (MODULE, "receipt.json") for p in vault.iterdir()):
            raise prior.Refusal("R25_QUARANTINE_UNKNOWN_CONTENT")
    live = app / MODULE
    held = vault / MODULE
    for path in (live, held):
        if path.exists() or path.is_symlink():
            if not prior.file_owned(path) or prior.sha(path) != expected:
                raise prior.Refusal("R25_ORPHAN_FOREIGN_SYMLINK_OR_MODIFIED")
    if (live.exists() or live.is_symlink()) and (held.exists() or held.is_symlink()):
        raise prior.Refusal("R25_ORPHAN_IN_BOTH_PLACES")
    return vault, live, held, receipt


def quarantine_receipt(vault: Path, receipt: dict) -> None:
    vault.mkdir(mode=0o700)
    fd, temp = tempfile.mkstemp(prefix=".receipt-", dir=vault)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, vault / "receipt.json")
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def run(app: Path, r21zip: Path, r24zip: Path, r25zip: Path, action: str) -> dict:
    base21 = prior.verified_package(r21zip, "R21")
    base24 = prior.verified_package(r24zip, "R24")
    preview = frozen_r25(r25zip)
    if MODULE in base21 or MODULE in base24:
        raise prior.Refusal("R25_ONLY_PROVENANCE_CONFLICT")
    target = installed_old(app, base21, base24)
    vault, live, held, receipt = snapshot(
        app, preview[MODULE], target, BASES[target][2])
    if action == "check":
        return {
            "status": "DRY_RUN", "installed": target,
            "eligible": [MODULE] if live.exists() else [],
            "quarantined": [MODULE] if held.exists() else [],
            "mutated": False,
        }
    prior.ensure_idle(app)
    ensure_no_peer_browser(app)
    if action == "restore":
        if not vault.exists():
            raise prior.Refusal("R25_NO_PINNED_QUARANTINE_TO_RESTORE")
        if not held.exists():
            return {"status": "ALREADY_RESTORED", "mutated": False}
        if live.exists() or live.is_symlink():
            raise prior.Refusal("R25_RESTORE_DESTINATION_OCCUPIED")
        os.replace(held, live)
        if not prior.file_owned(live) or prior.sha(live) != preview[MODULE]:
            # Preserve evidence of uncertain movement; never claim reverted.
            raise prior.Refusal("R25_RESTORE_POSTMOVE_HASH_UNVERIFIED")
        return {"status": "RESTORED", "module": MODULE, "mutated": True}
    if not live.exists():
        return {"status": "ALREADY_QUARANTINED" if held.exists()
                else "NO_RESIDUE", "mutated": False}
    if not vault.exists():
        quarantine_receipt(vault, receipt)
    if not prior.file_owned(live) or prior.sha(live) != preview[MODULE]:
        raise prior.Refusal("R25_MODULE_CHANGED_BEFORE_QUARANTINE")
    os.replace(live, held)
    if not prior.file_owned(held) or prior.sha(held) != preview[MODULE]:
        raise prior.Refusal("R25_QUARANTINE_POSTMOVE_HASH_UNVERIFIED")
    return {"status": "QUARANTINED", "module": MODULE,
            "mutated": True, "quarantine": str(vault)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app-home", required=True)
    p.add_argument("--r21-package", type=Path, required=True)
    p.add_argument("--r24-package", type=Path, required=True)
    p.add_argument("--r25-package", type=Path, required=True)
    act = p.add_mutually_exclusive_group()
    act.add_argument("--apply", action="store_true")
    act.add_argument("--restore", action="store_true")
    args = p.parse_args()
    action = "restore" if args.restore else "apply" if args.apply else "check"
    try:
        data = run(prior.app_root(args.app_home), args.r21_package,
                   args.r24_package, args.r25_package, action)
    except prior.Refusal as err:
        print(json.dumps({"status": "REFUSED", "reason": str(err),
                          "mutationState": "UNVERIFIED"}), file=sys.stderr)
        return 72
    except (OSError, KeyError, ValueError, UnicodeError,
            zipfile.BadZipFile) as err:
        print(json.dumps({"status": "UNRESOLVED", "kind": type(err).__name__,
                          "mutationState": "UNVERIFIED"}), file=sys.stderr)
        return 73
    print(json.dumps(data, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
