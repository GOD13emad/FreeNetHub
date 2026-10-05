import json, pathlib, sys, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"app"))
import nodehub as NH
import engine as E

class R51ProtocolExpansion(unittest.TestCase):
    def test_hysteria_v1_official_uri(self):
        n=NH.parse_uri("hysteria://hy.example.com:443?protocol=udp&auth=hello&peer=cdn.example.com&insecure=1&upmbps=20&downmbps=80&alpn=hysteria&obfs=xplus&obfsParam=mask#HY1")
        self.assertEqual(n["protocol"],"hysteria")
        self.assertEqual(n["auth_str"],"hello")
        self.assertEqual(n["up_mbps"],20); self.assertEqual(n["down_mbps"],80)
        self.assertEqual(n["obfs"],"mask"); self.assertTrue(n["tls"]["insecure"])
        out=NH.sing_box_config(n,19601)["outbounds"][0]
        self.assertEqual(out["type"],"hysteria"); self.assertEqual(out["tls"]["server_name"],"cdn.example.com")
    def test_hysteria_v1_rejects_unsupported_transport(self):
        with self.assertRaisesRegex(ValueError,"HYSTERIA_V1_PROTOCOL_UNSUPPORTED"):
            NH.parse_uri("hysteria://hy.example.com:443?protocol=faketcp&upmbps=20&downmbps=80")
    def test_json_expansion_protocols(self):
        rows=[
          {"type":"ssh","tag":"ssh","server":"ssh.example","server_port":22,"user":"u","password":"p"},
          {"type":"snell","tag":"sn","server":"sn.example","server_port":443,"version":4,"psk":"secret","obfs_mode":"http","obfs_host":"cdn.example"},
          {"type":"socks","tag":"s5","server":"so.example","server_port":1080,"version":"5","username":"u","password":"p"},
          {"type":"http","tag":"hp","server":"hp.example","server_port":8080,"username":"u","password":"p"},
          {"type":"naive","tag":"nv","server":"nv.example","server_port":443,"username":"u","password":"p","tls":{"enabled":True,"server_name":"nv.example"}},
          {"type":"hysteria","tag":"hy","server":"hy.example","server_port":443,"up_mbps":10,"down_mbps":20,"auth_str":"p","tls":{"enabled":True,"server_name":"hy.example"}}
        ]
        p=NH.parse_blob(json.dumps({"outbounds":rows}),"r51")
        self.assertEqual(p["errors"],[])
        self.assertEqual([n["protocol"] for n in p["nodes"]],["ssh","snell","socks","http","naive","hysteria"])
        for i,n in enumerate(p["nodes"]):
            self.assertEqual(NH.sing_box_config(n,19610+i)["outbounds"][0]["type"],n["protocol"])
    def test_json_local_paths_fail_closed(self):
        raw=json.dumps({"type":"ssh","server":"x","server_port":22,"user":"u","private_key_path":"C:/secret/id_rsa"})
        p=NH.parse_blob(raw,"x"); self.assertEqual(p["found"],0); self.assertIn("NODE_JSON_LOCAL_PATH_UNSUPPORTED",p["errors"])
    def test_new_protocol_visibility_is_secret_safe(self):
        raw=json.dumps({"type":"naive","server":"x","server_port":443,"username":"u","password":"secret","tls":{"enabled":True,"server_name":"x"}})
        n=NH.parse_blob(raw,"x")["nodes"][0]; pub=NH.public_node(n)
        self.assertNotIn("password",pub); self.assertNotIn("username",pub)
    def test_hysteria_v1_skips_tcp_preflight(self):
        with patch.object(E.socket,"create_connection") as cc:
            r=E.node_endpoint_probe({"protocol":"hysteria","server":"203.0.113.1","port":443})
        cc.assert_not_called(); self.assertIsNone(r["reachable"])
    def test_windows_naive_runtime_guard_present(self):
        src=(ROOT/"app"/"engine.py").read_text(encoding="utf-8-sig")
        self.assertIn("DEPENDENCY_NOT_CONFIGURED_CRONET",src)
        self.assertIn("EEE741046F0A3975124BAE349AEAC237AA306F3CC4DE59FF5DE070E74DBFDAEB",src)
    def test_setup_repairs_pinned_cronet(self):
        for rel in ("gateway/Setup-GatewayCore.ps1","gateway/Setup-ConsoleGateway.ps1"):
            src=(ROOT/rel).read_text(encoding="utf-8-sig")
            self.assertIn("libcronet.dll",src)
            self.assertIn("EEE741046F0A3975124BAE349AEAC237AA306F3CC4DE59FF5DE070E74DBFDAEB",src)
if __name__=="__main__":
    unittest.main()
