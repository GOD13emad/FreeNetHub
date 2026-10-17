#!/usr/bin/env python3
"""Regression for SHA-gated, opt-in R24-only orphan-module rollback cleanup."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "delivery/github_v4.2.0"
R21 = RELEASES / "FreeNetHub_4.2.0_Linux_R21.zip"
R24 = RELEASES / "FreeNetHub_4.2.0_Linux_R24.zip"
TOOL = ROOT / "tests/cleanup_r24_rollback_residue.py"
ORPHANS = ("selective_tunnel.py", "tailnet_cfon_gateway.py")
STORE = ".r24-to-r21-orphan-quarantine"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class RollbackResidue(unittest.TestCase):
    def setUp(self):
        if sys.platform != "linux":
            self.skipTest("Linux-only owner-local installation")
        self.temp = tempfile.TemporaryDirectory(prefix="fnh-r24-rollback-residue-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "user"
        self.home.mkdir(mode=0o700)
        self.app = self.home / ".local/share/FreeNetHub"
        bindir = self.app / "runtime/usr/bin"
        bindir.mkdir(parents=True)
        fake = b"#!/bin/sh\nexit 0\n"
        for name, version in (("sing-box", "1.14.2"), ("warp-plus", "1.2.6")):
            binary = bindir / name
            binary.write_bytes(fake)
            binary.chmod(0o755)
            (self.app / "runtime" / (name + ".pin.json")).write_text(
                json.dumps({"version": version, "binarySha256":
                            hashlib.sha256(fake).hexdigest()}))
        gi = self.root / "fakemod/gi"
        gi.mkdir(parents=True)
        (gi / "__init__.py").write_text("def require_version(*a): pass\n")
        (gi / "repository.py").write_text("class Gtk: pass\nclass Adw: pass\n")
        self.installer = {}
        for revision, archive in (("R21", R21), ("R24", R24)):
            with zipfile.ZipFile(archive) as zipped:
                self.assertIsNone(zipped.testzip())
                zipped.extractall(self.root / "payloads" / revision)
            self.installer[revision] = (self.root / "payloads" / revision
                                        / ("FreeNetHub_4.2.0_Linux_" + revision)
                                        / "install.sh")
        self.env = dict(os.environ, HOME=str(self.home),
                        PYTHONPATH=str(self.root / "fakemod"),
                        DBUS_SESSION_BUS_ADDRESS="", PYTHONDONTWRITEBYTECODE="1")
        self.install("R21")
        self.install("R24")
        self.install("R21")
        self.session = self.app / "session.json"
        self.session.write_text('{"schema":1,"mode":null,"connected":false}\n')
        policy = self.app / "selective/policy.json"
        policy.parent.mkdir(parents=True, exist_ok=True)
        policy.write_text('{"schema":1,"enabled":false}\n')
        self.sentinel = self.app / "data/other-user-state.txt"
        self.sentinel.parent.mkdir(parents=True, exist_ok=True)
        self.sentinel.write_bytes(b"PRIVATE_TEST_SENTINEL_ONLY\n")
        self.sentinel_sha = digest(self.sentinel.read_bytes())
        for module in ORPHANS:
            self.assertTrue((self.app / module).is_file())
        self.old_version = (self.app / "INSTALL.json").read_bytes()
        self.old_checksums = (self.app / "INSTALL.sha256").read_bytes()

    def install(self, revision):
        path = self.installer[revision]
        result = subprocess.run(["bash", str(path)], cwd=path.parent,
                                env=self.env, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0,
                         f"Installer {revision} failed: {result.stderr[-700:]}")
        expected = {"R21": "4.2.0-linux.21-r54",
                    "R24": "4.2.0-linux.24-r57"}[revision]
        self.assertEqual(json.loads((self.app / "INSTALL.json").read_text())["version"],
                         expected)

    def cmd(self, *additional, r21=R21, r24=R24):
        result = subprocess.run([
            sys.executable, str(TOOL), "--app-home", str(self.app),
            "--r21-package", str(r21), "--r24-package", str(r24),
            *additional
        ], cwd=ROOT, env=self.env, capture_output=True, text=True, timeout=15)
        return result

    def check_unchanged(self):
        self.assertEqual(digest(self.sentinel.read_bytes()), self.sentinel_sha)
        self.assertEqual((self.app / "INSTALL.json").read_bytes(), self.old_version)
        self.assertEqual((self.app / "INSTALL.sha256").read_bytes(),
                         self.old_checksums)

    def test_exact_quarantine_dry_run_and_idempotent_apply(self):
        before = {p: digest((self.app / p).read_bytes()) for p in ORPHANS}
        result = self.cmd()
        self.assertEqual(result.returncode, 0, result.stderr)
        outcome = json.loads(result.stdout)
        self.assertEqual(outcome["status"], "DRY_RUN")
        self.assertEqual(set(outcome["eligible"]), set(ORPHANS))
        self.assertFalse(outcome["mutated"])
        self.assertFalse((self.app / STORE).exists())
        for p in ORPHANS:
            self.assertEqual(digest((self.app / p).read_bytes()), before[p])
        applied = self.cmd("--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(json.loads(applied.stdout)["status"], "QUARANTINED")
        store = self.app / STORE
        self.assertEqual(store.stat().st_mode & 0o777, 0o700)
        self.assertEqual((store / "receipt.json").stat().st_mode & 0o777, 0o600)
        for p in ORPHANS:
            self.assertFalse((self.app / p).exists())
            self.assertEqual(digest((store / p).read_bytes()), before[p])
        self.check_unchanged()
        repeat = self.cmd("--apply")
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertEqual(json.loads(repeat.stdout)["status"], "ALREADY_QUARANTINED")
        self.check_unchanged()

    def test_active_session_fails_before_any_move(self):
        self.session.write_text('{"schema":1,"mode":"CFON","connected":true}\n')
        result = self.cmd("--apply")
        self.assertEqual(result.returncode, 72)
        self.assertIn("ACTIVE_OWNER_SESSION", result.stderr)
        self.assertFalse((self.app / STORE).exists())
        self.assertTrue(all((self.app / p).exists() for p in ORPHANS))
        self.check_unchanged()

    def test_modified_module_rejected_without_touching_other(self):
        path = self.app / ORPHANS[0]
        path.write_bytes(path.read_bytes() + b"MODIFIED\n")
        rejected = self.cmd("--apply")
        self.assertEqual(rejected.returncode, 72)
        self.assertIn("FOREIGN_OR_MODIFIED_MODULE", rejected.stderr)
        self.assertFalse((self.app / STORE).exists())
        self.assertTrue((self.app / ORPHANS[1]).is_file())
        self.check_unchanged()

    def test_symlink_refused(self):
        path = self.app / ORPHANS[0]
        target = self.root / "foreign.py"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        refused = self.cmd("--apply")
        self.assertEqual(refused.returncode, 72)
        self.assertIn("FOREIGN_OR_MODIFIED_MODULE", refused.stderr)
        self.assertFalse((self.app / STORE).exists())
        self.check_unchanged()

    def test_zip_digest_pinning_rejects_fake_archive(self):
        bad = self.root / "r24-corrupted.zip"
        bad.write_bytes(R24.read_bytes() + b"\nALTERED")
        rejected = self.cmd("--apply", r24=bad)
        self.assertEqual(rejected.returncode, 72)
        self.assertIn("FROZEN_R24_ZIP_SHA_FAILED", rejected.stderr)
        self.assertFalse((self.app / STORE).exists())
        self.check_unchanged()

    def test_installed_code_tamper_rejected(self):
        code = self.app / "freenet_hub_linux.py"
        code.write_bytes(code.read_bytes() + b"\nOWNER_EDITED\n")
        rejected = self.cmd("--apply")
        self.assertEqual(rejected.returncode, 72)
        self.assertIn("INSTALLED_R21_FILE_INTEGRITY_FAIL", rejected.stderr)
        self.assertTrue(all((self.app / p).is_file() for p in ORPHANS))
        self.check_unchanged()

    def test_partial_quarantine_reconciles_exact_remaining_file(self):
        first = self.cmd("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        store = self.app / STORE
        moved = ORPHANS[0]
        os.replace(store / moved, self.app / moved)
        repeat = self.cmd("--apply")
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertEqual(json.loads(repeat.stdout)["moved"], [moved])
        self.assertFalse((self.app / moved).exists())
        self.assertEqual(self.cmd("--apply").returncode, 0)
        self.check_unchanged()

    def test_conflicting_backup_manifest_blocks_replay(self):
        self.assertEqual(self.cmd("--apply").returncode, 0)
        receipt = self.app / STORE / "receipt.json"
        data = json.loads(receipt.read_text())
        data["r24Sha"] = "0" * 64
        receipt.write_text(json.dumps(data))
        rejected = self.cmd("--apply")
        self.assertEqual(rejected.returncode, 72)
        self.assertIn("QUARANTINE_RECEIPT_CONFLICT", rejected.stderr)
        self.check_unchanged()


    def test_explicit_restore_is_reversible_and_idempotent(self):
        initial = {f: digest((self.app / f).read_bytes()) for f in ORPHANS}
        apply = self.cmd("--apply")
        self.assertEqual(apply.returncode, 0, apply.stderr)
        restored = self.cmd("--restore")
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(json.loads(restored.stdout)["status"], "RESTORED")
        for f in ORPHANS:
            self.assertEqual(digest((self.app / f).read_bytes()), initial[f])
            self.assertFalse((self.app / STORE / f).exists())
        again = self.cmd("--restore")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(again.stdout)["status"], "ALREADY_RESTORED")
        quarantine_again = self.cmd("--apply")
        self.assertEqual(quarantine_again.returncode, 0, quarantine_again.stderr)
        self.assertEqual(json.loads(quarantine_again.stdout)["status"], "QUARANTINED")
        self.check_unchanged()

    def test_restore_refuses_active_session(self):
        self.assertEqual(self.cmd("--apply").returncode, 0)
        self.session.write_text('{"schema":1,"mode":"CFON","connected":true}\n')
        denied = self.cmd("--restore")
        self.assertEqual(denied.returncode, 72)
        self.assertIn("ACTIVE_OWNER_SESSION", denied.stderr)
        self.assertTrue(all((self.app / STORE / x).is_file() for x in ORPHANS))
        self.check_unchanged()

    def test_recovery_of_one_partially_restored_file(self):
        self.assertEqual(self.cmd("--apply").returncode, 0)
        store = self.app / STORE
        os.replace(store / ORPHANS[0], self.app / ORPHANS[0])
        restored = self.cmd("--restore")
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(json.loads(restored.stdout)["modules"], [ORPHANS[1]])
        self.assertTrue(all((self.app / f).is_file() for f in ORPHANS))
        self.assertFalse(any((store / f).exists() for f in ORPHANS))
        self.check_unchanged()


if __name__ == "__main__":
    unittest.main(verbosity=2)
