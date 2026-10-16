#!/usr/bin/env python3
"""V462 isolated mixed-platform GitHub Latest updater regression; zero network."""
import importlib.util
import json
import sys
from pathlib import Path

r = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(r / "crossplatform/linux"))  # Package-local legacy module import
spec = importlib.util.spec_from_file_location("fnh_v462_linux", r / "crossplatform/linux/freenet_hub_linux_r37.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FakeResponse:
    def __init__(self, obj):
        self.payload = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, count=-1):
        return self.payload[:count] if count >= 0 else self.payload

asset = {
    "name": "FreeNetHub_4.2.0_Linux_R21.zip",
    "size": 254833,
    "digest": "sha256:82305e1a15684662b7711b53a84522122c6a11d618366314d9dd297b3a7fec1a",
    "browser_download_url": "https://github.com/GOD13emad/FreeNetHub/releases/download/test/FreeNetHub_4.2.0_Linux_R21.zip",
}
windows = {
    "name": "FreeNetHub_4.3.10_R54_Setup.exe",
    "size": 24272803,
    "digest": "sha256:6d3f46c952efcb0bb653454da39f6e80754997bd15cb11376fc19e4535bf2db5",
}
draft_as_future_latest = {
    "tag_name": "v4.3.10-r54-windows-release-review",
    "published_at": "SIMULATED_ONLY_NOT_PUBLIC",
    "assets": [windows, asset],
}

old_open, old_version = module.urllib.request.urlopen, module.VERSION
module.VERSION = "4.2.0-linux.21-r54"  # immutable historical fixture
try:
    module.urllib.request.urlopen = lambda *args, **kwargs: FakeResponse(draft_as_future_latest)
    same = module.update_check()
    assert same["ok"] and same["localRevision"] == 21
    assert same["remoteRevision"] == 21 and not same["updateAvailable"]
    assert same["linuxAsset"]["name"] == asset["name"]

    module.VERSION = "4.2.0-linux.20-r47"
    older = module.update_check()
    assert older["ok"] and older["localRevision"] == 20
    assert older["remoteRevision"] == 21 and older["updateAvailable"]
    module.VERSION = old_version

    missing = dict(draft_as_future_latest, assets=[windows])
    module.urllib.request.urlopen = lambda *args, **kwargs: FakeResponse(missing)
    absent = module.update_check()
    assert absent["ok"] and absent["remoteRevision"] is None
    assert absent["linuxAsset"] is None and not absent["updateAvailable"]
finally:
    module.urllib.request.urlopen = old_open
    module.VERSION = old_version

print("V462_MIXED_WINDOWS_R54_LINUX_R21_UPDATER_3_CASES_PASS")
