"""FreeNet Hub 4: browser-scoped, bounded, explicit control. No system VPN mutation."""
from __future__ import annotations
import argparse, concurrent.futures, contextlib, ctypes as C, datetime as dt, hashlib, importlib.util, ipaddress, json, os, pathlib, re, shutil, socket, subprocess as sp, sys, time, uuid, zipfile
from ctypes import wintypes as W
ROOT=pathlib.Path(__file__).resolve().parent.parent
APP=ROOT/'app'
_nhspec=importlib.util.spec_from_file_location("freenethub_nodehub",APP/"nodehub.py")
NH=importlib.util.module_from_spec(_nhspec);_nhspec.loader.exec_module(NH)
PORTS={'NODE':19460,'WARP':19410,'GOOL':19413,'CFON':19414,'TOR':19450,'WEBTUNNEL':19452,'OBFS4':19453}
DEFAULT={'theme':'dark','country':'AUTO','home':'https://www.youtube.com/','monitor':False,'autoRepair':False,'showIp':False,'minimizeToTray':True,'order':['NODE','WARP','TOR','GOOL','CFON'],'localProxy':'socks5h://127.0.0.1:9909','includeDirect':False}
ALLOWED_COUNTRIES={'AT','DE','NL','US','CA','GB','FR','SG','JP','AUTO'}
FLAGS=0x08000000|0x00000200
JOB=''; DEADLINE=float('inf'); STARTED=[]

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def read(p,default=None):
 p=pathlib.Path(p)
 if not p.exists():return default
 if p.stat().st_size>4*1024*1024:raise ValueError('STATUS_TOO_LARGE')
 return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,value):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp');t.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
 last=None
 for attempt in range(8):
  try:os.replace(t,p);return
  except OSError as e:
   # Windows readers/AV can transiently deny replacement of an existing JSON file.
   # Retry only sharing/access violations; never mask unrelated filesystem failures.
   if not (isinstance(e,PermissionError) or getattr(e,'winerror',None) in (5,32,33)):raise
   last=e;time.sleep(.025*(attempt+1))
 with contextlib.suppress(FileNotFoundError):t.unlink()
 raise last
