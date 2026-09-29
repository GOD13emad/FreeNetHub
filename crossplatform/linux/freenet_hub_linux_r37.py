#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import importlib.util
import ipaddress
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import freenet_hub_linux as legacy
import nodehub_shared as NH

VERSION = "4.2.0-linux.12-r38"
STATE = legacy.STATE
SETTINGS_PATH = STATE / "settings-r37.json"
NODE_STORE_PATH = STATE / "nodes.json"
NODE_RUNTIME = STATE / "node"
NODE_OWNER = NODE_RUNTIME / "owner.json"
NODE_CONFIG = NODE_RUNTIME / "config.json"
NODE_PORT = 19460
SINGBOX_BIN = STATE / "runtime" / "usr" / "bin" / "sing-box"
SINGBOX_PIN = STATE / "runtime" / "sing-box.pin.json"
WARPPLUS_BIN = STATE / "runtime" / "usr" / "bin" / "warp-plus"
WARPPLUS_PIN = STATE / "runtime" / "warp-plus.pin.json"
WARPPLUS_RUNTIME = STATE / "warpplus"
WARPPLUS_PORTS = {"WARP":19410,"GOOL":19413,"CFON":19414}
WARPPLUS_ENDPOINTS = {"WARP":"162.159.192.165:987","GOOL":"188.114.98.35:1010","CFON":"188.114.98.15:8854"}
PUBLIC_REFRESH = STATE / "node_public_refresh.json"
BASE_ROUTE = STATE / "base_route.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "showIp": False,
    "country": "AUTO",
    "home": "https://www.youtube.com/",
    "testPathMode": "BASE",
    "pingTimeoutSec": 10,
    "downloadTimeoutSec": 30,
    "uploadTimeoutSec": 30,
    "monitor": False,
    "autoRepair": False,
    "customProxy": "",
}
ALLOWED_COUNTRIES = ("AUTO","AT","DE","NL","US","CA","GB","FR","SG","JP")
PUBLIC_NODE_SOURCES = (
    ("AURX_HTTP_VERIFIED","https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt"),
    ("MORPHEUS_BEST","https://raw.githubusercontent.com/morpheusadam/v2ray-config/main/subs/bundles/best.txt"),
    ("V2CROSS_PAGE","https://v2cross.com/en/free-v2ray-nodes/"),
    ("SHADOWSHARE_SUB_EN","https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_en"),
    ("SHADOWSHARE_SUB_DE","https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_de"),
    ("SHADOWSHARE_SUB_FR","https://raw.githubusercontent.com/Pawdroid/Free-servers/main/static/sub_fr"),
    ("RADIKAL_TOP100","https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/main/top100.txt"),
    ("MATIN_SUB1","https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/subs/sub1.txt"),
)

