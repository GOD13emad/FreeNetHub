import json, os, socket, struct, sys, time
LOCAL_IP="192.168.20.5"
LOCAL_PORT=54321
MAGIC=0x2112A442
STUN=("stun.cloudflare.com",3478)

def stun_map(sock):
    dest=socket.getaddrinfo(STUN[0],STUN[1],socket.AF_INET,socket.SOCK_DGRAM)[0][4]
    txid=os.urandom(12)
    sock.sendto(struct.pack("!HHI",0x0001,0,MAGIC)+txid,dest)
    data,addr=sock.recvfrom(4096)
    _,mlen,magic=struct.unpack("!HHI",data[:8])
    pos=20
    while pos+4<=20+mlen:
        at,ln=struct.unpack("!HH",data[pos:pos+4]); pos+=4
        val=data[pos:pos+ln]; pos+=(ln+3)&~3
        if at==0x0020 and ln>=8 and val[1]==1:
            port=struct.unpack("!H",val[2:4])[0]^(MAGIC>>16)
            cookie=struct.pack("!I",MAGIC)
            ipb=bytes(a^b for a,b in zip(val[4:8],cookie))
            return socket.inet_ntoa(ipb),port,addr
    raise RuntimeError("No XOR-MAPPED-ADDRESS")

s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((LOCAL_IP,LOCAL_PORT))
s.settimeout(4.0)
mapped_ip,mapped_port,stun_from=stun_map(s)
print(json.dumps({"state":"READY","localIp":LOCAL_IP,"localPort":LOCAL_PORT,"mappedIp":mapped_ip,"mappedPort":mapped_port,"stunFrom":f"{stun_from[0]}:{stun_from[1]}"}),flush=True)
# Create an outbound flow toward the independent peer as well; it may help reveal endpoint filtering.
try:
    s.sendto(b"FNH-R34-OUTBOUND-PRIME",("94.182.28.19",54322))
except Exception:
    pass
deadline=time.time()+12
events=[]
while time.time()<deadline:
    try:
        data,addr=s.recvfrom(4096)
        events.append({"from":f"{addr[0]}:{addr[1]}","data":data.decode("utf-8","replace")})
        print(json.dumps({"state":"RECEIVED","from":f"{addr[0]}:{addr[1]}","data":data.decode("utf-8","replace")}),flush=True)
        if data.startswith(b"FNH-R34"):
            break
    except socket.timeout:
        break
print(json.dumps({"state":"DONE","received":events}),flush=True)
s.close()
