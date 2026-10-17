#!/usr/bin/env python3
"""Static and mocked integration checks, no WinINet registry/system changes."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fnh_selective_engine_integration", ROOT / "app/engine.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


class IntegrationTests(unittest.TestCase):
    def test_enable_is_explicit_owned_healthy_and_payload_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            (base / "jobs").mkdir()
            req = base / "jobs" / "selective-request-good.json"
            req.write_text(json.dumps({"domains": "brave.com\nstripe.com"}))
            calls = []
            fake = type("SelectiveStub", (), {
                "enable": staticmethod(lambda domains, port, method:
                    calls.append((domains, port, method)) or {"ok": True}),
                "status": staticmethod(lambda: {"ok": True, "enabled": False}),
                "disable": staticmethod(lambda: {"ok": True, "restored": True}),
            })()
            with mock.patch.object(engine, "ROOT", base), \
                 mock.patch.object(engine, "_selective_route", return_value=fake), \
                 mock.patch.object(engine, "owned", return_value={"verified": True}) as owned, \
                 mock.patch.object(engine, "verify", return_value={"healthy": True}) as verified:
                result = engine.dispatch("SelectiveEnable", "CFON", str(req))
                self.assertTrue(result["ok"])
                self.assertEqual(calls, [("brave.com\nstripe.com", 19414, "CFON")])
                owned.assert_called_once_with("CFON")
                verified.assert_called_once_with("CFON")
                self.assertEqual(engine.dispatch("SelectiveStatus", "AUTO", ""), {"ok": True, "enabled": False})
                self.assertEqual(engine.dispatch("SelectiveDisable", "AUTO", ""), {"ok": True, "restored": True})
                outside = base / "forbidden.json"
                outside.write_text(req.read_text(encoding="utf-8"))
                with self.assertRaises(ValueError):
                    engine.dispatch("SelectiveEnable", "CFON", str(outside))
                with self.assertRaises(ValueError):
                    engine.dispatch("SelectiveEnable", "DIRECT", str(req))

    def test_google_preset_and_403_url_additions_require_explicit_apply(self):
        with tempfile.TemporaryDirectory() as d:
            home=pathlib.Path(d)
            (home/"jobs").mkdir()
            req=home/"jobs"/"site.json"
            req.write_text(json.dumps({"url":"https://console.cloud.google.com/apis/credentials?token=secret"}),encoding="utf-8")
            class SiteStub:
                GOOGLE_DOMAINS=("google.com","googleapis.com","gstatic.com")
                def host_from_url(self,url):
                    self.url=url
                    return "console.cloud.google.com"
                def diagnose_403_site(self,url,port):
                    self.observed=(url,port)
                    return {"ok":True,"directCode":403,"tunnelCode":302,
                            "host":"console.cloud.google.com","suggestAdd":True,
                            "settingsChanged":False}
            stub=SiteStub()
            with mock.patch.object(engine,"ROOT",home),\
                 mock.patch.object(engine,"_selective_route",return_value=stub),\
                 mock.patch.object(engine,"owned",return_value={"verified":True}) as owned,\
                 mock.patch.object(engine,"verify",return_value={"healthy":True}) as verified,\
                 mock.patch.object(engine,"ensure") as ensure:
                preset=engine.dispatch("SelectiveGooglePreset","AUTO","")
                self.assertIn("googleapis.com",preset["domains"])
                self.assertFalse(preset["settingsChanged"])
                added=engine.dispatch("SelectiveAddSite","AUTO",str(req))
                self.assertEqual(added["host"],"console.cloud.google.com")
                self.assertFalse(added["settingsChanged"])
                owned.assert_not_called()
                result=engine.dispatch("SelectiveProbe","CFON",str(req))
                self.assertEqual(stub.observed[1],engine.PORTS["CFON"])
                self.assertTrue(result["suggestAdd"])
                self.assertFalse(result["settingsChanged"])
                self.assertEqual(owned.call_count,1)
                self.assertEqual(verified.call_count,1)
                ensure.assert_not_called()
                with self.assertRaises(ValueError):
                    engine.dispatch("SelectiveProbe","DIRECT",str(req))
                with self.assertRaises(ValueError):
                    engine.dispatch("SelectiveAddSite","AUTO",str(home/"wrong.json"))

    def test_explicit_tailnet_mode_verified_peer_and_no_local_provider_mutation(self):
        peers={"BackendState":"Running",
               "Self":{"TailscaleIPs":["100.100.42.2"],"Online":True},
               "Peer":{"a":{"OS":"linux","HostName":"LinuxDemo",
                            "Online":True,"TailscaleIPs":["100.100.42.1"]}}}
        with mock.patch.object(engine,"_tailnet_peer_status",return_value=peers):
            self.assertEqual(engine._tailnet_endpoint("100.100.42.1:19551"),
                             ("100.100.42.1",19551))
            for ep in ("8.8.8.8:19551","100.100.42.1:19414",
                       "100.100.42.3:19551","100.100.42.1:80"):
                with self.subTest(ep=ep),self.assertRaises(ValueError):
                    engine._tailnet_endpoint(ep)
        with tempfile.TemporaryDirectory() as d:
            base=pathlib.Path(d)
            (base/"jobs").mkdir()
            req=base/"jobs"/"tailnet.json"
            req.write_text(json.dumps({"domains":"google.com","endpoint":"100.100.42.1:19551"}),encoding="utf-8")
            fake=type("GatewayStub",(),{
                "enable":staticmethod(lambda domains,port,method,proxy_host:
                    {"ok":True,"domains":domains,"port":port,"method":method,"proxyHost":proxy_host}),
                "diagnose_403_site":staticmethod(lambda url,port,host,method:
                    {"ok":True,"site":url,"port":port,"method":method,"proxyHost":host}),
            })()
            with mock.patch.object(engine,"ROOT",base),\
                 mock.patch.object(engine,"_selective_route",return_value=fake),\
                 mock.patch.object(engine,"_tailnet_peer_status",return_value=peers),\
                 mock.patch.object(engine,"owned") as owned,\
                 mock.patch.object(engine,"verify") as verify,\
                 mock.patch.object(engine,"ensure") as ensure:
                out=engine.dispatch("SelectiveEnable","TAILNET",str(req))
                self.assertTrue(out["ok"])
                self.assertEqual((out["port"],out["proxyHost"]),(19551,"100.100.42.1"))
                pr=engine.dispatch("SelectiveProbe","TAILNET",str(req))
                self.assertEqual(pr["method"],"TAILNET")
                owned.assert_not_called()
                verify.assert_not_called()
                ensure.assert_not_called()

    def test_no_unverified_provider_starts(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d)
            (base / "jobs").mkdir()
            req = base / "jobs" / "only.json"
            req.write_text(json.dumps({"domains": "brave.com"}))
            with mock.patch.object(engine, "ROOT", base), \
                 mock.patch.object(engine, "_selective_route") as module, \
                 mock.patch.object(engine, "owned", return_value=None), \
                 mock.patch.object(engine, "verify", return_value={"healthy": True}) as verified, \
                 mock.patch.object(engine, "ensure") as ensure:
                with self.assertRaises(ValueError):
                    engine.dispatch("SelectiveEnable", "CFON", str(req))
                module.return_value.enable.assert_not_called()
                verified.assert_not_called()
                ensure.assert_not_called()

    def test_disable_failure_is_not_reported_as_success(self):
        fake = type("SelectiveStub", (), {
            "disable": staticmethod(lambda: {"ok": False, "error": "WINDOWS_PROXY_DRIFT"}),
        })()
        with mock.patch.object(engine, "_selective_route", return_value=fake):
            with self.assertRaises(RuntimeError):
                engine.dispatch("SelectiveDisable", "AUTO", "")

    def test_settings_use_safe_domain_validation(self):
        good = engine.validate_settings(dict(engine.DEFAULT, selectiveDomains="brave.com\n*.stripe.com"))
        self.assertEqual(good["selectiveDomains"], "brave.com\nstripe.com")
        with self.assertRaises(ValueError):
            engine.validate_settings(dict(engine.DEFAULT, selectiveDomains="https://stripe.com/login"))

    def test_wpf_installer_and_uninstall_integration(self):
        xaml = (ROOT / "app/View.xaml").read_text(encoding="utf-8")
        ui = (ROOT / "app/FreeNetHub.ps1").read_text(encoding="utf-8")
        installer = (ROOT / "windows/installer/FreeNetHub.iss").read_text(encoding="utf-8")
        uninstall = (ROOT / "Uninstall-FreeNetHub.ps1").read_text(encoding="utf-8")
        elements = ET.fromstring(xaml).iter()
        names = [x.attrib["Name"] for x in elements if "Name" in x.attrib]
        self.assertEqual(len(names), len(set(names)))
        for name in ("SelectiveDomains", "SelectiveMethod", "SelectivePreset", "SelectiveApply",
                     "SelectiveDisable", "SelectiveRefresh", "SelectiveRouteStatus",
                     "SelectiveRoutingCard", "MethodsScopeSelective",
                     "SelectiveGooglePreset", "SelectiveSiteUrl", "SelectiveAddSite",
                     "SelectiveProbe", "SelectiveSiteStatus",
                     "SelectiveTailnetEndpoint","SelectiveTailnetDiscover","SelectiveTailnetStatus"):
            self.assertEqual(names.count(name), 1)
            self.assertIn("C." + name, ui)
        for action in ("SelectiveEnable", "SelectiveDisable", "SelectiveStatus"):
            self.assertIn("Start-Work '" + action + "'", ui)
            self.assertIn("'" + action + "'", (ROOT / "app/engine.py").read_text(encoding="utf-8"))
        for action in ("SelectiveGooglePreset","SelectiveAddSite","SelectiveProbe"):
            self.assertIn("Start-Work '" + action + "'", ui)
            self.assertIn("'" + action + "'", (ROOT / "app/engine.py").read_text(encoding="utf-8"))
        self.assertIn("selective_route_windows.py", installer)
        self.assertIn("selective_http_bridge.py", installer)
        self.assertIn("PROXY 127.0.0.1:", (ROOT / "app/selective_route_windows.py").read_text(encoding="utf-8"))
        self.assertIn("CONNECT_HOST_NOT_ALLOWED", (ROOT / "app/selective_http_bridge.py").read_text(encoding="utf-8"))
        self.assertIn("data\\selective_windows\\policy.json", uninstall)
        self.assertIn("SELECTIVE_RESTORE_REQUIRED_BEFORE_STOP", (ROOT / "app/engine.py").read_text(encoding="utf-8"))
        accepted=(ROOT / "windows/installer/Prepare-Upgrade.ps1").read_bytes()
        self.assertEqual(hashlib.sha256(accepted).hexdigest().upper(),
                         "98BD0A564EA8055960D3A5B6C8CB3B5737DA391D88846F7562621B8E8DC1656C")
        guard=(ROOT / "windows/installer/Prepare-SelectiveUpgrade.ps1").read_text(encoding="utf-8")
        self.assertIn("selective_windows\\policy.json", guard)
        self.assertIn("inFlight", guard)
        self.assertIn("Prepare-SelectiveUpgrade.ps1", installer)
        self.assertLess(installer.index("ExtractTemporaryFile('Prepare-SelectiveUpgrade.ps1')"),
                        installer.index("ExtractTemporaryFile('Prepare-Upgrade.ps1')"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
