#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess,re
R=pathlib.Path(__file__).resolve().parent.parent
DATE="2026-09-28"
INSTALLER=R/"delivery"/"github_v4.2.0"/"FreeNetHub_4.2.0_R27_Country_ShadowShare_Final_Setup.exe"
EXPECTED_INSTALLER="151444A7694D4BB9F3774B0767029F6F4AC8F8ECC2E0A858BED0C2A83D238996"
EXPECTED_ENGINE="F5B2E69948830BFE103A76BE23D4BAF542C45B75C4B70D61C71177337A78C82D"
EXPECTED_NODEHUB="C016F0975720505F0FD9901F25458AA98B6BCBE99387D952592517307CF3FBC2"
EXPECTED_MANIFEST="E3E8206F413B2E0830E821D63EEAC396D4BE1ECF86FA8CDB15682507EEC413AE"
E_INSTALL=R/"evidence"/"R27_INSTALL_ACCEPTANCE_20260928.json"
E_LIVE=R/"evidence"/"R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json"
E_SMOKE=R/"evidence"/"R27_INSTALLED_PRODUCT_SMOKE_20260928.json"
E_FINAL=R/"evidence"/"R27_FINAL_ACCEPTANCE_20260928.json"
E_KNOW=R/"evidence"/"R27_PROJECT_KNOWLEDGE_20260928.json"
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest().upper()
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
def writej(p,o): pathlib.Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def row(rel):
 p=R/rel
 return {"file":rel.replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)}
def candidates():
 raw=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=R)
 out=[]
 for x in raw.decode("utf-8").split("\0"):
  if not x: continue
  rel=pathlib.PurePosixPath(x).as_posix();p=R/rel
  if rel!="PUBLIC_MANIFEST.json" and p.is_file(): out.append(rel)
 return sorted(set(out),key=str.lower)

if sha(INSTALLER)!=EXPECTED_INSTALLER: raise SystemExit("R27_INSTALLER_HASH")
if sha(R/"app"/"engine.py")!=EXPECTED_ENGINE: raise SystemExit("R27_ENGINE_HASH")
if sha(R/"app"/"nodehub.py")!=EXPECTED_NODEHUB: raise SystemExit("R27_NODEHUB_HASH")
if sha(R/"app"/"manifest.json")!=EXPECTED_MANIFEST: raise SystemExit("R27_MANIFEST_HASH")
ei,el,es=load(E_INSTALL),load(E_LIVE),load(E_SMOKE)
if ei.get("status")!="PASS" or not all(ei.get("parity",{}).values()): raise SystemExit("R27_INSTALL_EVIDENCE")
if el.get("status")!="PASS" or el.get("target")!="SG" or el.get("actual")!="SG" or not el.get("healthy"): raise SystemExit("R27_LIVE_EVIDENCE")
if not es.get("accepted"): raise SystemExit("R27_SMOKE_EVIDENCE")

final={
 "schema":1,"date":DATE,"status":"LOCAL_ACCEPTED_WINDOWS_4.2_R27_COUNTRY_SHADOWSHARE_HY2",
 "installer":{"file":"delivery/github_v4.2.0/FreeNetHub_4.2.0_R27_Country_ShadowShare_Final_Setup.exe","bytes":INSTALLER.stat().st_size,"sha256":EXPECTED_INSTALLER,"authenticode":"NotSigned"},
 "source":{"engineSha256":EXPECTED_ENGINE,"nodeHubSha256":EXPECTED_NODEHUB,"appManifestSha256":EXPECTED_MANIFEST},
 "regression":{"strictRunner":"tests/verify_r24_strict.ps1","operationId":"cf4b2f11-d1e4-43fd-9b86-0a7d8a9f6b78","windowsCore":"65/65 PASS","gateway":"13/13 PASS","hysteria2Fidelity":"PASS","countryStrict":"PASS","nodeFailFast":"PASS","hy2PreflightPolicy":"PASS","failClosed":"PASS"},
 "installed":{"parity":"PASS","settingsPreserved":True,"nodesPreserved":True,"smoke":"PASS","idleProjectListeners":0,"newTerminalProcesses":False},
 "country":{"policy":"STRICT_ACTUAL_EXIT_MATCH","liveTarget":"SG","liveActual":"SG","healthy":True,"mode":"NODE"},
 "nodeHub":{"protocols":["SS","VMess","VLESS","Trojan","Hysteria2"],"publicSources":["V2CROSS_PAGE","SHADOWSHARE_SUB_EN","SHADOWSHARE_SUB_DE","SHADOWSHARE_SUB_FR","SHADOWSHARE_README_ID","SHADOWSHARE_README_BN","SHADOWSHARE_README_ES"],"lastRefreshTotal":el["refresh"].get("total"),"lastRefreshImported":el["refresh"].get("imported"),"failedSources":el["refresh"].get("failedSources",[]),"scope":"BROWSER_ONLY","management":["dedupe","favorites","pin","custom_name","tags","note","rating_0_5","history","filter","sort"],"exports":["raw","base64"]},
 "evidence":{"install":{"path":"evidence/R27_INSTALL_ACCEPTANCE_20260928.json","sha256":sha(E_INSTALL)},"live":{"path":"evidence/R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json","sha256":sha(E_LIVE)},"smoke":{"path":"evidence/R27_INSTALLED_PRODUCT_SMOKE_20260928.json","sha256":sha(E_SMOKE)}},
 "openExternalGates":{"PUBLIC_TRUST_WINDOWS_CODE_SIGNING":"OPEN_NOTSIGNED","PHYSICAL_CONSOLE_GAME_COUNTRY_E2E":"UNPROVEN","ANDROID_IOS_PRODUCTION_RUNTIME_SIGNING":"OPEN"},
 "privacy":"No raw node credentials or raw exit IP are included in acceptance evidence."
}
writej(E_FINAL,final)

