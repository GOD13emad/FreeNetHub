#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def row(base,rel):
    p=pathlib.Path(base)/rel
    return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
appfiles=["engine.py","directnet.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico","directdpi/Start-DirectDpi.ps1","directdpi/Stop-DirectDpi.ps1","directdpi/hosts.txt","directdpi/LICENSE-zapret.txt","directdpi/tools/winws.exe","directdpi/tools/WinDivert.dll","directdpi/tools/WinDivert64.sys","directdpi/tools/cygwin1.dll","directdns/ctrld.exe","directdns/ctrld.toml","directdns/LICENSE-ctrld.txt"]
manifest={
  "version":"4.2.0",
  "scope":"BROWSER_PROXY_DEFAULT+PC_TUNNEL_WARP+PC_TUNNEL_NODE_CANDIDATE+CONSOLE_GATEWAY_FAIL_CLOSED+NODE_HUB+R36_DIRECT_NETWORK_HARDENING+DIRECT_DPI_ZAPRET_WINDOWS+DIRECT_DNS_CTRLD_WINDOWS",
  "code":[row(R/"app",x) for x in appfiles],
  "coreVersion":"4.0-r36-direct-network-dns-dpi"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
  "releaseRevision":"4.2.0-local-r36-direct-network-dns-dpi",
  "status":"SOURCE_CANDIDATE_WINDOWS_4.2_R36_DIRECT_DNS_DPI",
  "engineSha256":sha(R/"app"/"engine.py"),
  "directNetSha256":sha(R/"app"/"directnet.py"),
  "nodeHubSha256":sha(R/"app"/"nodehub.py"),
  "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
  "viewSha256":sha(R/"app"/"View.xaml"),
  "appManifestSha256":sha(R/"app"/"manifest.json"),
  "installerSha256":None,
  "acceptanceEvidence":"evidence/R36_FINAL_WINDOWS_ACCEPTANCE_20260929.json",
  "installerStatus":"NOT_BUILT_R36_SOURCE_GATE"
})
rel["r36DirectNetwork"]={
  "status":"SOURCE_GATE",
  "noVpnProxyDirectAudit":True,
  "cgnatDetection":"UPNP_WAN_PLUS_RFC6598_CLASSIFICATION",
  "udpTraversal":"STUN_STABLE_MAPPING_PLUS_CROSS_HOST_HOLE_PUNCH_EVIDENCE",
  "encryptedDnsFallback":"CTRLD_1_5_7_CONTROL_D_P0_IPV6_LOOPBACK_NRPT",
  "systemDnsMutation":"NRPT_ONLY_DURING_DIRECT_DPI;ADAPTER_DNS_PRESTATE_PRESERVED",
  "mtuMutation":False,
  "nicMutation":False,
  "vpnGateOpenVpnExcluded":True,
  "publicRelease":False,
  "directDpiWindows":"CTRLD_DOH_IPV6_LOOPBACK_NRPT_PLUS_ZAPRET_HOSTLIST_SCOPED",
  "directDpiVpnProxy":False,
  "directDpiRuntimeEvidence":"evidence/R36_FINAL_WINDOWS_ACCEPTANCE_20260929.json",
  "directDpiRollbackState":"PROGRAMDATA_PREPARED_THEN_ACTIVE"
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({
 "status":"PASS",
 "engineSha256":sha(R/"app"/"engine.py"),
 "directNetSha256":sha(R/"app"/"directnet.py"),
 "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":sha(R/"app"/"View.xaml"),
 "manifestSha256":sha(R/"app"/"manifest.json"),
 "releaseSha256":sha(rp)
},indent=2))
