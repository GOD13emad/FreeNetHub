import json, hashlib, os, pathlib
S = pathlib.Path(__file__).resolve().parent.parent
I = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Programs" / "FreeNetHub"
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
am = json.loads((S/"app/manifest.json").read_text(encoding="utf-8"))
gm = json.loads((S/"gateway/manifest.json").read_text(encoding="utf-8"))
app=[]; gateway=[]; ok=True
for x in am["code"]:
    sp=S/"app"/x["file"]; ip=I/"app"/x["file"]
    same=sp.is_file() and ip.is_file() and h(sp)==h(ip)==x["sha256"].upper()
    app.append({"file":x["file"],"same":same}); ok=ok and same
for x in gm["files"]:
    sp=S/"gateway"/x["file"]; ip=I/"gateway"/x["file"]
    same=sp.is_file() and ip.is_file() and h(sp)==h(ip)==x["sha256"].upper()
    gateway.append({"file":x["file"],"same":same}); ok=ok and same
print(json.dumps({"status":"PASS" if ok else "FAIL","appCount":len(app),"gatewayCount":len(gateway),"appMismatches":[x for x in app if not x["same"]],"gatewayMismatches":[x for x in gateway if not x["same"]]}))