def digest(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def settings():
 s=DEFAULT|read(ROOT/'settings.json',{})
 order=[x for x in s.get('order',[]) if x in PORTS]
 if 'NODE' not in order:order=['NODE']+order
 s['order']=order
 return s
def deps():return read(APP/'dependencies.json',{}) or {}
def dep_path(name):
 d=deps();x=d.get(name)
 if isinstance(x,dict):return str(x.get('path') or '')
 return str(x or '')
def validate_settings(s):
 if s.get('theme') not in ('dark','light'):raise ValueError('INVALID_THEME')
 if s.get('country') not in ALLOWED_COUNTRIES:raise ValueError('INVALID_COUNTRY')
 from urllib.parse import urlparse
 u=urlparse(s.get('home',''))
 if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('HOME_MUST_BE_HTTPS')
 local_proxy(s.get('localProxy',''))
 if any(x not in PORTS for x in s.get('order',[])):raise ValueError('INVALID_AUTO_ORDER')
 return {k:s.get(k,v) for k,v in DEFAULT.items()}
def local_proxy(uri):
 from urllib.parse import urlparse
 u=urlparse(uri)
 if u.scheme not in ('socks5h','http') or u.hostname not in ('127.0.0.1','::1') or not u.port or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:raise ValueError('ONLY_LOCAL_UNAUTHENTICATED_PROXY_ALLOWED')
 return uri

def node_store():
 x=read(ROOT/'data'/'nodes.json',{'schema':1,'selected':'','nodes':[]}) or {}
 nodes=x.get('nodes',[]) if isinstance(x.get('nodes',[]),list) else []
 return {'schema':1,'selected':str(x.get('selected') or ''),'nodes':nodes[:NH.MAX_NODES]}

def save_node_store(store):
 write(ROOT/'data'/'nodes.json',{'schema':1,'selected':str(store.get('selected') or ''),'nodes':list(store.get('nodes') or [])[:NH.MAX_NODES]})

def node_selected(store=None):
 s=node_store() if store is None else store;sid=s.get('selected')
 return next((x for x in s['nodes'] if x.get('id')==sid),None)

def node_select(node_id):
 s=node_store()
 if not any(x.get('id')==node_id for x in s['nodes']):raise ValueError('NODE_NOT_FOUND')
 s['selected']=node_id;save_node_store(s);return node_selected(s)

def node_public_rows(store=None):
 s=node_store() if store is None else store
 def key(n):
  ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else {}
  lt=n.get('last_test') if isinstance(n.get('last_test'),dict) else {}
  return (0 if n.get('pinned') else 1,0 if n.get('favorite') else 1,0 if lt.get('healthy') else 1,0 if ep.get('reachable') else 1,float(ep.get('latency_ms',999999) or 999999),str(n.get('name','')).lower())
 return [NH.public_node(x) for x in sorted(s['nodes'],key=key)]

def node_endpoint_probe(n,timeout=1.25):
 started=time.monotonic()
 try:
  with socket.create_connection((str(n.get('server','')),int(n.get('port',0))),timeout=timeout):pass
  return {'reachable':True,'latency_ms':round((time.monotonic()-started)*1000,1),'checked':now(),'type':'TCP_ENDPOINT_ONLY'}
 except (OSError,ValueError):
  return {'reachable':False,'latency_ms':None,'checked':now(),'type':'TCP_ENDPOINT_ONLY'}

def node_batch_fast():
 s=node_store()
 if not s['nodes']:raise ValueError('NODE_POOL_EMPTY')
 progress('تست سریع همهٔ سرورهای Node؛ فقط TCP endpoint و بدون روشن کردن پروکسی','NODE')
 workers=min(32,max(4,len(s['nodes'])))
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
  futures={ex.submit(node_endpoint_probe,n):n.get('id') for n in s['nodes']}
  results={}
  for f in concurrent.futures.as_completed(futures):
   check();results[futures[f]]=f.result()
 for n in s['nodes']:
  if n.get('id') in results:n['endpoint_test']=results[n['id']]
 save_node_store(s)
 reachable=sum(1 for x in results.values() if x.get('reachable'))
 return {'total':len(s['nodes']),'reachable':reachable,'selected':s.get('selected'),'testType':'TCP_ENDPOINT_ONLY_NOT_PROXY_HEALTH','nodes':node_public_rows(s)}

def node_import_text(text,source='import'):
 parsed=NH.parse_blob(text,source);s=node_store();s['nodes']=NH.merge(s['nodes'],parsed['nodes'])
 if not s.get('selected') and s['nodes']:s['selected']=s['nodes'][0]['id']
 save_node_store(s)
 return {'imported':len(parsed['nodes']),'total':len(s['nodes']),'errors':parsed['errors'],'selected':s.get('selected'),'nodes':node_public_rows(s)}

def singbox_path():
 g=read(ROOT/'gateway'/'runtime'/'local_gateway.json',{}) or {};sb=g.get('singbox') if isinstance(g,dict) else None
 if not isinstance(sb,dict) or not sb.get('path') or not sb.get('sha256'):return ''
 p=pathlib.Path(sb['path'])
 if not p.is_file() or digest(p)!=str(sb['sha256']).upper():return ''
 return str(p)

def node_record_test(node_id,h):
 s=node_store()
 for n in s['nodes']:
  if n.get('id')==node_id:n['last_test']={k:h.get(k) for k in ('healthy','country','ip','seconds','error','checked')}
 save_node_store(s)

def ensure_node(target='AUTO',limit=12):
 s=node_store()
 if not s['nodes']:raise ValueError('NODE_POOL_EMPTY')
 target=str(target or 'AUTO').upper()
 def score(n):
  lt=n.get('last_test') if isinstance(n.get('last_test'),dict) else {}
  exact=target!='AUTO' and lt.get('healthy') and str(lt.get('country','')).upper()==target
  hint=target!='AUTO' and target.lower() in str(n.get('name','')).lower()
  ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else {}
  healthy=bool(lt.get('healthy'));lat=lt.get('seconds')
  return (0 if exact else 1,0 if hint else 1,0 if n.get('pinned') else 1,0 if n.get('favorite') else 1,0 if healthy else 1,0 if ep.get('reachable') else 1,float(ep.get('latency_ms',999999) or 999999),float(lat) if isinstance(lat,(int,float)) else 9999)
 nodes=sorted(s['nodes'],key=score)
 last=[]
 for n in nodes[:max(1,min(int(limit),24))]:
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:stop('NODE')
  node_select(n['id'])
  try:
   h=ensure('NODE');node_record_test(n['id'],h)
   if h.get('healthy'):return h
   last.append({'id':n['id'],'error':h.get('error'),'country':h.get('country')})
  except (ValueError,RuntimeError) as e:
   with contextlib.suppress(Exception):stop('NODE')
   node_record_test(n['id'],{'healthy':False,'country':'','ip':'','seconds':None,'error':str(e),'checked':now()})
   last.append({'id':n['id'],'error':str(e)})
 raise RuntimeError('NODE_COUNTRY_NOT_FOUND' if target!='AUTO' else 'NODE_POOL_NO_HEALTHY_NODE')

def country_target():
 return str(settings().get('country','AUTO')).upper()

def connect_candidates(mode):
 c=country_target()
 if c=='AUTO':return list(settings()['order']) if mode=='AUTO' else [mode]
 if mode=='AUTO':return ['NODE','CFON']
 if mode not in ('NODE','CFON','CUSTOM'):raise ValueError('COUNTRY_MODE_UNSUPPORTED')
 return [mode]

def check():
 if JOB and (ROOT/'jobs'/f'{JOB}.cancel').exists():raise InterruptedError('CANCELLED')
 if time.monotonic()>DEADLINE:raise TimeoutError('OPERATION_DEADLINE')
def progress(message,mode=''):
 if JOB:write(ROOT/'jobs'/f'{JOB}.progress.json',{'job':JOB,'utc':now(),'message':message,'mode':mode})
def env():return {k:v for k,v in os.environ.items() if k.lower() not in ('http_proxy','https_proxy','all_proxy','no_proxy')}
def native(argv,timeout=10):
 check()
 with sp.Popen([str(x) for x in argv],stdin=sp.DEVNULL,stdout=sp.PIPE,stderr=sp.PIPE,creationflags=FLAGS,env=env(),cwd=str(ROOT)) as p:
  end=min(DEADLINE,time.monotonic()+timeout)
  try:
   while True:
    check()
    try:
     out,err=p.communicate(timeout=.2)
     return {'exit':p.returncode,'out':out.decode('utf-8','replace'),'err':err.decode('utf-8','replace')}
    except sp.TimeoutExpired:
     if time.monotonic()>=end:raise TimeoutError('CHILD_DEADLINE')
  finally:
   if p.poll() is None:p.kill();p.communicate(timeout=3)

def curl(url,proxy='',seconds=7,body=True,size=262144):
 args=['curl.exe','-q','-4','-sS','--connect-timeout','3','--max-time',str(seconds),'--max-filesize',str(size),'--write-out','\n__FNH__%{http_code} %{time_total} %{size_download} %{speed_download}']
 args+=['--proxy',proxy,'--noproxy',''] if proxy else ['--noproxy','*']
 if not body:args+=['-o','NUL']
 args+=[url];started=time.monotonic()
 try:
  r=native(args,seconds+2);bodytext,sep,meta=r['out'].rpartition('\n__FNH__');parts=meta.split()
  return {'exit':r['exit'],'code':parts[0] if parts else '000','seconds':float(parts[1]) if len(parts)>1 else round(time.monotonic()-started,3),'bytes':int(float(parts[2])) if len(parts)>2 else 0,'bps':float(parts[3]) if len(parts)>3 else 0,'body':bodytext[:size],'error':r['err'][:700]}
 except TimeoutError:return {'exit':124,'code':'000','seconds':round(time.monotonic()-started,3),'body':'','error':'TIMEOUT'}
def direct_route():
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh:raise ValueError('DEPENDENCY_NOT_CONFIGURED_PWSH')
 script="$r=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object @{e={$_.RouteMetric + (Get-NetIPInterface -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4).InterfaceMetric}} | Select-Object -First 1;if(!$r){exit 3};$a=Get-NetAdapter -InterfaceIndex $r.InterfaceIndex -IncludeHidden -ErrorAction SilentlyContinue;$ip=Get-NetIPAddress -InterfaceIndex $r.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.IPAddress -notlike '169.254.*'}|Select-Object -First 1;[pscustomobject]@{ifIndex=$r.InterfaceIndex;nextHop=$r.NextHop;routeMetric=$r.RouteMetric;adapterName=$a.Name;description=$a.InterfaceDescription;hardware=[bool]$a.HardwareInterface;status=[string]$a.Status;ip=$ip.IPAddress}|ConvertTo-Json -Compress"
 r=native([pwsh,'-NoProfile','-Command',script],8)
 if r['exit']!=0:raise RuntimeError('DIRECT_ROUTE_UNAVAILABLE')
 try:x=json.loads(r['out'])
 except (ValueError,TypeError) as ex:raise RuntimeError('DIRECT_ROUTE_UNAVAILABLE') from ex
 label=(str(x.get('adapterName',''))+' '+str(x.get('description',''))).lower()
 suspicious=bool(re.search(r'\b(vpn|warp|wireguard|openvpn|tap|tun|wintun|tailscale|zerotier|mihomo|sing-box)\b',label))
 x['trustedPhysical']=bool(x.get('hardware') and str(x.get('status','')).lower()=='up' and not suspicious and x.get('ip'))
 return x

def ping_direct():
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh:return {'ok':False,'avgMs':None,'note':'PowerShell unavailable'}
 script="$r=Test-Connection -TargetName 1.1.1.1 -Count 3 -IPv4 -ErrorAction SilentlyContinue;if(!$r){exit 2};$v=@($r|ForEach-Object{$_.Latency}|Where-Object{$_ -ne $null});if(!$v){exit 3};[math]::Round((($v|Measure-Object -Average).Average),1)"
 r=native([pwsh,'-NoProfile','-Command',script],7)
 try:v=float(r['out'].strip()) if r['exit']==0 else None
 except ValueError:v=None
 return {'ok':v is not None,'avgMs':v,'target':'1.1.1.1','type':'ICMP'}

def cloudflare_upload(sample_bytes=1000000,seconds=20):
 sample_bytes=max(262144,min(int(sample_bytes),5000000));tmp=ROOT/'jobs'/f'{JOB or uuid.uuid4().hex}.speed-upload.bin'
 tmp.parent.mkdir(parents=True,exist_ok=True)
 try:
  with open(tmp,'wb') as f:f.truncate(sample_bytes)
  args=['curl.exe','-q','-4','-sS','--connect-timeout','3','--max-time',str(seconds),'--noproxy','*','-o','NUL','--data-binary','@'+str(tmp),'--write-out','\n__FNH__%{http_code} %{time_total} %{size_upload} %{speed_upload}','https://speed.cloudflare.com/__up']
  r=native(args,seconds+2);bodytext,sep,meta=r['out'].rpartition('\n__FNH__');parts=meta.split()
  return {'exit':r['exit'],'code':parts[0] if parts else '000','seconds':float(parts[1]) if len(parts)>1 else None,'bytes':int(float(parts[2])) if len(parts)>2 else 0,'bps':float(parts[3]) if len(parts)>3 else 0,'error':r['err'][:700]}
 finally:
  tmp.unlink(missing_ok=True)

def direct_speed():
 progress('Direct ISP speed test: no FreeNetHub browser proxy','DIRECT')
 route=direct_route()
 if not route.get('trustedPhysical'):raise RuntimeError('DIRECT_SPEED_NON_PHYSICAL_DEFAULT_ROUTE')
 a=curl('https://www.cloudflare.com/cdn-cgi/trace','',seconds=8);tr=trace(a.get('body',''))
 if a.get('exit')!=0 or a.get('code')!='200' or not tr:raise RuntimeError('DIRECT_SPEED_TRACE_FAILED')
 if str(tr.get('warp','')).lower()=='on' or str(tr.get('gateway','')).lower()=='on':raise RuntimeError('DIRECT_SPEED_SYSTEM_TUNNEL_DETECTED')
 ping=ping_direct()
 down=curl('https://speed.cloudflare.com/__down?bytes=5000000','',seconds=20,body=False,size=5100000)
 up=cloudflare_upload(1000000,20)
 down_ok=down.get('exit')==0 and down.get('code')=='200' and down.get('bytes')==5000000
 up_ok=up.get('exit')==0 and up.get('code')=='200' and up.get('bytes')==1000000
 return {'mode':'DIRECT','path':'DIRECT_HOST_INTERNET','ok':bool(down_ok and up_ok),'proxyUsed':False,'freeNetHubBrowserProxyUsed':False,'defaultRoute':route,'exitIp':tr.get('ip',''),'country':tr.get('loc',''),'cloudflareWarp':tr.get('warp',''),'cloudflareGateway':tr.get('gateway',''),'httpsLatencyMs':round(float(a.get('seconds',0))*1000,1),'pingMs':ping.get('avgMs'),'downloadMbps':round(float(down.get('bps',0))*8/1e6,2),'uploadMbps':round(float(up.get('bps',0))*8/1e6,2),'downloadSampleBytes':down.get('bytes',0),'uploadSampleBytes':up.get('bytes',0),'downloadSeconds':down.get('seconds'),'uploadSeconds':up.get('seconds'),'pathProof':'NO_PROXY_ENV+--noproxy_*+PHYSICAL_DEFAULT_ROUTE+CF_WARP_OFF','note':'Direct host Internet sample; FreeNetHub browser proxy is bypassed. Fails closed if the default route is not a physical adapter or Cloudflare reports WARP/Gateway on.'}

def trace(text):
 out={}
 for line in text.splitlines():
  if '=' in line:
   k,v=line.split('=',1);out[k]=v.strip()
 try:ipaddress.ip_address(out.get('ip',''))
 except ValueError:return {}
 return out

def probe(mode,proxy=None,required_country=None):
 if proxy is None:proxy='' if mode=='DIRECT' else settings()['localProxy'] if mode=='CUSTOM' else f'socks5h://127.0.0.1:{PORTS[mode]}'
 progress('در حال بررسی IP و HTTPS مسیر انتخاب‌شده',mode)
 a=curl('https://www.cloudflare.com/cdn-cgi/trace',proxy);t=trace(a['body'])
 b=curl('https://www.youtube.com/generate_204',proxy,body=False)
 good=bool(a['exit']==0 and a['code']=='200' and t and b['exit']==0 and b['code']=='204')
 c=required_country or (country_target() if mode in ('NODE','CFON','CUSTOM') else '')
 country_bad=bool(c and c!='AUTO' and t.get('loc')!=c)
 if country_bad:good=False
 error=''
 if country_bad:error='COUNTRY_MISMATCH_OR_UNKNOWN'
 elif proxy and (a['exit']==7 or b['exit']==7):error='LOCAL_PROXY_UNREACHABLE'
 elif not good:error='HTTPS_VERIFICATION_FAILED'
 return {'healthy':good,'mode':mode,'scope':'BROWSER_HTTPS','ip':t.get('ip',''),'country':t.get('loc',''),'warp':t.get('warp',''),'seconds':b['seconds'] if good else None,'checked':now(),'checks':[{'name':'Cloudflare HTTPS trace','code':a['code'],'exit':a['exit']},{'name':'YouTube HTTPS','code':b['code'],'exit':b['exit']}],'countryPolicy':c,'error':error,'applicationAcceptance':'NOT_TESTED'}

# Windows process identity: exact executable, creation time and process ID, not name/port alone.
def identity(pid):
 k=C.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
 k.CloseHandle.argtypes=[W.HANDLE];k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
 k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)]
 k.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
 h=k.OpenProcess(0x1000|0x100000,False,int(pid))
 if not h:return None
 try:
  if k.WaitForSingleObject(h,0)!=258:return None
  buf=C.create_unicode_buffer(32768);n=W.DWORD(len(buf))
  if not k.QueryFullProcessImageNameW(h,0,buf,C.byref(n)):return None
  a,b,c,d=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
  if not k.GetProcessTimes(h,C.byref(a),C.byref(b),C.byref(c),C.byref(d)):return None
  return {'pid':int(pid),'path':os.path.normcase(os.path.abspath(buf.value)),'created':(a.dwHighDateTime<<32)|a.dwLowDateTime}
 finally:k.CloseHandle(h)
