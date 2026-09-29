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
 def test_pc_tunnel_node_provider_uses_node_socks_without_cloudflare_exclusion(self):
  c,p=M.build("PC_TUNNEL","NODE",None)
  provider=next(x for x in c["outbounds"] if x.get("tag")=="provider")
  self.assertEqual(provider["type"],"socks");self.assertEqual(provider["server"],"127.0.0.1");self.assertEqual(provider["server_port"],19460)
  self.assertEqual(c["route"]["final"],"provider");self.assertTrue(c["route"]["auto_detect_interface"])
  self.assertNotIn("route_exclude_address",c["inbounds"][0])
  self.assertTrue(any("sing-box.exe" in x.get("process_name",[]) and x["outbound"]=="direct" for x in c["route"]["rules"]))
 def test_pc_tunnel_controller_supports_node_strict_udp_and_dynamic_stop(self):
  text=(G/"gateway_control.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("[ValidateSet('WARP','NODE')][string]$Provider='WARP'",text)
  self.assertIn("[ValidateSet('SELECTED','AUTO')][string]$NodePolicy='SELECTED'",text)
  self.assertIn("Run-Engine 'ConnectSelectedNode' 'NODE' 160",text)
  self.assertIn("Run-Engine 'Connect' 'NODE' 240",text)
  self.assertIn("if($NodePolicy -eq 'AUTO')",text)
  self.assertIn("Verify-ProviderUdp $Provider",text)
  self.assertIn("PC_NODE_TCP_COUNTRY_",text);self.assertIn("PC_NODE_UDP_COUNTRY_",text)
  self.assertIn("Run-Engine 'StopOne' $sp",text)
  self.assertIn("providerPreexisting",text);self.assertIn("providerUdpBefore",text)
 def test_pc_tunnel_captures_pre_tun_base_route_for_update_bypass(self):
  text=(G/"gateway_control.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("function Get-BaseRouteSnapshot",text)
  self.assertIn("$baseRoute=Get-BaseRouteSnapshot",text)
  self.assertIn("baseRoute=$baseRoute",text)
  self.assertIn("baseTrace=$before",text)
  self.assertIn("schema=4;mode='PC_TUNNEL'",text)
 def test_auto_full_system_udp_does_not_depend_on_external_geo_lookup(self):
  text=(G/"gateway_control.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("$country='UNVERIFIED_AUTO'",text)
  self.assertIn("if($target -and $target -ne 'AUTO'){",text)
  self.assertIn("countryVerified=($target -and $target -ne 'AUTO')",text)
  self.assertIn("$udpCountry='UNVERIFIED_AUTO'",text)
  self.assertIn("if($Provider -eq 'NODE' -and $target -ne 'AUTO'){",text)

 def test_gateway_request_forwards_full_system_provider(self):
  text=(G/"gateway_request.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("[ValidateSet('WARP','NODE')][string]$Provider='WARP'",text)
  self.assertIn("[ValidateSet('SELECTED','AUTO')][string]$NodePolicy='SELECTED'",text)
  self.assertIn("if($Action -eq 'StartPc'){$args+=@('-Provider',$Provider);if($Provider -eq 'NODE'){$args+=@('-NodePolicy',$NodePolicy)}}",text)
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
 def test_pc_tunnel_uses_country_independent_warp_provider_connect(self):
  text=(G/"gateway_control.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("Run-Engine 'ConnectProvider' 'WARP'",text)
  self.assertNotIn("Run-Engine 'Connect' 'WARP' 220",text)
 def test_gateway_core_bootstrap_uses_canonical_runtime_temp(self):
  text=(G/"Setup-GatewayCore.ps1").read_text(encoding="utf-8-sig")
  self.assertIn("Join-Path $Runtime ('bootstrap-'",text)
  self.assertNotIn("Join-Path $env:TEMP ('FreeNetHub-core-'",text)
 def test_unverified_wireguard_contract(self):
  p={"kind":"wireguard","country":"NL","capabilities":{"tcp":True,"udp":True,"country_verified":False},"endpoint":{"type":"wireguard","tag":"provider"}}
  x=M.console_contract("WARP",p,"NL");self.assertFalse(x["ready"]);self.assertIn("COUNTRY_NOT_RUNTIME_VERIFIED",x["reasons"])
if __name__=="__main__":unittest.main(verbosity=2)
