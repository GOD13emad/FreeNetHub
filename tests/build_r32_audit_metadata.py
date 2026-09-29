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
 "scope":"BROWSER_PROXY_DEFAULT+PC_TUNNEL_WARP+CONSOLE_GATEWAY_FAIL_CLOSED+NODE_HUB+R32_AUDIT_CLOSURE",
 "code":[row(R/"app",x) for x in appfiles],
 "coreVersion":"4.0-r32-audit-closure"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
 "releaseRevision":"4.2.0-local-r32-audit-closure",
 "status":"LOCAL_CANDIDATE_WINDOWS_4.2_R32_AUDIT_CLOSURE_OWNER_REVIEW",
 "engineSha256":sha(R/"app"/"engine.py"),
 "nodeHubSha256":sha(R/"app"/"nodehub.py"),
 "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":sha(R/"app"/"View.xaml"),
 "appManifestSha256":sha(R/"app"/"manifest.json"),
 "installerSha256":None,
 "acceptanceEvidence":"evidence/R32_AUDIT_CLOSURE_ACCEPTANCE_20260928.json",
 "installerStatus":"R32_AUDIT_CLOSURE_BUILD_PENDING"
})
rel["r32AuditClosure"]={
 "status":"OWNER_REVIEW_PENDING",
 "themeContrast":{"wcagAaNormalText":True,"lightMutedWorstCaseRatio":4.98,"lightAccentUpdatePanelRatio":4.75,"darkTheme":True},
 "preconnectSemantics":{"browser":"SELECTED_PROVIDER","system":"FINAL_WARP_PATH","console":"LOCAL_PROVIDER_ONLY_WHEN_CONFIGURED"},
 "consoleCapability":{"connectFailClosedWithoutProviderOrProfile":True,"preflightFailClosedWithoutLocalProvider":True,"missingRouteShownInUi":True,"setupButtonVisible":True},
 "developerRuntime":{"installedPinnedPythonPreferred":True,"sourcePathPythonFallback":True},
 "updateRouting":"SYSTEM_DEFAULT_ROUTE_WITH_FREENETHUB_PROXY_BYPASS",
 "knownOpen":{"allProviderFullSystem":True,"wireguardProfilePreconnectSpeed":True,"trustedSigning":True,"physicalConsoleE2E":True},
 "publicRelease":False
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":"PASS","engineSha256":sha(R/"app"/"engine.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),"viewSha256":sha(R/"app"/"View.xaml"),"manifestSha256":sha(R/"app"/"manifest.json"),"releaseSha256":sha(rp)},indent=2))
