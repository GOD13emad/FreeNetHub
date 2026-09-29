from __future__ import annotations
import importlib.util,json,pathlib,tempfile,time,shutil
R=pathlib.Path(__file__).resolve().parents[1]
I=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
sp=importlib.util.spec_from_file_location("E",R/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
KNOWN="b1a0c8cff7eca59f9cee";url=E.PUBLIC_COUNTRY_NODE_SOURCES["SG"]
with tempfile.TemporaryDirectory(prefix="FNH-R33-sg-shard-") as td:
 root=pathlib.Path(td);(root/"data").mkdir();(root/"jobs").mkdir();(root/"gateway/runtime").mkdir(parents=True)
 shutil.copy2(I/"gateway/runtime/local_gateway.json",root/"gateway/runtime/local_gateway.json")
 shutil.copy2(I/"settings.json",root/"settings.json")
 E.ROOT=root;E.APP=R/"app";E.JOB="";E.DEADLINE=time.monotonic()+180
 r=E.curl(url,seconds=25,size=E.NH.MAX_NODE_TEXT)
 out={"fetch":{"exit":r.get("exit"),"code":r.get("code"),"bytes":r.get("bytes"),"fetchPath":r.get("fetchPath"),"error":r.get("error")}}
 if r.get("exit")==0 and r.get("code")=="200":
  p=E.NH.parse_blob(r.get("body",""),"AURX_COUNTRY_SG");out["parsed"]=len(p.get("nodes") or []);out["parseErrors"]=len(p.get("errors") or []);out["hasKnown"]=any(n.get("id")==KNOWN for n in p.get("nodes") or [])
  E.save_node_store({"schema":1,"selected":"","nodes":p.get("nodes") or []});f=E.node_batch_fast();s=E.node_store()
  out["reachable"]=f.get("reachable");out["byProtocol"]={}
  for n in s["nodes"]:
   pr=str(n.get("protocol") or "");d=out["byProtocol"].setdefault(pr,{"total":0,"reachable":0});d["total"]+=1;d["reachable"]+=int((n.get("endpoint_test") or {}).get("reachable") is True)
 print(json.dumps(out,indent=2))
