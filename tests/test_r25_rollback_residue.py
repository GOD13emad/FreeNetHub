#!/usr/bin/env python3
"""Exact-owner R25-only leftover cleanup on frozen R21/R24 installations."""
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
BUNDLES = ROOT / "delivery/github_v4.2.0"
FILES = {r: BUNDLES / f"FreeNetHub_4.2.0_Linux_{r}.zip"
         for r in ("R21", "R24", "R25")}
CLEANUP = ROOT / "tests/cleanup_r25_rollback_residue.py"
ORPHAN = "tailnet_client_browser.py"
QUARANTINE = ".r25-to-old-orphan-quarantine"
CHECKSUMS = {
    "R21": "82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A",
    "R24": "D76958F80923BFC1B77E406FE00F4CE96CC83A9A54521415DBBDAE53AFFB1824",
    "R25": "4F035E158F9580F1ACA0554ED1FAE6DC45F6D74FD02F686744433CF35E75AD22",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


class TestR25RollbackResidue(unittest.TestCase):
    def setUp(self):
        if not sys.platform.startswith("linux"):
            self.skipTest("Linux user-local only")
        self.tmp = tempfile.TemporaryDirectory(prefix="fnh-r25-r21-orphan-case-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "user"
        self.home.mkdir(mode=0o700)
        self.app = self.home / ".local/share/FreeNetHub"
        runtime = self.app / "runtime/usr/bin"
        runtime.mkdir(parents=True)
        fake = b"#!/bin/sh\nexit 0\n"
        for binary, version in (("sing-box", "1.14.2"), ("warp-plus", "1.2.6")):
            item = runtime / binary
            item.write_bytes(fake)
            item.chmod(0o755)
            (self.app / "runtime" / (binary + ".pin.json")).write_text(
                json.dumps({"version": version,
                            "binarySha256": hashlib.sha256(fake).hexdigest()}))
        gi = self.root / "fakegi/gi"
        gi.mkdir(parents=True)
        (gi / "__init__.py").write_text("def require_version(*a): pass\n")
        (gi / "repository.py").write_text("class Gtk: pass\nclass Adw: pass\n")
        self.installer = {}
        for rev, path in FILES.items():
            self.assertEqual(sha(path), CHECKSUMS[rev], rev)
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                z.extractall(self.root / "payloads" / rev)
            self.installer[rev] = (self.root / "payloads" / rev
                                   / f"FreeNetHub_4.2.0_Linux_{rev}/install.sh")
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                        PYTHONPATH=str(self.root / "fakegi"), DBUS_SESSION_BUS_ADDRESS="")
        self.install("R21")
        self.install("R25")
        self.install("R21")
        self.session = self.app / "session.json"
        self.session.write_text('{"mode":null,"connected":false}\n')
        selective = self.app / "selective/policy.json"
        selective.parent.mkdir(parents=True, exist_ok=True)
        selective.write_text('{"schema":1,"enabled":false}\n')
        self.sentinel = self.app / "data/owner-preserve.bin"
        self.sentinel.parent.mkdir(parents=True, exist_ok=True)
        self.sentinel.write_bytes(b"DO-NOT-TOUCH-OWNER-STATE\n")
        self.code_before = (self.app / "INSTALL.sha256").read_bytes()
        self.meta_before = (self.app / "INSTALL.json").read_bytes()
        self.sentinel_before = sha(self.sentinel)
        self.orphan_before = sha(self.app / ORPHAN)

    def install(self, revision):
        p = self.installer[revision]
        proc = subprocess.run(["bash", str(p)], cwd=p.parent, env=self.env,
                              capture_output=True, text=True, timeout=35)
        self.assertEqual(proc.returncode, 0, proc.stderr[-600:])

    def call(self, *options, r25=None):
        args = [
            sys.executable, str(CLEANUP), "--app-home", str(self.app),
            "--r21-package", str(FILES["R21"]),
            "--r24-package", str(FILES["R24"]),
            "--r25-package", str(r25 or FILES["R25"]),
            *options,
        ]
        return subprocess.run(args, cwd=ROOT, env=self.env, capture_output=True,
                              text=True, timeout=15)

    def preserved(self, base="R21"):
        self.assertEqual(sha(self.sentinel), self.sentinel_before)
        if base == "R21":
            self.assertEqual((self.app / "INSTALL.sha256").read_bytes(), self.code_before)
            self.assertEqual((self.app / "INSTALL.json").read_bytes(), self.meta_before)
        self.assertEqual(
            subprocess.run(["sha256sum", "--status", "-c", "INSTALL.sha256"],
                           cwd=self.app, capture_output=True, timeout=8).returncode, 0)

    def test_r21_dry_apply_restore_idempotent(self):
        test = self.call()
        self.assertEqual(test.returncode, 0, test.stderr)
        got = json.loads(test.stdout)
        self.assertEqual(got["status"], "DRY_RUN")
        self.assertEqual(got["eligible"], [ORPHAN])
        self.assertEqual(got["installed"], "R21")
        self.assertFalse((self.app / QUARANTINE).exists())
        first = self.call("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["status"], "QUARANTINED")
        q = self.app / QUARANTINE
        self.assertFalse((self.app / ORPHAN).exists())
        self.assertEqual(sha(q / ORPHAN), self.orphan_before)
        self.assertEqual(q.stat().st_mode & 0o777, 0o700)
        self.assertEqual((q / "receipt.json").stat().st_mode & 0o777, 0o600)
        again = self.call("--apply")
        self.assertEqual(json.loads(again.stdout)["status"], "ALREADY_QUARANTINED")
        restore = self.call("--restore")
        self.assertEqual(restore.returncode, 0, restore.stderr)
        self.assertEqual(json.loads(restore.stdout)["status"], "RESTORED")
        self.assertEqual(sha(self.app / ORPHAN), self.orphan_before)
        self.assertEqual(json.loads(self.call("--restore").stdout)["status"],
                         "ALREADY_RESTORED")
        self.preserved()

    def test_r24_frozen_installed_target_eligible(self):
        self.install("R24")
        result = self.call("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        rec = json.loads((self.app / QUARANTINE / "receipt.json").read_text())
        self.assertEqual(rec["target"], "R24")
        self.assertEqual(rec["targetSHA256"], CHECKSUMS["R24"])
        self.assertEqual(self.call("--restore").returncode, 0)
        self.assertEqual(sha(self.app / ORPHAN), self.orphan_before)
        self.preserved("R24")

    def test_active_session_fails_closed(self):
        self.session.write_text('{"mode":"CFON","connected":true}\n')
        result = self.call("--apply")
        self.assertEqual(result.returncode, 72)
        self.assertIn("ACTIVE_OWNER_SESSION", result.stderr)
        self.assertTrue((self.app / ORPHAN).exists())
        self.assertFalse((self.app / QUARANTINE).exists())
        self.preserved()

    def test_r25_installed_is_not_eligible(self):
        self.install("R25")
        denied = self.call("--apply")
        self.assertEqual(denied.returncode, 72)
        self.assertIn("INSTALLED_VERSION_NOT_PINNED", denied.stderr)
        self.assertFalse((self.app / QUARANTINE).exists())

    def test_wrong_r25_archive_rejected(self):
        bad = self.root / "changed.zip"
        bad.write_bytes(FILES["R25"].read_bytes() + b"ALTERED")
        result = self.call("--apply", r25=bad)
        self.assertEqual(result.returncode, 72)
        self.assertIn("R25_FROZEN_ZIP_SHA_FAILED", result.stderr)
        self.assertTrue((self.app / ORPHAN).exists())

    def test_modified_orphan_not_quarantined(self):
        p = self.app / ORPHAN
        p.write_bytes(p.read_bytes() + b"\n# OWNER EDITED\n")
        result = self.call("--apply")
        self.assertEqual(result.returncode, 72)
        self.assertIn("R25_ORPHAN_FOREIGN_SYMLINK_OR_MODIFIED", result.stderr)
        self.assertFalse((self.app / QUARANTINE).exists())
        self.preserved()

    def test_symlink_never_followed(self):
        p = self.app / ORPHAN
        foreign = self.root / "owner.py"
        foreign.write_bytes(p.read_bytes())
        p.unlink()
        p.symlink_to(foreign)
        result = self.call("--apply")
        self.assertEqual(result.returncode, 72)
        self.assertIn("R25_ORPHAN_FOREIGN_SYMLINK_OR_MODIFIED", result.stderr)
        self.assertTrue(foreign.is_file())
        self.preserved()

    def test_guard_active_owner_peer_browser(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time;time.sleep(10)",
             str(self.app / ORPHAN)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            result = self.call("--apply")
            self.assertEqual(result.returncode, 72)
            self.assertIn("R25_PEER_BROWSER_OR_MODULE_PROCESS_ACTIVE", result.stderr)
            self.assertTrue((self.app / ORPHAN).exists())
        finally:
            proc.terminate()
            proc.wait(timeout=3)
        self.preserved()

    def test_running_firefox_argument_with_exact_profile_blocks(self):
        proc = subprocess.Popen(
            ["bash", "-c", 'exec -a firefox python3 -c "import time;time.sleep(10)" _ "$1"',
             "owner-test", str(self.app / "firefox-tailnet-r25")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            result = self.call("--apply")
            self.assertEqual(result.returncode, 72)
            self.assertIn("R25_PEER_BROWSER_OR_MODULE_PROCESS_ACTIVE", result.stderr)
            self.assertTrue((self.app / ORPHAN).exists())
            self.assertFalse((self.app / QUARANTINE).exists())
        finally:
            proc.terminate()
            proc.wait(timeout=3)
        self.preserved()

    def test_tampered_frozen_base_code_refused(self):
        p = self.app / "freenet_hub_linux.py"
        p.write_bytes(p.read_bytes() + b"\n# counterfeit code\n")
        x = self.call("--apply")
        self.assertEqual(x.returncode, 72)
        self.assertIn("INSTALLED_SOURCE_HASH_MISMATCH", x.stderr)
        self.assertTrue((self.app / ORPHAN).exists())

    def test_quarantine_conflict_and_foreign_receipt(self):
        x = self.call("--apply")
        self.assertEqual(x.returncode, 0, x.stderr)
        self.install("R24")
        y = self.call("--restore")
        self.assertEqual(y.returncode, 72)
        self.assertIn("R25_QUARANTINE_RECEIPT_CONFLICT", y.stderr)
        self.preserved("R24")

    def test_restore_before_quarantine_requires_receipt(self):
        denied = self.call("--restore")
        self.assertEqual(denied.returncode, 72)
        self.assertIn("R25_NO_PINNED_QUARANTINE_TO_RESTORE", denied.stderr)
        self.assertTrue((self.app / ORPHAN).exists())
        self.preserved()


if __name__ == "__main__":
    unittest.main(verbosity=2)
