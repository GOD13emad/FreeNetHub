"""FreeNet Hub 4: browser-scoped, bounded, explicit control. No system VPN mutation."""
from __future__ import annotations
import argparse, concurrent.futures, contextlib, ctypes as C, datetime as dt, hashlib, importlib.util, ipaddress, json, os, pathlib, re, shutil, socket, ssl, subprocess as sp, sys, time, urllib.error, urllib.request, uuid, zipfile
from ctypes import wintypes as W
ROOT=pathlib.Path(__file__).resolve().parent.parent
APP=ROOT/'app'
_nhspec=importlib.util.spec_from_file_location("freenethub_nodehub",APP/"nodehub.py")
NH=importlib.util.module_from_spec(_nhspec);_nhspec.loader.exec_module(NH)
_dnspec=importlib.util.spec_from_file_location("freenethub_directnet",APP/"directnet.py")
DN=importlib.util.module_from_spec(_dnspec);_dnspec.loader.exec_module(DN)
PORTS={'NODE':19460,'WARP':19410,'GOOL':19413,'CFON':19414,'TOR':19450,'WEBTUNNEL':19452,'OBFS4':19453}
BRIDGE_MODES=('WEBTUNNEL','OBFS4')
DEFAULT={'theme':'dark','country':'AUTO','home':'https://www.youtube.com/','monitor':False,'autoRepair':False,'showIp':False,'minimizeToTray':True,'order':['NODE','WARP','TOR','GOOL','CFON'],'localProxy':'socks5h://127.0.0.1:9909','includeDirect':False,'testPathMode':'BASE','pingTimeoutSec':10,'downloadTimeoutSec':30,'uploadTimeoutSec':30}
ALLOWED_COUNTRIES={'AT','DE','NL','US','CA','GB','FR','SG','JP','AUTO'}
PUBLIC_REFRESH_TTL_SECONDS=1800
PUBLIC_NODE_SOURCES=(
 # Measurement-backed feeds are ordered first so the bounded 2k pool does not
 # fill with lower-confidence TCP-only candidates before locally verified feeds.
 ('AURX_HTTP_VERIFIED','aurx-http-verified','https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt'),
 ('MORPHEUS_BEST','morpheusadam-measured','https://raw.githubusercontent.com/morpheusadam/v2ray-config/main/subs/bundles/best.txt'),
 ('V2CROSS_PAGE','v2cross','https://v2cross.com/en/free-v2ray-nodes/'),
 ('SHADOWSHARE_SUB_EN','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_en'),
 ('SHADOWSHARE_SUB_DE','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_de'),
 ('SHADOWSHARE_SUB_FR','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_fr'),
 ('SHADOWSHARE_README_ID','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/README-id.md'),
 ('SHADOWSHARE_README_BN','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/README-bn.md'),
 ('SHADOWSHARE_README_ES','pawdroid-shadowshare','https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/README-es.md'),
 ('RADIKAL_TOP100','0xradikal','https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt'),
 ('MATIN_SUB1','matinghanbari','https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/subs/sub1.txt'),
)
PUBLIC_COUNTRY_NODE_SOURCES={
 'AT':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-AT.txt',
 'DE':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-DE.txt',
 'NL':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-NL.txt',
 'US':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-US.txt',
 'CA':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-CA.txt',
 'GB':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-GB.txt',
 'FR':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-FR.txt',
 'SG':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-SG.txt',
 'JP':'https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/by-country/v2ray-base64-JP.txt',
}
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
 if str(s.get('testPathMode','BASE')).upper() not in ('BASE','SELECTED'):raise ValueError('INVALID_TEST_PATH_MODE')
 for k,lo,hi in (('pingTimeoutSec',3,30),('downloadTimeoutSec',10,120),('uploadTimeoutSec',10,120)):
  try:v=int(s.get(k,DEFAULT[k]))
  except (TypeError,ValueError):raise ValueError('INVALID_'+k.upper())
  if not lo<=v<=hi:raise ValueError('INVALID_'+k.upper())
  s[k]=v
 s['testPathMode']=str(s.get('testPathMode','BASE')).upper()
 return {k:s.get(k,v) for k,v in DEFAULT.items()}
def test_timeouts():
 s=settings()
 def b(k,d,lo,hi):
  try:v=int(s.get(k,d))
  except (TypeError,ValueError):v=d
  return max(lo,min(v,hi))
 return {'ping':b('pingTimeoutSec',10,3,30),'download':b('downloadTimeoutSec',30,10,120),'upload':b('uploadTimeoutSec',30,10,120)}

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

def public_refresh_state():
 x=read(ROOT/'data'/'node_public_refresh.json',{}) or {}
 return x if isinstance(x,dict) else {}

def public_refresh_age_seconds(state=None):
 s=public_refresh_state() if state is None else state;stamp=str(s.get('lastSuccessUtc') or '')
 if not stamp:return None
 try:
  when=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
  if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
  return max(0.0,(dt.datetime.now(dt.timezone.utc)-when.astimezone(dt.timezone.utc)).total_seconds())
 except ValueError:return None

def public_refresh_is_fresh(state=None,store=None):
 s=public_refresh_state() if state is None else state;pool=node_store() if store is None else store;age=public_refresh_age_seconds(s)
 return bool(pool.get('nodes') and s.get('status')=='PASS' and age is not None and age<PUBLIC_REFRESH_TTL_SECONDS)

def public_source_names():
 return {name for name,_,__ in PUBLIC_NODE_SOURCES}

def node_selected(store=None):
 s=node_store() if store is None else store;sid=s.get('selected')
 return next((x for x in s['nodes'] if x.get('id')==sid),None)

def node_source_quality(n):
 # Upstream verification is only a ranking hint; local HTTPS/path verification remains mandatory.
 src=str(n.get('source') or '')
 return 0 if src in ('AURX_HTTP_VERIFIED','MORPHEUS_BEST') or src.startswith('AURX_COUNTRY_') else 1

def node_select(node_id):
 s=node_store()
 if not any(x.get('id')==node_id for x in s['nodes']):raise ValueError('NODE_NOT_FOUND')
 s['selected']=node_id;save_node_store(s);return node_selected(s)

# Historic public-node measurements are hints, never current connection proof.
# Expired and undated measurements cannot promote an unusable NODE to PASS.
NODE_PROOF_TTL_SECONDS = 600

def node_proof_fresh(proof, ttl_seconds=NODE_PROOF_TTL_SECONDS, reference=None):
 if not isinstance(proof,dict) or not proof.get('checked'):return False
 try:
  stamp=dt.datetime.fromisoformat(str(proof['checked']).replace('Z','+00:00'))
  if stamp.tzinfo is None:return False
  clock=reference if reference is not None else dt.datetime.now(dt.timezone.utc)
  age=(clock.astimezone(dt.timezone.utc)-stamp.astimezone(dt.timezone.utc)).total_seconds()
  return 0<=age<=ttl_seconds
 except (TypeError,ValueError,OverflowError,AttributeError):return False

def node_public_rows(store=None):
 s=node_store() if store is None else store
 def num(v,default):
  try:return float(v) if v is not None else default
  except (TypeError,ValueError):return default
 def key(n):
  ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) and node_proof_fresh(n.get('endpoint_test'),300) else {}
  lt=n.get('last_test') if isinstance(n.get('last_test'),dict) else {}
  perf=n.get('performance_test') if isinstance(n.get('performance_test'),dict) else {}
  perf_ok=bool(perf.get('ok') and node_proof_fresh(perf))
  lt_ok=bool(lt.get('healthy') and node_proof_fresh(lt))
  # Smart order: only fresh application-level health outranks TCP reachability.
  return (0 if perf_ok else 1,num(perf.get('pingMs'),float('inf')) if perf_ok else float('inf'),-num(perf.get('downloadMbps'),0.0) if perf_ok else 0.0,-num(perf.get('uploadMbps'),0.0) if perf_ok else 0.0,0 if lt_ok else 1,0 if n.get('pinned') else 1,0 if n.get('favorite') else 1,0 if ep.get('reachable') else 1,num(ep.get('latency_ms'),999999.0),str(n.get('name','')).lower())
 return [NH.public_node(x) for x in sorted(s['nodes'],key=key)]

def node_endpoint_probe(n,timeout=1.25):
 if str(n.get('protocol','')).lower() in NH.UDP_PREFLIGHT_PROTOCOLS:
  return {'reachable':None,'latency_ms':None,'checked':now(),'type':'UDP_QUIC_PREFLIGHT_NOT_APPLICABLE'}
 started=time.monotonic()
 try:
  with socket.create_connection((str(n.get('server','')),int(n.get('port',0))),timeout=timeout):pass
  return {'reachable':True,'latency_ms':round((time.monotonic()-started)*1000,1),'checked':now(),'type':'TCP_ENDPOINT_ONLY'}
 except (OSError,ValueError):
  return {'reachable':False,'latency_ms':None,'checked':now(),'type':'TCP_ENDPOINT_ONLY'}

def node_endpoint_tests_fresh(store=None,ttl_seconds=300):
 s=node_store() if store is None else store
 nodes=list(s.get('nodes') or [])
 if not nodes:return False
 now_utc=dt.datetime.now(dt.timezone.utc)
 for n in nodes:
  ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else None
  if not ep or not ep.get('checked'):return False
  try:
   stamp=dt.datetime.fromisoformat(str(ep.get('checked')).replace('Z','+00:00'))
   if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=dt.timezone.utc)
   if (now_utc-stamp.astimezone(dt.timezone.utc)).total_seconds()>ttl_seconds:return False
  except ValueError:return False
 return True

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

SINGBOX_CRONET_SHA256='EEE741046F0A3975124BAE349AEAC237AA306F3CC4DE59FF5DE070E74DBFDAEB'

def singbox_path():
 g=read(ROOT/'gateway'/'runtime'/'local_gateway.json',{}) or {};sb=g.get('singbox') if isinstance(g,dict) else None
 if not isinstance(sb,dict) or not sb.get('path') or not sb.get('sha256'):return ''
 p=pathlib.Path(sb['path'])
 if not p.is_file() or digest(p)!=str(sb['sha256']).upper():return ''
 return str(p)

def singbox_naive_ready(exe=''):
 p=pathlib.Path(exe or singbox_path())
 if not p.is_file():return False
 if os.name!='nt':return True
 cronet=p.with_name('libcronet.dll')
 return cronet.is_file() and digest(cronet)==SINGBOX_CRONET_SHA256

def node_record_test(node_id,h):
 s=node_store()
 for n in s['nodes']:
  if n.get('id')==node_id:
   n['last_test']={k:h.get(k) for k in ('healthy','country','ip','seconds','error','checked')}
   event={k:h.get(k) for k in ('healthy','country','seconds','error','checked')}
   hist=list(n.get('history') or [])
   hist.append(event)
   n['history']=hist[-20:]
 save_node_store(s)