def owned(mode):
 r=read(ROOT/'data'/mode/'owner.json',{})
 cur=identity(r.get('pid',0)) if r else None
 return r if cur and cur=={k:r[k] for k in ('pid','path','created')} else None

def listener_pid(port):
 try:
  r=sp.run(['netstat.exe','-ano','-p','tcp'],stdin=sp.DEVNULL,stdout=sp.PIPE,stderr=sp.DEVNULL,text=True,timeout=4,creationflags=FLAGS)
 except (OSError,sp.SubprocessError):return None
 for line in r.stdout.splitlines():
  a=line.split()
  if len(a)>=5 and a[0].upper()=='TCP' and a[-2].upper()=='LISTENING':
   local=a[1]
   if local.rsplit(':',1)[-1]==str(int(port)):
    try:return int(a[-1])
    except ValueError:return None
 return None

def process_commandline(pid):
 try:
  d=deps();pwsh=d.get('pwsh','')
  if not pwsh:return ''
  cmd=f'(Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}").CommandLine'
  r=sp.run([pwsh,'-NoProfile','-NonInteractive','-Command',cmd],stdin=sp.DEVNULL,stdout=sp.PIPE,stderr=sp.DEVNULL,text=True,timeout=5,creationflags=FLAGS,env=env(),cwd=str(ROOT))
  return r.stdout.strip()
 except (OSError,sp.SubprocessError,ValueError):return ''

