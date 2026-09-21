#!/usr/bin/env python3
from __future__ import annotations
import json, os, pathlib, re, shutil, signal, socket, subprocess, threading, time, uuid

APP="FreeNet Hub"
VERSION="4.2.0-linux.3"
STATE=pathlib.Path.home()/".local"/"share"/"FreeNetHub"
TOR_STATE=STATE/"tor"
OWNER=TOR_STATE/"owner.json"
LAST_MODE=TOR_STATE/"last_mode.txt"
BRIDGES=STATE/"bridges_obfs4.txt"
SNOWFLAKE_BRIDGES=STATE/"bridges_snowflake.txt"
SOCKS_PORT=9909
WARP_GUARD_SECONDS=75

def executable(name:str):
    p=shutil.which(name)
    if p:return p
    q=STATE/"runtime"/"usr"/"bin"/name
    return str(q) if q.exists() else None

def exists(name):return executable(name) is not None

def run(args,timeout=20):
    try:
        return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(args,124,e.stdout or "",(e.stderr or "")+"\nTIMEOUT")

def trace(proxy=None,timeout=15):
    curl=executable("curl")
    if not curl:return {"ok":False,"error":"curl missing"}
    args=[curl,"-4","--max-time",str(timeout),"-fsS"]
    if proxy:args+=["--proxy",proxy]
    args+=["https://www.cloudflare.com/cdn-cgi/trace"]
    p=run(args,timeout+3)
    if p.returncode:return {"ok":False,"error":(p.stderr or p.stdout).strip()}
    d={}
    for line in p.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1);d[k]=v
    return {"ok":True,"trace":d}

def identity(pid:int):
    try:
        proc=pathlib.Path(f"/proc/{pid}")
        return {"pid":pid,"exe":os.readlink(proc/"exe"),"start":(proc/"stat").read_text().split()[21]}
    except Exception:return None

def owner():
    try:
        r=json.loads(OWNER.read_text())
        cur=identity(int(r["pid"]))
        if cur and all(str(cur[k])==str(r[k]) for k in ("pid","exe","start")):return r
    except Exception:pass
    return None

def _stop_pid(pid:int):
    try:os.kill(pid,signal.SIGTERM)
    except ProcessLookupError:return True
    except Exception:return False
    for _ in range(50):
        if identity(pid) is None:return True
        time.sleep(.1)
    try:os.kill(pid,signal.SIGKILL)
    except Exception:pass
    for _ in range(20):
        if identity(pid) is None:return True
        time.sleep(.05)
    return identity(pid) is None

def _listener_pid(port:int):
    ss=shutil.which("ss")
    if not ss:return None
    try:
        p=run([ss,"-ltnp",f"sport = :{port}"],5)
        m=re.search(r"pid=(\d+)",(p.stdout or "")+(p.stderr or ""))
        return int(m.group(1)) if m else None
    except Exception:return None