def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def _atomic(path: pathlib.Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

def _load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def settings():
    raw = _load(SETTINGS_PATH, {})
    out = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        out.update(raw)
    out["theme"] = out["theme"] if out["theme"] in ("dark","light") else "dark"
    out["country"] = out["country"] if out["country"] in ALLOWED_COUNTRIES else "AUTO"
    out["testPathMode"] = out["testPathMode"] if out["testPathMode"] in ("BASE","SELECTED") else "BASE"
    for key, lo, hi, default in (
        ("pingTimeoutSec",3,30,10),
        ("downloadTimeoutSec",10,120,30),
        ("uploadTimeoutSec",10,120,30),
    ):
        try:
            out[key] = max(lo, min(hi, int(out.get(key, default))))
        except Exception:
            out[key] = default
    return out

def save_settings(patch):
    out = settings()
    if not isinstance(patch, dict):
        raise ValueError("SETTINGS_PATCH_INVALID")
    out.update(patch)
    if out.get("country") not in ALLOWED_COUNTRIES:
        raise ValueError("COUNTRY_INVALID")
    if out.get("theme") not in ("dark","light"):
        raise ValueError("THEME_INVALID")
    if out.get("testPathMode") not in ("BASE","SELECTED"):
        raise ValueError("TEST_PATH_INVALID")
    cp = str(out.get("customProxy") or "").strip()
    if cp:
        u = urllib.parse.urlparse(cp)
        if u.scheme not in ("socks5h","socks5","http") or not u.hostname or not u.port:
            raise ValueError("CUSTOM_PROXY_INVALID")
    _atomic(SETTINGS_PATH, out)
    return {"ok": True, "settings": out}

def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().lower()

def singbox_status():
    if not SINGBOX_BIN.is_file():
        return {"ok": False, "installed": False, "error": "SINGBOX_NOT_PROVISIONED"}
    pin = _load(SINGBOX_PIN, {})
    got = _sha256(SINGBOX_BIN)
    expected = str(pin.get("binarySha256") or "").lower()
    if expected and got != expected:
        return {"ok": False, "installed": True, "error": "SINGBOX_INTEGRITY_FAIL", "sha256": got}
    p = legacy.run([str(SINGBOX_BIN), "version"], 8)
    return {"ok": p.returncode == 0, "installed": True, "sha256": got, "version": (p.stdout+p.stderr).splitlines()[:2]}

def warpplus_status():
    if not WARPPLUS_BIN.is_file():
        return {"ok":False,"installed":False,"error":"WARPPLUS_NOT_PROVISIONED"}
    pin=_load(WARPPLUS_PIN,{})
    got=_sha256(WARPPLUS_BIN)
    expected=str(pin.get("binarySha256") or "").lower()
    if not expected or got!=expected:
        return {"ok":False,"installed":True,"error":"WARPPLUS_INTEGRITY_FAIL","sha256":got}
    p=legacy.run([str(WARPPLUS_BIN),"-h"],8)
    return {"ok":p.returncode==0,"installed":True,"version":pin.get("version"),"sha256":got,"asset":pin.get("asset")}

def _warpplus_owner(mode):
    mode=str(mode or "").upper()
    rec=_load(WARPPLUS_RUNTIME/mode/"owner.json",{})
    if not rec:return None
    try:
        ident=legacy.identity(int(rec["pid"]))
        if not ident:return None
        if str(ident.get("exe"))!=str(rec.get("exe")) or str(ident.get("start"))!=str(rec.get("start")):return None
        if str(rec.get("mode"))!=mode:return None
        return rec
    except Exception:return None

def _warpplus_stop(mode):
    mode=str(mode or "").upper()
    if mode not in WARPPLUS_PORTS:return {"ok":False,"error":"WARPPLUS_MODE_INVALID"}
    owner=_warpplus_owner(mode);port=WARPPLUS_PORTS[mode]
    if not owner:
        if _port_open(port):return {"ok":False,"error":"WARPPLUS_PORT_FOREIGN_OR_UNPROVEN","mode":mode}
        try:(WARPPLUS_RUNTIME/mode/"owner.json").unlink(missing_ok=True)
        except OSError:pass
        return {"ok":True,"state":"not-owned","mode":mode}
    ok=legacy.stop_pid(int(owner["pid"]))
    if ok:
        try:(WARPPLUS_RUNTIME/mode/"owner.json").unlink(missing_ok=True)
        except OSError:pass
        cur=legacy.session()
        if (mode=="WARP" and cur.get("mode")=="WARP_PROXY") or cur.get("mode")==mode:legacy.set_session()
    return {"ok":ok,"state":"stopped" if ok else "stop-timeout","mode":mode}

def _warpplus_stop_all(except_mode=None):
    out={}
    for mode in WARPPLUS_PORTS:
        if mode==except_mode:continue
        out[mode]=_warpplus_stop(mode)
    return {"ok":all(x.get("ok") for x in out.values()),"results":out}

def _warpplus_proxy(mode):
    return f"socks5h://127.0.0.1:{WARPPLUS_PORTS[str(mode).upper()]}"

def warpplus_verify(mode):
    mode=str(mode or "").upper();owner=_warpplus_owner(mode)
    if not owner or not _port_open(WARPPLUS_PORTS.get(mode,0)):return {"ok":False,"error":"WARPPLUS_NOT_CONNECTED","mode":mode}
    out=_bench(_warpplus_proxy(mode),True);out.update(mode=mode,scope="BROWSER",provider="warp-plus")
    if mode=="CFON":
        target=str(owner.get("country") or "")
        if target and str(out.get("country") or "").upper()!=target:
            out["ok"]=False;out["error"]="CFON_COUNTRY_MISMATCH";out["expectedCountry"]=target
    if mode in ("WARP","GOOL") and str(out.get("warp") or "").lower()!="on":
        out["ok"]=False;out["error"]="WARPPLUS_WARP_NOT_ON"
    return out

def warpplus_start(mode):
    mode=str(mode or "").upper()
    if mode not in WARPPLUS_PORTS:return {"ok":False,"error":"WARPPLUS_MODE_INVALID","mode":mode}
    st=warpplus_status()
    if not st.get("ok"):return {"ok":False,"error":st.get("error","WARPPLUS_NOT_READY"),"mode":mode}
    current=_warpplus_owner(mode)
    if current and _port_open(WARPPLUS_PORTS[mode]):return warpplus_verify(mode)
    if _port_open(WARPPLUS_PORTS[mode]):return {"ok":False,"error":"WARPPLUS_PORT_FOREIGN_OR_UNPROVEN","mode":mode}
    _warpplus_stop_all(except_mode=mode);node_stop();legacy.stop_tor()
    data=WARPPLUS_RUNTIME/mode;cache=data/"cache";data.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    args=[str(WARPPLUS_BIN),"-4","--bind",f"127.0.0.1:{WARPPLUS_PORTS[mode]}","--cache-dir",str(cache),"--dns","1.1.1.1","--test-url","https://www.cloudflare.com/","--endpoint",WARPPLUS_ENDPOINTS[mode]]
    country=""
    if mode=="GOOL":args+=["--gool"]
    elif mode=="CFON":
        country=str(settings().get("country") or "AUTO").upper()
        if country=="AUTO":country="AT"
        args+=["--cfon","--country",country]
    log=open(data/"warp-plus.log","ab",buffering=0)
    p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
    deadline=time.time()+(45 if mode=="CFON" else 25)
    while time.time()<deadline and not _port_open(WARPPLUS_PORTS[mode]):
        if p.poll() is not None:break
        time.sleep(.25)
    if not _port_open(WARPPLUS_PORTS[mode]):
        try:legacy.stop_pid(p.pid)
        except Exception:pass
        return {"ok":False,"error":"WARPPLUS_PROXY_START_FAILED","mode":mode,"exit":p.poll()}
    ident=legacy.identity(p.pid)
    if not ident:
        legacy.stop_pid(p.pid);return {"ok":False,"error":"WARPPLUS_IDENTITY_FAIL","mode":mode}
    rec={**ident,"mode":mode,"country":country,"started":_now(),"port":WARPPLUS_PORTS[mode]}
    _atomic(data/"owner.json",rec)
    legacy.set_session("WARP_PROXY" if mode=="WARP" else mode,"warp-plus",{"scope":"BROWSER","method":mode,"country":country})
    result={}
    ready_deadline=time.time()+(30 if mode=="CFON" else 12)
    while time.time()<ready_deadline:
        result=warpplus_verify(mode)
        if result.get("ok"):break
        if result.get("error") not in ("PING_OR_TRACE_FAILED","CFON_COUNTRY_MISMATCH","WARPPLUS_WARP_NOT_ON"):break
        time.sleep(1)
    if not result.get("ok"):_warpplus_stop(mode)
    return result

def benchmark_warpplus(mode,ping_only=False):
    mode=str(mode or "").upper();pre=_warpplus_owner(mode);temp=not bool(pre and _port_open(WARPPLUS_PORTS.get(mode,0)))
    if temp:
        r=warpplus_start(mode)
        if not r.get("ok"):return r
    try:
        out=_bench(_warpplus_proxy(mode),ping_only);out.update(mode=mode,scope="BROWSER",provider="warp-plus",temporary=temp)
        if mode=="CFON":
            target=str((_warpplus_owner(mode) or {}).get("country") or "")
            if target and str(out.get("country") or "").upper()!=target:
                out["ok"]=False;out["error"]="CFON_COUNTRY_MISMATCH";out["expectedCountry"]=target
        if mode in ("WARP","GOOL") and str(out.get("warp") or "").lower()!="on":
            out["ok"]=False;out["error"]="WARPPLUS_WARP_NOT_ON"
        return out
    finally:
        if temp:_warpplus_stop(mode)

def _route_snapshot():
    p = legacy.run(["ip","route","get","1.1.1.1"], 5)
    text = (p.stdout + p.stderr).strip()
    m_dev = re.search(r"\bdev\s+(\S+)", text)
    m_src = re.search(r"\bsrc\s+([0-9a-fA-F:.]+)", text)
    return {"raw": text, "interface": m_dev.group(1) if m_dev else "", "source": m_src.group(1) if m_src else ""}

def remember_base_route():
    snap = _route_snapshot()
    snap["checked"] = _now()
    _atomic(BASE_ROUTE, snap)
    return snap

def base_route():
    return _load(BASE_ROUTE, {}) or _route_snapshot()

def _proxy_args(proxy):
    return ["--proxy", proxy] if proxy else []

def _curl(url, timeout=15, proxy=None, body=True, interface=None):
    curl = legacy.executable("curl") or "curl"
    fmt = "%{http_code}\t%{time_total}\t%{speed_download}\t%{speed_upload}\t%{size_download}"
    args = [curl, "-4", "--max-time", str(int(timeout)), "-L", "-sS"]
    if not body:
        args += ["-o", "/dev/null"]
    if proxy:
        args += _proxy_args(proxy)
    if interface:
        args += ["--interface", interface]
    args += ["-w", "\n__FNH__"+fmt, url]
    p = legacy.run(args, int(timeout)+5)
    out = p.stdout or ""
    marker = out.rfind("\n__FNH__")
    body_text = out[:marker] if marker >= 0 else ""
    meta = out[marker+8:].strip().split("\t") if marker >= 0 else []
    return {
        "exit": p.returncode,
        "code": meta[0] if len(meta)>0 else "000",
        "seconds": float(meta[1]) if len(meta)>1 and meta[1] else None,
        "speedDown": float(meta[2]) if len(meta)>2 and meta[2] else 0.0,
        "speedUp": float(meta[3]) if len(meta)>3 and meta[3] else 0.0,
        "bytes": int(float(meta[4])) if len(meta)>4 and meta[4] else 0,
        "body": body_text,
        "error": (p.stderr or "").strip(),
    }

def _trace(proxy=None, interface=None, timeout=12):
    r = _curl("https://www.cloudflare.com/cdn-cgi/trace", timeout, proxy, True, interface)
    d = {}
    if r["exit"] == 0 and r["code"] == "200":
        for line in r["body"].splitlines():
            if "=" in line:
                k,v = line.split("=",1)
                d[k] = v.strip()
    return r,d

def _upload(proxy=None, timeout=30, bytes_count=350000, interface=None):
    curl = legacy.executable("curl") or "curl"
    fd, name = tempfile.mkstemp(prefix="fnh-upload-", suffix=".bin")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(b"0" * int(bytes_count))
        fmt = "%{http_code}\t%{time_total}\t%{speed_upload}"
        args = [curl,"-4","--max-time",str(int(timeout)),"-sS","-o","/dev/null"]
        if proxy:
            args += _proxy_args(proxy)
        if interface:
            args += ["--interface", interface]
        args += ["--data-binary","@"+name,"-w",fmt,f"https://speed.cloudflare.com/__up?bytes={int(bytes_count)}"]
        p = legacy.run(args, int(timeout)+5)
        parts=(p.stdout or "").strip().split("\t")
        return {
            "exit":p.returncode,
            "code":parts[0] if parts else "000",
            "seconds":float(parts[1]) if len(parts)>1 and parts[1] else None,
            "speed":float(parts[2]) if len(parts)>2 and parts[2] else 0.0,
            "error":(p.stderr or "").strip(),
        }
    finally:
        try: os.unlink(name)
        except OSError: pass

def _bench(proxy=None, ping_only=False, interface=None):
    s = settings()
    tr, trace = _trace(proxy, interface, s["pingTimeoutSec"])
    ping = _curl("https://www.youtube.com/generate_204", s["pingTimeoutSec"], proxy, False, interface)
    trace_ok = tr["exit"]==0 and tr["code"]=="200" and bool(trace)
    youtube_ok = ping["exit"]==0 and ping["code"] in ("200","204")
    latency = ping if youtube_ok else tr
    result = {
        "ok": trace_ok,
        "pingMs": round((latency.get("seconds") or 0)*1000,1) if latency.get("seconds") is not None else None,
        "downloadMbps": None,
        "uploadMbps": None,
        "country": trace.get("loc",""),
        "exitIp": trace.get("ip",""),
        "warp": trace.get("warp",""),
        "checked": _now(),
        "proxyUsed": bool(proxy),
        "interface": interface or "",
        "youtubeReachable": youtube_ok,
        "error": "" if trace_ok else "TRACE_FAILED",
    }
    if ping_only or not trace_ok:
        return result
    down = _curl("https://speed.cloudflare.com/__down?bytes=2000000", s["downloadTimeoutSec"], proxy, False, interface)
    upload_bytes = 100000 if proxy else 350000
    up = _upload(proxy, s["uploadTimeoutSec"], upload_bytes, interface)
    down_ok = down["exit"]==0 and down["code"]=="200" and down["speedDown"]>0
    up_ok = up["exit"]==0 and up["code"]=="200" and up["speed"]>0
    result["downloadMbps"] = round(down["speedDown"]*8/1e6,2) if down_ok else None
    result["uploadMbps"] = round(up["speed"]*8/1e6,2) if up_ok else None
    result["ok"] = bool(trace_ok and down_ok and up_ok)
    if not result["ok"]:
        result["error"] = "THROUGHPUT_INCOMPLETE"
    return result

def physical_base_route():
    p=legacy.run(["ip","route","show","default"],5)
    candidates=[]
    for line in (p.stdout or "").splitlines():
        m=re.search(r"\bdev\s+(\S+)",line)
        if not m:continue
        dev=m.group(1)
        hw=(pathlib.Path("/sys/class/net")/dev/"device").exists()
        virtual=bool(re.match(r"^(tun|tap|wg|warp|tailscale|zt|docker|br-|veth)",dev,re.I))
        metric=re.search(r"\bmetric\s+(\d+)",line)
        candidates.append((0 if hw and not virtual else 1,int(metric.group(1)) if metric else 999999,dev,line))
    if not candidates:return {"interface":"","raw":"","proof":"NO_DEFAULT_ROUTE"}
    candidates.sort()
    _,_,dev,line=candidates[0]
    return {"interface":dev,"raw":line,"proof":"PHYSICAL_DEFAULT_ROUTE" if (pathlib.Path("/sys/class/net")/dev/"device").exists() else "BEST_NON_TUN_DEFAULT_ROUTE"}

def benchmark_direct(ping_only=False):
    s=settings();base=physical_base_route();iface=base.get("interface") or None
    tr,trace=_trace(None,iface,s["pingTimeoutSec"])
    ok=bool(tr["exit"]==0 and tr["code"]=="200" and trace)
    out={"ok":ok,"pingMs":round((tr.get("seconds") or 0)*1000,1) if tr.get("seconds") is not None else None,
         "downloadMbps":None,"uploadMbps":None,"country":trace.get("loc",""),"exitIp":trace.get("ip",""),"warp":trace.get("warp",""),
         "checked":_now(),"proxyUsed":False,"interface":iface or "","error":"" if ok else "DIRECT_TRACE_FAILED",
         "mode":"DIRECT","path":"PHYSICAL_BASE_INTERFACE","routeProof":base.get("proof"),"route":base.get("raw")}
    if ping_only or not ok:return out
    down=_curl("https://speed.cloudflare.com/__down?bytes=2000000",s["downloadTimeoutSec"],None,False,iface)
    up=_upload(None,s["uploadTimeoutSec"],350000,iface)
    down_ok=down["exit"]==0 and down["code"]=="200" and down["speedDown"]>0
    up_ok=up["exit"]==0 and up["code"]=="200" and up["speed"]>0
    out["downloadMbps"]=round(down["speedDown"]*8/1e6,2) if down_ok else None
    out["uploadMbps"]=round(up["speed"]*8/1e6,2) if up_ok else None
    out["ok"]=bool(ok and down_ok and up_ok)
    if not out["ok"]:out["error"]="DIRECT_THROUGHPUT_INCOMPLETE"
    return out

def node_store():
    x = _load(NODE_STORE_PATH, {"schema":1,"selected":"","nodes":[]})
    nodes = x.get("nodes",[]) if isinstance(x,dict) and isinstance(x.get("nodes"),list) else []
    return {"schema":1,"selected":str(x.get("selected") or "") if isinstance(x,dict) else "","nodes":nodes[:NH.MAX_NODES]}

def save_node_store(store):
    _atomic(NODE_STORE_PATH, {"schema":1,"selected":str(store.get("selected") or ""),"nodes":list(store.get("nodes") or [])[:NH.MAX_NODES]})

def node_rows():
    s = node_store()
    def key(n):
        ep=n.get("endpoint_test") if isinstance(n.get("endpoint_test"),dict) else {}
        perf=n.get("performance_test") if isinstance(n.get("performance_test"),dict) else {}
        source=str(n.get("source") or "")
        source_rank=0 if source=="AURX_HTTP_VERIFIED" else 1 if source=="MORPHEUS_BEST" else 2
        return (0 if n.get("pinned") else 1,0 if n.get("favorite") else 1,0 if ep.get("reachable") else 1,source_rank,float(ep.get("latency_ms") or 999999),-(float(perf.get("downloadMbps") or 0)),str(n.get("name") or "").lower())
    return [NH.public_node(n) for n in sorted(s["nodes"],key=key)]

def selected_node():
    s=node_store(); sid=s.get("selected")
    return next((n for n in s["nodes"] if n.get("id")==sid),None)

def node_select(node_id):
    s=node_store()
    if not any(n.get("id")==node_id for n in s["nodes"]):
        raise ValueError("NODE_NOT_FOUND")
    s["selected"]=node_id; save_node_store(s)
    return {"ok":True,"selected":node_id}

def node_import_text(text, source="manual"):
    parsed=NH.parse_blob(str(text),source)
    s=node_store(); s["nodes"]=NH.merge(s["nodes"],parsed["nodes"])
    if not s.get("selected") and s["nodes"]:
        s["selected"]=s["nodes"][0]["id"]
    save_node_store(s)
    return {"ok":True,"imported":len(parsed["nodes"]),"total":len(s["nodes"]),"errors":parsed["errors"],"selected":s.get("selected")}

def node_import_file(path):
    p=pathlib.Path(path)
    if not p.is_file() or p.stat().st_size > NH.MAX_NODE_TEXT:
        raise ValueError("NODE_FILE_INVALID")
    return node_import_text(p.read_text(encoding="utf-8",errors="replace"), "file")

def node_import_url(url):
    u=urllib.parse.urlparse(str(url).strip())
    if u.scheme!="https" or not u.hostname or u.username or u.password:
        raise ValueError("NODE_SUBSCRIPTION_HTTPS_REQUIRED")
    req=urllib.request.Request(url,headers={"User-Agent":"FreeNetHub-Linux-R37/1"})
    with urllib.request.urlopen(req,timeout=20) as resp:
        raw=resp.read(NH.MAX_NODE_TEXT+1)
    if len(raw)>NH.MAX_NODE_TEXT:
        raise ValueError("NODE_INPUT_TOO_LARGE")
    return node_import_text(raw.decode("utf-8",errors="replace"), "subscription")

def _fetch_source(item):
    name,url=item
    req=urllib.request.Request(url,headers={"User-Agent":"FreeNetHub-Linux-R37/1"})
    try:
        with urllib.request.urlopen(req,timeout=20) as resp:
            raw=resp.read(NH.MAX_NODE_TEXT+1)
        if len(raw)>NH.MAX_NODE_TEXT:
            return name,[],["NODE_INPUT_TOO_LARGE"]
        p=NH.parse_blob(raw.decode("utf-8",errors="replace"),name)
        return name,p["nodes"],p["errors"]
    except Exception as e:
        return name,[],[type(e).__name__+":"+str(e)[:140]]

def node_refresh_public():
    incoming=[]; ok=[]; failed=[]; stats=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8,len(PUBLIC_NODE_SOURCES))) as ex:
        futs=[ex.submit(_fetch_source,x) for x in PUBLIC_NODE_SOURCES]
        for f in concurrent.futures.as_completed(futs):
            name,nodes,errors=f.result()
            if nodes:
                incoming.extend(nodes); ok.append(name); stats.append({"name":name,"status":"PASS","found":len(nodes),"errors":len(errors)})
            else:
                failed.append(name); stats.append({"name":name,"status":"FAIL","found":0,"errors":errors[:3]})
    if not ok:
        return {"ok":False,"error":"PUBLIC_NODE_SOURCE_UNREACHABLE","failedSources":failed}
    s=node_store()
    source_names={x[0] for x in PUBLIC_NODE_SOURCES}
    preserved=[n for n in s["nodes"] if str(n.get("source") or "") not in source_names or n.get("favorite") or n.get("pinned")]
    merged=NH.merge(preserved,incoming)
    selected=s.get("selected")
    if not any(n.get("id")==selected for n in merged):
        selected=merged[0]["id"] if merged else ""
    save_node_store({"schema":1,"selected":selected,"nodes":merged})
    rec={"schema":1,"status":"PASS","checkedUtc":_now(),"sources":ok,"failedSources":failed,"parsedRaw":len(incoming),"total":len(merged),"endpointTest":"DEFERRED_TO_NODE_TEST_ALL","sourceStats":stats}
    _atomic(PUBLIC_REFRESH,rec)
    return {"ok":True,"refreshed":True,**rec}

