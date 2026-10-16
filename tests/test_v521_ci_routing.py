"""Regression: historical release identities never silently become R55 acceptance."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fnh_release_line",ROOT/"tests/verify_release_line.py")
classifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)

class ReleaseRoutingTests(unittest.TestCase):
    def test_local_line_is_explicit_r55_only(self):
        self.assertEqual(classifier.classify(
            classifier.load("RELEASE.json"),
            classifier.load("app/manifest.json"),
            (ROOT/"windows/installer/FreeNetHub.iss").read_text(encoding="utf-8-sig"),
        ),"R55")

    def test_reject_revision_and_untrusted_promotion(self):
        r=classifier.load("RELEASE.json")
        a=classifier.load("app/manifest.json")
        iss=(ROOT/"windows/installer/FreeNetHub.iss").read_text(encoding="utf-8-sig")
        for patch in ({"releaseRevision":"4.3.12-r56-future"},
                      {"status":"R55_PUBLIC_RELEASE"},
                      {"installerStatus":"SIGNED"},
                      {"gatewayManifestSha256":"0"*64}):
            mutated=dict(r,**patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                classifier.classify(mutated,a,iss)

    def test_r53_acceptance_immutable_and_r55_dedicated(self):
        ci=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
        private=(ROOT/".github/workflows/r55-private-acceptance.yml").read_text(encoding="utf-8")
        historical=(ROOT/".github/workflows/v465-private-gateway-review.yml").read_text(encoding="utf-8")
        self.assertIn("python tests/test_r53_release_identity.py",ci)
        self.assertIn("run: ./tests/build_v439_installer.ps1",ci)
        self.assertIn("needs.release-line.outputs.line == 'R53'",ci)
        self.assertIn("needs.release-line.outputs.line == 'R55'",ci)
        self.assertIn("uses: ./.github/workflows/r55-private-acceptance.yml",ci)
        self.assertIn("needs.windows-installer-r55.result == 'success'",ci)
        self.assertIn("SIMULATOR_BOOT_TIMEOUT_OR_FAILURE",ci)
        self.assertIn("alarm 720; exec @ARGV",ci)
        self.assertIn("needs.windows-installer-fresh.result == 'skipped'",ci)
        self.assertIn("workflow_call:",private)
        self.assertIn("r54-to-r55-to-r54:",private)
        self.assertIn("R55_EXACT_SAME_BINARY_UPGRADE_ROLLBACK_FRESH_PASS",private)
        self.assertIn("R55_EXACT_BINARY_CHANGED_AFTER_ROLLBACK",private)
        self.assertIn("R54_UNINSTALL_LEFT_APPID_REGISTRATION",private)
        self.assertIn("sameBinaryFreshInstall=$true",private)
        self.assertIn("440BFCE884F1B21E2ADA55EE3727786C2504EF500AF0530D1BE36C186EFEDBB5",historical)
        self.assertIn("if: needs.source-line.outputs.line == 'R53'",historical)

    def test_disposable_native_probe_is_bounded_and_requires_cleanup(self):
        wf=(ROOT/".github/workflows/r55-native-disposable.yml").read_text(encoding="utf-8")
        watchdog=(ROOT/"tests/r55_native_disposable_watchdog.ps1").read_text(encoding="utf-8")
        for token in ("R55_NATIVE_INDEPENDENT_WATCHDOG_ARMED",
                      "NATIVE_WATCHDOG_CLEANUP_UNVERIFIED",
                      "R55_NATIVE_START_GATEWAY_ERROR",
                      "R55_NATIVE_STOP_GATEWAY_ERROR",
                      "R55_NATIVE_DIRECT_CLEANUP=",
                      "NATIVE_CONTROLLER_STILL_RUNNING_AFTER_175S",
                      "R55_NATIVE_STOP_TIMEOUT_65S",
                      "DISPOSABLE_NATIVE_LEFT_NETWORK_MUTATIONS",
                      "DISPOSABLE_NATIVE_DEFAULT_ROUTE_NOT_RESTORED"):
            with self.subTest(token=token): self.assertIn(token,wf)
        for token in ("Stop-Process -Id $StartPid -Force",
                      "stop_elevated.ps1",
                      "TIMEOUT_CLEANUP_VERIFIED",
                      "FINAL_NETWORK_STATE_UNVERIFIED",
                      "not_a_native_pass"):
            with self.subTest(token=token): self.assertIn(token,watchdog)
        self.assertNotIn("R55_DISPOSABLE_NATIVE_START_STOP_PASS",watchdog)

    def test_native_dns53_disposable_lifecycle_is_fail_closed(self):
        wf=(ROOT/".github/workflows/r55-native-dns53-disposable.yml").read_text(encoding="utf-8")
        for marker in ("candidate/r55-v519-private-review",
                       "python tests/verify_release_line.py --expected R55",
                       "--dns-mode native",
                       "FreeNetHub-PC-DNS53-Guard-UDP-Wired",
                       "FreeNetHub-PC-DNS53-Guard-TCP-Wired",
                       "FreeNetHub-PC-DNS53-Guard-UDP-Wireless",
                       "FreeNetHub-PC-DNS53-Guard-TCP-Wireless",
                       "GUARD_OWNER_IDENTITY_UNVERIFIED",
                       "NATIVE_DNS53_RESIDUAL_NETWORK_MUTATION",
                       "NATIVE_DNS53_ROUTE_NOT_RESTORED",
                       "NATIVE_DNS53_STOP_NOT_PASS",
                       "R55_NATIVE_DNS53_GUARD_AND_STOP_PASS"):
            with self.subTest(marker=marker): self.assertIn(marker,wf)
        self.assertNotIn("PHYSICAL_WIFI_UDP53_PASS",wf)

if __name__=="__main__":
    unittest.main(verbosity=2)