def recover_owned(mode,not_before=0):
 # Recovery is deliberately narrow: dedicated project port + pinned executable +
 # canonical project command line. Foreign listeners are never adopted or killed.
 if mode not in PORTS:return None
 pid=listener_pid(PORTS[mode])
 if not pid:return None
 cur=identity(pid)
 if not cur:return None
 if not_before and cur['created']<int(not_before):return None
 d=deps()
 if mode in ('WARP','GOOL','CFON'):
  expected=dep_path('warp');needle=f'--bind 127.0.0.1:{PORTS[mode]}';scope=str((ROOT/'data'/mode/'cache').resolve())
 elif mode=='NODE':
  expected=singbox_path();needle=str((ROOT/'data'/mode/'config.json').resolve());scope=needle
 else:
  expected=dep_path('tor');needle=str((ROOT/'data'/mode/'torrc').resolve());scope=needle
 try:
  if pathlib.Path(cur['path']).resolve()!=pathlib.Path(expected).resolve():return None
 except (OSError,RuntimeError):return None
 cmd=process_commandline(pid)
 if not cmd or needle.lower() not in cmd.lower() or scope.lower() not in cmd.lower():return None
 extra={}
 if mode=='NODE':
  marker=ROOT/'data'/mode/'node-id.txt'
  if marker.is_file():extra['nodeId']=marker.read_text(encoding='utf-8',errors='replace').strip()[:64]
 r=cur|{'mode':mode,'scan':False,'started':now(),'recovered':True}|extra
 write(ROOT/'data'/mode/'owner.json',r)
 return r

def kill_identity(r):
 cur=identity(r['pid'])
 if not cur or cur!={k:r[k] for k in ('pid','path','created')}:return False
 k=C.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE;k.TerminateProcess.argtypes=[W.HANDLE,W.UINT];k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];k.CloseHandle.argtypes=[W.HANDLE]
 h=k.OpenProcess(0x1|0x100000,False,r['pid'])
 if not h:raise OSError('OWNED_PROCESS_ACCESS_DENIED')
 try:
  if not k.TerminateProcess(h,0):raise OSError('OWNED_PROCESS_STOP_FAILED')
  k.WaitForSingleObject(h,3000)
 finally:k.CloseHandle(h)
 return True

def children(pid):
 # Read-only process metadata; no process is acted on without a fresh identity match.
 pwsh=dep_path('pwsh')
 if not pwsh:return []
 r=native([pwsh,'-NoProfile','-NonInteractive','-Command',f'Get-CimInstance Win32_Process -Filter "ParentProcessId={int(pid)}" | Select-Object ProcessId,ExecutablePath | ConvertTo-Json -Compress'],8)
 if not r['out'].strip():return []
 x=json.loads(r['out']);return x if isinstance(x,list) else [x]

def cleanup_node_runtime():
 data=ROOT/'data'/'NODE'
 for name in ('config.json','node-id.txt'):
  with contextlib.suppress(OSError):(data/name).unlink(missing_ok=True)

def stop(mode):
 owner_path=ROOT/'data'/mode/'owner.json'
 r=owned(mode)
 opened=port_open(PORTS.get(mode,0))
 if not r and opened:r=recover_owned(mode)
 if not r:
  # A stale owner record is not authority. Remove it only when there is no
  # listener to attribute, and never act on a foreign listener/process.
  if not opened:
   owner_path.unlink(missing_ok=True)
   if mode=='NODE':cleanup_node_runtime()
  return False
 pts=[]
 if mode in ('TOR','WEBTUNNEL','OBFS4'):
  for child in children(r['pid']):
   ly=dep_path('lyrebird')
   if ly and str(child.get('ExecutablePath','')).lower()==ly.lower():
    i=identity(child['ProcessId'])
    if i and i['created']>=r['created']:pts.append(i)
 kill_identity(r)
 for i in pts:kill_identity(i)
 end=time.monotonic()+4
 while port_open(PORTS[mode]) and time.monotonic()<end:
  # A project process can hand off/replace its PID during shutdown. Recover only
  # an exact pinned-binary/canonical-command listener; never touch foreign ports.
  newer=recover_owned(mode)
  if newer and newer['pid']!=r['pid']:kill_identity(newer)
  time.sleep(.08)
 if port_open(PORTS[mode]):raise RuntimeError('OWNED_PROCESS_STOP_INCOMPLETE')
 owner_path.unlink(missing_ok=True)
 if mode=='NODE':cleanup_node_runtime()
 return True

def check_binary(name):
 x=deps().get(name)
 if not isinstance(x,dict) or not x.get('path') or not x.get('sha256'):raise ValueError('DEPENDENCY_NOT_CONFIGURED_'+name.upper())
 p=pathlib.Path(x['path'])
 if not p.is_file() or digest(p)!=str(x['sha256']).upper():raise ValueError('ENGINE_INTEGRITY_FAILED_'+name)
 return p

def port_open(port):
 try:
  with socket.create_connection(('127.0.0.1',int(port)),timeout=.25):return True
 except OSError:return False

def disconnected_health(mode,state='NOT_CONNECTED',error='NOT_CONNECTED'):
 return {'healthy':False,'connected':False,'state':state,'mode':mode,'scope':'BROWSER_HTTPS','ip':'','country':'','warp':'','seconds':None,'checked':now(),'checks':[],'countryPolicy':'','error':error,'applicationAcceptance':'NOT_TESTED'}

def verify(mode):
 if mode in PORTS:
  r=owned(mode);opened=port_open(PORTS[mode])
  if not r and opened:r=recover_owned(mode)
  if not r:
   return disconnected_health(mode,'FOREIGN_OR_STALE_LISTENER' if opened else 'NOT_CONNECTED','PORT_OWNED_BY_ANOTHER_PROCESS' if opened else 'NOT_CONNECTED')
  if not opened:return disconnected_health(mode,'STARTING_OR_UNREADY','PATH_NOT_READY')
  h=probe(mode);h['connected']=True;h['state']='CONNECTED_HEALTHY' if h['healthy'] else 'CONNECTED_UNHEALTHY'
  if h.get('error')=='LOCAL_PROXY_UNREACHABLE':
   h['connected']=False;h['state']='NOT_CONNECTED'
  return h
 h=probe(mode);h['state']='HEALTHY' if h['healthy'] else 'UNHEALTHY';return h

