from __future__ import annotations
import importlib.util,json,pathlib,shutil,tempfile,time
SRC=pathlib.Path(__file__).resolve().parents[1]
INST=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
sp=importlib.util.spec_from_file_location("E",SRC/"app"/"engine.py")
E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
with tempfile.TemporaryDirectory(prefix="FNH-R33-verified-sandbox-") as td:
    root=pathlib.Path(td)
    (root/"data").mkdir();(root/"jobs").mkdir();(root/"gateway/runtime").mkdir(parents=True)
    shutil.copy2(INST/"gateway/runtime/local_gateway.json",root/"gateway/runtime/local_gateway.json")
    shutil.copy2(INST/"settings.json",root/"settings.json")
    E.ROOT=root;E.APP=SRC/"app";E.JOB="";E.DEADLINE=time.monotonic()+420
    summary={"schema":1,"date":"2026-09-28","installedMutation":False}
    try:
        rr=E.node_refresh_public(True)
        summary["refresh"]={"total":rr.get("total"),"reachable":rr.get("reachable"),"sources":rr.get("sources"),"failed":rr.get("failedSources"),"imported":rr.get("imported")}
        br=E.dispatch("NodeBenchmarkBatch","NODE","")
        store=E.node_store();byid={n.get("id"):n for n in store.get("nodes",[])}
        summary["benchmark"]={
          "benchmarked":br.get("benchmarked"),"passed":br.get("passed"),"failed":br.get("failed"),"eligible":br.get("eligible"),
          "results":[{"source":str(byid.get(x.get("id"),{}).get("source") or ""),"protocol":str(byid.get(x.get("id"),{}).get("protocol") or ""),"status":x.get("status"),"pingMs":x.get("pingMs"),"downloadMbps":x.get("downloadMbps"),"uploadMbps":x.get("uploadMbps"),"country":x.get("country"),"error":x.get("error")} for x in br.get("results",[])]
        }
        summary["status"]="PASS" if int(br.get("passed") or 0)>0 else "NO_HEALTHY_PATH_FOUND"
    finally:
        try:E.stop("NODE")
        except Exception:pass
    print(json.dumps(summary,ensure_ascii=False,indent=2))
