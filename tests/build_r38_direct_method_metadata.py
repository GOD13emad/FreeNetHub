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
 "scope":"R38_DIRECT_METHOD_INTEGRATION+BROWSER_PROXY+SMART_COUNTRY+NODE_HUB+WARP+CFON+TOR+CUSTOM+DIRECT+PC_TUNNEL_WARP_NODE+CONSOLE_GATEWAY+BASE_ROUTE_UPDATE_NODE_REFRESH+DIRECT_NETWORK+DIRECT_DPI+DIRECT_DNS+TARGET_UI",
 "code":[row(R/"app",x) for x in appfiles],
 "coreVersion":"4.0-r38-direct-method"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
 "releaseRevision":"4.2.0-local-r38-direct-method",
 "status":"WINDOWS_4.2_R38_DIRECT_METHOD_LOCAL_FINAL",
 "engineSha256":canonical_sha(R/"app"/"engine.py"),
 "directNetSha256":sha(R/"app"/"directnet.py"),
 "nodeHubSha256":canonical_sha(R/"app"/"nodehub.py"),
 "uiSha256":canonical_sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":canonical_sha(R/"app"/"View.xaml"),
 "appManifestSha256":sha(R/"app"/"manifest.json"),
 "gatewayManifestSha256":canonical_sha(R/"gateway"/"manifest.json"),
 "installerSha256":None,
 "acceptanceEvidence":"evidence/R38_WINDOWS_DIRECT_METHOD_INSTALL_ACCEPTANCE_20260929.json",
 "installerStatus":"R38_LOCAL_INSTALL_ACCEPTED_NOT_PUBLIC_RELEASE"
})
rel["r38DirectMethod"]={
 "status":"PASS_LOCAL_FINAL",
 "publicRelease":False,
 "architecture":"LOOPBACK_ULA_CTRLD_DOH_NRPT_PLUS_ZAPRET",
 "twoCycleIntegration":"PASS",
 "adapterDnsMutation":False,
 "vpnProxyDefaultRoute":False,
 "exactRollback":"PASS",
 "installedAcceptance":"PASS",
 "trustedSigning":"OPEN_NOTSIGNED"
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":"PASS","releaseRevision":rel["releaseRevision"],"manifestSha256":sha(R/"app"/"manifest.json"),"releaseSha256":sha(rp)},indent=2))
