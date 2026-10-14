"""R53 release identity and updater compatibility regression (standard library only)."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
release = json.loads((ROOT / "RELEASE.json").read_text(encoding="utf-8-sig"))
app = json.loads((ROOT / "app" / "manifest.json").read_text(encoding="utf-8-sig"))
iss = (ROOT / "windows" / "installer" / "FreeNetHub.iss").read_text(encoding="utf-8-sig")
builder = (ROOT / "tests" / "build_v439_installer.ps1").read_text(encoding="utf-8-sig")
engine = (ROOT / "app" / "engine.py").read_text(encoding="utf-8-sig")
linux = (ROOT / "crossplatform" / "linux" / "freenet_hub_linux_r37.py").read_text(encoding="utf-8-sig")
tag = "v4.3.9-r53-windows-stable"
filename = "FreeNetHub_4.3.9_R53_Setup.exe"
assert release["version"] == app["version"] == "4.3.9"
evidence = json.loads((ROOT / release["acceptanceEvidence"]).read_text(encoding="utf-8-sig"))
assert evidence["version"] == release["version"]
assert evidence["status"] == release["status"]
assert evidence["verificationStatus"] == "UNPROVEN_CANDIDATE"
assert release["releaseRevision"] == app["coreVersion"] == "4.3.9-r53-inno-root-guard"
assert 'AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}' in iss
assert '#define MyAppVersion "4.3.9"' in iss
assert f"OutputBaseFilename={filename.removesuffix('.exe')}" in iss
assert filename in builder
assert "github_v4.3.9" in builder
assert "CheckConflictingInstallRoots" in iss
assert "Result := CheckConflictingInstallRoots;" in iss
assert "https://api.github.com/repos/GOD13emad/FreeNetHub/releases/latest" in engine
assert "remote_n>local_n" in engine
parse_rev = lambda x: int(re.search(r"(?i)(?:^|[-_])r(\d+)(?:[-_]|$)", x).group(1))
assert parse_rev(filename) == 53
assert parse_rev(release["releaseRevision"]) == 53
assert parse_rev("FreeNetHub_4.3.8_R52_Setup.exe") == 52
assert "FreeNetHub_4.2.0_Linux_R20.zip" not in filename
assert "_Linux_R(\\d+)\\.zip$" in linux
print("R53_RELEASE_IDENTITY_AND_REVISION_AWARE_UPDATE_PASS")
