import json, pathlib, sys
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/"app"))
import engine as E
host="www.youtube.com"
print(json.dumps({"host":host,"ips":E.public_dns_ips(host)},indent=2))
