from pathlib import Path
import json,base64,hashlib,ipaddress,re,socket
R=Path(__file__).resolve().parent.parent
src=R/"data"/"WARP"/"cache"/"primary"/"wgcf-identity.json"
out=R/"gateway"/"runtime"/"warp-native.profile.json"
if not src.is_file(): raise SystemExit("WARP_IDENTITY_MISSING")
j=json.loads(src.read_text(encoding="utf-8-sig"))
priv=str(j.get("private_key","")).strip()
if len(priv)!=44: raise SystemExit("WARP_PRIVATE_KEY_FORMAT")
cfg=j.get("config") or {}
peers=cfg.get("peers") or []
if not peers: raise SystemExit("WARP_PEER_MISSING")
peer=peers[0]
pub=str(peer.get("public_key","")).strip()
ep=peer.get("endpoint") or {}
host=str(ep.get("host","")).strip()
m=re.fullmatch(r"(.+):(\d+)",host)
if not m: raise SystemExit("WARP_ENDPOINT_HOST_BAD")
endpoint_host,port=m.group(1),int(m.group(2))
try:
    server=socket.getaddrinfo(endpoint_host,port,socket.AF_INET,socket.SOCK_DGRAM)[0][4][0]
except Exception as e:
    raise SystemExit("WARP_ENDPOINT_RESOLVE_FAILED")
addresses=[]
raw_addresses=((cfg.get("interface") or {}).get("addresses") or [])
if isinstance(raw_addresses,dict): raw_addresses=[raw_addresses]
for a in raw_addresses:
    if isinstance(a,dict):
        if a.get("v4"): addresses.append(str(ipaddress.ip_address(a["v4"]))+"/32")
        if a.get("v6"): addresses.append(str(ipaddress.ip_address(a["v6"]))+"/128")
if not addresses: raise SystemExit("WARP_ADDRESSES_MISSING")
reserved=[]
cid=cfg.get("client_id")
if cid:
    raw=base64.b64decode(cid)
    if len(raw)==3: reserved=list(raw)
p={
 "schema":1,"name":"WARP_NATIVE","country":"","kind":"wireguard",
 "capabilities":{"tcp":True,"udp":True,"country_verified":False},
 "endpoint":{
   "type":"wireguard","tag":"provider","system":False,"mtu":1280,
   "address":addresses,"private_key":priv,
   "peers":[{
      "address":server,"port":port,"public_key":pub,
      "allowed_ips":["0.0.0.0/0","::/0"],
      "persistent_keepalive_interval":25,
      **({"reserved":reserved} if reserved else {})
   }]
 },
 "source":{"kind":"wgcf-identity","sha256":hashlib.sha256(src.read_bytes()).hexdigest().upper(),"endpoint_host":endpoint_host}
}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":"PASS","output":str(out),"profileSha256":hashlib.sha256(out.read_bytes()).hexdigest().upper(),"addressCount":len(addresses),"reservedBytes":len(reserved),"endpointHost":endpoint_host,"endpointIPv4":server,"endpointPort":port},indent=2))
