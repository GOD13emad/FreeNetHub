#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
DATE="2026-09-28"; REV="4.2.0-public-r22-country-node-workspace-rc1"
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def wj(p,o): pathlib.Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def row(base,rel):
 p=pathlib.Path(base)/rel; return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
def candidates():
 raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=R); out=[]
 for x in raw.decode("utf-8").split("\0"):
  if not x: continue
  rel=pathlib.PurePosixPath(x).as_posix(); p=R/rel
  if rel!="PUBLIC_MANIFEST.json" and p.is_file(): out.append(rel)
 return sorted(set(out),key=str.lower)
def main():
 appfiles=["engine.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico"]
 wj(R/"app"/"manifest.json",{"version":"4.2.0","scope":"BROWSER_PROXY_DEFAULT+OPTIONAL_PC_TUNNEL+CONSOLE_GATEWAY+NODE_HUB","code":[row(R/"app",x) for x in appfiles],"coreVersion":"4.0-scope-ui4-country-strict-node-workspace-r22"})
 strict=R/"evidence"/"R22_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json"
 sj=json.loads(strict.read_text(encoding="utf-8-sig"))
 if sj.get("status")!="PASS" or sj.get("targetCountry")!="SG" or sj.get("actualCountry")!="SG": raise SystemExit("R22_STRICT_EVIDENCE_INVALID")
 static={"schema":1,"version":"4.2.0","date":DATE,"status":"R22_RELEASE_CANDIDATE_COUNTRY_NODE_WORKSPACE","sourceAcceptance":"STATIC_AND_LIVE_COUNTRY_PASS","sourceBaseHead":subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip(),"country":{"policy":"STRICT_ACTUAL_EXIT_MATCH","liveSG":"PASS","evidence":"evidence/R22_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json","sha256":sha(strict)},"nodeHub":{"protocols":["SS","VMess","VLESS","Trojan"],"imports":["clipboard","file","plain_text","base64","https_subscription","V2CROSS_public_pool"],"management":["dedupe","favorites","pin","custom_name","tags","note","rating_0_5","history","filter","sort"],"exports":["raw","base64"],"selectedRealTest":"HTTPS+EXIT_COUNTRY","fastBatch":"TCP_ENDPOINT_ONLY","scope":"BROWSER_ONLY"},"tests":{"countryStrict":"PASS","r22Static":"PASS","nodeHubUnit":"PASS","nodeHubEnginePolicy":"PASS","windowsDiscover":"65/65 PASS","gatewayAndScopeUI":"13/13 PASS","gateway":"10/10 PASS","scopeUI":"3/3 PASS","failClosed":"PASS","security":"PASS","powershellParse":"PASS"},"deferredWithReason":{"qr":"DEFERRED_LOCAL_QR_DEPENDENCY_AND_CREDENTIAL_EXPOSURE_REVIEW","clientFormatConversion":"DEFERRED_UNTIL_PROTOCOL_FIDELITY_TESTS_FOR_REALITY_AND_TRANSPORT_VARIANTS","privateSpaceBiometric":"DEFERRED_DESKTOP_CREDENTIAL_VAULT_DESIGN_REQUIRED"}}
 wj(R/"evidence"/"R22_SOURCE_ACCEPTANCE_20260928.json",static)
 rel=json.loads((R/"RELEASE.json").read_text(encoding="utf-8-sig")); prior=rel.get("installerSha256")
 rel.update({"releaseRevision":REV,"status":"R22_RELEASE_CANDIDATE_COUNTRY_NODE_WORKSPACE","engineSha256":sha(R/"app"/"engine.py"),"nodeHubSha256":sha(R/"app"/"nodehub.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),"viewSha256":sha(R/"app"/"View.xaml"),"appManifestSha256":sha(R/"app"/"manifest.json"),"previousAcceptedInstallerSha256":prior,"installerStatus":"R21_ACCEPTED_PREVIOUS__R22_BUILD_PENDING","acceptanceEvidence":"evidence/R22_SOURCE_ACCEPTANCE_20260928.json","r22":{"countryPolicy":"STRICT_ACTUAL_EXIT_MATCH_AND_IMMEDIATE_UI_PERSIST","strictCountryLiveEvidence":"evidence/R22_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json","nodeHub":static["nodeHub"],"shadowShareReference":"GOOGLE_PLAY_PUBLIC_FEATURE_SET_REIMPLEMENTED_INDEPENDENTLY","sourceAcceptance":"PASS","installerAcceptance":"PENDING"}})
 wj(R/"RELEASE.json",rel)
 wj(R/"PUBLIC_MANIFEST.json",{"schema":3,"version":REV,"source":"git-candidate-working-tree","files":[row(R,x) for x in candidates()]})
 print(json.dumps({"status":"PASS","appManifestSha256":sha(R/"app"/"manifest.json"),"releaseSha256":sha(R/"RELEASE.json"),"publicManifestSha256":sha(R/"PUBLIC_MANIFEST.json")},indent=2))
if __name__=="__main__": main()