def node_refresh_country_verified(target,force=False):
 target=str(target or '').upper()
 url=PUBLIC_COUNTRY_NODE_SOURCES.get(target)
 if not url:return {'refreshed':False,'country':target,'reason':'NO_COUNTRY_SHARD'}
 receipt_path=ROOT/'data'/'node_country_refresh.json';receipt=read(receipt_path,{}) or {}
 rec=receipt.get(target) if isinstance(receipt.get(target),dict) else {}
 source='AURX_COUNTRY_'+target
 if not force and any(str(n.get('source') or '')==source for n in node_store()['nodes']):
  stamp=str(rec.get('lastSuccessUtc') or '')
  try:
   when=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
   if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
   if (dt.datetime.now(dt.timezone.utc)-when.astimezone(dt.timezone.utc)).total_seconds()<PUBLIC_REFRESH_TTL_SECONDS:
    return {'refreshed':False,'fresh':True,'country':target,'source':source}
  except ValueError:pass
 rootctx=root_network_context()
 r=root_curl(url,seconds=20,size=NH.MAX_NODE_TEXT,ctx=rootctx)
 if r.get('exit')!=0 or r.get('code')!='200':
  return {'refreshed':False,'fresh':False,'country':target,'source':source,'error':str(r.get('error') or r.get('code') or 'UNREACHABLE')[:160]}
 try:p=NH.parse_blob(r.get('body',''),source)
 except ValueError as ex:return {'refreshed':False,'fresh':False,'country':target,'source':source,'error':str(ex)}
 incoming=list(p.get('nodes') or [])
 if not incoming:return {'refreshed':False,'fresh':False,'country':target,'source':source,'error':'COUNTRY_SHARD_EMPTY'}
 old=node_store();old_by={str(n.get('id')):n for n in old['nodes'] if n.get('id')}
 matching=[old_by[str(n.get('id'))] for n in incoming if str(n.get('id')) in old_by]
 fresh=NH.merge(matching,incoming);fresh_ids={str(n.get('id')) for n in fresh}
 preserved=[n for n in old['nodes'] if str(n.get('id')) not in fresh_ids]
 final=(fresh+preserved)[:NH.MAX_NODES]
 selected=str(old.get('selected') or '')
 if not any(str(n.get('id'))==selected for n in final):selected=str(final[0].get('id')) if final else ''
 save_node_store({'schema':1,'selected':selected,'nodes':final})
 stamp=now();receipt[target]={'status':'PASS','lastSuccessUtc':stamp,'source':source,'found':len(incoming),'parseErrors':len(p.get('errors') or [])}
 write(receipt_path,receipt)
 return {'refreshed':True,'fresh':True,'country':target,'source':source,'found':len(incoming),'total':len(final),'parseErrors':len(p.get('errors') or [])}

def ensure_node(target='AUTO',limit=12):
 s=node_store()
 if not s['nodes']:raise ValueError('NODE_POOL_EMPTY')
 target=str(target or 'AUTO').upper()
 if target!='AUTO':
  # Pull the verified country shard as a ranking hint. Failure is non-fatal:
  # cached/public nodes remain available and every candidate is still verified locally.
  node_refresh_country_verified(target,False)
  s=node_store()
  # Strict-country connect first performs the same concurrent TCP endpoint screen
  # as Test All, so dead public nodes do not consume the real HTTPS/country budget.
  if not node_endpoint_tests_fresh(s):node_batch_fast()
  s=node_store()
  candidates=[n for n in s['nodes'] if isinstance(n.get('endpoint_test'),dict) and (n['endpoint_test'].get('reachable') is True or str(n.get('protocol','')).lower() in NH.UDP_PREFLIGHT_PROTOCOLS)]
  if not candidates:raise RuntimeError('NODE_POOL_NO_REACHABLE_ENDPOINTS')
  s=dict(s);s['nodes']=candidates
 def score(n):
  lt=n.get('last_test') if isinstance(n.get('last_test'),dict) else {}
  exact=target!='AUTO' and lt.get('healthy') and node_proof_fresh(lt) and str(lt.get('country','')).upper()==target
  shard=target!='AUTO' and str(n.get('source') or '')=='AURX_COUNTRY_'+target
  aliases={'AT':('austria','?sterreich','autriche'),'DE':('germany','deutschland','allemagne'),'NL':('netherlands','niederlande','pays-bas','holland'),'US':('united states','usa','�tats unis','estados unidos'),'CA':('canada','kanada'),'GB':('united kingdom','uk','royaume-uni','vereinigtes k?nigreich'),'FR':('france','frankreich','francia'),'SG':('singapore','singapour','singapur'),'JP':('japan','japon','japan')}
  name=str(n.get('name','')).lower()
  hint=target!='AUTO' and (target.lower() in name or any(x in name for x in aliases.get(target,())))
  ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) and node_proof_fresh(n.get('endpoint_test'),300) else {}
  perf=n.get('performance_test') if isinstance(n.get('performance_test'),dict) else {}
  perf_ok=bool(perf.get('ok') and node_proof_fresh(perf))
  try:perf_ping=float(perf.get('pingMs')) if perf.get('pingMs') is not None else 999999.0
  except (TypeError,ValueError):perf_ping=999999.0
  try:perf_down=float(perf.get('downloadMbps') or 0)
  except (TypeError,ValueError):perf_down=0.0
  try:perf_up=float(perf.get('uploadMbps') or 0)
  except (TypeError,ValueError):perf_up=0.0
  if not perf_ok:perf_ping=999999.0;perf_down=0.0;perf_up=0.0
  healthy=bool(lt.get('healthy') and node_proof_fresh(lt));lat=lt.get('seconds') if healthy else None
  return (0 if exact else 1,0 if shard else 1,0 if hint else 1,0 if perf_ok else 1,perf_ping,-perf_down,-perf_up,0 if n.get('pinned') else 1,0 if n.get('favorite') else 1,0 if healthy else 1,node_source_quality(n),0 if ep.get('reachable') else 1,float(ep.get('latency_ms',999999) or 999999),float(lat) if isinstance(lat,(int,float)) else 9999)

 nodes=sorted(s['nodes'],key=score)
 last=[]
 for n in nodes[:max(1,min(int(limit),24))]:
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:stop('NODE')
  node_select(n['id'])
  try:
   h=ensure('NODE');node_record_test(n['id'],h)
   actual=str(h.get('country') or '').upper()
   if h.get('healthy') and (target=='AUTO' or actual==target):return h
   if h.get('healthy') and target!='AUTO' and actual!=target:
    with contextlib.suppress(Exception):stop('NODE')
    h=dict(h);h['healthy']=False;h['error']='COUNTRY_MISMATCH_OR_UNKNOWN'
    node_record_test(n['id'],h)
   last.append({'id':n['id'],'error':h.get('error'),'country':h.get('country')})
  except (ValueError,RuntimeError) as e:
   with contextlib.suppress(Exception):stop('NODE')
   node_record_test(n['id'],{'healthy':False,'country':'','ip':'','seconds':None,'error':str(e),'checked':now()})
   last.append({'id':n['id'],'error':str(e)})
 raise RuntimeError('NODE_COUNTRY_NOT_FOUND' if target!='AUTO' else 'NODE_POOL_NO_HEALTHY_NODE')

def country_target():
 return str(settings().get('country','AUTO')).upper()

def bridge_configured(mode):
 mode=str(mode or '').upper()
 if mode not in BRIDGE_MODES:return False
 f=ROOT/'data'/('bridges_'+mode.lower()+'.txt')
 try:
  if not f.is_file() or f.stat().st_size<=0 or f.stat().st_size>65536:return False
  return bool(bridge_lines(f.read_text(encoding='utf-8-sig'),mode.lower()))
 except (OSError,UnicodeError,ValueError):
  return False

def configured_bridge_modes():
 return [m for m in BRIDGE_MODES if bridge_configured(m)]

def connect_candidates(mode):
 c=country_target()
 if c=='AUTO':
  if mode!='AUTO':return [mode]
  out=[]
  for m in list(settings().get('order',DEFAULT['order']))+configured_bridge_modes():
   if m in PORTS and (m not in BRIDGE_MODES or bridge_configured(m)) and m not in out:out.append(m)
  return out
 if mode=='AUTO':return ['NODE','CFON']
 if mode not in ('NODE','CFON','CUSTOM'):raise ValueError('COUNTRY_MODE_UNSUPPORTED')
 return [mode]

def smart_benchmark_candidates():
 # Smart is a selector, never a synthetic benchmark row. Benchmark every real
 # browser method so the UI gets a terminal result for every row. Optional
 # bridge transports are included only when their private config validates.
 out=[]
 preferred=[x for x in settings().get('order',[]) if x in PORTS]
 for m in preferred+list(DEFAULT['order'])+configured_bridge_modes()+['CUSTOM','DIRECT']:
  if m in BRIDGE_MODES and not bridge_configured(m):continue
  if m not in out:out.append(m)
 return out

def performance_rank_key(perf):
 if not isinstance(perf,dict) or not perf.get('ok'):return (1,float('inf'),0.0,0.0)
 def num(k,default=0.0):
  try:
   v=perf.get(k)
   return float(v) if v is not None else default
  except (TypeError,ValueError):return default
 # Deterministic Smart policy: lowest measured latency first, then higher
 # download and upload as tie-breakers. Missing metrics never outrank measured.
 return (0,num('pingMs',float('inf')),-num('downloadMbps'),-num('uploadMbps'))

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

def public_dns_ips(host):
 host=str(host or '').strip().lower()
 if not re.fullmatch(r'[a-z0-9.-]{1,253}',host) or '..' in host:return []
 ips=[]
 try:secure=DN.doh_a(host,2.5)
 except Exception:secure={'ips':[]}
 for ip in secure.get('ips') or []:
  try:
   addr=ipaddress.ip_address(str(ip))
   if addr.version==4 and addr.is_global and str(addr) not in ips:ips.append(str(addr))
  except ValueError:pass
 if ips:return ips[:4]
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh:return []
 for server in ('1.1.1.1','8.8.8.8'):
  script="$h='"+host+"';Resolve-DnsName -Name $h -Type A -Server '"+server+"' -DnsOnly -QuickTimeout -ErrorAction SilentlyContinue|Where-Object{$_.IPAddress}|Select-Object -ExpandProperty IPAddress|ConvertTo-Json -Compress"
  try:r=native([pwsh,'-NoProfile','-Command',script],5)
  except TimeoutError:continue
  if r.get('exit')!=0 or not str(r.get('out') or '').strip():continue
  try:v=json.loads(r['out'])
  except (ValueError,TypeError):continue
  vals=v if isinstance(v,list) else [v]
  for ip in vals:
   try:
    addr=ipaddress.ip_address(str(ip));x=str(addr)
    if addr.version==4 and addr.is_global and x not in ips:ips.append(x)
   except ValueError:pass
  if ips:break
 return ips[:4]

def _curl_parse_result(r,started,size,fetch_path):
 bodytext,sep,meta=str(r.get('out') or '').rpartition('\n__FNH__');parts=meta.split()
 return {'exit':int(r.get('exit',1)),'code':parts[0] if parts else '000','seconds':float(parts[1]) if len(parts)>1 else round(time.monotonic()-started,3),'bytes':int(float(parts[2])) if len(parts)>2 else 0,'bps':float(parts[3]) if len(parts)>3 else 0,'body':bodytext[:size],'error':str(r.get('err') or '')[:700],'fetchPath':fetch_path}

def _openssl_direct_fetch(url,seconds=7,body=True,size=262144):
 # Independent direct HTTPS fallback for networks that interfere specifically
 # with the Windows Schannel/curl TLS fingerprint. No proxy is inherited.
 started=time.monotonic()
 if not re.match(r'^https://[A-Za-z0-9.-]+(?:/|$)',str(url)):
  return {'exit':1,'code':'000','seconds':0.0,'bytes':0,'bps':0.0,'body':'','error':'OPENSSL_FALLBACK_HTTPS_ONLY','fetchPath':'OPENSSL_DIRECT_FALLBACK'}
 try:
  ctx=ssl.create_default_context()
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ctx))
  req=urllib.request.Request(str(url),headers={'User-Agent':'Mozilla/5.0 FreeNetHub-DirectFallback/1.0','Accept':'*/*'})
  try:
   resp=opener.open(req,timeout=max(1,float(seconds)))
  except urllib.error.HTTPError as exc:
   resp=exc
  with resp:
   code=str(getattr(resp,'status',getattr(resp,'code',0)) or '000')
   data=resp.read(int(size)+1)
  elapsed=max(.001,time.monotonic()-started)
  if len(data)>int(size):
   return {'exit':63,'code':code,'seconds':elapsed,'bytes':len(data),'bps':len(data)/elapsed,'body':'','error':'MAX_FILESIZE_EXCEEDED','fetchPath':'OPENSSL_DIRECT_FALLBACK'}
  return {'exit':0,'code':code,'seconds':elapsed,'bytes':len(data),'bps':len(data)/elapsed,'body':data.decode('utf-8','replace') if body else '','error':'','fetchPath':'OPENSSL_DIRECT_FALLBACK'}
 except Exception as exc:
  elapsed=max(.001,time.monotonic()-started)
  return {'exit':1,'code':'000','seconds':elapsed,'bytes':0,'bps':0.0,'body':'','error':(type(exc).__name__+': '+str(exc))[:700],'fetchPath':'OPENSSL_DIRECT_FALLBACK'}

