import unittest,sys,pathlib,tempfile,json,os,socket,time
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'app'));import engine as E

class Unit(unittest.TestCase):
 def test_trace_crlf(self):self.assertEqual(E.trace('ip=1.2.3.4\r\nloc=AT\r\n')['loc'],'AT')
 def test_trace_ipv6(self):self.assertEqual(E.trace('ip=2001:db8::1\nloc=T1')['loc'],'T1')
 def test_trace_invalid(self):self.assertEqual(E.trace('ip=999.999.1.1\nloc=AT'),{})
 def test_trace_html(self):self.assertEqual(E.trace('<html>ok</html>'),{})
 def test_proxy_loopback(self):self.assertEqual(E.local_proxy('socks5h://127.0.0.1:9909'),'socks5h://127.0.0.1:9909')
 def test_proxy_public_rejected(self):
  with self.assertRaises(ValueError):E.local_proxy('socks5h://example.com:1080')
 def test_proxy_credentials_rejected(self):
  with self.assertRaises(ValueError):E.local_proxy('http://user:pass@127.0.0.1:8080')
 def test_proxy_path_rejected(self):
  with self.assertRaises(ValueError):E.local_proxy('http://127.0.0.1:8080/path')
 def test_settings_home_rejected(self):
  with self.assertRaises(ValueError):E.validate_settings(E.DEFAULT|{'home':'file:///C:/secret'})
 def test_settings_country_rejected(self):
  with self.assertRaises(ValueError):E.validate_settings(E.DEFAULT|{'country':'INVALID'})
 def test_auto_no_direct(self):self.assertNotIn('DIRECT',E.DEFAULT['order']);self.assertNotIn('CUSTOM',E.DEFAULT['order'])
 def test_settings_order_rejected(self):
  with self.assertRaises(ValueError):E.validate_settings(E.DEFAULT|{'order':['DIRECT']})
 def test_obfs_valid(self):
  s='obfs4 192.0.2.1:443 '+('A'*40)+' cert=abc iat-mode=0';self.assertEqual(E.bridge_lines(s,'obfs4'),[s])
 def test_bridge_empty(self):self.assertEqual(E.bridge_lines('# no bridge\n','webtunnel'),[])
 def test_bridge_duplicate(self):
  s='obfs4 192.0.2.1:443 '+('A'*40)+' cert=abc iat-mode=0';self.assertEqual(len(E.bridge_lines(s+'\nBridge '+s,'obfs4')),1)
 def test_bridge_config_injection(self):
  with self.assertRaises(ValueError):E.bridge_lines('SocksPort 0.0.0.0:9050','obfs4')
 def test_webtunnel_https_required(self):
  with self.assertRaises(ValueError):E.bridge_lines('webtunnel 192.0.2.1:443 '+('A'*40)+' url=http://example.com/','webtunnel')
 def test_bridge_port_range(self):
  with self.assertRaises(ValueError):E.bridge_lines('obfs4 192.0.2.1:99999 '+('A'*40)+' cert=abc iat-mode=0','obfs4')
 def test_country_mismatch_rejected(self):
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=IR','seconds':.2},{'exit':0,'code':'204','seconds':.3}]),patch.object(E,'settings',return_value=E.DEFAULT):
   r=E.probe('CFON');self.assertFalse(r['healthy']);self.assertEqual(r['error'],'COUNTRY_MISMATCH_OR_UNKNOWN')
 def test_country_valid(self):
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=AT','seconds':.2},{'exit':0,'code':'204','seconds':.3}]),patch.object(E,'settings',return_value=E.DEFAULT):self.assertTrue(E.probe('CFON')['healthy'])
 def test_curl_http_error_not_healthy(self):
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=AT','seconds':.2},{'exit':0,'code':'403','seconds':.3}]):self.assertFalse(E.probe('WARP')['healthy'])
 def test_native_failure_not_healthy(self):
  with patch.object(E,'curl',side_effect=[{'exit':60,'code':'200','body':'ip=1.2.3.4\nloc=AT','seconds':.2},{'exit':0,'code':'204','seconds':.3}]):self.assertFalse(E.probe('WARP')['healthy'])
 def test_process_identity(self):self.assertEqual(E.identity(os.getpid())['pid'],os.getpid())
 def test_missing_pid(self):self.assertIsNone(E.identity(99999999))
 def test_foreign_process_not_owned(self):
  with patch.object(E,'read',return_value={'pid':os.getpid(),'path':'C:/wrong.exe','created':1}):self.assertIsNone(E.owned('TEST'))
 def test_atomic_json(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as d:
   f=pathlib.Path(d)/'state.json';E.write(f,{'v':'فارسی'});E.write(f,{'v':2});self.assertEqual(E.read(f)['v'],2);self.assertEqual(len(list(pathlib.Path(d).iterdir())),1)
 def test_atomic_json_retries_windows_sharing_violation(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as d:
   f=pathlib.Path(d)/'state.json';real=E.os.replace;calls={'n':0}
   def flaky(a,b):
    calls['n']+=1
    if calls['n']<3:raise PermissionError(13,'sharing violation')
    return real(a,b)
   with patch.object(E.os,'replace',side_effect=flaky):E.write(f,{'v':3})
   self.assertEqual(E.read(f)['v'],3);self.assertEqual(calls['n'],3);self.assertEqual(len(list(pathlib.Path(d).iterdir())),1)
 def test_recover_owned_exact_project_listener(self):
  fake={'pid':1234,'path':'C:/trusted/tor.exe','created':99}
  cfg=str((R/'data'/'TOR'/'torrc').resolve())
  with patch.object(E,'listener_pid',return_value=1234),patch.object(E,'identity',return_value=fake),patch.object(E,'deps',return_value={'tor':{'path':'C:/trusted/tor.exe'}}),patch.object(E,'process_commandline',return_value='C:/trusted/tor.exe -f '+cfg),patch.object(E,'write') as w:
   r=E.recover_owned('TOR');self.assertEqual(r['pid'],1234);self.assertTrue(r['recovered']);self.assertTrue(w.called)
 def test_recover_owned_rejects_foreign_commandline(self):
  fake={'pid':1234,'path':'C:/trusted/tor.exe','created':99}
  with patch.object(E,'listener_pid',return_value=1234),patch.object(E,'identity',return_value=fake),patch.object(E,'deps',return_value={'tor':{'path':'C:/trusted/tor.exe'}}),patch.object(E,'process_commandline',return_value='C:/trusted/tor.exe -f C:/foreign/torrc'),patch.object(E,'write') as w:
   self.assertIsNone(E.recover_owned('TOR'));self.assertFalse(w.called)
 def test_start_adopts_exact_project_listener(self):
  recovered={'pid':1,'path':'C:/trusted/warp.exe','created':9}
  with patch.object(E,'owned',return_value=None),patch.object(E,'port_open',return_value=True),patch.object(E,'recover_owned',return_value=recovered),patch.object(E,'service_config') as sc:
   self.assertEqual(E.start('WARP'),recovered);self.assertFalse(sc.called)
 def test_recover_owned_rejects_old_listener(self):
  fake={'pid':1234,'path':'C:/trusted/tor.exe','created':99}
  cfg=str((R/'data'/'TOR'/'torrc').resolve())
  with patch.object(E,'listener_pid',return_value=1234),patch.object(E,'identity',return_value=fake),patch.object(E,'deps',return_value={'tor':{'path':'C:/trusted/tor.exe'}}),patch.object(E,'process_commandline',return_value='C:/trusted/tor.exe -f '+cfg),patch.object(E,'write') as w:
   self.assertIsNone(E.recover_owned('TOR',100));self.assertFalse(w.called)
 def test_recover_owned_rejects_warp_wrong_cache(self):
  fake={'pid':1234,'path':'C:/trusted/warp.exe','created':101}
  with patch.object(E,'listener_pid',return_value=1234),patch.object(E,'identity',return_value=fake),patch.object(E,'deps',return_value={'warp':{'path':'C:/trusted/warp.exe'}}),patch.object(E,'process_commandline',return_value='C:/trusted/warp.exe --bind 127.0.0.1:19410 --cache-dir C:/foreign/cache'),patch.object(E,'write') as w:
   self.assertIsNone(E.recover_owned('WARP',100));self.assertFalse(w.called)
 def test_ensure_waits_for_daemon_listener_handoff(self):
  starter={'pid':111,'path':'C:/trusted/tor.exe','created':100}
  adopted={'pid':222,'path':'C:/trusted/tor.exe','created':101}
  healthy={'healthy':True,'mode':'TOR','error':'','seconds':.2}
  with patch.object(E,'owned',return_value=None),patch.object(E,'start',return_value=starter),patch.object(E,'port_open',side_effect=[False,True,True]),patch.object(E,'recover_owned',return_value=adopted),patch.object(E,'probe',return_value=healthy),patch.object(E,'write'),patch.object(E.time,'sleep',return_value=None):
   self.assertEqual(E.ensure('TOR'),healthy)
 def test_environment_proxy_removed(self):
  with patch.dict(os.environ,{'ALL_PROXY':'http://example.com:999','https_proxy':'http://example.com:999'}):self.assertNotIn('ALL_PROXY',E.env());self.assertNotIn('https_proxy',E.env())
 def test_cancel_before_start(self):
  j='f'*32;p=R/'jobs'/f'{j}.cancel';p.write_text('cancel')
  try:
   with patch.object(E,'JOB',j):
    with self.assertRaises(InterruptedError):E.check()
  finally:p.unlink()
 def test_global_deadline(self):
  with patch.object(E,'DEADLINE',time.monotonic()-1):
   with self.assertRaises(TimeoutError):E.check()
 def test_native_timeout(self):
  with self.assertRaises(TimeoutError):E.native([sys.executable,'-c','import time;time.sleep(10)'],.6)
 def test_occupied_port_refused(self):
  with socket.socket() as s:
   s.bind(('127.0.0.1',0));s.listen();port=s.getsockname()[1]
   with patch.dict(E.PORTS,{'TEST':port}),patch.object(E,'owned',return_value=None),patch.object(E,'recover_owned',return_value=None):
    with self.assertRaisesRegex(RuntimeError,'PORT_OWNED'):E.start('TEST')
 def test_verify_disconnected_managed_path_does_not_curl(self):
  with patch.object(E,'owned',return_value=None),patch.object(E,'port_open',return_value=False),patch.object(E,'probe') as pr:
   r=E.verify('WARP');self.assertFalse(r['healthy']);self.assertFalse(r['connected']);self.assertEqual(r['state'],'NOT_CONNECTED');self.assertEqual(r['error'],'NOT_CONNECTED');self.assertIsNone(r['seconds']);pr.assert_not_called()
 def test_verify_starting_path_does_not_curl(self):
  fake={'pid':1,'path':'x','created':1}
  with patch.object(E,'owned',return_value=fake),patch.object(E,'port_open',return_value=False),patch.object(E,'probe') as pr:
   r=E.verify('WARP');self.assertEqual(r['state'],'STARTING_OR_UNREADY');self.assertEqual(r['error'],'PATH_NOT_READY');pr.assert_not_called()
 def test_verify_foreign_listener_does_not_curl(self):
  with patch.object(E,'owned',return_value=None),patch.object(E,'port_open',return_value=True),patch.object(E,'recover_owned',return_value=None),patch.object(E,'probe') as pr:
   r=E.verify('WARP');self.assertEqual(r['state'],'FOREIGN_OR_STALE_LISTENER');self.assertEqual(r['error'],'PORT_OWNED_BY_ANOTHER_PROCESS');pr.assert_not_called()
 def test_verify_connected_marks_connection_state(self):
  fake={'pid':1,'path':'x','created':1};healthy={'healthy':True,'mode':'WARP','error':'','seconds':.2}
  with patch.object(E,'owned',return_value=fake),patch.object(E,'port_open',return_value=True),patch.object(E,'probe',return_value=healthy):
   r=E.verify('WARP');self.assertTrue(r['connected']);self.assertEqual(r['state'],'CONNECTED_HEALTHY')
 def test_probe_failure_hides_latency_and_classifies_dead_proxy(self):
  with patch.object(E,'curl',side_effect=[{'exit':7,'code':'000','body':'','seconds':2.0},{'exit':7,'code':'000','seconds':2.0}]):
   r=E.probe('WARP');self.assertFalse(r['healthy']);self.assertIsNone(r['seconds']);self.assertEqual(r['error'],'LOCAL_PROXY_UNREACHABLE')
 def test_inventory_distinguishes_connected_and_foreign_listener(self):
  fake={'pid':1,'path':'x','created':1}
  with patch.object(E,'deps',return_value={'warp':{'path':sys.executable},'tor':{'path':sys.executable}}),patch.object(E,'owned',side_effect=lambda m: fake if m=='WARP' else None),patch.object(E,'port_open',side_effect=lambda port: port in (E.PORTS['WARP'],E.PORTS['TOR'])),patch.object(E,'settings',return_value=E.DEFAULT):
   rows={x['mode']:x for x in E.inventory()['providers']};self.assertEqual(rows['WARP']['state'],'CONNECTED_NOT_VERIFIED');self.assertEqual(rows['TOR']['state'],'LISTENER_PRESENT_NOT_OWNED')
 def test_connect_failure_is_structured_for_ui(self):
  with patch.object(E,'settings',return_value=E.DEFAULT|{'order':['WARP']}),patch.object(E,'ensure',side_effect=RuntimeError('PATH_NOT_VERIFIED_WARP')),patch.object(E,'write'):
   r=E.dispatch('Connect','AUTO','');self.assertFalse(r['healthy']);self.assertFalse(r['connected']);self.assertEqual(r['state'],'CONNECT_FAILED');self.assertEqual(r['error'],'ALL_PATHS_FAILED');self.assertIsNone(r['seconds'])
 def test_missing_bridge_skipped(self):
  if (R/'data'/'bridges_webtunnel.txt').exists():self.skipTest('user supplied bridge')
  with self.assertRaisesRegex(ValueError,'MISSING_PRIVATE'):E.ensure('WEBTUNNEL')

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Unit);result=unittest.TextTestRunner(verbosity=2).run(suite)
 E.write(R/'evidence'/'unit_tests.json',{'utc':E.now(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'scope':'Unit validation, ownership and bounded native child; no product tunnel start','success':result.wasSuccessful()})
 raise SystemExit(0 if result.wasSuccessful() else 1)