def bridge_lines(text,transport):
 if transport not in ('webtunnel','obfs4'):raise ValueError('BRIDGE_TYPE_UNSUPPORTED')
 lines=[]
 for raw in text.splitlines():
  x=raw.strip()
  if not x or x.startswith('#'):continue
  if x.startswith('Bridge '):x=x[7:].strip()
  if len(x)>2500 or any(ord(c)<32 for c in x):raise ValueError('INVALID_BRIDGE_CONTROL')
  a=x.split()
  if len(a)<4 or a[0]!=transport or not re.fullmatch('[0-9a-fA-F]{40}',a[2]):raise ValueError('INVALID_BRIDGE_HEADER')
  host,port=a[1].rsplit(':',1);ipaddress.ip_address(host.strip('[]'))
  if not 1<=int(port)<=65535:raise ValueError('INVALID_BRIDGE_PORT')
  options=dict(v.split('=',1) for v in a[3:] if '=' in v)
  if transport=='webtunnel':
   from urllib.parse import urlparse
   u=urlparse(options.get('url',''))
   if u.scheme!='https' or not u.hostname or u.username:raise ValueError('WEBTUNNEL_HTTPS_REQUIRED')
  elif not options.get('cert') or options.get('iat-mode') not in ('0','1','2'):raise ValueError('OBFS4_CERT_REQUIRED')
  if x not in lines:lines.append(x)
 if len(lines)>16:raise ValueError('TOO_MANY_BRIDGES')
 return lines

def service_config(mode,scan=False):
 d=deps();data=ROOT/'data'/mode;data.mkdir(parents=True,exist_ok=True)
 if mode=='NODE':
  exe=singbox_path()
  if not exe:raise ValueError('DEPENDENCY_NOT_CONFIGURED_SINGBOX')
  n=node_selected()
  if not n:raise ValueError('NODE_NOT_SELECTED')
  cfg=data/'config.json';write(cfg,NH.sing_box_config(n,PORTS['NODE']))
  (data/'node-id.txt').write_text(n['id'],encoding='utf-8')
  args=[exe,'run','-c',str(cfg)]
 elif mode in ('WARP','GOOL','CFON'):
  exe=check_binary('warp');cache=data/'cache';cache.mkdir(exist_ok=True)
  seed={'WARP':'162.159.192.165:987','GOOL':'188.114.98.35:1010','CFON':'188.114.98.15:8854'}
  ep=read(data/'endpoint.json',{}).get('endpoint',seed[mode])
  args=[str(exe),'-4','--bind',f'127.0.0.1:{PORTS[mode]}','--cache-dir',str(cache),'--dns','1.1.1.1','--test-url','https://www.cloudflare.com/']
  if mode=='GOOL':args+=['--gool']
  if mode=='CFON':
   args+=['--cfon']
   if settings()['country']!='AUTO':args+=['--country',settings()['country']]
  args+=['--scan','--rtt','2s'] if scan else ['--endpoint',ep]
 else:
  exe=check_binary('tor');check_binary('lyrebird')
  torrc=str(d.get('torrc') or '');runtime_root=str(d.get('runtimeRoot') or '')
  if not torrc or not pathlib.Path(torrc).is_file():raise ValueError('DEPENDENCY_NOT_CONFIGURED_TORRC')
  if not runtime_root or not pathlib.Path(runtime_root).is_dir():raise ValueError('DEPENDENCY_NOT_CONFIGURED_RUNTIME_ROOT')
  old=pathlib.Path(torrc).read_text(encoding='utf-8-sig').splitlines()
  lines=[l for l in old if not re.match(r'^(SocksPort|DataDirectory|Bridge|Log|ControlPort)\s',l)]
  if mode=='TOR':br=[l for l in old if l.startswith('Bridge snowflake ')]
  else:
   f=ROOT/'data'/('bridges_'+mode.lower()+'.txt');tr=mode.lower()
   br=['Bridge '+x for x in bridge_lines(f.read_text(encoding='utf-8-sig') if f.exists() else '',tr)]
  if not br:raise ValueError('MISSING_PRIVATE_BRIDGES')
  tor_data=data/'tor';tor_data.mkdir(exist_ok=True)
  # Optional bundled public directory caches may be reused; no identity/guard/browser state is copied.
  old_data=pathlib.Path(runtime_root)/'TorSnowflake'/'data'
  for n in ('cached-certs','cached-microdesc-consensus','cached-microdescs','cached-microdescs.new'):
   src=old_data/n;dst=tor_data/n
   if src.is_file() and not dst.exists():shutil.copyfile(src,dst)
  lines +=[f'SocksPort 127.0.0.1:{PORTS[mode]}','DataDirectory "'+tor_data.as_posix()+'"','Log notice stdout']+br
  cfg=data/'torrc';cfg.write_text('\n'.join(lines)+'\n',encoding='utf-8');args=[str(exe),'-f',str(cfg)]
 return args,data

def start(mode,scan=False):
 existing=owned(mode)
 if existing:return existing
 if port_open(PORTS[mode]):
  recovered=recover_owned(mode)
  if recovered:return recovered
  raise RuntimeError('PORT_OWNED_BY_ANOTHER_PROCESS')
 args,data=service_config(mode,scan)
 with open(data/'stdout.log','ab',buffering=0) as out,open(data/'stderr.log','ab',buffering=0) as err:
  p=sp.Popen(args,stdin=sp.DEVNULL,stdout=out,stderr=err,creationflags=FLAGS,cwd=str(data),env=env(),close_fds=True)
  r=identity(p.pid)
  if not r:raise RuntimeError('ENGINE_EXITED_DURING_START')
  extra={'nodeId':node_selected().get('id')} if mode=='NODE' and node_selected() else {}
  write(data/'owner.json',r|{'mode':mode,'scan':scan,'started':now()}|extra);STARTED.append(mode);return r

def ensure(mode):
 if mode in ('WEBTUNNEL','OBFS4') and not (ROOT/'data'/('bridges_'+mode.lower()+'.txt')).exists():raise ValueError('MISSING_PRIVATE_BRIDGES')
 if owned(mode):
  h=probe(mode)
  if h['healthy']:
   h['connected']=True;h['state']='CONNECTED_HEALTHY';return h
  stop(mode)
 for scan in ((False,True) if mode in ('WARP','GOOL','CFON') else (False,)):
  check();progress('در حال راه‌اندازی و تأیید مسیر',mode);starter=start(mode,scan)
  end=min(DEADLINE,time.monotonic()+(100 if scan else 30 if mode=='NODE' else 65 if mode in ('WARP','GOOL') else 110));grace=time.monotonic()+5
  while time.monotonic()<end:
   check()
   r=owned(mode)
   if not r and port_open(PORTS[mode]):r=recover_owned(mode,starter.get('created',0) if starter else 0)
   if not r:
    if starter and time.monotonic()<grace:
     time.sleep(.1);continue
    break
   if port_open(PORTS[mode]):
    h=probe(mode)
    if h['healthy']:
     h['connected']=True;h['state']='CONNECTED_HEALTHY'
     if mode in ('WARP','GOOL','CFON'):
      log=(ROOT/'data'/mode/'stdout.log').read_text(encoding='utf-8',errors='replace')[-50000:]
      matches=re.findall(r'using warp endpoints.*?\[([\d.]+:\d+)',log)
      if matches:write(ROOT/'data'/mode/'endpoint.json',{'endpoint':matches[-1],'tested':now()})
     write(ROOT/'data'/mode/'health.json',h);return h
    if h['error']=='COUNTRY_MISMATCH_OR_UNKNOWN' and h['ip']:break
   time.sleep(.65)
  stop(mode)
 raise RuntimeError('PATH_NOT_VERIFIED_'+mode)

