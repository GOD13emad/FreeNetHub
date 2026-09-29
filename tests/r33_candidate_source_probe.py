import importlib.util,pathlib,json
R=pathlib.Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("E",R/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
urls=[
("MORPHEUS_BEST","https://raw.githubusercontent.com/morpheusadam/v2ray-config/main/subs/bundles/best.txt"),
("AURX_VERIFIED","https://raw.githubusercontent.com/Au1rxx/free-vpn-subscriptions/main/output/v2ray-base64.txt"),
("ANON_DE","https://raw.githubusercontent.com/anonymouskeys/Free-configs-/main/output/countries/de.txt")
]
out=[]
for name,url in urls:
 r=E.curl(url,seconds=25,size=E.NH.MAX_NODE_TEXT)
 row={"name":name,"exit":r.get("exit"),"code":r.get("code"),"bytes":r.get("bytes"),"fetchPath":r.get("fetchPath"),"error":r.get("error")}
 if r.get("exit")==0 and r.get("code")=="200":
  try:
   p=E.NH.parse_blob(r.get("body",""),name);row["parsed"]=len(p.get("nodes") or []);row["parseErrors"]=len(p.get("errors") or [])
  except Exception as ex:row["parseException"]=str(ex)
 out.append(row)
print(json.dumps(out,indent=2))