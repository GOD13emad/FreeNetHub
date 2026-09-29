from __future__ import annotations
import importlib.util,json,pathlib,shutil,tempfile,time,subprocess,sys
SRC=pathlib.Path(__file__).resolve().parents[1]
INST=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
sp=importlib.util.spec_from_file_location("E",SRC/"app"/"engine.py")
E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
probe=SRC/"gateway"/"socks_udp_probe.py"
url="https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt"
with tempfile.TemporaryDirectory(prefix="FNH-R33-udp-sandbox-") as td:
    root=pathlib.Path(td);(root/"data").mkdir();(root/"jobs").mkdir();(root/"gateway/runtime").mkdir(parents=True)
    shutil.copy2(INST/"gateway/runtime/local_gateway.json",root/"gateway/runtime/local_gateway.json")
    shutil.copy2(INST/"settings.json",root/"settings.json")
    E.ROOT=root;E.APP=SRC/"app";E.JOB="";E.DEADLINE=time.monotonic()+480
    out={"schema":1,"date":"2026-09-28","installedMutation":False,"source":"AURX_HTTP_VERIFIED","results":[],"eligible":False}
    r=E.curl(url,seconds=25,size=E.NH.MAX_NODE_TEXT)
    if r.get("exit")!=0 or r.get("code")!="200":
        out["status"]="SOURCE_FETCH_FAIL";out["fetchPath"]=r.get("fetchPath");print(json.dumps(out,ensure_ascii=False,indent=2));raise SystemExit()
    imp=E.node_import_text(r.get("body",""),"AURX_HTTP_VERIFIED")
    fast=E.node_batch_fast();store=E.node_store()
    cand=[n for n in store["nodes"] if n.get("source")=="AURX_HTTP_VERIFIED" and isinstance(n.get("endpoint_test"),dict) and n["endpoint_test"].get("reachable") is True and str(n.get("protocol") or "").lower() in ("ss","vmess")]
    cand.sort(key=lambda n:(0 if str(n.get("protocol") or "").lower()=="ss" else 1,float(n["endpoint_test"].get("latency_ms") or 999999)))
    picked=[];seen=set()
    for n in cand:
        proto=str(n.get("protocol") or "").lower()
        if proto not in seen:
            picked.append(n);seen.add(proto)
        if len(picked)>=2:break
    for n in cand:
        if len(picked)>=4:break
        if n["id"] not in {x["id"] for x in picked}:picked.append(n)
    out["pool"]={"parsed":imp.get("imported"),"reachable":fast.get("reachable"),"candidateCount":len(cand),"tested":len(picked),"fetchPath":r.get("fetchPath")}
    for n in picked:
        rec={"id":n["id"],"protocol":n.get("protocol"),"endpointMs":n["endpoint_test"].get("latency_ms"),"https":False,"udp":False,"benchmarkOk":False}
        try:
            E.node_select(n["id"])
            h=E.ensure("NODE");rec["https"]=bool(h.get("healthy"));rec["tcpCountry"]=str(h.get("country") or "")
            if rec["https"]:
                pr=subprocess.run([sys.executable,str(probe),"19460","127.0.0.1"],capture_output=True,text=True,timeout=18)
                if pr.returncode==0:
                    uj=json.loads(pr.stdout);rec["udp"]=uj.get("status")=="PASS";udp_ip=str(uj.get("udp_public_ip") or "")
                    if udp_ip:
                        gr=E.curl("https://ipwho.is/"+udp_ip,seconds=10,size=65536)
                        try:gj=json.loads(gr.get("body") or "{}");rec["udpCountry"]=str(gj.get("country_code") or "").upper()
                        except Exception:rec["udpCountry"]=""
                else:rec["udpError"]="UDP_PROBE_FAILED"
                try:
                    perf=E.path_speed("NODE",1000000,250000)
                    rec["benchmarkOk"]=bool(perf.get("ok"));rec["pingMs"]=perf.get("pingMs")
                    rec["downloadMbps"]=perf.get("downloadMbps") if perf.get("ok") else None
                    rec["uploadMbps"]=perf.get("uploadMbps") if perf.get("ok") else None
                    rec["benchCountry"]=str(perf.get("country") or "");rec["benchError"]=str(perf.get("error") or "")
                except Exception as ex:rec["benchError"]=str(ex)
            if rec["https"] and rec["udp"]:
                out["eligible"]=True
        except Exception as ex:
            rec["error"]=str(ex)
        finally:
            try:E.stop("NODE")
            except Exception:pass
        out["results"].append(rec)
        if out["eligible"] and rec["benchmarkOk"]:break
    out["status"]="PASS" if out["eligible"] else "NO_UDP_CAPABLE_HEALTHY_NODE"
    print(json.dumps(out,ensure_ascii=False,indent=2))
