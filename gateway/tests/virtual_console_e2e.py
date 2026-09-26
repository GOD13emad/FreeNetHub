#!/usr/bin/env python3
import json, socket, threading, subprocess, shutil, sys, time

HOST="127.77.0.1"
CONSOLE="127.77.0.2"
GATEWAY="127.77.0.3"
WAN="127.77.0.4"
TIMEOUT=5.0
errors=[]
obs={}

def routes():
    if not shutil.which("ip"):
        return None
    p=subprocess.run(["ip","route","show"],capture_output=True,text=True,check=False)
    return p.stdout.strip().splitlines() if p.returncode==0 else None

before_routes=routes()

# TCP WAN echo server, two sessions: direct host and translated console.
tcp_srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcp_srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
tcp_srv.bind((WAN,0)); tcp_srv.listen(4); tcp_srv.settimeout(TIMEOUT)
tcp_port=tcp_srv.getsockname()[1]
tcp_peers=[]

def tcp_server():
    try:
        for _ in range(2):
            c,a=tcp_srv.accept(); c.settimeout(TIMEOUT); tcp_peers.append(a[0])
            data=c.recv(4096); c.sendall(b"WAN:"+data); c.close()
    except Exception as e:
        errors.append("TCP_SERVER:"+repr(e))
    finally:
        tcp_srv.close()

ts=threading.Thread(target=tcp_server,daemon=True); ts.start()

# Direct host control path.
c=socket.socket(socket.AF_INET,socket.SOCK_STREAM); c.settimeout(TIMEOUT); c.bind((HOST,0)); c.connect((WAN,tcp_port))
c.sendall(b"host-direct"); direct_reply=c.recv(4096); c.close()

# User-space gateway: accept console source, create WAN leg bound to gateway source.
proxy=socket.socket(socket.AF_INET,socket.SOCK_STREAM); proxy.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
proxy.bind((GATEWAY,0)); proxy.listen(1); proxy.settimeout(TIMEOUT)
proxy_port=proxy.getsockname()[1]
proxy_in=[]

def tcp_proxy():
    try:
        inc,a=proxy.accept(); inc.settimeout(TIMEOUT); proxy_in.append(a[0])
        data=inc.recv(4096)
        out=socket.socket(socket.AF_INET,socket.SOCK_STREAM); out.settimeout(TIMEOUT); out.bind((GATEWAY,0)); out.connect((WAN,tcp_port))
        out.sendall(data); reply=out.recv(4096); out.close()
        inc.sendall(reply); inc.close()
    except Exception as e:
        errors.append("TCP_PROXY:"+repr(e))
    finally:
        proxy.close()

tp=threading.Thread(target=tcp_proxy,daemon=True); tp.start()
cc=socket.socket(socket.AF_INET,socket.SOCK_STREAM); cc.settimeout(TIMEOUT); cc.bind((CONSOLE,0)); cc.connect((GATEWAY,proxy_port))
cc.sendall(b"console-through-gateway"); console_reply=cc.recv(4096); cc.close()
ts.join(TIMEOUT); tp.join(TIMEOUT)

# UDP WAN echo server, two datagrams: direct host and translated console.
udp_srv=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); udp_srv.bind((WAN,0)); udp_srv.settimeout(TIMEOUT)
udp_port=udp_srv.getsockname()[1]; udp_peers=[]

def udp_server():
    try:
        for _ in range(2):
            data,a=udp_srv.recvfrom(65535); udp_peers.append(a[0]); udp_srv.sendto(b"WAN:"+data,a)
    except Exception as e:
        errors.append("UDP_SERVER:"+repr(e))
    finally:
        udp_srv.close()

us=threading.Thread(target=udp_server,daemon=True); us.start()
uh=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); uh.settimeout(TIMEOUT); uh.bind((HOST,0))
uh.sendto(b"host-direct",(WAN,udp_port)); direct_udp=uh.recvfrom(65535)[0]; uh.close()

udp_proxy=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); udp_proxy.bind((GATEWAY,0)); udp_proxy.settimeout(TIMEOUT)
udp_proxy_port=udp_proxy.getsockname()[1]; udp_proxy_in=[]

def udp_proxy_fn():
    try:
        data,a=udp_proxy.recvfrom(65535); udp_proxy_in.append(a[0])
        out=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); out.settimeout(TIMEOUT); out.bind((GATEWAY,0))
        out.sendto(data,(WAN,udp_port)); reply,_=out.recvfrom(65535); out.close()
        udp_proxy.sendto(reply,a)
    except Exception as e:
        errors.append("UDP_PROXY:"+repr(e))
    finally:
        udp_proxy.close()

up=threading.Thread(target=udp_proxy_fn,daemon=True); up.start()
uc=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); uc.settimeout(TIMEOUT); uc.bind((CONSOLE,0))
uc.sendto(b"console-through-gateway",(GATEWAY,udp_proxy_port)); console_udp=uc.recvfrom(65535)[0]; uc.close()
us.join(TIMEOUT); up.join(TIMEOUT)

after_routes=routes()

checks={
    "tcp_direct_payload": direct_reply==b"WAN:host-direct",
    "tcp_console_payload": console_reply==b"WAN:console-through-gateway",
    "tcp_console_source_seen_by_gateway": proxy_in==[CONSOLE],
    "tcp_wan_sources": tcp_peers==[HOST,GATEWAY],
    "udp_direct_payload": direct_udp==b"WAN:host-direct",
    "udp_console_payload": console_udp==b"WAN:console-through-gateway",
    "udp_console_source_seen_by_gateway": udp_proxy_in==[CONSOLE],
    "udp_wan_sources": udp_peers==[HOST,GATEWAY],
    "host_route_table_unchanged": before_routes is None or before_routes==after_routes,
}
if errors:
    checks["thread_errors"]=False

out={
  "schema":1,
  "topology":{"host":HOST,"console":CONSOLE,"gateway":GATEWAY,"wan":WAN},
  "semantics":{
    "hostDirectSourcePreserved": True,
    "consoleSourceTranslatedToGateway": True,
    "protocols":["TCP","UDP"],
    "kernelNat":False,
    "level":"USERSPACE_VIRTUAL_DATAPLANE"
  },
  "observed":{
    "tcpWanPeers":tcp_peers,"tcpGatewayInboundPeers":proxy_in,
    "udpWanPeers":udp_peers,"udpGatewayInboundPeers":udp_proxy_in,
    "routeSnapshotAvailable":before_routes is not None,
    "errors":errors
  },
  "checks":checks,
  "status":"PASS" if all(checks.values()) else "FAIL"
}
print(json.dumps(out,indent=2))
sys.exit(0 if out["status"]=="PASS" else 1)
