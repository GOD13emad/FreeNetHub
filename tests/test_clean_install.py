import pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class CleanRuntimePackagingTests(unittest.TestCase):
    def test_active_files_do_not_depend_on_legacy_lab(self):
        active=[
            ROOT/"Setup-WindowsDependencies.ps1",
            ROOT/"app"/"engine.py",
            ROOT/"app"/"dependencies.example.json",
            ROOT/"gateway"/"Setup-GatewayCore.ps1",
            ROOT/"windows"/"installer"/"FreeNetHub.iss",
        ]
        forbidden=("AppData\\Local\\FreeTunnelLab","FreeTunnelLab\\WarpPlusFast","FreeTunnelLab\\TorSnowflake","FreeTunnelLab\\SingBox","oldRoot")
        for p in active:
            text=p.read_text(encoding="utf-8-sig")
            for token in forbidden:
                self.assertNotIn(token,text,f"{p} contains legacy dependency {token}")

    def test_runtime_is_bundled_by_installer(self):
        text=(ROOT/"windows"/"installer"/"FreeNetHub.iss").read_text(encoding="utf-8-sig")
        self.assertIn('runtime\\WarpPlusFast\\*',text)
        self.assertIn('runtime\\TorSnowflake\\bundle\\*',text)

    def test_setup_uses_self_contained_runtime_contract(self):
        text=(ROOT/"Setup-WindowsDependencies.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("runtimeRoot=$Runtime",text)
        self.assertIn("runtime='SELF_CONTAINED'",text)

if __name__=="__main__":
    unittest.main()
