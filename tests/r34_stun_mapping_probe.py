import json, os, socket, struct

LOCAL_IP="192.168.20.5"
TARGETS=[
    ("stun.l.google.com",19302),
    ("stun1.l.google.com",19302),
    ("stun.cloudflare.com",3478),
]
MAGIC=0x2112A442

def parse_addr(data, txid):
    if len(data)<20: return None
    mtype, mlen, magic = struct.unpack("!HHI", data[:8])
    if magic != MAGIC: return None
    pos=20
    end=min(len(data),20+mlen)
    while pos+4<=end:
        atype, alen=struct.unpack("!HH",data[pos:pos+4]); pos+=4
        val=data[pos:pos+alen]
        pos += (alen + 3) & ~3
        if atype in (0x0020,0x0001) and alen>=8:
            fam=val[1]
            port=struct.unpack("!H",val[2:4])[0]
            raw=val[4:]
            if atype==0x0020:
                port ^= MAGIC >> 16
                if fam==0x01 and len(raw)>=4:
                    cookie=struct.pack("!I",MAGIC)
                    ipb=bytes(a^b for a,b in zip(raw[:4],cookie))
                    return socket.inet_ntop(socket.AF_INET,ipb),port,"XOR-MAPPED-ADDRESS"
                if fam==0x02 and len(raw)>=16:
                    mask=struct.pack("!I",MAGIC)+txid
                    ipb=bytes(a^b for a,b in zip(raw[:16],mask))
                    return socket.inet_ntop(socket.AF_INET6,ipb),port,"XOR-MAPPED-ADDRESS"
            else:
                if fam==0x01 and len(raw)>=4:
                    return socket.inet_ntop(socket.AF_INET,raw[:4]),port,"MAPPED-ADDRESS"
    return None

sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind((LOCAL_IP,0))
sock.settimeout(2.0)
local_port=sock.getsockname()[1]
results=[]
for host,port in TARGETS:
    try:
        ips=socket.getaddrinfo(host,port,socket.AF_INET,socket.SOCK_DGRAM)
        dest=ips[0][4]
        txid=os.urandom(12)
        req=struct.pack("!HHI",0x0001,0,MAGIC)+txid
        sock.sendto(req,dest)
        data,addr=sock.recvfrom(4096)
        mapped=parse_addr(data,txid)
        results.append({"target":f"{host}:{port}","resolved":dest[0],"from":f"{addr[0]}:{addr[1]}","mappedIp":mapped[0] if mapped else None,"mappedPort":mapped[1] if mapped else None,"attribute":mapped[2] if mapped else None})
    except Exception as e:
        results.append({"target":f"{host}:{port}","error":type(e).__name__+": "+str(e)})
sock.close()
valid=[(x.get("mappedIp"),x.get("mappedPort")) for x in results if x.get("mappedIp")]
print(json.dumps({"localIp":LOCAL_IP,"localUdpPort":local_port,"results":results,"mappingStableAcrossTargets": len(set(valid))==1 if valid else None},indent=2))
