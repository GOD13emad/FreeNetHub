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
        self.assertIn("needs.windows-installer-fresh.result == 'skipped'",ci)
        self.assertIn("workflow_call:",private)
        self.assertIn("r54-to-r55-to-r54:",private)
        self.assertIn("440BFCE884F1B21E2ADA55EE3727786C2504EF500AF0530D1BE36C186EFEDBB5",historical)
        self.assertIn("if: needs.source-line.outputs.line == 'R53'",historical)

if __name__=="__main__":
    unittest.main(verbosity=2)
