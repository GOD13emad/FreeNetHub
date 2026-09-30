import json
#!/usr/bin/env python3
import hashlib
from pathlib import Path

R=Path(__file__).resolve().parents[1]
D=R/"app"/"directdpi"
DNS=R/"app"/"directdns"

EXPECTED_DPI={
    "tools/winws.exe":"A14BFF1DF6234EA555D2E0C61B589F0707C0B12D6C9B7EECCDA76012154996E8",
    "tools/WinDivert.dll":"C1E060EE19444A259B2162F8AF0F3FE8C4428A1C6F694DCE20DE194AC8D7D9A2",
    "tools/WinDivert64.sys":"8DA085332782708D8767BCACE5327A6EC7283C17CFB85E40B03CD2323A90DDC2",
    "tools/cygwin1.dll":"103104A52E5293CE418944725DF19E2BF81AD9269B9A120D71D39028E821499B",
}
EXPECTED_DNS={
    "ctrld.exe":"FC966FD7DD5EE850A9709F632789CFB5BBC06C45D903D24B8ECFCE3306B658CD",
    "ctrld.toml":"2E1AF2EF934367465B15284DE93016B839849D717F9A8DC4AC18858FC123EAE2",
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def test_pinned_runtime_complete():
    for rel,h in EXPECTED_DPI.items():
        p=D/rel
        assert p.is_file(), rel
        assert sha(p)==h, rel
    for rel,h in EXPECTED_DNS.items():
        p=DNS/rel
        assert p.is_file(), rel
        assert sha(p)==h, rel
    assert (D/"LICENSE-zapret.txt").is_file()
    assert "MIT License" in (D/"LICENSE-zapret.txt").read_text(encoding="utf-8")
    assert (DNS/"LICENSE-ctrld.txt").is_file()
    assert "MIT License" in (DNS/"LICENSE-ctrld.txt").read_text(encoding="utf-8")

def test_direct_dns_template_is_ipv6_loopback_and_encrypted():
    c=(DNS/"ctrld.toml").read_text(encoding="utf-8-sig")
    assert 'ip = "::1"' in c
    assert "port = 53" in c
    assert 'endpoint = "https://76.76.10.11/p0"' in c
    assert 'bootstrap_ip = "76.76.10.11"' in c
    assert 'type = "doh"' in c
    assert 'intercept_mode = "off"' in c
    assert "127.0.0.1" not in c
    assert "1053" not in c

def test_start_is_fail_closed_direct_only_and_uses_ctrld():
    s=(D/"Start-DirectDpi.ps1").read_text(encoding="utf-8-sig")
    # R38 authority: adapter DNS is preserved. ctrld runs foreground on an owned
    # loopback ULA and a temporary owned NRPT catch-all routes DNS to that ULA.
    assert "ProgramData" in s and "FreeNetHub\\directdpi" in s
    assert "$CtrldDir=Join-Path $AppDir 'directdns'" in s
    assert "$RuntimeCtrld=Join-Path $Runtime 'ctrld'" in s
    assert "$Ula='fd53:4444:48::53'" in s
    assert "phase='PREPARED'" in s
    prepared=s.index("Write-JsonAtomic $StatePath $state")
    ula=s.index("New-NetIPAddress", prepared)
    ctrld_start=s.index("Start-Process -FilePath $Ctrld", prepared)
    nrpt=s.index("Add-DnsClientNrptRule", ctrld_start)
    assert prepared < ula < ctrld_start < nrpt
    assert "Get-NetUDPEndpoint -LocalAddress $Ula -LocalPort 53" in s
    assert "Get-NetTCPConnection -LocalAddress $Ula -LocalPort 53" in s
    assert "SYSTEM_DNS_VIA_ULA_FAIL" in s
    assert "ICS_CHANGED_DURING_DNS_STAGE" in s
    assert "ADAPTER_DNS_CHANGED" in s
    assert "--hostlist=" in s
    assert "--ipset-exclude-ip=76.76.10.11" in s
    assert "--wf-tcp=443" in s
    assert "0.0.0.0/1" in s and "128.0.0.0/1" in s
    assert "REFUSE_BROAD_TUNNEL_ROUTE" in s
    assert "Direct access" in s
    assert "Add-VpnConnection" not in s
    assert "New-NetRoute" not in s
    assert "Set-NetRoute" not in s
    assert "Resolve-PhysicalDefault" in s
    assert "DEFAULT_ROUTE_NOT_PHYSICAL" in s
    assert "--interface $LocalIp" in s
    assert "$Interface='Ethernet 3'" not in s
    assert "Set-DnsClientServerAddress" not in s
    assert "Get-DnsClientDohServerAddress" not in s
    assert "Set-DnsClientDohServerAddress" not in s
    assert "Add-DnsClientDohServerAddress" not in s
    assert "Remove-DnsClientDohServerAddress" not in s

def test_stop_restores_authoritative_prestate_and_owned_dns():
    s=(D/"Stop-DirectDpi.ps1").read_text(encoding="utf-8-sig")
    # Since R38 never mutates adapter DNS, rollback verifies exact pre/post DNS
    # equality instead of resetting adapter DNS. Only owned NRPT/ULA/process state
    # may be removed.
    assert "dnsV4" in s and "dnsV6" in s
    assert "ROLLBACK_DNSV4_MISMATCH" in s and "ROLLBACK_DNSV6_MISMATCH" in s
    assert "ROLLBACK_NRPT_MISMATCH" in s
    assert "ROLLBACK_ULA_MISMATCH" in s
    assert "ROLLBACK_ICS_MISMATCH" in s
    assert "ROLLBACK_ROUTE_MISMATCH" in s
    assert "ROLLBACK_PROXY_MISMATCH" in s
    assert "Remove-DnsClientNrptRule" in s
    assert "Remove-NetIPAddress" in s
    assert "Get-OwnedCtrld|Stop-Process" in s
    assert "Remove-Item -LiteralPath $RuntimeCtrld" in s
    assert "Remove-Item -LiteralPath $StatePath" in s
    assert "Set-DnsClientServerAddress" not in s
    assert "Get-DnsClientDohServerAddress" not in s

def test_product_wiring_present():
    ui=(R/"app"/"View.xaml").read_text(encoding="utf-8-sig")
    ctl=(R/"app"/"FreeNetHub.ps1").read_text(encoding="utf-8-sig")
    iss=(R/"windows"/"installer"/"FreeNetHub.iss").read_text(encoding="utf-8-sig")
    un=(R/"Uninstall-FreeNetHub.ps1").read_text(encoding="utf-8-sig")
    for name in ("DirectDpiStart","DirectDpiStop","DirectDpiStatus"):
        assert f'Name="{name}"' in ui
        assert name in ctl
    assert "Invoke-DirectDpi" in ctl
    assert "app\\directdpi\\*" in iss
    assert "app\\directdns\\*" not in iss
    assert "app\\directdns\\ctrld.exe" in iss
    assert "app\\directdns\\ctrld.toml" in iss
    assert "app\\directdns\\LICENSE-ctrld.txt" in iss
    assert "Stop-DirectDpi.ps1" in un
    assert "Direct-DNS ctrld service" in un
    assert "FreeNetHub\\directdns" in un


def test_installer_upgrade_guard_closes_only_idle_owned_ui_child():
    iss=(R/"windows"/"installer"/"FreeNetHub.iss").read_text(encoding="utf-8-sig")
    helper=(R/"windows"/"installer"/"Prepare-Upgrade.ps1").read_text(encoding="utf-8-sig")
    assert 'Source: "Prepare-Upgrade.ps1"; Flags: dontcopy' in iss
    assert "ExtractTemporaryFile('Prepare-Upgrade.ps1')" in iss
    assert "Disconnect it before upgrading" in iss
    assert "AppMutex=Local\\FreeNetHub.Desktop.SingleInstance.v41" not in iss
    assert "$ports=19410,19413,19414,19450,19452,19453,19460,9909" in helper
    assert "if(@($active).Count){ exit 42 }" in helper
    assert "Get-CimInstance Win32_Process" in helper
    assert "$_.Name -ieq 'pwsh.exe'" in helper
    assert "FreeNetHub.ps1" in helper
    assert "Stop-Process -Id $p.ProcessId -Force" in helper
    assert "$launcher=[IO.Path]::GetFullPath((Join-Path $AppRoot 'FreeNetHub.exe'))" in helper
    assert "$_.Name -ieq 'FreeNetHub.exe'" in helper
    assert "[IO.Path]::GetFullPath($_.ExecutablePath).Equals($launcher" in helper
    builder=(R/"tests"/"build_r38_direct_method_installer.ps1").read_text(encoding="utf-8-sig")
    assert "windows\\installer\\Prepare-Upgrade.ps1" in builder


def test_installer_digest_is_external_not_self_referential():
    release=json.loads((R/"RELEASE.json").read_text(encoding="utf-8-sig"))
    builder=(R/"tests"/"build_r38_direct_method_installer.ps1").read_text(encoding="utf-8-sig")
    assert release.get("installerSha256") is None
    assert release.get("installerStatus") == "DIGEST_IN_EXTERNAL_ACCEPTANCE_EVIDENCE"
    assert "R38_RELEASE_INSTALLER_HASH_SELF_REFERENCE" in builder