def mode_proxy(mode):
 return local_proxy(settings()['localProxy']) if mode=='CUSTOM' else '' if mode=='DIRECT' else f'socks5h://127.0.0.1:{PORTS[mode]}'

def chatgpt_probe(mode):
 proxy=mode_proxy(mode)
 endpoints=('https://chatgpt.com/','https://auth.openai.com/','https://challenges.cloudflare.com/')
 checks=[]
 for url in endpoints:
  r=curl(url,proxy,seconds=9,body=False)
  code=int(r.get('code') or 0) if str(r.get('code','')).isdigit() else 0
  reachable=bool(r.get('exit')==0 and 200<=code<500)
  checks.append({'url':url,'code':r.get('code','000'),'exit':r.get('exit',1),'reachable':reachable})
 good=checks[0]['reachable'] and any(x['reachable'] for x in checks[1:])
 return {'healthy':good,'connected':True,'state':'CHATGPT_EDGE_REACHABLE' if good else 'CHATGPT_EDGE_UNREACHABLE','mode':mode,'scope':'CHATGPT_WEB_EDGE','ip':'','country':'','warp':'','seconds':None,'checked':now(),'checks':checks,'countryPolicy':'','error':'' if good else 'CHATGPT_UNREACHABLE','applicationAcceptance':'EDGE_REACHABILITY_ONLY_NOT_LOGIN'}

def emergency_candidates():
 out=[]
 for m in ('WEBTUNNEL','OBFS4'):
  f=ROOT/'data'/('bridges_'+m.lower()+'.txt')
  if f.exists() and f.stat().st_size>0:out.append(m)
 for m in ('TOR',)+tuple(settings()['order']):
  if m in PORTS and m not in out:out.append(m)
 return out

def browser_profile():
 marker=ROOT/'data'/'browser_profile.json'
 data=ROOT/'data';primary=data/'Browser_Primary';legacy=data/'Browser_WARP'
 rec={}
 with contextlib.suppress(Exception):rec=read(marker,{}) or {}
 name=str(rec.get('profile') or '')
 def migrate_legacy():
  if not legacy.exists():return None
  if primary.exists():
   try:has_primary=any(primary.iterdir())
   except OSError:raise ValueError('BROWSER_PROFILE_MIGRATION_CONFLICT')
   if has_primary:raise ValueError('BROWSER_PROFILE_MIGRATION_CONFLICT')
   primary.rmdir()
  legacy.replace(primary)
  write(marker,{'schema':2,'profile':'Browser_Primary','legacyPreserved':False,'migratedFrom':'Browser_WARP','migrated':now()})
  return primary
 if re.fullmatch(r'Browser_[A-Za-z0-9_-]{1,64}',name):
  p=data/name
  if p.exists():
   if p==legacy:return migrate_legacy()
   return p
 migrated=migrate_legacy()
 if migrated:return migrated
 primary.mkdir(parents=True,exist_ok=True)
 write(marker,{'schema':2,'profile':'Browser_Primary','legacyPreserved':False,'created':now()})
 return primary

def chrome_proxy(proxy):
 if proxy.lower().startswith('socks5h://'):return 'socks5://'+proxy[len('socks5h://'):]
 return proxy

def project_browser_roots(browser_exe,profile):
 pwsh=dep_path('pwsh')
 if not pwsh:return []
 e=str(pathlib.Path(browser_exe)).replace("'","''");p=str(pathlib.Path(profile)).replace("'","''")
 cmd=f"$e='{e}';$p='{p}';@((Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)|Where-Object {{$_.ExecutablePath -eq $e -and $_.CommandLine -like ('*'+$p+'*') -and $_.CommandLine -notmatch '--type='}}|Select-Object ProcessId,CommandLine)|ConvertTo-Json -Compress"
 r=native([pwsh,'-NoProfile','-NonInteractive','-Command',cmd],7)
 if r['exit']!=0 or not r['out'].strip():return []
 try:j=json.loads(r['out'])
 except ValueError:return []
 if isinstance(j,dict):j=[j]
 return [int(x['ProcessId']) for x in j if isinstance(x,dict) and str(x.get('ProcessId','')).isdigit()]

def stop_project_browser(browser_exe,profile):
 pids=project_browser_roots(browser_exe,profile)
 if not pids:return {'stopped':[],'forced':[]}
 pwsh=dep_path('pwsh')
 if pwsh:
  for pid in pids:
   with contextlib.suppress(Exception):native([pwsh,'-NoProfile','-NonInteractive','-Command',f'$p=Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue;if($p){{$null=$p.CloseMainWindow()}}'],5)
 end=time.monotonic()+5
 while time.monotonic()<end:
  alive=[pid for pid in pids if identity(pid)]
  if not alive:return {'stopped':pids,'forced':[]}
  time.sleep(.15)
 alive=[pid for pid in pids if identity(pid)]
 for pid in alive:
  with contextlib.suppress(Exception):native(['taskkill.exe','/PID',str(pid),'/T'],8)
 end=time.monotonic()+3
 while time.monotonic()<end:
  alive=[pid for pid in alive if identity(pid)]
  if not alive:return {'stopped':pids,'forced':[]}
  time.sleep(.15)
 alive=[pid for pid in alive if identity(pid)]
 forced=[]
 for pid in alive:
  with contextlib.suppress(Exception):
   native(['taskkill.exe','/F','/PID',str(pid),'/T'],8);forced.append(pid)
 end=time.monotonic()+3
 while time.monotonic()<end:
  still=[pid for pid in alive if identity(pid)]
  if not still:return {'stopped':pids,'forced':forced}
  time.sleep(.15)
 still=[pid for pid in alive if identity(pid)]
 if still:raise ValueError('BROWSER_BUSY_CLOSE_REQUIRED')
 return {'stopped':pids,'forced':forced}

