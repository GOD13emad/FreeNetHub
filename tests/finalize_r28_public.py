#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent.parent
STATUS="LOCAL_ACCEPTED_WINDOWS_4.2_R28_FINAL"
EXPECTED={
 "app/engine.py":"9D9DC7724D05BF8C58986ABE760C9CF0A127F09816046D8984617CBE9A9C8658",
 "app/nodehub.py":"A5C5A1D62B63EA3806D3B2C8BF53A31D7AD491F057DD353EE666A38791320A07",
 "app/FreeNetHub.ps1":"6D37EEDAFBE475C785176B50CEBEE11EBA455CF8E6760E0C95DE9D1A0E446C60",
 "app/View.xaml":"3B170D89488940EEF41503E00FD6DD7AC9C0EAFDCDB7CF53532BDDEBF8AE7E0C",
 "app/manifest.json":"F82910D2755B78F34FAD59463832F2A7CA8D2849EBBF1E2EBD81F8EF1BDE84EF",
 "gateway/manifest.json":"ACBC3A9622A75A7807C07A9DEC6D6A9FC310A527AEA185A1C4ED7552FB4E4966",
 "Uninstall-FreeNetHub.ps1":"DA9DF80E9AE19627BC665659306C9AB94EDAD25E5BD61E3E8AB90634F3532532",
}
INSTALLER=R/"delivery/github_v4.2.0/FreeNetHub_4.2.0_R28_Final_Setup.exe"
INSTALLER_SHA="2AA91D849A513A21D3BF9903F8E72FFB6A184D378FB357CE4FA7A9D6F7EB0073"
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def load(rel): return json.loads((R/rel).read_text(encoding="utf-8-sig"))
def dump(rel,obj): (R/rel).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def assert_pass(rel):
 j=load(rel)
 if j.get("status")!="PASS": raise SystemExit("EVIDENCE_NOT_PASS_"+rel)
 return j
for rel,want in EXPECTED.items():
 if sha(R/rel)!=want: raise SystemExit("SOURCE_DRIFT_"+rel)
