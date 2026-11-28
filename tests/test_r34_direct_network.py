import pathlib,sys,unittest
from unittest.mock import patch

R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'app'))
import engine as E


# The fake transport accepts only the exact URLs in this test contract.
TRACE_URL='https://www.cloudflare.com/cdn-cgi/trace'
TARGET_RESULTS={
 'https://api.openai.com/v1/models':(0,'401'),
 'https://www.youtube.com/generate_204':(1,'000'),
 'https://www.google.com/generate_204':(0,'204'),
 'https://github.com/':(63,'200'),
}

def fake_curl(url,*args,**kwargs):
 if url==TRACE_URL:
  return {'exit':0,'code':'200','seconds':.1,'body':'ip=164.215.159.13\nloc=IR\nwarp=off\ngateway=off','fetchPath':'SYSTEM_DNS','error':''}
 exit_code,code=TARGET_RESULTS[url]
 return {'exit':exit_code,'code':code,'seconds':.2,'body':'','fetchPath':'SYSTEM_DNS','error':'MAX_FILESIZE_EXCEEDED' if exit_code==63 else '' if code!='000' else 'reset'}


class DirectAuditUnit(unittest.TestCase):
 def test_dispatch_wires_direct_audit(self):
  with patch.object(E,'direct_network_audit',return_value={'status':'PASS_READ_ONLY'}) as f:
   self.assertEqual(E.dispatch('DirectNetworkAudit','','')['status'],'PASS_READ_ONLY')
   f.assert_called_once_with()

 def test_direct_audit_is_read_only_and_route_stable(self):
  route={'trustedPhysical':True,'ifIndex':18,'nextHop':'192.168.20.1','ip':'192.168.20.5','adapterName':'Ethernet 3','systemOverrideRoutes':[]}
  nat={'cgnatConfirmed':True,'udpTraversalCandidate':True,'portControl':{'pcp':{'supported':False},'natPmp':{'supported':False}},'natClassification':'CGNAT_CONFIRMED_SHARED_100_64_10'}
  adapter={'available':True,'ipv6DefaultRoutes':0,'receivedPacketErrors':0,'outboundPacketErrors':0}
  with patch.object(E,'direct_route',side_effect=[route,route]),patch.object(E.DN,'audit',return_value=nat),patch.object(E.DN,'dns_interception_probe',return_value={'interceptionConfirmed':True}),patch.object(E,'direct_adapter_snapshot',return_value=adapter),patch.object(E,'curl',side_effect=fake_curl) as transport,patch.object(E,'write') as w:
   out=E.direct_network_audit()
  self.assertEqual(out['status'],'PASS_READ_ONLY')
  self.assertTrue(out['routeStable'])
  self.assertTrue(out['nat']['cgnatConfirmed'])
  self.assertEqual(out['mutationsApplied'],[])
  self.assertTrue(out['applicationChecks']['github']['reachable'])
  self.assertFalse(out['applicationChecks']['youtube']['reachable'])
  w.assert_called_once()
  self.assertCountEqual([call.args[0] for call in transport.call_args_list],[*TARGET_RESULTS,TRACE_URL])

 def test_mock_rejects_urls_outside_exact_contract(self):
  for url in ('https://example.invalid/api.openai.com/v1/models',
              'https://www.youtube.com.example.invalid/generate_204',
              'https://example.invalid/?next=google.com',
              'https://example.invalid/?next=github.com',
              'https://example.invalid/cdn-cgi/trace'):
   with self.subTest(url=url),self.assertRaises(KeyError):
    fake_curl(url)

 def test_public_dns_prefers_validated_doh_and_rejects_private(self):
  with patch.object(E.DN,'doh_a',return_value={'ips':['10.10.34.35','142.251.156.4']}),patch.object(E,'native') as native:
   self.assertEqual(E.public_dns_ips('www.youtube.com'),['142.251.156.4'])
   native.assert_not_called()


if __name__=='__main__':
 unittest.main()
