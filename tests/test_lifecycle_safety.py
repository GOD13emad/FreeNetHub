from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_windows_shell_full_exit_uses_verified_cleanup():
    s=(ROOT/"windows/standalone/FreeNetHubShell.cs").read_text(encoding="utf-8-sig")
    assert 'menu.Items.Add("خروج کامل",null,delegate{ExitCleanly();});' in s
    assert 'Uninstall-FreeNetHub.ps1' in s
    assert 'cleanupProcess.ExitCode!=0' in s
    assert 'ExitAll(0);' in s

def test_windows_shell_hosted_close_minimizes_instead_of_destroying():
    s=(ROOT/"app/FreeNetHub.ps1").read_text(encoding="utf-8-sig")
    assert "$script:ShellHosted -and !$script:AllowClose" in s
    assert "$script:Window.WindowState='Minimized'" in s
    close=s.split("$script:Window.Add_Closing",1)[1]
    assert close.index("$script:ShellHosted") < close.index("$script:GatewayTask") < close.index("$script:Task")

def test_windows_update_install_fails_closed_on_active_or_unverified_runtime():
    s=(ROOT/"app/FreeNetHub.ps1").read_text(encoding="utf-8-sig")
    assert "$gateway=Gateway-Refresh" in s
    assert "if(!$gateway)" in s
    assert "[bool]$gateway.running" in s
    assert "$directDpi.active -or $directDpi.stale" in s
    p=(ROOT/"windows/installer/Prepare-Upgrade.ps1").read_text(encoding="utf-8-sig")
    assert "gateway_control.ps1" in p
    assert "directdpi" in p.lower()
    assert "exit 44" in p

def test_linux_close_hides_and_full_exit_is_fail_closed():
    s=(ROOT/"crossplatform/linux/freenet_hub_linux_gtk.py").read_text(encoding="utf-8")
    assert "self.win.set_hide_on_close(True)" in s
    assert 'self.connect("shutdown",self._on_shutdown)' in s
    assert "def request_full_exit(self,*_args):" in s
    assert "def _cleanup_owned_runtime(self):" in s
    assert "def _finish_full_exit(self,result):" in s
    assert 'Gtk.Button(label="خروج کامل")' in s
    assert 'GLib.idle_add(self.request_full_exit,"signal")' in s
    assert 'self.status_title.set_text("خروج کامل متوقف شد")' in s
    assert "self._shutdown_started=True" in s
    assert "self.quit()" in s

def test_windows_standalone_manifest_uses_dual_runtime_and_source_hashes():
    builder=(ROOT/"windows/standalone/Build-Manifest42.py").read_text(encoding="utf-8")
    verifier=(ROOT/"tests/verify_public_tree.py").read_text(encoding="utf-8")
    assert "sourceSha256" in builder
    assert "canonical_sha" in builder
    assert 'row.get("sourceSha256")' in verifier
    assert "hc(p)!=source_sha" in verifier
