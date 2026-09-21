import socket,struct,random,json,time,sys
port=int(sys.argv[1])
proxy_host=sys.argv[2] if len(sys.argv)>2 else "127.0.0.1"
proxy=(proxy_host,port)
stun=("stun.cloudflare.com",3478)
def rx(s,n):
 b=b""
 while len(b)<n:
  x=s.recv(n-len(b))
  if not x:raise RuntimeError("EOF")
  b+=x
 return b
tcp=socket.create_connection(proxy,timeout=5);tcp.sendall(b"\x05\x01\x00")
if rx(tcp,2)!=b"\x05\x00":raise RuntimeError("AUTH")
tcp.sendall(b"\x05\x03\x00\x01\x00\x00\x00\x00\x00\x00")
h=rx(tcp,4);at=h[3]
if h[1]!=0:raise RuntimeError("ASSOC")
if at==1:host=socket.inet_ntoa(rx(tcp,4))
elif at==3:
 ln=rx(tcp,1)[0];host=rx(tcp,ln).decode()
elif at==4:host=socket.inet_ntop(socket.AF_INET6,rx(tcp,16))
prt=struct.unpack("!H",rx(tcp,2))[0]
relay=(host if host not in ("0.0.0.0","::") else proxy_host,prt)
dst=socket.gethostbyname(stun[0]);tx=random.randbytes(12)
msg=struct.pack("!HHI",0x0001,0,0x2112A442)+tx
pkt=b"\x00\x00\x00\x01"+socket.inet_aton(dst)+struct.pack("!H",stun[1])+msg
u=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);u.settimeout(10);t0=time.monotonic();u.sendto(pkt,relay);resp,_=u.recvfrom(4096);dt=time.monotonic()-t0
i=4
if resp[3]==1:i+=4
elif resp[3]==3:i+=1+resp[4]
elif resp[3]==4:i+=16
i+=2
d=resp[i:]
typ,length,cookie=struct.unpack("!HHI",d[:8])
if typ!=0x0101 or cookie!=0x2112A442:raise RuntimeError("BAD_STUN")
j=20;mapped=None
while j+4<=len(d):
 at,ln=struct.unpack("!HH",d[j:j+4]);val=d[j+4:j+4+ln]
 if at in (0x0020,0x0001) and len(val)>=8:
  fam=val[1];p=struct.unpack("!H",val[2:4])[0]
  if at==0x0020:p^=(0x2112A442>>16)
  if fam==1:
   raw=bytearray(val[4:8])
   if at==0x0020:
    mc=struct.pack("!I",0x2112A442)
    raw=bytearray(a^b for a,b in zip(raw,mc))
   mapped=(socket.inet_ntoa(raw),p);break
 j+=4+((ln+3)//4)*4
if not mapped:raise RuntimeError("NO_MAPPED_ADDRESS")
print(json.dumps({"status":"PASS","udp_public_ip":mapped[0],"udp_public_port":mapped[1],"seconds":dt,"relay":relay},indent=2))
