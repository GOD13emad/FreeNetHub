from pathlib import Path
import argparse,configparser,json,re,hashlib,os,base64
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def split_csv(v):return [x.strip() for x in (v or "").split(",") if x.strip()]
def parse_endpoint(v):
 v=v.strip()
 if v.startswith("["):
  m=re.fullmatch(r"\[(.+)\]:(\d+)",v)
 else:
  m=re.fullmatch(r"(.+):(\d+)",v)
 if not m:raise ValueError("BAD_WIREGUARD_ENDPOINT")
 return m.group(1),int(m.group(2))
def key_ok(v):
 try:return len(base64.b64decode(v,validate=True))==32
 except Exception:return False
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("conf")
 ap.add_argument("--name",required=True)
 ap.add_argument("--country",required=True)
 ap.add_argument("--output",required=True)
 ns=ap.parse_args()
 c=configparser.ConfigParser(strict=True);c.optionxform=str
 with open(ns.conf,"r",encoding="utf-8-sig") as f:c.read_file(f)
 if "Interface" not in c or "Peer" not in c:raise SystemExit("WIREGUARD_INTERFACE_OR_PEER_MISSING")
 i=c["Interface"];p=c["Peer"]
 priv=i.get("PrivateKey","").strip();pub=p.get("PublicKey","").strip();psk=p.get("PresharedKey","").strip()
 if not key_ok(priv) or not key_ok(pub) or (psk and not key_ok(psk)):raise SystemExit("WIREGUARD_KEY_FORMAT_INVALID")
 addr=split_csv(i.get("Address",""))
 if not addr:raise SystemExit("WIREGUARD_ADDRESS_MISSING")
 host,port=parse_endpoint(p.get("Endpoint",""))
 allowed=split_csv(p.get("AllowedIPs","0.0.0.0/0,::/0"))
 ep={
  "type":"wireguard","tag":"provider","system":False,"mtu":int(i.get("MTU","1408")),
  "address":addr,"private_key":priv,
  "peers":[{
    "address":host,"port":port,"public_key":pub,"allowed_ips":allowed,
    "persistent_keepalive_interval":int(p.get("PersistentKeepalive","25"))
  }]
 }
 if psk:ep["peers"][0]["pre_shared_key"]=psk
 profile={
  "schema":1,"name":ns.name,"country":ns.country.upper(),"kind":"wireguard",
  "capabilities":{"tcp":True,"udp":True,"country_verified":False},
  "endpoint":ep,
  "source":{"filename":Path(ns.conf).name,"sha256":sha(Path(ns.conf))}
 }
 out=Path(ns.output);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"IMPORTED","name":profile["name"],"country":profile["country"],"output":str(out),"sha256":sha(out),"privateMaterialStored":True},indent=2))
if __name__=="__main__":main()
