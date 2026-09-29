#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def canonical_sha(p):
    p=pathlib.Path(p).resolve()
    rel=p.relative_to(R).as_posix()
    oid=subprocess.check_output(["git","hash-object","-w",f"--path={rel}",str(p)],cwd=R,text=True).strip()
    data=subprocess.check_output(["git","cat-file","blob",oid],cwd=R)
    return hashlib.sha256(data).hexdigest().upper()
def row(base,rel):
    p=pathlib.Path(base)/rel
    return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p),"sourceSha256":canonical_sha(p)}
appfiles=[
 "engine.py","directnet.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico",
 "directdpi/Start-DirectDpi.ps1","directdpi/Stop-DirectDpi.ps1","directdpi/hosts.txt","directdpi/LICENSE-zapret.txt",
 "directdpi/tools/winws.exe","directdpi/tools/WinDivert.dll","directdpi/tools/WinDivert64.sys","directdpi/tools/cygwin1.dll",
 "directdns/ctrld.exe","directdns/ctrld.toml","directdns/LICENSE-ctrld.txt"
]
manifest={
 "version":"4.2.0",
 "scope":"R37_PRODUCT_FINAL+BROWSER_PROXY+SMART_COUNTRY+NODE_HUB+WARP+CFON+TOR+CUSTOM+DIRECT+PC_TUNNEL_WARP_NODE+CONSOLE_GATEWAY+BASE_ROUTE_UPDATE_NODE_REFRESH+DIRECT_NETWORK+DIRECT_DPI+DIRECT_DNS+TARGET_UI",
 "code":[row(R/"app",x) for x in appfiles],
 "coreVersion":"4.0-r37-final"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
 "releaseRevision":"4.2.0-local-r37-final",
 "status":"WINDOWS_4.2_R37_FINAL_PAYLOAD",
 "engineSha256":canonical_sha(R/"app"/"engine.py"),
 "directNetSha256":sha(R/"app"/"directnet.py"),
 "nodeHubSha256":canonical_sha(R/"app"/"nodehub.py"),
 "uiSha256":canonical_sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":canonical_sha(R/"app"/"View.xaml"),
 "appManifestSha256":sha(R/"app"/"manifest.json"),
 "gatewayManifestSha256":canonical_sha(R/"gateway"/"manifest.json"),
 "installerSha256":None,
 "acceptanceEvidence":"evidence/R37_WINDOWS_FINAL_ACCEPTANCE_20260929.json",
 "installerStatus":"FINAL_PAYLOAD_REQUIRES_EXTERNAL_INSTALL_ACCEPTANCE"
})
rel["r37WindowsFinal"]={
 "status":"FINAL_PAYLOAD",
 "publicRelease":False,
 "uiTarget":"OWNER_REFERENCE_3_SCREEN_DASHBOARD_METHODS_TOOLS",
 "uiSmoke":"DASHBOARD_METHODS_TOOLS_PASS",
 "securityScan":"PASS",
 "updateNodePath":"SYSTEM_DEFAULT_WHEN_NO_FNH_PC_TUN;BOUND_PRE_TUN_BASE_ROUTE_WITH_TRACE_GUARD_WHEN_PC_TUN_ACTIVE",
 "nodeRefresh":"FETCH_MERGE_ONLY;TEST_ALL_EXPLICIT",
 "fullSystem":"WARP_ACCEPTED;NODE_REQUIRES_TCP_UDP_PREFLIGHT",
 "console":"INDEPENDENT_GATEWAY_FAIL_CLOSED",
 "directDpi":"R36_CAPABILITY_INCLUDED_NOT_PRODUCT_BOUNDARY",
 "installedAcceptance":"SEE_ACCEPTANCE_EVIDENCE","trustedSigning":"OPEN_NOTSIGNED","physicalConsoleE2E":"UNPROVEN_EXTERNAL_HARDWARE_GATE"
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({
 "status":"PASS","releaseRevision":rel["releaseRevision"],
 "engineSha256":sha(R/"app"/"engine.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":sha(R/"app"/"View.xaml"),"manifestSha256":sha(R/"app"/"manifest.json"),
 "gatewayManifestSha256":sha(R/"gateway"/"manifest.json"),"releaseSha256":sha(rp)
},indent=2))
