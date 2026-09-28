#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def row(base,rel):
 p=pathlib.Path(base)/rel
 return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
def main():
 appfiles=["engine.py","nodehub.py","FreeNetHub.ps1","View.xaml","assets/FreeNetHub.ico"]
 out={"version":"4.2.0","scope":"BROWSER_PROXY_DEFAULT+OPTIONAL_PC_TUNNEL+CONSOLE_GATEWAY+PROVIDER_CAPABILITY_UI+NODE_PERFORMANCE+SMART_PUBLIC_REFRESH+GITHUB_UPDATE","code":[row(R/"app",x) for x in appfiles],"coreVersion":"4.0-r28-final-transport-compat-provider-metrics-refresh-update"}
 (R/"app"/"manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
 rp=R/"RELEASE.json";rel=json.loads(rp.read_text(encoding="utf-8-sig"))
 rel.update({"releaseRevision":"4.2.0-local-r28-final","status":"LOCAL_CANDIDATE_WINDOWS_4.2_R28_FINAL_CURRENT","engineSha256":sha(R/"app"/"engine.py"),"nodeHubSha256":sha(R/"app"/"nodehub.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),"viewSha256":sha(R/"app"/"View.xaml"),"appManifestSha256":sha(R/"app"/"manifest.json"),"installerStatus":"R28_FINAL_CURRENT_BUILD_PENDING"})
 rel.pop("r28Preview",None)
 rel["r28"]={"status":"FINAL_CURRENT_PENDING_EXACT_ARTIFACT_ACCEPTANCE","providerCapabilityUi":True,"defaultScope":"BROWSER_ONLY","fullSystem":"WARP_EXPLICIT_ONLY","console":"SEPARATE_GATEWAY","metrics":["PING_OR_REAL_DELAY","DOWNLOAD_MBPS","UPLOAD_MBPS"],"nodeProtocols":["SS","VMESS","VLESS","TROJAN","HYSTERIA2"],"publicRefresh":{"ttlSeconds":1800,"uiRollingMinutes":30,"endpointRegistry":10,"independentFamilies":5,"stalePolicy":"DROP_ONLY_SUCCESSFULLY_REFRESHED_PUBLIC_SOURCES_PRESERVE_FAILED_SOURCE_CACHE_AND_MANUAL_FAVORITE_PINNED"},"nodeBenchmark":{"boundedMax":4,"persistPerformanceHistory":True,"rollingMinutes":10},"githubSelfUpdate":"CHECK_DOWNLOAD_SHA256_VERIFY_CONFIRM_INSTALL","protocolCompatibility":{"trojanDefaultTls":True,"wsEarlyData":True,"legacyTrojanWs":True,"httpHeaderTransport":True,"httpUpgradeHostFix":True,"quicTransport":True,"unsupportedXhttpKcpFailClosed":True},"benchmarkDiversity":"UNDERTESTED_PROTOCOL_THEN_SOURCE","publicRelease":False}
 rp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
 print(json.dumps({"status":"PASS","engineSha256":sha(R/"app"/"engine.py"),"nodeHubSha256":sha(R/"app"/"nodehub.py"),"uiSha256":sha(R/"app"/"FreeNetHub.ps1"),"viewSha256":sha(R/"app"/"View.xaml"),"appManifestSha256":sha(R/"app"/"manifest.json"),"releaseSha256":sha(rp)},indent=2))
if __name__=="__main__":main()
