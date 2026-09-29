import base64, http.client, ipaddress, json, os, socket, ssl, struct, time, urllib.parse

QNAME="www.youtube.com"
ENDPOINTS=[
 {"name":"controld-ip1","connect":"76.76.2.11","host":"76.76.2.11","path":"/p0"},
 {"name":"controld-ip2","connect":"76.76.10.11","host":"76.76.10.11","path":"/p0"},
 {"name":"controld-host","connect":"freedns.controld.com","host":"freedns.controld.com","path":"/p0"},
 {"name":"adguard-unfiltered","connect":"unfiltered.adguard-dns.com","host":"unfiltered.adguard-dns.com","path":"/dns-query"},
]
def qwire(name):
    tx=os.urandom(2); flags=b"\x01\x00"; counts=b"\x00\x01\x00\x00\x00\x00\x00\x00"
    q=b"".join(bytes([len(x)])+x.encode("ascii") for x in name.rstrip(".").split("."))+b"\x00"
    return tx+flags+counts+q+struct.pack("!HH",1,1)
def skip_name(data,p):
    while p<len(data):
        n=data[p]
        if n&0xC0==0xC0:return p+2
        if n==0:return p+1
        p+=1+n
    raise ValueError("bad-name")
def parse_a(data):
    if len(data)<12:return []
    qd,an=struct.unpack("!HH",data[4:8]);p=12
    for _ in range(qd):
        p=skip_name(data,p)+4
    out=[]
    for _ in range(an):
        p=skip_name(data,p)
        typ,cls,ttl,ln=struct.unpack("!HHIH",data[p:p+10]);p+=10
        r=data[p:p+ln];p+=ln
        if typ==1 and cls==1 and ln==4:out.append(socket.inet_ntoa(r))
    return out

ctx=ssl.create_default_context()
results=[]
wire=qwire(QNAME)
for ep in ENDPOINTS:
    started=time.time();row={"name":ep["name"],"connect":ep["connect"],"path":ep["path"]}
    try:
        c=http.client.HTTPSConnection(ep["connect"],443,timeout=5,context=ctx)
        c.request("POST",ep["path"],body=wire,headers={"Host":ep["host"],"Content-Type":"application/dns-message","Accept":"application/dns-message","User-Agent":"FreeNetHub-R34/1.0"})
        r=c.getresponse();body=r.read(65536)
        row.update({"status":r.status,"contentType":r.getheader("content-type"),"ips":parse_a(body) if r.status==200 else [],"bytes":len(body),"seconds":round(time.time()-started,3)})
        c.close()
    except Exception as e:
        row.update({"error":type(e).__name__+": "+str(e),"seconds":round(time.time()-started,3)})
    results.append(row)
print(json.dumps({"query":QNAME,"results":results},indent=2))
