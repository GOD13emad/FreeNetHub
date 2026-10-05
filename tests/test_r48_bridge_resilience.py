import pathlib,tempfile,unittest,sys,importlib.util
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("r48_engine",R/"app"/"engine.py")
E=importlib.util.module_from_spec(spec);sys.modules[spec.name]=E;spec.loader.exec_module(E)
PS=(R/"app"/"FreeNetHub.ps1").read_text(encoding="utf-8-sig")
XAML=(R/"app"/"View.xaml").read_text(encoding="utf-8-sig")
WEB='webtunnel 192.0.2.10:443 '+('A'*40)+' url=https://example.com/x ver=0.0.1'
OB='obfs4 192.0.2.11:443 '+('B'*40)+' cert=abc iat-mode=0'

class R48BridgeResilienceTests(unittest.TestCase):
 def mk(self,web=None,obfs=None):
  td=tempfile.TemporaryDirectory();root=pathlib.Path(td.name);(root/"data").mkdir()
  if web is not None:(root/"data"/"bridges_webtunnel.txt").write_text(web,encoding="utf-8")
  if obfs is not None:(root/"data"/"bridges_obfs4.txt").write_text(obfs,encoding="utf-8")
  return td,root
 def test_valid_configured_bridges_are_detected(self):
  td,root=self.mk(WEB,OB)
  try:
   with patch.object(E,"ROOT",root):self.assertEqual(E.configured_bridge_modes(),["WEBTUNNEL","OBFS4"])
  finally:td.cleanup()
 def test_invalid_or_missing_bridge_never_enters_candidates(self):
  td,root=self.mk("not-a-valid-bridge",None);cfg=E.DEFAULT|{"country":"AUTO","order":["NODE","WARP","TOR","GOOL","CFON"]}
  try:
   with patch.object(E,"ROOT",root),patch.object(E,"settings",return_value=cfg):
    self.assertEqual(E.configured_bridge_modes(),[])
    self.assertNotIn("WEBTUNNEL",E.smart_benchmark_candidates());self.assertNotIn("OBFS4",E.connect_candidates("AUTO"))
  finally:td.cleanup()
 def test_valid_bridges_enter_smart_and_auto_only_for_country_auto(self):
  td,root=self.mk(WEB,OB);cfg=E.DEFAULT|{"country":"AUTO","order":["NODE","WARP","TOR","GOOL","CFON"]}
  try:
   with patch.object(E,"ROOT",root),patch.object(E,"settings",return_value=cfg):
    self.assertIn("WEBTUNNEL",E.smart_benchmark_candidates());self.assertIn("OBFS4",E.smart_benchmark_candidates())
    self.assertIn("WEBTUNNEL",E.connect_candidates("AUTO"));self.assertIn("OBFS4",E.connect_candidates("AUTO"))
   strict=cfg|{"country":"DE"}
   with patch.object(E,"ROOT",root),patch.object(E,"settings",return_value=strict):
    self.assertEqual(E.connect_candidates("AUTO"),["NODE","CFON"])
    self.assertIn("WEBTUNNEL",E.smart_benchmark_candidates());self.assertIn("OBFS4",E.smart_benchmark_candidates())
  finally:td.cleanup()
 def test_emergency_candidates_skip_invalid_private_bridge_before_fallback(self):
  td,root=self.mk("invalid",OB);cfg=E.DEFAULT|{"country":"AUTO","order":["NODE","WARP"]}
  try:
   with patch.object(E,"ROOT",root),patch.object(E,"settings",return_value=cfg):
    c=E.emergency_candidates()
    self.assertNotIn("WEBTUNNEL",c);self.assertEqual(c[0],"OBFS4");self.assertIn("TOR",c)
  finally:td.cleanup()
 def test_scan_includes_only_configured_bridges(self):
  td,root=self.mk(WEB,None);calls=[];health=lambda m:{"healthy":True,"mode":m,"seconds":1.0}
  try:
   with patch.object(E,"ROOT",root),patch.object(E,"owned",return_value=None),patch.object(E,"ensure",side_effect=lambda m:(calls.append(m) or health(m))),patch.object(E,"stop"),patch.object(E,"settings",return_value=E.DEFAULT),patch.object(E,"write"):
    E.dispatch("Scan","AUTO","")
   self.assertIn("WEBTUNNEL",calls);self.assertNotIn("OBFS4",calls)
  finally:td.cleanup()
 def test_ui_exposes_bridge_metrics_and_explicit_controls(self):
  for name in ("DashWebTunnelPing","DashWebTunnelDown","DashWebTunnelUp","DashWebTunnelState","DashObfs4Ping","DashObfs4Down","DashObfs4Up","DashObfs4State","WebTunnelMetric","Obfs4Metric","BridgeWebTest","BridgeWebConnect","BridgeObfsTest","BridgeObfsConnect"):
   self.assertIn(f'Name="{name}"',XAML)
  self.assertIn("'WEBTUNNEL'{'DashWebTunnel'}",PS);self.assertIn("'OBFS4'{'DashObfs4'}",PS)
  self.assertIn("Start-ProviderBenchmark 'WEBTUNNEL'",PS);self.assertIn("Start-ProviderConnect 'WEBTUNNEL'",PS)
  self.assertIn("Start-ProviderBenchmark 'OBFS4'",PS);self.assertIn("Start-ProviderConnect 'OBFS4'",PS)
 def test_optional_bridge_rows_default_to_skip_not_false_fail(self):
  self.assertIn("Paint-TestState $m 'SKIP' 'NOT_CONFIGURED_OR_NOT_TESTED' $false",PS)
 def test_kill_identity_treats_natural_exit_race_as_benign(self):
  class Fn:
   def __init__(self,vals):self.vals=list(vals) if isinstance(vals,(list,tuple)) else None;self.value=vals
   def __call__(self,*args):
    if self.vals is not None:return self.vals.pop(0)
    return self.value
  class K: pass
  k=K();k.OpenProcess=Fn(123);k.TerminateProcess=Fn(0);k.WaitForSingleObject=Fn([258,0]);k.CloseHandle=Fn(None)
  rec={"pid":7,"path":"x","created":9}
  with patch.object(E,"identity",return_value=dict(rec)),patch.object(E.C,"WinDLL",return_value=k):
   self.assertFalse(E.kill_identity(rec))
 def test_kill_identity_still_fails_closed_when_owned_process_is_live(self):
  class Fn:
   def __init__(self,vals):self.vals=list(vals) if isinstance(vals,(list,tuple)) else None;self.value=vals
   def __call__(self,*args):
    if self.vals is not None:return self.vals.pop(0)
    return self.value
  class K: pass
  k=K();k.OpenProcess=Fn(123);k.TerminateProcess=Fn(0);k.WaitForSingleObject=Fn([258,258]);k.CloseHandle=Fn(None)
  rec={"pid":7,"path":"x","created":9}
  with patch.object(E,"identity",return_value=dict(rec)),patch.object(E.C,"WinDLL",return_value=k):
   with self.assertRaisesRegex(OSError,"OWNED_PROCESS_STOP_FAILED"):E.kill_identity(rec)
 def test_no_private_bridge_material_added_to_repo(self):
  self.assertFalse((R/"data"/"bridges_webtunnel.txt").exists());self.assertFalse((R/"data"/"bridges_obfs4.txt").exists())

if __name__=="__main__":unittest.main()
