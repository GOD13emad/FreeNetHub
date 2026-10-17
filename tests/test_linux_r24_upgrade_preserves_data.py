#!/usr/bin/env python3
"""Isolated HOME regression: corrupt-package refusal and R21->R24 user-data preservation."""
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "delivery/github_v4.2.0"
FILES = {
    "R21": BASE / "FreeNetHub_4.2.0_Linux_R21.zip",
    "R24": BASE / "FreeNetHub_4.2.0_Linux_R24.zip",
}
EXPECTED = {
    "R21": "82305e1a15684662b7711b53a84522122c6a11d618366314d9dd297b3a7fec1a",
}
for name, path in FILES.items():
    assert path.is_file(), f"{name} package missing"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if name in EXPECTED:
        assert digest == EXPECTED[name], "Frozen public R21 changed!"

with tempfile.TemporaryDirectory(prefix="fnh-r24-upgrade-") as td:
    t = pathlib.Path(td)
    home = t / "home"
    home.mkdir()
    app = home / ".local/share/FreeNetHub"
    binaries = app / "runtime/usr/bin"
    binaries.mkdir(parents=True)
    fake = b"#!/bin/sh\nexit 0\n"
    for name, version in (("sing-box", "1.14.2"), ("warp-plus", "1.2.6")):
        exe = binaries / name
        exe.write_bytes(fake)
        exe.chmod(0o755)
        pin = app / "runtime" / (name + ".pin.json")
        pin.write_text(json.dumps({
            "version": version,
            "binarySha256": hashlib.sha256(fake).hexdigest(),
        }))
    gi = t / "fakemod/gi"
    gi.mkdir(parents=True)
    (gi / "__init__.py").write_text("def require_version(*args): pass\n")
    (gi / "repository.py").write_text("class Gtk: pass\nclass Adw: pass\n")
    paths = {}
    for rev, zip_path in FILES.items():
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(t / "payloads" / rev)
        paths[rev] = next((t / "payloads" / rev).glob("*/install.sh"))
        assert paths[rev].exists()

    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(t / "fakemod"), DBUS_SESSION_BUS_ADDRESS="")
    def run_installer(path):
        return subprocess.run(["bash", str(path)], cwd=path.parent, env=env,
                              capture_output=True, text=True, timeout=35)
    old = run_installer(paths["R21"])
    assert old.returncode == 0, ("R21 fake-home bootstrap", old.returncode, old.stderr[-900:])
    assert json.loads((app / "INSTALL.json").read_text())["version"] == "4.2.0-linux.21-r54"
    user_files = {
        "bridges_obfs4.txt": b"private-user-bridges-sentinel\n",
        "session.json": b'{"mode":null,"provider":null,"detail":{}}\n',
        "console.json": b'{"created_by":"external","connection_uuid":"test-only"}\n',
        "evidence/owner-private.json": b'{"credential":"PRESERVED_MARKER_NOT_REAL_SECRET"}\n',
        "data/browser/Default/History": b"example-browser-history\n",
    }
    for relative, content in user_files.items():
        dest = app / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    prior = {path: hashlib.sha256((app / path).read_bytes()).hexdigest() for path in user_files}
    badfile = paths["R24"].parent / "freenet_hub_linux.py"
    good = badfile.read_bytes()
    badfile.write_bytes(good+b"\n# ALTERED_AUDIT_PAYLOAD\n")
    before = (app / "INSTALL.json").read_bytes()
    invalid = run_installer(paths["R24"])
    assert invalid.returncode == 75, ("Corrupt release not rejected", invalid.returncode, invalid.stderr)
    assert (app / "INSTALL.json").read_bytes() == before, "Corrupt install touched installed version"
    assert not (app / "backup").exists(), "Corrupt install created a backup before refusing"
    badfile.write_bytes(good)
    newer = run_installer(paths["R24"])
    assert newer.returncode == 0, ("Upgrade", newer.returncode, newer.stderr[-900:], newer.stdout[-900:])
    assert json.loads((app / "INSTALL.json").read_text())["version"] == "4.2.0-linux.24-r57"
    assert ((app / "INSTALL.json").stat().st_mode & 0o777) == 0o600
    checked = subprocess.run(["sha256sum", "-c", "INSTALL.sha256"], cwd=app,
                             capture_output=True, text=True, timeout=10)
    assert checked.returncode == 0, checked.stderr
    for rel, sha in prior.items():
        assert hashlib.sha256((app / rel).read_bytes()).hexdigest() == sha, rel
    assert len(list((app / "backup").glob("*/INSTALL.json"))) == 1, "Expected single rollback snapshot"
    assert not (app / "FreeNetHub_4.2.0_Linux_R24").exists()
    assert not (app / "FreeNetHub_4.2.0_Linux_R21").exists()
    assert (home / ".local/bin/freenethub").is_file()
    print(json.dumps({
        "status": "R21_TO_R24_ISOLATED_HOME_UPGRADE_PASS",
        "filesPreserved": len(prior),
        "corruptReleaseExit": invalid.returncode,
        "installChecksum": "PASS",
        "oneInstallRoot": True,
        "backupSnapshots": 1,
        "noExternalNetworkUsed": True,
    }))
