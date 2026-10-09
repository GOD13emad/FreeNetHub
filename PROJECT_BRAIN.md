# PROJECT BRAIN — FreeNet Hub

Status: CURRENT / V436_R50_LOCAL_GATES_PASS_HOSTED_OPEN
Brain version: v436-r50-node-selection-quality-local-2026-10-05
Previous public baseline: v4.3.5 / R49 at merge commit 93fea59d696b69eb5b723e2d6b2033d4fdb879dd.
Current source candidate: v4.3.6 / R50 (4.3.6-r50-node-selection-quality) on branch v4.3.6-r50-node-selection-quality; public promotion is NOT yet authorized until exact-SHA hosted CI passes.

## CURRENT — R50 Node Selection Quality
- Root cause confirmed by live Linux evidence: a fixed four-node deep sample returned no winner, while a 12-candidate continuation found 3 full-health PASS nodes. TCP endpoint reachability is only a preflight hint and must not outrank measured application-level health.
- Windows: Smart node ordering now prefers full-health performance results; batch output exposes deterministic best full-health result. Existing UI continues bounded 4-node batches when the user requests all-node benchmarking.
- Linux R16/r43: Smart ordering prefers full-health metrics; node_benchmark_best() performs bounded adaptive search (max 24 candidates, target 3 PASS, batch size 4).
- Full local regression: 244/244 PASS. Targeted node regression: 8/8 PASS. Python compile / PowerShell parse / Linux parity / Linux selftest / update revision / public security: PASS.
- Linux package: FreeNetHub_4.2.0_Linux_R16.zip, 225314 bytes, SHA-256 01F852B1350C591EAD5C03A0F094F92B4861E1D1DA96226A48B9AE691D48C503.
- Final frozen Windows installer: FreeNetHub_4.3.6_R50_Setup.exe, 24273858 bytes, SHA-256 A3A6E9490BE703B96068F3B481CFC85CE2E13EB52BA730D1DC6739F136AD9335; manifest preflight PASS; Authenticode NotSigned (trusted signing remains external).
- Superseded R50 installer hashes: FB317C82007749E82983C79A089E7499EACB231A6F0C98C6AFE7DD0CBFD35DC2, 8F458553E7EA3E4A88A31D1C0F6F9B4970DF578C859C2A739220ECED7532E8B4.
- Tor direct 90-second current-network probe reached 67% bootstrap then timed out; route/DNS/session semantics were restored/preserved. This is dynamic external-path evidence, not a proven code defect.
- No new external dependency was added by R50 and the patch itself does not mutate the Windows default route.

## CURRENT Open Gates / Critical Path
1. Freeze PUBLIC_MANIFEST.json with no concurrent writer and pass verify_public_tree.py, security, fail-closed and final regression on the exact snapshot.
2. Commit/push exact R50 candidate and require all hosted CI jobs PASS on the exact commit SHA.
3. Merge only after exact-SHA PASS, then publish v4.3.6 using the already-accepted Windows R50 and Linux R16 bytes without rebuilding.
4. Post-publish UpdateCheck: Windows read-only/preserve active session; Linux R15→R16 updater/install integrity and route/DNS/session preservation.
5. External/nonblocking tracks remain: trusted Authenticode; physical-console field E2E; production Android/iOS forwarding/signing; live TUIC/AnyTLS/ShadowTLS endpoints without authorized server material.

## Exact Next Action
Pass final local verification on the canonicalization correction, commit/push the correction SHA to PR #26, and require hosted exact-SHA CI PASS before merge or release.


## R50 hosted-attempt correction — CURRENT
- First candidate commit 0dd73a874ecf4aa37b191c6adaa12bbe8d760c27 reached PR #26. Hosted PR run 37334685245 failed only the early windows-unit step Verify public manifests; already-completed windows-virtual-signing, console-virtual-e2e, android-build, linux-static and windows-installer-fresh passed.
- Root cause: cross-platform manifest authority was not portable across Windows working-tree line endings and hosted checkout bytes. Correction policy: crossplatform manifest builder and public verifier use Git-canonical bytes for cross-platform source entries.
- Independent supply-chain prevention: RELEASE.json is embedded in the Windows installer, so the current installer digest/byte size must not be written into RELEASE.json. Artifact digest lives only in external evidence.
- Current self-reference-free frozen Windows installer: FreeNetHub_4.3.6_R50_Setup.exe, 24257042 bytes, SHA-256 E9592F858F166A7946BA8791CA9595B325456AB9BE27FEF07A3FC7E399F30AE1, Authenticode NotSigned, manifest preflight PASS.
- Linux R16 remains 225314 bytes, SHA-256 01F852B1350C591EAD5C03A0F094F92B4861E1D1DA96226A48B9AE691D48C503.
- Correction is local and requires final local public-tree reverify, then a new exact commit SHA and a fresh hosted CI run. Commit 0dd73a8 is not promotion authority.

## Superseded historical Brain follows

Status: CURRENT / V431_PUBLIC_FINAL + OWNER_LOCAL_R45_PRECONNECT_HOTFIX
Brain version: v431-public-final+r45-owner-hotfix-2026-10-04
Installed authority: Windows owner machine v4.3.1 with local R45 pre-connect-test hotfix applied in place; app manifest 17/17 PASS; installed Speed/DIRECT backend PASS (93.3 ms / 36.0 Mbps / 4.82 Mbps) and CFON remained CONNECTED_HEALTHY. Visual post-click table rendering is UNPROVEN because GUI helper timed out. Public artifact authority remains v4.3.1/R44.
Source authority: runtime release tag v4.3.1 -> 3bfbb8f51881eb53579325f80bf4e370bba42c76; main may advance only with post-release evidence/control changes. v4.3.0 release object removed as superseded; its tag/history preserved
Promotion state: Public v4.3.1 CLOSED_PASS / FINAL_PUBLIC. Owner-local R45 hotfix is INSTALLED_BACKEND_PASS but NOT_PUBLIC; visual post-click UI validation remains OPEN/UNPROVEN. Trusted Authenticode remains MISSING_EXTERNAL_NONBLOCKING ← CURRENT
Desktop closure scope:
- Included: Windows R40 desktop runtime/release continuity; Linux R14 desktop runtime/release; updater/integrity/CI/release continuity.
- Excluded separate tracks: physical Console field E2E; Android production forwarding/signing; iOS production forwarding/device signing; optional Linux Node Full-System privileged helper.
- Distribution trust: Windows Authenticode remains MISSING_EXTERNAL. Self-signed/test certificates do not satisfy this gate.

## Final Objective / DoD
FreeNet Hub is the comprehensive free multi-transport connectivity product. It must expose the widest practical set of independent censorship-resilient paths under one understandable UI, with explicit Browser / Full System / Console capability boundaries, pre-connect measurement where technically meaningful, fail-closed behavior, rollback for network mutation, and no hidden DIRECT fallback.

Locked boundary:
- FreeNet Hub does NOT absorb VPN Gate/OpenVPN relay discovery, pools or caches.
- VPN Gate/OpenVPN remains owned by OpenInternetGateway.
- FreeNet Hub expands through independent transport families.

## Current accepted installed baseline
R37 is the current Windows installed/source authority.
- Revision: `4.2.0-local-r37-final`; app manifest coreVersion: `4.0-r37-final`.
- UI: five tabs (Dashboard / Methods / Nodes / Tools / Settings), with Console retained as an independent capability inside Tools.
- Installed/source parity: PASS for 17 app files + 17 gateway files; zero mismatches.
- Runtime bootstrap: PASS, self-contained; WARP/Tor/Lyrebird and sing-box gateway core present.
- Broad source regression: 165 PASS; public-tree security scan PASS with zero forbidden artifacts and zero sensitive hits.
- Node refresh: PASS; fetch/parse/merge is separated from explicit Test All. Latest installed live refresh parsed 3064, imported 3015, total pool 2000, failed sources 0.
- Direct base-path measurement: PASS over physical Ethernet 3 with FreeNet Hub proxy bypassed; 78.3 ms / 37.71 Mbps / 5.23 Mbps in the recorded live sample.
- Browser WARP benchmark: PASS; temporary provider cleanup preserved.
- Full-System WARP: PASS through official gateway_request path. UpdateCheck while TUN active was bound to pre-TUN Ethernet 3 with proof `BOUND_PRE_TUN_SOURCE_AND_TRACE_NOT_POST_TUN`; system speed passed; Stop removed TUN/session and restored the exact base route.
- Final metadata promotion on installed runtime: PASS; five-tab post-promotion smoke PASS and route unchanged.
- Direct-DPI remains an optional fail-closed extension, not the main-product boundary. Live direct/Chrome evidence passes; installed lifecycle-specific acceptance remains UNPROVEN.
- Trusted Windows Authenticode remains OPEN_NOTSIGNED.
- Evidence: `evidence/R37_WINDOWS_FINAL_ACCEPTANCE_20260929.json`, `evidence/R37_PROJECT_KNOWLEDGE_20260929.json`, `evidence/CHAT4_R37_FS_OFFICIAL_GATEWAY_ACCEPTANCE_20260929.json`.

## Current R35 source candidate
R35 extends capability work beyond R32 without promoting/installing it yet.
- WARP Full System remains accepted baseline.
- NODE Full System is implemented as a strict candidate.
- AUTO System policy: explicit target country -> NODE; otherwise WARP.
- NODE System must prove selected-node HTTPS/TCP country, SOCKS5 UDP STUN, optional UDP country match, sing-box config check, post-TUN HTTPS/YouTube/STUN, post-TUN TCP+UDP country and exact rollback.
- CFON/TOR/CUSTOM/GOOL remain Browser-only because UDP/system semantics are not proven.
- Direct bootstrap/update path can retry DNS resolution through public resolver addresses while still using the system/default route and never the FreeNet Hub proxy.

## Current R36 direct-network candidate — no VPN / no proxy
- Current explicit priority is direct-path hardening without VPN/proxy; R35 NODE Full-System remains preserved but deferred.
- Installed OIG was cleanly disconnected for direct audit: desired=off, OVPNConnectorService stopped, no /1 full-route overrides.
- Physical path: Ethernet 3 / Intel I226-V / 192.168.20.5 -> 192.168.20.1, 1 Gbps, zero packet/discard errors in audit.
- CGNAT is CONFIRMED: CPE UPnP WAN IPv4 100.123.107.63 is RFC6598 shared space; STUN public mapping is 164.215.159.13 and is stable/source-port-preserving across Cloudflare + Google.
- PCP/NAT-PMP: unavailable. Static inbound cannot be made public from Windows alone under this ISP path.
- IPv6 live trial: NO_NATIVE_PUBLIC_IPV6_ROLLED_BACK. Enabling ms_tcpip6 produced no global IPv6 address and no ::/0 route; IPv4 stayed healthy and the original disabled binding was restored.
- DNS interception is CONFIRMED: system and direct UDP/53 queries to router/1.1.1.1/8.8.8.8/9.9.9.9 return private 10.10.34.35 for YouTube.
- Validated encrypted DNS bootstrap at https://76.76.10.11/p0 returns public YouTube addresses; Yandex alternate DNS on UDP/1253 also returned valid public answers for YouTube/ChatGPT/GitHub.
- YouTube still resets when connecting to a real public YouTube IP with correct SNI; forced Chrome QUIC fails, and a clean Chrome DoH+ECH/QUIC-disabled trial also failed to reach the page. Therefore the blocker is DNS interception + destination-specific TLS/DPI, not DNS alone.
- No MTU/NIC/TCP/system-DNS tweak was applied because evidence does not justify it.
- GoodbyeDPI 0.2.2 stable live trials for official modern modes -5 and -6 both FAILed for YouTube HTTPS while successfully replacing poisoned DNS with public answers; OpenAI/GitHub/direct route stayed healthy and cleanup was exact. GoodbyeDPI is therefore rejected for promotion on this ISP.
- zapret official blockcheck on exact zapret-win-bundle commit 6eb463a6758fb48cd101bc55dfd057e6e9d98af1 PASSed on this ISP for www.youtube.com over IPv4 HTTPS. Both TLS 1.2 and TLS 1.3 found the same strategy: `--wf-l3=ipv4 --wf-tcp=443 --dpi-desync=multisplit --dpi-desync-split-pos=sniext+1`. Cleanup restored winws/WinDivert/routes/TCP timestamps exactly.
- Native Windows DoH with 76.76.10.11 / https://76.76.10.11/p0 is separately CONFIRMED: system DNS returned public YouTube A records while poisoned UDP/53 had returned 10.10.34.35.
- Combined validation harness was retired after three harness-only failures; root causes are recorded in evidence/R36_ZAPRET_VALIDATION_HARNESS_AUDIT_20260928.json. Validation is now split into independent Curl then Chrome gates.
- Evidence: evidence/R36_DIRECT_NETWORK_ACCEPTANCE_20260928.json
- R36 evidence SHA-256: 29d6844ca2d574abbe67e9618cd2990b269ef209dde29fedbd3e50a7c2566c9c

## Evidence
- R36 direct/core/UI/boundary regression: 126 PASS.
- Gateway/scope regression: 18 PASS.
- Additional clean-install/protocol regression: 4 PASS.
- Python compile + git diff check: PASS.
- R36 source WPF smoke: PASS; networkRequested=false; 145 controls; 1360x900.
- Prior R35 static regression: 112 core PASS.
- Gateway/scope regression: 18 PASS.
- Theme contrast: 3 PASS.
- Product boundary guard: PASS.
- R35 source WPF smoke: PASS after manifest refresh.
- Direct underlay at current audit: Ethernet 3 -> 192.168.20.1; OIG split routes absent; OVPNConnectorService stopped.
- R35 Node pre-TUN acceptance: PASS.
  - public nodes: 2000
  - reachable: 1797
  - failed sources: 0
  - selected target: SG
  - TCP country: SG
  - UDP country: SG
  - Ping: 966.5 ms
  - Download: 2.86 Mbps
  - Upload: 0.98 Mbps
  - state restored: true
- Evidence: evidence/R35_NODE_PRE_TUN_ACCEPTANCE_20260928.json
- Source gate: evidence/R35_SOURCE_GATE_ACCEPTANCE_20260928.json

## Failure prevention
R36 zapret runtime validation: the original combined DoH+winws+Chrome harness had three independent harness defects (elevated TEMP redirect path, missing Scratch assignment, nullable Chrome stdout). All three executions rolled back network state exactly. The monolithic harness is retired; evidence is in `evidence/R36_ZAPRET_VALIDATION_HARNESS_AUDIT_20260928.json`. Prevention: independent Curl/Chrome gates, stage evidence written before cleanup, explicit self-contained tool hashes, no scratch/Chrome dependency in Curl Gate.

