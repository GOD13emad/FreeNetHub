from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ISS=(ROOT/"windows/installer/FreeNetHub.iss").read_text(encoding="utf-8-sig")

def _prepare_block():
    return ISS.split("function PrepareToInstall(var NeedsRestart: Boolean): String;",1)[1].split("procedure CurStepChanged",1)[0]

def test_v43_identity_and_single_public_installer_name():
    assert '#define MyAppVersion "4.3.0"' in ISS
    assert r"OutputDir=..\..\delivery\github_v4.3.0" in ISS
    assert "OutputBaseFilename=FreeNetHub_4.3.0_R43_Setup" in ISS
    assert "VersionInfoVersion=4.3.0.0" in ISS

def test_fresh_install_skips_upgrade_guard_before_extracting_helper():
    block=_prepare_block()
    fresh="if not DirExists(ExpandConstant('{app}')) then"
    helper="ExtractTemporaryFile('Prepare-Upgrade.ps1');"
    assert fresh in block
    assert helper in block
    assert block.index(fresh) < block.index(helper)

def test_upgrade_helper_uses_existing_temp_working_directory():
    block=_prepare_block()
    assert "Exec(P, Params, ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode)" in block
    assert "Exec(P, Params, ExpandConstant('{app}')" not in block
    assert "SysErrorMessage(ResultCode)" in block

def test_upgrade_guard_still_blocks_known_active_runtime():
    block=_prepare_block()
    assert "if ResultCode = 42 then begin" in block
    helper=(ROOT/"windows/installer/Prepare-Upgrade.ps1").read_text(encoding="utf-8-sig")
    assert "exit 42" in helper
    assert "directdpi" in helper.lower()
def test_hosted_ci_requires_exact_fresh_install_gate():
    workflow=(ROOT/".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "windows-installer-fresh:" in workflow
    assert "Fresh install exact artifact into absent app directory" in workflow
    needs=workflow.split("  virtual-acceptance:",1)[1].split("    runs-on:",1)[0]
    assert "- windows-installer-fresh" in needs
