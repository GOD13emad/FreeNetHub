import socket,struct,random,json,time
dst=(socket.gethostbyname("stun.cloudflare.com"),3478)
tx=random.randbytes(12);msg=struct.pack("!HHI",1,0,0x2112A442)+tx
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(8);t=time.monotonic();s.sendto(msg,dst);d,_=s.recvfrom(4096);dt=time.monotonic()-t
typ,l,cookie=struct.unpack("!HHI",d[:8])
if typ!=0x0101 or cookie!=0x2112A442:raise RuntimeError("BAD_STUN")
i=20;m=None
while i+4<=len(d):
 at,ln=struct.unpack("!HH",d[i:i+4]);v=d[i+4:i+4+ln]
 if at in (0x0020,0x0001) and len(v)>=8 and v[1]==1:
  p=struct.unpack("!H",v[2:4])[0]
  raw=bytearray(v[4:8])
  if at==0x0020:
   p^=(0x2112A442>>16);mc=struct.pack("!I",0x2112A442);raw=bytearray(a^b for a,b in zip(raw,mc))
  m=(socket.inet_ntoa(raw),p);break
 i+=4+((ln+3)//4)*4
if not m:raise RuntimeError("NO_MAPPED")
print(json.dumps({"status":"PASS","public_ip":m[0],"public_port":m[1],"seconds":dt}))