def _recover_stale_project_listener():
    pid=_listener_pid(SOCKS_PORT)
    if not pid:return {"ok":True,"state":"free"}
    r=owner()
    if r and int(r.get("pid",0))==pid:
        return {"ok":False,"error":"project Tor already running","pid":pid,"owned":True}
    try:
        ident=identity(pid)
        cmd=(pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace"))
        tor=executable("tor")
        trusted=bool(ident and tor and pathlib.Path(ident["exe"]).resolve()==pathlib.Path(tor).resolve())
        local_cfg=str(TOR_STATE.resolve()) in cmd and "torrc-" in cmd
        if trusted and local_cfg:
            stopped=_stop_pid(pid)
            try:OWNER.unlink(missing_ok=True)
            except Exception:pass
            return {"ok":bool(stopped),"state":"recovered-stale-project-listener" if stopped else "recovery-failed","pid":pid}
    except Exception:pass
    return {"ok":False,"error":"SOCKS port occupied by foreign or unproven process","pid":pid}

def _normalize_snowflake_bridge(line:str):
    parts=line.split()
    out=[]
    for token in parts:
        if token.startswith("front="):
            value=token.split("=",1)[1]
            if "," in value:token="front="+value.split(",",1)[0]
        out.append(token)
    return " ".join(out)

def _bridge_lines(path=BRIDGES):
    try:return [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
    except Exception:return []

def _bootstrap_percent(log_path:pathlib.Path):
    try:
        pct=0
        for line in log_path.read_text(errors="replace").splitlines():
            if "Bootstrapped " in line:
                s=line.split("Bootstrapped ",1)[1].split("%",1)[0]
                if s.isdigit():pct=max(pct,int(s))
        return pct
    except Exception:return 0

def _launch_tor(mode:str,timeout:float):
    tor=executable("tor")
    if not tor:return {"ok":False,"mode":mode,"error":"tor executable missing"}
    guard=_recover_stale_project_listener()
    if not guard.get("ok"):return {"ok":False,"mode":mode,"error":guard.get("error","SOCKS port unavailable"),"listener":guard}
    TOR_STATE.mkdir(parents=True,exist_ok=True)
    data=TOR_STATE/f"data-{mode}";data.mkdir(exist_ok=True)
    log_path=TOR_STATE/f"tor-{mode}.log";torrc=TOR_STATE/f"torrc-{mode}"
    lines=[f"SocksPort 127.0.0.1:{SOCKS_PORT}",f"DataDirectory {data}","AvoidDiskWrites 1"]
    if mode=="obfs4":
        obfs=executable("obfs4proxy");bridges=_bridge_lines(BRIDGES)
        if not obfs:return {"ok":False,"mode":mode,"error":"obfs4proxy missing"}
        if not bridges:return {"ok":False,"mode":mode,"error":"no obfs4 bridges configured"}
        lines+=["UseBridges 1",f"ClientTransportPlugin obfs4 exec {obfs}"]
        lines += [f"Bridge {b}" for b in bridges]
    elif mode=="snowflake":
        snow=executable("snowflake-client");bridges=[_normalize_snowflake_bridge(b) for b in _bridge_lines(SNOWFLAKE_BRIDGES)]
        if not snow:return {"ok":False,"mode":mode,"error":"snowflake-client missing"}
        if not bridges:return {"ok":False,"mode":mode,"error":"no snowflake bridges configured"}
        lines+=["UseBridges 1",f"ClientTransportPlugin snowflake exec {snow}"]
        lines += [f"Bridge {b}" for b in bridges]
    torrc.write_text("\n".join(lines)+"\n",encoding="utf-8")
    log=open(log_path,"wb",buffering=0)
    p=subprocess.Popen([tor,"-f",str(torrc)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
    deadline=time.time()+timeout;pct=0
    while time.time()<deadline:
        if p.poll() is not None:
            log.close();return {"ok":False,"mode":mode,"error":"tor exited during startup","bootstrap":pct}
        pct=_bootstrap_percent(log_path)
        if pct>=100:
            ident=identity(p.pid)
            if ident:
                OWNER.write_text(json.dumps(ident|{"started":time.time(),"mode":mode,"bootstrap":100},indent=2),encoding="utf-8")
                LAST_MODE.write_text(mode,encoding="utf-8")
            log.close()
            return {"ok":True,"state":"running","mode":mode,"bootstrap":100,"proxy":f"socks5h://127.0.0.1:{SOCKS_PORT}"}
        time.sleep(.25)
    _stop_pid(p.pid);log.close()
    return {"ok":False,"mode":mode,"error":"bootstrap timeout","bootstrap":pct}

def tor_status():
    r=owner()
    if not r:return {"ok":True,"state":"stopped","proxy":f"socks5h://127.0.0.1:{SOCKS_PORT}"}
    t=trace(f"socks5h://127.0.0.1:{SOCKS_PORT}",12)
    return {"ok":bool(t.get("ok")),"state":"running","mode":r.get("mode"),"pid":r.get("pid"),"bootstrap":r.get("bootstrap"),"egress":t}

def start_tor():
    r=owner()
    if r:
        t=trace(f"socks5h://127.0.0.1:{SOCKS_PORT}",12)
        return {"ok":bool(t.get("ok")),"state":"already-running","mode":r.get("mode"),"proxy":f"socks5h://127.0.0.1:{SOCKS_PORT}","egress":t}
    preferred=""
    try:preferred=LAST_MODE.read_text().strip()
    except Exception:pass
    available=["snowflake","direct","obfs4"] if _bridge_lines(SNOWFLAKE_BRIDGES) else ["direct","obfs4"]
    modes=([preferred]+[m for m in available if m!=preferred]) if preferred in available else available
    attempts=[]
    for mode in modes:
        x=_launch_tor(mode,90 if mode=="direct" else 120)
        attempts.append({k:v for k,v in x.items() if k!="log_tail"})
        if x.get("ok"):
            t=trace(x["proxy"],20)
            if t.get("ok"):
                x["egress"]=t;x["attempts"]=attempts;return x
            if owner():_stop_pid(int(owner()["pid"]))
            try:OWNER.unlink(missing_ok=True)
            except Exception:pass
            attempts[-1]["egress_error"]=t.get("error","egress failed")
    return {"ok":False,"state":"failed","attempts":attempts}

def stop_tor():
    r=owner()
    if not r:return {"ok":True,"state":"not-owned"}
    stopped=_stop_pid(int(r["pid"]))
    if stopped:
        try:OWNER.unlink(missing_ok=True)
        except Exception:pass
    return {"ok":stopped,"state":"stopped" if stopped else "stop-timeout","mode":r.get("mode")}

def warp_status():
    cli=executable("warp-cli")
    if not cli:return {"ok":False,"error":"warp-cli missing"}
    p=run([cli,"--accept-tos","status"],12)
    return {"ok":p.returncode==0,"text":(p.stdout+p.stderr).strip(),"returncode":p.returncode}

def _warp_registration_ready():
    cli=executable("warp-cli")
    if not cli:return {"ok":False,"error":"warp-cli missing"}
    p=run([cli,"--accept-tos","registration","show"],12)
    if p.returncode==0:return {"ok":True,"state":"existing","text":(p.stdout+p.stderr).strip()}
    p=run([cli,"--accept-tos","registration","new"],25)
    if p.returncode!=0:return {"ok":False,"error":"registration failed or timed out","detail":(p.stdout+p.stderr).strip(),"returncode":p.returncode}
    return {"ok":True,"state":"created","text":(p.stdout+p.stderr).strip()}

def _start_warp_guard():
    guard=STATE/"warp_guard.py"
    if not guard.exists():return {"ok":False,"error":"warp guard missing"}
    token=uuid.uuid4().hex
    keep=STATE/f"warp_keep_{token}.ok"
    log=STATE/f"warp_guard_{token}.log"
    subprocess.Popen([shutil.which("python3") or "python3",str(guard),token,str(WARP_GUARD_SECONDS),str(keep),str(log)],
                     stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                     start_new_session=True,close_fds=True)
    return {"ok":True,"token":token,"keep":str(keep),"seconds":WARP_GUARD_SECONDS}

def warp_connect():
    cli=executable("warp-cli")
    if not cli:return {"ok":False,"error":"warp-cli missing"}
    reg=_warp_registration_ready()
    if not reg.get("ok"):return {"ok":False,"stage":"registration","registration":reg}
    guard=_start_warp_guard()
    if not guard.get("ok"):return {"ok":False,"stage":"guard","error":guard.get("error")}
    p=run([cli,"--accept-tos","connect"],20)
    if p.returncode:
        return {"ok":False,"stage":"connect","error":(p.stdout+p.stderr).strip(),"guard":guard}
    last={}
    for _ in range(15):
        time.sleep(1)
        last=trace(timeout=8)
        if last.get("ok") and (last.get("trace") or {}).get("warp")=="on":
            return {"ok":True,"state":"trial-connected","warp":"on","trace":last,"guard":guard,
                    "message":f"WARP is in a {WARP_GUARD_SECONDS}s safe trial. Keep only after external connectivity is confirmed."}
    return {"ok":False,"stage":"e2e","error":"trace did not show warp=on; guard will auto-disconnect","trace":last,"guard":guard}

def warp_keep(token:str):
    cli=executable("warp-cli")
    if not cli:return {"ok":False,"error":"warp-cli missing"}
    t=trace(timeout=10)
    if not (t.get("ok") and (t.get("trace") or {}).get("warp")=="on"):
        return {"ok":False,"error":"WARP is not end-to-end connected","trace":t}
    keep=STATE/f"warp_keep_{token}.ok"
    keep.write_text("confirmed\n",encoding="utf-8")
    return {"ok":True,"state":"persistent","warp":"on","trace":t,"token":token}

def warp_disconnect():
    cli=executable("warp-cli")
    if not cli:return {"ok":False,"error":"warp-cli missing"}
    p=run([cli,"--accept-tos","disconnect"],20)
    time.sleep(1);t=trace(timeout=10)
    return {"ok":bool(p.returncode==0 and t.get("ok") and (t.get("trace") or {}).get("warp")!="on"),
            "text":(p.stdout+p.stderr).strip(),"trace":t}

def tk_main():
    import tkinter as tk
    from tkinter import ttk, messagebox
    class UI(tk.Tk):
        def __init__(self):
            super().__init__();self.title(f"{APP} {VERSION}");self.geometry("980x640");self.minsize(780,500);self.configure(bg="#0b1423");self.pending_token=None
            style=ttk.Style(self)
            try:style.theme_use("clam")
            except Exception:pass
            style.configure("TFrame",background="#0b1423");style.configure("TLabel",background="#0b1423",foreground="#ecf2fa",font=("Sans",11));style.configure("Title.TLabel",background="#0b1423",foreground="#ecf2fa",font=("Sans",24,"bold"));style.configure("TButton",padding=9)
            top=ttk.Frame(self);top.pack(fill="x",padx=22,pady=(22,10));ttk.Label(top,text="FreeNet Hub",style="Title.TLabel").pack(side="left");ttk.Label(top,text="Linux · explicit connection only · safe WARP trial").pack(side="right")
            self.status=tk.StringVar(value="Ready — choose an action explicitly.");ttk.Label(self,textvariable=self.status,wraplength=900).pack(fill="x",padx=22,pady=8)
            row=ttk.Frame(self);row.pack(fill="x",padx=22,pady=10)
            actions=[("Direct status",lambda:trace()),("Tor status",tor_status),("Start Tor",start_tor),("Stop Tor",stop_tor),("WARP status",warp_status),("Connect WARP",self.confirm_warp),("Keep WARP",self.keep_warp),("Disconnect WARP",warp_disconnect)]
            for name,fn in actions:ttk.Button(row,text=name,command=lambda f=fn:self.bg(f)).pack(side="left",padx=3)
            self.log=tk.Text(self,bg="#132135",fg="#ecf2fa",insertbackground="white",relief="flat",font=("Consolas",10));self.log.pack(fill="both",expand=True,padx=22,pady=(6,22))
            self.write({"version":VERSION,"warp_cli":exists("warp-cli"),"tor":exists("tor"),"obfs4proxy":exists("obfs4proxy"),"owned_tor":bool(owner())})
        def write(self,x):self.log.insert("end",json.dumps(x,ensure_ascii=False,indent=2)+"\n\n");self.log.see("end")
        def bg(self,fn):
            def work():
                try:r=fn()
                except Exception as e:r={"ok":False,"error":repr(e)}
                if r.get("guard",{}).get("token"):self.pending_token=r["guard"]["token"]
                self.after(0,lambda:(self.write(r),self.status.set("PASS" if r.get("ok") else "Needs attention")))
            threading.Thread(target=work,daemon=True).start()
        def confirm_warp(self):
            if not messagebox.askyesno(APP,f"Connect WARP as a {WARP_GUARD_SECONDS}-second safe trial? It auto-disconnects unless you confirm Keep WARP."):return {"ok":False,"error":"cancelled"}
            return warp_connect()
        def keep_warp(self):
            if not self.pending_token:return {"ok":False,"error":"no pending safe-trial token"}
            return warp_keep(self.pending_token)
    STATE.mkdir(parents=True,exist_ok=True);UI().mainloop()

if __name__=="__main__":tk_main()