def curl(url,proxy='',seconds=7,body=True,size=262144,interface=''):
 args=['curl.exe','-q','-4','-sS','--connect-timeout','3','--max-time',str(seconds),'--max-filesize',str(size),'--write-out','\n__FNH__%{http_code} %{time_total} %{size_download} %{speed_download}']
 args+=['--proxy',proxy,'--noproxy',''] if proxy else ['--noproxy','*']
 if interface:args+=['--interface',str(interface)]
 if not body:args+=['-o','NUL']
 args+=[url];started=time.monotonic()
 try:r=native(args,seconds+2)
 except TimeoutError:r={'exit':124,'out':'','err':'TIMEOUT'}
 result=_curl_parse_result(r,started,size,'PROXY_DNS' if proxy else 'SYSTEM_DNS')
 if proxy or (result['exit']==0 and result['code']!='000'):return result
 m=re.match(r'^https://([A-Za-z0-9.-]+)(?:/|$)',str(url))
 if not m:return result
 host=m.group(1).lower()
 for ip in public_dns_ips(host)[:2]:
  retry=list(args[:-1])+['--resolve',f'{host}:443:{ip}',args[-1]]
  try:rr=native(retry,seconds+2)
  except TimeoutError:continue
  alt=_curl_parse_result(rr,started,size,'PUBLIC_DNS_RESOLVE')
  if alt['exit']==0 and alt['code']!='000':return alt
 if interface:return result
 fallback=_openssl_direct_fetch(url,seconds,body,size)
 if fallback.get('exit')==0 and fallback.get('code')!='000':return fallback
 return result


def root_network_context():
 sess=read(ROOT/'gateway'/'runtime'/'gateway-session.json',{}) or {}
 if str(sess.get('mode') or '')!='PC_TUNNEL':
  return {'bound':False,'interface':'','interfaceAlias':'','proof':'SYSTEM_DEFAULT_NO_FNH_PC_TUNNEL'}
 br=sess.get('baseRoute') if isinstance(sess.get('baseRoute'),dict) else {}
 src=str(br.get('sourceAddress') or '')
 try:
  ip=ipaddress.ip_address(src)
  if ip.version!=4 or ip.is_loopback or ip.is_unspecified:raise ValueError()
 except ValueError as ex:
  raise RuntimeError('ROOT_BASE_ROUTE_SOURCE_INVALID') from ex
 expected=sess.get('baseTrace') if isinstance(sess.get('baseTrace'),dict) else {}
 post=((sess.get('verify') or {}).get('trace') if isinstance(sess.get('verify'),dict) else {}) or {}
 pr=curl('https://www.cloudflare.com/cdn-cgi/trace','',seconds=8,size=65536,interface=src)
 got=trace(pr.get('body','')) if pr.get('exit')==0 and pr.get('code')=='200' else {}
 if not got:raise RuntimeError('ROOT_BASE_ROUTE_PROBE_FAILED')
 expected_ip=str(expected.get('ip') or '');post_ip=str(post.get('ip') or '');got_ip=str(got.get('ip') or '')
 if expected_ip and post_ip and expected_ip!=post_ip and got_ip==post_ip:
  raise RuntimeError('ROOT_BASE_ROUTE_TUNNEL_LEAK')
 expected_warp=str(expected.get('warp') or '').lower();post_warp=str(post.get('warp') or '').lower();got_warp=str(got.get('warp') or '').lower()
 if expected_warp and post_warp and expected_warp!=post_warp and got_warp==post_warp:
  raise RuntimeError('ROOT_BASE_ROUTE_TUNNEL_LEAK')
 return {'bound':True,'interface':src,'interfaceAlias':str(br.get('interfaceAlias') or ''),'proof':'BOUND_PRE_TUN_SOURCE_AND_TRACE_NOT_POST_TUN','trace':got}

def root_network_public(ctx):
 return {'bound':bool(ctx.get('bound')),'interfaceAlias':str(ctx.get('interfaceAlias') or ''),'proof':str(ctx.get('proof') or '')}

def root_curl(url,seconds=7,body=True,size=262144,ctx=None):
 c=root_network_context() if ctx is None else ctx
 interface=str(c.get('interface') or '')
 if interface:return curl(url,proxy='',seconds=seconds,body=body,size=size,interface=interface)
 return curl(url,proxy='',seconds=seconds,body=body,size=size)

