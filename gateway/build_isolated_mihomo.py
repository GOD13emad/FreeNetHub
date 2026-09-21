from pathlib import Path
import yaml,json,argparse,hashlib,shutil,ipaddress
R=Path(__file__).resolve().parent.parent
OUTDIR=R/"gateway"/"runtime"
FLAGS={"DE":"🇩🇪","NL":"🇳🇱","US":"🇺🇸","GB":"🇬🇧"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
ap=argparse.ArgumentParser();ap.add_argument("--source-config",required=True);ap.add_argument("--country",choices=FLAGS,required=True);ap.add_argument("--port",type=int,default=19591);ap.add_argument("--controller",type=int,default=19592);ap.add_argument("--listen",default="127.0.0.1");ap.add_argument("--output",required=True)
ns=ap.parse_args()
try: ipaddress.ip_address(ns.listen)
except ValueError: raise SystemExit("BAD_LISTEN_IP")
SRC=Path(ns.source_config).expanduser().resolve()
if not SRC.is_file(): raise SystemExit("SOURCE_CONFIG_MISSING")
j=yaml.safe_load(SRC.read_text(encoding="utf-8-sig")) or {}
proxies=[x for x in (j.get("proxies") or []) if isinstance(x,dict)]
flag=FLAGS[ns.country]
cand=[x for x in proxies if str(x.get("name","")).startswith(flag) and x.get("udp") is True]
if not cand: raise SystemExit("NO_DIRECT_UDP_NODE_"+ns.country)
x=dict(cand[0]);name=x["name"]
cfg={
 "mixed-port":ns.port,"allow-lan":ns.listen!="127.0.0.1","bind-address":ns.listen,"mode":"rule","log-level":"warning","ipv6":True,
 "external-controller":f"127.0.0.1:{ns.controller}","secret":"",
 "profile":{"store-selected":False,"store-fake-ip":False},
 "proxies":[x],
 "proxy-groups":[{"name":"FNH_FIXED","type":"select","proxies":[name]}],
 "rules":["MATCH,FNH_FIXED"]
}
out=Path(ns.output);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),encoding="utf-8")
print(json.dumps({"status":"PASS","country":ns.country,"nodeName":name,"nodeType":x.get("type"),"udp":x.get("udp"),"sourceSha256":sha(SRC),"output":str(out),"outputSha256":sha(out)},ensure_ascii=True))