def _endpoint_probe(n, timeout=1.5):
    if str(n.get("protocol") or "").lower()=="hysteria2":
        return {"reachable":None,"latency_ms":None,"checked":_now(),"type":"UDP_QUIC_PREFLIGHT"}
    started=time.monotonic()
    try:
        with socket.create_connection((str(n.get("server") or ""),int(n.get("port") or 0)),timeout=timeout):
            pass
        return {"reachable":True,"latency_ms":round((time.monotonic()-started)*1000,1),"checked":_now(),"type":"TCP_ENDPOINT_ONLY"}
    except Exception:
        return {"reachable":False,"latency_ms":None,"checked":_now(),"type":"TCP_ENDPOINT_ONLY"}

def node_test_all():
    s=node_store()
    if not s["nodes"]:
        return {"ok":False,"error":"NODE_POOL_EMPTY","total":0}
    results={}
    workers=min(32,max(4,len(s["nodes"])))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        fs={ex.submit(_endpoint_probe,n):n.get("id") for n in s["nodes"]}
        for f in concurrent.futures.as_completed(fs):
            results[fs[f]]=f.result()
    for n in s["nodes"]:
        if n.get("id") in results:
            n["endpoint_test"]=results[n["id"]]
    save_node_store(s)
    reachable=sum(1 for x in results.values() if x.get("reachable") is True)
    return {"ok":True,"total":len(s["nodes"]),"reachable":reachable,"nodes":node_rows(),"testType":"TCP_ENDPOINT_ONLY_NOT_PROXY_HEALTH"}

