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
  "scope":"BROWSER_PROXY_DEFAULT+PC_TUNNEL_WARP+PC_TUNNEL_NODE_CANDIDATE+CONSOLE_GATEWAY_FAIL_CLOSED+NODE_HUB+R35_CAPABILITY_CANDIDATE",
  "code":[row(R/"app",x) for x in appfiles],
  "coreVersion":"4.0-r35-capability-candidate"
}
(R/"app"/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
rel.update({
  "releaseRevision":"4.2.0-local-r35-capability-candidate",
  "status":"SOURCE_CANDIDATE_WINDOWS_4.2_R35_LIVE_SYSTEM_PENDING",
  "engineSha256":sha(R/"app"/"engine.py"),
  "nodeHubSha256":sha(R/"app"/"nodehub.py"),
  "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
  "viewSha256":sha(R/"app"/"View.xaml"),
  "appManifestSha256":sha(R/"app"/"manifest.json"),
  "installerSha256":None,
  "acceptanceEvidence":"evidence/R35_SOURCE_GATE_ACCEPTANCE_20260928.json",
  "installerStatus":"NOT_BUILT_LIVE_SYSTEM_PENDING"
})
rel["r35CapabilityCandidate"]={
  "status":"SOURCE_GATE_PENDING_LIVE_SYSTEM",
  "baseInstalledAuthority":"4.2.0-local-r32-audit-closure",
  "browserPreconnect":"SELECTED_PROVIDER",
  "systemProviders":{"WARP":"ACCEPTED_BASELINE","NODE":"CANDIDATE_TCP_UDP_STRICT"},
  "nodeSystemPolicy":"STRICT_HTTPS_TCP_COUNTRY_PLUS_SOCKS5_UDP_STUN_PLUS_POST_TUN_TCP_UDP_COUNTRY",
  "directBootstrapRecovery":"SYSTEM_ROUTE_WITH_PUBLIC_DNS_RESOLVE_FALLBACK_NO_FNH_PROXY",
  "publicNodeSources":"EXPANDED_AND_COUNTRY_SHARDED",
  "console":"FAIL_CLOSED_WITHOUT_PROVIDER_OR_PROFILE",
  "vpnGateOpenVpnExcluded":True,
  "publicRelease":False,
  "installAllowed":False
}
rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({
 "status":"PASS",
 "engineSha256":sha(R/"app"/"engine.py"),
 "nodeHubSha256":sha(R/"app"/"nodehub.py"),
 "uiSha256":sha(R/"app"/"FreeNetHub.ps1"),
 "viewSha256":sha(R/"app"/"View.xaml"),
 "manifestSha256":sha(R/"app"/"manifest.json"),
 "releaseSha256":sha(rp)
},indent=2))
