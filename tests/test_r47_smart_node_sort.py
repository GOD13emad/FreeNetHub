import pathlib,sys,unittest
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'app'))
import engine as E
PS=(R/'app'/'FreeNetHub.ps1').read_text(encoding='utf-8-sig')
XAML=(R/'app'/'View.xaml').read_text(encoding='utf-8-sig')
class R47SmartNodeSort(unittest.TestCase):
 def test_smart_candidates_cover_actual_auto_methods_plus_comparison_paths(self):
  with patch.object(E,'settings',return_value=E.DEFAULT|{'country':'AUTO','order':['NODE','WARP','TOR','GOOL','CFON']}):
   self.assertEqual(E.smart_benchmark_candidates(),['NODE','WARP','TOR','GOOL','CFON','CUSTOM','DIRECT'])
 def test_smart_country_policy_still_benchmarks_all_rows_but_eligibility_is_strict(self):
  cfg=E.DEFAULT|{'country':'DE','order':['NODE','WARP','TOR','GOOL','CFON']}
  with patch.object(E,'settings',return_value=cfg):
   self.assertEqual(E.connect_candidates('AUTO'),['NODE','CFON'])
   self.assertEqual(E.smart_benchmark_candidates(),['NODE','WARP','TOR','GOOL','CFON','CUSTOM','DIRECT'])
 def test_smart_rank_is_numeric_and_latency_first(self):
  rows=[{'provider':'WARP','performance':{'ok':True,'pingMs':80,'downloadMbps':100,'uploadMbps':5}},{'provider':'NODE','performance':{'ok':True,'pingMs':20,'downloadMbps':10,'uploadMbps':1}},{'provider':'CFON','performance':{'ok':True,'pingMs':20,'downloadMbps':20,'uploadMbps':1}}]
  ranked=sorted(rows,key=lambda x:E.performance_rank_key(x['performance']))
  self.assertEqual([x['provider'] for x in ranked],['CFON','NODE','WARP'])
 def test_smart_never_auto_connects_direct_or_custom(self):
  with patch.object(E,'settings',return_value=E.DEFAULT|{'country':'AUTO','order':['NODE','WARP']}):
   self.assertEqual(E.connect_candidates('AUTO'),['NODE','WARP'])
   self.assertIn('DIRECT',E.smart_benchmark_candidates());self.assertIn('CUSTOM',E.smart_benchmark_candidates())
 def test_base_setting_does_not_replace_selected_method_with_direct(self):
  block=PS.split('function Start-ConfiguredTest',1)[1].split('function Start-ProviderBenchmark',1)[0]
  self.assertIn('$mode=Selected',block);self.assertNotIn("Start-Work 'Speed' 'DIRECT'",block)
 def test_auto_ui_consumes_every_provider_result(self):
  block=PS.split("if($r.action -eq 'ProviderBenchmark')",1)[1].split("if($r.action -eq 'ProviderPing')",1)[0]
  self.assertIn('foreach($row in @($r.result.results))',block);self.assertIn('Paint-Performance $row.performance $m $false',block)
  self.assertIn("$script:C.SmartMetric.Text='Best → '+$best",block)
 def test_dashboard_contains_only_real_method_result_rows(self):
  self.assertNotIn('Name="DashSmartPing"',XAML)
  for n in ('DashNodePing','DashWarpPing','DashCfonPing','DashGoolPing','DashTorPing','DashCustomPing','DashDirectPing'):self.assertIn(f'Name="{n}"',XAML)
 def test_node_numeric_columns_sort_on_raw_numbers(self):
  for k in ('PingValue','DownloadValue','UploadValue'):
   self.assertIn(f'SortMemberPath="{k}"',XAML);self.assertIn(k,PS)
  self.assertIn('Add_Sorting',PS);self.assertIn('Sort-NodeRowsNumeric',PS)
 def test_missing_numeric_results_always_append(self):
  block=PS.split('function Sort-NodeRowsNumeric',1)[1].split('function Sort-NodeRowsText',1)[0]
  self.assertIn('$missing=',block);self.assertIn('return @($present)+@($missing)',block)
 def test_dropdown_numeric_sort_is_ascending(self):
  block=PS.split('function Apply-NodeFilter',1)[1].split('function Paint-Nodes',1)[0]
  self.assertIn("'LATENCY'{$rows=Sort-NodeRowsNumeric $rows 'PingValue' $false}",block)
  self.assertIn("'SPEED'{$rows=Sort-NodeRowsNumeric $rows 'DownloadValue' $false}",block)
  self.assertIn("'UPLOAD'{$rows=Sort-NodeRowsNumeric $rows 'UploadValue' $false}",block)
 def test_best_known_node_performance_is_ranked_first(self):
  src=(R/'app'/'engine.py').read_text(encoding='utf-8-sig');block=src.split('def ensure_node',1)[1].split('def country_target',1)[0]
  self.assertIn('0 if perf_ok else 1',block);self.assertIn('perf_ping,-perf_down,-perf_up',block)
 def test_auto_benchmark_runs_every_candidate_and_returns_best(self):
  cfg=E.DEFAULT|{'country':'AUTO','order':['NODE','WARP']}
  speeds={'NODE':{'ok':True,'pingMs':60,'downloadMbps':50,'uploadMbps':5,'country':'DE'},'WARP':{'ok':True,'pingMs':20,'downloadMbps':20,'uploadMbps':2,'country':'DE'},'TOR':{'ok':False,'pingMs':120,'downloadMbps':0,'uploadMbps':0,'country':'DE'},'GOOL':{'ok':False,'pingMs':110,'downloadMbps':0,'uploadMbps':0,'country':'DE'},'CFON':{'ok':False,'pingMs':100,'downloadMbps':0,'uploadMbps':0,'country':'DE'},'CUSTOM':{'ok':False,'pingMs':90,'downloadMbps':0,'uploadMbps':0,'country':'DE'},'DIRECT':{'ok':True,'pingMs':10,'downloadMbps':200,'uploadMbps':20,'country':'DE'}}
  health={'healthy':True,'error':''}
  writes=[]
  with patch.object(E,'settings',return_value=cfg),patch.object(E,'owned',return_value=None),patch.object(E,'ensure_node',return_value=health),patch.object(E,'ensure',return_value=health),patch.object(E,'probe',return_value=health),patch.object(E,'path_speed',side_effect=lambda m:speeds[m]),patch.object(E,'direct_speed',return_value=speeds['DIRECT']),patch.object(E,'stop'),patch.object(E,'node_selected',return_value=None),patch.object(E,'write',side_effect=lambda path,obj:writes.append((path,obj))):
   out=E.dispatch('ProviderBenchmark','AUTO','')
  self.assertEqual([x['provider'] for x in out['results']],['NODE','WARP','TOR','GOOL','CFON','CUSTOM','DIRECT'])
  self.assertEqual(out['provider'],'WARP')
  self.assertEqual(out['rank'],['WARP','NODE'])
  self.assertTrue(any(obj.get('order',[None])[0]=='WARP' for _,obj in writes if isinstance(obj,dict)))

 def test_node_benchmark_records_best_node_performance(self):
  src=(R/'app'/'engine.py').read_text(encoding='utf-8-sig');block=src.split("if action=='ProviderBenchmark':",1)[1].split("if action=='ProviderPing':",1)[0]
  self.assertIn("node_record_performance(n['id'],perf)",block);self.assertIn("out['node']=NH.public_node",block)
if __name__=='__main__':unittest.main()
