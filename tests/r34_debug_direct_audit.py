import importlib.util, pathlib, sys, traceback, time, json
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fnh_engine",ROOT/"app"/"engine.py")
E=importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
E.JOB=""; E.DEADLINE=time.monotonic()+60

def step(name,fn):
    try:
        v=fn()
        print(name,"PASS",json.dumps(v,ensure_ascii=False,default=str)[:5000])
        return v
    except Exception as e:
        print(name,"FAIL",type(e).__name__,repr(str(e)))
        traceback.print_exc()
        return None

route=step("direct_route",E.direct_route)
if route:
    step("adapter_snapshot",lambda:E.direct_adapter_snapshot(route))
    step("dn_audit",lambda:E.DN.audit(str(route.get("ip") or ""),str(route.get("nextHop") or "")))
step("curl_openai",lambda:E.curl("https://api.openai.com/v1/models","",6,False,65536))
step("curl_github",lambda:E.curl("https://github.com/","",6,False,65536))
step("curl_google",lambda:E.curl("https://www.google.com/generate_204","",6,False,65536))
step("curl_youtube",lambda:E.curl("https://www.youtube.com/generate_204","",6,False,65536))
step("direct_network_audit",E.direct_network_audit)
