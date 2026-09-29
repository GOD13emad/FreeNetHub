import json, os, socket, struct, sys, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
import directnet as D

TARGETS=[
    ("77.88.8.8",1253,"Yandex alternate"),
    ("77.88.8.1",1253,"Yandex alternate secondary"),
]
HOSTS=["www.youtube.com","chatgpt.com","github.com"]
rows=[]
for server,port,label in TARGETS:
    for host in HOSTS:
        txid=os.urandom(2)
        q=txid+b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"+D._dns_name_wire(host)+struct.pack("!HH",1,1)
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(2.0)
        try:
            s.sendto(q,(server,port))
            data,addr=s.recvfrom(65535)
            ips=D._parse_dns_a(data,txid)
            rows.append({"server":f"{server}:{port}","label":label,"host":host,"from":f"{addr[0]}:{addr[1]}","globalA":ips,"ok":bool(ips)})
        except Exception as e:
            rows.append({"server":f"{server}:{port}","label":label,"host":host,"ok":False,"error":type(e).__name__+": "+str(e)})
        finally:s.close()
print(json.dumps(rows,ensure_ascii=False,indent=2))
