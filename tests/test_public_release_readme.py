#!/usr/bin/env python3
"""Local, offline check of the documented public release against accepted evidence.

This checks the pinned R53/R21 release pointer only; it cannot discover future
GitHub releases or confer publisher signing/physical acceptance.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README_FA.md").read_text(encoding="utf-8")
CURRENT = README.split("## نسخه‌های توسعه و پیش‌نمایش", 1)[0]
ENGLISH = (ROOT / "README.md").read_text(encoding="utf-8")
CURRENT_ENGLISH = ENGLISH.split("## Development and Preview Builds", 1)[0]
EVIDENCE = json.loads(
    (ROOT / "evidence/V443_R21_R53_POSTPUBLISH_VERIFICATION_20261014.json").read_text(
        encoding="utf-8"
    )
)
RELEASE = json.loads((ROOT / "RELEASE.json").read_text(encoding="utf-8"))
CONFIRMED = EVIDENCE["confirmed"]
revision = RELEASE["releaseRevision"]
assert RELEASE["version"] == "4.3.9", "Release version drifted; reverify public latest."
assert revision == CONFIRMED["ownerWindows"]["version"], "R53 evidence/release mismatch"
match = re.search(r"-r(\d+)-", revision)
assert match, "Unexpected Windows release revision format"
r_number = match.group(1)
assert r_number == "53", "Update public evidence and guide before promoting a new stable"
tag = CONFIRMED["publicRelease"]
assert tag == f"v{RELEASE['version']}-r{r_number}-windows-stable"
url = f"https://github.com/GOD13emad/FreeNetHub/releases/tag/{tag}"
stable = {
    "tag": url,
    "Windows asset": f"FreeNetHub_{RELEASE['version']}_R{r_number}_Setup.exe",
    "Windows revision": revision,
    "Windows SHA-256": CONFIRMED["windowsR53InstallerSHA256"],
    "Linux asset": "FreeNetHub_4.2.0_Linux_R21.zip",
    "Linux version": CONFIRMED["ownerLinux"]["version"],
    "Linux SHA-256": CONFIRMED["linuxR21SHA256"],
}
for name, value in stable.items():
    assert CURRENT.count(value) == 1, ("fa", name, "missing/duplicated stable value")
    assert CURRENT_ENGLISH.count(value) == 1, ("en", name, "missing/duplicated stable value")
assert "# FreeNet Hub" in README.splitlines()[0]
assert "Windows R53" in README.splitlines()[0] and "Linux R21" in README.splitlines()[0]
assert "Windows R52" not in CURRENT and "Linux R20 —" not in CURRENT
assert "docs/LINUX_ROLLBACK_RESIDUE.md" in README
assert "docs/LINUX_ROLLBACK_RESIDUE.md" in ENGLISH
assert (ROOT / "docs/LINUX_ROLLBACK_RESIDUE.md").is_file()
assert "R57" in README and "R24" in README, "FA preview differentiation missing"
assert "R57" in ENGLISH and "R24" in ENGLISH, "EN preview differentiation missing"
assert "Linux R20 — public" not in CURRENT_ENGLISH
assert "README_FA.md" in ENGLISH and "Windows R53" in ENGLISH.splitlines()[0]
assert "Linux R21" in ENGLISH.splitlines()[0]
print(json.dumps({"status": "PASS", "publicRelease": tag,
                  "checkedCurrentMetadataFields": len(stable) * 2,
                  "languages": ["fa", "en"],
                  "scope": "offline accepted R53/R21 GitHub evidence"}))
