import ipaddress, pathlib, struct, sys, unittest
from unittest.mock import patch

R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'app'))
import directnet as D


class DirectNetUnit(unittest.TestCase):
 def test_parse_stun_ipv4(self):
  tx=b'0123456789ab';ip='203.0.113.7';port=54321
  cookie=struct.pack('!I',D.MAGIC)
  xip=bytes(a^b for a,b in zip(ipaddress.ip_address(ip).packed,cookie))
  xport=port^(D.MAGIC>>16)
  attr=struct.pack('!HH',0x0020,8)+b'\x00\x01'+struct.pack('!H',xport)+xip
  msg=struct.pack('!HHI',0x0101,len(attr),D.MAGIC)+tx+attr
  self.assertEqual(D._parse_stun(msg,tx),{'ip':ip,'port':port})

 def test_classify_cgnat_shared_space(self):
  self.assertEqual(D.classify_nat('100.123.107.63','164.215.159.13'),'CGNAT_CONFIRMED_SHARED_100_64_10')

 def test_classify_public_wan(self):
  self.assertEqual(D.classify_nat('8.8.8.8','8.8.8.8'),'PUBLIC_WAN_OR_1TO1_NAT')

 def test_parse_dns_a_filters_non_global(self):
  tx=b'AB';q=D._dns_name_wire('www.youtube.com')+struct.pack('!HH',1,1)
  a1=b'\xc0\x0c'+struct.pack('!HHIH',1,1,60,4)+ipaddress.ip_address('10.10.34.35').packed
  a2=b'\xc0\x0c'+struct.pack('!HHIH',1,1,60,4)+ipaddress.ip_address('142.251.156.4').packed
  msg=tx+b'\x81\x80'+struct.pack('!HHHH',1,2,0,0)+q+a1+a2
  self.assertEqual(D._parse_dns_a(msg,tx),['142.251.156.4'])

 def test_stable_port_preserving_mapping_is_traversal_candidate(self):
  with patch.object(D,'upnp_external_ip',return_value={'available':True,'externalIp':'100.123.107.63'}), \
       patch.object(D,'stun_mappings',return_value={'mappingStableAcrossTargets':True,'portPreserved':True,'publicMappedIp':'164.215.159.13','publicMappedPort':50000}), \
       patch.object(D,'pcp_natpmp',return_value={'pcp':{'supported':False},'natPmp':{'supported':False}}):
   r=D.audit('192.168.20.5','192.168.20.1')
  self.assertTrue(r['cgnatConfirmed'])
  self.assertTrue(r['udpTraversalCandidate'])

 def test_unstable_mapping_is_not_traversal_candidate(self):
  with patch.object(D,'upnp_external_ip',return_value={'available':True,'externalIp':'100.123.107.63'}), \
       patch.object(D,'stun_mappings',return_value={'mappingStableAcrossTargets':False,'portPreserved':True,'publicMappedIp':'164.215.159.13','publicMappedPort':50000}), \
       patch.object(D,'pcp_natpmp',return_value={'pcp':{'supported':False},'natPmp':{'supported':False}}):
   r=D.audit('192.168.20.5','192.168.20.1')
  self.assertFalse(r['udpTraversalCandidate'])


if __name__=='__main__':
 unittest.main()
