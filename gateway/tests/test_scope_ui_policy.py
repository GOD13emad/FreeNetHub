import pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class ScopeUiPolicyTests(unittest.TestCase):
    def test_windows_scope_switch_default_and_console_only_ui(self):
        view = (ROOT / "app" / "View.xaml").read_text(encoding="utf-8-sig")
        self.assertIn('Name="FullSystem"', view)
        self.assertIn('IsChecked="False"', view)
        self.assertIn('Name="ScopeText"', view)
        self.assertIn('Header="اتصال کنسول"', view)
        self.assertNotIn('Name="GatewayPcStart"', view)

    def test_country_selection_is_persisted_and_mismatch_not_healthy(self):
        ui = (ROOT / "app" / "FreeNetHub.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("function Sync-CountrySelection", ui)
        self.assertIn("$script:C.Country.Add_SelectionChanged({Sync-CountrySelection})", ui)
        self.assertIn("Write-Json (Join-Path $script:Root 'settings.json') $script:Settings", ui)
        self.assertIn("$countryMismatch=[bool]($connected -and $uiCountry -ne 'AUTO' -and [string]$h.country -ne $uiCountry)", ui)
        self.assertIn("کشور خروجی با انتخاب شما یکی نیست", ui)
        self.assertIn("این اتصال برای کشور هدف سالم اعلام نمی‌شود", ui)

    def test_console_stop_is_isolated_from_pc_tunnel(self):
        ui = (ROOT / "app" / "FreeNetHub.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("$script:C.GatewayStop.Add_Click({Start-GatewayRequest 'StopConsole'})", ui)
        ctl = (ROOT / "gateway" / "gateway_control.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("'StopConsole'", ctl)
        start = ctl.index("elseif($Action -eq 'StopConsole'){")
        end = ctl.index("\n else{", start)
        block = ctl[start:end]
        self.assertIn("Run-WslConsole 'Stop'", block)
        self.assertNotIn("StopScript", block)
        self.assertNotIn("Run-Engine", block)

if __name__ == "__main__":
    unittest.main()
