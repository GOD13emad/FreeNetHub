#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def row(base,rel):
 p=pathlib.Path(base)/rel
 return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
appfiles=["engine.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico"]
manifest={
 "version":"4.2.0",
 "scope":"BROWSER_PROXY_DEFAULT+OPTIONAL_PC_TUNNEL+CONSOLE_GATEWAY+NODE_HUB+R30_UI_FIDELITY",
 "code":[row(R/"app",x) for x in appfiles],
 "coreVersion":"4.0-r30-ui-fidelity"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
 "releaseRevision":"4.2.0-local-r30-ui-fidelity",
 "status":"LOCAL_CANDIDATE_WINDOWS_4.2_R30_UI_FIDELITY_OWNER_REVIEW",
 "engineSha256":sha(R/"app"/"engine.py"),
 "nodeHubSha256":sha(R/"app"/"nodehub.py"),
 "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":sha(R/"app"/"View.xaml"),
 "appManifestSha256":sha(R/"app"/"manifest.json"),
 "installerStatus":"R30_UI_FIDELITY_BUILD_PENDING"
})
rel["r30UiFidelity"]={
 "status":"OWNER_REVIEW_PENDING",
 "reason":"R29 layout rejected by owner as visually inconsistent with approved mockup",
 "navigation":["اتصال","سرورها / نودها","روش‌ها و تنظیمات پیشرفته","کنسول","ابزارها و آپدیت"],
 "connectionScreen":{
   "step1":"SEGMENTED_SCOPE_CARDS",
   "step2":"SEVEN_METHOD_CARDS_WITH_CAPABILITY_BADGES",
   "step3":"PRECONNECT_BENCHMARK_TABLE",
   "step4":"SINGLE_PRIMARY_CONNECT_ACTION"
 },
 "sidebar":["selectedScope","selectedMethod","targetCountry","lastMetrics","baseSystemUpdatePolicy"],
 "customDarkNavigation":True,
 "selectedCardHighlighting":True,
 "runtimeEngineChanged":False,
 "publicRelease":False
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":"PASS","engineSha256":sha(R/"app"/"engine.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),"viewSha256":sha(R/"app"/"View.xaml"),"manifestSha256":sha(R/"app"/"manifest.json"),"releaseSha256":sha(rp)},indent=2))
