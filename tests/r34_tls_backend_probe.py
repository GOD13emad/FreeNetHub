import json, ssl, urllib.request, urllib.error, time

URLS=[
 "https://www.youtube.com/",
 "https://chatgpt.com/",
 "https://auth.openai.com/",
 "https://gemini.google.com/",
 "https://github.com/",
]
ctx=ssl.create_default_context()
opener=urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(context=ctx),
)
out={"openssl":ssl.OPENSSL_VERSION,"results":[]}
for url in URLS:
    t=time.time()
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 FreeNetHub-DirectProbe/1.0"})
        with opener.open(req,timeout=6) as resp:
            out["results"].append({"url":url,"status":resp.status,"final":resp.geturl(),"seconds":round(time.time()-t,3)})
    except urllib.error.HTTPError as e:
        out["results"].append({"url":url,"status":e.code,"final":e.geturl(),"seconds":round(time.time()-t,3),"httpError":True})
    except Exception as e:
        out["results"].append({"url":url,"seconds":round(time.time()-t,3),"error":type(e).__name__+": "+str(e)})
print(json.dumps(out,indent=2))
