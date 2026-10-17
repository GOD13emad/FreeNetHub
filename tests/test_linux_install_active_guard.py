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


def test_selective_active_refuses_upgrade_without_stopping_tunnel():
    with tempfile.TemporaryDirectory(prefix="fnh-selective-active-") as td:
        home=pathlib.Path(td)
        app=home/".local/share/FreeNetHub"
        (app/"selective").mkdir(parents=True)
        (app/"session.json").write_text('{"mode":null,"provider":null,"detail":{}}')
        (app/"selective/policy.json").write_text('{"schema":1,"enabled":true}')
        ui=app/"freenet_hub_linux_gtk.py"
        ui.write_text("UNMODIFIED_OWNER_UI")
        old=ui.read_bytes()
        proc=subprocess.run(["bash",str(INSTALL)],text=True,capture_output=True,
                            env={**os.environ,"HOME":str(home),"DBUS_SESSION_BUS_ADDRESS":""},
                            timeout=10)
        assert proc.returncode==72,(proc.returncode,proc.stderr)
        assert "FREENET_HUB_SELECTIVE_ACTIVE" in proc.stderr
        assert ui.read_bytes()==old
        assert not (app/"backup").exists()
        assert not (app/"INSTALL.sha256").exists()



def test_tailnet_active_or_corrupt_owner_refuses_upgrade_before_mutation():
    for payload in ('{"schema":1,"enabled":true}', '{"schema":1,"enabled":false}', '{not-json'):
        with tempfile.TemporaryDirectory(prefix="fnh-tailnet-install-") as td:
            home=pathlib.Path(td)
            app=home/".local/share/FreeNetHub"
            app.mkdir(parents=True)
            (app/"session.json").write_text('{"mode":null,"provider":null,"detail":{}}')
            ui=app/"freenet_hub_linux_gtk.py"
            ui.write_text("UNMODIFIED_USER_GUI")
            owner=app/"tailnet_cfon_gateway.json"
            owner.write_text(payload)
            if payload.endswith('false}'):
                # A stopped owner is allowed by policy. Add unowned unit marker
                # so foreign unit is still blocked preflight.
                unit=home/".config/systemd/user/freenethub-tailnet-cfon.service"
                unit.parent.mkdir(parents=True)
                unit.write_text("# FOREIGN SYSTEMD UNIT\n")
            proc=subprocess.run(["bash",str(INSTALL)],capture_output=True,text=True,
                     env={**os.environ,"HOME":str(home),"DBUS_SESSION_BUS_ADDRESS":""},timeout=10)
            assert proc.returncode==72,(payload,proc.returncode,proc.stderr)
            assert "FREENET_HUB_TAILNET_ACTIVE_OR_UNKNOWN" in proc.stderr
            assert ui.read_text()=="UNMODIFIED_USER_GUI"
            assert not (app/"INSTALL.sha256").exists()
            assert not (app/"backup").exists()


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