A previous R33 live harness prepared/refreshed Node state before UAC. When elevation could not be controlled and the run was stopped, a Node listener and temporary state remained. Root cause was harness ordering, not product TUN behavior.
Fix:
- outer acceptance no longer mutates before UAC;
- all backup/preparation/TUN/verification/rollback/state restoration moved inside elevated process;
- parser validation PASS;
- interrupted prior state was restored exactly and listener/owner/TUN returned to zero.


## Holistic system audit — 2026-09-29
- Direct-DPI is an extension/capability, not the product boundary. Product scope includes Windows browser providers, Node Hub/protocols, WARP/NODE system paths, Console Gateway, direct-network capabilities, Linux desktop/runtime, Android and iOS tracks, installer/update, release/CI/security and rollback/state management.
- Public GitHub authority: main at 970c394 (R28). Windows installed authority: R32 audit closure. Linux installed authority: 4.2.0-linux.8 on source 42dbf97. These authorities are intentionally distinct and currently drifted.
- Local Windows working candidate contains cumulative R29-R36 plus DirectDNS work and is not a release authority.
- Broad static regression: 152 PASS. Post-hygiene focused regression: 140 PASS. Gateway PowerShell parse PASS. git diff --check PASS with EOL warnings only.
- Release verifier: app/gateway/cross-platform/windows-package manifests PASS; PUBLIC_MANIFEST FAIL versus dirty candidate; RELEASE hashes FAIL for engine/UI/gateway/acceptanceEvidence. No promotion allowed.
- Latest R36 final Windows acceptance is FAIL_ROLLED_BACK: candidate installed parity and smoke PASS, Direct-DPI start failed at DIRECT_DPI_DOH_NOT_CLEAN, network rollback PASS, installed R32 restoration PASS.
- Managed DNS pivot using ctrld 1.5.7: foreground resolver PASS and exact cleanup PASS; Windows service lifecycle FAIL because service self-check cannot reopen persisted config. Root cause narrowed, not promoted.
- Security/release hygiene initial scan FAIL: finalizer copied full installed private runtime/browser state into repo artifacts and raw browser/runtime evidence was unignored. Exact sensitive backup path was not tracked and no Git history for that path was found. Containment applied: private backup moved outside repo, generated artifacts/raw runtime paths ignored, secret samples redacted in scanner, scanner now fails closed on unreadable candidate files.
- Release hygiene is now CLOSED_PASS: `security_scan_public.py` reports zero forbidden runtime artifacts and zero sensitive-pattern hits. Installer-build evidence uses a repository-relative path and the build script now prevents absolute user-path recurrence.
- Evidence: evidence/HOLISTIC_SYSTEM_AUDIT_20260929.json (SHA-256 ae679a3215d71cdd03f045424339bc4773af8fbcbaed15ea406052d6147fdae2).

## Roadmap
1. Whole-product authority/capability audit — Completed.
2. R37 target UI/controller/engine convergence — Completed.
3. Node refresh latency separation + configurable preconnect semantics — Completed/PASS.
4. Pre-TUN base-route capture and update/node root-path verification — Completed/PASS.
5. Windows installed runtime, browser WARP, Direct base speed, Full-System WARP and rollback acceptance — Completed/PASS.
6. Final source/installed metadata promotion + parity + five-tab smoke — Completed/PASS.
7. R37 Final installer build + exact final installer execution — Completed/PASS.
8. Canonical public manifest + local public release gate — Completed/PASS.
9. Git commit/push + corrective dual-hash CI contract + hosted CI — Completed/PASS.
10. GitHub release `v4.2.0-r37-final` + asset digest verification + post-publish self-update check — Completed/PASS.
11. Linux R9 R37-parity UI/backend convergence + installed acceptance — Completed/PASS.
12. Linux R9 exact package + manifest/security/local public gate — Completed/PASS.
13. Linux public promotion through R12 and R39 release continuity — Completed/PASS; R9 is superseded history.
14. Desktop final closure — Completed/PASS. External identity signing and separate mobile/physical-console/optional privileged-extension tracks remain explicitly outside desktop DoD.
15. R40 deep lifecycle-safety audit and Linux R13 hardening — Completed/PASS; superseded for Linux updater authority by R41/R14.