def node_update_meta(node_id, patch):
    s=node_store(); found=None
    for n in s["nodes"]:
        if n.get("id")==node_id:
            found=n;break
    if not found:
        raise ValueError("NODE_NOT_FOUND")
    for k in ("favorite","pinned"):
        if k in patch: found[k]=bool(patch[k])
    if "rating" in patch: found["rating"]=max(0,min(5,int(patch["rating"])))
    if "tags" in patch: found["tags"]=[str(x)[:40] for x in list(patch["tags"])[:16]]
    if "note" in patch: found["note"]=str(patch["note"])[:500]
    if "name" in patch and str(patch["name"]).strip(): found["name"]=str(patch["name"]).strip()[:120]
    save_node_store(s)
    return {"ok":True,"node":NH.public_node(found)}

def node_raw(node_id):
    s=node_store()
    n=next((x for x in s["nodes"] if x.get("id")==node_id),None)
    if not n:raise ValueError("NODE_NOT_FOUND")
    return str(n.get("raw") or "")

def node_history(node_id):
    s=node_store()
    n=next((x for x in s["nodes"] if x.get("id")==node_id),None)
    if not n:raise ValueError("NODE_NOT_FOUND")
    return {"ok":True,"id":node_id,"name":n.get("name"),"history":list(n.get("history") or [])[-20:],"performanceHistory":list(n.get("performance_history") or [])[-12:]}

