from pathlib import Path

R=Path(__file__).resolve().parents[1]

def text(rel):
    return (R/rel).read_text(encoding="utf-8-sig")

def test_normal_launcher_is_explicitly_non_admin_and_no_runtime_bootstrap():
    manifest=text("windows/standalone/FreeNetHubShell.manifest")
    shell=text("windows/standalone/FreeNetHubShell.cs")
    iss=text("windows/installer/FreeNetHub.iss")
    assert 'requestedExecutionLevel level="asInvoker" uiAccess="false"' in manifest
    assert "PrivilegesRequired=lowest" in iss
    assert "ValidateDependencies(script,ps)" in shell
    assert "Setup-WindowsDependencies.ps1" not in shell
    assert "InstallMissingRuntime" not in shell
    assert "Verb = \"runas\"" not in shell
    assert "Verb=\"runas\"" not in shell

def test_online_update_is_revision_aware_verified_and_per_user():
    engine=text("app/engine.py")
    ui=text("app/FreeNetHub.ps1")
    iss=text("windows/installer/FreeNetHub.iss")
    assert "https://api.github.com/repos/GOD13emad/FreeNetHub/releases/latest" in engine
    assert "UPDATE_NOT_NEWER_THAN_CURRENT" in engine
    assert "UPDATE_SHA256_METADATA_MISSING" in engine
    assert "UPDATE_HASH_MISMATCH" in engine
    assert "curl.exe" in engine and "--noproxy" in engine
    assert "Install-VerifiedUpdate" in ui
    assert "$psi.UseShellExecute=$false" in ui
    assert "StartupUpdateChecked=$false" in ui
    assert "Start-Work 'UpdateCheck'" in ui
    assert "DefaultDirName={localappdata}\\Programs\\FreeNetHub" in iss
    assert "PrivilegesRequired=lowest" in iss

def test_r39_installer_freezes_noadmin_launcher_inputs():
    builder=text("tests/build_r38_direct_method_installer.ps1")
    for rel in (
        "windows\\standalone\\FreeNetHub.exe",
        "windows\\standalone\\FreeNetHubShell.cs",
        "windows\\standalone\\FreeNetHubShell.manifest",
        "windows\\standalone\\MANIFEST.json",
    ):
        assert rel in builder
    assert "FreeNetHub_4.2.0_R39_OnlineNoAdmin_Setup.exe" in builder