def browser(mode,home_override=''):
 s=settings();proxy=mode_proxy(mode)
 h=verify(mode)
 if not h['healthy']:
  if h.get('connected') is False:raise ValueError('CONNECT_FIRST')
  raise ValueError('BROWSER_BLOCKED_PATH_UNHEALTHY')
 profile=browser_profile()
 browser_exe=dep_path('chrome')
 if not browser_exe or not pathlib.Path(browser_exe).is_file():raise ValueError('DEPENDENCY_NOT_CONFIGURED_BROWSER')
 stopped=stop_project_browser(browser_exe,profile)
 bp=chrome_proxy(proxy)
 args=[browser_exe,f'--user-data-dir={profile}','--no-first-run','--no-default-browser-check','--disable-quic','--force-webrtc-ip-handling-policy=disable_non_proxied_udp']
 if bp:
  args+=[f'--proxy-server={bp}','--proxy-bypass-list=<-loopback>']
  if bp.lower().startswith('socks5://'):args+=['--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1']
 args+=[home_override or s['home']]
 sp.Popen(args,stdin=sp.DEVNULL,stdout=sp.DEVNULL,stderr=sp.DEVNULL,creationflags=FLAGS,cwd=str(ROOT),env=env(),close_fds=True)
 write(ROOT/'data'/'browser_route.json',{'schema':1,'mode':mode,'proxy':bp,'profile':profile.name,'launched':now()})
 return {'launched':True,'mode':mode,'health':h,'home':home_override or s['home'],'profile':profile.name,'proxy':bp,'restarted':bool(stopped.get('stopped'))}

def inventory():
 r=[]
 for mode in PORTS:
  name='warp' if mode in ('WARP','GOOL','CFON') else 'tor'
  f=ROOT/'data'/('bridges_'+mode.lower()+'.txt');o=owned(mode);opened=port_open(PORTS[mode])
  installed=bool(singbox_path()) if mode=='NODE' else bool(dep_path(name) and pathlib.Path(dep_path(name)).is_file())
  state='CONNECTED_NOT_VERIFIED' if o and opened else 'STARTING_OR_UNREADY' if o else 'LISTENER_PRESENT_NOT_OWNED' if opened else 'AVAILABLE_NOT_CONNECTED' if installed else 'DEPENDENCY_NOT_CONFIGURED'
  if mode in ('WEBTUNNEL','OBFS4') and not f.exists() and not o and installed:state='MISSING_PRIVATE_BRIDGES'
  r.append({'mode':mode,'state':state,'port':PORTS[mode],'installed':installed})
 return {'providers':r,'settings':settings(),'fullSystem':'NOT_VALIDATED_DISABLED','systemMutation':False,'utc':now()}

def diagnostics():
 progress('خط پایهٔ مستقیم؛ VPN جدید روشن نمی‌شود')
 rows={u:curl(u,seconds=5,body=False) for u in ('https://www.google.com/','https://www.youtube.com/generate_204','https://www.instagram.com/','https://web.telegram.org/')}
 dns={}
 for host in ('www.youtube.com','www.instagram.com','web.telegram.org'):
  pwsh=dep_path('pwsh')
  if not pwsh:raise ValueError('DEPENDENCY_NOT_CONFIGURED_PWSH')
  r=native([pwsh,'-NoProfile','-Command',f'Resolve-DnsName {host} -Type A -QuickTimeout -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress'],7)
  ips=list(dict.fromkeys(r['out'].split()));dns[host]={'addresses':ips,'nonPublic':any(not ipaddress.ip_address(a).is_global for a in ips if re.fullmatch(r'[\d.]+',a))}
 return {'direct':rows,'dns':dns,'note':'Direct probes bypass inherited proxies. DNS anomaly is an indication, not definitive attribution.','utc':now()}

