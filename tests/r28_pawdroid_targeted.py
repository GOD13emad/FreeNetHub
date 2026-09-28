from __future__ import annotations
import json,pathlib,subprocess,uuid,sys
root=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
store=json.loads((root/"data/nodes.json").read_text(encoding="utf-8-sig"))
candidates=[]
for n in store.get("nodes",[]):
    src=str(n.get("source") or "")
    if not src.startswith("SHADOWSHARE_"):
        continue
    ep=n.get("endpoint_test") if isinstance(n.get("endpoint_test"),dict) else {}
    if ep.get("reachable") is not True and str(n.get("protocol") or "").lower()!="hysteria2":
        continue
    candidates.append(n)
by={}
for n in sorted(candidates,key=lambda x:float(((x.get("endpoint_test") or {}).get("latency_ms") or 999999))):
    p=str(n.get("protocol") or "").lower()
    by.setdefault(p,[])
    if len(by[p])<2:
        by[p].append(n)
chosen=[]
for p in ("vmess","ss","hysteria2","trojan","vless"):
    chosen.extend(by.get(p,[]))
chosen=chosen[:8]
def run(action,mode="NODE",payload="",budget=180):
    job=uuid.uuid4().hex
    cmd=[sys.executable,str(root/"app/engine.py"),"--action",action,"--mode",mode,"--job",job,"--budget",str(budget)]
    if payload:
        cmd+=["--payload",payload]
    cp=subprocess.run(cmd,cwd=root,timeout=budget+20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    rec=json.loads((root/"jobs"/f"{job}.json").read_text(encoding="utf-8-sig"))
    return cp.returncode,rec.get("result") or {}
rows=[]
for n in chosen:
    try:
        ec,_=run("NodeSelect","NODE",str(n["id"]),30)
        if ec:
            raise RuntimeError("SELECT_FAILED")
        ec,r=run("NodeSpeed","NODE","",150)
        perf=(r.get("performance") or {}) if isinstance(r,dict) else {}
        err=""
        if isinstance(r,dict):
            err=str(perf.get("error") or r.get("error") or "")
        rows.append({"protocol":n.get("protocol"),"source":n.get("source"),"status":"PASS" if ec==0 and perf.get("ok") else "FAIL","pingMs":perf.get("pingMs"),"downloadMbps":perf.get("downloadMbps"),"uploadMbps":perf.get("uploadMbps"),"country":perf.get("country"),"error":err})
        if ec==0 and perf.get("ok"):
            break
    except Exception as ex:
        rows.append({"protocol":n.get("protocol"),"source":n.get("source"),"status":"FAIL","pingMs":None,"downloadMbps":None,"uploadMbps":None,"country":"","error":str(ex)})
    finally:
        try:
            run("Stop","AUTO","",45)
        except Exception:
            pass
out={"schema":1,"date":"2026-09-28","sourceHypothesis":"Pawdroid/ShadowShare subset advertised as periodically speed-tested; results remain local-network dependent.","attempted":len(rows),"passed":sum(r["status"]=="PASS" for r in rows),"results":rows,"privacy":"No raw URI, server, credential, path, key, or IP persisted."}
PROJECT=pathlib.Path(__file__).resolve().parent.parent\nev=PROJECT/"evidence"/"R28_PAWDROID_TARGETED_NODE_ACCEPTANCE_20260928.json"
ev.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
