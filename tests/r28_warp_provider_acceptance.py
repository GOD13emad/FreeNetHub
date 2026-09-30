from __future__ import annotations
import json,pathlib,subprocess,uuid,sys,time
root=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
def run(action,mode,budget):
    job=uuid.uuid4().hex
    cp=subprocess.run([sys.executable,str(root/"app/engine.py"),"--action",action,"--mode",mode,"--job",job,"--budget",str(budget)],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=budget+25)
    rec=json.loads((root/"jobs"/f"{job}.json").read_text(encoding="utf-8-sig"))
    return cp.returncode,rec.get("result") or {}
out={"schema":1,"date":"2026-09-28","provider":"WARP","status":"FAIL","performance":{},"cleanup":{},"privacy":"No raw exit IP persisted."}
try:
    ec,r=run("ProviderBenchmark","WARP",180)
    p=r.get("performance") if isinstance(r,dict) else {}
    out["performance"]={"exit":ec,"healthy":bool((r.get("health") or {}).get("healthy")) if isinstance(r,dict) else False,"temporary":bool(r.get("temporary")) if isinstance(r,dict) else False,"ok":bool((p or {}).get("ok")),"pingMs":(p or {}).get("pingMs"),"downloadMbps":(p or {}).get("downloadMbps"),"uploadMbps":(p or {}).get("uploadMbps"),"country":(p or {}).get("country"),"error":(p or {}).get("error") or (r.get("error") if isinstance(r,dict) else "")}
    if ec==0 and out["performance"]["healthy"] and out["performance"]["ok"]:
        out["status"]="PASS"
except Exception as ex:
    out["error"]=type(ex).__name__+":"+str(ex)
finally:
    try: run("Stop","AUTO",45)
    except Exception: pass
    time.sleep(.5)
    # evidence-only cleanup check using netstat; no process mutation
    cp=subprocess.run(["netstat.exe","-ano","-p","tcp"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=5)
    ports={19410,19413,19414,19450,19452,19453,19460}
    hits=[]
    for line in cp.stdout.splitlines():
        a=line.split()
        if len(a)>=5 and a[0].upper()=="TCP" and a[-2].upper()=="LISTENING":
            try: port=int(a[1].rsplit(":",1)[-1])
            except ValueError: continue
            if port in ports:hits.append(port)
    out["cleanup"]={"projectListeners":sorted(set(hits)),"pass":not hits}
    if hits: out["status"]="FAIL";out["error"]="CLEANUP_RESIDUE"
PROJECT=pathlib.Path(__file__).resolve().parent.parent
ev=PROJECT/"evidence"/"R28_WARP_PROVIDER_ACCEPTANCE_20260928.json"
ev.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
sys.exit(0 if out["status"]=="PASS" else 28)
