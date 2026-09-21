from pathlib import Path
import hashlib,json
G=Path(__file__).resolve().parents[1]
R=G.parent
files=[
 'gateway_control.ps1','gateway_request.ps1','Setup-GatewayCore.ps1','Setup-ConsoleGateway.ps1','gateway_defaults.json','runtime_config.ps1','preflight.ps1','generate_config.py',
 'apply_elevated.ps1','stop_elevated.ps1','console_provider.ps1','wsl_console.ps1','build_isolated_mihomo.py',
 'import_wireguard.py','validate_console_profile.ps1','tests/direct_stun.py','socks_udp_probe.py'
]
rows=[]
for rel in files:
 p=G/rel
 if not p.is_file(): raise SystemExit('MISSING '+rel)
 b=p.read_bytes(); rows.append({'file':rel.replace('\\','/'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()})
m={'schema':1,'product':'FreeNet Hub Gateway','version':'4.2.0','scope':'PC_TUNNEL+CONSOLE_GATEWAY','files':rows,'excludes':['runtime/**','tests/*acceptance*','tests/*patch*','tests/*request*','tests/*cleanup*','*.private.*']}
(G/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'sha256':hashlib.sha256((G/'manifest.json').read_bytes()).hexdigest().upper()},indent=2))
