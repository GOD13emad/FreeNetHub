from __future__ import annotations
import importlib.util,json,pathlib,time
R=pathlib.Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("E",R/"app"/"engine.py");E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
E.ROOT=R;E.APP=R/"app";E.JOB="";E.DEADLINE=time.monotonic()+540
s=E.read(R/"settings.json",{}) or {};s["country"]="SG";E.write(R/"settings.json",s)
rr=E.node_refresh_public(True)
p=E.node_system_preflight_auto()
if not p.get("systemEligible") or str(p.get("country") or "").upper()!="SG" or str(p.get("udpCountry") or "").upper()!="SG":
 raise SystemExit("AUTO_NODE_PREFLIGHT_FAILED")
print(json.dumps({"status":"PASS","refresh":{"total":rr.get("total"),"reachable":rr.get("reachable"),"sources":rr.get("sources"),"failedSources":rr.get("failedSources")},"selected":p.get("selected"),"country":p.get("country"),"udpCountry":p.get("udpCountry"),"pingMs":p.get("pingMs"),"downloadMbps":p.get("downloadMbps"),"uploadMbps":p.get("uploadMbps"),"selectionPolicy":p.get("selectionPolicy")},indent=2))
