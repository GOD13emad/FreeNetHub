"""An installer must not shut down an active FreeNet Hub browser tunnel."""
import os
import pathlib
import subprocess
import tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
INSTALL=ROOT/"crossplatform"/"linux"/"install.sh"


def test_active_cfon_install_refuses_before_any_file_changes():
    with tempfile.TemporaryDirectory(prefix="fnh-active-guard-") as td:
        home=pathlib.Path(td)
        app=home/".local"/"share"/"FreeNetHub"
        app.mkdir(parents=True)
        session=app/"session.json"
        session.write_text('{"mode":"CFON","provider":"warp-plus","detail":{"scope":"BROWSER"}}')
        ui=app/"freenet_hub_linux_gtk.py"
        ui.write_text("SENTINEL_LEGACY_UI")
        before=(session.read_bytes(),ui.read_bytes())
        proc=subprocess.run(["bash",str(INSTALL)],text=True,capture_output=True,
                            env={**os.environ,"HOME":str(home),"DBUS_SESSION_BUS_ADDRESS":""},
                            timeout=10)
        assert proc.returncode==72,(proc.returncode,proc.stderr[-800:])
        assert "FREENET_HUB_ACTIVE_SESSION" in proc.stderr
        assert (session.read_bytes(),ui.read_bytes())==before
        assert not (app/"backup").exists()
        assert not (app/"INSTALL.sha256").exists()


def test_unreadable_session_fails_closed():
    with tempfile.TemporaryDirectory(prefix="fnh-active-guard-") as td:
        home=pathlib.Path(td)
        app=home/".local"/"share"/"FreeNetHub"
        app.mkdir(parents=True)
        (app/"session.json").write_text("{not-json")
        proc=subprocess.run(["bash",str(INSTALL)],text=True,capture_output=True,
                            env={**os.environ,"HOME":str(home),"DBUS_SESSION_BUS_ADDRESS":""},
                            timeout=10)
        assert proc.returncode==72
        assert "UNREADABLE_SESSION_STATE" in proc.stderr


if __name__=="__main__":
    for name,obj in sorted(globals().copy().items()):
        if name.startswith("test_") and callable(obj):
            obj()
            print(name,"PASS")
