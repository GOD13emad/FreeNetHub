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
 "scope":"R40_LIFECYCLE_SAFE+BROWSER_PROXY+NODE_HUB+WARP+CFON+TOR+CUSTOM+DIRECT+PC_TUNNEL_WARP_NODE+CONSOLE_GATEWAY+ONLINE_UPDATE+NOADMIN_NORMAL_LAUNCH+VERIFIED_EXIT_ROLLBACK",
 "code":[row(R/"app",x) for x in appfiles],
 "coreVersion":"4.0-r40-lifecycle-safe"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
 "releaseRevision":"4.2.0-local-r40-lifecycle-safe",
 "status":"R40_LIFECYCLE_SAFE_CANDIDATE",
 "engineSha256":canonical_sha(R/"app"/"engine.py"),
 "directNetSha256":sha(R/"app"/"directnet.py"),
 "nodeHubSha256":canonical_sha(R/"app"/"nodehub.py"),
 "uiSha256":canonical_sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":canonical_sha(R/"app"/"View.xaml"),
 "appManifestSha256":sha(R/"app"/"manifest.json"),
 "gatewayManifestSha256":canonical_sha(R/"gateway"/"manifest.json"),
 "desktopShellSha256":sha(R/"windows"/"standalone"/"FreeNetHub.exe"),
 "crossPlatformManifestSha256":canonical_sha(R/"crossplatform"/"MANIFEST.json"),
 "installerSha256":None,
 "acceptanceEvidence":"evidence/R40_DEEP_AUDIT_ACCEPTANCE_20260930.json",
 "installerStatus":"DIGEST_IN_EXTERNAL_ACCEPTANCE_EVIDENCE"
})
rel.setdefault("crossPlatform",{})["linux"]="CANDIDATE_NATIVE_LINUX_4.2_SOFTWARE_RELEASE_R13_R40_LIFECYCLE_SAFE"
rel.setdefault("postReleaseMainDelta",{})["nativeLinuxVersion"]="4.2.0-linux.13-r40"
rel["r40LifecycleSafe"]={
 "status":"CANDIDATE",
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