def node_export(path,base64_mode=False):
    import base64
    p=pathlib.Path(path)
    raws=[str(n.get("raw") or "").strip() for n in node_store()["nodes"] if str(n.get("raw") or "").strip()]
    text="\\n".join(raws)+"\\n"
    if base64_mode:text=base64.b64encode(text.encode("utf-8")).decode("ascii")+"\\n"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text,encoding="utf-8")
    try:os.chmod(p,0o600)
    except OSError:pass
    return {"ok":True,"path":str(p),"count":len(raws),"format":"BASE64" if base64_mode else "RAW","permissions":"0600_REQUESTED"}

def node_benchmark_batch(limit=4):
    s=node_store()
    if not s["nodes"]:return {"ok":False,"error":"NODE_POOL_EMPTY","benchmarked":0}
    if not any(isinstance(n.get("endpoint_test"),dict) for n in s["nodes"]):node_test_all();s=node_store()
    def source_rank(n):
        src=str(n.get("source") or "")
        return 0 if src=="AURX_HTTP_VERIFIED" else 1 if src=="MORPHEUS_BEST" else 2
    ranked=[]
    for n in s["nodes"]:
        ep=n.get("endpoint_test") if isinstance(n.get("endpoint_test"),dict) else {}
        proto=str(n.get("protocol") or "").lower()
        if ep.get("reachable") is True or proto=="hysteria2":
            ranked.append((0 if not isinstance(n.get("performance_test"),dict) else 1,source_rank(n),float(ep.get("latency_ms") or 999999),n))
    ordered=sorted(ranked,key=lambda x:x[:3]);picked=[];ids=set();protos=set();sources=set()
    for row in ordered:
        n=row[-1];proto=str(n.get("protocol") or "").lower()
        if proto not in protos:
            picked.append(row);ids.add(n.get("id"));protos.add(proto);sources.add(str(n.get("source") or ""))
            if len(picked)>=limit:break
    if len(picked)<limit:
        for row in ordered:
            n=row[-1];src=str(n.get("source") or "")
            if n.get("id") in ids or src in sources:continue
            picked.append(row);ids.add(n.get("id"));sources.add(src)
            if len(picked)>=limit:break
    if len(picked)<limit:
        for row in ordered:
            if row[-1].get("id") in ids:continue
            picked.append(row);ids.add(row[-1].get("id"))
            if len(picked)>=limit:break
    original=s.get("selected");rows=[]
    try:
        for *_,n in picked:
            node_select(n["id"])
            c=node_connect()
            if not c.get("ok"):
                ep=n.get("endpoint_test") or {}
                fail={"ok":False,"pingMs":ep.get("latency_ms"),"downloadMbps":None,"uploadMbps":None,"country":"","checked":_now(),"error":str(c.get("error") or "NODE_HEALTH_FAIL")}
                st=node_store()
                for x in st["nodes"]:
                    if x.get("id")==n["id"]:x["performance_test"]=fail;hist=list(x.get("performance_history") or []);hist.append(fail);x["performance_history"]=hist[-12:];break
                save_node_store(st);rows.append({"id":n["id"],"status":"FAIL",**fail});continue
            perf=_bench(f"socks5h://127.0.0.1:{NODE_PORT}",False)
            st=node_store()
            for x in st["nodes"]:
                if x.get("id")==n["id"]:
                    x["performance_test"]={k:perf.get(k) for k in ("ok","pingMs","downloadMbps","uploadMbps","country","checked","error")}
                    hist=list(x.get("performance_history") or []);hist.append(x["performance_test"]);x["performance_history"]=hist[-12:];break
            save_node_store(st)
            rows.append({"id":n["id"],"status":"PASS" if perf.get("ok") else "FAIL","ok":bool(perf.get("ok")),"pingMs":perf.get("pingMs"),"downloadMbps":perf.get("downloadMbps") if perf.get("ok") else None,"uploadMbps":perf.get("uploadMbps") if perf.get("ok") else None,"country":perf.get("country"),"error":perf.get("error","")})
            node_stop()
    finally:
        node_stop()
        if original and any(x.get("id")==original for x in node_store()["nodes"]):node_select(original)
    eligible=len(ordered);remaining=sum(1 for n in node_store()["nodes"] if ((n.get("endpoint_test") or {}).get("reachable") is True or str(n.get("protocol") or "").lower()=="hysteria2") and not isinstance(n.get("performance_test"),dict))
    return {"ok":True,"benchmarked":len(rows),"passed":sum(1 for x in rows if x.get("ok")),"failed":sum(1 for x in rows if not x.get("ok")),"eligible":eligible,"remainingUnbenchmarked":remaining,"results":rows}

def _node_owner():
    rec=_load(NODE_OWNER,{})
    if not rec: return None
    try:
        pid=int(rec["pid"]); ident=legacy.identity(pid)
        if not ident: return None
        if str(ident.get("exe"))!=str(rec.get("exe")) or str(ident.get("start"))!=str(rec.get("start")):
            return None
        if str(rec.get("config"))!=str(NODE_CONFIG):
            return None
        return rec
    except Exception:
        return None

def _port_open(port):
    try:
        with socket.create_connection(("127.0.0.1",int(port)),timeout=.25): return True
    except OSError:
        return False

def node_stop():
    rec=_node_owner()
    if not rec:
        if _port_open(NODE_PORT):
            return {"ok":False,"error":"NODE_PORT_FOREIGN_OR_UNPROVEN"}
        try: NODE_OWNER.unlink(missing_ok=True)
        except OSError: pass
        s=legacy.session()
        if s.get("mode")=="NODE": legacy.set_session()
        return {"ok":True,"state":"not-owned"}
    ok=legacy.stop_pid(int(rec["pid"]))
    if ok:
        try: NODE_OWNER.unlink(missing_ok=True)
        except OSError: pass
        s=legacy.session()
        if s.get("mode")=="NODE": legacy.set_session()
    return {"ok":ok,"state":"stopped" if ok else "stop-timeout"}

