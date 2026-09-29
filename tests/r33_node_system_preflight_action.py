from __future__ import annotations
import importlib.util,json,pathlib,shutil,tempfile,time
SRC=pathlib.Path(__file__).resolve().parents[1]
INST=pathlib.Path.home()/"AppData/Local/Programs/FreeNetHub"
NODE_ID="b1a0c8cff7eca59f9cee"
URL="https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt"
sp=importlib.util.spec_from_file_location("E",SRC/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
with tempfile.TemporaryDirectory(prefix="FNH-R33-preflight-action-") as td:
 root=pathlib.Path(td);(root/"data").mkdir();(root/"jobs").mkdir();(root/"gateway/runtime").mkdir(parents=True)
 shutil.copy2(INST/"gateway/runtime/local_gateway.json",root/"gateway/runtime/local_gateway.json")
 shutil.copy2(INST/"settings.json",root/"settings.json")
 shutil.copy2(SRC/"gateway/socks_udp_probe.py",root/"gateway/socks_udp_probe.py")
 E.ROOT=root;E.APP=SRC/"app";E.JOB="";E.DEADLINE=time.monotonic()+240
 out={"schema":1,"date":"2026-09-28","installedMutation":False,"selected":NODE_ID}
 try:
  r=E.curl(URL,seconds=25,size=E.NH.MAX_NODE_TEXT)
  if r.get("exit")!=0 or r.get("code")!="200":raise RuntimeError("SOURCE_FETCH_FAIL")
  E.node_import_text(r.get("body",""),"AURX_HTTP_VERIFIED");E.node_batch_fast()
  ids={n["id"] for n in E.node_store()["nodes"]}
  if NODE_ID not in ids:raise RuntimeError("PROVEN_NODE_NOT_PRESENT")
  E.node_select(NODE_ID)
  p=E.dispatch("NodeSystemPreflight","NODE","")
  out["result"]={k:p.get(k) for k in ("mode","provider","path","systemEligible","ok","pingMs","downloadMbps","uploadMbps","country","udpCountry","error","selected","temporary")}
  out["status"]="PASS" if p.get("systemEligible") else "FAIL"
 except Exception as ex:
  out["status"]="FAIL";out["error"]=str(ex)
 finally:
  try:E.stop("NODE")
  except Exception:pass
 print(json.dumps(out,ensure_ascii=False,indent=2))
