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
    assert "ProgramData" in s and "FreeNetHub\\directdpi" in s
    assert "FreeNetHub\\directdns" in s
    assert "phase='PREPARED'" in s
    prepared=s.index("Write-JsonAtomic $StatePath $runtimeState")
    ctrld_start=s.index("& $Ctrld start --config $DnsRuntimeConfig --intercept-mode dns", prepared)
    assert prepared < ctrld_start
    assert "DIRECT_DNS_IPV6_LOOPBACK_LISTENER_MISSING" in s
    assert "Get-NetUDPEndpoint -LocalAddress '::1' -LocalPort 53" in s
    assert "DIRECT_DNS_ICS_CHANGED" in s
    assert "--hostlist=" in s
    assert "--ipset-exclude-ip=76.76.10.11" in s
    assert "--wf-tcp=443" in s
    assert "0.0.0.0/1" in s and "128.0.0.0/1" in s
    assert "REFUSE_FULL_ROUTE_OVERRIDE" in s
    assert "Direct access" in s
    assert "Add-VpnConnection" not in s
    assert "New-NetRoute" not in s
    assert "Set-NetRoute" not in s
    assert "Resolve-PhysicalDefaultInterface" in s
    assert "DIRECT_DPI_DEFAULT_ROUTE_NOT_PHYSICAL" in s
    assert "--interface $script:DirectLocalIp" in s
    assert "$Interface='Ethernet 3'" not in s
    assert "Get-DnsClientDohServerAddress" not in s
    assert "Set-DnsClientDohServerAddress" not in s
    assert "Add-DnsClientDohServerAddress" not in s
    assert "Remove-DnsClientDohServerAddress" not in s

def test_stop_restores_authoritative_prestate_and_owned_dns():
    s=(D/"Stop-DirectDpi.ps1").read_text(encoding="utf-8-sig")
    assert "preDnsMode" in s and "preDns" in s
    assert "ResetServerAddresses" in s
    assert "& $Ctrld uninstall" in s
    assert "DIRECT_DNS_NRPT_RESIDUE" in s
    assert "DIRECT_DNS_ICS_CHANGED_ON_STOP" in s
    assert "Remove-Item -LiteralPath $DnsRuntimeDir" in s
    assert "Remove-Item -LiteralPath $StatePath" in s
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
