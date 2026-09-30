from __future__ import annotations
import base64,json,pathlib,subprocess,socket,time,uuid,sys,os,shutil
ROOT=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
sys.path.insert(0,str(ROOT/"app"))
import nodehub as NH
runtime=json.loads((ROOT/"gateway/runtime/local_gateway.json").read_text(encoding="utf-8-sig"))
SB=pathlib.Path(runtime["singbox"]["path"])
WORK=ROOT/"jobs"/("hermetic2-"+uuid.uuid4().hex);WORK.mkdir(parents=True,exist_ok=True)
FLAGS=0x08000000|0x00000200 if os.name=="nt" else 0
def wait_port(port,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            with socket.create_connection(("127.0.0.1",port),timeout=.2): return True
        except OSError: time.sleep(.05)
    return False
def b64(s): return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
def curl_probe(proxy,url,expect,insecure=False):
    cmd=["curl.exe","-q","-4","-sS","--proxy",proxy,"--noproxy","","--connect-timeout","4","--max-time","12","-o","NUL","--write-out","%{http_code} %{time_total}"]
    if insecure: cmd.append("-k")
    cmd.append(url)
    c=subprocess.run(cmd,cwd=WORK,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=FLAGS,timeout=15,text=True)
    parts=c.stdout.strip().split()
    code=parts[0] if parts else "000"
    return {"ok":c.returncode==0 and code==expect,"exit":c.returncode,"code":code,"seconds":float(parts[1]) if len(parts)>1 else None}
def run_case(name,uri,server_inbound,server_port,client_port):
    case=WORK/name;case.mkdir()
    node=NH.parse_uri(uri);ccfg=NH.sing_box_config(node,client_port)
    scfg={"log":{"level":"warn","timestamp":True},"dns":{"servers":[{"type":"local","tag":"local"}],"final":"local","strategy":"ipv4_only"},"inbounds":[server_inbound],"outbounds":[{"type":"direct","tag":"direct"}],"route":{"final":"direct","auto_detect_interface":True,"default_domain_resolver":"local"}}
    cp=case/"client.json";sp=case/"server.json";cp.write_text(json.dumps(ccfg,indent=2),encoding="utf-8");sp.write_text(json.dumps(scfg,indent=2),encoding="utf-8")
    checks={}
    for label,path in (("server",sp),("client",cp)):
        c=subprocess.run([str(SB),"check","-c",str(path)],cwd=case,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=FLAGS,timeout=10)
        checks[label]=c.returncode
        if c.returncode: return {"case":name,"status":"FAIL","stage":label+"_check","exit":c.returncode}
    slog=open(case/"server.log","wb");clog=open(case/"client.log","wb");srv=cli=None
    try:
        srv=subprocess.Popen([str(SB),"run","-c",str(sp)],cwd=case,stdin=subprocess.DEVNULL,stdout=slog,stderr=slog,creationflags=FLAGS)
        if not wait_port(server_port,5): return {"case":name,"status":"FAIL","stage":"server_listen"}
        cli=subprocess.Popen([str(SB),"run","-c",str(cp)],cwd=case,stdin=subprocess.DEVNULL,stdout=clog,stderr=clog,creationflags=FLAGS)
        if not wait_port(client_port,5): return {"case":name,"status":"FAIL","stage":"client_listen"}
        proxy=f"socks5h://127.0.0.1:{client_port}"
        ip=curl_probe(proxy,"https://1.1.1.1/cdn-cgi/trace","200",True)
        domain=curl_probe(proxy,"https://www.youtube.com/generate_204","204",False)
        ok=ip["ok"] and domain["ok"]
        return {"case":name,"status":"PASS" if ok else "FAIL","stage":"https","ipLiteral":ip,"domain":domain}
    finally:
        for proc in (cli,srv):
            if proc and proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill();proc.wait(timeout=3)
        slog.close();clog.close()
uid="11111111-1111-1111-1111-111111111111"
cases=[
 ("ss_tcp","ss://"+b64("aes-128-gcm:local-test-password")+"@127.0.0.1:19711#local",{"type":"shadowsocks","tag":"srv","listen":"127.0.0.1","listen_port":19711,"method":"aes-128-gcm","password":"local-test-password"},19711,19611),
 ("vmess_ws","vmess://"+b64(json.dumps({"v":"2","ps":"local","add":"127.0.0.1","port":"19712","id":uid,"aid":"0","scy":"auto","net":"ws","host":"","path":"/vm","tls":""},separators=(",",":"))),{"type":"vmess","tag":"srv","listen":"127.0.0.1","listen_port":19712,"users":[{"name":"u","uuid":uid,"alterId":0}],"transport":{"type":"ws","path":"/vm"}},19712,19612),
 ("vless_tcp",f"vless://{uid}@127.0.0.1:19713?security=none&type=tcp#local",{"type":"vless","tag":"srv","listen":"127.0.0.1","listen_port":19713,"users":[{"name":"u","uuid":uid}]},19713,19613),
 ("vless_ws_ed",f"vless://{uid}@127.0.0.1:19714?security=none&type=ws&path=%2Fed&ed=1024&eh=Sec-WebSocket-Protocol#local",{"type":"vless","tag":"srv","listen":"127.0.0.1","listen_port":19714,"users":[{"name":"u","uuid":uid}],"transport":{"type":"ws","path":"/ed","max_early_data":1024,"early_data_header_name":"Sec-WebSocket-Protocol"}},19714,19614),
]
rows=[]
try:
    for c in cases: rows.append(run_case(*c))
finally: shutil.rmtree(WORK,ignore_errors=True)
out={"schema":2,"date":"2026-09-28","status":"PASS" if all(x["status"]=="PASS" for x in rows) else "FAIL","singboxVersion":runtime["singbox"].get("version"),"serverDns":"sing-box local DNS + route.default_domain_resolver=local","cases":rows,"privacy":"Synthetic loopback credentials/configs deleted; no public-node material used."}
PROJECT=pathlib.Path(__file__).resolve().parent.parent
path=PROJECT/"evidence"/"R28_HERMETIC_PROTOCOL_LOOPBACK2_ACCEPTANCE_20260928.json";path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(0 if out["status"]=="PASS" else 28)
