from __future__ import annotations
import importlib.util,json,pathlib,tempfile,time,shutil
R=pathlib.Path(__file__).resolve().parents[1];I=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub";KNOWN="b1a0c8cff7eca59f9cee"
sp=importlib.util.spec_from_file_location("E",R/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
with tempfile.TemporaryDirectory(prefix="FNH-R33-rank-") as td:
 root=pathlib.Path(td);(root/"data").mkdir();(root/"jobs").mkdir();(root/"gateway/runtime").mkdir(parents=True);shutil.copy2(I/"gateway/runtime/local_gateway.json",root/"gateway/runtime/local_gateway.json");shutil.copy2(I/"settings.json",root/"settings.json")
 E.ROOT=root;E.APP=R/"app";E.JOB="";E.DEADLINE=time.monotonic()+180
 r=E.curl(E.PUBLIC_COUNTRY_NODE_SOURCES["SG"],seconds=25,size=E.NH.MAX_NODE_TEXT);p=E.NH.parse_blob(r.get("body",""),"AURX_COUNTRY_SG");E.save_node_store({"schema":1,"selected":"","nodes":p["nodes"]});E.node_batch_fast();s=E.node_store()
 def key(n):
  ep=n.get("endpoint_test") if isinstance(n.get("endpoint_test"),dict) else {}; return (0 if ep.get("reachable") else 1,float(ep.get("latency_ms",999999) or 999999))
 eligible=[n for n in s["nodes"] if (n.get("endpoint_test") or {}).get("reachable") is True or str(n.get("protocol") or "").lower()=="hysteria2"]
 overall=sorted(eligible,key=key);same=sorted([n for n in eligible if n.get("protocol")=="ss"],key=key)
 print(json.dumps({"eligible":len(eligible),"knownOverallRank":next((i+1 for i,n in enumerate(overall) if n.get("id")==KNOWN),None),"knownProtocolRank":next((i+1 for i,n in enumerate(same) if n.get("id")==KNOWN),None),"protocolCounts":{p:sum(1 for n in eligible if n.get("protocol")==p) for p in sorted({n.get("protocol") for n in eligible})}},indent=2))
