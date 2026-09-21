from pathlib import Path
import json, hashlib, argparse
R=Path(__file__).resolve().parent.parent
G=R/"gateway"
DEFAULT_PATH=G/"gateway_defaults.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def defaults():return json.loads(DEFAULT_PATH.read_text(encoding="utf-8-sig"))
def load_profile(path):
 p=Path(path);x=json.loads(p.read_text(encoding="utf-8-sig"))
 if x.get("kind")!="wireguard" or x.get("endpoint",{}).get("type")!="wireguard":raise ValueError("BAD_LOCAL_PROFILE")
 if x["endpoint"].get("tag")!="provider":raise ValueError("BAD_PROVIDER_TAG")
 return x
def socks_out(p):return {"type":"socks","tag":"provider","server":p["host"],"server_port":int(p["port"]),"version":"5"}
def build(mode,provider="WARP",profile_path=None):
 d=defaults();tun=d["tun"];console=d["console"]
 private={"ip_is_private":True,"action":"route","outbound":"direct"}
 selfproc={"process_name":["warp-plus.exe","sing-box.exe"],"action":"route","outbound":"direct"}
 rules=[private,selfproc];tun_in={"type":"tun","tag":"fnh-tun","interface_name":tun["interface_name"],"address":tun["address"],"mtu":tun["mtu"],"auto_route":True,"strict_route":True,"stack":"system","dns_mode":"disabled"}
 cfg={
  "log":{"level":"warn","timestamp":True},
  "inbounds":[tun_in],
  "outbounds":[{"type":"direct","tag":"direct"}],
  "route":{"rules":rules,"auto_detect_interface":True}
 }
 profile=None
 if profile_path:
  profile=load_profile(profile_path);cfg["endpoints"]=[profile["endpoint"]]
 else:
  p=d["providers"][provider];cfg["outbounds"].insert(0,socks_out(p))
  if provider in ("WARP","GOOL","CFON"):
   # Keep warp-plus underlay outside the default TUN. Without an OS-level route
   # exclusion its userspace WireGuard transport can be recaptured by the TUN,
   # which collapses the local SOCKS provider after a few seconds.
   tun_in["route_exclude_address"]=["162.159.192.0/24","162.159.193.0/24","162.159.197.0/24"]
 if mode=="PC_TUNNEL":
  cfg["route"]["final"]="provider"
  cfg["inbounds"][0]["dns_mode"]="hijack"
  cfg["dns"]={"servers":[{"type":"udp","tag":"dns-provider","server":"1.1.1.1","server_port":53,"detour":"provider"}],"final":"dns-provider"}
 elif mode=="CONSOLE_ONLY":
  cfg["route"]["rules"].append({"source_ip_cidr":[console["subnet"]],"action":"route","outbound":"provider"});cfg["route"]["final"]="direct"
 else:raise ValueError("BAD_MODE")
 return cfg,profile
def console_contract(provider,profile,target_country=None):
 d=defaults();reasons=[];country=(target_country or "").upper()
 if profile:
  c=profile.get("capabilities",{})
  if not c.get("tcp"):reasons.append("TCP_NOT_VERIFIED")
  if not c.get("udp"):reasons.append("UDP_NOT_VERIFIED")
  if not c.get("country_verified"):reasons.append("COUNTRY_NOT_RUNTIME_VERIFIED")
  if country and profile.get("country","").upper()!=country:reasons.append("COUNTRY_MISMATCH")
 else:
  p=d["providers"][provider]
  if p.get("udp") is not True:reasons.append("UDP_NOT_VERIFIED")
  if country:
   if not p.get("country_verified"):reasons.append("UDP_COUNTRY_NOT_VERIFIED")
   elif str(p.get("country","")).upper()!=country:reasons.append("COUNTRY_MISMATCH")
 return {"ready":not reasons,"reasons":reasons}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--mode",choices=["PC_TUNNEL","CONSOLE_ONLY"],required=True)
 ap.add_argument("--provider",default="WARP")
 ap.add_argument("--profile")
 ap.add_argument("--target-country",default="")
 ap.add_argument("--output",required=True)
 ap.add_argument("--allow-unverified-console",action="store_true")
 ns=ap.parse_args()
 cfg,profile=build(ns.mode,ns.provider,ns.profile)
 if ns.mode=="CONSOLE_ONLY" and not ns.allow_unverified_console:
  c=console_contract(ns.provider,profile,ns.target_country)
  if not c["ready"]:raise SystemExit("CONSOLE_PROVIDER_CONTRACT_FAILED:"+",".join(c["reasons"]))
 out=Path(ns.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"GENERATED","mode":ns.mode,"provider":profile["name"] if profile else ns.provider,"output":str(out),"sha256":sha(out)},indent=2))
if __name__=="__main__":main()
