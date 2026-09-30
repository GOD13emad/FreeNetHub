from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
REPO=R.parents[1]
files=['FreeNetHub.exe','FreeNetHub.ico','FreeNetHub.png','FreeNetHubShell.cs','FreeNetHubShell.manifest','Install-FreeNetHubShell.ps1','Verify-FreeNetHubShell.ps1','Rollback-FreeNetHubShell.ps1','README_FA.md','RUNTIME_ACCEPTANCE.json','Test-FreeNetHubShell42.ps1']
def canonical_sha(p):
 p=Path(p).resolve(); rel=p.relative_to(REPO).as_posix()
 oid=subprocess.check_output(['git','hash-object','-w',f'--path={rel}',str(p)],cwd=REPO,text=True).strip()
 data=subprocess.check_output(['git','cat-file','blob',oid],cwd=REPO)
 return hashlib.sha256(data).hexdigest().upper()
rows=[]
for n in files:
 p=R/n
 if not p.is_file(): raise SystemExit('MISSING '+n)
 b=p.read_bytes(); rows.append({'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper(),'sourceSha256':canonical_sha(p)})
m={'product':'FreeNet Hub','version':'4.2.0','state':'R40_LIFECYCLE_SAFE_CANDIDATE','scope':'WINDOWS_STANDALONE_420_R40_LIFECYCLE_SAFE','files':rows}
(R/'MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'manifestSha256':hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest().upper()}))