def node_refresh_public(force=False):
 old=node_store();state=public_refresh_state();age=public_refresh_age_seconds(state)
 families=sorted({family for _,family,__ in PUBLIC_NODE_SOURCES})
 if not force and public_refresh_is_fresh(state,old):
  return {'refreshed':False,'fresh':True,'ageSeconds':round(age,1) if age is not None else None,'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'total':len(old['nodes']),'selected':old.get('selected'),'sourceFamilies':families,'sources':list(state.get('sources') or []),'failedSources':list(state.get('failedSources') or []),'nodes':node_public_rows(old)}
 progress('Refreshing public node sources','NODE')
 rootctx=root_network_context()
 fetched={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=min(8,len(PUBLIC_NODE_SOURCES))) as ex:
  fs={ex.submit(root_curl,url,seconds=18,size=NH.MAX_NODE_TEXT,ctx=rootctx):(name,family,url) for name,family,url in PUBLIC_NODE_SOURCES}
  for f in concurrent.futures.as_completed(fs):
   check();name,family,url=fs[f]
   try:fetched[name]=f.result()
   except Exception as exc:fetched[name]={'exit':1,'code':'','body':'','error':str(exc)}
 incoming=[];ok=[];failed=[];stats=[];parsed_raw=0
 for name,family,_ in PUBLIC_NODE_SOURCES:
  r=fetched.get(name,{})
  if r.get('exit')==0 and r.get('code')=='200':
   try:p=NH.parse_blob(r.get('body',''),name)
   except ValueError as exc:
    failed.append(name);stats.append({'name':name,'family':family,'status':'PARSE_FAILED','found':0,'error':str(exc)});continue
   incoming.extend(p['nodes']);found=len(p['nodes']);parsed_raw+=found;ok.append(name)
   stats.append({'name':name,'family':family,'status':'PASS','found':found,'parseErrors':len(p.get('errors') or []),'fetchPath':str(r.get('fetchPath') or 'UNKNOWN')})
  else:
   failed.append(name);stats.append({'name':name,'family':family,'status':'FETCH_FAILED','found':0,'error':str(r.get('error') or r.get('code') or 'UNREACHABLE')[:160],'fetchPath':str(r.get('fetchPath') or 'UNKNOWN')})
 if not ok:
  degraded={'schema':1,'status':'DEGRADED','checkedUtc':now(),'lastSuccessUtc':state.get('lastSuccessUtc'),'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'sourceFamilies':families,'sources':[],'failedSources':failed,'sourceStats':stats}
  write(ROOT/'data'/'node_public_refresh.json',degraded)
  if old['nodes']:
   return {'refreshed':False,'fresh':False,'degraded':True,'ageSeconds':age,'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'total':len(old['nodes']),'selected':old.get('selected'),'sourceFamilies':families,'sources':[],'failedSources':failed,'nodes':node_public_rows(old),'warning':'Public refresh failed; retained the existing pool.'}
  raise ValueError('PUBLIC_NODE_SOURCE_UNREACHABLE')
 old_by={str(n.get('id')):n for n in old['nodes'] if n.get('id')}
 old_by_raw={str(n.get('raw')):n for n in old['nodes'] if n.get('raw')}
 incoming_ids={str(n.get('id')) for n in incoming if n.get('id')}
 matching=[];migrated_old_ids=set()
 for n in incoming:
  nid=str(n.get('id') or '')
  if nid in old_by:
   matching.append(old_by[nid]);continue
  raw=str(n.get('raw') or '')
  legacy=old_by_raw.get(raw) if raw else None
  if legacy:
   # Parser-semantic migrations may change node ID. Preserve only user-authored
   # metadata; old endpoint/HTTPS/performance evidence belongs to the old config.
   matching.append({'id':nid,'favorite':bool(legacy.get('favorite')),'pinned':bool(legacy.get('pinned')),'rating':int(legacy.get('rating',0) or 0),'tags':list(legacy.get('tags') or [])[:16],'note':str(legacy.get('note') or '')[:500]})
   migrated_old_ids.add(str(legacy.get('id') or ''))
 fresh_nodes=NH.merge(matching,incoming)
 refreshed_names=set(ok)
 preserved=[n for n in old['nodes'] if str(n.get('id')) not in incoming_ids and str(n.get('id')) not in migrated_old_ids and (str(n.get('source') or '') not in refreshed_names or bool(n.get('favorite')) or bool(n.get('pinned')))]
 dropped=sum(1 for n in old['nodes'] if str(n.get('id')) not in incoming_ids and str(n.get('source') or '') in refreshed_names and not n.get('favorite') and not n.get('pinned'))
 final_nodes=NH.merge(preserved,fresh_nodes)
 selected=str(old.get('selected') or '')
 if not any(str(n.get('id'))==selected for n in final_nodes):selected=str(final_nodes[0].get('id')) if final_nodes else ''
 save_node_store({'schema':1,'selected':selected,'nodes':final_nodes})
 pool=node_store();stamp=now()
 cached_reachable=sum(1 for n in pool['nodes'] if isinstance(n.get('endpoint_test'),dict) and n['endpoint_test'].get('reachable') is True)
 receipt={'schema':1,'status':'PASS','checkedUtc':stamp,'lastSuccessUtc':stamp,'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'sourceFamilies':families,'sources':ok,'failedSources':failed,'sourceStats':stats,'parsedRaw':parsed_raw,'freshPublicUnique':len(incoming_ids),'staleDropped':dropped,'total':len(pool['nodes']),'endpointTest':'DEFERRED_TO_NODE_TEST_ALL','cachedReachable':cached_reachable}
 write(ROOT/'data'/'node_public_refresh.json',receipt)
 return {'refreshed':True,'fresh':True,'ageSeconds':0.0,'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'imported':len(incoming_ids),'parsedRaw':parsed_raw,'staleDropped':dropped,'total':len(pool['nodes']),'reachableCached':cached_reachable,'endpointTest':'DEFERRED_TO_NODE_TEST_ALL','selected':pool.get('selected'),'sourceFamilies':families,'sources':ok,'failedSources':failed,'sourceStats':stats,'nodes':node_public_rows(pool),'warning':'Public shared nodes are untrusted and temporary; run Test All before relying on a node.'}
def _route_print_ipv4_rows(text):
 rows=[]
 for line in str(text or '').splitlines():
  m=re.match(r'^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\S+)\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)\s*$',line)
  if not m:continue
  dest,mask,gateway,interface,metric=m.groups()
  try:
   net=ipaddress.ip_network(dest+'/'+mask,strict=False);ipaddress.ip_address(interface)
  except ValueError:
   continue
  rows.append({'network':net,'destination':dest,'netmask':mask,'gateway':gateway,'interface':interface,'metric':int(metric)})
 return rows

def _windows_ipv4_ifindex(ip):
 if os.name!='nt':raise RuntimeError('WINDOWS_IP_HELPER_REQUIRED')
 DWORD=C.c_uint32;ULONG=C.c_uint32;USHORT=C.c_ushort
 class MIB_IPADDRROW(C.Structure):
  _fields_=[('dwAddr',DWORD),('dwIndex',DWORD),('dwMask',DWORD),('dwBCastAddr',DWORD),('dwReasmSize',DWORD),('unused1',USHORT),('wType',USHORT)]
 api=C.WinDLL('iphlpapi.dll')
 fn=api.GetIpAddrTable;fn.argtypes=[C.c_void_p,C.POINTER(ULONG),C.c_int];fn.restype=DWORD
 size=ULONG(0);fn(None,C.byref(size),0)
 if not size.value:raise RuntimeError('DIRECT_IP_TABLE_UNAVAILABLE')
 buf=C.create_string_buffer(size.value)
 rc=int(fn(buf,C.byref(size),0))
 if rc!=0:raise RuntimeError('DIRECT_IP_TABLE_UNAVAILABLE')
 count=int(C.cast(buf,C.POINTER(DWORD))[0]);base=C.addressof(buf)+C.sizeof(DWORD)
 for i in range(count):
  row=MIB_IPADDRROW.from_address(base+i*C.sizeof(MIB_IPADDRROW))
  addr=socket.inet_ntoa(C.string_at(C.addressof(row),4))
  if addr==str(ip):return int(row.dwIndex)
 raise RuntimeError('DIRECT_ROUTE_IDENTITY_MISMATCH')

def _windows_if_row2(idx):
 if os.name!='nt':raise RuntimeError('WINDOWS_IP_HELPER_REQUIRED')
 U32=C.c_uint32;U64=C.c_uint64;U8=C.c_ubyte
 class GUID(C.Structure):
  _fields_=[('Data1',U32),('Data2',C.c_ushort),('Data3',C.c_ushort),('Data4',U8*8)]
 class MIB_IF_ROW2(C.Structure):
  _fields_=[
   ('InterfaceLuid',U64),('InterfaceIndex',U32),('InterfaceGuid',GUID),
   ('Alias',C.c_wchar*257),('Description',C.c_wchar*257),
   ('PhysicalAddressLength',U32),('PhysicalAddress',U8*32),('PermanentPhysicalAddress',U8*32),
   ('Mtu',U32),('Type',U32),('TunnelType',U32),('MediaType',U32),('PhysicalMediumType',U32),
   ('AccessType',U32),('DirectionType',U32),('InterfaceAndOperStatusFlags',U8),('_pad',U8*3),
   ('OperStatus',U32),('AdminStatus',U32),('MediaConnectState',U32),('NetworkGuid',GUID),('ConnectionType',U32),
   ('TransmitLinkSpeed',U64),('ReceiveLinkSpeed',U64),
   ('InOctets',U64),('InUcastPkts',U64),('InNUcastPkts',U64),('InDiscards',U64),('InErrors',U64),('InUnknownProtos',U64),
   ('InUcastOctets',U64),('InMulticastOctets',U64),('InBroadcastOctets',U64),
   ('OutOctets',U64),('OutUcastPkts',U64),('OutNUcastPkts',U64),('OutDiscards',U64),('OutErrors',U64),
   ('OutUcastOctets',U64),('OutMulticastOctets',U64),('OutBroadcastOctets',U64),('OutQLen',U64)
  ]
 api=C.WinDLL('iphlpapi.dll')
 fn=api.GetIfEntry2;fn.argtypes=[C.POINTER(MIB_IF_ROW2)];fn.restype=U32
 row=MIB_IF_ROW2();row.InterfaceIndex=int(idx)
 rc=int(fn(C.byref(row)))
 if rc!=0 or int(row.InterfaceIndex)!=int(idx):raise RuntimeError('DIRECT_ADAPTER_IDENTITY_UNAVAILABLE')
 flags=int(row.InterfaceAndOperStatusFlags)
 return {
  'ifIndex':int(row.InterfaceIndex),'adapterName':str(row.Alias or ''),'description':str(row.Description or ''),
  'hardware':bool(flags&1),'connectorPresent':bool(flags&4),'status':'Up' if int(row.OperStatus)==1 else str(int(row.OperStatus)),
  'ifType':int(row.Type),'transmitLinkSpeed':int(row.TransmitLinkSpeed),'receiveLinkSpeed':int(row.ReceiveLinkSpeed)
 }

def direct_route():
 rr=native(['route.exe','print','-4'],6)
 if rr.get('exit')!=0:raise RuntimeError('DIRECT_ROUTE_UNAVAILABLE')
 rows=_route_print_ipv4_rows(rr.get('out',''))
 defaults=[x for x in rows if x['network'].prefixlen==0]
 if not defaults:raise RuntimeError('DIRECT_ROUTE_UNAVAILABLE')
 default=min(defaults,key=lambda x:x['metric'])
 try:gateway=str(ipaddress.ip_address(default['gateway']))
 except ValueError as ex:raise RuntimeError('DIRECT_ROUTE_UNAVAILABLE') from ex
 idx=_windows_ipv4_ifindex(default['interface'])
 adapter=_windows_if_row2(idx)
 label=(str(adapter.get('adapterName',''))+' '+str(adapter.get('description',''))).lower()
 suspicious=bool(re.search(r'\b(vpn|warp|wireguard|openvpn|tap|tun|wintun|tailscale|zerotier|mihomo|sing-box|fortinet|tunnelbear|hyper-v|vethernet)\b',label))
 overrides=[]
 for row in rows:
  net=row['network']
  if net.prefixlen==0 or net.prefixlen>8 or not net.is_global or net.is_multicast:continue
  if row['interface']==default['interface']:continue
  overrides.append({'DestinationPrefix':str(net),'InterfaceAlias':'','InterfaceIndex':None,'NextHop':row['gateway'],'RouteMetric':row['metric']})
 x={
  'ifIndex':idx,'nextHop':gateway,'routeMetric':default['metric'],'interfaceMetric':None,
  'adapterName':adapter.get('adapterName',''),'description':adapter.get('description',''),
  'hardware':bool(adapter.get('hardware')),'status':adapter.get('status',''),'ifType':adapter.get('ifType'),
  'ip':default['interface'],'systemOverrideRoutes':overrides,'routeProof':'ROUTE_EXE+WINDOWS_IPHELPER'
 }
 x['trustedPhysical']=bool(x['hardware'] and str(x['status']).lower()=='up' and not suspicious and x['ip'] and not overrides)
 return x

def ping_direct(seconds=None):
 if seconds is None:seconds=test_timeouts()['ping']
 seconds=max(3,min(int(seconds),30))
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh:return {'ok':False,'avgMs':None,'note':'PowerShell unavailable'}
 script="$r=Test-Connection -TargetName 1.1.1.1 -Count 3 -IPv4 -ErrorAction SilentlyContinue;if(!$r){exit 2};$v=@($r|ForEach-Object{$_.Latency}|Where-Object{$_ -ne $null});if(!$v){exit 3};[math]::Round((($v|Measure-Object -Average).Average),1)"
 try:r=native([pwsh,'-NoProfile','-Command',script],seconds)
 except TimeoutError:return {'ok':False,'avgMs':None,'target':'1.1.1.1','type':'ICMP','note':'ICMP_TIMEOUT'}
 try:v=float(r['out'].strip()) if r['exit']==0 else None
 except ValueError:v=None
 return {'ok':v is not None,'avgMs':v,'target':'1.1.1.1','type':'ICMP'}

def cloudflare_upload(sample_bytes=1000000,seconds=20,proxy=''):
 sample_bytes=max(131072,min(int(sample_bytes),5000000));tmp=ROOT/'jobs'/f'{JOB or uuid.uuid4().hex}.speed-upload.bin'
 tmp.parent.mkdir(parents=True,exist_ok=True)
 try:
  with open(tmp,'wb') as f:f.truncate(sample_bytes)
  args=['curl.exe','-q','-4','-sS','--connect-timeout','3','--max-time',str(seconds)]
  args+=['--proxy',proxy,'--noproxy',''] if proxy else ['--noproxy','*']
  args+=['-o','NUL','--data-binary','@'+str(tmp),'--write-out','\n__FNH__%{http_code} %{time_total} %{size_upload} %{speed_upload}','https://speed.cloudflare.com/__up']
  try:r=native(args,seconds+2)
  except TimeoutError:r={'exit':124,'out':'','err':'TIMEOUT'}
  bodytext,sep,meta=r['out'].rpartition('\n__FNH__');parts=meta.split()
  return {'exit':r['exit'],'code':parts[0] if parts else '000','seconds':float(parts[1]) if len(parts)>1 else None,'bytes':int(float(parts[2])) if len(parts)>2 else 0,'bps':float(parts[3]) if len(parts)>3 else 0,'error':r['err'][:700]}
 finally:
  tmp.unlink(missing_ok=True)

def path_speed(mode,download_bytes=2000000,upload_bytes=500000):
 mode=str(mode or 'AUTO').upper();t=test_timeouts()
 if mode=='DIRECT':return direct_speed()
 if mode not in PORTS and mode!='CUSTOM':raise ValueError('SPEED_MODE_UNSUPPORTED')
 if mode in PORTS and not owned(mode):raise RuntimeError('CONNECT_FIRST')
 proxy=mode_proxy(mode)
 trace_r=curl('https://www.cloudflare.com/cdn-cgi/trace',proxy,seconds=t['ping']);tr=trace(trace_r.get('body',''))
 ping_r=curl('https://www.youtube.com/generate_204',proxy,seconds=t['ping'],body=False)
 if trace_r.get('exit')!=0 or trace_r.get('code')!='200' or not tr or ping_r.get('exit')!=0 or ping_r.get('code')!='204':
  ping_ms=round(float(ping_r.get('seconds',0))*1000,1) if ping_r.get('exit')==0 and ping_r.get('code')=='204' else None
  return {
   'mode':mode,'path':'PROXY_PATH' if proxy else 'SYSTEM_PATH','ok':False,
   'pingMs':ping_ms,'pingType':'HTTPS_RTT','downloadMbps':None,'uploadMbps':None,
   'downloadSampleBytes':0,'uploadSampleBytes':0,'country':tr.get('loc','') if tr else '',
   'exitIp':tr.get('ip','') if tr else '','checked':now(),'proxyUsed':bool(proxy),
   'error':'PATH_SPEED_VERIFICATION_FAILED',
   'verification':{'traceCode':trace_r.get('code'),'traceExit':trace_r.get('exit'),'youtubeCode':ping_r.get('code'),'youtubeExit':ping_r.get('exit')}
  }
 down=curl('https://speed.cloudflare.com/__down?bytes='+str(int(download_bytes)),proxy,seconds=t['download'],body=False,size=int(download_bytes)+65536)
 up=cloudflare_upload(int(upload_bytes),t['upload'],proxy)
 down_ok=down.get('exit')==0 and down.get('code')=='200' and down.get('bytes')==int(download_bytes)
 up_ok=up.get('exit')==0 and up.get('code')=='200' and up.get('bytes')==int(upload_bytes)
 return {
  'mode':mode,'path':'PROXY_PATH' if proxy else 'SYSTEM_PATH','ok':bool(down_ok and up_ok),
  'pingMs':round(float(ping_r.get('seconds',0))*1000,1),'pingType':'HTTPS_RTT',
  'downloadMbps':round(float(down.get('bps',0))*8/1e6,2),'uploadMbps':round(float(up.get('bps',0))*8/1e6,2),
  'downloadSampleBytes':down.get('bytes',0),'uploadSampleBytes':up.get('bytes',0),
  'country':tr.get('loc',''),'exitIp':tr.get('ip',''),'checked':now(),
  'proxyUsed':bool(proxy),'error':'' if (down_ok and up_ok) else 'THROUGHPUT_SAMPLE_INCOMPLETE'
 }

def system_speed(provider='WARP'):
 provider=str(provider or 'WARP').upper();t=test_timeouts()
 if provider not in ('WARP','NODE'):raise ValueError('SYSTEM_PROVIDER_UNSUPPORTED')
 sess=read(ROOT/'gateway'/'runtime'/'gateway-session.json',{}) or {}
 if str(sess.get('mode') or '')!='PC_TUNNEL' or str(sess.get('provider') or '').upper()!=provider:raise RuntimeError('SYSTEM_TUNNEL_NOT_ACTIVE')
 trace_r=curl('https://www.cloudflare.com/cdn-cgi/trace','',seconds=t['ping']);tr=trace(trace_r.get('body',''))
 ping_r=curl('https://www.youtube.com/generate_204','',seconds=t['ping'],body=False)
 if trace_r.get('exit')!=0 or trace_r.get('code')!='200' or not tr or ping_r.get('exit')!=0 or ping_r.get('code')!='204':
  ping_ms=round(float(ping_r.get('seconds',0))*1000,1) if ping_r.get('exit')==0 and ping_r.get('code')=='204' else None
  return {'mode':'SYSTEM','provider':provider,'path':'CURRENT_SYSTEM_DEFAULT_ROUTE','ok':False,
   'pingMs':ping_ms,'pingType':'HTTPS_RTT','downloadMbps':None,'uploadMbps':None,
   'country':tr.get('loc','') if tr else '','exitIp':tr.get('ip','') if tr else '',
   'warp':tr.get('warp','') if tr else '','checked':now(),'error':'SYSTEM_SPEED_VERIFICATION_FAILED',
   'verification':{'traceCode':trace_r.get('code'),'traceExit':trace_r.get('exit'),'youtubeCode':ping_r.get('code'),'youtubeExit':ping_r.get('exit')}}
 if provider=='WARP' and str(tr.get('warp','')).lower()!='on':raise RuntimeError('SYSTEM_TUNNEL_NOT_ACTIVE')
 target=country_target()
 if provider=='NODE' and target!='AUTO' and str(tr.get('loc') or '').upper()!=target:raise RuntimeError('SYSTEM_NODE_COUNTRY_MISMATCH')
 down=curl('https://speed.cloudflare.com/__down?bytes=2000000','',seconds=t['download'],body=False,size=2065536)
 up=cloudflare_upload(500000,t['upload'],'')
 down_ok=down.get('exit')==0 and down.get('code')=='200'
 up_ok=up.get('exit')==0 and up.get('code')=='200'
 return {'mode':'SYSTEM','provider':provider,'path':'CURRENT_SYSTEM_DEFAULT_ROUTE','ok':bool(down_ok and up_ok),
  'pingMs':round(float(ping_r.get('seconds',0))*1000,1),'pingType':'HTTPS_RTT','downloadMbps':round(float(down.get('bps',0))*8/1e6,2) if down_ok else None,
  'uploadMbps':round(float(up.get('bps',0))*8/1e6,2) if up_ok else None,'country':tr.get('loc',''),'exitIp':tr.get('ip',''),'warp':tr.get('warp',''),'checked':now(),
  'error':'' if (down_ok and up_ok) else 'THROUGHPUT_SAMPLE_INCOMPLETE'}

def geo_country_for_ip(ip):
 ip=str(ip or '').strip()
 try:ipaddress.ip_address(ip)
 except ValueError:raise RuntimeError('GEO_IP_INVALID')
 r=curl('https://ipwho.is/'+ip,'',seconds=10,size=65536)
 if r.get('exit')!=0 or r.get('code')!='200':raise RuntimeError('GEO_LOOKUP_FAIL')
 try:j=json.loads(r.get('body') or '{}')
 except ValueError:raise RuntimeError('GEO_LOOKUP_INVALID')
 cc=str(j.get('country_code') or '').upper()
 if not j.get('success',True) or not re.fullmatch(r'[A-Z]{2}',cc):raise RuntimeError('GEO_LOOKUP_INVALID')
 return cc

def node_udp_preflight():
 probe_script=ROOT/'gateway'/'socks_udp_probe.py'
 if not probe_script.is_file():raise RuntimeError('NODE_UDP_PROBE_MISSING')
 py=dep_path('python') or sys.executable
 r=native([py,str(probe_script),str(PORTS['NODE']),'127.0.0.1'],18)
 if r.get('exit')!=0:raise RuntimeError('NODE_UDP_PREFLIGHT_FAIL')
 try:j=json.loads(r.get('out') or '{}')
 except ValueError:raise RuntimeError('NODE_UDP_PREFLIGHT_INVALID')
 if str(j.get('status') or '')!='PASS':raise RuntimeError('NODE_UDP_PREFLIGHT_FAIL')
 return {'ok':True,'country':geo_country_for_ip(j.get('udp_public_ip')),'seconds':j.get('seconds')}

def _node_system_preflight(auto_select=False):
 s=node_store();target=country_target();pre=owned('NODE');pre_id=str((pre or {}).get('nodeId') or '')
 if auto_select:
  h=ensure_node(target)
  n=node_selected()
  if not n:raise RuntimeError('NODE_NOT_SELECTED')
 else:
  n=node_selected(s)
  if not n:raise ValueError('NODE_NOT_SELECTED')
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:raise ValueError('NODE_ACTIVE_STOP_FIRST')
  h=ensure('NODE');node_record_test(n['id'],h)
 tcp_country=str(h.get('country') or '').upper()
 if not h.get('healthy'):raise RuntimeError(h.get('error') or 'PATH_NOT_VERIFIED_NODE')
 if target!='AUTO' and tcp_country!=target:raise RuntimeError('NODE_TCP_COUNTRY_MISMATCH')
 post=owned('NODE');post_id=str((post or {}).get('nodeId') or '')
 temporary=(not pre) or (pre_id!=post_id)
 try:
  udp=node_udp_preflight()
  if target!='AUTO' and str(udp.get('country') or '').upper()!=target:raise RuntimeError('NODE_UDP_COUNTRY_MISMATCH')
  perf=path_speed('NODE',1000000,250000)
  if perf.get('ok') is True:
   node_record_performance(n['id'],perf);shown=dict(perf)
  else:
   shown=dict(perf);shown['ok']=False;shown['downloadMbps']=None;shown['uploadMbps']=None;shown['error']=str(perf.get('error') or 'THROUGHPUT_SAMPLE_INCOMPLETE')
   node_record_performance(n['id'],shown)
  return {'mode':'NODE','provider':'NODE','path':'AUTO_NODE_SYSTEM_PREFLIGHT' if auto_select else 'SELECTED_NODE_SYSTEM_PREFLIGHT','systemEligible':True,'ok':bool(shown.get('ok')),
   'pingMs':shown.get('pingMs'),'downloadMbps':shown.get('downloadMbps'),'uploadMbps':shown.get('uploadMbps'),
   'country':tcp_country,'udpCountry':str(udp.get('country') or ''),'checked':now(),'error':str(shown.get('error') or ''),
   'selected':n['id'],'temporary':temporary,'selectionPolicy':'AUTO' if auto_select else 'SELECTED'}
 finally:
  if temporary:
   with contextlib.suppress(Exception):stop('NODE')

def node_system_preflight():
 return _node_system_preflight(False)

def node_system_preflight_auto():
 return _node_system_preflight(True)
def console_preflight_speed():
 progress('Console provider pre-connect benchmark','CONSOLE');t=test_timeouts()
 runtime=ROOT/'gateway'/'runtime';owner_path=runtime/'console-provider-owner.json'
 local_provider=runtime/'local_provider.json';console_profile=runtime/'console.profile.json'
 if not local_provider.is_file():
  if console_profile.is_file():raise ValueError('CONSOLE_PROFILE_PREFLIGHT_UNAVAILABLE')
  raise ValueError('CONSOLE_ROUTE_NOT_CONFIGURED')
 provider_script=ROOT/'gateway'/'console_provider.ps1'
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh or not pathlib.Path(pwsh).is_file():raise ValueError('DEPENDENCY_NOT_CONFIGURED_PWSH')
 if not provider_script.is_file():raise RuntimeError('CONSOLE_PROVIDER_SCRIPT_MISSING')
 preexisting=bool(read(owner_path,{}) or {})
 start_result=runtime/f'console-preflight-start-{uuid.uuid4().hex}.json'
 stop_result=runtime/f'console-preflight-stop-{uuid.uuid4().hex}.json'
 started_by_us=False
 try:
  rr=native([pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(provider_script),'-Action','Start','-ListenAddress','127.0.0.1','-ResultPath',str(start_result)],130)
  rec=read(start_result,{}) or {}
  if rr.get('exit')!=0 or str(rec.get('status') or '')!='PASS':raise RuntimeError(str(rec.get('error') or 'CONSOLE_PREFLIGHT_PROVIDER_START_FAILED'))
  owner=read(owner_path,{}) or {}
  if not owner:raise RuntimeError('CONSOLE_PROVIDER_OWNER_MISSING')
  started_by_us=not preexisting
  host=str(owner.get('listen') or '127.0.0.1');port=int(owner.get('port') or 0)
  if not host or not (1024<=port<=65535):raise RuntimeError('CONSOLE_PROVIDER_ENDPOINT_INVALID')
  proxy=f'socks5h://{host}:{port}'
  trace_r=curl('https://www.cloudflare.com/cdn-cgi/trace',proxy,seconds=t['ping']);tr=trace(trace_r.get('body',''))
  ping_r=curl('https://www.youtube.com/generate_204',proxy,seconds=t['ping'],body=False)
  if trace_r.get('exit')!=0 or trace_r.get('code')!='200' or not tr or ping_r.get('exit')!=0 or ping_r.get('code')!='204':raise RuntimeError('CONSOLE_PREFLIGHT_VERIFICATION_FAILED')
  if str(tr.get('loc') or '').upper()!='DE':raise RuntimeError('CONSOLE_PREFLIGHT_COUNTRY_MISMATCH')
  down=curl('https://speed.cloudflare.com/__down?bytes=1500000',proxy,seconds=t['download'],body=False,size=1565536)
  up=cloudflare_upload(350000,t['upload'],proxy)
  down_ok=down.get('exit')==0 and down.get('code')=='200' and down.get('bytes')==1500000
  up_ok=up.get('exit')==0 and up.get('code')=='200' and up.get('bytes')==350000
  return {'mode':'CONSOLE_PREFLIGHT','path':'CONSOLE_PROVIDER_PRECONNECT','ok':bool(down_ok and up_ok),'pingMs':round(float(ping_r.get('seconds',0))*1000,1),'pingType':'HTTPS_RTT','downloadMbps':round(float(down.get('bps',0))*8/1e6,2),'uploadMbps':round(float(up.get('bps',0))*8/1e6,2),'downloadSampleBytes':down.get('bytes',0),'uploadSampleBytes':up.get('bytes',0),'country':tr.get('loc',''),'exitIp':tr.get('ip',''),'checked':now(),'providerKind':'LOCAL_MIHOMO','temporary':started_by_us,'error':'' if (down_ok and up_ok) else 'THROUGHPUT_SAMPLE_INCOMPLETE'}
 finally:
  with contextlib.suppress(Exception):start_result.unlink(missing_ok=True)
  if started_by_us:
   with contextlib.suppress(Exception):native([pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(provider_script),'-Action','Stop','-ResultPath',str(stop_result)],20)
  with contextlib.suppress(Exception):stop_result.unlink(missing_ok=True)

def console_speed():
 t=test_timeouts();owner=read(ROOT/'gateway'/'runtime'/'wsl-console-owner.json',{}) or {}
 if not owner:raise RuntimeError('CONSOLE_CONNECT_FIRST')
 if str(owner.get('providerKind') or '')!='LOCAL_MIHOMO':raise RuntimeError('CONSOLE_SPEED_PROFILE_PATH_UNAVAILABLE')
 host=str(owner.get('hostIp') or '');port=int(owner.get('providerPort') or 0)
 if not host or not (1024<=port<=65535):raise RuntimeError('CONSOLE_PROVIDER_ENDPOINT_INVALID')
 proxy=f'socks5h://{host}:{port}'
 trace_r=curl('https://www.cloudflare.com/cdn-cgi/trace',proxy,seconds=t['ping']);tr=trace(trace_r.get('body',''))
 ping_r=curl('https://www.youtube.com/generate_204',proxy,seconds=t['ping'],body=False)
 if trace_r.get('exit')!=0 or trace_r.get('code')!='200' or not tr or ping_r.get('exit')!=0 or ping_r.get('code')!='204':raise RuntimeError('CONSOLE_SPEED_VERIFICATION_FAILED')
 expected=str(owner.get('country') or '').upper()
 if expected and str(tr.get('loc') or '').upper()!=expected:raise RuntimeError('CONSOLE_COUNTRY_MISMATCH')
 down=curl('https://speed.cloudflare.com/__down?bytes=1500000',proxy,seconds=t['download'],body=False,size=1565536)
 up=cloudflare_upload(350000,t['upload'],proxy)
 return {'mode':'CONSOLE','path':'CONSOLE_PROVIDER_OUTBOUND','ok':bool(down.get('exit')==0 and down.get('code')=='200' and up.get('exit')==0 and up.get('code')=='200'),
  'pingMs':round(float(ping_r.get('seconds',0))*1000,1),'pingType':'HTTPS_RTT','downloadMbps':round(float(down.get('bps',0))*8/1e6,2),
  'uploadMbps':round(float(up.get('bps',0))*8/1e6,2),'country':tr.get('loc',''),'exitIp':tr.get('ip',''),'checked':now(),'providerKind':'LOCAL_MIHOMO'}

def node_record_performance(node_id,perf):
 s=node_store()
 for n in s['nodes']:
  if n.get('id')==node_id:
   rec={k:perf.get(k) for k in ('ok','pingMs','pingType','downloadMbps','uploadMbps','country','checked','error')}
   n['performance_test']=rec
   hist=list(n.get('performance_history') or []);hist.append(rec);n['performance_history']=hist[-12:]
   break
 save_node_store(s)

def update_release():
 ctx=root_network_context()
 r=root_curl('https://api.github.com/repos/GOD13emad/FreeNetHub/releases/latest',seconds=12,size=1048576,ctx=ctx)
 if r.get('exit')!=0 or r.get('code')!='200':raise RuntimeError('UPDATE_GITHUB_UNREACHABLE')
 try:j=json.loads(r.get('body',''))
 except ValueError as ex:raise RuntimeError('UPDATE_RESPONSE_INVALID') from ex
 assets=[a for a in (j.get('assets') or []) if isinstance(a,dict) and str(a.get('name','')).lower().endswith('_setup.exe') and str(a.get('name','')).startswith('FreeNetHub_')]
 ranked=[]
 for a in assets:
  m=re.search(r'(?i)(?:^|[-_])r(\d+)(?:[-_]|$)',str(a.get('name','')))
  if m:ranked.append((int(m.group(1)),a))
 asset=max(ranked,key=lambda x:x[0])[1] if ranked else (assets[0] if assets else None)
 release=read(ROOT/'RELEASE.json',{}) or {}
 manifest=read(ROOT/'app'/'manifest.json',{}) or {}
 local_rev=str(release.get('releaseRevision') or manifest.get('coreVersion') or '')
 lm=re.search(r'(?i)(?:^|[-_])r(\d+)(?:[-_]|$)',local_rev)
 rm=re.search(r'(?i)(?:^|[-_])r(\d+)(?:[-_]|$)',str(asset.get('name','')) if asset else '')
 local_n=int(lm.group(1)) if lm else 0;remote_n=int(rm.group(1)) if rm else 0
 revision_comparable=bool(local_n>0 and remote_n>0)
 update_available=bool(asset and revision_comparable and remote_n>local_n)
 return {'tag':str(j.get('tag_name') or ''),'name':str(j.get('name') or ''),'published':j.get('published_at'),'htmlUrl':j.get('html_url'),
         'currentRevision':local_rev,'currentRevisionNumber':local_n,'remoteRevisionNumber':remote_n,'revisionComparable':revision_comparable,'updateAvailable':update_available,
         'asset':({'name':asset.get('name'),'url':asset.get('browser_download_url'),'bytes':asset.get('size'),'digest':asset.get('digest')} if asset else None),'rootPath':root_network_public(ctx)}

def update_download():
 rel=update_release();a=rel.get('asset')
 if not a or not a.get('url'):raise RuntimeError('UPDATE_INSTALLER_ASSET_MISSING')
 if not rel.get('updateAvailable'):raise RuntimeError('UPDATE_NOT_NEWER_THAN_CURRENT')
 dg=str(a.get('digest') or '')
 if not dg.lower().startswith('sha256:') or not re.fullmatch(r'[0-9a-fA-F]{64}',dg.split(':',1)[1]):raise RuntimeError('UPDATE_SHA256_METADATA_MISSING')
 expected=dg.split(':',1)[1].upper()
 tag=re.sub(r'[^A-Za-z0-9._-]','_',rel.get('tag') or 'latest')[:80]
 outdir=ROOT/'updates'/tag;outdir.mkdir(parents=True,exist_ok=True);dest=outdir/pathlib.Path(str(a['name'])).name
 ctx=root_network_context()
 args=['curl.exe','-q','-4','-L','--fail','--connect-timeout','5','--max-time','240','--noproxy','*']
 if ctx.get('interface'):args+=['--interface',str(ctx['interface'])]
 args+=['-o',str(dest),str(a['url'])]
 rr=native(args,250)
 if rr.get('exit')!=0 or not dest.is_file():raise RuntimeError('UPDATE_DOWNLOAD_FAILED')
 actual=digest(dest)
 if actual!=expected:
  with contextlib.suppress(Exception):dest.unlink()
  raise RuntimeError('UPDATE_HASH_MISMATCH')
 return {'tag':rel.get('tag'),'name':rel.get('name'),'published':rel.get('published'),'installer':str(dest),'sha256':actual,'bytes':dest.stat().st_size,'verified':True,'rootPath':root_network_public(ctx)}

def direct_speed():
 progress('Direct test · verifying physical default route','DIRECT');t=test_timeouts()
 route=direct_route()
 if not route.get('trustedPhysical'):raise RuntimeError('DIRECT_SPEED_NON_PHYSICAL_DEFAULT_ROUTE')
 progress('Direct test · verifying HTTPS exit','DIRECT')
 a=curl('https://www.cloudflare.com/cdn-cgi/trace','',seconds=t['ping']);tr=trace(a.get('body',''))
 if a.get('exit')!=0 or a.get('code')!='200' or not tr:raise RuntimeError('DIRECT_SPEED_TRACE_FAILED')
 if str(tr.get('warp','')).lower()=='on' or str(tr.get('gateway','')).lower()=='on':raise RuntimeError('DIRECT_SPEED_SYSTEM_TUNNEL_DETECTED')
 progress('Direct test · measuring Ping','DIRECT')
 ping=ping_direct(t['ping'])
 progress('Direct test · measuring Download','DIRECT')
 down=curl('https://speed.cloudflare.com/__down?bytes=5000000','',seconds=t['download'],body=False,size=5100000)
 progress('Direct test · measuring Upload','DIRECT')
 up=cloudflare_upload(1000000,t['upload'])
 down_ok=down.get('exit')==0 and down.get('code')=='200' and down.get('bytes')==5000000
 up_ok=up.get('exit')==0 and up.get('code')=='200' and up.get('bytes')==1000000
 return {'mode':'DIRECT','path':'DIRECT_HOST_INTERNET','ok':bool(down_ok and up_ok),'proxyUsed':False,'freeNetHubBrowserProxyUsed':False,'defaultRoute':route,'exitIp':tr.get('ip',''),'country':tr.get('loc',''),'cloudflareWarp':tr.get('warp',''),'cloudflareGateway':tr.get('gateway',''),'httpsLatencyMs':round(float(a.get('seconds',0))*1000,1),'pingMs':ping.get('avgMs'),'downloadMbps':round(float(down.get('bps',0))*8/1e6,2),'uploadMbps':round(float(up.get('bps',0))*8/1e6,2),'downloadSampleBytes':down.get('bytes',0),'uploadSampleBytes':up.get('bytes',0),'downloadSeconds':down.get('seconds'),'uploadSeconds':up.get('seconds'),'pathProof':'NO_PROXY_ENV+--noproxy_*+PHYSICAL_DEFAULT_ROUTE+NO_BROAD_OVERRIDE_ROUTES+CF_WARP_OFF','note':'Direct host Internet sample; FreeNetHub browser proxy is bypassed. Fails closed if the default route is not a physical adapter or Cloudflare reports WARP/Gateway on.'}

def direct_adapter_snapshot(route):
 pwsh=dep_path('pwsh') or shutil.which('pwsh.exe') or shutil.which('pwsh')
 if not pwsh:return {'available':False,'error':'PWSH_UNAVAILABLE'}
 try:idx=int(route.get('ifIndex'))
 except (TypeError,ValueError):return {'available':False,'error':'INTERFACE_INDEX_INVALID'}
 script=f"$i={idx};$a=Get-NetAdapter -InterfaceIndex $i -IncludeHidden -ErrorAction SilentlyContinue;$s=if($a){{Get-NetAdapterStatistics -Name $a.Name -ErrorAction SilentlyContinue}}else{{$null}};$b=if($a){{Get-NetAdapterBinding -Name $a.Name -ComponentID 'ms_tcpip6' -ErrorAction SilentlyContinue}}else{{$null}};$v6=@(Get-NetRoute -AddressFamily IPv6 -DestinationPrefix '::/0' -ErrorAction SilentlyContinue);$dns=@((Get-DnsClientServerAddress -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses);[pscustomobject]@{{available=[bool]$a;name=$a.Name;description=$a.InterfaceDescription;status=[string]$a.Status;linkSpeed=[string]$a.LinkSpeed;driverVersion=[string]$a.DriverVersion;driverDate=[string]$a.DriverDate;receivedPacketErrors=$(if($s){{$s.ReceivedPacketErrors}}else{{$null}});outboundPacketErrors=$(if($s){{$s.OutboundPacketErrors}}else{{$null}});receivedDiscardedPackets=$(if($s){{$s.ReceivedDiscardedPackets}}else{{$null}});outboundDiscardedPackets=$(if($s){{$s.OutboundDiscardedPackets}}else{{$null}});ipv6BindingEnabled=$(if($b){{[bool]$b.Enabled}}else{{$null}});ipv6DefaultRoutes=$v6.Count;dnsServers=$dns}}|ConvertTo-Json -Compress -Depth 4"
 try:rr=native([pwsh,'-NoProfile','-Command',script],8)
 except TimeoutError:return {'available':False,'error':'ADAPTER_SNAPSHOT_TIMEOUT'}
 if rr.get('exit')!=0:return {'available':False,'error':'ADAPTER_SNAPSHOT_FAILED'}
 try:return json.loads(rr.get('out') or '{}')
 except (TypeError,ValueError):return {'available':False,'error':'ADAPTER_SNAPSHOT_INVALID'}

def direct_network_audit():
 progress('Direct network / CGNAT audit: no FreeNetHub proxy or tunnel','DIRECT')
 route=direct_route()
 if not route.get('trustedPhysical'):raise RuntimeError('DIRECT_AUDIT_NON_PHYSICAL_DEFAULT_ROUTE')
 local_ip=str(route.get('ip') or '');gateway=str(route.get('nextHop') or '')
 try:
  ipaddress.ip_address(local_ip);ipaddress.ip_address(gateway)
 except ValueError as ex:raise RuntimeError('DIRECT_AUDIT_ROUTE_INVALID') from ex
 nat=DN.audit(local_ip,gateway)
 dns_probe=DN.dns_interception_probe('www.youtube.com')
 adapter=direct_adapter_snapshot(route)
 checks={}
 targets={
  'openai':'https://api.openai.com/v1/models',
  'github':'https://github.com/',
  'google':'https://www.google.com/generate_204',
  'youtube':'https://www.youtube.com/generate_204',
 }
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  fs={name:ex.submit(curl,url,'',6,False,65536) for name,url in targets.items()}
  for name,f in fs.items():
   try:r=f.result()
   except Exception as exc:r={'exit':1,'code':'000','seconds':None,'fetchPath':'','error':str(exc)}
   http_code=str(r.get('code') or '000')
   reached=bool(http_code!='000' and (r.get('exit')==0 or (r.get('exit')==63 and http_code[0] in '12345')))
   checks[name]={'reachable':reached,'httpCode':http_code,'seconds':r.get('seconds'),'fetchPath':r.get('fetchPath'),'error':str(r.get('error') or '')[:300]}
 trace_r=curl('https://www.cloudflare.com/cdn-cgi/trace','',6,True,65536);tr=trace(trace_r.get('body',''))
 route_after=direct_route()
 stable=bool(route_after.get('trustedPhysical') and route_after.get('ifIndex')==route.get('ifIndex') and route_after.get('nextHop')==route.get('nextHop') and route_after.get('ip')==route.get('ip'))
 if not stable:raise RuntimeError('DIRECT_AUDIT_ROUTE_CHANGED')
 recommendations=[]
 if nat.get('cgnatConfirmed'):recommendations.append('CGNAT upstream cannot be removed by Windows; static inbound requires ISP public IPv4, native IPv6, or working upstream port control.')
 if dns_probe.get('interceptionConfirmed'):recommendations.append('Non-global system DNS answer detected while validated encrypted DNS returned public addresses.')
 if nat.get('udpTraversalCandidate'):recommendations.append('STUN mapping is stable and source-port preserving; UDP peer traversal is a strong candidate.')
 pc=nat.get('portControl') or {}
 if not (pc.get('pcp',{}).get('supported') or pc.get('natPmp',{}).get('supported')):recommendations.append('PCP/NAT-PMP is unavailable on the CPE path; do not rely on automatic upstream static port mapping.')
 if adapter.get('ipv6BindingEnabled') is False:recommendations.append('IPv6 is disabled on the physical adapter; enable the IPv6 binding with administrator rights before judging ISP/router IPv6 availability.')
 elif int(adapter.get('ipv6DefaultRoutes') or 0)==0:recommendations.append('IPv6 binding is enabled but no native IPv6 default route was learned; router/ISP IPv6 remains unavailable or unconfigured.')
 if checks.get('youtube',{}).get('reachable') is False and checks.get('google',{}).get('reachable') and checks.get('openai',{}).get('reachable'):recommendations.append('Destination-specific filtering/DPI is suspected; local DNS/MTU/NIC mutation is not justified by this audit.')
 out={'schema':1,'checked':now(),'status':'PASS_READ_ONLY','mode':'DIRECT','proxyUsed':False,'tunnelUsed':False,'routeStable':stable,'defaultRoute':route,'adapter':adapter,'nat':nat,'dns':dns_probe,'publicTrace':{'ip':tr.get('ip',''),'country':tr.get('loc',''),'warp':tr.get('warp',''),'gateway':tr.get('gateway',''),'reachable':bool(trace_r.get('exit')==0 and trace_r.get('code')=='200')},'applicationChecks':checks,'recommendations':recommendations,'mutationsApplied':[],'pathProof':'NO_FREENETHUB_PROXY+PHYSICAL_DEFAULT_ROUTE+NO_BROAD_OVERRIDE_ROUTES+ROUTE_STABLE'}
 write(ROOT/'data'/'direct_network_audit.json',out)
 return out

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
 expected={k:r[k] for k in ('pid','path','created')}
 cur=identity(r['pid'])
 if not cur or cur!=expected:return False
 k=C.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE;k.TerminateProcess.argtypes=[W.HANDLE,W.UINT];k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];k.CloseHandle.argtypes=[W.HANDLE]
 h=k.OpenProcess(0x1|0x100000,False,r['pid'])
 if not h:
  # Benign lifecycle race: the exact owned process may have exited after the
  # identity check. Never reinterpret a reused PID as our process.
  if identity(r['pid'])!=expected:return False
  raise OSError('OWNED_PROCESS_ACCESS_DENIED')
 try:
  # WAIT_TIMEOUT (258) means still running. A signalled handle is already dead.
  if k.WaitForSingleObject(h,0)!=258:return False
  if not k.TerminateProcess(h,0):
   # TerminateProcess can lose a race with a process already entering shutdown.
   # Give that exact handle a bounded grace period; never act on a reused PID.
   if k.WaitForSingleObject(h,2000)!=258 or identity(r['pid'])!=expected:return False
   raise OSError('OWNED_PROCESS_STOP_FAILED')
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
  if str(n.get('protocol') or '').lower()=='naive' and not singbox_naive_ready(exe):
   raise ValueError('DEPENDENCY_NOT_CONFIGURED_CRONET')
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
  end=min(DEADLINE,time.monotonic()+(100 if scan else 30 if mode=='NODE' else 65 if mode in ('WARP','GOOL') else 110));grace=time.monotonic()+5;node_bad_probes=0
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
    if mode=='NODE' and h['error']!='LOCAL_PROXY_UNREACHABLE':
     node_bad_probes+=1
     if node_bad_probes>=2:break
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
 out=list(configured_bridge_modes())
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
  if mode in BRIDGE_MODES and not o and installed:
   if not f.exists():state='MISSING_PRIVATE_BRIDGES'
   elif not bridge_configured(mode):state='INVALID_PRIVATE_BRIDGES'
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
  if 'NODE' in candidates:
   try:node_refresh_public(False)
   except (ValueError,RuntimeError,TimeoutError):pass
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
 if action=='ConnectProvider':
  # Internal capability-specific connection path. It deliberately ignores the
  # global country selector for providers that do not support country targeting.
  if mode not in ('WARP','GOOL','TOR','WEBTUNNEL','OBFS4'):raise ValueError('PROVIDER_CONNECT_MODE_UNSUPPORTED')
  h=ensure(mode)
  if h.get('healthy'):
   write(ROOT/'session.json',h);return h
  raise RuntimeError(h.get('error') or ('PATH_NOT_VERIFIED_'+mode))
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
   for m in tuple(('NODE','WARP','GOOL','CFON','TOR'))+tuple(configured_bridge_modes()):
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
 if action=='DirectNetworkAudit':
  return direct_network_audit()
 if action=='PathSpeed':
  return path_speed(mode)
 if action=='ProviderBenchmark':
  if mode=='DIRECT':return {'provider':'DIRECT','health':probe('DIRECT'),'performance':direct_speed(),'temporary':False}
  if mode=='CUSTOM':return {'provider':'CUSTOM','health':probe('CUSTOM'),'performance':path_speed('CUSTOM'),'temporary':False}
  if mode=='AUTO':
   attempts=[];rows=[];eligible=list(connect_candidates('AUTO'))
   for m in smart_benchmark_candidates():
    check();progress('Smart benchmark: '+m,m)
    was=bool(owned(m)) if m in PORTS else False
    try:
     if m=='DIRECT':
      h=probe('DIRECT');perf=direct_speed()
     elif m=='CUSTOM':
      h=probe('CUSTOM')
      if not h.get('healthy'):raise RuntimeError(h.get('error') or 'CUSTOM_PATH_NOT_VERIFIED')
      perf=path_speed('CUSTOM')
     elif m=='NODE':
      h=ensure_node(country_target());perf=path_speed('NODE')
      n=node_selected()
      if n:node_record_performance(n['id'],perf)
     else:
      h=ensure(m);perf=path_speed(m)
     row={'provider':m,'ok':bool(perf.get('ok')),'health':h,'performance':perf,'temporary':bool(m in PORTS and not was)}
     if m=='NODE':
      n=node_selected()
      if n:row['node']=NH.public_node(n)
     rows.append(row)
    except (ValueError,RuntimeError,TimeoutError) as ex:
     attempts.append({'mode':m,'reason':str(ex)})
     rows.append({'provider':m,'ok':False,'performance':None,'error':str(ex),'temporary':bool(m in PORTS and not was)})
    finally:
     if m in PORTS and not was:
      with contextlib.suppress(Exception):stop(m)
   good=[x for x in rows if x.get('provider') in eligible and isinstance(x.get('performance'),dict) and x['performance'].get('ok')]
   ranked=sorted(good,key=lambda x:performance_rank_key(x.get('performance')))
   rank=[x['provider'] for x in ranked]
   if rank:
    s=settings();old=[x for x in s.get('order',[]) if x in PORTS]
    s['order']=rank+[x for x in old if x not in rank]+[x for x in DEFAULT['order'] if x not in rank and x not in old]
    write(ROOT/'settings.json',s)
    best=ranked[0]
    return {'provider':best['provider'],'health':best.get('health') or {},'performance':best['performance'],'temporary':bool(best.get('temporary')),'results':rows,'rank':rank,'attempts':attempts,'selectionPolicy':'LOWEST_PING_THEN_DOWNLOAD_UPLOAD'}
   return {'provider':'','health':{},'performance':None,'temporary':False,'results':rows,'rank':[],'attempts':attempts,'error':'ALL_SMART_PATHS_FAILED','selectionPolicy':'LOWEST_PING_THEN_DOWNLOAD_UPLOAD'}
  if mode not in PORTS:raise ValueError('SPEED_MODE_UNSUPPORTED')
  was=bool(owned(mode))
  try:
   h=ensure_node(country_target()) if mode=='NODE' else ensure(mode)
   perf=path_speed(mode)
   out={'provider':mode,'health':h,'performance':perf,'temporary':not was}
   if mode=='NODE':
    n=node_selected()
    if n:
     node_record_performance(n['id'],perf)
     out['node']=NH.public_node(node_selected() or n)
   return out
  finally:
   if not was:
    with contextlib.suppress(Exception):stop(mode)
 if action=='ProviderPing':
  t=test_timeouts()
  def _provider_ping_one(m):
   m=str(m or 'AUTO').upper()
   if m=='DIRECT':
    q=ping_direct(t['ping'])
    return {'provider':'DIRECT','performance':{'mode':'DIRECT','ok':bool(q.get('ok')),'pingMs':q.get('avgMs'),'downloadMbps':None,'uploadMbps':None,'country':'','checked':now()}}
   was=bool(owned(m)) if m in PORTS else False
   try:
    if m=='CUSTOM':
     proxy=mode_proxy('CUSTOM')
    else:
     ensure_node(country_target()) if m=='NODE' else ensure(m)
     proxy=mode_proxy(m)
    pr=curl('https://www.youtube.com/generate_204',proxy,seconds=t['ping'],body=False)
    trr=curl('https://www.cloudflare.com/cdn-cgi/trace',proxy,seconds=t['ping'])
    tr=trace(trr.get('body','')) if trr.get('exit')==0 and trr.get('code')=='200' else {}
    ok=pr.get('exit')==0 and pr.get('code')=='204'
    return {'provider':m,'performance':{'mode':m,'ok':ok,'pingMs':round(float(pr.get('seconds',0))*1000,1) if ok else None,'downloadMbps':None,'uploadMbps':None,'country':tr.get('loc',''),'checked':now()}}
   finally:
    if m in PORTS and not was:
     with contextlib.suppress(Exception):stop(m)
  if mode=='AUTO':
   attempts=[];rows=[];eligible=list(connect_candidates('AUTO'))
   for m in smart_benchmark_candidates():
    check();progress('Smart ping: '+m,m)
    try:
     row=_provider_ping_one(m);rows.append(row)
    except (ValueError,RuntimeError,TimeoutError) as ex:
     attempts.append({'mode':m,'reason':str(ex)});rows.append({'provider':m,'performance':None,'error':str(ex)})
   good=[x for x in rows if x.get('provider') in eligible and isinstance(x.get('performance'),dict) and x['performance'].get('ok')]
   ranked=sorted(good,key=lambda x:performance_rank_key(x.get('performance')))
   if ranked:
    best=ranked[0]
    return {'provider':best['provider'],'performance':best['performance'],'results':rows,'rank':[x['provider'] for x in ranked],'attempts':attempts}
   return {'provider':'','performance':None,'results':rows,'rank':[],'attempts':attempts,'error':'ALL_SMART_PATHS_FAILED'}
  if mode not in tuple(PORTS)+('CUSTOM','DIRECT'):raise ValueError('PING_MODE_UNSUPPORTED')
  return _provider_ping_one(mode)
 if action=='SystemSpeed':
  return system_speed(mode)
 if action=='NodeSystemPreflight':
  return node_system_preflight()
 if action=='NodeSystemPreflightAuto':
  return node_system_preflight_auto()
 if action=='ConsoleSpeed':
  return console_speed()
 if action=='ConsolePreflight':
  return console_preflight_speed()
 if action=='Providers':
  return {'providers':[
   {'id':'AUTO','label':'Smart','country':True,'list':False,'browser':True,'system':True,'console':False,'speed':True},
   {'id':'NODE','label':'Node Pool','country':True,'list':True,'browser':True,'system':True,'console':False,'speed':True},
   {'id':'CFON','label':'CFON','country':True,'list':False,'browser':True,'system':False,'console':False,'speed':True},
   {'id':'WARP','label':'WARP','country':False,'list':False,'browser':True,'system':True,'console':False,'speed':True},
   {'id':'GOOL','label':'GOOL','country':False,'list':False,'browser':True,'system':False,'console':False,'speed':True},
   {'id':'TOR','label':'Tor / Snowflake','country':False,'list':False,'browser':True,'system':False,'console':False,'speed':True},
   {'id':'WEBTUNNEL','label':'WebTunnel','country':False,'list':False,'browser':True,'system':False,'console':False,'speed':True,'configured':bridge_configured('WEBTUNNEL')},
   {'id':'OBFS4','label':'obfs4','country':False,'list':False,'browser':True,'system':False,'console':False,'speed':True,'configured':bridge_configured('OBFS4')},
   {'id':'CUSTOM','label':'Custom Proxy','country':'verify','list':False,'browser':True,'system':False,'console':False,'speed':True},
   {'id':'DIRECT','label':'Direct','country':'observed','list':False,'browser':True,'system':False,'console':False,'speed':True}
  ]}
 if action=='UpdateCheck':
  return update_release()
 if action=='UpdateDownload':
  return update_download()
 if action=='Doctor':return diagnostics()
 if action=='Import':
  if mode not in ('WEBTUNNEL','OBFS4'):raise ValueError('INVALID_IMPORT_MODE')
  f=pathlib.Path(payload)
  temporary=(f.parent.resolve()==(ROOT/'jobs').resolve() and f.name.startswith('bridge-import-'))
  try:
   if not f.is_file() or f.stat().st_size>65536:raise ValueError('BRIDGE_FILE_TOO_LARGE')
   lines=bridge_lines(f.read_text(encoding='utf-8-sig'),mode.lower())
   if not lines:raise ValueError('NO_BRIDGES')
   dest=ROOT/'data'/('bridges_'+mode.lower()+'.txt')
   if dest.exists():shutil.copyfile(dest,ROOT/'backup'/f'{mode}_{uuid.uuid4().hex}.txt')
   dest.write_text('\n'.join(lines)+'\n',encoding='utf8');return {'imported':len(lines),'connection':'NOT_TESTED','mode':mode}
  finally:
   if temporary:
    with contextlib.suppress(OSError):f.unlink()
 if action=='NodeList':
  s=node_store();st=public_refresh_state();age=public_refresh_age_seconds(st);return {'total':len(s['nodes']),'selected':s.get('selected'),'refresh':{'fresh':public_refresh_is_fresh(st,s),'ageSeconds':round(age,1) if age is not None else None,'ttlSeconds':PUBLIC_REFRESH_TTL_SECONDS,'sourceFamilies':sorted({family for _,family,__ in PUBLIC_NODE_SOURCES}),'sources':list(st.get('sources') or []),'failedSources':list(st.get('failedSources') or [])},'nodes':node_public_rows(s)}
 if action=='NodeRefreshSmart':
  return node_refresh_public(False)
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
  save_node_store(s);return {'id':str(payload),'favorite':bool(n.get('favorite')),'nodes':node_public_rows(s),'selected':s.get('selected'),'total':len(s['nodes'])}
 if action=='NodePin':
  s=node_store();found=False
  for n in s['nodes']:
   if n.get('id')==str(payload):n['pinned']=not bool(n.get('pinned'));found=True;break
  if not found:raise ValueError('NODE_NOT_FOUND')
  save_node_store(s);return {'id':str(payload),'pinned':bool(n.get('pinned')),'nodes':node_public_rows(s),'selected':s.get('selected'),'total':len(s['nodes'])}
 if action=='NodeMeta':
  f=pathlib.Path(payload);temporary=f.parent.resolve()==(ROOT/'jobs').resolve() and f.name.startswith('node-meta-')
  try:
   req=read(f,{}) or {};node_id=str(req.get('id') or '')
   name=str(req.get('name') or '').strip()[:120]
   note=str(req.get('note') or '').strip()[:500]
   tags=[str(x).strip()[:32] for x in (req.get('tags') or []) if str(x).strip()][:16]
   try:rating=int(req.get('rating') or 0)
   except (TypeError,ValueError):raise ValueError('NODE_RATING_INVALID')
   if rating<0 or rating>5:raise ValueError('NODE_RATING_INVALID')
   s=node_store();found=False
   for n in s['nodes']:
    if n.get('id')==node_id:
     if name:n['name']=name
     n['note']=note;n['tags']=tags;n['rating']=rating;found=True;break
   if not found:raise ValueError('NODE_NOT_FOUND')
   save_node_store(s);return {'id':node_id,'node':NH.public_node(n),'nodes':node_public_rows(s),'selected':s.get('selected'),'total':len(s['nodes'])}
  finally:
   if temporary:f.unlink(missing_ok=True)
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
  return node_refresh_public(True)
 if action=='ConnectSelectedNode':
  s=node_store();n=node_selected(s)
  if not n:raise ValueError('NODE_NOT_SELECTED')
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:raise ValueError('NODE_ACTIVE_STOP_FIRST')
  started_here=not bool(current)
  try:
   h=ensure('NODE')
   target=country_target();actual=str(h.get('country') or '').upper()
   if not h.get('healthy'):raise RuntimeError(h.get('error') or 'PATH_NOT_VERIFIED_NODE')
   if target!='AUTO' and actual!=target:raise RuntimeError('NODE_TCP_COUNTRY_MISMATCH')
   node_record_test(n['id'],h);write(ROOT/'session.json',h)
   return {'healthy':True,'selected':n['id'],'country':actual,'startedHere':started_here,'node':NH.public_node(node_selected() or n)}
  except Exception:
   if started_here:
    with contextlib.suppress(Exception):stop('NODE')
   raise
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
 if action=='NodeSpeed':
  s=node_store();n=node_selected(s)
  if not n:raise ValueError('NODE_NOT_SELECTED')
  current=owned('NODE')
  if current and current.get('nodeId')!=n['id']:raise ValueError('NODE_ACTIVE_STOP_FIRST')
  was=bool(current)
  try:
   h=ensure('NODE');node_record_test(n['id'],h)
   perf=path_speed('NODE');node_record_performance(n['id'],perf)
   return {'performance':perf,'node':NH.public_node(node_selected() or n),'temporary':not was}
  finally:
   if not was:
    with contextlib.suppress(Exception):stop('NODE')
 if action=='NodeBenchmarkBatch':
  s=node_store()
  if not s['nodes']:raise ValueError('NODE_POOL_EMPTY')
  if not node_endpoint_tests_fresh(s):node_batch_fast()
  s=node_store()
  protocol_attempts={}
  for n in s['nodes']:
   if isinstance(n.get('performance_test'),dict):
    proto=str(n.get('protocol') or '').lower();protocol_attempts[proto]=protocol_attempts.get(proto,0)+1
  ranked=[]
  for n in s['nodes']:
   ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else {}
   old=n.get('performance_test') if isinstance(n.get('performance_test'),dict) else {}
   proto=str(n.get('protocol','')).lower()
   eligible=(ep.get('reachable') is True or proto in NH.UDP_PREFLIGHT_PROTOCOLS)
   if eligible:ranked.append((0 if not old else 1,protocol_attempts.get(proto,0),node_source_quality(n),0 if n.get('pinned') else 1,0 if n.get('favorite') else 1,float(ep.get('latency_ms',999999) or 999999),n))
  rows=[];limit=4
  ordered=sorted(ranked,key=lambda x:x[:6]);picked=[];picked_ids=set();seen_protocols=set();seen_sources=set()
  for row in ordered:
   n=row[-1];proto=str(n.get('protocol') or '').lower()
   if proto not in seen_protocols:
    picked.append(row);picked_ids.add(n.get('id'));seen_protocols.add(proto);seen_sources.add(str(n.get('source') or 'UNKNOWN'))
    if len(picked)>=limit:break
  if len(picked)<limit:
   for row in ordered:
    n=row[-1];source=str(n.get('source') or 'UNKNOWN')
    if n.get('id') in picked_ids or source in seen_sources:continue
    picked.append(row);picked_ids.add(n.get('id'));seen_sources.add(source)
    if len(picked)>=limit:break
  if len(picked)<limit:
   for row in ordered:
    if row[-1].get('id') in picked_ids:continue
    picked.append(row);picked_ids.add(row[-1].get('id'))
    if len(picked)>=limit:break
  for _,__,___,____,_____,______,n in picked:
   check()
   current=owned('NODE')
   if current and current.get('nodeId')!=n['id']:stop('NODE')
   node_select(n['id'])
   try:
    h=ensure('NODE');node_record_test(n['id'],h)
    perf=path_speed('NODE',1000000,250000)
    if perf.get('ok') is True:
     node_record_performance(n['id'],perf)
     rows.append({'id':n['id'],'status':'PASS','ok':True,'pingMs':perf.get('pingMs'),'downloadMbps':perf.get('downloadMbps'),'uploadMbps':perf.get('uploadMbps'),'country':perf.get('country'),'error':''})
    else:
     fail=dict(perf);fail['ok']=False;fail['downloadMbps']=None;fail['uploadMbps']=None;fail['error']=str(perf.get('error') or 'THROUGHPUT_SAMPLE_INCOMPLETE')
     node_record_performance(n['id'],fail)
     rows.append({'id':n['id'],'status':'FAIL','ok':False,'pingMs':perf.get('pingMs'),'downloadMbps':None,'uploadMbps':None,'country':perf.get('country'),'error':fail['error']})
   except (ValueError,RuntimeError,TimeoutError) as ex:
    ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else {}
    fallback_ping=ep.get('latency_ms') if ep.get('reachable') is True else None
    fail={'ok':False,'pingMs':fallback_ping,'pingType':'TCP_CONNECT' if fallback_ping is not None else None,'downloadMbps':None,'uploadMbps':None,'country':'','checked':now(),'error':str(ex)}
    node_record_performance(n['id'],fail)
    rows.append({'id':n['id'],'status':'FAIL','ok':False,'pingMs':fallback_ping,'downloadMbps':None,'uploadMbps':None,'country':'','error':str(ex)})
   finally:
    with contextlib.suppress(Exception):stop('NODE')
  s=node_store()
  def bench_eligible(n):
   ep=n.get('endpoint_test') if isinstance(n.get('endpoint_test'),dict) else {}
   return ep.get('reachable') is True or str(n.get('protocol','')).lower() in NH.UDP_PREFLIGHT_PROTOCOLS
  remaining=sum(1 for n in s['nodes'] if bench_eligible(n) and not isinstance(n.get('performance_test'),dict))
  eligible_total=sum(1 for n in s['nodes'] if bench_eligible(n))
  passed=sum(1 for r in rows if r.get('ok') is True);failed=len(rows)-passed
  winners=[n for n in s['nodes'] if isinstance(n.get('performance_test'),dict) and n['performance_test'].get('ok') is True]
  best=min(winners,key=lambda n:performance_rank_key(n.get('performance_test'))) if winners else None
  best_public=({'id':best.get('id'),'performance':best.get('performance_test'),'node':NH.public_node(best)} if best else None)
  return {'benchmarked':len(rows),'passed':passed,'failed':failed,'eligible':eligible_total,'remainingUnbenchmarked':remaining,'results':rows,'best':best_public,'total':len(s['nodes']),'selected':s.get('selected'),'nodes':node_public_rows(s)}
 if action=='Export':return safe_export()
 if action=='Updates':
  rows=[]
  for repo in ('GOD13emad/FreeNetHub','bepass-org/warp-plus','SagerNet/sing-box','bepass-org/oblivion-desktop'):
   r=curl('https://api.github.com/repos/'+repo+'/releases/latest',seconds=8,size=1048576)
   try:
    j=json.loads(r['body']);rows.append({'project':repo,'latest':j['tag_name'],'published':j.get('published_at'),'assetCount':len(j.get('assets') or []),'action':'SELF_UPDATE_AVAILABLE' if repo=='GOD13emad/FreeNetHub' else 'CHECK_ONLY'})
   except (ValueError,KeyError):rows.append({'project':repo,'status':'UNREACHABLE'})
  return {'releases':rows,'selfUpdate':update_release(),'autoInstallation':False}
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
  record={'schema':1,'version':'4.0','job':JOB,'action':ns.action,'mode':ns.mode,'exit':code,'utc':now(),'result':result};write(result_file,record);write(ROOT/'last.json',record)
 return code
if __name__=='__main__':raise SystemExit(main())