if sha(INSTALLER)!=INSTALLER_SHA: raise SystemExit("INSTALLER_DRIFT")
install=assert_pass("evidence/R28_FINAL_INSTALL_ACCEPTANCE_20260928.json")
qual=assert_pass("evidence/R28_FINAL_QUALIFICATION_ACCEPTANCE_20260928.json")
live=assert_pass("evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json")
smoke=load("evidence/R28_FINAL_INSTALLED_SMOKE_20260928.json")
if smoke.get("accepted") is not True: raise SystemExit("SMOKE_NOT_ACCEPTED")
transport=assert_pass("evidence/R28_TRANSPORT_COMPAT_ACCEPTANCE_20260928.json")
knowledge={
 "schema":2,"project":"Open Internet Gateway / FreeNet Hub","date":"2026-09-28","status":"CURRENT_R28_LOCAL_ACCEPTED",
 "records":[
  {"claim":"R28 provider-specific Windows UI exposes Smart, Node Pool, WARP, CFON, Tor, Custom, console and GitHub update controls; browser-only remains default and full-system is explicit WARP only.","evidence":["app/View.xaml","app/FreeNetHub.ps1"],"status":"CONFIRMED"},
  {"claim":"Public-node refresh uses 10 HTTPS endpoints across 5 independent families with a 30-minute TTL and drops stale nodes only for sources that refreshed successfully, preserving failed-source cache and manual/favorite/pinned entries.","evidence":["app/engine.py","evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json"],"status":"CONFIRMED"},
  {"claim":"Installed-product refresh on the final payload succeeded for all 10 sources / 5 families: 467 raw, 460 unique, 308 TCP-reachable and 33 stale entries dropped in that bounded run.","evidence":["evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json"],"status":"CONFIRMED_SAMPLE"},
  {"claim":"Direct speed uses the host physical route and bypasses the app proxy; WARP benchmark measures a verified proxy path. Final live sample measured ping/download/upload for both paths.","evidence":["evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json"],"status":"CONFIRMED_SAMPLE"},
  {"claim":"Node throughput is only shown after a verified path; failed public nodes retain real endpoint ping where available and report download/upload as N/A rather than fabricated values.","evidence":["app/engine.py","tests/test_engine.py","evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json"],"status":"CONFIRMED"},
  {"claim":"R28 handles SS/VMess/VLESS/Trojan/Hysteria2 and tested transport compatibility includes Trojan default TLS, WebSocket early-data, HTTP/H2, HTTPUpgrade, QUIC and Reality alias handling.","evidence":["app/nodehub.py","evidence/R28_TRANSPORT_COMPAT_ACCEPTANCE_20260928.json"],"status":"CONFIRMED"},
  {"claim":"Uninstall race with a finishing background engine job was root-caused and prevented by exact-job cancellation, bounded drain and narrow retry; isolated clean-install qualification ends with no install-root residue or project listeners.","evidence":["Uninstall-FreeNetHub.ps1","evidence/R28_FINAL_QUALIFICATION_ACCEPTANCE_20260928.json"],"status":"CONFIRMED"},
  {"claim":"Exact final installer upgraded the real installation while preserving settings, node pool and refresh metadata; installed source parity and desktop smoke passed.","evidence":["evidence/R28_FINAL_INSTALL_ACCEPTANCE_20260928.json","evidence/R28_FINAL_INSTALLED_SMOKE_20260928.json"],"status":"CONFIRMED"}
 ],
 "limitations":[
  "Final Windows installer is Authenticode NotSigned; trusted public code signing is an external gate.",
  "Physical console game/country end-to-end remains unproven unless real console traffic is attached.",
  "Public-node availability is external and ephemeral; a reachable TCP endpoint is not treated as verified proxy throughput."
 ]
}
dump("evidence/R28_PROJECT_KNOWLEDGE_20260928.json",knowledge)
final={
 "schema":3,"version":"4.2.0","date":"2026-09-28","product":"Open Internet Gateway / FreeNet Hub","status":STATUS,
 "authority":{"releaseRevision":"4.2.0-local-r28-final","installer":{"file":"delivery/github_v4.2.0/FreeNetHub_4.2.0_R28_Final_Setup.exe","sha256":INSTALLER_SHA,"bytes":INSTALLER.stat().st_size,"authenticode":"NotSigned"}},
 "sourceHashes":{k:v for k,v in EXPECTED.items()},
 "verification":{
  "staticRegression":{"status":"PASS","coreTests":89,"gatewayScopeTests":14,"uiContract":"PASS","strictCountry":"PASS","transportCompatibility":"PASS","failClosed":"PASS"},
  "qualification":{"status":"PASS","evidence":"evidence/R28_FINAL_QUALIFICATION_ACCEPTANCE_20260928.json","sha256":sha(R/"evidence/R28_FINAL_QUALIFICATION_ACCEPTANCE_20260928.json"),"cleanInstall":True,"smoke":True,"uninstall":True,"residueRoot":False,"listenersAfter":0},
  "productionInstall":{"status":"PASS","evidence":"evidence/R28_FINAL_INSTALL_ACCEPTANCE_20260928.json","sha256":sha(R/"evidence/R28_FINAL_INSTALL_ACCEPTANCE_20260928.json"),"sourceParity":True,"userStatePreserved":True},
  "installedSmoke":{"status":"PASS","evidence":"evidence/R28_FINAL_INSTALLED_SMOKE_20260928.json","sha256":sha(R/"evidence/R28_FINAL_INSTALLED_SMOKE_20260928.json"),"singleInstance":True,"trayRestore":True,"noAttributedTerminal":True,"idleListeners":0},
  "live":{"status":"PASS","evidence":"evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json","sha256":sha(R/"evidence/R28_FINAL_LIVE_ACCEPTANCE_20260928.json"),"publicRefresh":live["publicRefresh"],"direct":live["direct"],"warp":live["warp"],"nodeSample":live["nodeSample"],"cleanup":live["cleanup"]},
  "transport":{"status":"PASS","evidence":"evidence/R28_TRANSPORT_COMPAT_ACCEPTANCE_20260928.json","sha256":sha(R/"evidence/R28_TRANSPORT_COMPAT_ACCEPTANCE_20260928.json")}
 },
 "capabilities":{"defaultScope":"BROWSER_ONLY","fullSystem":"EXPLICIT_WARP_ONLY","console":"SEPARATE_GATEWAY","publicSources":{"endpoints":10,"families":5,"ttlSeconds":1800},"metrics":"PING + VERIFIED DOWNLOAD/UPLOAD; failed/unverified throughput=N/A","githubSelfUpdate":"CHECK -> reject downgrade -> require SHA-256 -> download -> verify -> user confirm -> install"},
 "externalGates":{"trustedWindowsCodeSigning":"OPEN_NOTSIGNED","physicalConsoleGameCountryE2E":"UNPROVEN_WITHOUT_ATTACHED_CONSOLE"},
 "promotion":{"localAcceptance":"PASS","publicTreeSecurity":"TO_VERIFY","hostedCI":"PENDING","githubR28Release":"PENDING"},
 "decision":"R28 Windows payload is locally accepted. Public promotion requires final public-tree/security verification and hosted CI."
}
dump("evidence/R28_FINAL_ACCEPTANCE_20260928.json",final)
rel=load("RELEASE.json")
rel.update({
 "releaseRevision":"4.2.0-local-r28-final","status":STATUS,
 "engineSha256":EXPECTED["app/engine.py"],"nodeHubSha256":EXPECTED["app/nodehub.py"],"uiSha256":EXPECTED["app/FreeNetHub.ps1"],
 "viewSha256":EXPECTED["app/View.xaml"],"appManifestSha256":EXPECTED["app/manifest.json"],
 "gatewayManifestSha256":EXPECTED["gateway/manifest.json"],"installerSha256":INSTALLER_SHA,
 "installerStatus":"R28_FINAL_EXACT_ARTIFACT_ACCEPTED_LOCAL_CI_REQUIRED",
 "acceptanceEvidence":"evidence/R28_FINAL_ACCEPTANCE_20260928.json"
})
rel.setdefault("r28",{}).update({"status":"LOCAL_ACCEPTED_HOSTED_CI_REQUIRED","publicRelease":False,"publicTreeSecurity":"TO_VERIFY","hostedCI":"PENDING","installerAsset":INSTALLER.name})
dump("RELEASE.json",rel)
brain=f"""# PROJECT BRAIN — Open Internet Gateway / FreeNet Hub

Status: CURRENT
Brain version: R28-local-accepted-2026-09-28
Authority: working tree R28 candidate + evidence/R28_FINAL_ACCEPTANCE_20260928.json
Installer: FreeNetHub_4.2.0_R28_Final_Setup.exe
Installer SHA-256: {INSTALLER_SHA}

## Objective / DoD
A self-contained Windows gateway with browser-only default, explicit WARP full-system mode, separate console gateway, provider-specific connection UI, refreshed/tested public node pool, real path metrics, safe update and evidence-backed install/uninstall.

## Roadmap
1. Browser identity/proxy baseline — Completed.
2. Full-system WARP with rollback — Completed.
3. Separate console gateway software path — Completed; physical-console field gate remains external.
4. Strict country + Node Hub — Completed.
5. R28 provider-specific UI / metrics / refresh / self-update — Completed.
6. Exact final installer clean-install/upgrade/uninstall/live validation — Completed.
7. Public-tree/security verification — CURRENT.
8. Hosted CI + GitHub R28 release — Open.

## Accepted current state
- Static regression: 89 core + 14 gateway/scope PASS.
- Public refresh: 10 endpoints / 5 independent source families / 30-minute TTL; installed live sample 10 successful, 0 failed.
- Direct and WARP installed path Ping/Download/Upload: PASS.
- Node metric contract: verified path only; invalid throughput=N/A.
- Qualification: clean install + smoke + uninstall + zero residue/listeners PASS.
- Production upgrade: exact final installer, source parity and user-state preservation PASS.
- Security privacy scan must be PASS before promotion.

## Open external gates
- Windows trusted Authenticode signing: OPEN_NOTSIGNED.
- Physical console game/country E2E: UNPROVEN without attached console traffic.

## Exact Next Action
Run security/public-tree on finalized metadata, record PASS, commit/push R28, validate hosted CI, then publish the R28 GitHub release asset.

## HISTORY
- R28: provider-capability UI, 10-source/5-family public refresh, TTL/stale pruning, real Ping/Download/Upload metrics, bounded diverse node benchmarking and GitHub self-update.
- R28: transport compatibility expanded and fail-closed semantics strengthened.
- R28: concurrent build supersede prevented with source-freeze guard.
- R28: uninstall race root-caused to a finishing background engine job and fixed with exact-job cancel/drain plus narrow retry.
- R28: exact final installer qualified and production-upgraded with state preservation and installed live validation.
"""
(R/"PROJECT_BRAIN.md").write_text(brain,encoding="utf-8",newline="\n")
def candidates():
 raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=R)
 out=[]
 for x in raw.decode("utf-8").split("\0"):
  if not x: continue
  rel=pathlib.PurePosixPath(x).as_posix()
  if rel=="PUBLIC_MANIFEST.json": continue
  p=R/rel
  if p.is_file(): out.append(rel)
 return sorted(set(out),key=str.lower)
def row(rel):
 p=R/rel; data=p.read_bytes()
 return {"file":rel,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}
pm={"schema":3,"version":"4.2.0-local-r28-final","source":"working-tree-public-candidate","files":[row(x) for x in candidates()]}
dump("PUBLIC_MANIFEST.json",pm)
print(json.dumps({"status":"PASS","files":len(pm["files"]),"installerSha256":INSTALLER_SHA,"finalAcceptanceSha256":sha(R/"evidence/R28_FINAL_ACCEPTANCE_20260928.json"),"publicManifestSha256":sha(R/"PUBLIC_MANIFEST.json")},indent=2))
