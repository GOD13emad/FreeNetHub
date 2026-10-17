#!/usr/bin/env python3
"""R24->R25 and R25->R24 isolated real-installer reversible acceptance.

R24 accepted preview bytes stay immutable. Preserve private files, refuse
corruption and live sessions, never access OS networks or live owner HOME.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "delivery/github_v4.2.0"
R24 = ASSETS / "FreeNetHub_4.2.0_Linux_R24.zip"
R25 = ASSETS / "FreeNetHub_4.2.0_Linux_R25.zip"
EXPECTED_24 = "D76958F80923BFC1B77E406FE00F4CE96CC83A9A54521415DBBDAE53AFFB1824"
VERSION_25 = "4.2.0-linux.25-r58"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


assert digest(R24) == EXPECTED_24
with tempfile.TemporaryDirectory(prefix="fnh-r25-owner-upgrade-isolated-") as work:
    tmp = Path(work)
    home = tmp / "home"
    home.mkdir(mode=0o700)
    app = home / ".local/share/FreeNetHub"
    binpath = app / "runtime/usr/bin"
    binpath.mkdir(parents=True)
    fake = b"#!/bin/sh\nexit 0\n"
    for binary, version in (("warp-plus", "1.2.6"), ("sing-box", "1.14.2")):
        path = binpath / binary
        path.write_bytes(fake)
        path.chmod(0o755)
        (app / "runtime" / (binary + ".pin.json")).write_text(
            json.dumps({"version": version,
                        "binarySha256": hashlib.sha256(fake).hexdigest()}))
    lib = tmp / "fakegi/gi"
    lib.mkdir(parents=True)
    (lib / "__init__.py").write_text("def require_version(*args): pass\n")
    (lib / "repository.py").write_text("class Gtk: pass\nclass Adw: pass\n")
    paths = {}
    for label, path in (("R24", R24), ("R25", R25)):
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            z.extractall(tmp / label)
        paths[label] = tmp / label / ("FreeNetHub_4.2.0_Linux_" + label)
        assert (paths[label] / "install.sh").is_file()
    env = dict(os.environ, HOME=str(home), DBUS_SESSION_BUS_ADDRESS="",
               PYTHONPATH=str(tmp / "fakegi"), PYTHONDONTWRITEBYTECODE="1")
    def install(label):
        path = paths[label]
        return subprocess.run(["bash", str(path / "install.sh")],
                              cwd=path, env=env, text=True,
                              capture_output=True, timeout=40)

    old = install("R24")
    assert old.returncode == 0, (old.returncode, old.stderr[-400:])
    assert json.loads((app / "INSTALL.json").read_text())["version"] == "4.2.0-linux.24-r57"
    private = {
        "session.json": b'{"mode":null,"provider":null,"detail":{}}\n',
        "selective/policy.json": b'{"schema":1,"enabled":false}\n',
        "settings-r37.json": b'{"tailnetClientPeer":"","customProxy":""}\n',
        "nodes.json": b'{"schema":1,"nodes":[]}\n',
        "bridges_obfs4.txt": b"# protected-marker-for-test-only\n",
        "data/browser/Default/History": b"owner-history-do-not-replace",
        "console.json": b'{"created_by":"external-owner","connection_uuid":"fake"}\n',
    }
    for rel, raw in private.items():
        file = app / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    original = {key: digest(app / key) for key in private}
    original_install = (app / "INSTALL.json").read_bytes()
    # Dedicated private Firefox must be treated as active even though
    # the old core session.json deliberately has no provider mode.
    fake_active = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(30)",
         str(app / "firefox-tailnet-r25")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        protected_browser = install("R25")
        assert protected_browser.returncode == 72, protected_browser.stderr
        assert "FREENET_HUB_TAILNET_CLIENT_BROWSER_ACTIVE" in protected_browser.stderr
        assert (app / "INSTALL.json").read_bytes() == original_install
        assert not (app / "backup").exists()
    finally:
        fake_active.terminate()
        try:fake_active.wait(timeout=3)
        except subprocess.TimeoutExpired:
            fake_active.kill();fake_active.wait(timeout=3)
    corrupted = paths["R25"] / "freenet_hub_linux_r37.py"
    before = corrupted.read_bytes()
    corrupted.write_bytes(before + b"\n# MODIFIED_INVALID_FILE\n")
    denied = install("R25")
    assert denied.returncode == 75, (denied.returncode, denied.stderr[-600:])
    assert (app / "INSTALL.json").read_bytes() == original_install
    assert not (app / "backup").exists()
    corrupted.write_bytes(before)
    newer = install("R25")
    assert newer.returncode == 0, (newer.returncode, newer.stderr[-600:], newer.stdout[-600:])
    reg = json.loads((app / "INSTALL.json").read_text())
    assert reg["version"] == VERSION_25
    assert reg["release"] == "LINUX_4.2.0_R25_R58_PEER_BROWSER_SELECTIVE"
    assert reg["network_mutation_on_install"] is False
    checks = (app / "INSTALL.sha256").read_text().strip().splitlines()
    assert len(checks) == 12, len(checks)
    assert subprocess.run(["sha256sum", "-c", "INSTALL.sha256"], cwd=app,
                          capture_output=True, text=True, timeout=8).returncode == 0
    assert (app / "tailnet_client_browser.py").is_file()
    assert all(digest(app / f) == sha for f, sha in original.items())
    assert len(list((app / "backup").glob("*/INSTALL.json"))) == 1
    assert (home / ".local/bin/freenethub").is_file()
    assert not (app / "tailnet_cfon_gateway.json").exists()
    # No private session may be bypassed by the installer.
    (app / "session.json").write_text('{"mode":"CFON"}\n')
    protected = install("R25")
    assert protected.returncode == 72
    assert "FREENET_HUB_ACTIVE_SESSION" in protected.stderr
    assert json.loads((app / "INSTALL.json").read_text())["version"] == VERSION_25
    (app / "session.json").write_bytes(private["session.json"])
    # Frozen R24 rollback must restore its tested files, preserving user data.
    restored = install("R24")
    assert restored.returncode == 0, (restored.returncode, restored.stderr[-600:])
    assert json.loads((app / "INSTALL.json").read_text())["version"] == "4.2.0-linux.24-r57"
    assert subprocess.run(["sha256sum", "-c", "INSTALL.sha256"], cwd=app,
                          capture_output=True, text=True, timeout=8).returncode == 0
    assert all(digest(app / f) == sha for f, sha in original.items())
    # The frozen R24 installer cannot know the extra R25 module.
    assert (app / "tailnet_client_browser.py").is_file()
    print(json.dumps({
        "status": "PASS", "sequence": ["R24", "R25", "R24"],
        "isolatedHome": True, "privateFilesPreserved": len(private),
        "invalidPackageExit": denied.returncode, "activeSessionGuardExit": protected.returncode,
        "activePrivatePeerBrowserGuardExit": protected_browser.returncode,
        "r25InstallChecksumFiles": len(checks),
        "r25ToR24InertOrphan": "tailnet_client_browser.py",
        "realOwnerHostModified": False, "networkMutation": False,
    }))
