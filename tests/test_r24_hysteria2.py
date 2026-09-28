#!/usr/bin/env python3
import base64, importlib.util, pathlib, json
P=pathlib.Path(__file__).resolve().parent.parent/'app'/'nodehub.py'
spec=importlib.util.spec_from_file_location('nh_r24',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

u='hysteria2://secret@vpn-sg.example:443?insecure=1&security=tls&sni=example.com#Singapore'
n=m.parse_uri(u)
assert n['protocol']=='hysteria2'
assert n['server']=='vpn-sg.example' and n['port']==443
assert n['password']=='secret'
assert n['tls']=={'enabled':True,'server_name':'example.com','insecure':True}
cfg=m.sing_box_config(n)
o=cfg['outbounds'][0]
assert o['type']=='hysteria2' and o['password']=='secret'
assert o['tls']['server_name']=='example.com' and o['tls']['insecure'] is True

u2='hy2://pw@example.net:8443?obfs=salamander&obfs-password=mask&sni=sni.example#SG'
n2=m.parse_uri(u2)
assert n2['protocol']=='hysteria2'
assert n2['obfs']=={'type':'salamander','password':'mask'}
assert m.sing_box_config(n2)['outbounds'][0]['obfs']['type']=='salamander'

blob='\n'.join([u,'vless://id@example.org:443?security=tls&sni=example.org#US'])
enc=base64.b64encode(blob.encode()).decode()
p=m.parse_blob(enc,'test-sub')
assert {x['protocol'] for x in p['nodes']}=={'hysteria2','vless'}
assert 'hysteria2' in m.SUPPORTED_PROTOCOLS
print('R24_HYSTERIA2_FIDELITY=PASS')
