import importlib.util, json, pathlib, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fnh_engine_r34", ROOT/"app"/"engine.py")
E=importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
E.JOB=""
E.DEADLINE=time.monotonic()+90

def run(name, fn):
    print("BEGIN",name,flush=True)
    t=time.monotonic()
    try:
        v=fn()
        row={"name":name,"seconds":round(time.monotonic()-t,3),"ok":True,"value":v}
    except Exception as e:
        row={"name":name,"seconds":round(time.monotonic()-t,3),"ok":False,"error":type(e).__name__+": "+str(e)}
    print(json.dumps(row,ensure_ascii=False),flush=True)

run("direct_route", E.direct_route)
run("trace", lambda:E.curl("https://www.cloudflare.com/cdn-cgi/trace","",seconds=8))
run("youtube204", lambda:E.curl("https://www.youtube.com/generate_204","",seconds=8,body=False))
run("ping_direct", E.ping_direct)
run("download_500k", lambda:E.curl("https://speed.cloudflare.com/__down?bytes=500000","",seconds=10,body=False,size=565536))
run("upload_250k", lambda:E.cloudflare_upload(250000,10,""))