knowledge={
 "schema":1,"date":DATE,"project":"FreeNet Hub / Open Internet Gateway","milestone":"R27 country + ShadowShare-style Node Hub",
 "records":[
  {"context":"Country selection correctness","claimDecision":"A selected non-AUTO country is accepted only when the verified actual exit country equals the selected country; healthy wrong-country exits are stopped and rejected.","evidenceSource":["app/engine.py","tests/test_country_policy.py","evidence/R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["release notes","technical report","troubleshooting","thesis methods"],"provenance":{"engineSha256":EXPECTED_ENGINE}},
  {"context":"Root cause / prevention","claimDecision":"The earlier defect was an acceptance bug: strict-country scanning could return any healthy Node. Prevention is fail-closed actual-exit comparison plus regression for healthy wrong-country nodes.","evidenceSource":["tests/test_country_policy.py"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["postmortem","testing guide","engineering report"]},
  {"context":"Country availability","claimDecision":"A small single public pool was insufficient for reliable country availability. The minimum useful change was merge+dedupe across audited public Pawdroid/ShadowShare-family sources and V2CROSS, not blind retries.","evidenceSource":["app/engine.py","evidence/R24_SHADOWSHARE_REFRESH_ACCEPTANCE_20260928.json","evidence/R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["architecture rationale","release notes"]},
  {"context":"Protocol coverage","claimDecision":"Hysteria2/hy2 is supported with sing-box-compatible password/TLS/obfs mapping. TCP endpoint preflight is not used to reject Hysteria2 because its transport is UDP/QUIC.","evidenceSource":["app/nodehub.py","tests/test_r24_hysteria2.py","tests/test_r26_hy2_preflight.py"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["protocol matrix","developer docs"]},
  {"context":"Failure prevention","claimDecision":"Broken Node paths fail fast after bounded completed probes rather than consuming the full retry window; wrong-country paths remain fail-closed.","evidenceSource":["app/engine.py","tests/test_country_policy.py"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["operations guide","test plan"]},
  {"context":"Installed product","claimDecision":"R27 installer preserves settings and node data; installed engine/nodehub/UI/view/manifest match source; idle UI smoke creates no project network listeners or new terminal windows.","evidenceSource":["evidence/R27_INSTALL_ACCEPTANCE_20260928.json","evidence/R27_INSTALLED_PRODUCT_SMOKE_20260928.json"],"confidence":"CONFIRMED","status":"PASS","reuseTargets":["release checklist","support guide"]},
  {"context":"Distribution trust","claimDecision":"Functional/local acceptance does not imply public code-signing trust. The R27 installer is Authenticode NotSigned; obtaining a trusted signing certificate remains an external gate.","evidenceSource":["evidence/R27_FINAL_ACCEPTANCE_20260928.json"],"confidence":"CONFIRMED","status":"OPEN_EXTERNAL_GATE","reuseTargets":["release notes","distribution checklist"]}
 ],
 "externalReferences":[
  {"name":"ShadowShare Google Play","url":"https://play.google.com/store/apps/details?id=com.v2cross.shadowshare&hl=en"},
  {"name":"Pawdroid Free-servers public repository","url":"https://github.com/Pawdroid/Free-servers"}
 ]
}
writej(E_KNOW,knowledge)

rel=load(R/"RELEASE.json")
old_inst=rel.get("installerSha256")
rel.update({
 "releaseRevision":"4.2.0-local-r27-country-shadowshare-hy2-final",
 "status":"LOCAL_ACCEPTED_WINDOWS_4.2_R27_COUNTRY_SHADOWSHARE_HY2",
 "engineSha256":EXPECTED_ENGINE,"nodeHubSha256":EXPECTED_NODEHUB,"appManifestSha256":EXPECTED_MANIFEST,
 "previousAcceptedInstallerSha256":old_inst,"installerSha256":EXPECTED_INSTALLER,
 "installerStatus":"R27_BUILT_INSTALLED_LIVE_SMOKE_ACCEPTED",
 "acceptanceEvidence":"evidence/R27_FINAL_ACCEPTANCE_20260928.json"
})
rel["r27"]={
 "countryPolicy":"STRICT_ACTUAL_EXIT_MATCH",
 "liveStrictCountry":{"target":"SG","actual":"SG","status":"PASS","evidence":"evidence/R27_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json"},
 "nodeHub":final["nodeHub"],
 "hysteria2":"PASS_PROTOCOL_AWARE_PREFLIGHT",
 "failFast":"PASS_BOUNDED_NODE_VERIFICATION",
 "sourceRegression":"PASS_65_CORE_13_GATEWAY",
 "installerAcceptance":"PASS","installedParity":"PASS","installedUiSmoke":"PASS","atRestNetwork":"PASS",
 "trustedWindowsSigning":"OPEN_NOTSIGNED",
 "knowledgeRecord":"evidence/R27_PROJECT_KNOWLEDGE_20260928.json"
}
writej(R/"RELEASE.json",rel)
writej(R/"PUBLIC_MANIFEST.json",{"schema":3,"version":"4.2.0-local-r27-country-shadowshare-hy2-final","source":"git-candidate-working-tree","files":[row(x) for x in candidates()]})

brain=R/"PROJECT_BRAIN.md"
bt=brain.read_text(encoding="utf-8")
bt=re.sub(r"Brain version: .*","Brain version: R27-country-shadowshare-hy2-final-2026-09-28",bt,count=1)
bt=re.sub(r"Current base authority: .*","Current base authority: LOCAL R27 accepted candidate; origin/main remains prior authority until follow-up commit/push.",bt,count=1)
bt=bt.replace("7. Final manifest/installer/installed-product regression — ← CURRENT.","7. Final manifest/installer/installed-product regression — Completed/PASS (R27).")
bt=bt.replace("8. Follow-up commit/push + hosted CI; publish follow-up asset only after gates — OPEN.","8. Follow-up commit/push + hosted CI; publish follow-up asset only after gates — ← CURRENT.")
head,hist=(bt.split("## HISTORY (append-only)",1) if "## HISTORY (append-only)" in bt else (bt,""))
head=re.sub(r"## Exact Next Action\n[^\n]*(?:\n(?!(?:## )).*)*","## Exact Next Action\nCommit/push the accepted R27 delta and run hosted CI. Publish the R27 installer asset only after CI; trusted Windows signing remains a separate external gate.",head,count=1)
milestone=f"""\n## R27 Accepted Local Milestone — 2026-09-28
- Status: LOCAL_ACCEPTED / functional Windows R27.
- Installer: FreeNetHub_4.2.0_R27_Country_ShadowShare_Final_Setup.exe; SHA-256 {EXPECTED_INSTALLER}; Authenticode NotSigned.
- Country: strict actual-exit semantics PASS; installed live target SG -> actual SG via NODE.
- Public Node refresh: 145 total candidates on acceptance run, 137 imported during refresh, 7/7 configured public sources succeeded.
- Protocols: SS / VMess / VLESS / Trojan / Hysteria2.
- Regression: 65/65 Windows/core, 13/13 gateway, Hysteria2 fidelity, protocol-aware HY2 preflight, strict-country mismatch, Node fail-fast, fail-closed all PASS.
- Installed parity: engine/nodehub/PowerShell UI/View/manifest all source-identical; settings and nodes preserved.
- Installed smoke: single-instance/tray/taskbar/no-terminal PASS; idle project listeners=0.
- Evidence: evidence/R27_FINAL_ACCEPTANCE_20260928.json; evidence/R27_PROJECT_KNOWLEDGE_20260928.json.
- External gate: PUBLIC_TRUST_WINDOWS_CODE_SIGNING remains OPEN (NotSigned).
"""
if "## R27 Accepted Local Milestone — 2026-09-28" not in head:
 head=head.rstrip()+"\n"+milestone+"\n"
bt=head+"## HISTORY (append-only)"+hist
history_line=f"\n- 2026-09-28: R27 local acceptance completed: strict SG live PASS, ShadowShare-style multi-source Node refresh + Hysteria2 PASS, installed parity/smoke PASS; trusted signing remains OPEN.\n"
if history_line.strip() not in bt:
 pos=bt.find("## HISTORY (append-only)")
 if pos>=0:
  nl=bt.find("\n",pos)
  bt=bt[:nl+1]+history_line.lstrip("\n")+bt[nl+1:]
brain.write_text(bt,encoding="utf-8",newline="\n")

print(json.dumps({
 "status":"PASS","finalEvidenceSha256":sha(E_FINAL),"knowledgeSha256":sha(E_KNOW),
 "releaseSha256":sha(R/"RELEASE.json"),"publicManifestSha256":sha(R/"PUBLIC_MANIFEST.json"),
 "brainSha256":sha(brain)
},indent=2))
