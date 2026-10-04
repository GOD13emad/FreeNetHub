# PROJECT BRAIN — FreeNet Hub

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
