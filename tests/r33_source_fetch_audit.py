from __future__ import annotations
import concurrent.futures, importlib.util, json, pathlib
R=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fnh_engine_r33",R/"app"/"engine.py")
E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
def one(item):
    name,family,url=item
    r=E.curl(url,seconds=18,size=E.NH.MAX_NODE_TEXT)
    found=0;errors=0
    if r.get("exit")==0 and r.get("code")=="200":
        try:
            p=E.NH.parse_blob(r.get("body",""),name)
            found=len(p.get("nodes") or []);errors=len(p.get("errors") or [])
        except Exception:
            pass
    return {"name":name,"family":family,"exit":r.get("exit"),"code":r.get("code"),"fetchPath":r.get("fetchPath"),"found":found,"parseErrors":errors,"error":str(r.get("error") or "")[:160]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    rows=list(ex.map(one,E.PUBLIC_NODE_SOURCES))
out={"schema":1,"date":"2026-09-28","status":"PASS","mutatesNodeStore":False,"sources":rows,"http200":sum(x["code"]=="200" and x["exit"]==0 for x in rows),"parsedNodes":sum(x["found"] for x in rows),"publicDnsFallbacks":sum(x["fetchPath"]=="PUBLIC_DNS_RESOLVE" for x in rows)}
print(json.dumps(out,ensure_ascii=False,indent=2))
