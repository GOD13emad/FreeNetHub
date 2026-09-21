from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
files=['FreeNetHub.exe','FreeNetHub.ico','FreeNetHub.png','FreeNetHubShell.cs','FreeNetHubShell.manifest','Install-FreeNetHubShell.ps1','Verify-FreeNetHubShell.ps1','Rollback-FreeNetHubShell.ps1','README_FA.md','RUNTIME_ACCEPTANCE.json','Test-FreeNetHubShell42.ps1']
rows=[]
for n in files:
 p=R/n
 if not p.is_file(): raise SystemExit('MISSING '+n)
 b=p.read_bytes(); rows.append({'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()})
m={'product':'FreeNet Hub','version':'4.2.0','state':'TARGET_RUNTIME_ACCEPTED','scope':'WINDOWS_STANDALONE_420','files':rows}
(R/'MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'manifestSha256':hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest().upper()}))