def safe_export():
 last=read(ROOT/'last.json',{});inv=inventory()
 def redact(x):
  if isinstance(x,dict):return {k:('[redacted]' if k.lower() in ('ip','endpoint','private_key','token','password','home','localproxy') else redact(v)) for k,v in x.items()}
  if isinstance(x,list):return [redact(v) for v in x]
  return x.replace(str(pathlib.Path.home()),'[USER]') if isinstance(x,str) else x
 path=ROOT/'evidence'/('support_'+dt.datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('diagnostic.json',json.dumps(redact({'version':'4.0','inventory':inv,'last':last,'scope':'No private caches, browser profiles or raw logs included'}),ensure_ascii=False,indent=2))
 return {'path':str(path),'sha256':digest(path)}

def dispatch(action,mode,payload):
 if action=='Inventory':return inventory()
 if action=='Settings':
  new=validate_settings(read(payload));write(ROOT/'settings.json',new);return {'saved':True,'settings':new}
 if action=='Connect':
  candidates=connect_candidates(mode);failed=[]
  for m in candidates:
   try:
    h=probe(m,required_country=country_target() if (m=='CUSTOM' and country_target()!='AUTO') else None) if m in ('CUSTOM','DIRECT') else ensure_node(country_target()) if m=='NODE' else ensure(m)
    if h['healthy']:
     if m not in PORTS:h['state']='HEALTHY'
     write(ROOT/'session.json',h);return h
    failed.append({'mode':m,'reason':h['error'] or 'HTTPS_FAILED'})
   except (ValueError,RuntimeError) as e:failed.append({'mode':m,'reason':str(e)})
  h={'healthy':False,'connected':False,'state':'CONNECT_FAILED','mode':mode,'scope':'BROWSER_HTTPS','ip':'','country':'','warp':'','seconds':None,'checked':now(),'checks':[],'countryPolicy':country_target() if mode=='AUTO' else '','error':'ALL_PATHS_FAILED','attempts':failed,'applicationAcceptance':'NOT_TESTED'}
  write(ROOT/'session.json',h);return h
 if action=='Verify':
  h=verify(mode);write(ROOT/'session.json',h);return h
 if action=='Browser':return browser(mode)
 if action=='ChatGPT':
  failed=[]
  for m in emergency_candidates():
   was=bool(owned(m));a=None
   try:
    h=ensure(m)
    if not h.get('healthy'):
     failed.append({'mode':m,'reason':h.get('error') or 'PATH_UNHEALTHY'});continue
    a=chatgpt_probe(m)
    if a['healthy']:
     b=browser(m,'https://chatgpt.com/')
     a['launched']=bool(b.get('launched'));write(ROOT/'session.json',a);return a
    failed.append({'mode':m,'reason':a['error']})
   except (ValueError,RuntimeError) as e:failed.append({'mode':m,'reason':str(e)})
   finally:
    if not was and (not isinstance(a,dict) or not a.get('healthy')):
     with contextlib.suppress(Exception):stop(m)
  h={'healthy':False,'connected':False,'state':'CONNECT_FAILED','mode':'CHATGPT','scope':'CHATGPT_WEB_EDGE','ip':'','country':'','warp':'','seconds':None,'checked':now(),'checks':[],'countryPolicy':'','error':'ALL_CHATGPT_PATHS_FAILED','attempts':failed,'applicationAcceptance':'NOT_TESTED'}
  write(ROOT/'session.json',h);return h
 if action=='Stop':
  stopped=[m for m in PORTS if stop(m)];write(ROOT/'session.json',{'healthy':False,'stopped':True,'checked':now()});return {'stopped':stopped}
 if action=='StopOne':
  if mode not in PORTS:raise ValueError('INVALID_STOP_MODE')
  did=stop(mode);return {'stopped':[mode] if did else [],'mode':mode}
 if action=='Scan':
  old=[m for m in PORTS if owned(m)];rows=[]
  try:
   for m in ('NODE','WARP','GOOL','CFON','TOR'):
    try:rows.append(ensure(m))
    except (RuntimeError,ValueError) as e:rows.append({'mode':m,'healthy':False,'error':str(e)})
    finally:
     if m not in old:stop(m)
  finally:
   for m in PORTS:
    if m not in old:stop(m)
  rank=[x['mode'] for x in sorted([x for x in rows if x.get('healthy')],key=lambda x:x['seconds'])]
  if rank:
   s=settings();s['order']=rank+[x for x in DEFAULT['order'] if x not in rank];write(ROOT/'settings.json',s)
  return {'results':rows,'rank':rank,'note':'Sample HTTPS latency, not guaranteed application speed.'}
 if action=='Speed':
  return direct_speed()
 if action=='Doctor':return diagnostics()
 if action=='Import':
  if mode not in ('WEBTUNNEL','OBFS4'):raise ValueError('INVALID_IMPORT_MODE')
  f=pathlib.Path(payload)
  if f.stat().st_size>65536:raise ValueError('BRIDGE_FILE_TOO_LARGE')
  lines=bridge_lines(f.read_text(encoding='utf-8-sig'),mode.lower())
  if not lines:raise ValueError('NO_BRIDGES')
  dest=ROOT/'data'/('bridges_'+mode.lower()+'.txt')
  if dest.exists():shutil.copyfile(dest,ROOT/'backup'/f'{mode}_{uuid.uuid4().hex}.txt')
  dest.write_text('\n'.join(lines)+'\n',encoding='utf8');return {'imported':len(lines),'connection':'NOT_TESTED','mode':mode}
 if action=='NodeList':
  s=node_store();return {'total':len(s['nodes']),'selected':s.get('selected'),'nodes':node_public_rows(s)}
 if action=='NodeTestAll':
  return node_batch_fast()
 if action=='NodeSelect':
  current=owned('NODE')
  if current and current.get('nodeId')!=str(payload):raise ValueError('NODE_ACTIVE_STOP_FIRST')
  n=node_select(str(payload));return {'selected':n['id'],'node':NH.public_node(n)}
 if action=='NodeFavorite':
  s=node_store();found=False
  for n in s['nodes']:
   if n.get('id')==str(payload):n['favorite']=not bool(n.get('favorite'));found=True;break
  if not found:raise ValueError('NODE_NOT_FOUND')
  save_node_store(s);return {'id':str(payload),'favorite':bool(n.get('favorite'))}
 if action=='NodeImport':
  f=pathlib.Path(payload)
  if not f.is_file() or f.stat().st_size>NH.MAX_NODE_TEXT:raise ValueError('NODE_IMPORT_FILE_INVALID')
  temporary=f.parent.resolve()==(ROOT/'jobs').resolve() and f.name.startswith('node-import-')
  try:return node_import_text(f.read_text(encoding='utf-8-sig',errors='replace'),f.name)
  finally:
   if temporary:f.unlink(missing_ok=True)
 if action=='NodeImportUrl':
  f=pathlib.Path(payload);temporary=f.parent.resolve()==(ROOT/'jobs').resolve() and f.name.startswith('node-sub-')
  try:
   req=read(f,{}) or {};url=str(req.get('url') or '')
   from urllib.parse import urlparse
   u=urlparse(url)
   if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('NODE_SUBSCRIPTION_HTTPS_REQUIRED')
   r=curl(url,seconds=25,size=NH.MAX_NODE_TEXT)
   if r['exit']!=0 or r['code']!='200':raise ValueError('NODE_SUBSCRIPTION_FETCH_FAILED')
   return node_import_text(r['body'],u.hostname)
  finally:
   if temporary:f.unlink(missing_ok=True)
 if action=='NodeRefreshPublic':
  url='https://v2cross.com/en/free-v2ray-nodes/'
  r=curl(url,seconds=25,size=NH.MAX_NODE_TEXT)
  if r['exit']!=0 or r['code']!='200':raise ValueError('PUBLIC_NODE_SOURCE_UNREACHABLE')
  x=node_import_text(r['body'],'V2CROSS_PUBLIC');x['warning']='Public shared nodes are untrusted and temporary; avoid sensitive logins/payments.'
  return x
 if action=='NodeTest':
  s=node_store();n=node_selected(s)
  if not n:raise ValueError('NODE_NOT_SELECTED')
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:raise ValueError('NODE_ACTIVE_STOP_FIRST')
  was=bool(current)
  try:
   h=ensure('NODE');node_record_test(n['id'],h)
   return {'test':h,'node':NH.public_node(node_selected() or n),'temporary':not was}
  finally:
   if not was:
    with contextlib.suppress(Exception):stop('NODE')
 if action=='Export':return safe_export()
 if action=='Updates':
  rows=[]
  for repo in ('bepass-org/warp-plus','SagerNet/sing-box','bepass-org/oblivion-desktop'):
   r=curl('https://api.github.com/repos/'+repo+'/releases/latest',seconds=8)
   try:j=json.loads(r['body']);rows.append({'project':repo,'latest':j['tag_name'],'published':j.get('published_at'),'action':'CHECK_ONLY_NO_INSTALL'})
   except (ValueError,KeyError):rows.append({'project':repo,'status':'UNREACHABLE'})
  return {'releases':rows,'autoInstallation':False}
 raise ValueError('ACTION_NOT_ALLOWED')

def main():
 global JOB,DEADLINE
 a=argparse.ArgumentParser();a.add_argument('--action',required=True);a.add_argument('--mode',default='AUTO');a.add_argument('--job',required=True);a.add_argument('--payload',default='');a.add_argument('--budget',type=int,default=240);ns=a.parse_args()
 if not re.fullmatch('[a-f0-9]{32}',ns.job):raise ValueError('BAD_JOB')
 JOB=ns.job;DEADLINE=time.monotonic()+min(max(ns.budget,10),600);result_file=ROOT/'jobs'/f'{JOB}.json'
 if result_file.exists():return 2
 lock=None;result={};code=0
 try:
  import msvcrt
  lock=open(ROOT/'jobs'/'manager.lock','a+b');lock.seek(0)
  if lock.read(1)==b'':lock.write(b'0');lock.flush()
  lock.seek(0)
  try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  except OSError:raise RuntimeError('BUSY_ANOTHER_JOB')
  progress('در حال انجام درخواست',ns.mode);result=dispatch(ns.action,ns.mode,ns.payload)
  if isinstance(result,dict) and result.get('healthy') is False and ns.action in ('Connect','Verify'):code=3
 except (Exception,KeyboardInterrupt) as e:
  code=20 if isinstance(e,InterruptedError) else 124 if isinstance(e,TimeoutError) else 1;result={'error':str(e),'kind':type(e).__name__}
  # Any failed job cleans only identities it started/recovered for this job.
  # Identity/path/command-line guards prevent touching foreign listeners.
  saved=JOB;JOB='';DEADLINE=time.monotonic()+20
  for m in set(STARTED):
   try:stop(m)
   except Exception:pass
  JOB=saved
 finally:
  if lock:
   with contextlib.suppress(Exception):lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
   lock.close()
  record={'schema':1,'version':'4.0','job':JOB,'action':ns.action,'exit':code,'utc':now(),'result':result};write(result_file,record);write(ROOT/'last.json',record)
 return code
if __name__=='__main__':raise SystemExit(main())
