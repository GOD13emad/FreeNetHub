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
 def test_test_timeout_settings_are_validated_and_bounded(self):
  good=E.validate_settings(E.DEFAULT|{'testPathMode':'SELECTED','pingTimeoutSec':7,'downloadTimeoutSec':41,'uploadTimeoutSec':43})
  self.assertEqual(good['testPathMode'],'SELECTED');self.assertEqual(good['pingTimeoutSec'],7)
  with self.assertRaises(ValueError):E.validate_settings(E.DEFAULT|{'testPathMode':'INVALID'})
  with patch.object(E,'settings',return_value=E.DEFAULT|{'pingTimeoutSec':999,'downloadTimeoutSec':'bad','uploadTimeoutSec':1}):
   self.assertEqual(E.test_timeouts(),{'ping':30,'download':30,'upload':10})
 def test_path_speed_uses_configured_timeouts(self):
  trace={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=DE','seconds':.1,'bytes':10,'bps':10}
  ping={'exit':0,'code':'204','body':'','seconds':.2,'bytes':0,'bps':0}
  down={'exit':0,'code':'200','body':'','seconds':1,'bytes':2000000,'bps':1000000}
  with patch.object(E,'test_timeouts',return_value={'ping':7,'download':41,'upload':43}),patch.object(E,'owned',return_value={'pid':1}),patch.object(E,'mode_proxy',return_value='socks5h://127.0.0.1:19410'),patch.object(E,'curl',side_effect=[trace,ping,down]) as c,patch.object(E,'cloudflare_upload',return_value={'exit':0,'code':'200','seconds':1,'bytes':500000,'bps':500000}) as up:
   out=E.path_speed('WARP')
  self.assertTrue(out['ok']);self.assertEqual(c.call_args_list[0].kwargs['seconds'],7);self.assertEqual(c.call_args_list[1].kwargs['seconds'],7);self.assertEqual(c.call_args_list[2].kwargs['seconds'],41)
  self.assertEqual(up.call_args.args[1],43)
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
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=IR','seconds':.2},{'exit':0,'code':'204','seconds':.3}]),patch.object(E,'settings',return_value=E.DEFAULT|{'country':'AT'}):
   r=E.probe('CFON');self.assertFalse(r['healthy']);self.assertEqual(r['error'],'COUNTRY_MISMATCH_OR_UNKNOWN')
 def test_country_valid(self):
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=AT','seconds':.2},{'exit':0,'code':'204','seconds':.3}]),patch.object(E,'settings',return_value=E.DEFAULT|{'country':'AT'}):self.assertTrue(E.probe('CFON')['healthy'])
 def test_curl_http_error_not_healthy(self):
  with patch.object(E,'curl',side_effect=[{'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=AT','seconds':.2},{'exit':0,'code':'403','seconds':.3}]):self.assertFalse(E.probe('WARP')['healthy'])
 def test_direct_curl_retries_with_public_dns_resolve_after_system_dns_failure(self):
  calls=[]
  def fake_native(args,timeout):
   calls.append(list(args))
   if '--resolve' not in args:return {'exit':6,'out':'\n__FNH__000 0 0 0','err':'Could not resolve host'}
   return {'exit':0,'out':'payload\n__FNH__200 0.1 7 70','err':''}
  with patch.object(E,'native',side_effect=fake_native),patch.object(E,'public_dns_ips',return_value=['203.0.113.10']):
   r=E.curl('https://raw.githubusercontent.com/example/repo/main/sub',seconds=2)
  self.assertEqual(r['code'],'200');self.assertEqual(r['body'],'payload');self.assertEqual(r['fetchPath'],'PUBLIC_DNS_RESOLVE')
  self.assertIn('--resolve',calls[1]);self.assertIn('raw.githubusercontent.com:443:203.0.113.10',calls[1])
 def test_proxy_curl_never_uses_public_dns_fallback(self):
  with patch.object(E,'native',return_value={'exit':6,'out':'\n__FNH__000 0 0 0','err':'dns'}),patch.object(E,'public_dns_ips') as dns,patch.object(E,'_openssl_direct_fetch') as tls:
   r=E.curl('https://example.com/x',proxy='socks5h://127.0.0.1:19410',seconds=2)
  self.assertEqual(r['code'],'000');dns.assert_not_called();tls.assert_not_called()
 def test_direct_curl_uses_openssl_fallback_after_schannel_failure(self):
  schannel={'exit':35,'out':'\n__FNH__000 0.1 0 0','err':'SEC_E_INVALID_TOKEN'}
  fallback={'exit':0,'code':'204','seconds':.2,'bytes':0,'bps':0,'body':'','error':'','fetchPath':'OPENSSL_DIRECT_FALLBACK'}
  with patch.object(E,'native',return_value=schannel),patch.object(E,'public_dns_ips',return_value=[]),patch.object(E,'_openssl_direct_fetch',return_value=fallback) as tls:
   r=E.curl('https://www.youtube.com/generate_204',seconds=2,body=False)
  self.assertEqual(r['code'],'204');self.assertEqual(r['fetchPath'],'OPENSSL_DIRECT_FALLBACK');tls.assert_called_once()
 def test_bound_curl_uses_requested_base_interface_and_never_unbound_tls_fallback(self):
  calls=[]
  def fake_native(args,timeout):
   calls.append(list(args));return {'exit':6,'out':'\n__FNH__000 0 0 0','err':'dns'}
  with patch.object(E,'native',side_effect=fake_native),patch.object(E,'public_dns_ips',return_value=[]),patch.object(E,'_openssl_direct_fetch') as tls:
   r=E.curl('https://example.com/x',seconds=2,interface='192.0.2.10')
  self.assertEqual(r['code'],'000');self.assertIn('--interface',calls[0]);self.assertIn('192.0.2.10',calls[0]);tls.assert_not_called()
 def test_root_network_context_accepts_pre_tun_bound_trace(self):
  sess={'mode':'PC_TUNNEL','baseRoute':{'sourceAddress':'192.168.20.5','interfaceAlias':'Ethernet 3'},'baseTrace':{'ip':'198.51.100.10','warp':'off'},'verify':{'trace':{'ip':'203.0.113.20','warp':'on'}}}
  reply={'exit':0,'code':'200','body':'ip=198.51.100.10\nwarp=off\ngateway=off\nloc=DE'}
  with patch.object(E,'read',return_value=sess),patch.object(E,'curl',return_value=reply) as c:
   ctx=E.root_network_context()
  self.assertTrue(ctx['bound']);self.assertEqual(ctx['interface'],'192.168.20.5');self.assertIn('PRE_TUN',ctx['proof'])
  self.assertEqual(c.call_args.kwargs['interface'],'192.168.20.5')
 def test_root_network_context_rejects_known_fnh_tunnel_exit(self):
  sess={'mode':'PC_TUNNEL','baseRoute':{'sourceAddress':'192.168.20.5','interfaceAlias':'Ethernet 3'},'baseTrace':{'ip':'198.51.100.10','warp':'off'},'verify':{'trace':{'ip':'203.0.113.20','warp':'on'}}}
  reply={'exit':0,'code':'200','body':'ip=203.0.113.20\nwarp=on\ngateway=off\nloc=DE'}
  with patch.object(E,'read',return_value=sess),patch.object(E,'curl',return_value=reply):
   with self.assertRaisesRegex(RuntimeError,'ROOT_BASE_ROUTE_TUNNEL_LEAK'):E.root_network_context()
 def test_update_release_fetches_through_verified_root_context(self):
  payload=json.dumps({'tag_name':'v4.2.1','name':'test','published_at':'x','html_url':'https://example.invalid','assets':[]})
  ctx={'bound':True,'interface':'192.168.20.5','interfaceAlias':'Ethernet 3','proof':'BOUND_PRE_TUN_SOURCE_AND_TRACE_NOT_POST_TUN'}
  with patch.object(E,'root_network_context',return_value=ctx),patch.object(E,'root_curl',return_value={'exit':0,'code':'200','body':payload}) as rc,patch.object(E,'read',return_value={'releaseRevision':'r36'}):
   out=E.update_release()
  self.assertTrue(out['rootPath']['bound']);self.assertEqual(out['rootPath']['interfaceAlias'],'Ethernet 3')
  self.assertIs(rc.call_args.kwargs['ctx'],ctx)
 @staticmethod
 def _route_text(extra=''):
  return """IPv4 Route Table
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0     192.168.20.1     192.168.20.5     25
%s
        224.0.0.0        240.0.0.0         On-link      192.168.20.5    281
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
"""%extra
 @staticmethod
 def _physical_ifrow():
  return {'ifIndex':18,'adapterName':'Ethernet 3','description':'Intel(R) Ethernet Controller I226-V','hardware':True,'status':'Up','ifType':6}
 def test_direct_route_rejects_broad_foreign_override(self):
  extra='          0.0.0.0        128.0.0.0         10.0.0.1         10.0.0.2      1'
  with patch.object(E,'native',return_value={'exit':0,'out':self._route_text(extra),'err':''}),patch.object(E,'_windows_ipv4_ifindex',return_value=18),patch.object(E,'_windows_if_row2',return_value=self._physical_ifrow()):
   r=E.direct_route()
  self.assertFalse(r['trustedPhysical']);self.assertEqual(r['systemOverrideRoutes'][0]['DestinationPrefix'],'0.0.0.0/1')
 def test_direct_route_ignores_multicast_and_loopback_routes(self):
  with patch.object(E,'native',return_value={'exit':0,'out':self._route_text(),'err':''}),patch.object(E,'_windows_ipv4_ifindex',return_value=18),patch.object(E,'_windows_if_row2',return_value=self._physical_ifrow()):
   r=E.direct_route()
  self.assertTrue(r['trustedPhysical']);self.assertEqual(r['systemOverrideRoutes'],[]);self.assertEqual(r['routeProof'],'ROUTE_EXE+WINDOWS_IPHELPER')
 def test_direct_route_rejects_virtual_default_adapter(self):
  virtual={'ifIndex':18,'adapterName':'vEthernet (Default Switch)','description':'Hyper-V Virtual Ethernet Adapter','hardware':False,'status':'Up','ifType':6}
  with patch.object(E,'native',return_value={'exit':0,'out':self._route_text(),'err':''}),patch.object(E,'_windows_ipv4_ifindex',return_value=18),patch.object(E,'_windows_if_row2',return_value=virtual):
   r=E.direct_route()
  self.assertFalse(r['trustedPhysical'])
 def test_route_print_parser_is_header_locale_independent(self):
  rows=E._route_print_ipv4_rows('عنوان محلی\n 0.0.0.0 0.0.0.0 192.168.1.1 192.168.1.10 25\n 0.0.0.0 128.0.0.0 10.0.0.1 10.0.0.2 1')
  self.assertEqual(len(rows),2);self.assertEqual(str(rows[1]['network']),'0.0.0.0/1')
 def test_ping_direct_timeout_is_structured(self):
  with patch.object(E,'dep_path',return_value='pwsh.exe'),patch.object(E,'native',side_effect=TimeoutError('CHILD_DEADLINE')):
   r=E.ping_direct()
  self.assertFalse(r['ok']);self.assertEqual(r['note'],'ICMP_TIMEOUT')
 def test_upload_timeout_is_structured(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as td:
   with patch.object(E,'ROOT',pathlib.Path(td)),patch.object(E,'JOB',''),patch.object(E,'native',side_effect=TimeoutError('CHILD_DEADLINE')):
    r=E.cloudflare_upload(131072,2,'')
  self.assertEqual(r['exit'],124);self.assertEqual(r['code'],'000')
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


 def test_inventory_missing_optional_dependencies_is_safe(self):
  with patch.object(E,'deps',return_value={'pwsh':sys.executable}),patch.object(E,'singbox_path',return_value=''),patch.object(E,'owned',return_value=None),patch.object(E,'port_open',return_value=False),patch.object(E,'settings',return_value=E.DEFAULT):
   rows=E.inventory()['providers'];self.assertEqual(len(rows),len(E.PORTS));self.assertTrue(all(x['installed'] is False for x in rows));self.assertTrue(all(x['state']=='DEPENDENCY_NOT_CONFIGURED' for x in rows))
 def test_missing_provider_dependency_is_structured(self):
  with patch.object(E,'deps',return_value={}):
   with self.assertRaisesRegex(ValueError,'DEPENDENCY_NOT_CONFIGURED_WARP'):E.check_binary('warp')

 def test_browser_profile_migrates_legacy_identity(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as d:
   rr=pathlib.Path(d);data=rr/'data';legacy=data/'Browser_WARP';legacy.mkdir(parents=True);sentinel=legacy/'Login Data';sentinel.write_bytes(b'identity')
   E.write(data/'browser_profile.json',{'schema':1,'profile':'Browser_WARP','legacyPreserved':True})
   with patch.object(E,'ROOT',rr):
    p=E.browser_profile()
   self.assertEqual(p,data/'Browser_Primary');self.assertFalse(legacy.exists());self.assertEqual((p/'Login Data').read_bytes(),b'identity')
   m=E.read(data/'browser_profile.json');self.assertEqual(m['profile'],'Browser_Primary');self.assertFalse(m['legacyPreserved']);self.assertEqual(m['migratedFrom'],'Browser_WARP')
 def test_browser_profile_migration_conflict_fails_closed(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as d:
   rr=pathlib.Path(d);data=rr/'data';legacy=data/'Browser_WARP';primary=data/'Browser_Primary';legacy.mkdir(parents=True);primary.mkdir();(legacy/'Login Data').write_bytes(b'old');(primary/'Login Data').write_bytes(b'new')
   E.write(data/'browser_profile.json',{'schema':1,'profile':'Browser_WARP'})
   with patch.object(E,'ROOT',rr):
    with self.assertRaisesRegex(ValueError,'BROWSER_PROFILE_MIGRATION_CONFLICT'):E.browser_profile()
   self.assertTrue(legacy.exists());self.assertTrue(primary.exists())

 def test_emergency_candidates_prioritize_private_bridges(self):
  with tempfile.TemporaryDirectory(dir=R/'tests') as d:
   rr=pathlib.Path(d)
   with patch.object(E,'ROOT',rr),patch.object(E,'settings',return_value=E.DEFAULT|{'order':['WARP','TOR']}):
    (rr/'data').mkdir();(rr/'data'/'bridges_webtunnel.txt').write_text('webtunnel 192.0.2.10:443 '+('A'*40)+' url=https://example.com/x ver=0.0.1')
    self.assertEqual(E.emergency_candidates()[0],'WEBTUNNEL');self.assertIn('TOR',E.emergency_candidates());self.assertEqual(len(E.emergency_candidates()),len(set(E.emergency_candidates())))
 def test_chatgpt_probe_requires_primary_and_supporting_edge(self):
  ok={'exit':0,'code':'200','seconds':.1};bad={'exit':7,'code':'000','seconds':.1}
  with patch.object(E,'curl',side_effect=[ok,ok,bad]),patch.object(E,'mode_proxy',return_value='socks5h://127.0.0.1:1'):
   r=E.chatgpt_probe('TOR');self.assertTrue(r['healthy']);self.assertEqual(r['state'],'CHATGPT_EDGE_REACHABLE');self.assertEqual(r['applicationAcceptance'],'EDGE_REACHABILITY_ONLY_NOT_LOGIN')
  with patch.object(E,'curl',side_effect=[bad,ok,ok]),patch.object(E,'mode_proxy',return_value='socks5h://127.0.0.1:1'):
   self.assertFalse(E.chatgpt_probe('TOR')['healthy'])
 def test_chatgpt_dispatch_uses_first_reachable_and_launches(self):
  health={'healthy':True,'mode':'TOR'}
  app={'healthy':True,'mode':'TOR','error':'','state':'CHATGPT_EDGE_REACHABLE'}
  with patch.object(E,'emergency_candidates',return_value=['TOR','WARP']),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health) as en,patch.object(E,'chatgpt_probe',return_value=app),patch.object(E,'browser',return_value={'launched':True}),patch.object(E,'write'),patch.object(E,'stop') as st:
   r=E.dispatch('ChatGPT','AUTO','');self.assertTrue(r['healthy']);self.assertTrue(r['launched']);en.assert_called_once_with('TOR');st.assert_not_called()

 def test_node_pin_meta_and_history_persist(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir()
   E.write(root/'data'/'nodes.json',{'schema':1,'selected':'n1','nodes':[{'id':'n1','name':'old','protocol':'vless','server':'example.com','port':443,'raw':'vless://example','favorite':False,'pinned':False,'rating':0,'tags':[],'note':'','source':'unit'}]})
   with patch.object(E,'ROOT',root):
    r=E.dispatch('NodePin','NODE','n1');self.assertTrue(r['pinned']);self.assertTrue(E.node_store()['nodes'][0]['pinned'])
    meta=root/'jobs'/'node-meta-unit.json';E.write(meta,{'id':'n1','name':'Home SG','note':'stable','tags':['home','sg'],'rating':4})
    r=E.dispatch('NodeMeta','NODE',str(meta));self.assertEqual(r['node']['name'],'Home SG');self.assertEqual(r['node']['rating'],4);self.assertFalse(meta.exists())
    E.node_record_test('n1',{'healthy':True,'country':'SG','ip':'203.0.113.9','seconds':0.2,'error':'','checked':'2026-09-28T00:00:00Z'})
    pub=E.node_public_rows()[0];self.assertEqual(pub['history'][-1]['country'],'SG');self.assertNotIn('ip',pub['history'][-1]);self.assertEqual(pub['tags'],['home','sg'])
 def test_provider_capabilities_expose_node_system_support(self):
  r=E.dispatch('Providers','AUTO','');caps={x['id']:x for x in r['providers']}
  self.assertTrue(caps['NODE']['system']);self.assertTrue(caps['NODE']['country']);self.assertTrue(caps['WARP']['system'])
 def test_public_source_registry_has_independent_families(self):
  self.assertEqual(len(E.PUBLIC_NODE_SOURCES),11)
  self.assertGreaterEqual(len({x[1] for x in E.PUBLIC_NODE_SOURCES}),6)
  self.assertEqual(len({x[0] for x in E.PUBLIC_NODE_SOURCES}),len(E.PUBLIC_NODE_SOURCES))
  self.assertTrue(all(x[2].startswith('https://') for x in E.PUBLIC_NODE_SOURCES))
  names={x[0] for x in E.PUBLIC_NODE_SOURCES}
  self.assertIn('RADIKAL_TOP100',names);self.assertIn('MORPHEUS_BEST',names);self.assertIn('MATIN_SUB1',names);self.assertIn('AURX_HTTP_VERIFIED',names)
  self.assertEqual(E.PUBLIC_NODE_SOURCES[0][0],'AURX_HTTP_VERIFIED');self.assertEqual(E.PUBLIC_NODE_SOURCES[1][0],'MORPHEUS_BEST')
 def test_http_verified_source_is_only_a_ranking_hint(self):
  self.assertLess(E.node_source_quality({'source':'AURX_HTTP_VERIFIED'}),E.node_source_quality({'source':'TCP_ONLY'}))
  self.assertLess(E.node_source_quality({'source':'MORPHEUS_BEST'}),E.node_source_quality({'source':'TCP_ONLY'}))
 def test_verified_country_shards_cover_all_ui_countries(self):
  self.assertEqual(set(E.PUBLIC_COUNTRY_NODE_SOURCES),{'AT','DE','NL','US','CA','GB','FR','SG','JP'})
  self.assertTrue(all(v.startswith('https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-') for v in E.PUBLIC_COUNTRY_NODE_SOURCES.values()))
 def test_country_shard_refresh_promotes_candidates_and_preserves_existing(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir()
   old={'id':'old','raw':'ss://old','protocol':'ss','source':'MANUAL','server':'old.example','port':443,'favorite':True}
   E.write(root/'data'/'nodes.json',{'schema':1,'selected':'old','nodes':[old]})
   incoming={'id':'sg1','raw':'ss://new','protocol':'ss','source':'AURX_COUNTRY_SG','server':'sg.example','port':443}
   with patch.object(E,'ROOT',root),patch.object(E,'curl',return_value={'exit':0,'code':'200','body':'x','error':''}),patch.object(E.NH,'parse_blob',return_value={'nodes':[incoming],'errors':[]}):
    r=E.node_refresh_country_verified('SG',True);s=E.node_store()
   self.assertTrue(r['refreshed']);self.assertEqual(s['nodes'][0]['id'],'sg1');self.assertTrue(any(n['id']=='old' for n in s['nodes']))
 def test_country_shard_fetch_failure_is_nonfatal_record(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir();E.write(root/'data'/'nodes.json',{'schema':1,'selected':'','nodes':[]})
   with patch.object(E,'ROOT',root),patch.object(E,'curl',return_value={'exit':28,'code':'000','error':'timeout'}):
    r=E.node_refresh_country_verified('DE',True)
   self.assertFalse(r['refreshed']);self.assertEqual(r['country'],'DE')
 def test_public_refresh_ttl_skips_network_when_fresh(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir()
   E.write(root/'data'/'nodes.json',{'schema':1,'selected':'manual','nodes':[{'id':'manual','name':'manual','protocol':'vless','server':'example.com','port':443,'uuid':'u','raw':'vless://u@example.com:443','source':'import'}]})
   E.write(root/'data'/'node_public_refresh.json',{'schema':1,'status':'PASS','lastSuccessUtc':E.now(),'sources':['X'],'failedSources':[]})
   with patch.object(E,'ROOT',root),patch.object(E,'curl') as c:
    r=E.node_refresh_public(False);self.assertFalse(r['refreshed']);self.assertTrue(r['fresh']);c.assert_not_called()
 def test_public_refresh_replaces_stale_public_and_preserves_manual_pinned(self):
  def node(i,source,pinned=False):
   return {'id':i,'name':i,'protocol':'vless','server':i+'.example','port':443,'uuid':'11111111-1111-1111-1111-'+i.zfill(12)[-12:],'raw':'vless://x@'+i+'.example:443','source':source,'favorite':False,'pinned':pinned,'rating':0,'tags':[],'note':''}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir()
   E.write(root/'data'/'nodes.json',{'schema':1,'selected':'manual','nodes':[node('manual','import'),node('stale','SRC_A'),node('keep','SRC_A',True)]})
   body='vless://11111111-1111-1111-1111-111111111111@fresh.example:443?security=tls#fresh'
   fake={'exit':0,'code':'200','body':body,'seconds':.1}
   with patch.object(E,'ROOT',root),patch.object(E,'PUBLIC_NODE_SOURCES',( ('SRC_A','family-a','https://a.invalid'),('SRC_B','family-b','https://b.invalid') )),patch.object(E,'curl',return_value=fake),patch.object(E,'node_batch_fast') as batch:
    r=E.node_refresh_public(True);s=E.node_store();ids={n['id'] for n in s['nodes']}
    self.assertTrue(r['refreshed']);self.assertEqual(r['endpointTest'],'DEFERRED_TO_NODE_TEST_ALL');batch.assert_not_called()
    self.assertIn('manual',ids);self.assertIn('keep',ids);self.assertNotIn('stale',ids);self.assertEqual(r['staleDropped'],1);self.assertEqual(E.public_refresh_state()['status'],'PASS')
 def test_public_refresh_parser_id_migration_preserves_user_metadata_only(self):
  old={'id':'old-id','name':'custom-ish','protocol':'trojan','server':'old.example','port':443,'password':'p','raw':'trojan://p@old.example:443#same','source':'SRC_A','favorite':True,'pinned':True,'rating':4,'tags':['keep'],'note':'memo','endpoint_test':{'reachable':True},'performance_test':{'ok':True,'downloadMbps':99},'history':[{'healthy':True}]}
  incoming={'id':'new-id','name':'upstream','protocol':'trojan','server':'old.example','port':443,'password':'p','raw':'trojan://p@old.example:443#same','source':'SRC_A','favorite':False,'pinned':False,'rating':0,'tags':[],'note':''}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir();E.write(root/'data'/'nodes.json',{'schema':1,'selected':'old-id','nodes':[old]})
   with patch.object(E,'ROOT',root),patch.object(E,'PUBLIC_NODE_SOURCES',( ('SRC_A','family-a','https://a.invalid'), )),patch.object(E,'curl',return_value={'exit':0,'code':'200','body':'x'}),patch.object(E.NH,'parse_blob',return_value={'nodes':[incoming],'errors':[]}),patch.object(E,'node_batch_fast',return_value={'reachable':1}):
    r=E.node_refresh_public(True);s=E.node_store()
  self.assertTrue(r['refreshed']);self.assertEqual(len(s['nodes']),1);n=s['nodes'][0]
  self.assertEqual(n['id'],'new-id');self.assertTrue(n['favorite']);self.assertTrue(n['pinned']);self.assertEqual(n['rating'],4);self.assertEqual(n['tags'],['keep']);self.assertEqual(n['note'],'memo')
  self.assertNotIn('performance_test',n);self.assertNotIn('endpoint_test',n);self.assertNotIn('history',n)
 def test_public_refresh_preserves_stale_nodes_from_failed_source(self):
  oldnode={'id':'old-b','name':'old-b','protocol':'vless','server':'old.example','port':443,'uuid':'11111111-1111-1111-1111-111111111111','raw':'vless://x@old.example:443','source':'SRC_B','favorite':False,'pinned':False,'rating':0,'tags':[],'note':''}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir();E.write(root/'data'/'nodes.json',{'schema':1,'selected':'old-b','nodes':[oldnode]})
   good={'exit':0,'code':'200','body':'vless://11111111-1111-1111-1111-111111111112@fresh.example:443?security=tls#fresh','seconds':.1}
   bad={'exit':1,'code':'000','body':'','error':'TIMEOUT'}
   def fc(url,**kwargs):return good if url.endswith('/a') else bad
   with patch.object(E,'ROOT',root),patch.object(E,'PUBLIC_NODE_SOURCES',( ('SRC_A','family-a','https://x.invalid/a'),('SRC_B','family-b','https://x.invalid/b') )),patch.object(E,'curl',side_effect=fc),patch.object(E,'node_batch_fast',return_value={'reachable':1}):
    r=E.node_refresh_public(True);ids={n['id'] for n in E.node_store()['nodes']}
    self.assertIn('old-b',ids);self.assertEqual(r['failedSources'],['SRC_B']);self.assertEqual(r['staleDropped'],0)

 def test_connect_smart_refreshes_node_pool_before_node_candidate(self):
  healthy={'healthy':True,'mode':'NODE','country':'SG','error':'','seconds':.1}
  with patch.object(E,'connect_candidates',return_value=['NODE']),patch.object(E,'node_refresh_public',return_value={'fresh':True}) as rr,patch.object(E,'ensure_node',return_value=healthy),patch.object(E,'write'):
   r=E.dispatch('Connect','NODE','');self.assertTrue(r['healthy']);rr.assert_called_once_with(False)

 def test_node_stop_removes_sensitive_runtime_config_when_inactive(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);d=root/'data'/'NODE';d.mkdir(parents=True);(d/'config.json').write_text('secret');(d/'node-id.txt').write_text('id');(d/'owner.json').write_text('{}')
   with patch.object(E,'ROOT',root),patch.object(E,'owned',return_value=None),patch.object(E,'port_open',return_value=False):
    self.assertFalse(E.stop('NODE'))
   self.assertFalse((d/'config.json').exists());self.assertFalse((d/'node-id.txt').exists());self.assertFalse((d/'owner.json').exists())
 def test_speed_dispatch_always_uses_direct_measurement(self):
  with patch.object(E,'direct_speed',return_value={'ok':True,'mode':'DIRECT'}) as ds:
   r=E.dispatch('Speed','WARP','');self.assertEqual(r['mode'],'DIRECT');ds.assert_called_once_with()
 def test_direct_speed_rejects_nonphysical_default_route(self):
  with patch.object(E,'direct_route',return_value={'trustedPhysical':False}):
   with self.assertRaisesRegex(RuntimeError,'DIRECT_SPEED_NON_PHYSICAL'):E.direct_speed()
 def test_direct_speed_reports_download_upload_and_path(self):
  tr={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=IR\nwarp=off\ngateway=off','seconds':.1}
  down={'exit':0,'code':'200','bytes':5000000,'bps':12500000,'seconds':.4}
  up={'exit':0,'code':'200','bytes':1000000,'bps':2500000,'seconds':.4}
  route={'trustedPhysical':True,'adapterName':'Ethernet','description':'Intel','hardware':True,'status':'Up','ip':'192.0.2.10'}
  with patch.object(E,'direct_route',return_value=route),patch.object(E,'curl',side_effect=[tr,down]),patch.object(E,'ping_direct',return_value={'ok':True,'avgMs':12.5}),patch.object(E,'cloudflare_upload',return_value=up):
   r=E.direct_speed();self.assertTrue(r['ok']);self.assertFalse(r['proxyUsed']);self.assertEqual(r['downloadMbps'],100.0);self.assertEqual(r['uploadMbps'],20.0);self.assertEqual(r['pingMs'],12.5)
 def test_direct_speed_rejects_cloudflare_warp(self):
  tr={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=IR\nwarp=on\ngateway=off','seconds':.1}
  with patch.object(E,'direct_route',return_value={'trustedPhysical':True}),patch.object(E,'curl',return_value=tr):
   with self.assertRaisesRegex(RuntimeError,'DIRECT_SPEED_SYSTEM_TUNNEL'):E.direct_speed()

 def test_path_speed_uses_active_provider_proxy(self):
  tr={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=SG\nwarp=off','seconds':.1}
  ping={'exit':0,'code':'204','bytes':0,'bps':0,'seconds':.05}
  down={'exit':0,'code':'200','bytes':2000000,'bps':10000000,'seconds':.2}
  up={'exit':0,'code':'200','bytes':500000,'bps':2500000,'seconds':.2}
  with patch.object(E,'owned',return_value={'pid':1}),patch.object(E,'mode_proxy',return_value='socks5h://127.0.0.1:19410'),patch.object(E,'curl',side_effect=[tr,ping,down]) as c,patch.object(E,'cloudflare_upload',return_value=up) as u:
   r=E.path_speed('WARP');self.assertTrue(r['ok']);self.assertTrue(r['proxyUsed']);self.assertEqual(r['country'],'SG');self.assertEqual(r['downloadMbps'],80.0);self.assertEqual(r['uploadMbps'],20.0)
   self.assertEqual(c.call_args_list[0].args[1],'socks5h://127.0.0.1:19410');u.assert_called_once_with(500000,30,'socks5h://127.0.0.1:19410')
 def test_connect_provider_warp_ignores_global_country(self):
  health={'healthy':True,'mode':'WARP','country':'IR','error':''}
  with patch.object(E,'country_target',return_value='SG'),patch.object(E,'ensure',return_value=health) as en,patch.object(E,'write') as wr:
   r=E.dispatch('ConnectProvider','WARP','')
  self.assertTrue(r['healthy']);en.assert_called_once_with('WARP');wr.assert_called_once()
 def test_connect_provider_rejects_country_capable_modes(self):
  with self.assertRaisesRegex(ValueError,'PROVIDER_CONNECT_MODE_UNSUPPORTED'):
   E.dispatch('ConnectProvider','NODE','')
 def test_provider_benchmark_auto_tests_all_smart_candidates_and_cleans_temporary(self):
  node_h={'healthy':True,'mode':'NODE','country':'SG','error':''};cfon_h={'healthy':True,'mode':'CFON','country':'SG','error':''}
  speeds={'NODE':{'ok':True,'mode':'NODE','country':'SG','pingMs':20,'downloadMbps':10,'uploadMbps':1},'CFON':{'ok':True,'mode':'CFON','country':'SG','pingMs':40,'downloadMbps':20,'uploadMbps':2}}
  with patch.object(E,'connect_candidates',return_value=['NODE','CFON']),patch.object(E,'smart_benchmark_candidates',return_value=['NODE','CFON']),patch.object(E,'country_target',return_value='SG'),patch.object(E,'owned',return_value=None),patch.object(E,'ensure_node',return_value=node_h) as en,patch.object(E,'ensure',return_value=cfon_h) as ens,patch.object(E,'path_speed',side_effect=lambda m:speeds[m]) as ps,patch.object(E,'node_selected',return_value=None),patch.object(E,'write'),patch.object(E,'stop') as st:
   r=E.dispatch('ProviderBenchmark','AUTO','')
  self.assertEqual(r['provider'],'NODE');self.assertTrue(r['temporary']);self.assertEqual(r['attempts'],[])
  self.assertEqual([x['provider'] for x in r['results']],['NODE','CFON']);en.assert_called_once_with('SG');ens.assert_called_once_with('CFON');self.assertEqual(ps.call_count,2)
  self.assertEqual(st.call_count,2);st.assert_any_call('NODE');st.assert_any_call('CFON')
 def test_provider_benchmark_auto_records_failure_and_still_tests_later_candidate(self):
  health={'healthy':True,'mode':'TOR','country':'','error':''};perf={'ok':True,'mode':'TOR','pingMs':30,'downloadMbps':5,'uploadMbps':1}
  def ensure(mode):
   if mode=='WARP':raise RuntimeError('WARP_FAIL')
   return health
  with patch.object(E,'connect_candidates',return_value=['WARP','TOR']),patch.object(E,'smart_benchmark_candidates',return_value=['WARP','TOR']),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',side_effect=ensure),patch.object(E,'path_speed',return_value=perf),patch.object(E,'write'),patch.object(E,'stop') as st:
   r=E.dispatch('ProviderBenchmark','AUTO','')
  self.assertEqual(r['provider'],'TOR');self.assertEqual(r['attempts'][0]['mode'],'WARP')
  self.assertEqual([x['provider'] for x in r['results']],['WARP','TOR']);self.assertEqual(st.call_count,2)
 def test_console_speed_dispatch_uses_console_path(self):
  with patch.object(E,'console_speed',return_value={'ok':True,'mode':'CONSOLE'}) as cs:
   r=E.dispatch('ConsoleSpeed','CONSOLE','');self.assertTrue(r['ok']);cs.assert_called_once_with()
 def test_node_system_preflight_requires_same_tcp_udp_country_and_stops_temporary(self):
  node={'id':'sel','protocol':'ss','source':'AURX_HTTP_VERIFIED','server':'example.com','port':443}
  store={'schema':1,'selected':'sel','nodes':[node]}
  health={'healthy':True,'country':'SG','error':''}
  perf={'ok':True,'pingMs':100,'downloadMbps':2.5,'uploadMbps':1.2,'country':'SG','checked':E.now(),'error':''}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_selected',return_value=node),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health),patch.object(E,'country_target',return_value='SG'),patch.object(E,'node_udp_preflight',return_value={'ok':True,'country':'SG','seconds':.1}),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_test'),patch.object(E,'node_record_performance'),patch.object(E,'stop') as st:
   r=E.node_system_preflight()
  self.assertTrue(r['systemEligible']);self.assertTrue(r['ok']);self.assertEqual(r['country'],'SG');self.assertEqual(r['udpCountry'],'SG');st.assert_called_once_with('NODE')
 def test_node_system_preflight_auto_selects_country_node_and_cleans_temporary(self):
  node={'id':'auto','protocol':'vless','source':'MORPHEUS_BEST','server':'example.com','port':443}
  health={'healthy':True,'country':'DE','error':''};perf={'ok':True,'pingMs':90,'downloadMbps':8.0,'uploadMbps':2.0,'country':'DE','checked':E.now(),'error':''}
  owned_calls=[None,{'nodeId':'auto'}]
  with patch.object(E,'node_store',return_value={'schema':1,'selected':'old','nodes':[node]}),patch.object(E,'country_target',return_value='DE'),patch.object(E,'owned',side_effect=owned_calls),patch.object(E,'ensure_node',return_value=health) as en,patch.object(E,'node_selected',return_value=node),patch.object(E,'node_udp_preflight',return_value={'ok':True,'country':'DE','seconds':.1}),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_performance'),patch.object(E,'stop') as st:
   r=E.node_system_preflight_auto()
  en.assert_called_once_with('DE');self.assertEqual(r['selectionPolicy'],'AUTO');self.assertEqual(r['country'],'DE');self.assertEqual(r['udpCountry'],'DE');self.assertTrue(r['temporary']);st.assert_called_once_with('NODE')
 def test_node_system_preflight_auto_dispatch(self):
  with patch.object(E,'node_system_preflight_auto',return_value={'ok':True,'selectionPolicy':'AUTO'}) as ap:
   r=E.dispatch('NodeSystemPreflightAuto','NODE','');self.assertTrue(r['ok']);ap.assert_called_once_with()
 def test_node_system_preflight_keeps_eligibility_when_speed_sample_incomplete(self):
  node={'id':'sel','protocol':'ss','source':'AURX_HTTP_VERIFIED','server':'example.com','port':443}
  store={'schema':1,'selected':'sel','nodes':[node]}
  health={'healthy':True,'country':'SG','error':''};perf={'ok':False,'pingMs':200,'downloadMbps':0.0,'uploadMbps':.4,'country':'SG','error':'THROUGHPUT_SAMPLE_INCOMPLETE'}
  saved=[]
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_selected',return_value=node),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health),patch.object(E,'country_target',return_value='AUTO'),patch.object(E,'node_udp_preflight',return_value={'ok':True,'country':'SG','seconds':.1}),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_test'),patch.object(E,'node_record_performance',side_effect=lambda nid,p:saved.append(p)),patch.object(E,'stop'):
   r=E.node_system_preflight()
  self.assertTrue(r['systemEligible']);self.assertFalse(r['ok']);self.assertIsNone(r['downloadMbps']);self.assertIsNone(r['uploadMbps']);self.assertIsNone(saved[0]['downloadMbps'])
 def test_system_speed_accepts_active_node_tunnel_without_warp_flag(self):
  sess={'mode':'PC_TUNNEL','provider':'NODE'}
  trace={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=SG\nwarp=off','seconds':.1}
  ping={'exit':0,'code':'204','body':'','seconds':.2}
  down={'exit':0,'code':'200','body':'','seconds':.3,'bps':1000000}
  up={'exit':0,'code':'200','body':'','seconds':.3,'bps':500000}
  def rd(path,default=None):
   return sess if str(path).endswith('gateway-session.json') else default
  with patch.object(E,'read',side_effect=rd),patch.object(E,'curl',side_effect=[trace,ping,down]),patch.object(E,'cloudflare_upload',return_value=up),patch.object(E,'country_target',return_value='SG'):
   r=E.system_speed('NODE')
  self.assertTrue(r['ok']);self.assertEqual(r['provider'],'NODE');self.assertEqual(r['country'],'SG')
 def test_system_speed_rejects_provider_mismatch(self):
  with patch.object(E,'read',return_value={'mode':'PC_TUNNEL','provider':'WARP'}):
   with self.assertRaisesRegex(RuntimeError,'SYSTEM_TUNNEL_NOT_ACTIVE'):E.system_speed('NODE')
 def test_console_preflight_dispatch_uses_preconnect_path(self):
  with patch.object(E,'console_preflight_speed',return_value={'ok':True,'mode':'CONSOLE_PREFLIGHT'}) as cp:
   r=E.dispatch('ConsolePreflight','CONSOLE','');self.assertTrue(r['ok']);cp.assert_called_once_with()
 def test_console_preflight_starts_measures_and_cleans_temporary_provider(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);runtime=root/'gateway'/'runtime';runtime.mkdir(parents=True);provider=root/'gateway'/'console_provider.ps1';provider.write_text('# unit');E.write(runtime/'local_provider.json',{'type':'mihomo_source','country':'DE'})
   calls=[]
   def fake_native(args,timeout):
    action=args[args.index('-Action')+1];calls.append(action)
    rp=pathlib.Path(args[args.index('-ResultPath')+1])
    if action=='Start':
     E.write(runtime/'console-provider-owner.json',{'listen':'127.0.0.1','port':19591})
     E.write(rp,{'status':'PASS','state':'STARTED'})
    else:
     (runtime/'console-provider-owner.json').unlink(missing_ok=True);E.write(rp,{'status':'PASS','state':'STOPPED'})
    return {'exit':0,'out':'','err':''}
   tr={'exit':0,'code':'200','body':'ip=1.2.3.4\nloc=DE\nwarp=off','seconds':.1,'bytes':100,'bps':1000}
   yt={'exit':0,'code':'204','body':'','seconds':.08,'bytes':0,'bps':0}
   down={'exit':0,'code':'200','body':'','seconds':.2,'bytes':1500000,'bps':7500000}
   up={'exit':0,'code':'200','body':'','seconds':.2,'bytes':350000,'bps':1750000}
   with patch.object(E,'ROOT',root),patch.object(E,'dep_path',return_value=sys.executable),patch.object(E,'native',side_effect=fake_native),patch.object(E,'curl',side_effect=[tr,yt,down]),patch.object(E,'cloudflare_upload',return_value=up),patch.object(E,'progress'):
    r=E.console_preflight_speed()
   self.assertTrue(r['ok']);self.assertTrue(r['temporary']);self.assertEqual(r['country'],'DE');self.assertEqual(calls,['Start','Stop']);self.assertFalse((runtime/'console-provider-owner.json').exists())
 def test_node_public_rows_smart_prefers_full_health_over_tcp_only(self):
  healthy={'id':'healthy','name':'healthy','protocol':'vless','endpoint_test':{'reachable':True,'latency_ms':250},'performance_test':{'ok':True,'pingMs':800,'downloadMbps':5,'uploadMbps':1,'checked':E.now()}}
  tcp={'id':'tcp','name':'tcp','protocol':'vless','endpoint_test':{'reachable':True,'latency_ms':1}}
  rows=E.node_public_rows({'schema':1,'selected':'','nodes':[tcp,healthy]})
  self.assertEqual(rows[0]['id'],'healthy')
 def test_node_endpoint_freshness_reuses_recent_fast_scan(self):
  stamp=E.now();store={'schema':1,'selected':'n0','nodes':[{'id':'n0','endpoint_test':{'reachable':True,'checked':stamp}},{'id':'n1','endpoint_test':{'reachable':False,'checked':stamp}}]}
  self.assertTrue(E.node_endpoint_tests_fresh(store,300))
 def test_node_endpoint_scan_rejects_future_and_undated_proofs(self):
  import datetime as dt
  future=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=365)).isoformat()
  valid=E.now()
  node={'id':'n0','endpoint_test':{'reachable':True,'checked':future}}
  store={'schema':1,'selected':'n0','nodes':[node]}
  self.assertFalse(E.node_endpoint_tests_fresh(store,300))
  node['endpoint_test']['checked']=valid
  self.assertTrue(E.node_endpoint_tests_fresh(store,300))
  node['endpoint_test']['checked']=dt.datetime.now().isoformat()
  self.assertFalse(E.node_endpoint_tests_fresh(store,300))
  node['endpoint_test']['checked']='2000-01-01T00:00:00+00:00'
  self.assertFalse(E.node_endpoint_tests_fresh(store,300))
 def test_node_benchmark_reuses_fresh_endpoint_evidence_without_rescan(self):
  stamp=E.now();nodes=[
   {'id':'s','protocol':'ss','source':'AURX_HTTP_VERIFIED','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':10,'checked':stamp}},
   {'id':'v','protocol':'vless','source':'MORPHEUS_BEST','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':20,'checked':stamp}},
   {'id':'m','protocol':'vmess','source':'A','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':30,'checked':stamp}},
   {'id':'t','protocol':'trojan','source':'B','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':40,'checked':stamp}},
  ]
  store={'schema':1,'selected':'s','nodes':nodes};health={'healthy':True,'country':'DE','error':''};perf={'ok':True,'pingMs':10,'downloadMbps':20,'uploadMbps':5,'country':'DE'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast') as fast,patch.object(E,'owned',return_value=None),patch.object(E,'node_select'),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_performance'),patch.object(E,'stop'):
   r=E.dispatch('NodeBenchmarkBatch','NODE','')
  fast.assert_not_called();self.assertEqual(r['benchmarked'],4);self.assertEqual(r['passed'],4)
 def test_node_refresh_smart_uses_ttl_refresh_path(self):
  with patch.object(E,'node_refresh_public',return_value={'refreshed':False,'fresh':True}) as rr:
   r=E.dispatch('NodeRefreshSmart','NODE','');self.assertTrue(r['fresh']);rr.assert_called_once_with(False)
 def test_provider_benchmark_temporary_managed_path_cleans_up(self):
  health={'healthy':True,'mode':'WARP','country':'','error':''};perf={'ok':True,'mode':'WARP'}
  with patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health),patch.object(E,'path_speed',return_value=perf),patch.object(E,'stop') as st:
   r=E.dispatch('ProviderBenchmark','WARP','');self.assertTrue(r['temporary']);self.assertEqual(r['provider'],'WARP');st.assert_called_once_with('WARP')
 def test_provider_benchmark_existing_managed_path_is_preserved(self):
  health={'healthy':True,'mode':'WARP','country':'','error':''};perf={'ok':True,'mode':'WARP'}
  with patch.object(E,'owned',return_value={'pid':1}),patch.object(E,'ensure',return_value=health),patch.object(E,'path_speed',return_value=perf),patch.object(E,'stop') as st:
   r=E.dispatch('ProviderBenchmark','WARP','');self.assertFalse(r['temporary']);st.assert_not_called()
 def test_node_benchmark_batch_is_bounded_to_four_and_cleans_each(self):
  nodes=[{'id':f'n{i}','protocol':'vless','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':i}} for i in range(12)]
  store={'schema':1,'selected':'n0','nodes':nodes}
  health={'healthy':True,'country':'SG','error':''};perf={'ok':True,'pingMs':10,'downloadMbps':20,'uploadMbps':5,'country':'SG'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':12}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select'),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=perf) as ps,patch.object(E,'node_record_performance'),patch.object(E,'stop') as st:
   r=E.dispatch('NodeBenchmarkBatch','NODE','');self.assertEqual(r['benchmarked'],4);self.assertEqual(r['eligible'],12);self.assertEqual(r['remainingUnbenchmarked'],12);self.assertEqual(ps.call_count,4);self.assertEqual(st.call_count,4)
 def test_connect_selected_node_uses_selected_without_reselection(self):
  node={'id':'sel','protocol':'ss','source':'x','server':'example.com','port':443,'endpoint_test':{'reachable':True}}
  store={'schema':1,'selected':'sel','nodes':[node]}
  health={'healthy':True,'country':'SG','error':''}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_selected',return_value=node),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health) as en,patch.object(E,'country_target',return_value='SG'),patch.object(E,'node_record_test'),patch.object(E,'write'),patch.object(E,'stop') as st:
   r=E.dispatch('ConnectSelectedNode','NODE','')
  self.assertTrue(r['healthy']);self.assertEqual(r['selected'],'sel');en.assert_called_once_with('NODE');st.assert_not_called()
 def test_connect_selected_node_country_mismatch_stops_started_node(self):
  node={'id':'sel','protocol':'ss','source':'x','server':'example.com','port':443,'endpoint_test':{'reachable':True}}
  store={'schema':1,'selected':'sel','nodes':[node]}
  health={'healthy':True,'country':'US','error':''}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_selected',return_value=node),patch.object(E,'owned',return_value=None),patch.object(E,'ensure',return_value=health),patch.object(E,'country_target',return_value='SG'),patch.object(E,'stop') as st:
   with self.assertRaisesRegex(RuntimeError,'NODE_TCP_COUNTRY_MISMATCH'):E.dispatch('ConnectSelectedNode','NODE','')
  st.assert_called_once_with('NODE')
 def test_node_benchmark_incomplete_throughput_is_fail_and_na(self):
  nodes=[{'id':'n0','protocol':'ss','source':'AURX_HTTP_VERIFIED','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':22}}]
  store={'schema':1,'selected':'n0','nodes':nodes};saved=[]
  health={'healthy':True,'country':'CA','error':''}
  partial={'ok':False,'pingMs':321.0,'pingType':'HTTPS_RTT','downloadMbps':0.0,'uploadMbps':0.5,'country':'CA','checked':E.now(),'error':'THROUGHPUT_SAMPLE_INCOMPLETE'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':1}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select'),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=partial),patch.object(E,'node_record_performance',side_effect=lambda nid,perf:saved.append(perf)),patch.object(E,'stop'):
   r=E.dispatch('NodeBenchmarkBatch','NODE','')
  self.assertEqual(r['passed'],0);self.assertEqual(r['failed'],1);self.assertEqual(r['results'][0]['status'],'FAIL');self.assertIsNone(r['results'][0]['downloadMbps']);self.assertIsNone(r['results'][0]['uploadMbps']);self.assertEqual(r['results'][0]['pingMs'],321.0);self.assertIsNone(saved[0]['downloadMbps']);self.assertEqual(saved[0]['error'],'THROUGHPUT_SAMPLE_INCOMPLETE')
 def test_node_benchmark_failure_uses_na_for_throughput_and_keeps_tcp_delay(self):
  nodes=[{'id':'n0','protocol':'vless','source':'SRC','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':37}}]
  store={'schema':1,'selected':'n0','nodes':nodes};saved=[]
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':1}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select'),patch.object(E,'ensure',side_effect=RuntimeError('PATH_NOT_VERIFIED_NODE')),patch.object(E,'node_record_test'),patch.object(E,'node_record_performance',side_effect=lambda nid,perf:saved.append((nid,perf))),patch.object(E,'stop'):
   r=E.dispatch('NodeBenchmarkBatch','NODE','')
  self.assertEqual(r['benchmarked'],1);self.assertEqual(r['passed'],0);self.assertEqual(r['failed'],1);self.assertEqual(r['results'][0]['pingMs'],37);self.assertIsNone(r['results'][0]['downloadMbps']);self.assertIsNone(r['results'][0]['uploadMbps']);self.assertEqual(saved[0][1]['pingType'],'TCP_CONNECT');self.assertIsNone(saved[0][1]['downloadMbps'])
 def test_node_benchmark_prioritizes_protocols_with_fewer_prior_attempts(self):
  nodes=[
   {'id':'v0','protocol':'vless','source':'A','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':1},'performance_test':{'ok':False}},
   {'id':'v1','protocol':'vless','source':'B','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':2}},
   {'id':'t0','protocol':'trojan','source':'C','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':3}},
   {'id':'m0','protocol':'vmess','source':'D','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':4}},
   {'id':'s0','protocol':'ss','source':'E','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':5}},
   {'id':'h0','protocol':'hysteria2','source':'F','pinned':False,'favorite':False,'endpoint_test':{'reachable':False,'latency_ms':None}},
  ]
  store={'schema':1,'selected':'v0','nodes':nodes};selected=[]
  def sel(nid):selected.append(nid);return next(n for n in nodes if n['id']==nid)
  health={'healthy':True,'country':'SG','error':''};perf={'ok':True,'pingMs':10,'downloadMbps':20,'uploadMbps':5,'country':'SG'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':5}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select',side_effect=sel),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_performance'),patch.object(E,'stop'):
   E.dispatch('NodeBenchmarkBatch','NODE','')
  self.assertEqual(len(selected),4)
  selected_protocols={next(n['protocol'] for n in nodes if n['id']==nid) for nid in selected}
  self.assertEqual(len(selected_protocols),4)
  self.assertIn('vmess',selected_protocols);self.assertIn('ss',selected_protocols);self.assertNotIn('v0',selected)
 def test_node_benchmark_spreads_first_wave_across_sources(self):
  nodes=[]
  for i,src in enumerate(['A','A','A','B','B','C','D','E']):
   nodes.append({'id':f'n{i}','protocol':'vless','source':src,'pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':i+1}})
  store={'schema':1,'selected':'n0','nodes':nodes};selected=[]
  def sel(nid):selected.append(nid);return next(n for n in nodes if n['id']==nid)
  health={'healthy':True,'country':'SG','error':''};perf={'ok':True,'pingMs':10,'downloadMbps':20,'uploadMbps':5,'country':'SG'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':8}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select',side_effect=sel),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_performance'),patch.object(E,'stop'):
   E.dispatch('NodeBenchmarkBatch','NODE','')
  self.assertEqual(selected,['n0','n3','n5','n6'])
 def test_node_benchmark_prioritizes_unbenchmarked_before_pinned_old_metrics(self):
  old={'id':'old','protocol':'vless','pinned':True,'favorite':True,'endpoint_test':{'reachable':True,'latency_ms':1},'performance_test':{'ok':True,'downloadMbps':99}}
  fresh=[{'id':f'n{i}','protocol':'vless','pinned':False,'favorite':False,'endpoint_test':{'reachable':True,'latency_ms':10+i}} for i in range(5)]
  store={'schema':1,'selected':'old','nodes':[old]+fresh};selected=[]
  def sel(nid):selected.append(nid);return next(n for n in store['nodes'] if n['id']==nid)
  health={'healthy':True,'country':'SG','error':''};perf={'ok':True,'pingMs':10,'downloadMbps':20,'uploadMbps':5,'country':'SG'}
  with patch.object(E,'node_store',return_value=store),patch.object(E,'node_batch_fast',return_value={'reachable':6}),patch.object(E,'owned',return_value=None),patch.object(E,'node_select',side_effect=sel),patch.object(E,'ensure',return_value=health),patch.object(E,'node_record_test'),patch.object(E,'path_speed',return_value=perf),patch.object(E,'node_record_performance'),patch.object(E,'stop'):
   E.dispatch('NodeBenchmarkBatch','NODE','')
  self.assertNotIn('old',selected);self.assertEqual(selected,['n0','n1','n2','n3'])
 def test_update_release_compares_r_revision(self):
  body=json.dumps({'tag_name':'v4.2.0-r29','name':'R29','published_at':'x','html_url':'https://example.invalid','assets':[{'name':'FreeNetHub_4.2.0_R29_Setup.exe','browser_download_url':'https://example.invalid/x.exe','size':1,'digest':'sha256:'+'a'*64}]})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'4.2.0-local-r28-final'}):
   r=E.update_release();self.assertTrue(r['updateAvailable']);self.assertEqual(r['currentRevisionNumber'],28);self.assertEqual(r['remoteRevisionNumber'],29)
 def test_v432_r44_to_r46_update_transition(self):
  body=json.dumps({'tag_name':'v4.3.2','name':'FreeNet Hub 4.3.2','published_at':'x','html_url':'https://example.invalid','assets':[{'name':'FreeNetHub_4.3.2_R46_Setup.exe','browser_download_url':'https://example.invalid/r46.exe','size':1,'digest':'sha256:'+'a'*64}]})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'4.3.1-r44-final'}):
   r=E.update_release();self.assertTrue(r['revisionComparable']);self.assertTrue(r['updateAvailable']);self.assertEqual(r['currentRevisionNumber'],44);self.assertEqual(r['remoteRevisionNumber'],46);self.assertEqual(r['asset']['name'],'FreeNetHub_4.3.2_R46_Setup.exe')
 def test_update_release_uses_manifest_revision_when_release_file_missing(self):
  body=json.dumps({'tag_name':'v4.2.0-r27','name':'R27','published_at':'x','html_url':'https://example.invalid','assets':[{'name':'FreeNetHub_4.2.0_R27_Setup.exe','browser_download_url':'https://example.invalid/x.exe','size':1,'digest':'sha256:'+'a'*64}]})
  def fake_read(path,default=None):
   return {'coreVersion':'4.0-r28-final-provider-capability'} if str(path).endswith('manifest.json') else {}
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',side_effect=fake_read):
   r=E.update_release();self.assertFalse(r['updateAvailable']);self.assertEqual(r['currentRevisionNumber'],28);self.assertEqual(r['remoteRevisionNumber'],27)
 def test_update_release_fails_closed_when_local_revision_is_unparseable(self):
  body=json.dumps({'tag_name':'v4.2.0-r29','name':'R29','published_at':'x','html_url':'https://example.invalid','assets':[{'name':'FreeNetHub_4.2.0_R29_Setup.exe','browser_download_url':'https://example.invalid/x.exe','size':1,'digest':'sha256:'+'a'*64}]})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'unknown'}):
   r=E.update_release();self.assertFalse(r['revisionComparable']);self.assertFalse(r['updateAvailable']);self.assertEqual(r['remoteRevisionNumber'],29)
 def test_update_release_fails_closed_when_remote_revision_is_unparseable(self):
  body=json.dumps({'tag_name':'latest','name':'Latest','published_at':'x','html_url':'https://example.invalid','assets':[{'name':'FreeNetHub_Setup.exe','browser_download_url':'https://example.invalid/x.exe','size':1,'digest':'sha256:'+'a'*64}]})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'4.2.0-local-r28-final'}):
   r=E.update_release();self.assertFalse(r['revisionComparable']);self.assertFalse(r['updateAvailable']);self.assertEqual(r['remoteRevisionNumber'],0)
 def test_update_release_selects_highest_revisioned_installer_asset(self):
  assets=[
   {'name':'FreeNetHub_4.2.0_R28_Setup.exe','browser_download_url':'https://example.invalid/r28.exe','size':1,'digest':'sha256:'+'a'*64},
   {'name':'FreeNetHub_4.2.0_R30_Setup.exe','browser_download_url':'https://example.invalid/r30.exe','size':1,'digest':'sha256:'+'b'*64},
   {'name':'FreeNetHub_Setup.exe','browser_download_url':'https://example.invalid/unversioned.exe','size':1,'digest':'sha256:'+'c'*64},
  ]
  body=json.dumps({'tag_name':'v4.2.0-r30','name':'R30','published_at':'x','html_url':'https://example.invalid','assets':assets})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'4.2.0-local-r29-final'}):
   r=E.update_release();self.assertTrue(r['revisionComparable']);self.assertTrue(r['updateAvailable']);self.assertEqual(r['remoteRevisionNumber'],30);self.assertEqual(r['asset']['name'],'FreeNetHub_4.2.0_R30_Setup.exe')
 def test_update_release_ignores_non_installer_exe_even_with_higher_revision(self):
  assets=[
   {'name':'FreeNetHub_4.2.0_R99_Diagnostic.exe','browser_download_url':'https://example.invalid/tool.exe','size':1,'digest':'sha256:'+'c'*64},
   {'name':'FreeNetHub_4.2.0_R40_LifecycleSafe_Setup.exe','browser_download_url':'https://example.invalid/setup.exe','size':1,'digest':'sha256:'+'d'*64},
  ]
  body=json.dumps({'tag_name':'v4.2.0-r40','name':'R40','published_at':'x','html_url':'https://example.invalid','assets':assets})
  with patch.object(E,'curl',return_value={'exit':0,'code':'200','body':body}),patch.object(E,'read',return_value={'releaseRevision':'4.2.0-local-r39-final'}):
   r=E.update_release();self.assertTrue(r['updateAvailable']);self.assertEqual(r['remoteRevisionNumber'],40);self.assertEqual(r['asset']['name'],'FreeNetHub_4.2.0_R40_LifecycleSafe_Setup.exe')
 def test_system_speed_probe_failure_is_structured_when_session_is_active(self):
  sess={'mode':'PC_TUNNEL','provider':'WARP'}
  badtrace={'exit':28,'code':'000','body':'','seconds':None}
  badyt={'exit':28,'code':'000','body':'','seconds':None}
  with patch.object(E,'read',return_value=sess),patch.object(E,'curl',side_effect=[badtrace,badyt]),patch.object(E,'cloudflare_upload') as up:
   out=E.system_speed('WARP')
  self.assertFalse(out['ok']);self.assertEqual(out['error'],'SYSTEM_SPEED_VERIFICATION_FAILED');up.assert_not_called()

 def test_path_speed_verification_failure_is_structured_not_exception(self):
  trace={'exit':0,'code':'200','body':'ip=198.51.100.7\nloc=US','seconds':.2}
  youtube={'exit':28,'code':'000','body':'','seconds':None}
  with patch.object(E,'owned',return_value={'pid':1}),patch.object(E,'mode_proxy',return_value='socks5h://127.0.0.1:19410'),patch.object(E,'curl',side_effect=[trace,youtube]),patch.object(E,'cloudflare_upload') as up:
   out=E.path_speed('WARP')
  self.assertFalse(out['ok']);self.assertEqual(out['error'],'PATH_SPEED_VERIFICATION_FAILED');self.assertEqual(out['country'],'US');up.assert_not_called()

 def test_update_download_requires_github_sha256_metadata(self):
  rel={'tag':'v4.2.0-r29','name':'R29','published':'x','updateAvailable':True,'asset':{'name':'FreeNetHub_R29.exe','url':'https://example.invalid/x.exe','bytes':1,'digest':None}}
  with patch.object(E,'update_release',return_value=rel),patch.object(E,'native') as n:
   with self.assertRaisesRegex(RuntimeError,'UPDATE_SHA256_METADATA_MISSING'):E.update_download()
   n.assert_not_called()
 def test_update_download_rejects_hash_mismatch_and_deletes_file(self):
  rel={'tag':'v4.2.0-r29','name':'R29','published':'x','updateAvailable':True,'asset':{'name':'FreeNetHub_R29.exe','url':'https://example.invalid/x.exe','bytes':3,'digest':'sha256:'+'0'*64}}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'jobs').mkdir()
   def fake_native(args,timeout):
    pathlib.Path(args[args.index('-o')+1]).write_bytes(b'abc');return {'exit':0,'out':'','err':''}
   with patch.object(E,'ROOT',root),patch.object(E,'update_release',return_value=rel),patch.object(E,'native',side_effect=fake_native):
    with self.assertRaisesRegex(RuntimeError,'UPDATE_HASH_MISMATCH'):E.update_download()
    self.assertFalse(any((root/'updates').rglob('*.exe')))

 def test_update_download_binds_pre_tun_root_interface(self):
  rel={'tag':'v4.2.0-r29','name':'R29','published':'x','updateAvailable':True,'asset':{'name':'FreeNetHub_R29.exe','url':'https://example.invalid/x.exe','bytes':3,'digest':'sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}}
  ctx={'bound':True,'interface':'192.168.20.5','interfaceAlias':'Ethernet 3','proof':'BOUND_PRE_TUN_SOURCE_AND_TRACE_NOT_POST_TUN'}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'jobs').mkdir()
   def fake_native(args,timeout):
    self.assertIn('--interface',args);self.assertEqual(args[args.index('--interface')+1],'192.168.20.5')
    pathlib.Path(args[args.index('-o')+1]).write_bytes(b'abc');return {'exit':0,'out':'','err':''}
   with patch.object(E,'ROOT',root),patch.object(E,'update_release',return_value=rel),patch.object(E,'root_network_context',return_value=ctx),patch.object(E,'native',side_effect=fake_native):
    out=E.update_download()
  self.assertTrue(out['verified']);self.assertTrue(out['rootPath']['bound'])

 def test_country_shard_refresh_uses_verified_root_context(self):
  node={'id':'n1','name':'n1','protocol':'vless','server':'example.com','port':443,'uuid':'11111111-1111-1111-1111-111111111111','raw':'vless://11111111-1111-1111-1111-111111111111@example.com:443','source':'AURX_COUNTRY_DE','favorite':False,'pinned':False,'rating':0,'tags':[],'note':''}
  ctx={'bound':True,'interface':'192.168.20.5','interfaceAlias':'Ethernet 3','proof':'BOUND_PRE_TUN_SOURCE_AND_TRACE_NOT_POST_TUN'}
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);(root/'data').mkdir();(root/'jobs').mkdir();E.write(root/'data'/'nodes.json',{'schema':1,'selected':'','nodes':[]})
   with patch.object(E,'ROOT',root),patch.object(E,'root_network_context',return_value=ctx),patch.object(E,'root_curl',return_value={'exit':0,'code':'200','body':'x'}) as rc,patch.object(E.NH,'parse_blob',return_value={'nodes':[node],'errors':[]}):
    out=E.node_refresh_country_verified('DE',True)
  self.assertTrue(out['refreshed']);self.assertIs(rc.call_args.kwargs['ctx'],ctx)

 def test_stop_one_only_requested_mode(self):
  with patch.object(E,'stop',return_value=True) as st:
   r=E.dispatch('StopOne','WARP','');self.assertEqual(r['stopped'],['WARP']);st.assert_called_once_with('WARP')
 def test_stop_one_rejects_invalid_mode(self):
  with self.assertRaisesRegex(ValueError,'INVALID_STOP_MODE'):E.dispatch('StopOne','AUTO','')

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Unit);result=unittest.TextTestRunner(verbosity=2).run(suite)
 E.write(R/'evidence'/'unit_tests.json',{'utc':E.now(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'scope':'Unit validation, ownership and bounded native child; no product tunnel start','success':result.wasSuccessful()})
 raise SystemExit(0 if result.wasSuccessful() else 1)