16. R41 Linux self-update revision authority + CI current-package guard — Completed/PASS; PUBLIC FINAL.
17. R45 pre-connect test hotfix on owner Windows — Backend/root-cause/regression/install/connection-preservation Completed/PASS; visual post-click rendering OPEN/UNPROVEN.
## Open Gates / Critical Path
- Owner-local R45 visual post-click UI confirmation — OPEN/UNPROVEN only because Commander GUI helper timed out; installed backend and connection-preservation gates are CLOSED_PASS.
- R37 Windows runtime/product behavior — CLOSED_PASS.
- Installed/source manifest parity — CLOSED_PASS.
- Five-tab UI smoke and no-route-mutation launch — CLOSED_PASS.
- Node refresh fast fetch/merge behavior — CLOSED_PASS.
- Full-System WARP + update-through-pre-TUN-base-route + rollback — CLOSED_PASS.
- Final installer exact execution — CLOSED_PASS. SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64`.
- Canonical PUBLIC_MANIFEST / RELEASE verifier — CLOSED_PASS.
- Hosted CI follow-up #99 / run `36546861061` — CLOSED_PASS, including aggregate virtual-acceptance.
- Public GitHub release `v4.2.0-r37-final` targeting `45e21a1bc64aefaf3276751754c0f4f4fd1fb649` — CLOSED_PASS.
- Post-publish installed UpdateCheck — CLOSED_PASS: local=37, remote=37, selected asset digest matches, `updateAvailable=false`.
- Trusted Windows Authenticode — MISSING_EXTERNAL distribution-trust gate; no local code-signing certificate/private key, no GitHub signing secret, and Azure account has no usable subscription. Functional desktop release is not blocked; do not claim signed distribution.
- Linux R9 R37-parity installed runtime — CLOSED_PASS: Dashboard/Methods/Nodes/Tools/Settings; Node metadata/history/export/bounded benchmark; revision-aware update; app-local pinned sing-box 1.14.2 and warp-plus 1.2.6; WARP/GOOL/CFON browser live PASS; route preserved.
- Linux R9 historical package — SUPERSEDED by R11; prior CLOSED_PASS: `FreeNetHub_4.2.0_Linux_R9.zip`, SHA-256 `7693D70E424FE9CE0271C3A5AE6E8F5921838CCD12F52749B7339576A17F98A8`, internal SHA256SUMS PASS, exact install/integrity/UI-restart/route-preservation PASS.
- Linux R9 local public verifier/security/regression — CLOSED_PASS.
- Linux R9 Git/hosted CI/release — SUPERSEDED/CLOSED by Linux R12 carried in R39 public final.
- Physical console game/country E2E — DEFERRED_SEPARATE_TRACK external hardware validation; not part of Windows/Linux desktop final DoD.
- Direct-DPI installed lifecycle — UNPROVEN optional extension; fail-closed and non-blocking for core product.
- Android production forwarding core/signing — DEFERRED_SEPARATE_TRACK; hosted fail-closed emulator lifecycle PASS; not part of desktop final DoD.
- iOS production packet-forwarding core/device signing — DEFERRED_SEPARATE_TRACK; hosted simulator lifecycle PASS; not part of desktop final DoD.

## Exact Next Action
On the already-running owner Windows UI, press the same pre-connect Ping + Download + Upload test once and visually confirm the three values replace dashes. The installed backend fix is already active and CFON remained healthy; no disconnect or restart is required for this confirmation.

## HISTORY
- 2026-10-04 R45 owner-local pre-connect test hotfix: owner symptom 'test shows nothing' traced to installed Speed/DIRECT job ce913b2f... exiting 124/CHILD_DEADLINE. Independent reproduction matched. Stage isolation proved only direct_route() exceeded deadline (~8.685 s); trace/Ping/download/upload probes passed. Slow aggregate NetTCPIP PowerShell discovery was replaced by route.exe + Windows IP Helper while retaining physical-route, broad-override and WARP-off guards. Focused regression 130/130 PASS. Source live test PASS (96.0 ms / 37.92 / 5.36 Mbps); installed live test PASS (93.3 ms / 36.0 / 4.82 Mbps); app integrity 17/17 PASS; CFON postcheck remained CONNECTED_HEALTHY with Cloudflare 200 and YouTube 204. Visual post-click table observation remains UNPROVEN because Commander GUI helper timed out. Evidence: evidence/V431_R45_PRECONNECT_TEST_HOTFIX_20261004.json.
- 2026-09-29 Linux R11 UX final candidate: exact package SHA-256 `F56F55F2B020AC98F888A63E8D5E2705B5738D93F504B556EC9569419FAAED70` installed with zero route mutation; UI minimum 842x602; explicit scope/method selection; base/selected/all-method tests; two-stage node testing; seven sort modes; instant IP visibility; direct update flow. Live UI WARP Ping, sequential all-method testing, 2000-node endpoint test, real node benchmark, IP reveal and update check all exercised. Evidence: `evidence/R37_LINUX_R11_UX_ACCEPTANCE_20260929.json`.
- 2026-09-29 Linux R9 local public gate CLOSED_PASS: R37-parity GTK UI/backend installed on aliemad-Labtop; pinned sing-box 1.14.2 and warp-plus 1.2.6; browser WARP/GOOL/CFON live PASS; BASE test bypassed pre-existing tun0 via physical enp1s0 with IR/warp=off and real Ping/Download/Upload; deterministic exact ZIP SHA-256 `7693D70E424FE9CE0271C3A5AE6E8F5921838CCD12F52749B7339576A17F98A8` passed clean-HOME install, integrity and route-preservation; canonical public/security gate PASS. Evidence: `evidence/R37_LINUX_R9_PARITY_ACCEPTANCE_20260929.json`.
- 2026-09-29 R37 PUBLIC FINAL: corrective source/runtime dual-hash commit `45e21a1bc64aefaf3276751754c0f4f4fd1fb649` passed hosted CI #99/run `36546861061` across Windows, Linux, Android build/emulator, iOS static/simulator, console virtual E2E, virtual signing and aggregate virtual acceptance. GitHub release `v4.2.0-r37-final` published as latest with Windows installer SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64` and unchanged accepted Linux R8 SHA-256 `BD9F1311F02D4AA874609D61116EC26C107C5ECD4ED36086C2C3347E0A0C695A`. Post-publish installed UpdateCheck PASS: local=37, remote=37, digest/size exact, updateAvailable=false. Evidence: `evidence/R37_PUBLIC_RELEASE_ACCEPTANCE_20260929.json`.
- 2026-09-29 Hosted CI #98 root cause: Windows `Verify public manifests` failed because `app/manifest.json.sha256` intentionally represented deployed CRLF bytes while GitHub checkout normalized text files to LF. Runtime integrity was not weakened; R37 now carries dual hashes per app file: `sha256` for exact deployed/runtime bytes and `sourceSha256` for canonical Git-filtered source bytes. Exact rebuilt installer SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64` passed install/runtime/parity/five-tab/route acceptance. Follow-up hosted CI is current gate.
- 2026-09-29 hosted CI attempt #1 root cause: run `36542733818` on public commit `c70a4238d0ccaf7b835866ab34c382383c05219d` failed only at Windows `Verify public manifests`; PUBLIC_MANIFEST, RELEASE, gateway, cross-platform, Windows package and forbidden-runtime checks passed. App manifest failed for five normalized text files because runtime `sha256` intentionally hashes deployed Windows bytes while GitHub checkout normalizes source text to LF. Prevention: preserve runtime `sha256` and add canonical Git `sourceSha256`; CI verifies `sourceSha256`. Runtime code unchanged. Rebuilt exact installer SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64` then installed/verified PASS with route unchanged.
- 2026-09-29 R37 canonical public-tree gate CLOSED_PASS: PUBLIC_MANIFEST, app/gateway/cross-platform/windows package manifests, canonical RELEASE hashes and forbidden-runtime checks PASS; security scan zero hits; 165 regression tests PASS; git diff check PASS. Final installer SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64` exact execution PASS. Evidence: `evidence/R37_PUBLIC_TREE_ACCEPTANCE_20260929.json`.
- 2026-09-29 R37 exact final installer acceptance CLOSED_PASS: canonical-metadata installer SHA-256 `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64` installed with exit 0; runtime bootstrap PASS; source/install parity PASS; all five UI smoke tabs PASS; base route remained Ethernet 3 -> 192.168.20.1. A first metadata verification harness attempt failed before install because helper name `H` collided with PowerShell Get-History alias; rollback completed and helper was renamed `FileHash`. Evidence: `evidence/R37_PUBLIC_METADATA_INSTALL_ACCEPTANCE_20260929.json`.
- 2026-09-29 R37 final-installer execution fallback: connected execution guard blocked launching the exact Final EXE, so no false PASS was claimed. Prepared `artifacts/R37_FINAL_INSTALL_VERIFY_RUNNER.zip`, SHA-256 `18C1D5F4E7885B510FF888470EB9671BEA28655DDC25FE455653561F1DCD477A`; script SHA-256 `65476D4EA94331BE87F05016DFC65CCC48B83BDD70CD700E9FCE0E6678E33354`. Runner performs hash-pin, backup, install, runtime/parity/five-tab/route verification and rollback on failure.
- 2026-09-29 R37 Windows runtime final: installed/source authority promoted to 4.2.0-local-r37-final. 165 source tests PASS; security scan zero hits; installed parity 17 app + 17 gateway PASS; five-tab smoke PASS with route unchanged; Node refresh live PASS; Direct base speed PASS; browser WARP benchmark PASS; official Full-System WARP + UpdateCheck bound to pre-TUN Ethernet 3 + system speed + rollback PASS. Final installer static build PASS at SHA-256 8362141DAEAAB7927B097076C98AA2A9A0FFFC4C1E4EF8B130E85451D7433780; exact clean-install reexecution of that metadata-only rebuilt EXE remains UNPROVEN because the execution environment blocked launching it. Evidence: evidence/R37_WINDOWS_FINAL_ACCEPTANCE_20260929.json and evidence/R37_PROJECT_KNOWLEDGE_20260929.json.
- 2026-09-29 R36 release-hygiene gate CLOSED_PASS: security scan zero hits; installer build evidence sanitized to repo-relative path and builder hardened against absolute user-path recurrence. Current candidate `FreeNetHub_4.2.0_R36_DirectDPI_Final_Setup.exe` SHA-256 `8BDB02AEEC09E8403AFCE6238EDDB1EC7891F7B88357BF3FF113CF6F225FD87A`; finalizer SHA-256 `B68E635B990673935201478565852FAB58391634AD485E149BA58625890D0DC4`. One-elevation installed lifecycle acceptance is CURRENT.
- 2026-09-29 holistic audit: Direct-DPI reframed as one extension inside the full FreeNet Hub product. Authority drift, release metadata/public-manifest failure, R36 final Windows rollback, managed-DNS service blocker, Linux/public/local divergence and security-hygiene contamination were established. Private installed backup moved outside repo; release-hygiene remains CURRENT.
- 2026-09-29 R36 managed-DNS pivot: official ctrld v1.5.7 foreground resolver PASS on 127.0.0.1:1053 with Control D p0 (YouTube/GitHub/OpenAI public DNS). Service trial #1 failed from long Windows AF_UNIX socket path; short product path removed that failure. Service trial #2 then failed self-check because `ctrld.toml` was not found. Both trials cleanup exact PASS: DNS 192.168.20.1, no ctrld service/process/listener, ICS SharedAccess stayed Running with PID 5044, NRPT baseline preserved. Current blocker is service config persistence, not upstream DNS. Evidence: `evidence/R36_CTRLD_MANAGED_DNS_ROOT_CAUSE_20260929.json`.
- 2026-09-29 R36 installed-candidate Start failure: candidate parity + UI smoke PASS, Direct-DPI Start FAIL_ROLLED_BACK. Root cause CONFIRMED: `@(@($Dns1,$Tpl1))` flattened to strings, so `$pair[0]/$pair[1]` passed characters (`7`,`6`) to Windows DoH cmdlets. Fixed by direct `$Dns1/$Tpl1` calls; regression forbids pair indexing. Network and installed R32 rollback PASS. New candidate SHA-256 `5823DEA3641D5628582057C8770D12AD3EBF9989E2434491868E21EA844D2251`. Evidence: `evidence/R36_DIRECT_DPI_SINGLE_DOH_ROOT_CAUSE_20260929.json`.
- 2026-09-29 R36 cycle gate adjudication: prior cycle FAIL traced to PowerShell scalar unrolling before `.Count`; harness normalized relevant outputs to arrays. Targeted Direct-DPI/direct-network/product-boundary regression 11 PASS and `git diff --check` PASS. Elevated rerun remains UNPROVEN; evidence: `evidence/R36_CYCLE_HARNESS_FIX_20260929.json`.
- 2026-09-29 R36 packaging root cause: final zapret runner omitted required cygwin1.dll; Windows loader error reproduced by user; rollback state was clean. Fixed by bundling official v72.13 cygwin1.dll (SHA-256 103104A52E5293CE418944725DF19E2BF81AD9269B9A120D71D39028E821499B) and adding it to pre-mutation hash gate.
- 2026-09-28 R36: official zapret blockcheck PASS on actual ISP; same multisplit/sniext+1 strategy found for TLS1.2 and TLS1.3; exact cleanup PASS.
- 2026-09-28 R36: native Windows DoH to Control D fixed poisoned system DNS in bounded elevated trials; temporary configuration was rolled back.
- 2026-09-28 R36: three combined-validation harness defects audited; no strategy conclusion drawn from them; harness retired and Curl/Chrome gates separated.
- 2026-09-28 R36: self-contained hash-locked Curl Gate artifact prepared; owner UAC is current blocker.
- 2026-09-28 R36: native IPv6 trial CLOSED_NEGATIVE; no public IPv6/default route appeared and automatic rollback restored the prior binding.
- 2026-09-28 R36: GoodbyeDPI stable -5 and -6 both fixed DNS poisoning but failed YouTube HTTPS; OpenAI/GitHub/direct route remained healthy and WinDivert/process cleanup PASS.
- 2026-09-28 R36: after repeated GoodbyeDPI failure, path changed from parameter tuning to upstream-recommended zapret blockcheck on exact bundle commit; quick IPv4 HTTPS-only/no-tpws/no-QUIC scan prepared with TCP timestamp rollback.
- 2026-09-28 R36: direct-path audit PASS without FreeNetHub proxy/tunnel; CGNAT proven from RFC6598 CPE WAN address plus stable STUN mapping.
- 2026-09-28 R36: transparent DNS interception proven for YouTube even when UDP/53 is addressed to public resolvers; validated encrypted bootstrap returned public A records.
- 2026-09-28 R36: real-IP + correct-SNI and forced-QUIC trials still failed for YouTube, isolating destination-specific DPI beyond DNS.
- 2026-09-28 R36: IPv6 binding found locally disabled; exact rollback-safe admin trial prepared. No speculative MTU/NIC/TCP tuning applied.
- 2026-09-28 R36: GoodbyeDPI 0.2.2 stable staged and audited for minimum-sufficient direct-DPI trial; runtime/promotion remains UNPROVEN pending elevation.
- 2026-09-28 R35: current source frozen as non-installable capability candidate; manifest integrity and source smoke PASS.
- 2026-09-28 R35: Node pre-TUN live acceptance PASS for SG over TCP+UDP with real Ping/Download/Upload and exact state restoration.
- 2026-09-28 R35: live-harness ordering defect fixed so UAC rejection/interruption cannot leave preflight Node state.
- 2026-09-28 R33: official sing-box-based NODE Full-System architecture adopted; WARP+NODE only, other methods remain Browser-only until UDP/system evidence exists.
- 2026-09-28 R32: local audit closure PASS and installed authority.
- 2026-09-28 R31: architecture boundary locked; VPN Gate/OpenVPN excluded from FreeNet Hub.

## 2026-09-30 R39 ONLINE UPDATE + NO-ADMIN NORMAL-LAUNCH LOCAL GATE
- Previous accepted/public state: R38 Windows + Linux R12 at GitHub release `v4.2.0-r38-final`; immutable published digests remain authoritative.
- R39 objective: ordinary Windows launch must stay non-elevated; online update must be revision-aware and SHA-256 verified.
- Normal-launch authority: shell manifest `asInvoker`; Inno installer `PrivilegesRequired=lowest`; launcher no longer invokes dependency installation/winget on ordinary startup. Missing dependency metadata fails closed with a user message; repair remains Setup/update responsibility.
- Privileged operations remain explicit/on-demand only: Direct DPI / full-system / gateway may elevate when deliberately selected; the main UI does not elevate.
- Online update: delayed startup `UpdateCheck` plus existing manual update; GitHub latest release; downgrade/same revision rejected; asset digest must contain SHA-256; downloaded installer hash is verified before launch; installer starts with `UseShellExecute=false`.
- Local V&V: pytest `150/150 PASS`; R28 static PASS; Linux parity PASS; security scan PASS; PowerShell parse PASS; C# launcher compile PASS; shell runtime acceptance PASS with single-instance/tray/icon and zero FreeNetHub network artifacts.
- Pre-publish update behavior: local R39 vs public R38 => `updateAvailable=false`, proving downgrade prevention; default route unchanged.
- R39 local installer candidate: `FreeNetHub_4.2.0_R39_OnlineNoAdmin_Setup.exe`, 24,264,406 bytes, SHA-256 `28D0D9D64F9580F6B800BEA53F3E8310C4A2C52CD052E7F56BF721D4E0927F9F`, 25 frozen build inputs, Authenticode `NotSigned`.
- Brain status: CURRENT. Public promotion is not yet claimed.
- Open critical path: public-tree verify -> commit/push -> hosted CI -> merge main -> publish R39 -> live R38-to-R39 online update -> exact installed parity/UI smoke -> post-publish UpdateCheck 39=39.
- External/open gate retained: trusted Windows Authenticode signing.

## 2026-09-30 R39 PUBLIC FINAL — ONLINE UPDATE + NO-ADMIN NORMAL LAUNCH
- Previous accepted state: R38 Windows + Linux R12 public final.
- Current authority: main c80d9a16d315a15c185b6eba67c3a97f70d5c1ce; release v4.2.0-r39-final; hosted main CI run 36698146779 PASS.
- Windows R39 asset: FreeNetHub_4.2.0_R39_OnlineNoAdmin_Setup.exe, 24,264,406 bytes, SHA-256 28D0D9D64F9580F6B800BEA53F3E8310C4A2C52CD052E7F56BF721D4E0927F9F; GitHub digest exact match.
- Live online-upgrade gate CLOSED_PASS: installed R38 detected R39, SHA-256-verified download, then installed with exit 0 from a real non-admin/Medium-integrity runner using UseShellExecute=false; post-state local=39/remote=39, updateAvailable=false, route unchanged, zero FreeNetHub listeners.
- Normal-launch gate CLOSED_PASS: launcher is asInvoker, no RUNASADMIN AppCompat flag, no dependency/winget bootstrap during startup; installed R39 UI + owned PowerShell child ran under normal user context, no tunnel/listener was created, and delayed automatic UpdateCheck fired with 39=39/no update.
- Installed byte parity: 17 app + 17 gateway files and RELEASE parity exact; legacy R38 verifier's only failure was its stale hard-coded revision assertion.
- Linux continuity CLOSED_PASS: unchanged R12 SHA-256 9B0D413C168EC5DEF50CF29A574E243B8F4195C1CFDB9008E4307CF09C4A4CC3 is present in R39 release; installed Linux reports local=12, remote=12, updateAvailable=false.
- Privileged Direct DPI/full-system/gateway helpers remain explicit/on-demand; ordinary app launch and ordinary update do not require admin.
- External gate still OPEN: production trusted Windows Authenticode signing (NotSigned).
- Evidence: evidence/R39_PUBLIC_FINAL_ACCEPTANCE_20260930.json and evidence/R39_PROJECT_KNOWLEDGE_20260930.json.

- 2026-09-30 R39 control sync: reconciled stale Brain header/next-action against authoritative public-final evidence. origin/main=6c10c8c; R39 public acceptance evidence SHA-256 7D319EBED43D46BB3D4C07B18EF843AC69B5702D8FFEC23A9C786E5F3D1E0653. Runtime behavior unchanged; Windows installed coreVersion=4.0-r39-online-noadmin and Linux installed version=4.2.0-linux.12-r38 were re-read from hosts. RELEASE.json candidate wording is retained as historical build metadata and superseded by R39_PUBLIC_FINAL_ACCEPTANCE evidence.

- 2026-09-30 DESKTOP FINAL CLOSURE: Windows installed app/gateway integrity 17/17 + 17/17 PASS; self-contained runtime PASS; live UpdateCheck local=39/remote=39/updateAvailable=false and exact default-route preservation PASS. Linux INSTALL.sha256 9/9 PASS; live update local=12/remote=12/updateAvailable=false with route table unchanged and pre-existing tun0 untouched. R39 PR CI #131 and post-merge main CI #132 both PASS including Android/iOS virtual runtime and aggregate virtual-acceptance. Trusted Windows Authenticode remains MISSING_EXTERNAL after direct audit found zero local code-signing certificates, zero GitHub signing secrets, and Azure tenant-only login without a usable subscription. Desktop functional product is FINAL_ACCEPTED; signing is not falsely promoted. Evidence: evidence/R39_DESKTOP_FINAL_CLOSURE_20260930.json.

- 2026-09-30 R40 strict deep-audit delta: product candidate 9eb44a264466fa430ec62c87ebb2ee4b369cf74b; Windows exact installer C64CC98D08D3216BFAADE7D50A2F62D7B6734C8A9490CEFC6C52D395D1D17F32 PASS (17/17 app + 17/17 gateway parity, 5/5 UI smoke, X→tray hidden by 250ms, restore/single-instance PASS, fail-closed cleanup PASS, zero residue, route unchanged, local R40 correctly refuses public R39 downgrade). Full local pytest 181/181 PASS. Linux R13 exact local build 3FFE2DBFBF5D2473D3B6C2AFCF39AD553337790BEDC6ACAC47BA8C8264C132FF remains MISSING live host acceptance because aliemad-Labtop is offline. Evidence: evidence/R40_WINDOWS_EXACT_ACCEPTANCE_20260930.json and evidence/R40_DEEP_AUDIT_ACCEPTANCE_20260930.json.

- 2026-09-30 R40 Linux R13 exact live acceptance: final candidate package SHA-256 3FFE2DBFBF5D2473D3B6C2AFCF39AD553337790BEDC6ACAC47BA8C8264C132FF rebuilt from ab6a246 and exact-installed on aliemad-Labtop. Integrity 9/9 PASS; all IPv4 routes preserved byte-for-byte; pre-existing external tun0/default route preserved; SIGTERM/Full Exit cleanup PASS with process exit and route/tun unchanged. Pre-publish UpdateCheck hit GitHub unauthenticated 403 rate limit and is classified EXTERNAL_RATE_LIMIT, with post-publish recheck required. Evidence: evidence/R40_LINUX_R13_EXACT_ACCEPTANCE_20260930.json.

- 2026-09-30 R41 root cause: post-publish Linux R13 self-update returned localRevision=12 despite VERSION=4.2.0-linux.13-r40, so same public R13 was falsely reported as available. Root cause is hard-coded local_rev=12. R41/Linux R14 derives local revision from VERSION, fails closed on malformed version, adds regression coverage, and updates hosted Linux CI to build the current R14 package. Windows R40 runtime is unchanged. Evidence: evidence/R41_LINUX_UPDATE_REVISION_FIX_20260930.json.

- 2026-09-30 R41 Linux R14 live acceptance: exact package B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984 from source f1da84a installed on aliemad-Labtop; integrity 9/9 PASS; external tun0 and all routes preserved; pre-publish updater PASS local=14/remote=13/updateAvailable=false; SIGTERM/Full Exit PASS with process exit and route/tun unchanged; hosted CI #148/run 36739836044 complete SUCCESS including virtual-acceptance.

- 2026-09-30 R41 PUBLIC FINAL: runtime/release main at publication 967fe5920a00f102e408002f8ffb030e4d15b6fd; release v4.2.0-r41-final. Windows R40 unchanged asset C64CC98D08D3216BFAADE7D50A2F62D7B6734C8A9490CEFC6C52D395D1D17F32 and Linux R14 B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984 published with exact GitHub digests. Post-publish UpdateCheck PASS: Windows 40=40/no-update/route unchanged; Linux 14=14/no-update, 9/9 integrity, external tun0/routes unchanged. Post-merge CI #151 had one transient Android emulator 'adb: device offline' after build/install/VPN-consent stages; targeted same-commit retry PASS and aggregate virtual-acceptance PASS. Evidence: evidence/R41_PUBLIC_FINAL_ACCEPTANCE_20260930.json.

- 2026-09-30 R41 authority-label closure: PR #19 merged control/evidence-only commit f56d8d30213fbde4f5702d6a49d85c5591e7dabc after PR CI #154 PASS. Runtime/release authority remains 967fe5920a00f102e408002f8ffb030e4d15b6fd; future control-only main commits must not be confused with runtime release bytes. GitHub repository description was synchronized from stale R39 wording to R41 / Windows R40 + Linux R14.

- 2026-09-30 FINAL WORKSPACE CLOSEOUT: GitHub reduced to branch main only with zero open PRs/issues; obsolete Dependabot major-upgrade PRs #2-#5 closed as deferred maintenance. Windows and Linux each reduced to one clean canonical main worktree synced to origin/main. Dirty/non-merged legacy states were archived before cleanup: Windows archive manifest SHA-256 AC2A40DF...A96E and branch bundle 0987AB8F...E7BB; Linux branch bundle 3cfd30a8...d39d and verified SHA256SUMS baf05b01...b85e. No runtime/network mutation was performed by workspace cleanup. Evidence: evidence/R41_FINAL_WORKSPACE_CLOSEOUT_20260930.json.

- 2026-09-30 Android CI hardening candidate: PR #21 CI #160 proved emulator boot/ADB/build/APK install/MainActivity launch PASS (Status: ok) but failed on a one-shot first UI hierarchy state assertion. This differs from the earlier #151 ADB-offline transient. Root cause is PROBABLE_HIGH: hierarchy publication can lag Activity launch completion. Official Android UI Automator guidance favors bounded element/state waiting and stability controls. Harness now uses bounded dump_until_contains waits at all lifecycle transitions, preserves fail-closed assertions, emits diagnostics on timeout, and has a static regression guard. Promotion requires a fresh direct PASS, not a blind job rerun. Evidence: evidence/R41_FINAL_WORKSPACE_CLOSEOUT_20260930.json.

- 2026-09-30 Android CI hardening validation: fresh CI #162 (run 36765328910) on hardened head 7bb945a passed android-emulator-runtime directly with no manual rerun; ios-simulator-runtime and aggregate virtual-acceptance also PASS. Prevention is CLOSED_PASS while root-cause wording remains PROBABLE_HIGH rather than overstated.

- 2026-10-03 V43 INSTALLER CORRECTION CANDIDATE: owner screenshot proved a fresh-install blocker in the published 4.2 installer: PrepareToInstall invoked pwsh.exe with {app} as Exec WorkingDir before that directory existed, so process launch failed and Setup displayed could not verify the upgrade process state. Root cause is source-confirmed. V43 separates fresh install from upgrade: absent app root bypasses previous-install verification; existing installs retain lifecycle safety and execute Prepare-Upgrade.ps1 from Setup {tmp} with explicit AppRoot. Removing the lifecycle guard entirely was rejected as unnecessary and less safe. Exact current installer: FreeNetHub_4.3.0_R43_Setup.exe, SHA-256 E577BFC662E8D5EF8C6B2512C4904E6161A114F7EB78AB7FE02F62D347FDFD91, Authenticode MISSING_EXTERNAL_NOTSIGNED. Hosted clean-install gate remains OPEN before promotion. Evidence: evidence/V43_INSTALLER_ACCEPTANCE_20261003.json; knowledge: evidence/V43_PROJECT_KNOWLEDGE_20261003.json.

- 2026-10-03 V43 PUBLIC FINAL: PR #22 head 82daa9e passed CI #167 including exact fresh install into an absent app directory and aggregate virtual-acceptance; merged runtime commit 5930326185bbeb1118a1fb4381d56e79d0af78bd passed post-merge CI #168 with the same fresh-install gate. Public release v4.3.0 carries Windows SHA-256 E577BFC662E8D5EF8C6B2512C4904E6161A114F7EB78AB7FE02F62D347FDFD91 and unchanged Linux R14 SHA-256 B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984. Exact public Windows asset upgraded live 4.2 R40 -> 4.3 R43 with exit 0 and route unchanged; post-publish Windows 43=43/no-update and Linux 14=14/no-update PASS. GitHub Releases reduced to v4.3.0 only; 16 superseded release objects removed after inventory archive SHA-256 B32D30624F1E9776F6309F295F815CD798875DABBA9E5C3608783FB791CE66EB, while Git tags/history were preserved. Authenticode remains MISSING_EXTERNAL/NotSigned. Evidence: evidence/V43_INSTALLER_ACCEPTANCE_20261003.json.

- 2026-10-04 V431 INTEGRITY HOTFIX CANDIDATE: public v4.3.0 installed but failed before WPF window creation because the app integrity manifest did not match the exact Windows-packaged bytes for View.xaml and directdpi/hosts.txt. The guard itself behaved correctly; the package/manifest byte contract was wrong. Prevention is minimum-sufficient: build fails unless every protected app file hash/size matches the exact raw bytes packaged, hosted fresh-install CI launches the installed UI and rejects ui-error.txt, and all manifest entries are regression-checked. The same owner-system audit exposed the Node UI defect: 2000 backend nodes existed but NodeList was squeezed to a near-zero-height strip and lacked explicit DataGrid text/header/cell styling. V431 gives NodeList a minimum height, explicit readable styles/row sizing, and collapses advanced metadata by default. Exact current installer FreeNetHub_4.3.1_R44_Setup.exe SHA-256 A2613A62AEE78664C43D451B262A79456D077B40EC53CD083DDEE783D4B76A19 / 24266713 bytes has PASS_RAW_BYTES_MATCH_APP_MANIFEST. Local targeted 23/23 and full 195/195 PASS; exact live install is 4.3.1-r44-final with 17/17 integrity, route unchanged, real UI window and no ui-error. Live UI Automation measured NodeList 1088x473, 15 visible rows and 144 text elements with real VLESS/Shadowsocks data. Hosted promotion remains OPEN.

- 2026-10-04 V431 LOCAL EXACT ACCEPTANCE: exact installer FreeNetHub_4.3.1_R44_Setup.exe SHA-256 A2613A62AEE78664C43D451B262A79456D077B40EC53CD083DDEE783D4B76A19 / 24266713 bytes passed raw-byte manifest preflight and live upgrade/install with exit 0, 17/17 installed manifest entries, FreeNet Hub UI window present, no ui-error, and default route unchanged (Ethernet 3 -> 192.168.20.1). Node UI root cause was layout collapse, not missing backend data: after MinHeight/style/advanced-metadata collapse fix, live UI Automation measured NodeList 1088x473 with 15 visible rows and 144 text elements. First live upgrade also exposed two disconnected owned WARP/CFON orphan listeners with dead parents; lifecycle guard now cleans only that narrowly verified orphan case while retaining fail-closed behavior for connected/unknown/live-parent runtime. Full regression 195/195 PASS. Hosted promotion remains OPEN.

- 2026-10-04 V431 PUBLIC FINAL: PR #24 merged as runtime commit 3bfbb8f51881eb53579325f80bf4e370bba42c76; PR CI #183, post-merge main CI #184 and tag CI #185 all SUCCESS, including windows-installer-fresh and aggregate virtual-acceptance. GitHub release v4.3.1 is Latest and sole public Release authority. Public Windows asset FreeNetHub_4.3.1_R44_Setup.exe is 24,266,713 bytes / SHA-256 A2613A62AEE78664C43D451B262A79456D077B40EC53CD083DDEE783D4B76A19; Linux remains accepted R14, 213,124 bytes / SHA-256 B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984. GitHub server-side digests and independent public downloads match both hashes. Broken v4.3.0 release object was removed after metadata archival, while tags/history v4.3.0 -> 5930326... and v4.3.1 -> 3bfbb8f... were preserved. Authenticode remains MISSING_EXTERNAL/NotSigned and is the only Windows distribution polish gap, not a functional correctness blocker. Evidence: evidence/V431_PUBLIC_RELEASE_CLOSURE_20261004.json; superseded release archive: evidence/V430_SUPERSEDED_RELEASE_ARCHIVE_20261004.json.

- 2026-10-04 V431 REPOSITORY CLOSURE: evidence/control commit `44dd1b68e64c995ae6cc9594b1603e7d965c0c32` passed hosted CI #186 / run `37185596527`, including `windows-installer-fresh`, Android emulator runtime, iOS simulator runtime and aggregate `virtual-acceptance`. This validates the final repository control/evidence state; runtime release authority remains tag `v4.3.1 -> 3bfbb8f51881eb53579325f80bf4e370bba42c76`.


## Audit continuation — 2026-10-04 (new chat after stream failure)
Status: CURRENT / PARTIAL_PASS_WITH_OPEN_GATES
- Windows owner source is still `v4.3.2-preconnect-test-hotfix` at `cdb251d44a41ba9f3970a7ee7cdc05b87a7b89cf`; public `main` remains `009151581bc5c3d7fe955b3000ac5fb45b843d2b`. R45 is therefore OWNER_LOCAL_NOT_PUBLIC.
- Existing R45 backend evidence remains valid: installed/source pre-connect Ping+Download+Upload backend PASS and prior focused regression 130/130 PASS. In this continuation, a full pytest rerun was intentionally not auto-promoted: synchronous transport timed out after 24 passing dots, so result = INCOMPLETE_NOT_FAIL.
- Windows visual post-click rendering remains OPEN/UNPROVEN. FreeNet Hub launched and its window was observed, but Commander rejected focus/click with `GUI_TAKEOVER_NOT_AUTHORIZED`; no visual PASS claim is permitted.
- Linux source is clean at `main...origin/main` commit `0091515`. Installed runtime remains `4.2.0-linux.14-r41`. Current Linux selftest/browser-profile/console-policy/private-state/R37-parity checks all PASS.
- No tunnel/proxy/VPN connection was started or stopped by this audit. The Windows UI process opened for observation was terminated afterward. Pytest temp directory created by the audit was removed and verified absent.
- New evidence: `evidence/HOLISTIC_AUDIT_CONTINUATION_20261004.json`, SHA-256 `3fda63fa0ae32d64fdaf4c6ff8cedf2fb8c07b38069aa0e2c98b86b036fc2abe`.

### Current critical path
1. Close only the Windows R45 visual post-click gate with authorized GUI interaction: click the installed pre-connect Ping+Download+Upload test once and prove all three values replace dashes.
2. If and only if that visual gate passes, record screenshot/evidence and decide whether to promote `cdb251d` into public `main`/release.
3. Keep Authenticode, physical-console E2E and mobile production signing/forwarding as explicit external/separate gates; do not block desktop functional closure on them.

### Exact Next Action
Obtain an authorized GUI takeover lease for the owner Windows session, run the single pre-connect UI test without changing tunnel state, capture post-click evidence, and then update promotion authority.


## R46 holistic finalization — local gates milestone (2026-10-04)
Status: CURRENT / R46_LOCAL_GATES_PASS_HOSTED_OPEN
- Previous public authority remains FreeNet Hub v4.3.1 / Windows R44. R46 is not public yet.
- Windows R46 source WPF pre-connect rendering is CLOSED_PASS: Ping 95 ms, Download 34.6 Mbps, Upload 1.7 Mbps rendered from the successful Speed/DIRECT worker. Root cause was StrictMode access to optional `checked`; minimum fix uses `ContainsKey('checked')` and retains StrictMode.
- Owner Windows CFON session was preserved byte-for-byte; default route and DNS were unchanged by the R46 BASE/DIRECT test.
- Windows full local regression: 183/183 PASS.
- Exact current R46 installer build: `delivery/github_v4.3.2/FreeNetHub_4.3.2_R46_Setup.exe`, 24,254,909 bytes, SHA-256 `227881038598CB77CD6F1EB03E4EE0884E11C054A6B1881219BF6B43A678199F`; 25 build inputs frozen; raw-byte app-manifest preflight PASS; Authenticode NotSigned (external distribution identity gate).
- Linux authority remains public R14/R41 at source commit `009151581bc5c3d7fe955b3000ac5fb45b843d2b`. Current owner-laptop revalidation PASS: all Linux tests PASS, installed integrity 9/9 PASS, route and DNS unchanged.
- Android is configured for API 36 with AGP 8.10.1 / Gradle 8.11.1 / Build Tools 35.0.0 and remains fail-closed because packet forwarding core is not linked. iOS CI targets macOS 26 / Xcode 26 / iOS 26 SDK and remains fail-closed because packet forwarding core is not linked. Production mobile forwarding/signing/device validation is a separate external/legal architecture track; the repository currently has no project-wide license, so libbox/sing-box embedding is not auto-promoted.
- Console software/virtual acceptance remains on the hosted critical path; physical console field E2E remains external hardware validation.
- Evidence authority: `evidence/R46_WINDOWS_PRECONNECT_UI_CLOSURE_20261004.json`, `evidence/R46_LINUX_R14_REVALIDATION_20261004.json`, `evidence/R46_PLATFORM_BENCHMARK_20261004.json`, `evidence/V432_R46_INSTALLER_BUILD_20261004.json`, `evidence/V432_R46_CANDIDATE_ACCEPTANCE_20261004.json`.

### ← CURRENT critical path
1. Rebuild PUBLIC_MANIFEST once from the final local candidate and run public-tree + security verification.
2. If PASS, commit/push R46 candidate and require hosted Windows fresh-install + Linux + Android API36 emulator + iOS Xcode26 simulator + console virtual + aggregate acceptance.
3. Only after hosted PASS: merge/promote v4.3.2, publish exact Windows R46 + unchanged accepted Linux R14 assets, verify GitHub digests/download hashes and post-publish update equality.
4. Keep trusted Authenticode, physical console field E2E and mobile production forwarding/signing/device explicitly external until independently proven.

### Exact Next Action
Rebuild `PUBLIC_MANIFEST.json` once from this candidate, run `verify_public_tree.py` and `security_scan_public.py`, and stop promotion on any mismatch.


## V432 PUBLIC FINAL CLOSURE — 2026-10-04
Status: CURRENT / PUBLIC_FINAL_CLOSED
- Runtime/release authority is immutable tag `v4.3.2 -> dd8bee89be71e39777152b6428c2ec0b1ba50809`. Promotion used fast-forward only; no merge commit changed the tested SHA.
- Hosted CI evidence is complete on the exact same SHA: branch CI #187 / run 37207042859 SUCCESS, main CI #188 / run 37208572220 SUCCESS, tag CI #189 / run 37209108871 SUCCESS. Required Windows fresh-install, Linux, console virtual, Android API36 emulator, iOS Xcode26 simulator and aggregate virtual-acceptance gates all PASS.
- Public release `v4.3.2` / `FreeNet Hub 4.3.2 Final` is latest. Windows asset `FreeNetHub_4.3.2_R46_Setup.exe` = 24,254,909 bytes / SHA-256 `227881038598CB77CD6F1EB03E4EE0884E11C054A6B1881219BF6B43A678199F`. Linux asset remains accepted R14 = 213,124 bytes / SHA-256 `B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984`. GitHub server digests and independent post-publish downloads match both hashes exactly.
- Windows post-publish `UpdateCheck` PASS: installed R45 sees remote R46 as newer and selects the exact R46 name/size/digest. Active CFON session, default-route state and DNS state hashes are unchanged before/after.
- Linux owner-laptop post-publish `update_check()` PASS: installed `4.2.0-linux.14-r41`, localRevision=14, remoteRevision=14, updateAvailable=false, and route/DNS/session hashes are unchanged.
- First release-create wrapper attempt failed before applying any remote mutation because nested PowerShell quoting consumed variable markers. Remote reconciliation proved release/assets absent; retry was only then permitted. Direct `gh release create` with notes under `.git` succeeded. Prevention: avoid nested PowerShell quoting for release mutation and always reconcile remote state before retry.
- `RELEASE.json` is intentionally not rewritten post-publication because it is one of the 25 frozen installer inputs; changing it would create source/runtime byte drift from the published R46 artifact. Post-release state is recorded in Brain/Evidence instead.
- External/separate gates remain explicit and non-blocking for this desktop release: trusted Windows Authenticode identity (MISSING_EXTERNAL/NotSigned), physical-console field E2E, Android production forwarding/signing/real-device, and iOS production forwarding/signing/entitlement/real-device.
- Authoritative closure evidence: `evidence/V432_PUBLIC_RELEASE_CLOSURE_20261004.json`; project knowledge: `evidence/V432_PROJECT_KNOWLEDGE_20261004.json`; Windows updater proof: `evidence/V432_POSTPUBLISH_UPDATECHECK_20261004.json`.

### Roadmap ← CURRENT
Desktop/public v4.3.2 objective: CLOSED_PASS. No desktop release blocker remains. Future runtime work must start as a new change set and must not mutate the v4.3.2 tag or published asset bytes.

### Exact Next Action
Commit the control-only Brain/Evidence/Public Manifest closure, verify the public tree/security scan, push it to main, and require one final repository-state CI PASS. Then record that CI result without changing runtime/release authority.


### V432 repository-state closure — 2026-10-04
- Control-only main commit `db38157a3affad6ace0f4796e554271eda27d5f1` passed CI #190 / run `37214169321` with all 10 jobs SUCCESS, including exact Windows fresh-install, Linux static, console virtual, Android API36 emulator, iOS simulator and aggregate `virtual-acceptance`.
- Runtime/installer diff versus tag `v4.3.2` is empty. Runtime release authority therefore remains `v4.3.2 -> dd8bee89be71e39777152b6428c2ec0b1ba50809`; the repository closure commit is control/evidence only.
- Status: FINAL / PUBLIC_FINAL_CLOSED. No desktop/public-release blocker remains.
- Exact Next Action: none for v4.3.2. Preserve tag/assets immutably; begin any future runtime change under a new change set. External Authenticode, physical-console field E2E, and production mobile forwarding/signing/device gates remain separate.

## V433 R47 Smart / Node / Sort candidate — 2026-10-05
Status: CURRENT / LOCAL_GATES_PASS_HOSTED_OPEN
- Previous public authority remains immutable v4.3.2 -> dd8bee89be71e39777152b6428c2ec0b1ba50809. R47 is not public.
- Smart now benchmarks all seven real browser methods and paints terminal per-method results. Smart remains selector-only; DIRECT/CUSTOM are comparison-only for automatic selection.
- Live Smart PASS: Best=WARP; rank=['WARP', 'CFON', 'TOR', 'GOOL']; installed session, route and DNS unchanged.
- Node live PASS: 2000 nodes, 1297 reachable endpoints; current-run best node=shadowsocks-812343868 / ss / AURX_HTTP_VERIFIED, country=BG, Ping=268.9 ms, Down=10.45 Mbps, Up=8.16 Mbps.
- Node table sorting is typed; missing values remain last; numeric dropdown default is ascending and header click toggles direction.
- Harness-only failures were isolated and guarded: bad stage destination naming, omitted local_gateway sing-box authority, and StrictMode optional-property access.
- Full local regression PASS 196/196; fail-closed PASS; security PASS after local-path redaction; git diff --check PASS.
- Exact local installer: FreeNetHub_4.3.3_R47_Setup.exe, 24276785 bytes, SHA-256 A4B82AB5B2176F11C1AE4AAB920331D5FC7B82B988655932DC83A253FB188B63, raw app-manifest preflight PASS. Authenticode remains NotSigned/external.
- Evidence: evidence/V433_R47_CANDIDATE_ACCEPTANCE_20261005.json; knowledge: evidence/V433_PROJECT_KNOWLEDGE_20261005.json.

### Roadmap ← CURRENT
1. Rebuild PUBLIC_MANIFEST.json and run verify_public_tree.py + security scan.
2. Record public-tree closure, rebuild/verify once more so closure evidence is included.
3. Commit/push R47 and require hosted Windows fresh-install + Linux + console virtual + Android emulator + iOS simulator + aggregate acceptance.
4. Promote/publish v4.3.3 only after hosted PASS; Authenticode remains external.

### Exact Next Action
Rebuild and verify the public manifest/tree on the exact R47 candidate; stop promotion on any mismatch.

### V433 R47 local promotion gate closure — 2026-10-05
Status: CURRENT / LOCAL_GATES_CLOSED_HOSTED_OPEN
- Exact R47 candidate behavior is locally CLOSED_PASS: Smart tests all seven real browser methods with per-method terminal results while remaining selector-only; Node Pool returns the current-run best successful node identity/performance; Node numeric sorting uses raw numeric values ascending by default with missing values last, while text sorting is A-Z.
- Live Smart and Node stage validations preserved installed session, route and DNS. Current-run Node proof selected the tested BG node with Ping 268.9 ms / Download 10.45 Mbps / Upload 8.16 Mbps.
- Full frozen-candidate regression: 196/196 PASS. Mobile fail-closed PASS. Public security PASS. git diff --check PASS.
- Exact local installer: delivery/github_v4.3.3/FreeNetHub_4.3.3_R47_Setup.exe, 24,276,785 bytes, SHA-256 A4B82AB5B2176F11C1AE4AAB920331D5FC7B82B988655932DC83A253FB188B63; 25 frozen inputs and raw app-manifest preflight PASS. Authenticode remains NotSigned / external.
- Public-tree local gate PASS: PUBLIC_MANIFEST covered 466 files; public/app/gateway/cross-platform/windows manifests, release hashes and forbidden-runtime-artifact checks all PASS with zero mismatches.
- Public authority remains immutable v4.3.2 -> dd8bee89be71e39777152b6428c2ec0b1ba50809. R47 is not public until hosted CI passes.

#### Roadmap ← CURRENT
1. Rebuild PUBLIC_MANIFEST once more so this closure record is included, then verify public tree/security.
2. Commit/push exact R47 branch and require hosted Windows fresh-install + Linux + console virtual + Android emulator + iOS simulator + aggregate acceptance.
3. Only after hosted PASS: promote exact tested SHA to main/tag v4.3.3 and publish the exact R47 Windows installer plus unchanged accepted Linux R14.
4. Trusted Authenticode remains an explicit external distribution gate.

#### Exact Next Action
Final PUBLIC_MANIFEST rebuild/verification, then commit and push the exact R47 candidate for hosted CI.

## V433 PUBLIC RELEASE — 2026-10-05
Status: CURRENT / PUBLIC_RELEASED_REPOSITORY_CLOSURE_PENDING
- Runtime/release authority is now exact tag v4.3.3 -> af1983f18a5bcf49d0d8f0b8ed89a4649ff42a93. The tag dereferences to the same SHA that passed branch CI 37237796960, main CI 37238257289 and tag CI 37257248862.
- All required hosted gates PASS on the exact authority SHA: windows-unit, windows-installer-fresh, windows-virtual-signing, linux-static, console-virtual-e2e, android-build, android-emulator-runtime, ios-static, ios-simulator-runtime and aggregate virtual-acceptance.
- Public release FreeNet Hub 4.3.3 Final is latest. Windows asset FreeNetHub_4.3.3_R47_Setup.exe = 24,276,785 bytes / SHA-256 A4B82AB5B2176F11C1AE4AAB920331D5FC7B82B988655932DC83A253FB188B63. Linux asset remains unchanged accepted R14 = 213,124 bytes / SHA-256 B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984. GitHub server digests and independently re-downloaded bytes match both hashes exactly.
- One gh release download invocation returned exit 1 with empty stderr although both fresh destination files were complete and matched exact size/hash. This is recorded as a CLI/transport anomaly; no blind rerun was performed because byte-level evidence is authoritative.
- Windows post-publish UpdateCheck PASS on installed R45: remote R47 is newer, exact asset name/size/digest selected, and active CFON session/default route/DNS hashes are unchanged before/after.
- Linux owner-laptop post-publish update_check() PASS on installed 4.2.0-linux.14-r41: remote Linux revision remains 14, updateAvailable=false, exact unchanged R14 asset selected, and session/route/DNS hashes are unchanged.
- Production mobile packet forwarding/signing/real-device gates remain separate external work; current Android/iOS hosted evidence is fail-closed integration validation, not production tunnel completion. Physical console field E2E and trusted Windows Authenticode also remain external.
- Authoritative public closure evidence: evidence/V433_PUBLIC_RELEASE_CLOSURE_20261005.json. Project knowledge: evidence/V433_PROJECT_KNOWLEDGE_20261005.json.

### Roadmap ← CURRENT
1. Create one control-only repository closure commit containing Brain/Evidence/Public Manifest updates; runtime diff versus v4.3.3 must be empty.
2. Push that control commit to main and require one final repository-state CI PASS.
3. Record the repository-state CI result without mutating v4.3.3 tag or published asset bytes.
4. Preserve trusted Authenticode, physical-console field E2E and production mobile forwarding/signing/device as explicit external gates.

### Exact Next Action
Rebuild PUBLIC_MANIFEST.json from this control-only closure state, verify public tree/security/diff and zero runtime diff versus v4.3.3, then commit/push for final repository-state CI.

### V433 Repository Closure CI
- Final control-only closure commit `d13ef406eadd04c626a9d1e6c65e8219fd55d6a3` passed hosted CI run `37259927516`.
- Runtime diff versus immutable authority tag `v4.3.3` is NONE; runtime authority remains `v4.3.3 -> af1983f18a5bcf49d0d8f0b8ed89a4649ff42a93`.
- Status: PUBLIC_FINAL_CLOSED. New resilience work must start as a new change set; do not mutate v4.3.3 tag or asset bytes.

## V434 R48 RESILIENCE — LOCAL GATES
Status: CURRENT / LOCAL_GATES_PASS_HOSTED_OPEN
- Baseline authority remains immutable v4.3.3 / af1983f18a5bcf49d0d8f0b8ed89a4649ff42a93. R48 is not public yet.
- R48 promotes the already-shipped Tor WebTunnel and obfs4 backends into Smart/AUTO/Scan/UI only when private bridge files parse validly. Invalid/missing bridge files do not enter Smart or Emergency priority.
- Country=AUTO can automatically fail over through configured valid bridges; strict country selection remains NODE/CFON only.
- Live isolated bridge validation preserved installed CFON session, route and DNS. Current obfs4 bridge PASS: Ping 1213.9 ms / Download 1.2 Mbps / Upload 1.34 Mbps. Current WebTunnel private bridge FAIL_CLOSED with PATH_NOT_VERIFIED_WEBTUNNEL; no false PASS claim.
- R48 focused regression 23/23 PASS; exact final full regression 206/206 PASS; Python/PowerShell/XAML parse PASS; mobile fail-closed PASS; public security PASS; git diff check PASS.
- Integrity guard caught a stale engine.py manifest entry after a runtime delta; manifest was resynced from raw bytes and the full suite then passed. Emergency invalid-bridge ordering was also corrected to use configured_bridge_modes().
- Exact final local installer: delivery/github_v4.3.4/FreeNetHub_4.3.4_R48_Setup.exe, 24,271,225 bytes, SHA-256 5AAFF015FFE196FF82132E52B891E73CF2FCD4ACB6A36CFD64CA50C9347D3FBA; 25 frozen inputs; raw app-manifest preflight PASS; Authenticode NotSigned/external.
- Evidence: evidence/R48_RESILIENCE_AUDIT_20261005.json; evidence/R48_BRIDGE_LIVE_20261005.json; evidence/V434_R48_CANDIDATE_ACCEPTANCE_20261005.json; knowledge: evidence/V434_PROJECT_KNOWLEDGE_20261005.json.
- Further protocols are not added as decorative UI: Psiphon, OpenVPN/OpenConnect, TUIC/AnyTLS/ShadowTLS/Naive and AmneziaWG-like transports remain separate evidence-gated change sets because compatible server/config/dependency/license authority is not yet proven.
- Guaranteeing connectivity when every physical/upstream path is unavailable remains UNPROVEN and is not claimed.

### Roadmap ← CURRENT
1. Rebuild PUBLIC_MANIFEST from exact R48 candidate including new evidence/Brain records and verify public tree/security.
2. Commit/push exact R48 candidate and require hosted Windows fresh-install + Linux + console virtual + Android emulator + iOS simulator + aggregate acceptance.
3. Only after hosted PASS: tag/publish v4.3.4 exact R48 Windows installer plus unchanged accepted Linux R14, then verify public digests/download hashes and Windows/Linux updater semantics.
4. Keep Authenticode, physical-console field E2E and production mobile forwarding/signing/device as explicit external gates.

### Exact Next Action
Rebuild/verify PUBLIC_MANIFEST and stop promotion on any mismatch; otherwise commit/push exact R48 candidate for hosted CI.

### V434 R48 local promotion gate closure — 2026-10-05
Status: CURRENT / LOCAL_GATES_CLOSED_HOSTED_OPEN
- Exact R48 runtime candidate remains based on immutable public authority v4.3.3 / af1983f18a5bcf49d0d8f0b8ed89a4649ff42a93; v4.3.3 tag/assets are untouched.
- Smart/AUTO/Scan/Emergency now admit WebTunnel/obfs4 only when private bridge configuration passes strict parser validation. Country=AUTO may auto-failover through valid configured bridges; strict-country automatic selection remains NODE/CFON only.
- Live isolated evidence: obfs4 PASS (Ping 1213.9 ms / Download 1.2 Mbps / Upload 1.34 Mbps); current private WebTunnel bridge fails closed with PATH_NOT_VERIFIED_WEBTUNNEL. Installed session, route, DNS and temporary-port ownership were preserved.
- Focused regression 23/23 PASS; full regression 206/206 PASS; Python/PowerShell/XAML parse PASS; mobile fail-closed PASS; public security PASS; git diff --check PASS.
- Exact installer candidate: FreeNetHub_4.3.4_R48_Setup.exe = 24,271,225 bytes / SHA-256 5AAFF015FFE196FF82132E52B891E73CF2FCD4ACB6A36CFD64CA50C9347D3FBA; 25 frozen inputs; raw app-manifest preflight PASS; Authenticode remains external/NotSigned.
- Public-tree verification PASS after correcting a control-plane acceptance-status mismatch: 476 public files, app/gateway/cross-platform/windows manifests and RELEASE hashes all PASS with zero mismatches; forbidden runtime/private bridge artifacts are absent.
- Root cause/prevention: acceptance evidence status must exactly equal RELEASE.status; future final public-tree gate must enforce this before promotion.

#### Roadmap ← CURRENT
1. Rebuild PUBLIC_MANIFEST once more so this local-closure record is included, then verify public tree/security.
2. Commit/push exact R48 candidate and require hosted Windows fresh-install, Linux, console virtual, Android emulator, iOS simulator and aggregate virtual acceptance on the exact SHA.
3. Only after hosted PASS: tag/publish v4.3.4 exact Windows R48 asset plus unchanged accepted Linux R14; verify server digests, independent re-download hashes and Windows/Linux updater semantics.
4. Trusted Authenticode, physical-console field E2E and production mobile packet-forwarding/signing/real-device remain explicit external gates.

#### Exact Next Action
Final PUBLIC_MANIFEST rebuild/verification, then commit/push exact R48 candidate for hosted CI. No public promotion before that PASS.

## V434 PUBLIC RELEASE — 2026-10-05
Status: CURRENT / PUBLIC_RELEASED_REPOSITORY_CLOSURE_PENDING
- Runtime/release authority is exact tag v4.3.4 -> 4a3a24351ac892563d2c01e7d40cd5a001fe13e5. Branch CI 37281848369, main CI 37282638834 and tag CI 37290013302 all SUCCESS on the same SHA, including Windows fresh-install, Linux, console virtual, Android emulator, iOS simulator and aggregate acceptance.
- Public release FreeNet Hub 4.3.4 Final is latest. Windows R48 asset = 24,271,225 bytes / SHA-256 5AAFF015FFE196FF82132E52B891E73CF2FCD4ACB6A36CFD64CA50C9347D3FBA. Linux remains unchanged accepted R14 = 213,124 bytes / SHA-256 B3FD52C76C9331660BA06B667BA07A7D7A4BEB87FBC074461CCA14F9E13FF984. GitHub digests and independent re-downloads match exactly.
- R48 resilience is evidence-backed: valid configured WebTunnel/obfs4 participate in Smart/AUTO/Scan/Emergency; missing or invalid bridge configs are excluded fail-closed. Current obfs4 live path passed; current private WebTunnel path fails closed instead of generating a false success.
- Windows installed updater read-only check PASS: installed R45 sees R48 as newer and selects exact asset bytes/digest; session/route/DNS unchanged. Linux installed R14 sees v4.3.4 Linux R14 as equal and updateAvailable=false; session/route/DNS unchanged.
- Post-release expansion audit checked the 11 configured public node sources. They currently expose VLESS/Trojan/VMess/SS/Hysteria2 but no TUIC/AnyTLS/ShadowTLS/Naive endpoints. Therefore additional automatic Smart methods are not added merely because sing-box can support them; OpenVPN/OpenConnect/Psiphon/other families remain evidence-gated until real config/server authority exists.
- No software guarantee is made for connectivity when all physical/upstream paths are unavailable. The product goal is maximum path diversity, failover and recovery with evidence-backed transports.
- Evidence: evidence/V434_PUBLIC_RELEASE_CLOSURE_20261005.json; evidence/V434_POSTPUBLISH_UPDATECHECK_20261005.json; evidence/V434_LINUX_POSTPUBLISH_UPDATECHECK_20261005.json; evidence/V434_POSTRELEASE_EXPANSION_AUDIT_20261005.json.

### Roadmap ← CURRENT
1. Rebuild PUBLIC_MANIFEST including public closure/expansion audit records and verify public tree/security.
2. Commit/push one control-only closure commit with zero runtime diff versus v4.3.4 and require final repository-state CI PASS.
3. Record final repository-state CI without mutating tag/assets.
4. Future protocol/profile imports begin as a new evidence-gated change set. Authenticode, physical console field E2E, and production mobile forwarding/signing/device remain external.

### Exact Next Action
Rebuild/verify PUBLIC_MANIFEST, prove runtime diff versus v4.3.4 is zero, commit/push control-only closure, and require final CI.

### V434 Repository Closure CI
- Final control-only closure commit 161619b9ab3c931d171f9d80082a4b1dc7fa0d71 passed hosted CI run 37292728318.
- Runtime diff versus immutable authority tag v4.3.4 is NONE; runtime authority remains v4.3.4 -> 4a3a24351ac892563d2c01e7d40cd5a001fe13e5.
- Status: PUBLIC_FINAL_CLOSED. Any further resilience work must start as a new evidence-gated change set.

## V435 R49 NODE PROTOCOL EXPANSION — 2026-10-05
Status: CURRENT / LOCAL_GATES_CLOSED_HOSTED_OPEN
- Baseline: public v4.3.4 / runtime commit 4a3a24351ac892563d2c01e7d40cd5a001fe13e5 / repository closure 7d6902f.
- R49 expands the existing pinned sing-box Node Pool without a new external tunnel dependency: TUIC and AnyTLS share imports, standalone sing-box JSON import for TUIC/AnyTLS/ShadowTLS, and fail-closed clipboard import for WebTunnel/obfs4 bridges.
- Naive remains intentionally not advertised because the installed Windows runtime lacks required libcronet.dll. OpenVPN/OpenConnect remain outside this product boundary, and Psiphon remains deferred because no authorized bootstrap/server-entry authority is integrated.
- Exact local regression: R49 focused 15/15 PASS; legacy compatibility 138/138 PASS; full suite 221/221 PASS; frozen-input integrity 26/26 PASS; Python compile and PowerShell/XAML parse PASS.
- Installed sing-box 1.14.0 runtime proof: parser-generated TUIC, AnyTLS and ShadowTLS configs all pass sing-box check and open their local SOCKS listeners. This proves config/runtime loading only; real external endpoints for these three protocols remain UNPROVEN because no authorized endpoint is available in current feeds.
- Runtime-preservation proof: installed session hash, IPv4 route state and DNS state are identical before/after synthetic runtime tests.
- Public security caught and closed one evidence-only privacy defect: initial synthetic receipts contained a local Windows user path. Receipts are now redacted to %LOCALAPPDATA% and security scan PASS.
- Public-tree verifier caught and closed stale RELEASE.json nodeHubSha256. The final frozen RELEASE authority is synced to app/nodehub.py.
- Exact final Windows installer: delivery/github_v4.3.5/FreeNetHub_4.3.5_R49_Setup.exe = 24,278,071 bytes / SHA-256 7BC7BCED649BE925B2D5C67D36FAFD6AEF0F1A3B613ADD7CC7B2D113859A201E. 25 frozen inputs and raw app-manifest preflight PASS. Authenticode remains NotSigned / external.
- Public tree: 489 files; public/app/gateway/cross-platform/windows manifests, release hashes, forbidden runtime artifacts, public security, mobile fail-closed and diff-check all PASS.
- Evidence authority: evidence/R49_PROTOCOL_EXPANSION_AUDIT_20261005.json; evidence/V435_R49_CANDIDATE_ACCEPTANCE_20261005.json; evidence/V435_PROJECT_KNOWLEDGE_20261005.json; evidence/R49_SYNTHETIC_RUNTIME_PRESERVATION_20261005.json; evidence/V435_R49_INSTALLER_BUILD_20261005.json.

### Roadmap ← CURRENT
1. Commit/push exact R49 candidate branch.
2. Require hosted exact-SHA Windows fresh-install, Linux, console virtual, Android emulator, iOS simulator and aggregate acceptance.
3. Only after hosted PASS: fast-forward/promote exact tested SHA, tag v4.3.5, require tag CI, publish exact R49 Windows bytes plus unchanged accepted Linux R14, then post-publish updater/digest verification.
4. Trusted Authenticode, physical-console field E2E, and production Android/iOS forwarding/signing/real-device remain separate external gates.

### Exact Next Action
Update only the changed control-file entries in PUBLIC_MANIFEST, verify complete public tree/security, commit/push exact R49 and require hosted CI.

### V435 R49 hosted Linux parity root-cause — 2026-10-05
Status: CURRENT / FIX_LOCAL_PASS_HOSTED_RETRY_OPEN
- Hosted CI run 37302766809 failed only linux-static. Windows unit/fresh-install/virtual-signing, console virtual, Android build/emulator and iOS static/simulator all passed; aggregate was skipped only because Linux failed.
- Root cause: R49 changed app/nodehub.py for TUIC/AnyTLS/ShadowTLS imports but crossplatform/linux/nodehub_shared.py remained at R48 bytes. The existing SHA parity guard correctly blocked promotion.
- Prevention: keep byte-parity guard; Linux shared nodehub is synchronized from app authority in the same change set. Because Linux package bytes changed, do not reuse R14 identity. Linux candidate is bumped to 4.2.0-linux.15-r42 / FreeNetHub_4.2.0_Linux_R15.zip.
- Local Linux logic gates PASS: selftest, console policy, browser profile, scope policy, R37 parity and updater revision. POSIX permission test is not authoritative on NTFS and remains a Linux-host/CI gate.
- R15 package candidate: 221,657 bytes / SHA-256 FBA77FB02A7E4F207FA12606B4E1A49D3311188501AC3C550D87F98F08ECDF01.
- Exact Next Action: rebuild Windows R49 installer because RELEASE/cross-platform authority changed, rerun full/public gates, commit/push parity fix and require hosted retry PASS before promotion.

### V435 R49 post-parity frozen installer — 2026-10-05
Status: CURRENT / LOCAL_FROZEN_CANDIDATE_HOSTED_RETRY_OPEN
- Linux parity fix changes RELEASE/cross-platform authority, so the earlier R49 Windows installer digest 7BC7BCED... is superseded.
- Current exact Windows R49 installer: 24,271,706 bytes / SHA-256 29227FA8E8A8FE388396204D4FEAE75FF24CE110ABE1CBA5BC45BEF9FF8231DF. Frozen inputs=25; raw app-manifest preflight PASS; Authenticode NotSigned/external.
- Current Linux candidate: 4.2.0-linux.15-r42 / FreeNetHub_4.2.0_Linux_R15.zip = 221,657 bytes / SHA-256 FBA77FB02A7E4F207FA12606B4E1A49D3311188501AC3C550D87F98F08ECDF01.
- Previous R49 Windows installer hash is historical/superseded and must not be promoted.
- Exact Next Action: full regression + public-tree/security on this frozen state, then commit/push parity fix and require hosted retry PASS.

### V435 R49 canonical cross-platform hash correction — 2026-10-05
- Public-tree verification found only releaseHashes/crossPlatformManifestSha256 mismatched after Linux R15 sync.
- Root cause: cross-platform manifest generator reported raw working-tree SHA (CRLF on Windows), while release verifier correctly hashes Git-canonical bytes. RELEASE must use canonical SHA.
- Raw SHA: 060A9D8E907E424F00DE45C2C5BE0A67EA6C2BE02D54456F4FD9D774E21FE570. Canonical release SHA: DE4F27B50EFF88E3A5E1F85D8B06D8F74E8F72391009773DC240445B39158D89.
- Prevention: release authorities use the same canonicalization policy as verify_public_tree; generator receipts may retain raw hashes only as secondary evidence.
- Because RELEASE is a frozen Windows installer input, rebuild the installer after this correction before promotion.

### V435 R49 canonical-authority frozen installer — 2026-10-05
Status: CURRENT / FINAL_LOCAL_FREEZE_PENDING_HOSTED_RETRY
- Correcting RELEASE to the Git-canonical cross-platform manifest hash required one final Windows installer rebuild.
- Current exact R49 Windows installer: 24,260,411 bytes / SHA-256 1EE176570BAA8605BD32170FE7E6E11D219204EEDB84012D1C0C28B50018974E; 25 frozen inputs; raw app-manifest preflight PASS; Authenticode NotSigned/external.
- Earlier R49 installer hashes 7BC7... and 29227... are superseded and must not be promoted.
- Linux candidate remains 4.2.0-linux.15-r42 / R15, 221,657 bytes / SHA-256 FBA77FB02A7E4F207FA12606B4E1A49D3311188501AC3C550D87F98F08ECDF01.
- Exact Next Action: one final regression/public verification, then commit/push exact state and require hosted retry PASS.

### V435 R49 parity-fixed local closure — 2026-10-05
Status: CURRENT / LOCAL_GATES_CLOSED_HOSTED_RETRY_OPEN
- Hosted CI first attempt failed only Linux nodehub byte parity; root cause was app/nodehub.py changing without synchronizing crossplatform/linux/nodehub_shared.py.
- Linux is now versioned as a new candidate, not silently mutated R14: 4.2.0-linux.15-r42 / FreeNetHub_4.2.0_Linux_R15.zip = 221,657 bytes / SHA-256 FBA77FB02A7E4F207FA12606B4E1A49D3311188501AC3C550D87F98F08ECDF01.
- Current Windows R49 installer authority: 24,260,411 bytes / SHA-256 1EE176570BAA8605BD32170FE7E6E11D219204EEDB84012D1C0C28B50018974E.
- Final local regression: 221/221 PASS. Fail-closed PASS. Public security PASS. diff-check PASS. Public tree PASS over 490 files with nested manifests/release hashes/forbidden-runtime checks all PASS.
- RELEASE cross-platform manifest authority uses Git-canonical bytes; raw Windows CRLF hash is evidence-only.
- Exact Next Action: rebuild PUBLIC_MANIFEST including this closure record, verify once more, commit/push exact R49 parity fix and require hosted retry CI PASS before any v4.3.5 promotion.

## V435 PUBLIC RELEASE — 2026-10-05
**Status: CURRENT / PUBLIC_RELEASED_REPOSITORY_CLOSURE_PENDING**

### Status / Key Result
- Exact candidate b47b7149a10d0bf1986fddb0eead32a05fa0b267 passed PR CI run 37312605504 with 10/10 required jobs.
- Merge/runtime authority is 93fea59d696b69eb5b723e2d6b2033d4fdb879dd. Main CI 37314410412 and exact tag v4.3.5 CI 37315272184 both SUCCESS on that SHA.
- Public release FreeNet Hub 4.3.5 Final is published. Windows R49 = 24,260,411 bytes / SHA-256 1EE176570BAA8605BD32170FE7E6E11D219204EEDB84012D1C0C28B50018974E; Linux R15 = 221,657 bytes / SHA-256 FBA77FB02A7E4F207FA12606B4E1A49D3311188501AC3C550D87F98F08ECDF01. GitHub digests and independent re-download hashes match.
- Windows owner install remains R45 intentionally because a healthy CFON browser session is active. Read-only updater check PASS: exact R49 asset discovered; session/route/DNS unchanged. Hosted fresh-install gates already validate R49 installer execution.
- Linux public updater R14->R15 PASS using the product path: digest verification, safe extraction/install, no connection started. Installed R15 integrity 9/9 PASS; post-update local=remote revision 15 and updateAvailable=false.

### Linux live operational result
- Full Ping+Download+Upload: DIRECT PASS (277.7 ms / 17.19 / 4.36 Mbps), WARP PASS (527.5 / 15.84 / 1.32), GOOL PASS (467.8 / 14.28 / 1.20), CFON PASS (541.5 / 4.72 / 1.07), AUTO PASS via WARP (458.3 / 15.54 / 1.27).
- NODE proxy reached NL/YouTube but failed complete throughput. A diverse 4-node full benchmark found 0 full-health winners among 1,770 TCP-reachable endpoints; current best-node truth is NONE.
- TOR direct reached 64% bootstrap then timed out; obfs4 timed out at 0% on the current network. This is current dynamic path health, not hidden as success.
- Cleanup PASS: no owned node/warpplus/Tor residue; physical route and DNS exact; disconnected session semantics preserved. Raw session hash drift was timestamp-only.

### Authority / Open Gates
- Runtime/tag/assets are frozen at v4.3.5 / 93fea59d; this closure must not mutate app/crossplatform/windows runtime bytes.
- External/non-blocking: trusted Windows Authenticode; physical console field E2E; production Android/iOS forwarding/signing/real-device; authorized live TUIC/AnyTLS/ShadowTLS endpoint validation.
- Dynamic current-path limitation: Linux sampled NODE and TOR are not live-full-health now; AUTO/WARP remains operational.

### Roadmap ← CURRENT
1. Public v4.3.5 exact-SHA release + asset verification — Completed/PASS.
2. Windows non-disruptive updater + Linux real updater/install acceptance — Completed/PASS.
3. Linux all-method live audit + Node truth audit — Completed/MIXED CURRENT NETWORK, fail-closed with working AUTO fallback.
4. Control-only repository closure with zero runtime diff + final main CI — ← CURRENT.
5. External signing/physical console/production mobile/live authorized new-protocol endpoints — Deferred/External.

### Exact Next Action
Rebuild/verify PUBLIC_MANIFEST.json; prove runtime diff versus immutable v4.3.5 is NONE; commit/push only Brain/Knowledge/evidence/manifest closure records and require final main CI.

## V436 R50 NODE SELECTION QUALITY — 2026-10-05
**Status: CURRENT / LOCAL_GATES_CLOSED_HOSTED_OPEN**

### Root Cause / Fix
- Live Linux R15 evidence disproved the earlier best-node-none conclusion: a 12-candidate full benchmark found 3 full-health nodes, while the prior fixed 4-candidate sample found none.
- Linux best-node action is now bounded/adaptive: batches of 4, maximum 24 candidates, stopping after 3 full-health PASS results.
- Windows and Linux smart node ordering now prioritize measured full-health HTTPS/throughput results before TCP-only reachability hints.
- Windows batch result exposes deterministic best; UI reports explicit PASS/FAIL/HTTPS/TCP state instead of ambiguous placeholders.

### Local Acceptance
- Full regression: 244/244 PASS.
- Linux: selftest PASS at 4.2.0-linux.16-r43; parity PASS; updater revision PASS.
- Windows exact fresh install/UI smoke PASS; default route remained 192.168.20.1.
- Windows R50 installer: 24,258,557 bytes / SHA-256 8F458553E7EA3E4A88A31D1C0F6F9B4970DF578C859C2A739220ECED7532E8B4; 25 frozen inputs; manifest preflight PASS; Authenticode NotSigned/external.
- Linux R16 package: 225,314 bytes / SHA-256 01F852B1350C591EAD5C03A0F094F92B4861E1D1DA96226A48B9AE691D48C503.
- Earlier R50 installer FB317C... is superseded because it preceded final frozen RELEASE authority.
- TOR direct on the current Linux network reached 67% at 90s and timed out; route/DNS/session semantics were preserved. This remains dynamic network health, not a product PASS claim.

### Roadmap ← CURRENT
1. Final public-manifest/security/fail-closed verification — CURRENT.
2. Commit/push exact R50 candidate and require exact-SHA hosted matrix — OPEN.
3. Merge only after hosted PASS; publish v4.3.6 exact R50 + Linux R16 bytes; verify release digests — OPEN.
4. Post-publish Windows read-only updater and Linux updater/install acceptance — OPEN.
5. Broader new-connection-method research starts only after this product release is closed.

### Exact Next Action
Generate PUBLIC_MANIFEST last; pass security/public-tree/fail-closed; freeze commit SHA and require hosted CI before any v4.3.6 promotion.

### R50 Hosted Attempt 1 — Canonical Nested-Manifest Guard
- Exact candidate 0dd73a874ecf4aa37b191c6adaa12bbe8d760c27 reached hosted CI run 37334451018.
- Linux static, console virtual, Windows installer build/fresh path, Android build, iOS static and virtual signing progressed/passed; windows-unit blocked promotion at Verify public manifests.
- Exact root cause: crossplatform/MANIFEST.json entries were generated from raw Windows working-tree bytes. linux/freenet_hub_linux_gtk.py was CRLF locally but LF in fresh checkout, so the nested entry hash failed even though RELEASE used a canonical hash for the manifest file itself.
- Prevention: tests/rebuild_crossplatform_manifest.py now canonicalizes every entry through Git hash-object/cat-file before recording bytes/SHA-256. Nested manifests must use the same canonicalization policy as their verifier.
- Corrected cross-platform manifest canonical SHA-256: 2C39E72AC80A76DE1A597A870412F26070977AB57D82E9E396596E23576250C9.
- RELEASE changed, so the prior 8F4585... installer became superseded. The A4A207... installer was superseded when late control-plane RELEASE fields were stabilized. Final frozen R50 installer is 24,257,042 bytes / SHA-256 E9592F858F166A7946BA8791CA9595B325456AB9BE27FEF07A3FC7E399F30AE1; manifest preflight PASS; Authenticode NotSigned/external.
- Post-fix local regression remains 244/244 PASS. Final E9592F... exact fresh-install/UI smoke PASS; Windows default route stayed 192.168.20.1.
- Exact Next Action: rebuild PUBLIC_MANIFEST last, verify public/security/fail-closed, commit/push corrected exact SHA, require hosted retry PASS before merge/promotion.

## V436 PUBLIC FINAL — 2026-10-05
**Status: CURRENT / PUBLIC_FINAL_REPOSITORY_CLOSED**

### Accepted Authority
- Exact candidate: 4c2658a53dce4aed0c8b6f84b563d60c3b52bbd5; PR #26 hosted run 37336539430: 10/10 SUCCESS.
- Merge/runtime authority: 915b9574aac107c333c298ca35391be097df1200; main run 37337997914: 10/10 SUCCESS.
- Exact tag v4.3.6 points to the same merge commit; tag run 37339712561: 10/10 SUCCESS.
- Candidate and merge Git trees are identical. No merge-time runtime byte drift occurred.

### Public Release / Exact Artifacts
- FreeNetHub_4.3.6_R50_Setup.exe: 24,257,042 bytes; SHA-256 E9592F858F166A7946BA8791CA9595B325456AB9BE27FEF07A3FC7E399F30AE1.
- FreeNetHub_4.2.0_Linux_R16.zip: 225,314 bytes; SHA-256 01F852B1350C591EAD5C03A0F094F92B4861E1D1DA96226A48B9AE691D48C503.
- GitHub release digests and independent re-download SHA-256 values match both frozen artifacts exactly.
- Windows public Authenticode remains NotSigned; trusted signing identity is an external/non-blocking gate.

### Post-Publish Acceptance
- Windows installed updater check: PASS. Installed R45 discovered exact public R50 asset; updateAvailable=true; session, route and DNS hashes unchanged. Owner Windows was not forcibly upgraded.
- Linux real updater: PASS R15->R16 using public release asset/digest. Installed version 4.2.0-linux.16-r43; integrity 9/9 PASS; post-update local=remote revision 16 and updateAvailable=false; route/DNS/disconnected session semantics preserved.
- R50 node-selection correction remains evidence-backed: the former fixed four-candidate sample was a false negative; bounded/adaptive search and full-health-first ranking are the accepted behavior.

### Software DoD
- Local regression/security/public/fresh-install gates: PASS.
- Candidate/main/tag hosted promotion matrices: PASS.
- Exact assets/digests/redownload verification: PASS.
- Windows updater preservation: PASS.
- Linux real updater/install/integrity/preservation: PASS.
- Therefore the desktop software release DoD is closed for v4.3.6 R50/R16.

### External / Deferred
- Trusted Windows Authenticode signing identity.
- Physical console field/game/country E2E.
- Production Android/iOS packet-forwarding core, signing and real-device validation.
- Authorized live TUIC/AnyTLS/ShadowTLS endpoint validation.

### Roadmap ← CURRENT
1. v4.3.6 R50/R16 exact-SHA release — Completed/PASS.
2. Post-publish Windows/Linux updater acceptance — Completed/PASS.
3. Control-only repository closure with zero runtime diff — Completed/PASS; final main CI run 37343449317 SUCCESS on 3cdbd19fc62eaccdef9c0ae7f16cf2073f1c6392.
4. External hardware/signing/mobile-production/live-endpoint tracks — Deferred/External.

### Exact Next Action
No open v4.3.6 software gates. Final main CI run 37343449317 is SUCCESS on control-only closure commit 3cdbd19fc62eaccdef9c0ae7f16cf2073f1c6392; runtime diff versus immutable v4.3.6 is NONE. Preserve the frozen release. Any broader connection-method research starts as a new change set.

## V437 R51 PROTOCOL EXPANSION 2 — 2026-10-05
**Status: CURRENT / PUBLIC_FINAL_REPOSITORY_CLOSED**

### Previous Accepted State
- v4.3.6 R50 / Linux R16 remains immutable and publicly finalized.
- Frozen base for this new change set: b3e58a659c566422d5548546ae4de1bd46b16bfa.
- No v4.3.6 runtime bytes were mutated; R51 lives on branch v4.3.7-r51-protocol-expansion-2.

### Current Delta
- Added Hysteria v1 official share-URI support, restricted to safely representable UDP mode; unsupported legacy transport modes fail closed.
- Added fail-closed sing-box JSON import/config support for SSH, Snell, upstream SOCKS, HTTP CONNECT and Naive.
- Local-path credential/certificate references in imported JSON are rejected to prevent arbitrary local-file reads.
- Public node views continue to redact credentials.
- Hysteria v1 joins Hysteria2/TUIC in the UDP/QUIC preflight class; no false TCP-only rejection.
- Windows Naive prerequisite is repaired from the exact same already-pinned sing-box v1.14.0 official archive. libcronet.dll SHA-256: EEE741046F0A3975124BAE349AEAC237AA306F3CC4DE59FF5DE070E74DBFDAEB.
- Real Cronet repair acceptance: PASS; route, DNS and session hashes preserved; networkMutation=false.

### Runtime Evidence
- Focused node/protocol regression: 19/19 PASS.
- Windows sing-box 1.14.0 generated configs: Hysteria/SSH/Snell/SOCKS/HTTP/Naive = 6/6 check PASS.
- Linux sing-box 1.14.2 same generated configs = 6/6 check PASS.
- Full local regression: 252/252 PASS.
- Public security scan: PASS.
- Linux selftest/parity/update-revision: PASS.
- Linux R17 artifact: FreeNetHub_4.2.0_Linux_R17.zip, 234,341 bytes, SHA-256 1646C70FBF2CA3C7EAAC9D6470BEED3D53063D9E5D9FF50A830D0507420C6EA6.
- Cross-platform manifest canonical SHA-256: 78651558F85B42FBA051D33BB80AD4CA522B9395E0026E40BF6646277F6851BE.
- Final local Windows installer: FreeNetHub_4.3.7_R51_Setup.exe, 24,269,473 bytes, SHA-256 4CCAE665D9F641BEC3FACF2BFDB908F5E727BDC32F278A91EA2E6C3BFE8208A3; manifest preflight PASS; Authenticode NotSigned/external.

### Research Boundary / Exhaustion So Far
- MASQUE and Tailcat are not mixed into R51 because official sing-box support requires 1.15+, while accepted runtimes are Windows 1.14.0 and Linux 1.14.2. They require a separate runtime-upgrade trial.
- OpenVPN/OpenConnect are available in modern sing-box builds but remain outside the locked FreeNet Hub product boundary and belong to OpenInternetGateway.
- WireGuard remains explicitly excluded from this FreeNet Hub line.
- sing-box Tor outbound was not duplicated because FreeNet Hub already has dedicated native Tor/Snowflake/WebTunnel/obfs4 methods.
- Naive is no longer deferred: the missing Windows Cronet dependency was found inside the already-pinned official archive and validated.

### Roadmap ← CURRENT
1. Freeze/verify PUBLIC_MANIFEST on this exact R51 snapshot — Completed/PASS.
2. Commit/push exact candidate and require hosted PR matrix — CURRENT.
3. Merge only after exact-SHA PASS; require main CI — OPEN.
4. Tag/release v4.3.7 + Linux R17 only after promotion gates — OPEN.
5. Post-publish Windows read-only updater + Linux real updater/install acceptance — OPEN.
6. After R51 is closed, perform a second research pass for additional authoritative connection families and runtime-upgrade candidates.

### Exact Next Action
No open v4.3.7 software gates. Final repository-closure CI run 37359029522 is 10/10 SUCCESS on commit 4d2ab2270904b76b261d5c2f75a0f01b50342a57; runtime diff versus immutable v4.3.7 is NONE. Preserve the frozen release. Any R52 work starts as a new change set.


### R51 Public Promotion / Post-Publish Evidence
- Exact candidate e80d406d89bb9539689a5209d86ddb714f1a8539: push CI 37353807006 and PR #27 CI 37353842830 are both 10/10 SUCCESS.
- Merge/runtime authority 07424a87a0dfa2047afcfefeb62a71feb38a906d has an identical Git tree; main CI 37354810434 is 10/10 SUCCESS.
- Exact v4.3.7 tag points to the merge authority; tag CI 37356646618 is 10/10 SUCCESS.
- Public Windows asset: 24,269,473 bytes / SHA-256 4CCAE665D9F641BEC3FACF2BFDB908F5E727BDC32F278A91EA2E6C3BFE8208A3.
- Public Linux R17 asset: 234,341 bytes / SHA-256 1646C70FBF2CA3C7EAAC9D6470BEED3D53063D9E5D9FF50A830D0507420C6EA6.
- GitHub digests and independent re-download hashes match both assets.
- Windows installed R45 updater discovery: PASS for R51; session/route/DNS unchanged; owner Windows was not forcibly upgraded.
- Linux public updater: PASS R16->R17; installed 4.2.0-linux.17-r44; integrity 9/9 PASS; updateAvailable=false; route/DNS/domain/disconnected-session semantics preserved.
- Stable sing-box 1.14 outbound-family coverage is now exhausted for accepted node families, subject to product exclusions. A narrower R52 refinement remains for Shadowsocks SIP002/SIP003 plugin query preservation (obfs-local/v2ray-plugin). Mieru requires a separate runtime/server-authority evaluation. sing-box 1.15 MASQUE/Tailcat are alpha/pre-release and not accepted into this stable release line.
- Final repository closure commit 4d2ab2270904b76b261d5c2f75a0f01b50342a57: main CI run 37359029522 = 10/10 SUCCESS; app/crossplatform/windows runtime diff versus v4.3.7 = NONE.

### Owner Windows + Linux Installed Final Acceptance — 2026-10-06
- Windows canonical install path is now v4.3.7 / R51, upgraded from the prior R45 owner install.
- Windows app manifest 17/17 PASS; gateway manifest 17/17 PASS.
- Windows sing-box 1.14.0 and pinned Cronet runtime are configured; setup preserved route, DNS and session and reported networkMutation=false.
- Windows backend Inventory PASS; all advertised providers are available/not connected. Update check reports localRevision=remoteRevision=51 and updateAvailable=false.
- Windows installed UI smoke PASS: visible=true, 212 controls rendered, UI PNG generated, networkRequested=false, no ui-error.
- The stale fresh-install Temp instance was stopped and removed; Inno uninstall authority now points to the canonical per-user Programs/FreeNetHub path.
- Linux owner install remains 4.2.0-linux.17-r44 / R17; installed integrity 9/9 PASS; update check local=remote=17 and updateAvailable=false.
- Linux package selftest PASS with network_on_import=false; route/DNS/session remained preserved.
- Result: both owner Windows and Linux installations are current and final for immutable v4.3.7.


## Linux R18 browser/NODE hotfix — 2026-10-06 — LOCAL EXACT PACKAGE OWNER ACCEPTED; HOSTED CI OPEN

Previous accepted Linux authority was `4.2.0-linux.17-r44` / `FreeNetHub_4.2.0_Linux_R17.zip` under public release `v4.3.7`.

Current evidence-backed delta:
- CONFIRMED product root cause: Linux `open_browser()` proxied TOR but not NODE even though NODE/sing-box exposes SOCKS5 on `127.0.0.1:19460`. R18 maps NODE to that port, uses remote DNS, persists `proxyPort`, verifies NODE before browser launch, and verifies a real project Firefox process before reporting success.
- CONFIRMED host root cause for the original Firefox launch failure: Ubuntu 24.04 -> 26.04.1 release upgrade required reboot. After owner-controlled reboot the host runs kernel `7.0.0-38-generic`, GDM/user Wayland session is healthy, and standard Ubuntu Snap Firefox launches normally. The temporary native-Mozilla diagnostic workaround was rejected and removed; the original Snap desktop entry was restored.
- Public-node refresh: 8/8 configured sources returned data; 2,876 raw configs parsed; capped pool 2,000; 1,199 TCP endpoints reachable. TCP reachability was not treated as full proxy health.
- Full-health NODE evidence: ID `189bdf109289b55ae495`, VMess / `AURX_HTTP_VERIFIED`, DE; throughput acceptance 447.1 ms / 12.61 Mbps down / 0.66 Mbps up. Final installed acceptance: exit IP `31.76.11.83`, DE, YouTube HTTP 204.
- One transient first `TRACE_FAILED` was observed on an otherwise healthy existing NODE. R18 adds a bounded two-attempt verification guard with 0.5 s delay; regression added. No unbounded retry.
- R18 exact package: `FreeNetHub_4.2.0_Linux_R18.zip`, 240,757 bytes, SHA-256 `3C9254840C85B6D7305B0986209FF96EBEE578193D193538E8E8D45924ECBCD7`.
- Exact extracted package: SHA256SUMS PASS; 7/7 bundled standalone tests PASS. Exact owner install: `4.2.0-linux.18-r45`, installed integrity 9/9 PASS, install network mutation = false.
- Final installed runtime acceptance: NODE connect PASS; `/usr/bin/firefox` -> Ubuntu Snap Firefox PASS with isolated FreeNet Hub profile; browser route records NODE / SOCKS 19460; live SOCKS trace DE / `31.76.11.83`; YouTube HTTP 204.
- CI prevention: Linux hosted job now builds R18 and executes the extracted ZIP tests, closing the package-layout regression that source-tree-only testing missed.
- Windows runtime remains unchanged at public `4.3.7/R51`. Public tag `v4.3.7` is not moved.

Evidence authority: `evidence/V437_LINUX_R18_BROWSER_NODE_HOTFIX_20261006.json`.

Roadmap ← CURRENT:
1. Local source/live acceptance — PASS.
2. Exact R18 package build/extracted-package tests — PASS.
3. Exact owner install/post-install NODE->Snap Firefox validation — PASS.
4. Hosted CI on exact candidate SHA — OPEN.
5. Merge to main only after exact-SHA CI PASS — OPEN.
6. Add R18 asset to existing public `v4.3.7` release and verify updater R18==R18 — OPEN.
7. Post-publish evidence/Brain closure — OPEN.

Exact Next Action: rebuild current manifests, commit/push the candidate branch, run hosted CI on the exact candidate SHA, and promote/upload only if hosted evidence passes.

## 2026-10-09 — Linux Browser Button Defect — CANDIDATE ONLY
- Scope: Linux FreeNet Hub, browser action semantics only; previous public v4.3.7 R18/R51 release and accepted SHA 06d3459 remain authoritative and unchanged.
- Live reproduction: on aliemad-Labtop, installed open_browser() returned CONNECT_FIRST with session.mode=None. Firefox 157 Snap exists, integrity PASS, and an isolated Firefox profile launched and terminated correctly with PID verification.
- Cause: tunneled browser requires active session, GUI offers no explicit normal-browser path, and r37 open_browser returned success without inspecting process launch.
- Candidate branch: fix/linux-browser-explicit-20261009. Changes: explicit unprotected system browser action, clear protected-browser labeling, validated Firefox PID before success, failure display kept after refresh.
- Regression: four new mocked tests PASS, browser-profile test PASS, scope-policy PASS, permissions PASS, parity PASS, update-revision PASS, py_compile PASS, isolated live Firefox launch/cleanup PASS. pytest unavailable on this host; tests executed as standalone functions.
- V&V boundaries: no new Linux release built or published; no Windows runtime mutation; no VPN/system-route mutation. Public upgrade and fresh-install verification pending.
- Status: CANDIDATE/UNPROVEN FOR PUBLIC RELEASE. Exact next action: complete candidate review and hosted CI, then new versioned artifact with install/fresh-upgrade evidence; do not overwrite accepted 4.3.7 asset.

## 2026-10-09 — R19 Browser Fix Candidate — Packaging and Install Evidence
- Previous accepted: public v4.3.7 Linux R18 SHA256 3C9254840C85B6D7305B0986209FF96EBEE578193D193538E8E8D45924ECBCD7, Windows R51 SHA256 8283803146E1625A31F0223487A63C05D7B7D9C3D8B59D1A7432D14AB9D4FF11, main 06d34593766560423608cd97aefd014bf625dcfe.
- Candidate Linux version 4.2.0-linux.19-r46; R19 ZIP 243147 bytes, SHA256 26EF150D7BE890D54EAC5D518F2A0EFDF66CD20E92C3DC659855039D23A344CC; 23 source-controlled files and 23 checksum checks PASS. NOT YET PUBLIC.
- Reproduced CONNECT_FIRST when session.mode=None; patch retains fail-closed protected browser, adds distinct direct/unprotected browser action, verifies live Firefox process and leaves GUI error visible. Native Firefox Snap 157 isolated launch/teardown PASS.
- Regression: 4 new tests, legacy selftest, parity, update revision, browser-profile, scope PASS; public manifest, crossplatform manifest, security PASS.
- Install validation: fresh and R18-to-R19 upgrade installs in isolated HOME PASS using pre-seeded previously verified sing-box and warp-plus pinned runtime binaries. User settings preserved, backup created, no network started. Online bootstrap and real network proxy readiness NOT CLAIMED.
- PR #28 remains draft, candidate only. CI release job scoped to successful push on main after virtual-acceptance; reproduces Linux R19, confirms unchanged Windows R51 SHA and validates public asset digests. Await hosted exact-SHA PR CI, merge, main CI, post-release verification and installed UI acceptance.
- Brain status CURRENT, public FINAL = UNPROVEN.
- R19 package reconstruction after README-only edit: previous candidate ZIP SHA256 26EF150D7BE890D54EAC5D518F2A0EFDF66CD20E92C3DC659855039D23A344CC superseded; authoritative candidate ZIP is 243206 bytes, SHA256 AB95D42A4A9A7AA30CEF5F4B99CC9939436B3A4D3779F3770A04305C27F8FFB7. Runtime Python and shell install sources unchanged by this rebuild.

## 2026-10-09 — Linux R20 CFON smart and independent site checks (candidate)
- Motivation: current Linux Browser AUTO uses Node -> WARP IR -> Tor, skipping demonstrated working CFON AT; trace-only success can misrepresent site reachability.
- Candidate source branch fix/linux-cfon-smart-and-site-diagnostics-20261009 (not public at this point).
- Changes: Browser AUTO tries owned/verified CFON after Node and before WARP, requires independent Google + GitHub/NVIDIA site probes and refuses to promote CFON on trace only; explicit dashboard site-test controls report HTTP statuses for Google/GitHub/NVIDIA/ChatGPT using only owned SOCKS5H local proxy and remote DNS, HTTP403/429 not PASS, no direct fallback.
- Live independent Ubuntu 26.04 result: CFON AT (Google204, GitHub200, NVIDIA200, ChatGPT403 classified restricted/challenge), 8/8 new regression tests PASS, parity and browser profile PASS.
- Linux version candidate 4.2.0-linux.20-r47, package FreeNetHub_4.2.0_Linux_R20.zip, 23 source-controlled files, isolated fresh install and R19 upgrade with pinned runtime binaries PASS, installed source checks 9/9 PASS; no route/network changes on install.
- This patch only improves BROWSER. Full-system global CFON+VPN Gate remains explicitly BLOCKED by unaccepted all-UID live route trial and server privacy/reliability gates. No subscription/server purchase, no implicit volunteer-VPN routing.
- Release progression: update manifests and hosted CI on exact SHA, merge only if CI green, then publish new R20 Linux asset plus byte-exact Windows R51 and verify latest asset SHA. Do not mutate old R19 asset.
- Release blocker discovered before R20 acceptance: existing installer SIGTERMs GTK at install start; GTK cleanup may stop currently active CFON/WARP. R20 now fails before touching state when session.mode is active or session JSON unreadable (error FREENET_HUB_ACTIVE_SESSION / exit72), allowing user to intentionally disconnect before upgrading; CI includes active-session no-mutation regression and unparseable JSON fail-closed tests. No live CFON process touched.

## 2026-10-10 — Reusable Windows public-signing gate — PREPARED, not signed

- Previous accepted public Windows baseline remains R51; R52 source commit `5f99c56e294ff225479ee0a828bd0e6050e13740` remains an unpublished candidate.
- R52 evidence `evidence/V438_R52_STAGED_CANDIDATE_ACCEPTANCE_20261009.json` records unsigned setup 24,260,213 bytes and SHA256 `7214F7AE832539924B58A6750584079DD859DB5CDA53A59A345B5C9DA3D24DD0`, with signing/isolated installation still OPEN. This hash is unsigned pre-sign evidence only.
- One-blocker preparation on PR #36, branch `chore/windows-public-signing-gate-20261010`: `scripts/signing/Test-PublicAuthenticode.ps1` (read-only fail-closed verification), `.github/workflows/windows-signing-gate.yml` (reject unsigned sample; no public signing claim), `docs/CODE_SIGNING_POLICY.md` (legal providers, accepted baseline, ownership/security, staged signing and DoD).
- No signing keys, secrets, vendor files, root network state, Smart App Control, or public release mutated.
- Authoritative independent references collected in `docs/CODE_SIGNING_POLICY.md`. Microsoft Artifact Signing Public Trust unavailable to Iranian individual/organization without independently verified eligible publisher; SignPath Foundation would show Foundation publisher and has stricter OSS eligibility. OV/EV cert issuer and legal eligibility unresolved.
- Root cause: virtual self-signed CI proves signature mechanics only; R52 Inno pipeline lacks production signing, signed inner files require integrity manifest regeneration, and separate signed uninstaller.
- Prevention: CI distinguishes a **negative verification regression** from publicly trusted release signature and never auto-promotes unsigned setup.
- Roadmap ← CURRENT: policy and negative gate PREPARED; hosted PR verification OPEN; publisher legal issuer/identity OPEN; HSM/cloud authorized signing OPEN; signed staging+Inno+uninstaller OPEN; verify/isolated SAC/immutable release OPEN.
- Brain status: CURRENT for code-signing delta, not a claim of FINAL. Exact Next Action: check hosted CI for PR #36, confirm lawful publisher jurisdiction and issuer eligibility, then implement one chosen provider's signer integration in a signed staging tree; never sign tracked raw R52 sources in-place.

