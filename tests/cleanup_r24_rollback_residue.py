#!/usr/bin/env python3
"""R21 rollback residue: inspect or opt-in quarantine two exact R24-only modules.

The published R21 and R24 archives stay immutable. No network, system service,
browser, or current-session state is changed. Default invocation is read-only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pwd
from pathlib import Path
import re
import socket
import stat
import sys
import tempfile
import zipfile

R21_SHA = "82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A"
R24_SHA = "D76958F80923BFC1B77E406FE00F4CE96CC83A9A54521415DBBDAE53AFFB1824"
R21_VERSION = "4.2.0-linux.21-r54"
R24_VERSION = "4.2.0-linux.24-r57"
R21_RELEASE = "LINUX_4.2.0_R21_R54_WARP_OWNER_CONSENT"
ORPHANS = ("selective_tunnel.py", "tailnet_cfon_gateway.py")
R21_CODE = (
    "freenet_hub_linux.py", "freenet_hub_linux_r37.py",
    "freenet_hub_linux_gtk.py", "nodehub_shared.py", "warp_guard.py",
    "recover_warp_remote.sh", "uninstall.sh",
)
QUARANTINE = ".r24-to-r21-orphan-quarantine"
HEX = re.compile(r"[a-fA-F0-9]{64}\Z")


class Refusal(Exception):
    pass


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def file_owned(path: Path) -> bool:
    try:
        entry = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(entry.st_mode) and entry.st_uid == os.getuid()


def directory_owned(path: Path) -> bool:
    try:
        entry = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISDIR(entry.st_mode) and entry.st_uid == os.getuid()


def app_root(value: str) -> Path:
    root = Path(value).expanduser()
    if (os.name != "posix" or not root.is_absolute()
            or (root.name, root.parent.name, root.parent.parent.name)
            != ("FreeNetHub", "share", ".local")
            or not all(directory_owned(x) for x in (root, root.parent, root.parent.parent))):
        raise Refusal("EXACT_OWNED_USER_LOCAL_APP_ROOT_REQUIRED")
    return root


def verified_package(path: Path, revision: str) -> dict[str, str]:
    expected_sha = {"R21": R21_SHA, "R24": R24_SHA}[revision]
    expected_version = {"R21": R21_VERSION, "R24": R24_VERSION}[revision]
    if not file_owned(path) or sha(path) != expected_sha:
        raise Refusal("FROZEN_" + revision + "_ZIP_SHA_FAILED")
    prefix = "FreeNetHub_4.2.0_Linux_" + revision + "/"
    with zipfile.ZipFile(path) as zipped:
        members = zipped.namelist()
        if (zipped.testzip() is not None or len(members) != len(set(members))
                or any(not n.startswith(prefix) or ".." in Path(n).parts for n in members)):
            raise Refusal("ZIP_ENTRY_OR_INTEGRITY_INVALID_" + revision)
        manifest = json.loads(zipped.read(prefix + "PACKAGE_MANIFEST.json"))
        if manifest.get("version") != expected_version:
            raise Refusal("ZIP_VERSION_MISMATCH_" + revision)
        result = {}
        for row in manifest["files"]:
            name, hashval = row["file"], row["sha256"]
            if (name in result or "/" in name or "\\" in name or name in (".", "..")
                    or not HEX.fullmatch(hashval)
                    or hashlib.sha256(zipped.read(prefix + name)).hexdigest().upper()
                    != hashval.upper()):
                raise Refusal("ZIP_MANIFEST_INVALID_" + revision)
            result[name] = hashval.upper()
        return result


def verify_installed_r21(app: Path, r21: dict[str, str]) -> None:
    receipt = app / "INSTALL.json"
    index = app / "INSTALL.sha256"
    if not file_owned(receipt) or not file_owned(index):
        raise Refusal("R21_INSTALLED_RECEIPT_MISSING")
    info = json.loads(receipt.read_text(encoding="utf-8"))
    if (info.get("version") != R21_VERSION or info.get("release") != R21_RELEASE
            or info.get("integrity_manifest") != "INSTALL.sha256"):
        raise Refusal("ACTIVE_INSTALL_NOT_EXACT_R21")
    rows = {}
    for line in index.read_text(encoding="ascii").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or not HEX.fullmatch(parts[0]):
            raise Refusal("INSTALLED_INDEX_MALFORMED")
        name = parts[1]
        if (not name or name in rows or Path(name).is_absolute()
                or any(p in (".", "..") for p in Path(name).parts)):
            raise Refusal("INSTALLED_INDEX_PATH_UNSAFE")
        p = app / name
        if not file_owned(p) or sha(p) != parts[0].upper():
            raise Refusal("INSTALLED_R21_FILE_INTEGRITY_FAIL_" + name)
        rows[name] = parts[0].upper()
    if any(rows.get(name) != r21.get(name) for name in R21_CODE):
        raise Refusal("INSTALLED_R21_CODE_DIFFERS_FROM_FROZEN_ARCHIVE")


def ensure_idle(app: Path) -> None:
    session = app / "session.json"
    if not file_owned(session):
        raise Refusal("OWNER_SESSION_MISSING_OR_FOREIGN")
    state = json.loads(session.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("mode") or state.get("connected"):
        raise Refusal("ACTIVE_OWNER_SESSION")
    policy = app / "selective/policy.json"
    if policy.exists() or policy.is_symlink():
        if not file_owned(policy):
            raise Refusal("SELECTIVE_POLICY_UNTRUSTED")
        info = json.loads(policy.read_text(encoding="utf-8"))
        if not isinstance(info, dict) or info.get("enabled") is not False:
            raise Refusal("SELECTIVE_POLICY_NOT_DISABLED")
    if (app / "tailnet_cfon_gateway.json").exists():
        raise Refusal("TAILNET_OWNER_STATE_PRESENT")
    # The OS identity, not mutable HOME, identifies the real installed owner.
    # Disposable test homes may be idle while real CFON is operating.
    physical_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    if app == physical_home / ".local/share/FreeNetHub":
        if (physical_home / ".config/systemd/user/freenethub-tailnet-cfon.service").exists():
            raise Refusal("TAILNET_UNIT_PRESENT")
        for port in (19414, 19415):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.15):
                    raise Refusal("ACTIVE_PROXY_PORT_" + str(port))
            except OSError:
                pass
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = (proc / "cmdline").read_bytes().decode("utf-8", errors="replace")
        except OSError:
            continue
        if str(app) in args and any(s in args for s in (
            "freenet_hub_linux.py", "freenet_hub_linux_r37.py",
            "freenet_hub_linux_gtk.py", "tailnet_cfon_gateway.py"
        )):
            raise Refusal("OWNER_APP_PROCESS_STILL_RUNNING")


def inspect(app: Path, expected: dict[str, str]) -> tuple[Path, list[str], list[str]]:
    store = app / QUARANTINE
    if store.exists() or store.is_symlink():
        if not directory_owned(store) or store.stat().st_mode & 0o077:
            raise Refusal("QUARANTINE_DIRECTORY_UNTRUSTED")
        receipt = store / "receipt.json"
        if not file_owned(receipt):
            raise Refusal("QUARANTINE_RECEIPT_MISSING")
        recorded = json.loads(receipt.read_text(encoding="utf-8"))
        if recorded != {"schema": 1, "r21Sha": R21_SHA, "r24Sha": R24_SHA,
                        "modules": expected}:
            raise Refusal("QUARANTINE_RECEIPT_CONFLICT")
        if any(p.name not in (*ORPHANS, "receipt.json") for p in store.iterdir()):
            raise Refusal("QUARANTINE_UNKNOWN_CONTENT")
    current, held = [], []
    for name in ORPHANS:
        for path, found in ((app / name, current), (store / name, held)):
            if path.exists() or path.is_symlink():
                if not file_owned(path) or sha(path) != expected[name]:
                    raise Refusal("FOREIGN_OR_MODIFIED_MODULE_" + name)
                found.append(name)
        if name in current and name in held:
            raise Refusal("MODULE_CONFLICT_BOTH_LOCATIONS_" + name)
    return store, current, held


def init_quarantine(store: Path, expected: dict[str, str]) -> None:
    store.mkdir(mode=0o700)
    payload = {"schema": 1, "r21Sha": R21_SHA, "r24Sha": R24_SHA, "modules": expected}
    fd, tmp = tempfile.mkstemp(prefix=".receipt-", dir=store)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            os.fchmod(file.fileno(), 0o600)
            json.dump(payload, file, indent=2, sort_keys=True)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, store / "receipt.json")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run(app: Path, r21_pkg: Path, r24_pkg: Path, action: str) -> dict:
    r21 = verified_package(r21_pkg, "R21")
    r24 = verified_package(r24_pkg, "R24")
    if any(name in r21 or name not in r24 for name in ORPHANS):
        raise Refusal("R24_ONLY_MODULE_PROVENANCE_NOT_CONFIRMED")
    verify_installed_r21(app, r21)
    expected = {name: r24[name] for name in ORPHANS}
    store, current, held = inspect(app, expected)
    if action == "check":
        return {"status": "DRY_RUN", "eligible": current,
                "quarantined": held, "mutated": False}
    ensure_idle(app)
    if action == "restore":
        if not store.exists():
            raise Refusal("NO_VERIFIED_QUARANTINE_TO_RESTORE")
        if not held:
            return {"status": "ALREADY_RESTORED", "mutated": False}
        restored = []
        try:
            for name in held:
                source, target = store / name, app / name
                if target.exists() or target.is_symlink():
                    raise Refusal("RESTORE_WOULD_OVERWRITE_MODULE_" + name)
                if not file_owned(source) or sha(source) != expected[name]:
                    raise Refusal("QUARANTINE_CHANGED_DURING_RESTORE_" + name)
                os.replace(source, target)
                restored.append(name)
                if not file_owned(target) or sha(target) != expected[name]:
                    raise Refusal("RESTORE_POSTMOVE_INTEGRITY_FAILED_" + name)
        except Exception:
            for name in reversed(restored):
                if file_owned(app / name) and not (store / name).exists():
                    os.replace(app / name, store / name)
            raise
        return {"status": "RESTORED", "modules": restored, "mutated": True}
    if not current:
        return {"status": "ALREADY_QUARANTINED" if held else "NO_RESIDUE",
                "mutated": False}
    if not store.exists():
        init_quarantine(store, expected)
    moved = []
    try:
        for name in current:
            live, quarantined = app / name, store / name
            if not file_owned(live) or sha(live) != expected[name]:
                raise Refusal("MODULE_CHANGED_DURING_APPLY_" + name)
            os.replace(live, quarantined)
            moved.append(name)
            if not file_owned(quarantined) or sha(quarantined) != expected[name]:
                raise Refusal("QUARANTINE_POSTMOVE_INTEGRITY_FAILED_" + name)
    except Exception:
        for name in reversed(moved):
            if file_owned(store / name) and not (app / name).exists():
                os.replace(store / name, app / name)
        raise
    return {"status": "QUARANTINED", "moved": moved,
            "quarantine": str(store), "mutated": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-home", required=True)
    parser.add_argument("--r21-package", type=Path, required=True)
    parser.add_argument("--r24-package", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true",
                      help="Quarantine only if the exact installed R21 is idle")
    mode.add_argument("--restore", action="store_true",
                      help="Reinstate exactly the quarantined files without touching anything else")
    args = parser.parse_args()
    action = "restore" if args.restore else "apply" if args.apply else "check"
    try:
        result = run(app_root(args.app_home), args.r21_package,
                     args.r24_package, action)
    except Refusal as error:
        # A refusal can also be raised during a multi-file move. Even though
        # the helper attempts rollback, never promise it succeeded on error.
        print(json.dumps({"status": "REFUSED", "reason": str(error),
                          "mutationState": "UNVERIFIED"}), file=sys.stderr)
        return 72
    except (OSError, ValueError, KeyError, UnicodeError,
            zipfile.BadZipFile) as error:
        print(json.dumps({"status": "UNRESOLVED", "reason": type(error).__name__,
                          "mutationState": "UNVERIFIED"}), file=sys.stderr)
        return 73
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
