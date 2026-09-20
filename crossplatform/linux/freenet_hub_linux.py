#!/usr/bin/env python3
from __future__ import annotations
import json, os, pathlib, shutil, signal, socket, subprocess, threading, time
import tkinter as tk
from tkinter import ttk, messagebox
APP="FreeNet Hub";VERSION="4.1.2"
STATE=pathlib.Path.home()/".local"/"share"/"FreeNetHub";TOR_STATE=STATE/"tor";OWNER=TOR_STATE/"owner.json";SOCKS_PORT=9909
def exists(name): return shutil.which(name) is not None
def run(args,timeout=20): return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
def trace(proxy=None,timeout=15):
    if not exists("curl"): return {"ok":False,"error":"curl missing"}
    args=["curl","-4","--max-time",str(timeout),"-fsS"]
    if proxy: args+=["--proxy",proxy]
    args+=["https://www.cloudflare.com/cdn-cgi/trace"];p=run(args,timeout+3)
    if p.returncode:return {"ok":False,"error":(p.stderr or p.stdout).strip()}
    d={}
    for line in p.stdout.splitlines():
        if "=" in line:k,v=line.split("=",1);d[k]=v
    return {"ok":True,"trace":d}
def identity(pid:int):
    try:
        proc=pathlib.Path(f"/proc/{pid}");return {"pid":pid,"exe":os.readlink(proc/"exe"),"start":(proc/"stat").read_text().split()[21]}
    except Exception:return None
def owner():
    try:
        r=json.loads(OWNER.read_text());cur=identity(int(r["pid"]))
        if cur and all(str(cur[k])==str(r[k]) for k in ("pid","exe","start")):return r
    except Exception:pass
    return None
def start_tor():
    if owner():return {"ok":True,"state":"already-running","proxy":f"socks5h://127.0.0.1:{SOCKS_PORT}"}
    if not exists("tor"):return {"ok":False,"error":"tor executable missing"}
    TOR_STATE.mkdir(parents=True,exist_ok=True);data=TOR_STATE/"data";data.mkdir(exist_ok=True);log=open(TOR_STATE/"tor.log","ab",buffering=0)
    p=subprocess.Popen(["tor","--SocksPort",f"127.0.0.1:{SOCKS_PORT}","--DataDirectory",str(data),"--AvoidDiskWrites","1"],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
    for _ in range(100):
        if p.poll() is not None:return {"ok":False,"error":"tor exited during startup"}
        try:
            with socket.create_connection(("127.0.0.1",SOCKS_PORT),timeout=.2):
                ident=identity(p.pid)
                if ident:OWNER.write_text(json.dumps(ident|{"started":time.time()},indent=2))
                return {"ok":True,"state":"running","proxy":f"socks5h://127.0.0.1:{SOCKS_PORT}"}
        except OSError:time.sleep(.25)
    try:os.killpg(p.pid,signal.SIGTERM)
    except Exception:pass
    return {"ok":False,"error":"tor SOCKS listener timeout"}
def stop_tor():
    r=owner()
    if not r:return {"ok":True,"state":"not-owned"}
    try:
        os.kill(int(r["pid"]),signal.SIGTERM)
        for _ in range(40):
            if identity(int(r["pid"])) is None:break
            time.sleep(.1)
        stopped=identity(int(r["pid"])) is None
        return {"ok":stopped,"state":"stopped" if stopped else "stop-timeout"}
    except Exception as e:return {"ok":False,"error":str(e)}
def warp_status():
    if not exists("warp-cli"):return {"ok":False,"error":"warp-cli missing"}
    p=run(["warp-cli","status"],15);return {"ok":p.returncode==0,"text":(p.stdout+p.stderr).strip()}
def warp_connect():
    if not exists("warp-cli"):return {"ok":False,"error":"warp-cli missing"}
    p=run(["warp-cli","connect"],25)
    if p.returncode:return {"ok":False,"error":(p.stdout+p.stderr).strip()}
    time.sleep(2);t=trace();w=(t.get("trace") or {}).get("warp")
    return {"ok":bool(t.get("ok") and w=="on"),"warp":w,"trace":t}
def warp_disconnect():
    if not exists("warp-cli"):return {"ok":False,"error":"warp-cli missing"}
    p=run(["warp-cli","disconnect"],25);return {"ok":p.returncode==0,"text":(p.stdout+p.stderr).strip()}
class UI(tk.Tk):
    def __init__(self):
        super().__init__();self.title(f"{APP} {VERSION}");self.geometry("880x580");self.minsize(720,480);self.configure(bg="#0b1423")
        style=ttk.Style(self)
        try:style.theme_use("clam")
        except Exception:pass
        style.configure("TFrame",background="#0b1423");style.configure("TLabel",background="#0b1423",foreground="#ecf2fa",font=("Sans",11));style.configure("Title.TLabel",background="#0b1423",foreground="#ecf2fa",font=("Sans",24,"bold"));style.configure("TButton",padding=9)
        top=ttk.Frame(self);top.pack(fill="x",padx=22,pady=(22,10));ttk.Label(top,text="FreeNet Hub",style="Title.TLabel").pack(side="left");ttk.Label(top,text="Linux - no network change on launch").pack(side="right")
        self.status=tk.StringVar(value="Ready - choose an action explicitly.");ttk.Label(self,textvariable=self.status,wraplength=800).pack(fill="x",padx=22,pady=8)
        row=ttk.Frame(self);row.pack(fill="x",padx=22,pady=10)
        actions=[("Direct status",lambda:trace()),("WARP status",warp_status),("Connect WARP",self.confirm_warp),("Disconnect WARP",warp_disconnect),("Start Tor",start_tor),("Stop Tor",stop_tor),("Tor HTTPS",lambda:trace(f"socks5h://127.0.0.1:{SOCKS_PORT}"))]
        for name,fn in actions:ttk.Button(row,text=name,command=lambda f=fn:self.bg(f)).pack(side="left",padx=3)
        self.log=tk.Text(self,bg="#132135",fg="#ecf2fa",insertbackground="white",relief="flat",font=("Consolas",10));self.log.pack(fill="both",expand=True,padx=22,pady=(6,22));self.write({"version":VERSION,"warp_cli":exists("warp-cli"),"tor":exists("tor"),"curl":exists("curl"),"owned_tor":bool(owner())})
    def write(self,x):self.log.insert("end",json.dumps(x,ensure_ascii=False,indent=2)+"\n\n");self.log.see("end")
    def bg(self,fn):
        def work():
            try:r=fn()
            except Exception as e:r={"ok":False,"error":repr(e)}
            self.after(0,lambda:(self.write(r),self.status.set("PASS" if r.get("ok") else "Needs attention")))
        threading.Thread(target=work,daemon=True).start()
    def confirm_warp(self):
        if not messagebox.askyesno(APP,"Connect official Cloudflare WARP system-wide now?"):return {"ok":False,"error":"cancelled"}
        return warp_connect()
if __name__=="__main__":STATE.mkdir(parents=True,exist_ok=True);UI().mainloop()
