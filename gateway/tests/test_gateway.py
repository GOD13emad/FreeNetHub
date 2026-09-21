import importlib.util,json,pathlib,tempfile,subprocess,unittest,base64
R=pathlib.Path(__file__).resolve().parents[2]
G=R/"gateway"
spec=importlib.util.spec_from_file_location("gc",G/"generate_config.py");M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class GatewayTests(unittest.TestCase):
 def test_pc_tunnel_final_provider(self):
  c,p=M.build("PC_TUNNEL","WARP",None)
  self.assertEqual(c["route"]["final"],"provider")
  self.assertTrue(c["inbounds"][0]["auto_route"]);self.assertTrue(c["inbounds"][0]["strict_route"])
  self.assertEqual(c["inbounds"][0]["dns_mode"],"hijack");self.assertEqual(c["dns"]["servers"][0]["detour"],"provider")
  self.assertTrue(any("warp-plus.exe" in x.get("process_name",[]) and x["outbound"]=="direct" for x in c["route"]["rules"]))
  self.assertIn("162.159.192.0/24",c["inbounds"][0]["route_exclude_address"])
  self.assertIn("162.159.193.0/24",c["inbounds"][0]["route_exclude_address"])
  self.assertIn("162.159.197.0/24",c["inbounds"][0]["route_exclude_address"])
 def test_profile_path_has_no_warp_socks_underlay_exclusion(self):
  import tempfile,json
  prof={"kind":"wireguard","name":"TEST","country":"NL","capabilities":{"tcp":True,"udp":True,"country_verified":True},"endpoint":{"type":"wireguard","tag":"provider","system":False,"address":["10.0.0.2/32"],"private_key":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","peers":[{"address":"203.0.113.1","port":51820,"public_key":"AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=","allowed_ips":["0.0.0.0/0"]}]}}
  with tempfile.TemporaryDirectory() as td:
   q=pathlib.Path(td)/"p.json";q.write_text(json.dumps(prof),encoding="utf-8")
   c,p=M.build("PC_TUNNEL","WARP",str(q))
   self.assertNotIn("route_exclude_address",c["inbounds"][0])
 def test_console_only_source_rule_and_pc_direct(self):
  c,p=M.build("CONSOLE_ONLY","WARP",None)
  self.assertEqual(c["route"]["final"],"direct");self.assertEqual(c["inbounds"][0]["dns_mode"],"disabled");self.assertNotIn("dns",c)
  rules=[x for x in c["route"]["rules"] if "source_ip_cidr" in x]
  self.assertEqual(rules[0]["source_ip_cidr"],["192.168.77.0/24"]);self.assertEqual(rules[0]["outbound"],"provider")
 def test_console_warp_foreign_country_blocked(self):
  x=M.console_contract("WARP",None,"NL")
  self.assertFalse(x["ready"]);self.assertIn("UDP_COUNTRY_NOT_VERIFIED",x["reasons"])
 def test_console_fixed_de_contract(self):
  x=M.console_contract("FNH_DE",None,"DE")
  self.assertTrue(x["ready"]);self.assertEqual(x["reasons"],[])
 def test_console_fixed_de_country_mismatch(self):
  x=M.console_contract("FNH_DE",None,"NL")
  self.assertFalse(x["ready"]);self.assertIn("COUNTRY_MISMATCH",x["reasons"])
 def test_console_cfon_udp_blocked(self):
  x=M.console_contract("CFON",None,"NL")
  self.assertFalse(x["ready"]);self.assertIn("UDP_NOT_VERIFIED",x["reasons"])
 def test_verified_wireguard_contract(self):
  p={"kind":"wireguard","country":"NL","capabilities":{"tcp":True,"udp":True,"country_verified":True},"endpoint":{"type":"wireguard","tag":"provider"}}
  x=M.console_contract("WARP",p,"NL");self.assertTrue(x["ready"])
 def test_unverified_wireguard_contract(self):
  p={"kind":"wireguard","country":"NL","capabilities":{"tcp":True,"udp":True,"country_verified":False},"endpoint":{"type":"wireguard","tag":"provider"}}
  x=M.console_contract("WARP",p,"NL");self.assertFalse(x["ready"]);self.assertIn("COUNTRY_NOT_RUNTIME_VERIFIED",x["reasons"])
if __name__=="__main__":unittest.main(verbosity=2)
