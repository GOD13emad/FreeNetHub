import importlib.util,pathlib,json
R=pathlib.Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("E",R/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
u="https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt"
r=E.curl(u,seconds=25,size=E.NH.MAX_NODE_TEXT)
out={"exit":r.get("exit"),"code":r.get("code"),"bytes":r.get("bytes"),"fetchPath":r.get("fetchPath"),"error":r.get("error")}
if r.get("exit")==0 and r.get("code")=="200":
 p=E.NH.parse_blob(r.get("body",""),"AURX_HTTP_VERIFIED")
 out["parsed"]=len(p.get("nodes") or []);out["parseErrors"]=len(p.get("errors") or [])
print(json.dumps(out,indent=2))
