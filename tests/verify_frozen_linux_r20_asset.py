#!/usr/bin/env python3
"""Fail closed if the accepted public Linux R20 asset is replaced or misidentified."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

root = Path(__file__).resolve().parent.parent
asset = root / "delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R20.zip"
expected = "5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B"
if not asset.is_file():
    raise SystemExit("FROZEN_R20_PUBLIC_ASSET_MISSING")
digest = hashlib.sha256(asset.read_bytes()).hexdigest().upper()
if digest != expected:
    raise SystemExit("FROZEN_R20_RELEASE_HASH_MISMATCH")
with zipfile.ZipFile(asset) as z:
    base="FreeNetHub_4.2.0_Linux_R20/"
    manifest=json.loads(z.read(base+"PACKAGE_MANIFEST.json"))
    assert manifest["version"] == "4.2.0-linux.20-r47", "FROZEN_VERSION_MISMATCH"
    assert len(manifest["files"]) >= 20, "FROZEN_MANIFEST_TRUNCATED"
    files={f["file"]:f for f in manifest["files"]}
    for relative in ("freenet_hub_linux.py","warp_guard.py","install_warp_official.sh","recover_warp_remote.sh"):
        data=z.read(base+relative)
        sha=hashlib.sha256(data).hexdigest().upper()
        if sha != files[relative]["sha256"] or len(data) != files[relative]["bytes"]:
            raise SystemExit("FROZEN_INTERNAL_MANIFEST_MISMATCH:"+relative)
print(json.dumps({"status":"FROZEN_LINUX_R20_PUBLIC_ASSET_PASS","size":asset.stat().st_size,"sha256":digest}))
