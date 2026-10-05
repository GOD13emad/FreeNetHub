import json, pathlib, sys, unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"app"))
import nodehub as NH
import engine as E

class R49NodeProtocolExpansion(unittest.TestCase):
    def test_tuic_share_uri_parses_and_maps_to_singbox(self):
        n=NH.parse_uri("tuic://2DD61D93-75D8-4DA4-AC0E-6AECE7EAC365:hello@example.com:443?allow_insecure=1&alpn=h3&congestion_control=bbr&sni=cdn.example.com&udp_relay_mode=native#TUIC%20Test")
        self.assertEqual(n["protocol"],"tuic")
        self.assertEqual(n["name"],"TUIC Test")
        self.assertEqual(n["uuid"],"2DD61D93-75D8-4DA4-AC0E-6AECE7EAC365")
        self.assertEqual(n["password"],"hello")
        self.assertEqual(n["congestion_control"],"bbr")
        self.assertTrue(n["tls"]["insecure"])
        self.assertEqual(n["tls"]["server_name"],"cdn.example.com")
        out=NH.sing_box_config(n,19501)["outbounds"][0]
        self.assertEqual(out["type"],"tuic")
        self.assertEqual(out["udp_relay_mode"],"native")
        self.assertEqual(out["tls"]["alpn"],["h3"])

    def test_tuic_rejects_invalid_control_values(self):
        with self.assertRaisesRegex(ValueError,"TUIC_CONGESTION_CONTROL_INVALID"):
            NH.parse_uri("tuic://u:p@example.com:443?congestion_control=nope")
        with self.assertRaisesRegex(ValueError,"TUIC_UDP_RELAY_MODE_INVALID"):
            NH.parse_uri("tuic://u:p@example.com:443?udp_relay_mode=nope")

    def test_anytls_official_uri_defaults_to_443(self):
        n=NH.parse_uri("anytls://letmein@example.com/?sni=real.example.com&insecure=1#AnyTLS%20Test")
        self.assertEqual(n["protocol"],"anytls")
        self.assertEqual(n["port"],443)
        self.assertEqual(n["password"],"letmein")
        self.assertEqual(n["tls"]["server_name"],"real.example.com")
        self.assertTrue(n["tls"]["insecure"])
        out=NH.sing_box_config(n,19502)["outbounds"][0]
        self.assertEqual(out["type"],"anytls")
        self.assertEqual(out["password"],"letmein")

    def test_extract_uris_includes_new_protocols(self):
        rows=NH.extract_uris("x\ntuic://u:p@a.example:443#t\nanytls://pw@b.example/?sni=b.example#x")
        self.assertEqual(len(rows),2)
        self.assertTrue(rows[0].startswith("tuic://"))
        self.assertTrue(rows[1].startswith("anytls://"))

    def test_shadowtls_standalone_singbox_json_import(self):
        raw=json.dumps({"outbounds":[
            {"type":"shadowtls","tag":"shadow-safe","server":"st.example","server_port":443,"version":3,"password":"secret","tls":{"enabled":True,"server_name":"www.example.com"}},
            {"type":"direct","tag":"direct"}
        ]})
        p=NH.parse_blob(raw,"json-test")
        self.assertEqual(p["found"],1)
        n=p["nodes"][0]
        self.assertEqual(n["protocol"],"shadowtls")
        self.assertEqual(n["version"],3)
        self.assertEqual(n["source"],"json-test")
        out=NH.sing_box_config(n,19503)["outbounds"][0]
        self.assertEqual(out["type"],"shadowtls")
        self.assertEqual(out["password"],"secret")

    def test_json_tuic_anytls_import(self):
        raw=json.dumps({"outbounds":[
            {"type":"tuic","tag":"t","server":"t.example","server_port":443,"uuid":"u","password":"p","congestion_control":"cubic","udp_relay_mode":"native","tls":{"enabled":True,"server_name":"t.example"}},
            {"type":"anytls","tag":"a","server":"a.example","server_port":8443,"password":"p2","min_idle_session":3,"tls":{"enabled":True,"server_name":"a.example"}}
        ]})
        p=NH.parse_blob(raw,"json")
        self.assertEqual([n["protocol"] for n in p["nodes"]],["tuic","anytls"])
        self.assertEqual(p["nodes"][1]["min_idle_session"],3)

    def test_json_detour_fails_closed(self):
        raw=json.dumps({"type":"shadowtls","server":"x.example","server_port":443,"version":3,"password":"p","detour":"ss-out","tls":{"enabled":True,"server_name":"x.example"}})
        p=NH.parse_blob(raw,"json")
        self.assertEqual(p["found"],0)
        self.assertIn("NODE_JSON_DETOUR_UNSUPPORTED",p["errors"])

    def test_tuic_skips_tcp_only_endpoint_preflight(self):
        n={"protocol":"tuic","server":"203.0.113.1","port":443}
        with patch.object(E.socket,"create_connection") as cc:
            r=E.node_endpoint_probe(n)
        cc.assert_not_called()
        self.assertIsNone(r["reachable"])
        self.assertEqual(r["type"],"UDP_QUIC_PREFLIGHT_NOT_APPLICABLE")

    def test_hysteria2_regression_still_skips_tcp_preflight(self):
        n={"protocol":"hysteria2","server":"203.0.113.1","port":443}
        with patch.object(E.socket,"create_connection") as cc:
            r=E.node_endpoint_probe(n)
        cc.assert_not_called()
        self.assertIsNone(r["reachable"])

    def test_quic_protocols_are_eligible_for_benchmark_without_tcp_reachability(self):
        src=(ROOT/"app"/"engine.py").read_text(encoding="utf-8-sig")
        self.assertGreaterEqual(src.count("NH.UDP_PREFLIGHT_PROTOCOLS"),4)
        self.assertNotIn("proto=='hysteria2'",src)

    def test_naive_not_false_advertised_without_runtime_prerequisite(self):
        self.assertNotIn("naive",NH.SUPPORTED_PROTOCOLS)
        self.assertNotIn("naive",NH.JSON_ONLY_PROTOCOLS)

if __name__=="__main__":
    unittest.main()