def node_connect(node_id=None):
    st=singbox_status()
    if not st.get("ok"):
        return {"ok":False,"error":st.get("error","SINGBOX_NOT_READY")}
    if node_id:
        node_select(node_id)
    n=selected_node()
    if not n:
        return {"ok":False,"error":"NODE_NOT_SELECTED"}
    existing=_node_owner()
    if existing and existing.get("nodeId")==n.get("id") and _port_open(NODE_PORT):
        return node_verify()
    if existing:
        node_stop()
    elif _port_open(NODE_PORT):
        return {"ok":False,"error":"NODE_PORT_FOREIGN_OR_UNPROVEN"}
    legacy.stop_tor()
    _warpplus_stop_all()
    cfg=NH.sing_box_config(n,NODE_PORT)
    NODE_RUNTIME.mkdir(parents=True,exist_ok=True)
    _atomic(NODE_CONFIG,cfg)
    log=open(NODE_RUNTIME/"sing-box.log","ab",buffering=0)
    p=subprocess.Popen([str(SINGBOX_BIN),"run","-c",str(NODE_CONFIG)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
    deadline=time.time()+10
    while time.time()<deadline and not _port_open(NODE_PORT):
        if p.poll() is not None: break
        time.sleep(.2)
    if not _port_open(NODE_PORT):
        try: legacy.stop_pid(p.pid)
        except Exception: pass
        return {"ok":False,"error":"NODE_PROXY_START_FAILED","exit":p.poll()}
    ident=legacy.identity(p.pid)
    if not ident:
        legacy.stop_pid(p.pid); return {"ok":False,"error":"NODE_IDENTITY_FAIL"}
    rec={**ident,"config":str(NODE_CONFIG),"nodeId":n["id"],"started":_now()}
    _atomic(NODE_OWNER,rec)
    legacy.set_session("NODE","sing-box",{"scope":"BROWSER","nodeId":n["id"],"name":n.get("name")})
    result=node_verify()
    if not result.get("ok"):
        node_stop()
    return result

def node_verify():
    rec=_node_owner()
    if not rec or not _port_open(NODE_PORT):
        return {"ok":False,"error":"NODE_NOT_CONNECTED"}
    out=_bench(f"socks5h://127.0.0.1:{NODE_PORT}",True)
    out.update(mode="NODE",scope="BROWSER",nodeId=rec.get("nodeId"))
    return out

def node_connect_auto(limit=10):
    rows=node_rows()
    candidates=[n for n in rows if (n.get("endpoint_test") or {}).get("reachable") is True]
    if not candidates:
        node_test_all()
        rows=node_rows()
        candidates=[n for n in rows if (n.get("endpoint_test") or {}).get("reachable") is True]
    attempts=[]
    for n in candidates[:max(1,min(int(limit),20))]:
        node_select(n["id"])
        r=node_connect()
        attempts.append({"id":n.get("id"),"name":n.get("name"),"protocol":n.get("protocol"),"source":n.get("source"),"ok":bool(r.get("ok")),"error":r.get("error",""),"country":r.get("country",""),"pingMs":r.get("pingMs")})
        if r.get("ok"):
            r["autoSelected"]=True
            r["attempts"]=attempts
            return r
    return {"ok":False,"error":"NODE_POOL_NO_HEALTHY_NODE","attempts":attempts}

def benchmark_node(ping_only=False):
    before=_node_owner()
    temp=not bool(before and _port_open(NODE_PORT))
    if temp:
        r=node_connect()
        if not r.get("ok"): return r
    try:
        out=_bench(f"socks5h://127.0.0.1:{NODE_PORT}",ping_only)
        out.update(mode="NODE",scope="BROWSER",temporary=temp)
        n=selected_node()
        if n:
            s=node_store()
            for item in s["nodes"]:
                if item.get("id")==n.get("id"):
                    item["performance_test"]={k:out.get(k) for k in ("ok","pingMs","downloadMbps","uploadMbps","country","exitIp","checked","error")}
                    hist=list(item.get("performance_history") or [])
                    hist.append(item["performance_test"]); item["performance_history"]=hist[-12:]
                    break
            save_node_store(s)
        return out
    finally:
        if temp: node_stop()

def benchmark_tor(ping_only=False):
    ts=legacy.tor_status(); temp=not bool(ts.get("ok") and ts.get("state")=="running")
    if temp:
        r=legacy.start_tor()
        if not r.get("ok"): return r
    try:
        out=_bench(f"socks5h://127.0.0.1:{legacy.SOCKS_PORT}",ping_only)
        out.update(mode="TOR",scope="BROWSER",temporary=temp)
        return out
    finally:
        if temp: legacy.stop_tor()

def benchmark_warp(ping_only=False):
    pre=legacy.warp_status(); temp=not bool(pre.get("connected"))
    if temp:
        remember_base_route()
        r=legacy.warp_connect_safe()
        if not r.get("ok"): return r
    try:
        out=_bench(None,ping_only)
        out.update(mode="WARP",scope="SYSTEM",temporary=temp)
        return out
    finally:
        if temp: legacy.warp_disconnect()

def benchmark_custom(ping_only=False):
    cp=str(settings().get("customProxy") or "").strip()
    if not cp:
        return {"ok":False,"error":"CUSTOM_PROXY_NOT_CONFIGURED"}
    out=_bench(cp,ping_only);out.update(mode="CUSTOM",scope="BROWSER")
    return out

def benchmark_configured(mode, ping_only=False):
    requested=str(mode or "DIRECT").upper()
    path_mode=str(settings().get("testPathMode") or "BASE").upper()
    if path_mode=="BASE":
        out=benchmark_direct(ping_only)
        out["requestedMethod"]=requested
        out["testPathMode"]="BASE"
        return out
    out=benchmark_method(requested,ping_only)
    if isinstance(out,dict):
        out["requestedMethod"]=requested
        out["testPathMode"]="SELECTED"
    return out

def benchmark_method(mode, ping_only=False):
    mode=str(mode or "DIRECT").upper()
    if mode=="DIRECT": return benchmark_direct(ping_only)
    if mode=="NODE": return benchmark_node(ping_only)
    if mode=="TOR": return benchmark_tor(ping_only)
    if mode in ("WARP","GOOL","CFON"): return benchmark_warpplus(mode,ping_only)
    if mode=="CUSTOM": return benchmark_custom(ping_only)
    if mode=="AUTO":
        if singbox_status().get("ok"):
            pre=_node_owner()
            if not pre:
                c=node_connect_auto(8)
                if c.get("ok"):
                    try:
                        r=benchmark_node(ping_only);r["mode"]="AUTO/NODE"
                        if r.get("ok"):return r
                    finally:
                        node_stop()
            else:
                r=benchmark_node(ping_only)
                if r.get("ok"):r["mode"]="AUTO/NODE";return r
        if warpplus_status().get("ok"):
            r=benchmark_warpplus("WARP",ping_only)
            if r.get("ok"):r["mode"]="AUTO/WARP";return r
        r=benchmark_tor(ping_only); r["mode"]="AUTO/TOR"; return r
    return {"ok":False,"error":"METHOD_UNAVAILABLE_ON_LINUX","mode":mode}

def benchmark_all_methods(ping_only=False):
    active=legacy.session()
    if active.get("mode"):
        return {"ok":False,"error":"STOP_FREENETHUB_CONNECTION_BEFORE_TEST_ALL","activeMode":active.get("mode"),"results":[]}
    methods=["DIRECT","NODE","WARP","GOOL","CFON","TOR","AUTO"]
    if str(settings().get("customProxy") or "").strip():methods.insert(-1,"CUSTOM")
    rows=[]
    for method in methods:
        try:
            item=benchmark_method(method,ping_only)
            if not isinstance(item,dict):item={"ok":False,"error":"INVALID_BENCHMARK_RESULT"}
        except Exception as e:
            item={"ok":False,"error":type(e).__name__+": "+str(e)}
        item=dict(item);item["method"]=method;rows.append(item)
    return {
        "ok":True,
        "pingOnly":bool(ping_only),
        "completed":len(rows),
        "passed":sum(1 for x in rows if x.get("ok")),
        "failed":sum(1 for x in rows if not x.get("ok")),
        "results":rows,
    }

def connect_method(mode, scope="BROWSER"):
    mode=str(mode or "AUTO").upper(); scope=str(scope or "BROWSER").upper()
    if scope=="CONSOLE":
        return legacy.console_start()
    if scope=="SYSTEM":
        if mode not in ("AUTO","WARP"):
            return {"ok":False,"error":"LINUX_FULL_SYSTEM_WARP_ONLY","mode":mode}
        remember_base_route()
        return legacy.connect_mode("WARP",full_system=True)
    if mode=="NODE":
        return node_connect()
    if mode=="AUTO":
        if singbox_status().get("ok"):
            r=node_connect_auto(8)
            if r.get("ok"):
                r["selected"]="NODE"
                return r
        if warpplus_status().get("ok"):
            r=warpplus_start("WARP")
            if r.get("ok"):
                r["selected"]="WARP"
                return r
        r=legacy.start_tor()
        r["selected"]="TOR"
        r["scope"]="BROWSER"
        return r
    if mode in ("WARP","GOOL","CFON"):
        return warpplus_start(mode)
    if mode=="CUSTOM":
        cp=str(settings().get("customProxy") or "").strip()
        if not cp: return {"ok":False,"error":"CUSTOM_PROXY_NOT_CONFIGURED"}
        r=_bench(cp,True)
        if r.get("ok"):
            legacy.set_session("CUSTOM","custom",{"scope":"BROWSER","proxy":cp})
        return r
    if mode in ("TOR","OBFS4","SNOWFLAKE","DIRECT"):
        node_stop();_warpplus_stop_all()
    return legacy.connect_mode(mode,full_system=False)

def stop_all():
    nr=node_stop()
    wr=_warpplus_stop_all()
    lr=legacy.stop_all()
    return {"ok":bool(nr.get("ok") and wr.get("ok") and lr.get("ok")),"node":nr,"warpplus":wr,"legacy":lr}

def _firefox_profile(proxy=None):
    base=legacy.firefox_profile_root()/"firefox-r37"
    base.mkdir(parents=True,exist_ok=True)
    prefs=[
        'user_pref("browser.shell.checkDefaultBrowser", false);',
        'user_pref("browser.startup.homepage", "about:blank");',
        'user_pref("datareporting.healthreport.uploadEnabled", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
    ]
    if proxy:
        u=urllib.parse.urlparse(proxy)
        if u.scheme.startswith("socks"):
            prefs += [
                'user_pref("network.proxy.type", 1);',
                f'user_pref("network.proxy.socks", "{u.hostname}");',
                f'user_pref("network.proxy.socks_port", {u.port});',
                'user_pref("network.proxy.socks_version", 5);',
                'user_pref("network.proxy.socks_remote_dns", true);',
            ]
        elif u.scheme=="http":
            prefs += [
                'user_pref("network.proxy.type", 1);',
                f'user_pref("network.proxy.http", "{u.hostname}");',
                f'user_pref("network.proxy.http_port", {u.port});',
                f'user_pref("network.proxy.ssl", "{u.hostname}");',
                f'user_pref("network.proxy.ssl_port", {u.port});',
            ]
    else:
        prefs += ['user_pref("network.proxy.type", 0);']
    (base/"user.js").write_text("\n".join(prefs)+"\n",encoding="utf-8")
    return base

def open_browser(url=None):
    firefox=legacy.executable("firefox")
    if not firefox: return {"ok":False,"error":"FIREFOX_MISSING"}
    s=legacy.session();mode=str(s.get("mode") or "")
    if not mode: return {"ok":False,"error":"CONNECT_FIRST"}
    proxy=None
    if mode=="NODE":
        if not (_node_owner() and _port_open(NODE_PORT)): return {"ok":False,"error":"NODE_NOT_READY"}
        proxy=f"socks5h://127.0.0.1:{NODE_PORT}"
    elif mode in ("WARP_PROXY","GOOL","CFON"):
        method="WARP" if mode=="WARP_PROXY" else mode
        if not (_warpplus_owner(method) and _port_open(WARPPLUS_PORTS[method])):return {"ok":False,"error":"WARPPLUS_NOT_READY"}
        proxy=_warpplus_proxy(method)
    elif mode=="TOR":
        if not legacy.tor_status().get("ok"): return {"ok":False,"error":"TOR_NOT_READY"}
        proxy=f"socks5h://127.0.0.1:{legacy.SOCKS_PORT}"
    elif mode=="CUSTOM":
        proxy=str((s.get("detail") or {}).get("proxy") or settings().get("customProxy") or "")
    elif mode in ("WARP","WARP_TRIAL","WARP_EXTERNAL"):
        tr=legacy.trace(timeout=10)
        if not (tr.get("ok") and (tr.get("trace") or {}).get("warp")=="on"): return {"ok":False,"error":"WARP_NOT_READY"}
    prof=_firefox_profile(proxy)
    stopped=legacy.stop_project_firefox(prof)
    if not stopped.get("ok"): return {"ok":False,"error":"BROWSER_BUSY"}
    target=url or str(settings().get("home") or "https://www.youtube.com/")
    subprocess.Popen([firefox,"--no-remote","--new-instance","--profile",str(prof),target],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
    return {"ok":True,"mode":mode,"proxy":proxy or "DIRECT_SYSTEM","profile":str(prof)}

def current_snapshot():
    s=legacy.session();mode=str(s.get("mode") or "")
    if mode=="NODE":
        v=node_verify()
        return {"ok":v.get("ok",False),"mode":"NODE","provider":"Node Pool","scope":"BROWSER","country":v.get("country",""),"ip":v.get("exitIp",""),"warp":v.get("warp",""),"detail":s.get("detail",{})}
    if mode in ("WARP_PROXY","GOOL","CFON"):
        method="WARP" if mode=="WARP_PROXY" else mode
        v=warpplus_verify(method)
        return {"ok":v.get("ok",False),"mode":method,"provider":"warp-plus","scope":"BROWSER","country":v.get("country",""),"ip":v.get("exitIp",""),"warp":v.get("warp",""),"detail":s.get("detail",{}),"error":v.get("error","")}
    if mode=="CUSTOM":
        cp=str((s.get("detail") or {}).get("proxy") or "")
        v=_bench(cp,True) if cp else {"ok":False}
        return {"ok":v.get("ok",False),"mode":"CUSTOM","provider":"Custom Proxy","scope":"BROWSER","country":v.get("country",""),"ip":v.get("exitIp",""),"warp":v.get("warp",""),"detail":s.get("detail",{})}
    snap=legacy.app_snapshot()
    if isinstance(snap,dict):
        snap["version"]=VERSION
    return snap

def inventory():
    out=legacy.inventory()
    out["version"]=VERSION
    out["singbox"]=singbox_status()
    out["warpplus"]=warpplus_status()
    out["nodes"]={"total":len(node_store()["nodes"]),"selected":node_store().get("selected")}
    out["settings"]=settings()
    return out

def doctor():
    out=legacy.doctor()
    out["singbox"]=singbox_status()
    out["warpplus"]=warpplus_status()
    out["nodePortOpen"]=_port_open(NODE_PORT)
    out["nodeOwner"]=bool(_node_owner())
    out["sourceRevision"]="R37-LINUX-PARITY"
    return out

def _linux_revision_from_name(name):
    m=re.search(r"_Linux_R(\d+)\.zip$",str(name or ""),re.I)
    return int(m.group(1)) if m else None

def update_check():
    req=urllib.request.Request("https://api.github.com/repos/GOD13emad/FreeNetHub/releases/latest",headers={"User-Agent":"FreeNetHub-Linux-R37/1","Accept":"application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req,timeout=12) as resp:
            j=json.loads(resp.read(1024*1024).decode("utf-8"))
    except Exception as e:
        return {"ok":False,"error":"UPDATE_CHECK_FAILED","detail":str(e)}
    assets=[{"name":a.get("name"),"size":a.get("size"),"digest":a.get("digest"),"url":a.get("browser_download_url")} for a in j.get("assets",[]) if isinstance(a,dict)]
    linux_assets=[a for a in assets if _linux_revision_from_name(a.get("name")) is not None]
    linux=max(linux_assets,key=lambda a:_linux_revision_from_name(a.get("name")),default=None)
    remote_rev=_linux_revision_from_name(linux.get("name")) if linux else None
    local_rev=12
    return {"ok":True,"current":VERSION,"localRevision":local_rev,"tag":j.get("tag_name"),"published":j.get("published_at"),"linuxAsset":linux,"remoteRevision":remote_rev,"updateAvailable":bool(remote_rev is not None and remote_rev>local_rev),"assets":assets}

def update_install():
    chk=update_check()
    if not chk.get("ok"):return chk
    asset=chk.get("linuxAsset")
    if not chk.get("updateAvailable") or not asset:
        return {"ok":False,"error":"NO_NEWER_LINUX_UPDATE","current":VERSION,"remoteRevision":chk.get("remoteRevision"),"tag":chk.get("tag")}
    digest=str(asset.get("digest") or "")
    if not digest.lower().startswith("sha256:") or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}",digest):
        return {"ok":False,"error":"UPDATE_ASSET_DIGEST_MISSING"}
    url=str(asset.get("url") or "")
    u=urllib.parse.urlparse(url)
    if u.scheme!="https" or u.hostname!="github.com":
        return {"ok":False,"error":"UPDATE_ASSET_URL_UNTRUSTED"}
    upd=STATE/"update"/str(chk.get("tag") or "latest");upd.mkdir(parents=True,exist_ok=True)
    archive=upd/str(asset.get("name"))
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"FreeNetHub-Linux-R37/1"})
        with urllib.request.urlopen(req,timeout=120) as resp,open(archive,"wb") as f:
            total=0
            while True:
                chunk=resp.read(1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>256*1024*1024:raise ValueError("UPDATE_ASSET_TOO_LARGE")
                f.write(chunk)
    except Exception as e:
        return {"ok":False,"error":"UPDATE_DOWNLOAD_FAILED","detail":str(e)}
    got=_sha256(archive)
    expected=digest.split(":",1)[1].lower()
    if got!=expected:
        try:archive.unlink()
        except OSError:pass
        return {"ok":False,"error":"UPDATE_ASSET_HASH_MISMATCH","expected":expected,"actual":got}
    extract=upd/"payload"
    if extract.exists():shutil.rmtree(extract)
    extract.mkdir()
    try:
        import zipfile
        with zipfile.ZipFile(archive) as z:
            root=extract.resolve()
            for info in z.infolist():
                target=(extract/info.filename).resolve()
                if root not in target.parents and target!=root:raise ValueError("UPDATE_ZIP_PATH_ESCAPE")
                if info.file_size>128*1024*1024:raise ValueError("UPDATE_ZIP_MEMBER_TOO_LARGE")
            z.extractall(extract)
    except Exception as e:
        return {"ok":False,"error":"UPDATE_EXTRACT_FAILED","detail":str(e)}
    scripts=list(extract.rglob("install.sh"))
    installer=next((p for p in scripts if (p.parent/"freenet_hub_linux_gtk.py").is_file() and (p.parent/"freenet_hub_linux_r37.py").is_file()),None)
    if not installer:return {"ok":False,"error":"UPDATE_INSTALLER_MISSING"}
    log=STATE/"evidence"/f"linux-update-{int(time.time())}.log"
    out=open(log,"ab",buffering=0)
    subprocess.Popen(["bash",str(installer)],stdin=subprocess.DEVNULL,stdout=out,stderr=out,cwd=str(installer.parent),start_new_session=True,close_fds=True)
    return {"ok":True,"scheduled":True,"tag":chk.get("tag"),"asset":asset.get("name"),"sha256":got,"log":str(log),"note":"Installer will restart only the FreeNet Hub UI; no connection is started by install."}

def import_obfs4(path):
    return legacy.import_obfs4(path)

def import_snowflake(path):
    return legacy.import_snowflake(path)

def console_status():
    return legacy.console_status()

def console_prepare():
    return legacy.console_prepare()

def console_start():
    return legacy.console_start()

def console_stop():
    return legacy.console_stop()

def export_report():
    base=legacy.export_report()
    base["linuxR37"]={"version":VERSION,"settings":settings(),"singbox":singbox_status(),"warpplus":warpplus_status(),"nodes":{"total":len(node_store()["nodes"]),"selected":node_store().get("selected")}}
    p=STATE/"evidence"/f"linux-r37-report-{int(time.time())}.json"
    _atomic(p,base)
    return {"ok":True,"path":str(p),"report":base}
