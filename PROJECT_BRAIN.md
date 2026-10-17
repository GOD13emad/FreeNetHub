# PROJECT BRAIN — FreeNet Hub

## CURRENT — 2026-10-17 Private CFON Tailnet egress · Linux R24 / Windows R57 candidate

- Event FNH-TAILNET-CFON-R57-20261017, based on accepted main SHA 79486d44665bb89c62636051d37b2d7c70b9dca4. Owner Windows direct and existing WARP each gave signed-out Google Cloud HTTP403, but via restricted Tailscale private peer relay to existing Linux CFON HTTPS returned HTTP200. New exact Linux source temporary protected user systemd unit bound only to Tailscale IPv4:19551, accepted one online Windows peer and six selected DNS suffixes for HTTPS:443; Windows new exact candidate code verified SOCKS5 peer handshake and signed-out Google Cloud direct403 versus via peer CFON302 (login redirect, NOT account permission proof). The service was stopped and temporary owner records/unit deleted; user Windows R54 WARP19410, Linux installed R21 CFON19414, manual Brave/Stripe/Google PAC19415, browser tabs, default routes and system proxy were not modified. Real owner Tailscale device IPs/names excluded from public test fixtures; synthetic 100.100.42.x used.
- New Linux tailnet_cfon_gateway.py is opt-in only: actual CFON owner PID/EXE/start tick validated by parent; protected systemd requires same-UID exact PID birthtime and 0600 owner record fallback when ProtectSystem and PrivateTmp hide cross-process proc-exe; sandbox features retained. Bound only self Tailnet IP, only explicit online peer IP, allowlisted DNS + SOCKS remote DNS HTTPS443, no direct internet fallback, 16 simultaneous sessions, hard TTL maximum 60 minutes (GUI uses 30); no Tailscale ACL, route, DNS or service auto-enable changes. GTK Settings has peer discovery, explicit start/stop/status; user systemd service ownership and safe installer/uninstaller rollback guards added.
- Windows planned explicit Linux CFON via Tailscale method: read-only Tailscale Linux online peer identity, strict 100.64.0.0/10 address and exact port19551, SOCKS5 health verification; PAC/HTTP CONNECT bridge uses remote only in TAILNET mode, all existing local providers remain loopback only. Windows GUI includes peer discovery/address and per-action apply; no automatic system PAC mutation. Local regression PASS Linux tailnet six, Windows bridge five, Windows selective thirteen, Windows engine/UI seven, Linux R21 upgrade guards including corrupt/active/foreign state. Real cross-device source trial PASS. Account authorization, whole-device UDP/TUN and PAC-fetch fallback are not guaranteed.
- Candidate Linux version 4.2.0-linux.24-r57, distinct 29-file ZIP FreeNetHub_4.2.0_Linux_R24.zip SHA256 D76958F80923BFC1B77E406FE00F4CE96CC83A9A54521415DBBDAE53AFFB1824, 339695 bytes; R21->R24 isolated install with five private fixtures preserved, modified ZIP rejected before mutations exit75, installed SHA verification and one rollback snapshot PASS. Existing published R21 and old CI-preview R23 frozen, owner installed R21/CFON not interrupted. Windows distinct future 4.3.13-r57-tailnet-cfon-selective-routing is source candidate only pending exact-source CI and disposable binary acceptance.
- Next: exact-source app/release/crossplatform/public manifest hashes, native WPF parser, Windows R57 independent staging and hosted CI, PR review and merge only after evidence. User Windows R54 and Linux R21 stay connected until safe maintenance idle window. Official latest R53 and accepted old Linux R21 public assets unchanged; source candidate not FINAL or owner-installed acceptance.

## HISTORICAL — 2026-10-17 Google/403 R23/R56 accepted; field installation open

- Event FNH-GOOGLE-403-SELECTIVE-20261017 (current verified delta): owner screenshot shows Google Cloud Console /apis/credentials 403. Emad Linux signed-out direct GET/HEAD console.cloud.google.com returned 403; owned CFON SOCKS5 127.0.0.1:19414 gave GET200 and HEAD302 login redirect, proving routing improvement only, not account authorization. Existing user GNOME PAC 19415 was updated in place with exact prestate backup brave-only.pre-google.pac; LIVE PAC contains 33 explicitly selected Brave/Stripe/Google suffixes (SHA256 971559BDD712597E45A56D8E32E2BBD7C12E23596E34E322B70A1EC695CAFE15), not 34; R23/R56 SOURCE Google preset has 30 Google suffixes plus 4 Brave/Stripe = 34, with doubleclick.net deliberately not added to the separate active manual PAC. Native GNOME resolver selected Cloud Console, accounts.google.com, googleapis.com, Brave/Stripe SOCKS5 and unrelated Wikipedia DIRECT; CFON route, browser tabs and existing network remained intact. Versioned R23 Linux package 4.2.0-linux.23-r56 ZIP SHA256 AE3E02E791AAE9CE6740A7DF5C9AD08E910E0D18EBAFB37B379C3E003BA28D48 (304356 bytes), isolated R21->R23 data-preserving upgrade and SHA/tamper PASS. Versioned R56 Windows 4.3.12-r56-google-403-selective-routing EXE SHA256 7822A5E771F0A1A9207180D1C710BBFA940B79404121BB0C4F40DE9C5E9FFDC8 (24280090 bytes), disposable same-binary fresh install, WPF launch, R53 upgrade and rollback all PASS. Source PR #76 head f3169edf84949aeb97f6489df10068ec13e444f9 merged as main cd7727ac416ed3a4952959593cf1ad51c255d477; PR CI run 39003018539 and postmerge CI run 39003336940 completed SUCCESS. R56 acceptance run 39003018581 SUCCESS; unsigned artifact ID 12090365032, exact binary SHA verified on Emad Windows without installation. R23 CI artifact ID 12089414117 available. Real Emad Windows headless Edge with throwaway browser profile used exact candidate PAC: 2 PAC fetches, 2 Google Cloud HTTP CONNECTs, 1 additional allowlisted CONNECT, 0 unselected CONNECTs; temporary bridge stopped and HKCU PAC/ProxyEnable stayed unchanged. Existing Windows WARP 19410 still returns signed-out Google Cloud HTTP403 direct AND tunneled, so selected path correctness does not prove destination availability, geo exit, Google account permissions or payment. UI merges Google preset without losing custom suffixes, pastes HTTPS URL as validated hostname only, and HEAD-probes origin signed-out over direct and owned SOCKS; neither detects all HTTP403 responses automatically nor activates user proxy without explicit Apply. Legacy R22/R55 accepted artifacts remain immutable. Neither R23 nor R56 installed on owner hosts; no latest/public release promotion. Evidence: Actions 39003018539, 39003336940, 39003018581; Chromium PAC design https://chromium.googlesource.com/chromium/src/+/main/net/docs/proxy.md.
- Event FNH-SELECTIVE-WINDOWS-SOURCE-20261017 (depends on FNH-R22-SELECTIVE-20261017): Linux R22 PAC/GTK source merged from GitHub PR #74. PR head 721ea1d2814c10033d13d6b7e98d297d4ecd5540 hosted CI 10/10 SUCCESS; main merge 138ebd75beabe5fc3e6271c46a5f8d57c951e9ac hosted postmerge CI completed SUCCESS. Public R53 Windows installer and Linux R21 asset not replaced. Linux owner installed R21 retains active CFON/Brave/Tailscale.
- Owner laptop Linux R22 actual-source engine temporary field trial (no install): under correct XDG_CURRENT_DESKTOP=ubuntu:GNOME, native GProxyResolverGnome selected owned CFON SOCKS5 for account.brave.com, api-dashboard.search.brave.com, checkout.stripe.com, js.stripe.com and DIRECT for Google (5/5). Exact original user GNOME PAC URL/mode and default route restored; source-controlled PAC daemon inactive/disabled; Brave tabs untouched. First contrary result was a test-environment false negative: Remote Commander shell lacked XDG_CURRENT_DESKTOP and chose GLibproxyResolver rather than GNOME. Do not mark installed GTK acceptance.
- Event FNH-R55-SOURCE-MERGE-20261017: Windows scoped PAC/HTTPS-CONNECT source merged via PR #75, exact PR head 75617970645b55a57540ee1ef0d30d6a65246df9 to main merge c4ee10a411fc5c3fa41a878e22903cb87851306f, matching source tree 80e66bf48bdf5852c2c60d52afa4b952b19f9a0a. The Settings Brave+Stripe domain editor/preset/enable/status/disable, Dashboard/Methods shortcut, loopback HTTP PAC to owned HTTPS CONNECT→SOCKS5, HKCU typed AutoConfigURL/ProxyEnable snapshot and restore, owner validation, status/drift protection, independent pre-upgrade guard and uninstall rollback are in source. This is domain-limited HTTPS/PAC-aware routing, not native system TUN, and does not imply installed or public R55.
- Scope-bound tests PASS: 10 Windows PAC policy, lifecycle, tamper and recovery fixtures; 4 loopback HTTP CONNECT/SOCKS bridge fixtures; 5 engine/WPF integration fixtures; 6 native Windows pre-upgrade guard states; Windows native PowerShell syntax/XAML reader and real CONNECT-to-WARP transport. In disposable CI 38979586837 the same exact R55 installer performed fresh 4.3.11 install, real WPF startup, R53→R55 update with private fixture preservation and explicit R55→SHA256-pinned R53 rollback, all PASS, with no system proxy auto-mutation. Owner-host installed R55/real user-browser WinINet PAC acceptance is OPEN. Real Windows source test WARP port 19410 returned Brave HTTP 403 despite TLS transport; do not conflate tunnel connectivity with geo/business-site access.
- Regression history FNH-R55-PREFLIGHT-FIX: initial PR tests exposed mutation of frozen V458 Prepare-Upgrade.ps1 hash, implicit cp1252 read of UTF-8 in Python, and inherited PowerShell LASTEXITCODE=42 from expected denial; accepted helper restored exact SHA 98BD0A564EA8055960D3A5B6C8CB3B5737DA391D88846F7562621B8E8DC1656C, separate Prepare-SelectiveUpgrade.ps1 checks active/foreign state, Python reads UTF-8, and test explicitly exits zero after verified negative fixtures. R55 first disposable run 38979268054 further exposed Node.js cold start timeout 5s on busy Windows runner, now bounded 20s with original assertions unchanged. Exact corrected PR #75 CI 38979586845 completed success; R55 disposable acceptance 38979586837 completed success; no waiver of original functional gates.
- Compatibility and field-proof FNH-R55-HTTP-CONNECT-20261017: Microsoft documents no SOCKS5 in WinINet/WinHTTP while Chromium supports SOCKS5 PAC; thus Windows PAC uses standard PROXY 127.0.0.1:19417 for HTTPS :443 only, with hostname allowlist and SOCKS5 remote DNS through owned provider; excluded destinations DIRECT. The TCP relay has no DIRECT fallback after PAC resolution; PAC-fetch failure in some clients may still go direct and plaintext HTTP selected targets are explicitly unsupported. Verified Linux source bridge TLS via CFON returned Brave HTTP200; Windows owner WARP 19410 returned HTTP403 from Brave though tunnel TLS worked. References: https://learn.microsoft.com/en-us/windows/win32/wininet/wininet-vs-winhttp and https://chromium.googlesource.com/chromium/src/+/main/net/docs/proxy.md. Real owner WinINet PAC/browser and all-device UDP/DNS-leak prevention remain UNPROVEN.
- Current critical path: main cd7727ac416ed3a4952959593cf1ad51c255d477 source CI 39003336940 completed SUCCESS; source and CI-test/artifact gates CLOSED only for their tested scope. R23 Linux ZIP SHA256 AE3E02E791AAE9CE6740A7DF5C9AD08E910E0D18EBAFB37B379C3E003BA28D48 and R56 Windows unsigned EXE SHA256 7822A5E771F0A1A9207180D1C710BBFA940B79404121BB0C4F40DE9C5E9FFDC8 are separately delivered as CI-tested candidates. Owner Emad Windows installed R54, owned WARP SOCKS5 19410 active, HKCU PAC disabled; owner Emad Linux installed R21, CFON 19414 and independent manually owned Google/Brave/Stripe GNOME PAC 19415 active. Current Windows 403 on Google Cloud persists from existing WARP exit; Linux CFON route returns login redirect. Open field gates: install/versioned upgrade on actual hosts at safe idle boundary, GTK/WPF interactive controls and selective apply/disable/rollback on owner devices, suitable Windows egress for Google Cloud, optional signing and official public release decision. Do not stop existing providers, close tabs, mutate authenticated sessions or infer FINAL from CI. Existing public R53/R21 releases and installed sessions remain unchanged.
- Event FNH-R55-OWNER-STAGING-RECEIPT-20261017: docs-only main d67a525211a4a11ced0b68fca4a6fdb9d34ddda9 CI 38980840524 SUCCESS. On owner Windows, independent GitHub checkout of exact R55 source 75617970645b55a57540ee1ef0d30d6a65246df9 staged under %LOCALAPPDATA%/FreeNetHub-R55-Verification; frozen V458 helper, app code SHA checks and source identity verified. Initial locally built unsigned Windows R55 installer SHA256 CF754B50A4552C7DA6CD645BE1A80477F5775CA5F7487B6EDCB754BC611AEF0F was not CI-tested, and was deleted with its disposable source clone/stage after the independently proven CI-tested R55 artifact was downloaded. Local rebuild NEVER installed; user Windows R54 remained untouched. Found and fixed evidence-integrity defect: preparer printed installerBoundCodeHashes=PASS only after writing R55_ISOLATED_BUILD_SOURCE.json so old persisted receipt omitted the field. Revised preparer persists PASS before writing; hosted exact-source CI now asserts persisted field. Existing local historical receipt remains explicitly incomplete, not silently rewritten. Headless Edge with fresh disposable profile on Windows fetched PAC twice and issued two selected-domain HTTPS CONNECT requests via private loopback-to-active SOCKS5 bridge; no unrelated CONNECT requests. Edge page load received HTTP error (Brave geo 403 remains); browser PAC routing PASS but destination success NOT proven. User Edge profile and HKCU proxy settings were untouched; temporary listeners closed. Owner Windows installed R54 SOCKS listener 19410 and Linux R21 CFON 19414 with separate Brave/Stripe PAC remain active; installation requires idle owner sessions.

- Event FNH-R55-EXACT-CI-BINARY-ARTIFACT-20261017: exact-source SHA b6655e581bcae21a714998c89340d59e9fbcfd2a CI run 39000578508 completed SUCCESS. Windows R55 4.3.11 unsigned CI-tested EXE SHA256 6A68904C1DD6A3FADC62D38349B9191843EE4747FBFE77EC7C6516FBEB3FFF49, 24,275,383 bytes, matched fresh install, WPF startup, R53->R55 private-state-preserving upgrade and pinned R53 rollback. Artifact ID 12088474664 (FreeNetHub_4.3.11_R55_SELECTIVE_CI_TESTED_UNSIGNED) includes tested EXE, R55_TESTED_RECEIPT.json, R55_ISOLATED_BUILD_SOURCE.json and SHA256SUMS.txt; persisted source-code receipt installerBoundCodeHashes=PASS verified. Exact binary downloaded and checked on owner Windows under %LOCALAPPDATA%/FreeNetHub-R55-Verification/CI-Tested-R55. The earlier different-SHA local rebuild and scratch clone/stage were removed after verifying CI-tested delivery. Installer is not installed on owner Windows and is not a Latest/public Release; signed=false, user-browser field acceptance OPEN.

- Event FNH-R22-CI-DELIVERY-20261017: exact Linux R22 27-file ZIP SHA256 5FFA0D7FE5CE6971000693185687C0E1870BBBA15484416C1C297BA3902869EE, 292,327 bytes, matched isolated R21->R22 upgrade with 5/5 private fixtures preserved, corruption denial exit75, manifest/checksum PASS and no external network changes. SHA-pinned GitHub main CI run 39000686983 linux-static PASS and artifact upload completed: ID 12088891791 named FreeNetHub_4.2.0_Linux_R22_CI_TESTED_UNSIGNED, containing exact ZIP and R22_SHA256SUMS.txt. Local owner Emad Linux ZIP has identical SHA. Artifact is preview delivery, not official Latest release, and not installed while CFON 19414 is active; GTK field acceptance OPEN.

- Event FNH-R55-ISOLATED-WINDOWS-20261017 (supersedes planning status): exact PR source SHA 75617970645b55a57540ee1ef0d30d6a65246df9 produced distinct unsigned/private Windows 4.3.11-r55-selective-domain-routing artifact in disposable GitHub run 38979586837. CI tested binary SHA-256 055538F1CFC0DB3D9E124B6D7E6A3F2024D1CFA12C5DBE9184C9D36E6BF38DDD across fresh install, real UI smoke, R53 upgrade and R53 rollback with app integrity verified. Test receipt artifact ID 12080492894 is archived, binary intentionally NOT published; status SOURCE+DISPOSABLE-CI PASS, OWNER-INSTALLED/PUBLIC FINAL not claimed. The reproducible isolate uses tests/prepare_r55_selective_candidate.py and tests/test_windows_r55_isolated.ps1; source AppId is preserved and frozen V458 helper pinned. Earlier local preflight on source e7e3ece passed; GitHub source head supersedes it.

## HISTORICAL — 2026-10-17 R22 initial candidate (pre-merge)

- Event FNH-R22-SELECTIVE-20261017, accepted source baseline main 406447b8ca7793064b15dab8cf4420bed4a4684d; candidate branch feat/selective-domain-routing. Public Windows R53 and Linux R21 are unchanged and frozen.
- Owner goal: fourth FreeNetHub scope «تونل انتخابی»: edit domain list, choose healthy local method, apply, inspect, disable, exact user GNOME proxy rollback. Defaults Brave and Stripe hostname suffixes. Selected domains use owned SOCKS5, all other domains DIRECT; selected domains never PAC-fallback DIRECT. This is GNOME/PAC-aware app routing, not full host TCP/UDP/TUN or per-process enforcement.
- Linux source version 4.2.0-linux.22-r55 and separate unpublished R22 package. GTK Dashboard/Methods/Settings domain editor, Brave+Stripe preset and activation controls; validated helper, loopback PAC HTTP user service, strict ownership, bounded domain parsing, local SOCKS health test and content-hash versioned PAC URL to defeat observed GNOME compiled-PAC stale cache. Installer refuses active CFON/selective scopes before mutation (exit 72), integrity/preflight and uninstall rollback extended.
- Local verification: seven focused PAC/security/recovery cases PASS; scoped provider integration, prior browser, system, console, WARP consent, node and version/update regressions PASS. Isolated R21->R22 upgrade PASS: five private-file samples retained, tamper denied before mutation with exit75, single installed root and checksum verified. Exact R22 27-file local ZIP SHA256 5ffa0d7fe5ce6971000693185687c0e1870bbba15484416c1c297ba3902869ee; prior published R21 SHA256 82305e1a15684662b7711b53a84522122c6a11d618366314d9dd297b3a7fec1a retained.
- Owner field evidence remains Linux R21 CFON SOCKS5 port 19414 healthy, browser/tabs active. Existing separate live PAC: direct Brave geo-403 vs scoped SOCKS HTTP200. After adding Stripe rules and cache-busting PAC URL, GNOME resolver routes checkout.stripe.com and js.stripe.com via port 19414, Google DIRECT. Actual browser payment/Stripe checkout success is UNPROVEN; no login/payment performed, no tabs or external network routes stopped. R22 must not adopt an unrelated previous PAC without explicit restoration boundary.
- Gates OPEN: exact-source hosted CI, code review/promote, R22 owner installed GTK/browser acceptance after safe idle CFON boundary, Windows selective-scope parity. Existing Linux full-device WARP ToS/sudo and Windows elevated gateway/mobile real-device gates are unrelated, remain OPEN/EXTERNAL. Strict FINAL is UNPROVEN.
- Next: seal candidate SHA, run hosted CI, keep public R21 immutable, avoid replacing active owner host connection. Release/install only on verified evidence and safe idle, without terminating browser, Tailscale or other sessions.

## Previous accepted R21 field milestone (historical; superseded for current R22 candidate)

Status: CURRENT / OWNER_WINDOWS_R53_AND_LINUX_R21_FIELD_PASS / STRICT_SYSTEM_AND_MOBILE_EXTERNAL_OPEN
Brain version: v442-linux-r21-public-field-acceptance-2026-10-14
Accepted source main and Fork: bb3237472ced37572934f500c17bd83aaad952e3 (before this docs-only milestone).
Official Latest Release: v4.3.9-r53-windows-stable, with one current Windows R53 installer and current Linux R21 package. Earlier Linux R20 kept unchanged for rollback.

## Previous accepted state → current delta
- PR48 candidate SHA a9d7c9d32928278c1c06b8e4187fadd3554c9b43 exact hosted CI 10/10 PASS, new versioned Linux R21 package. Source merged to bb3237472ced37572934f500c17bd83aaad952e3 and same SHA fast-forwarded to fork, Windows and Linux code worktrees.
- **PHYSICAL owner Linux upgrade R20→R21 4.2.0-linux.21-r54 completed**; INSTALL.sha256 PASS, 4/4 sampled private settings and bridge hashes unchanged, correct GTK program process running, CFON SOCKS5 HTTPS200, Tailscale Running Online, Seman L2TP maintained, LAN default route unchanged.
- Authoritative quiescent private full-copy R20 rollback snapshot kept (~238MB) and source file hashes PASS; destructive restoration NOT performed. The old Linux R20 public asset stayed unchanged (SHA 5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B).
- New Linux R21 ZIP SHA 82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A reproducible on Linux and Windows, GitHub public digest identical, separately downloaded ZIP valid. R20 updater sees remote R21 newer; R21 updater sees no update; Windows R53 updater still sees no newer Windows installer.
- GitHub official release body updated with current R21 note. Fork postmerge CI 10/10 PASS, CodeQL analysis 3/3 PASS. Canonical main postmerge CI status pending when this record was prepared.
- WARP Terms not accepted automatically. SYSTEM WARP on Linux still requires owner-native ToS review and authorized sudo for route and DNS trial. Windows elevated Gateway and mobile real hardware likewise remain unproven.
- Three owner-runner harness faults are documented with root cause, prevention and repaired physical outcomes in evidence/V442_LINUX_R21_PUBLIC_FIELD_ACCEPTANCE_20261014.json. After repeated harness faults, we stopped rerunning the same transaction and restored CFON manually via exact installed API. Never claim the private runner itself passed; the **independent post-recovery physical checks passed**.
- All substantive evidence/reference/reuse targets are in the current V442 record; private backups/raw logs are EXTERNAL under .git/maintenance/FNH_R21_OWNER_20261014, never committed.

## Roadmap to FINAL
1. Official Windows R53 installation, one canonical uninstall, owner field WPF CFON and updater — COMPLETED PASS.
2. Versioned Linux R21 ToS-safe package, immutable public artifact digest, actual field in-place upgrade/data preservation, GTK and scoped CFON — COMPLETED PASS.
3. PR candidate exact CI and postmerge Fork CI — COMPLETED PASS; canonical main postmerge pending when this header was authored.
4. Linux SYSTEM route/DNS/WARP physical leak-free with owner native consent, sudo, reversible Tailscale+L2TP coexistence — EXTERNAL/UNPROVEN.
5. Windows privileged Gateway PC/console end-to-end with UDP backend and Tailscale-safe rollback — EXTERNAL/UNPROVEN.
6. Android/iOS physical-device deployment and production signing/provider gates — EXTERNAL/UNPROVEN. Simulator CI does not validate hardware.

## Exact Next Action
Confirm pending canonical postmerge CI. If software gates remain passed, refrain from arbitrary new mutations. Systemwide and physical final require native OS owner approvals and actual devices, not a product/source fix. Keep R20 private rollback snapshot until explicit restore validation and preservation policy.

---
## Previous cumulative Project Brain (verbatim)

# PROJECT BRAIN — FreeNet Hub

Status: CANDIDATE / LINUX_R21_VERSIONED_UPGRADE_LOCAL_PASS / NOT YET INSTALLED OR RELEASED
Brain version: v441-linux-r21-owner-consent-2026-10-14
Accepted source authority: d0389613f753cddbc90d06e48b790f7672c3b52a; main and Fork exact SHA CI 10/10 each.
Accepted PUBLIC binaries: Windows R53 / Linux R20; hashes frozen and immutable.

## Current change set — one blocker
- V440 Linux WARP native Terms-of-Service owner-consent source fix merged, but R20 installed source still old. Qualify **new named** Linux R21 4.2.0-linux.21-r54 rather than silently patching the previous R20 ZIP.
- New R21 package builder and source revisions; R21 installer checks full package SHA256SUMS before any file or UI mutations, retains R20 active-session guard and existing settings/data, and secures private INSTALL.json to 0600.
- Isolated HOME R20->R21 true installer execution PASS with 5/5 representative private files unchanged and only one installed app root. Tampered R21 package rejected with exit 75 before backup or mutation, and built package SHA verified.
- Local source static/parity/update revision tests PASS. Exact SHA hosted CI, owner physical install and public release asset are OPEN. No user/host network mutation yet.
- Sources and detailed parameters: evidence/V441_LINUX_R21_VERSIONED_OWNER_CONSENT_20261014.json.
- Current owner Linux R20 CFON + Tailscale + Seman L2TP running. Windows R53 CFON still healthy; do not disturb.

## Roadmap to final
1. Windows R53 accepted field, old Linux R20 scoped, main/Fork source CI: PASS.
2. Versioned Linux R21 packaged and rollback/preflight validation: local PASS, exact CI OPEN.
3. Owner in-place update preserving data, bounded downtime, independent Tailscale/L2TP validation, new app field smoke and update check: OPEN.
4. New Linux asset attached to official GitHub release with verified digest; updater R20->R21 discovery: OPEN.
5. Owner-native Cloudflare WARP legal acceptance and sudo/UAC full-system traffic/DNS routing and rollback: EXTERNAL UNPROVEN.
6. Android/iOS physical-device and Windows elevated console gateway: EXTERNAL UNPROVEN.

## Exact Next Action
Complete R21 full-source/manifest CI and candidate build, then guarded field install with prestate/backup and post-check. Do not claim source tests represent installed success; do not auto-accept WARP ToS or modify overlapping Tailscale/L2TP system routing.

---
## Previous cumulative accepted Project Brain — verbatim

# PROJECT BRAIN — FreeNet Hub

Status: CANDIDATE / WARP_TOS_OWNER_CONSENT_FAIL_CLOSED (NOT YET RELEASED)
Brain version: v440-linux-warp-tos-owner-consent-candidate-2026-10-14
Accepted baseline main: d6dc7b27152d8bc2df6b489e17c93614f314368b
Frozen published release: Windows R53 + Linux R20. Public installer bytes and installed copies unchanged.

## CURRENT change set
- Source had the Cloudflare WARP --accept-tos flag even in status and recovery paths; Cloudflare documents this as accepting legal terms.
- Owner Linux warp-cli status without this flag requests ToS acceptance; no owner agreement was entered.
- Candidate: remove --accept-tos from Linux app, recovery, guard, install-version; add owner-consent fail-closed error before any WARP registration/route mutation.
- Added simulated read-only ToS negative regression and hooked Linux hosted CI.
- Accepted Windows R53 owner physical 15/15, source/main/fork hosted CI 10/10, Linux R20 scoped CFON and dual-host Tailscale unchanged. Linux L2TP Seman continues.
- Source candidate is not installed, not yet merged, not released. Full-system routing, DNS leak-free, PC gateway and hardware mobile remain UNPROVEN.
- Release-integrity downstream guard: hosted CI must download publicly published Linux R20, verify SHA-256 5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B and package-manifest sample. Never rebuild a patched source under frozen R20 filename; new source candidate remains distinct from installed/public artifact.
- Evidence detail: evidence/V440_LINUX_WARP_TOS_OWNER_CONSENT_20261014.json.

## Roadmap to strict FINAL
1. Frozen official release and accepted physical Windows owner R53 and scoped Linux R20: PASS.
2. Consent-safe Linux WARP source behavior: local tests PASS; exact SHA hosted CI OPEN.
3. Qualified versioned Linux update/build/install with profile preservation: OPEN if source fix promoted.
4. Owner native WARP ToS approval, OS administrative authentication and reversible full-device Tailscale/L2TP/DNS trial: EXTERNAL OPEN.
5. Windows elevated PC/console gateway and mobile physical device tests: EXTERNAL OPEN.

## Exact Next Action
Run exact SHA hosted CI; do not auto-promote source edit as production app until versioned install/rollback proof. For actual SYSTEM WARP, owner must accept terms natively and approve sudo; do not bypass OS prompts or change routes until recovery proven.

---
## Previous accepted cumulative Project Brain (verbatim)

# PROJECT BRAIN — FreeNet Hub

Status: CURRENT / OWNER_WINDOWS_R53_PHYSICAL_PASS_LINUX_R20_SCOPED_PASS_EXTERNAL_GATES_OPEN
Brain version: v439-r53-owner-physical-acceptance-2026-10-14
Authoritative source: GOD13emad/FreeNetHub main 243b2a3085889f9abc5dadd7e4e456aa6254a986 (before this docs-only record).
Frozen published release: v4.3.9-r53-windows-stable (one Windows R53 installer + Linux R20 ZIP). Do not change published binaries.

## Current accepted evidence delta
- Hosted postmerge exact-SHA canonical CI 38543447337 **10/10 PASS**; fork 38543700692 **10/10 PASS**; same accepted code SHA. Release and runtime executable artifacts unchanged.
- Windows owner R51 -> official SHA-pinned R53 **PHYSICAL UPGRADE PASS**: baseline two-root data and HKCU uninstall log escrow, app-owned NODE/CFON gracefully disconnected, offline copy 11/11 selected critical hashes, exact Inno AppId location reconciliation, R53 Setup.exe exit 0. Installed RELEASE version 4.3.9, Runtime status PASS, only one registered active Inno uninstall entry at canonical path.
- WPF GUI physically launched with a real window handle; R53 engine CFON Connect exit 0, healthy/connected, country AT; SOCKS5 HTTPS 200. UpdateCheck exit 0, latest public R53, updateAvailable false. Tailscale Running Online and direct HTTPS remained available throughout maintenance.
- Distinct original and temporary Chromium profiles preserved as Browser_Primary and Browser_Temp_R51 within canonical R53 data; six initial critical secondary-profile hashes matched, copied SQLite/JSON 14/14 PASS and final quiescent sample 11/11 PASS. Real secondary Chrome Headless about:blank returned code 0 and valid DOM without changing primary selector.
- Old TEMP R51 root moved to PRIVATE rollback archive (not deleted, not a registered/active installation), verified four archival sample hashes. Public repo contains NO private user profiles or registry backups.
- Two failed audit probes retained as superseded: PowerShell GUI Chrome attempt produced null native exit, corrected with bounded subprocess; install-count audit regex excluded actual display name, corrected to optional-space pattern and 15/15 physical Windows acceptance PASS. Neither false-negative was an application regression.
- Public knowledge and references: evidence/V439_R53_OWNER_PHYSICAL_ACCEPTANCE_20261014.json. Raw private rollback receipts: Windows project .git/maintenance/R53_OWNER_20261014_PRESTATE (EXTERNAL/PRIVATE, not transferred).

## Remaining road to strict FINAL
1. Public R53/R20 frozen release, exact SHA hosted CI and official mirrored source — COMPLETED/PASS.
2. Windows owner physical R53 installation, one active registration, WPF GUI, CFON, update, dual browser profile preservation, direct/Tailscale regression — COMPLETED/PASS, verified on owner machine.
3. Linux R20 installed SHA integrity, GTK process and scoped CFON SOCKS5 with Tailscale — COMPLETED/PASS.
4. Linux full-device WARP routing, DNS leak-free and Tailscale-safe rollback physical validation — OPEN/UNPROVEN; sudo unavailable. Never force system route changes without privilege and recovery.
5. Windows elevated PC/console gateway physical validation — OPEN/UNPROVEN; gateway status is not running, current Windows session not elevated.
6. Android/iOS hardware deployment, physical forwarding, production-signing/provider gates — EXTERNAL/UNPROVEN; hosted emulator PASS does not satisfy device acceptance.

## Exact Next Action
Preserve accepted Windows owner R53 baseline and active CFON. Acquire explicitly authorized elevated capability with independently reversible route/DNS guards for full-system/console scopes only if included in strict final DoD, then conduct physical acceptance on the required real devices. Do not create new release versions or patch binaries absent a reproduced defect. Keep private old R51 recovery archives until restore acceptance and cleanup policy is confirmed.

---
## Previous accepted cumulative Brain — preserved verbatim

# PROJECT BRAIN — FreeNet Hub

Status: CURRENT / R53_PUBLIC_RELEASE_AND_CI_PASS; OWNER_OFFLINE_UPGRADE_BLOCKED
Brain version: v439-r53-owner-precopy-readiness-2026-10-14
Accepted source SHA: 9d0fde42d2a7da85056bbc2666074057e370c5bb
Accepted public release: v4.3.9-r53-windows-stable (Windows R53 installer + Linux R20 ZIP, frozen bytes)

## Current delta — evidence after previous accepted Brain
- Main and fork postmerge hosted CI on accepted SHA: each 10/10 PASS. Both local source repositories clean. Public release assets unchanged.
- Windows owner currently R51. Canonical and TEMP same-AppId roots both exist. HKCU uninstall registration points to TEMP; three active app/gateway/helper processes span both roots. Do not force installer or registry overwrite.
- Private recovery staging: canonical pre-copy Robocopy exit 1, 25,460 files / 7,060,381,711 bytes. TEMP pre-copy initial exit 9 due solely to active runtime jobs/ui.lock; narrowly repeated with this one lock excluded and exit 1. No source files deleted.
- Distinct Chromium profile data preserved in BOTH private staged roots. 6/6 critical source/destination file hashes agree in each; no recent writes in ten-minute observation; 14/14 copied SQLite quick-check and JSON validations PASS. This does NOT prove app-consistent restore, complete user-state preservation or valid profile merge.
- Official local R53 installer SHA equals frozen public digest 34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2. Guarded offline-upgrade preflight: source/install/staged copy tests PASS, OWNER_OFFLINE_UPGRADE_READY=FALSE because three processes still active, registry split and rollback not tested.
- Linux R20 installed integrity + full-system scope-policy regression PASS. Scoped SOCKS5 HTTPS 200; Tailscale running and online. WARP-only full-system path is known from code; no privileged route change, DNS leak-free or Tailscale coexistence validation. No install or network mutation.
- Detailed source/method/rationale: evidence/V439_R53_OWNER_PRECOPY_READINESS_20261014.json. Private live-profile backups and audit scripts reside under Windows project .git/maintenance and are EXTERNAL/PRIVATE, not in GitHub.

## Roadmap to FINAL (proportional gates)
1. Official frozen release, exact-SHA CI, mirror repository, Windows and Linux source audits — COMPLETED/PASS.
2. Owner Windows two-root structural backup and basic database integrity — STAGED/PASS (not app-consistent).
3. Controlled owner idle recovery: preserve access to BOTH profiles, finalize delta copy, test rollback, reconcile same AppId and upgrade physical R51 to R53 — BLOCKED / CRITICAL PATH.
4. Linux installed local proxy and coexistence with active Tailscale — COMPLETED/PASS at browser/proxy scope.
5. Linux WARP full-device/DNS leak-free validation — OPEN/UNPROVEN, root access and rollback prerequisite; do not force a route while connected.
6. Real mobile/console forwarding and production-signing/provider dependencies — EXTERNAL/UNPROVEN; hosted simulator PASS is not real hardware.

## Exact Next Action
Maintain active connections. Once owner application is idle with independently recoverable remote access, finalize OFFLINE backup of both distinct Chromium roots, test restoration, then reconcile Inno AppId and upgrade using the frozen R53 installer. Fail closed and preserve R51 if any invariant fails. Continue scoped Linux tests without route mutation.

---
## Previous accepted cumulative Brain — preserved verbatim

# PROJECT BRAIN — FreeNet Hub

Status: CURRENT / R53_PUBLIC_RELEASE_PASS_OWNER_FIELD_GATES_OPEN
Brain version: v439-r53-postmerge-field-verified-2026-10-14
Accepted source baseline: GOD13emad/FreeNetHub main 5c824fc3d800f850edad64d7bf2e0df90294a466; Latest runtime release v4.3.9-r53-windows-stable, peeled tag 17daff34805b82bcae0c6e8d5e6cbed6258c50ff.
Objective / DoD: one official current Windows installer plus Linux R20 distribution, verifiable public GitHub hashes and hosted CI, safe upgrade preserving user data, working browser proxy, optional full-device tunnel only when validated, and physical host acceptance evidence.

## CURRENT — R53 2026-10-14 field and release audit
- GitHub Latest release is PUBLIC/CONFIRMED with Windows R53 SHA-256 34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2 and Linux R20 SHA-256 5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B; exactly two assets.
- PR #42 hosted CI run 38523926557: 10/10 SUCCESS. Merged main exact SHA ec2ce34 postmerge CI 38525037084: 10/10 SUCCESS. Windows local R53 identity and 13/13 installer/lifecycle tests PASS. No runtime code changed by docs PR #42.
- Windows owner currently on **R51**, not R53. Canonical installed tree and active TEMP R51 with SAME Inno AppId conflict; uninstall registry points to TEMP. ACTIVE connection; 7.06GB canonical + 1.07GB TEMP dynamic tree. R53 guard correctly refuses split-root; physical R53 upgrade is BLOCKED pending idle consistent backup and controlled rollback. No unsafe auto-fix or install.
- Linux installed R20 manifest SHA-256 checks PASS; CFON SOCKS5 endpoint 127.0.0.1:19414 reaches Cloudflare HTTPS and GitHub API (HTTP 200). Incorrect HTTP-proxy probe produced false negative; no product mutation needed. System default route and DNS still via wlp2s0/192.168.20.1; systemwide DNS-leak-free and optional full-tunnel remain UNPROVEN.
- External: mobile hardware forwarding/console, production signing, real owner installed R53, full-system DNS routing, and interactive browser acceptance remain OPEN or EXTERNAL. Do not relabel virtual CI as physical validation.
- Mirror Usefull-Skills/FreeNetHub main was safely fast-forwarded to source baseline 5c824fc; its exact-SHA hosted push CI 38534293426: 10/10 PASS. Canonical postmerge CI 38534184216: initial Android emulator ADB offline after VPN consent acceptance; one targeted retry of failed Job succeeded; latest attempt 10/10 PASS. See new evidence record; initial failed attempt remains historical, not erased.
- Evidence: evidence/V439_R53_LIVE_HOST_AUDIT_20261014.json with live results, sources, previous-brain SHA and backup.

- 2026-10-14 live field extension: Windows installed R51 canonical and TEMP user sessions remain active; official immutable Windows R53 Setup.exe in local delivery has SHA-256 matching public release. Both Windows and Linux Cloudflare trace direct egress reported IR, and SOCKS5 through existing CFON 127.0.0.1:19414 reported AT with a different IP. This verifies scoped proxy routing, NOT full-device tunneling. Windows private backup of eight installation metadata files plus exact HKCU Inno uninstall registry export was independently SHA-256 verified; USER DATA (~8 GB across roots) was not snapshotted and actual owner R53 upgrade remains BLOCKED.
- Evidence: evidence/V439_R53_POSTMERGE_FIELD_VERIFICATION_20261014.json records hosted attempts, root cause, sources, private escrow boundary and open gates. First Android CI failure was ephemeral ADB-offline on hosted emulator (after UI permission flow), second attempt PASS on same SHA; fork independent emulator PASS. No product-code mutation justified by this one failure.

## Roadmap to FINAL (evidence gated)
1. Source and public exact release/CI — COMPLETED/PASS for v4.3.9 R53.
2. Windows source installer isolation, rollback and preserving profile — COMPLETED/PASS in hosted isolated CI, not owner host.
3. Linux R20 installed integrity and localhost CFON SOCKS5 — COMPLETED/PASS on owner Linux; no full-system claim.
4. Owner Windows R51 split-root reconciliation after consistent backup/idle, then R53 in-place installed validation — BLOCKED/critical path.
5. Linux optional full-tunnel/DNS physical acceptance without breaking Tailscale or owner connectivity — OPEN; do not force-route blindly.
6. Physical console/mobile/browser and signing/provider-dependent steps — EXTERNAL/UNPROVEN, report individually.
7. Public R53 release, canonical and mirror CI, and latest source synchronization — COMPLETED/PASS; owner physical acceptance and external capabilities remain separately OPEN.

## Exact Next Action
Keep connected sessions intact. Private Windows prestate static metadata escrow (both uninstall logs/installer metadata plus registry) is verified but is NOT a consistent backup of live user data. Next, acquire a consistent recoverable backup of BOTH data trees and an idle maintenance state before any split-root reconciliation and R53 installed upgrade. The Linux full-device route/DNS gate still requires separate privileged, leak-safe field validation; scoped SOCKS5 egress is PASS on Windows and Linux. Do not blindly force route, delete either tree, or replay failed CI attempts.

---
## PREVIOUS HISTORICAL BRAIN — retained verbatim after this heading

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

## 2026-10-14 — V443: R53/R21 exact-CI and installed-state checkpoint

**Status:** CURRENT / CI_AND_SCOPED_FIELD_PASS; strict full-device and mobile physical FINAL remain UNPROVEN.

**Previous accepted state:** public v4.3.9-r53-windows-stable, GitHub main `e542d0d8891a566a14ddb356bb52a730fea41dac`; owner Windows 4.3.9/R53, owner Linux 4.2.0-linux.21-r54; field evidence V442.

**Current delta (read-only audit):**
- Exact GitHub main run `38562076539`: 10/10 SUCCESS; previously pending main run `38559614207`: 10/10 SUCCESS.
- Latest public Windows R53 installer SHA256 `34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2`; Linux R21 asset SHA256 `82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A` matches local archive; frozen prior Linux R20 SHA unchanged.
- Installed Linux R21 integrity 9/9 PASS; install active-session protection 2/2 PASS. Real owner CFON SOCKS5H traffic: Google HTTPS204 and GitHub HEAD200. Tailscale Running, two peers; Linux default Wi-Fi route unchanged.
- Installed canonical Windows R53 release identity and active app process verified. Tailscale Running, default Ethernet route unchanged. Windows shell not elevated.
- Linux native WARP client requests owner Terms acceptance; noninteractive sudo unavailable. No claim of systemwide all-UID routing, DNS leak protection or destructive rollback restore.

**Verification versus validation:** Hosted CI verifies software matrix; real owner installs and proxied HTTP establish limited field validation. Mobile CI simulators do not establish actual-device acceptance. No privileged VPN or system networking changes were executed during this audit.

**Roadmap / gates:** (1) Release asset authenticity and SHA-bound main CI: PASS. (2) Windows R53 and Linux R21 installed/scoped browsing: PASS in evidenced scope. (3) Linux full-system WARP, native owner ToS, sudo, route/DNS/Tailscale/L2TP recovery: OPEN/OWNER EXTERNAL. (4) Windows elevated system/console gateway: OPEN/PRIVILEGE. (5) Android/iOS physical testing: OPEN/EXTERNAL. (6) Real restore of private rollback snapshot: UNPROVEN. (7) This V443 documentation-only evidence closure: CURRENT until exact-SHA PR CI/merge.

**Authority:** `evidence/V443_R21_R53_POSTPUBLISH_VERIFICATION_20261014.json` (new) + `evidence/V442_LINUX_R21_PUBLIC_FIELD_ACCEPTANCE_20261014.json` (accepted). Official method sources: Cloudflare WARP Linux setup, Tailscale coexistence docs, GitHub Actions API.

**Failure prevention / decision:** Preserve running CFON, Tailscale, L2TP, routes, DNS and immutable public packages. Do not silently accept third-party ToS or create systemwide route mutations while recovery/privilege conditions remain unsatisfied.

**Exact next action:** Commit and run exact-SHA CI for this evidence-only checkpoint. For strict full-device FINAL, owner-approved native ToS and authenticated sudo/UAC maintenance plus rollback-safe physical trials are required.

**V443 CI failure and prevention (same change set):** PR #50 initial exact-head run `38564523659` failed `windows-unit` at `Verify public manifests`; raw logs identify only `PROJECT_BRAIN.md` and new V443 evidence as `publicManifestBad`. This is publication metadata drift, not a demonstrated Windows runtime defect. Root cause: missing PUBLIC_MANIFEST regeneration after documentation change. Guard: run deterministic `tests/rebuild_public_manifest.py` and `tests/verify_public_tree.py` before commit; do not re-run the failed SHA blindly. Candidate remedy is scoped to PUBLIC_MANIFEST plus this evidence/Brain delta. New exact-SHA CI remains OPEN until independently observed.

## 2026-10-14 — V444 mobile forwarding truth and benchmark-first architecture gate

**Status:** CURRENT / MOBILE_CORE_MISSING_CONFIRMED; source runtime unchanged; V444 evidence-only candidate.

**Accepted base:** GitHub main `4b072d31531665d69d012b8183b52f85365eacd2`, after PR #50 merge of SHA `753a98f7b800cd7ecb1ebfd01aa6d4ac6a522958` (exact-head PR CI `38564918204` 10/10 PASS). Post-merge main CI `38567225963` in progress at initial V444 observation, do not infer PASS.

**Authoritative facts:** Android `FreeNetVpnService.kt` reports `providerCoreReady() = false` and omits `Builder.establish()`; iOS `PacketTunnelProvider.swift` returns `coreNotLinked` and does not forward packets. These are intentionally fail-closed prototypes, not operational VPNs despite emulated build/runtime PASS. A real Android 13 owner device is detected by read-only ADB; FreeNet Hub itself is absent; unrelated VPN test apps are preserved. No physical app installation, Android VPN permission change or routing mutation was made. `THIRD_PARTY_NOTICES.md` confirms no project-wide source license declaration.

**Method and comparative evidence:** Android official VpnService lifecycle requires upstream socket protection, configured TUN and real forwarding; Apple official NEPacketTunnelProvider requires entitlement, interface settings and packetFlow implementation. SagerNet SFA/SFI offer comparable functional sing-box TUN integration; assess pinned/reproducible libbox/library reuse rather than inventing a new forwarding stack. Compare ABI, lifecycle, upstream compatibility, license terms (including GPL-3.0), and real-device behavior before any implementation/redistribution. Tailscale documentation confirms one active VPN per mobile OS; never displace another app implicitly.

**Decision:** MOBILE CORE INTEGRATION = PROPOSAL, NOT ACCEPTED / NOT IMPLEMENTED. Reject false completion from debug APK and emulator PASS. Minimum sufficient controls when implementing: pinned binary SHA and license, fail-closed start/stop, non-looping protected upstream, IP/DNS/UDP integrity and no leak, real device exit/connection/reconnect, rollback and installation/update; iOS entitlement/provisioning and physical device separately. Additional gates require measured benefit. Desktop owner releases remain frozen.

**Roadmap:** (1) Desktop R53/R21 scoped install/browser — ACCEPTED (V443); (2) Mobile source gap audit and comparable method evidence — COMPLETED/PASS; (3) Android real forwarding + device test — OPEN; (4) iOS real forwarding + entitled physical validation — OPEN; (5) Third-party license and signing/owner authority — OPEN; (6) Windows/Linux strict global tunnel owner elevated gates — OPEN; (7) Cross-device FINAL — UNPROVEN. Verification is distinct from validation.

**Evidence:** `evidence/V444_MOBILE_FORWARDING_GAP_BENCHMARK_20261014.json`; official Android/Apple VPN documentation, official sing-box platform feature docs and Tailscale other-VPN compatibility. No mobile/network mutations made.

**Exact next action:** Promote this V444 knowledge-only candidate after exact-SHA CI. Begin a separate mobile forwarding implementation only after a license/core pin decision and a reversible test harness preserving other device VPNs.

### V444A corrective delta — Android unlinked VPN permission guard (2026-10-14)

**Previous V444 candidate status superseded:** the initial knowledge-only mobile review identified a user-visible VPN permission request in `MainActivity.kt` despite `providerCoreReady() == false`. Official Android `VpnService.prepare` documentation confirms authorization is exclusive and approving another application revokes the previous VPN right. This is a real disruption risk to other user-installed VPNs even without any FreeNet Hub TUN.

**ONE mutation objective:** stop the nonfunctional Android application from requesting VPN ownership. Android UI now exposes an explicitly disabled control; no `VpnService.prepare` call remains reachable in `MainActivity.kt`. Emulator CI now asserts the visible control is disabled, no misleading permission action is exposed, no FreeNet Hub VPN service starts and interface inventory remains unchanged. No host/device deployment or active user VPN change occurred. Windows, Linux, iOS runtime and accepted public release assets are untouched.

**Root cause -> prevention -> guard -> regression:** premature permission lifecycle demonstration -> withhold permission until functional forwarding core exists -> disabled UI and no source permission invocation -> Android emulator + full exact-SHA hosted CI mandatory. Minimal controls, no extra retries. Status: LOCAL CANDIDATE; hosted/physical acceptance UNPROVEN until results.

**Evidence/authority:** `evidence/V444_MOBILE_FORWARDING_GAP_BENCHMARK_20261014.json`, Android official `https://developer.android.com/reference/android/net/VpnService`. Exact next action: rebuild nested/public manifests, test, promote PR #51 only after exact-head CI passes. Full mobile Internet remains MISSING.

**V444A manifest-rebuild failure prevention:** First local rebuild exposed that `tests/rebuild_crossplatform_manifest.py` hardcoded superseded `4.3.7-crossplatform-r51-linux-r18` and would silently downgrade the accepted manifest version `4.3.7-crossplatform-r51-linux-r20`. Root cause: stale generator constant. Prevention: derive schema/version from the existing authoritative manifest and fail if absent; regenerate the cross-platform file digests without changing its accepted version. Keep Windows R53/Linux R21 public asset hashes frozen; update only source `RELEASE.json` cross-platform SHA, `PUBLIC_MANIFEST.json`, and related evidence. Verification is pending full local and hosted exact-SHA tests; no release promotion implied.

**V444A hosted emulator first failure (not repeated blindly):** CI run `38569163285` Android emulator built APK, installed and launched `MainActivity`, and observed initial `NOT LINKED` UI PASS. The subsequently added exact UIAutomator text+enabled assertion failed with `UNLINKED_VPN_BUTTON_NOT_DISABLED`; the log did not retain raw XML, so whether the expected node was absent or its rendered attribute differed is UNVERIFIED, not a confirmed Android code defect. Root-cause class: over-specific UI test condition beyond required safety contract. Prevention/guard: preserve no `VpnService.prepare` call in unlinked source, no permission request in live UI, no running FreeNet Hub VPN service and no network-interface mutation; remove brittle exact disabled-node assertion. The earlier failure remains preserved in hosted logs and V444 evidence. New exact-head CI is OPEN; no PASS or promotion inferred.

## 2026-10-14 — V445: Android unlinked VPN Always-on opt-out + accepted dual-repo CI closure

**Previous accepted state:** GitHub main `14145ac00af934c1405760f086cbd1c3e9272816`, PR #50/#51 merged, official CI run `38570732401` 10/10 SUCCESS; organization CI `38571407077` 10/10 SUCCESS and code analysis `38571407597` 3/3 SUCCESS. Windows R53 4.3.9 and Linux R21 installed and scoped CFON HTTPS204 accepted; both host installs remain unchanged.

**ONE mutation objective (V445, current candidate):** Android `FreeNetVpnService` is intentionally a nonfunctional stub (no forwarding, no VPN permission action). Android's documented `SERVICE_META_DATA_SUPPORTS_ALWAYS_ON` defaults to true when not explicitly disabled. Source AndroidManifest lacked the false flag, creating a misleading eligibility for OS Always-on despite no forwarding core. Add exactly one `android.net.VpnService.SUPPORTS_ALWAYS_ON=false` metadata tag and a scoped XML parser guard in hosted `android-build` CI; do not establish TUN, grant VPN consent, or change device. This is a safety/quality fix, not operational mobile-VPN acceptance.

**Root cause -> Prevention -> Guard -> Regression:** Missing explicit Always-on metadata -> explicit false until a working core is integrated and tested -> verify manifest, stub status and absence of `VpnService.prepare` in Android CI -> public and cross-platform manifest hashes, desktop regression, Android emulator, exact-SHA hosted matrix. Official primary source: https://developer.android.com/reference/android/net/VpnService. No independent hardware validation of Android Always-on selection is claimed.

**Fresh read-only Windows Gateway owner status:** Called `gateway/gateway_control.ps1 -Action Status` from the actual installed R53 runtime. Script exited 0 with `status=PASS`, `running=false`, `mode=""`, `tun=null`, `console.status=Missing`. Calling the same source from clean Git checkout failed `APP_DEPENDENCIES_MISSING` because build-time sources deliberately omit installed dependency metadata; not evidence of installed-product failure. Current Windows session is not elevated. No PC_TUNNEL full-system validation was performed, and no network route/DNS changes made.

**Linux status:** R21 installed integrity 9/9 PASS, scoped CFON 204, Tailscale Running. Native WARP Terms remain unaccepted and noninteractive sudo unavailable. Full-system native WARP and network leak/rollback still OPEN.

**Roadmap:** Windows/Linux scoped install/browser and dual-repo CI — ACCEPTED; Android prototype false permission fix V444 — ACCEPTED in source/CI; Android Always-on opt-out V445 — CURRENT CANDIDATE; mobile functional forwarding and Apple provisioning — MISSING/EXTERNAL; privileged Windows/Linux strict full-system proof — OPEN external owner/admin; physical rollback and cross-device FINAL — UNPROVEN.

**Evidence/knowledge:** `evidence/V445_ANDROID_UNLINKED_ALWAYS_ON_GUARD_20261014.json`, Android official VpnService contract, V444 and V443 accepted records. Status: CANDIDATE until exact-SHA hosted tests pass, merge + postmerge verification. Project license choice and GPL obligations remain owner/legal gate. Exact next action: rebuild dependent manifests preserving accepted release version; local tests; exact-SHA CI; promote only on evidence.

**V445B evidence-first correction before promotion:** The initial V445A candidate used Android `SERVICE_META_DATA_SUPPORTS_ALWAYS_ON=false`, but official Android VpnService API documentation states this metadata is only honored on Android 8.1 / API 27+. Since FreeNet Hub still supports minSdk 26, that fix leaves Android 8.0 exposure. Minimum sufficient, OS-version-independent correction: remove the incomplete `FreeNetVpnService` service entry from AndroidManifest altogether while preserving the unlinked Kotlin stub for future development. The Android CI guard now asserts that the unlinked service is NOT registered, `providerCoreReady()==false`, and the Activity never calls `VpnService.prepare`. No dummy TUN, no device install, no VPN ownership, and no host routing mutation. Previous V445A exact-head SHA `4419c21fc2a3e4417fee13aa9c931b7053ed452b` is SUPERSEDED as a candidate even if its narrower CI succeeds. Root cause: platform-version limitation overlooked when selecting a flag-only remedy. Prevention: benchmark Android-supported OS floor alongside API behavior and choose service-unregistration until functioning core is ready. The new V445B exact-SHA CI and cross-platform release manifest seals remain open. Evidence: `evidence/V445_ANDROID_UNLINKED_ALWAYS_ON_GUARD_20261014.json`, https://developer.android.com/reference/android/net/VpnService.

**V445C downstream documentation consistency:** A follow-on read-only source audit found `crossplatform/android/README_FA.md` still claimed VpnService registration and obsolete Gradle/SDK versions. This contradicted the unregistered service guard and could mislead users about a historical debug APK. The Android README now matches the current manifest, hosted JDK17/Gradle8.11.1/AGP8.10.1/SDK36 toolchain, and explicitly marks historical debug APK as NOT a functional VPN installer. Root cause: reference documentation not propagated after a safety mutation. Prevention: include user-facing Android scope and release claims in the same change-set review. No new product/runtime scope; candidate remains UNPROVEN until exact-head CI.

## 2026-10-14 — V446: Verified Windows old-installer cache removal and source prevention candidate

**Accepted baseline:** official and organizational GitHub main both at `a7893b5d2f5158dd7b644e029f91f0c955a5b5e1`; hosted postmerge CI official `38584377964` 10/10 SUCCESS, organization `38584538560` 10/10 SUCCESS, organization security `38584535347` 3/3 SUCCESS. PR #52/Android fail-closed service unregistration is ACCEPTED in source. Installed Windows R53 and Linux R21 scoped CFON remain healthy.

**One new change-set blocker:** On physical owner Windows R53, two leftover installer-download caches (R39 and R46) totaling **48,519,315 bytes** existed in `<installed FreeNetHub>/updates`; they were not duplicate app installations. Exact path, version, file size and SHA256 checks passed. Narrow transaction quarantined only those two known single-installer directories, verified app process and CFON HTTP204, then removed the quarantine. Both old update directories are now absent. No active app, installation identity, Tailscale, route, DNS or user settings changed. Private physical receipt: `OWNER_PRIVATE_GIT_MAINTENANCE/FNH_R446_CACHE_20261014/RECEIPT.json`.

**Root cause:** `app/engine.py:update_download` verified the new installer but never expired earlier `ROOT/updates/<tag>` installers. **Source prevention candidate V446:** add `prune_stale_installer_cache` immediately AFTER successful download SHA verification. Remove only known version-tagged, one-file `FreeNetHub_*_Setup.exe` cache directories; preserve current verified tag, unknown sidecars, nested files, symlinks and locked files; never prune if download or hash fails. Reject generic recursive deletes, cleanup-before-verification and a hidden release/installation mutation. Return pruned directory names for traceability.

**Local verification:** Python source compile PASS. 128 Linux-compatible unit cases PASS, including three new cache safety tests. Four unmodified Windows process/native tests cannot run on Linux (`ctypes.WinDLL` and Windows-only `creationflags`); they were NOT reported as application regression, and the exact-SHA hosted Windows CI must prove them. An initial Linux all-test run wrote `evidence/unit_tests.json` with 4 OS-specific errors; this generated status artifact was restored from accepted main, while the failure rationale was retained here and in V446 Evidence. Separate physical installed-R53 cleanup PASS. **No newly compiled installer or field update from V446 source has been deployed**, so future cache auto-GC is NOT yet accepted in the installed application.

**V&V / roadmap:** ACCEPTED = V445 dual-repo CI + CodeQL, owner R53/R21 scoped browser functionality, physically scoped one-install audit and stale cache cleanup. CURRENT = V446 updater source guard, tests and metadata. OPEN = exact-head Windows and cross-platform CI, publish/install a future engine revision, owner privileged Windows PC_TUNNEL, Linux native WARP ToS/sudo recovery, mobile Android/iOS real forwarding, Apple signing and real device, physical rollback. Verification of the source is not validation of the future installed release.

**Authority/reuse:** `evidence/V446_WINDOWS_UPDATE_CACHE_GC_20261014.json`; owner receipt in private .git maintenance; `app/engine.py`, `tests/test_engine.py`, official CI run IDs. Status: CANDIDATE, no automatic promotion. Exact Next Action: rebuild app/source/public integrity references, run local tests and hosted exact-SHA CI before any merge.

**V446B junction regression hardening (2026-10-14):** Reviewed official Python 3.12 pathlib reference: `Path.is_junction()` is a Windows-specific guard independent of `Path.is_symlink()`. Initial V446A cleanup could follow a Windows NTFS junction in `updates` or a tagged cache directory, potentially touching unrelated data. One objective retained: safe bounded stale installer GC. Add junction checks at both root and candidate directories and a hermetic test simulating each type. Source: https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.is_junction. Initial V446A SHA `b5835221991c90cd0094621e2e2fcd0b314003e1` is SUPERSEDED for promotion even if its CI succeeds; V446B revised SHA and hosted Windows CI must PASS first. No owner runtime or published assets changed. Documented in `evidence/V446_WINDOWS_UPDATE_CACHE_GC_20261014.json`.

**V446C compatibility closure (2026-10-14):** Source audit revealed that `FreeNetHub.ps1` can select an existing `pythonw.exe`/`python.exe` and does not require Python >=3.12, whereas direct `Path.is_junction()` calls introduced in V446B require Python 3.12+. Root cause: new guard overlooked old runtimes. Prevention: a missing `is_junction` method marks cache paths unsafe, so automatic prune is skipped without interfering with the SHA-verified installer download; no files are deleted. Added test that simulates absence of API. V446B SHA `b20a30ba3d72409d30fa46df515eaa2017c08b46` superseded by final compatibility candidate; no main/release/owner runtime mutation. Primary source Python 3.12 `pathlib.Path.is_junction()` official documentation. Promote only after candidate full exact-SHA CI (Windows Unit/Installer, Android/iOS included). Evidence updated in `evidence/V446_WINDOWS_UPDATE_CACHE_GC_20261014.json`.

## 2026-10-14 — V447 dedicated R54 disposable Windows installer validation (candidate)

**Previous accepted state:** PR53 / V446C merge `e4112be36d6cce97863c59a5dbe6a5d0bcdf5786`, exact 10/10 official and 10/10 organization hosted CI, 3/3 organizational security PASS. Owner Windows R53 and Linux R21 scoped live CFON/Tailscale healthy. R54 4.3.10 offline Inno-built installer SHA256 `BBDD67CA274EEDA7486017BD2EDF9EACBF1995405F7913634F4F42E80B9076D8` and 24,277,407 bytes; **not published, signed, installed or field accepted**. Raw Windows private build receipt in owner Git maintenance.

**One V447 objective:** isolate acceptance of R54 fresh installation, exact SHA verified R53-to-R54 update, single Inno AppId/uninstall registry entry, user settings/data preservation and explicit R53 rollback, without ever touching running owner R53 or unrelated production servers. Method follows official Inno AppId / use previous directory contract, SHA-pinned accepted public R53 and disposable Windows GitHub runners. Source refs: https://jrsoftware.org/ishelp/topic_setup_appid.htm ; https://jrsoftware.org/isfaq.php ; https://docs.github.com/en/actions/reference/security/secure-use.

**Candidate implementation:** `tests/prepare_r54_isolated.py` only transforms a clean detached Git worktree at exact V446C accepted SHA; verifies 17 app source hashes and adjusts R54 source/release/Inno metadata, fixed AppId. `tests/test_r54_isolated_upgrade.ps1` builds using Inno and verifies real Windows fresh install and R53→R54→R53 rollback with user data fixtures and one uninstall registration. A dedicated isolated Windows CI workflow adds independent fresh and upgrade matrix runners, no secrets and pinned checkout. Main source and published installer remain R53. Unchanged owner settings/routes are protected.

**Verification vs Validation:** Local Linux staging and new version checksum-chain PASS; PowerShell AST syntax checked on owner Windows PASS; isolated native Windows install/upgrade NOT YET RUN (candidate CI pending). A standalone private owner-side R54 build passing metadata validation does NOT prove upgrade/rollback. Current evidence `evidence/V447_R54_ISOLATED_UPGRADE_VALIDATION_20261014.json`; previous V446 evidence/history preserved. No installation attempted on connected shared admin server because no disposable sandbox available.

**Roadmap and Next:** Completed = source V446, hosted repo CI/security, physical Windows junction safety, R54 offline metadata/build; CURRENT = R54 disposable Windows install/upgrade/rollback acceptance; OPEN = exact candidate CI, future versioned release, owner field update, Windows privileged PC tunnel, Linux WARP owner consent/sudo, actual mobile forwarding/signing/license. Exact next action: run PR-hosted exact-SHA Windows fresh and upgrade tests and resolve evidence-backed blockers only. Do not auto-promote on local or source-only PASS.

**V447 first hosted Windows install trial — evidence-backed TEST FAILURE (2026-10-14):** PR #54 first candidate exact SHA `0289d985e7ae0aa6e80a859be740249d4223a016`, dedicated hosted R54 run `38597150753`, both fresh and R53→R54 scenarios failed at the same overly restrictive test assertion `DUPLICATE_INSTALL_REGISTRATION_0`. The installer invocation had already completed and exact Inno AppId registry lookup succeeded, but the regression test incorrectly filtered display name `^Free Net Hub$` rather than actual `FreeNet Hub version 4.3.9` observed by independent read-only owner HKCU query. Root cause: incorrect test fixture string, NOT a confirmed R54 install/upgrade defect. Replace only product display-name matcher and require a single registration and exact AppId/root. Do not rerun old failed CI; revised exact SHA must run fresh+upgrade again. Hosted log job IDs `115966708132` and `115966708535`; `evidence/V447_R54_ISOLATED_UPGRADE_VALIDATION_20261014.json`. No production owner app/network mutation; existing R54 private artifact untouched. State=REVISED_CANDIDATE_UNPROVEN.

## 2026-10-14 — V448 R54 exact-tested artifact provenance candidate

**Previous Accepted:** PR #54 merged source `03318fa00ba56d625f6178aed517fbaba65d55a4`, exact PR-head CI 10/10 PASS, disposable Windows fresh + R53→R54→R53 upgrade/rollback 2/2 PASS. Both GitHub main refs and Windows/Linux owner source clean on same SHA. Owner Windows R53 and Linux R21 active; no published R54. Post-merge CI running, no promotion until complete.

**One blocker:** generated private R54 installer SHA-256 differed across owner offline, CI fresh and CI upgrade runs; byte-level identity with previously tested installer unproven. **V448 limited fix:** after a successful hosted R53→R54→R53 upgrade test, compare exact binary SHA and size to the test receipt, copy only that binary, write SHA256SUMS and private EVIDENCE.json, and archive via SHA-pinned official actions/upload-artifact v4.6.2. Retains current R53 public release, no owner runtime or routes changed. This provides a canonical **private** tested R54 candidate for later release gating, not a public installer, signing, physical field acceptance or deterministic-build proof. Source: https://github.com/actions/upload-artifact ; https://github.com/github/docs/blob/main/content/actions/tutorials/store-and-share-data.md. Evidence in `evidence/V448_R54_EXACT_TESTED_ARTIFACT_20261014.json`. Rejected: guessing hashes, publishing untested rebuilt bytes, uploading entire runner directories. New exact-PR CI and archived artifact digest confirmation required before Accepted. Roadmap CURRENT = V448 private tested binary provenance; OPEN = versioned public R54 release and physical owner safe upgrade, whole-system Windows/Linux, mobile real forwarding. Exact Next Action = obtain passing hosted CI, retrieve artifact and verify its binary digest equals in-run receipt.

## 2026-10-14 — V449: Coherent R54 release-line embedded metadata (candidate)

**Previous accepted state:** V448 source merged at `b9bb40e6e504e1c3eba5bc442c1286782a36eb4e`; exact older *private* Windows R54 installer SHA256 `6D8DA29328842149371DB862908FB6D1E6079E1FD055DB8450AE7BE51804AE0D` passed dedicated Windows fresh + R53→R54→R53 upgrade/rollback and was preserved in GitHub Draft release `v4.3.10-r54-windows-candidate` (ID `412978295`, **unpublished**). Official and organizational source parity PASS, organization CodeQL 3/3 PASS. Physical Windows R53 and Linux R21 live sessions remain untouched.

**One blocker:** publishing the prior tested EXE under a Stable label would contradict its embedded `RELEASE.json` private-candidate status and Windows VersionInfo private description. Do not mislabel exact bytes as production. **V449 proposal:** keep prior draft unchanged; alter only the *detached exact-base R54 build recipe* to emit internally consistent unsigned versioned R54 metadata (`R54_UNSIGNED_WINDOWS_INSTALLER_RELEASE_LINE`), matching Inno description and a new hash-verified artifact. Retest actual fresh install, same-AppId R53→R54 upgrade, settings/data retention, and explicit R53 rollback on disposable Windows runners. Failed or inconsistent artifact never promoted. New build is a distinct SHA by design; older digest is not reused.

**Evidence and proportionality:** Local preparation checks 17 code hashes and App/RELEASE integrity PASS; existing Inno AppId retained; PowerShell AST PASS on owner Windows; dedicated exact-SHA hosted Windows matrix and artifact digest are still PENDING. Primary docs: https://jrsoftware.org/ishelp/topic_setup_appid.htm ; https://cli.github.com/manual/gh_release_create ; https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository. Rejected rebuilding and silently reusing old digest, overwriting R53 assets, publishing unsigned product without scope warnings, or unilateral license grant. Project's lack of an explicit license remains owner/legal gate; no license was assigned.

**Roadmap:** COMPLETED = V446C cache safety source and V447 isolated upgrade, V448 exact private artifact/archive and draft; CURRENT = V449 coherent R54 release-line binary, new CI; OPEN = V449 exact binary acceptance and public release decision, physical owner upgrade+rollback/connection restoration, Windows privileged PC_TUNNEL, Linux native WARP owner consent/sudo, real Android/iOS forwarding. See `evidence/V449_R54_RELEASE_METADATA_20261014.json`. Exact next action: run new 2-job Windows CI and full source CI on the final V449 SHA, confirm new archive SHA, then review public release scope without modifying active R53.

## 2026-10-14 — V450 R54 tested draft binary provenance and exact postmerge CI

**Previous accepted:** source main `85869597170ab111c890a26ca3c902a6e87cbacc`; Windows owner R53 and Linux R21 scoped installations unchanged. Earlier V449 candidate status superseded for CI/asset-upload integrity only; history remains append-only.

**Evidence-backed completion:** GitHub Actions main CI `38606871791` at that exact SHA passed **10/10** jobs. Dedicated Windows R54 isolated `38605228141` at PR #56 head `446996a3a6033feabe36506b1ea7e1f42e1673e4` passed **2/2** native fresh and R53→R54→R53 upgrade/rollback jobs, with one Inno AppId and settings/data preservation in disposable runners. Installer is 24,267,012 bytes; exact run receipt SHA-256 `ED9B89C4C228D128229F5C1C98B628D7226E2E3FD784F8990A63494862C83852`. GitHub Release REST API upload-computed digest for draft asset `641103644` matches the same hash and size. Draft release ID `412991602`, tag `v4.3.10-r54-windows-release-review`, remains unpublished. GitHub hosted ZIP artifact `11915626213` has a distinct archive digest; do not confuse with installer hash. A separate 25 MB owner-host download stalled and was stopped, so no local downloaded-byte hash claimed.

**Risk and V&V:** PASS applies to source CI, disposable Windows installation/reversion, and uploaded draft artifact integrity; it does NOT prove installed owner R54, public release rights, privileged Windows PC_TUNNEL, Linux native WARP full-device routing, Android/iOS forwarding or Apple entitlement. Windows still has active R53; Linux R21, Tailscale Running/two peers and direct Google HTTPS204. No owner app, route, DNS, Tailscale or published release changed. Method benchmark: GitHub official release-asset SHA-256 digest field (https://docs.github.com/en/rest/releases/assets?apiVersion=2026-03-10). Licensing/third-party rights remains an owner/legal review gate; no license assignment or silent ToS consent.

**One mutation objective:** carry verified V450 provenance forward in Project Brain and structured evidence; source/installer/runtime unchanged. Status = CANDIDATE until exact-head CI and merge. Evidence: `evidence/V450_R54_HOSTED_DRAFT_ASSET_AUDIT_20261014.json`. Roadmap: accepted source and hosted installer proof → CURRENT documentation CI → OPEN owner release authority → reversible physical upgrade → strict Windows/Linux full-system and real mobile validation. Exact next action: run evidence-only exact-head CI and merge only on success, then separately assess rights and perform recoverable owner upgrade.

## 2026-10-15 — V451 final CI closure and owner-field safety gate

**Previous accepted → current delta:** V450 documentation PR #57 merged as main `22b5a0e4b8c960e3a601067a891deba10475f4f1`; exact postmerge GitHub run `38630643887` finished **10/10 SUCCESS**. This supersedes the V450 record's prior `CANDIDATE` CI status *for source/CI only*. Both Windows/Linux owner source copies clean on that SHA, Linux full public manifest verification PASS. The R54 GitHub Draft candidate remains unpublished.

**ONE objective:** close verified release-binary readiness and identify the real owner-field blocker without mutating live networking. Owner Windows separately downloaded and SHA-256 verified the exact hosted Windows-tested R54 4.3.10 binary (24,267,012 bytes; `ED9B89C4C228D128229F5C1C98B628D7226E2E3FD784F8990A63494862C83852`) and pinned R53 rollback EXE (24,268,030 bytes; `34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2`). These are staged in private `.git/FNH_R54_SMALL_ASSET_PROBE_20261014/`, **not installed**. The installed Windows registry lists one FreeNet Hub 4.3.9 R53. Its `session.json` explicitly says `connected=true`, `mode=CFON`; socket `127.0.0.1:19414` responds HTTPS 204 via SOCKS5H. Installed Gateway Status exits 0, but `running=false` and Console Missing. The Inno upgrade's `Prepare-Upgrade.ps1` intentionally blocks a connected session with exit 42. **Do not bypass** while remote-control independence/recovery remains unproven.

**Cross-host and benchmarking:** Linux R21 remains installed; Tailscale Running/two peers; native Cloudflare `warp-cli status` still requests explicit Terms agreement and noninteractive `sudo` fails. Windows default route Ethernet 3 and Linux Wi-Fi route were not modified. Official Inno Setup AppId/Same Application docs confirm fixed AppId + equivalent install mode supports the one-install upgrade pattern; prior disposable GitHub-hosted R53→R54→R53 test 2/2 PASS. Official Tailscale docs caution VPN firewall/route conflicts; Cloudflare docs specify WARP registration/connection after valid setup. GitHub licensing docs distinguish *no open-source license* from copyright owner's own distribution authority: no root LICENSE is not automatic legal prohibition, but rights and bundled third-party notices remain a bounded owner review. Optional GitHub artifact attestation is useful supply-chain enhancement, **not** a substitute for current byte identity or a required new gate. Sources and rationale in `evidence/V451_R54_FIELD_RELEASE_READINESS_20261015.json`.

**Verification ≠ validation:** ACCEPTED = source/postmerge CI 10/10, exact R54 binary integrity, isolated native upgrade/rollback, current browser-scoped CFON 204. OPEN = owner's R54 physical upgrade and restoration without losing remote control, stable publication/rights and coherent release source authority (main RELEASE.json deliberately still R53; R54 built through pinned detached recipe), Windows elevated PC_TUNNEL, Linux owner WARP ToS/sudo and leak/route restore, mobile Android/iOS forwarding and Apple physical signing. No host app, routes, DNS, Tailscale or public release were altered. This is evidence-only V451, candidate until exact-head CI/merge. Exact next action: merge verified evidence and prepare out-of-band supported field-maintenance, rather than weakening installed safety guard.

**V451 security-scan regression and prevention (same objective; 2026-10-15):** First hosted PR #58 run `38633992473` failed the `windows-unit` job at `tests/security_scan_public.py`: sensitive-pattern detection correctly found a Windows account-specific absolute path inside `evidence/V451_R54_FIELD_RELEASE_READINESS_20261015.json`. Earlier manifest validation passed. Root cause was public evidence over-disclosure, not an application runtime failure. Narrow remedy: replace only that path with `OWNER_PRIVATE_GIT_STAGING/...` logical locator; exact owner file location remains private. Prevention: run full `tests/security_scan_public.py` together with manifest/public integrity locally before re-sealing evidence. First PR SHA `10516fe1bbcb5d4ee9552ba82bf9ee9cf20e8aac` superseded for promotion. A new exact-head CI is required; do not blindly retry the failed SHA. No installer, network, settings, licensing or source runtime changes.


## 2026-10-15 — V456 live CFON country, destination diagnosis and owner recovery readiness

**Previous accepted:** V451 main `7b2d0514c966b372f766ca2f95db27a55f49022f`, postmerge CI run `38635713648` 10/10 SUCCESS, owner Windows R53 4.3.9 and Linux R21 `4.2.0-linux.21-r54`. No software upgrade or route, DNS, Tailscale, Cloudflare WARP Terms, or published-release change.

**ONE objective, evidence-backed delta:** Scoped explicit SOCKS5H Cloudflare Trace compared with direct on both owners: direct `loc=IR`, CFON `loc=AT`, `warp=off` in all observations. This is a successful browser-proxy egress change, not full-system network capture, strict leak elimination, country permanence or browser/account acceptance. Owner Linux R21's native `test_active_sites(timeout=5)` returned overall PASS in `BROWSER` scope (Google HTTP204, GitHub 200, NVIDIA 200); ChatGPT curl HTTP403 was correctly `HTTP_RESTRICTED_OR_CHALLENGED`. Direct and CFON `curl` on both owners received `cf-mitigated: challenge` at ChatGPT; official Cloudflare docs establish this is a Challenge Page response, not proof of a failed proxy transport or an accepted interactive browser. GitHub and Google HTTPS via CFON remained reachable.

**Root cause → prevention → guard:** Windows owner CFON session remains `connected=true`, so the installer deliberately blocks an unsafe in-place update. Tailscale peer ping works bidirectionally, but no *authenticated, independently recoverable control* was demonstrated if the active provider is interrupted: WinRM and RDP services are stopped, Windows SSH server not available, tailnet probes of ports 22/3389/5985/5986 closed, execution context not elevated. Official Tailscale SSH server only supports Linux/macOS (not Windows). Official Windows OpenSSH setup requires elevated configuration and firewall handling. Do not create a privileged remote service merely to bypass the live upgrade gate, or force a session termination. Recovery/owner maintenance gate still OPEN.

**Minimum sufficient data preservation:** Read-only owner Windows inventory counted 33,204 files / 7,159,078,292 bytes in app data, plus 1,833 job files / 486,846,719 bytes. Folder-name classification (not a deletion authorization) suggested 6,205,151,627 bytes in browser/profiles and 817,313,401 bytes in cache/temp. Rather than duplicate >7 GiB, one limited DPAPI CurrentUser encrypted backup of **9** selected settings/identity files was created on the owner Windows (2,287,495 original bytes; 254,134 ciphertext bytes, SHA256 `64C6BE6FD6867D6177B64087C09281538BC9234925204FA525AF862835D6A210`), re-opened/decrypted in a separate PowerShell 7 process and independently verified all 9 archive members and no source drift. It explicitly does **not** cover browser profiles, jobs, runtime or ephemeral session. Per Microsoft DPAPI reference it is usually tied to the same user and computer. Sensitive original data and ciphertext are excluded from repository evidence.

**Method benchmarks, limits, authority:** Inno Setup Same Application docs favor fixed AppId for one install, existing hosted R53→R54→R53 tests PASS, but physical owner upgrade/rollback UNPROVEN. Cloudflare Challenge Page docs require `cf-mitigated: challenge` classification, not forced HTTP PASS. Tailscale SSH documentation does not authorize Windows hosting. No additional attestation, mass backups, blind reruns, unsafe cleanup or new mandatory controls without outcome benefit. Structured knowledge `evidence/V456_CFON_FIELD_AND_RECOVERY_READINESS_20261015.json` records sources, decisions, risks, confidence and reuse targets. Source/installer/runtime authoritative and unchanged.

**Roadmap:** Accepted source & binary CI → accepted scoped owner browser proxy → CURRENT V456 knowledge CI → OPEN authenticated independent owner Windows recovery and controlled R54 field upgrade/rollback → OPEN rights/public release & Windows/Linux full-system leak/route validation → OPEN mobile forwarding/Apple entitlement → FINAL UNPROVEN. Exact next action: verify V456 exact-head CI and merge, then acquire and test a recoverable authorized Windows control path before gracefully stopping CFON and upgrading. Existing owner connectivity and public R53 are deliberately preserved.


## 2026-10-15 — V457 physical R54 upgrade abort and accepted R53 scoped reconnection

**Previous accepted:** V456 knowledge PR #59 merged to main `2c7f368ae9ac2f6e3c015327a545345abd1881fa`, exact-head push/PR CI runs `38638733000` and `38638806618` 10/10 each, Windows owner R53 4.3.9 CFON working, Linux R21 unchanged. This section is an append-only field-failure delta: it supersedes earlier assumptions that authenticated AnyDesk can be relied upon continuously, not historical source CI success.

**ONE change objective = bounded physical upgrade failure → prevention → recovery:** existing installed Windows R53 engine's official `Stop CFON` returned exit0, session `stopped=true` and port 19414 closed. A PowerShell receipt wrapper incorrectly required optional `connected` field in the stopped schema and failed AFTER the successful Stop; future wrappers must use optional property semantics. One prior DPAPI snapshot check initially rejected natural drift in `last.json` written by Stop; comparison proved 8/9 selected config and identity members unchanged and only ephemeral `last.json` changed. Narrow field preflight permitted only that exact expected drift, not arbitrary changes.

The exact SHA-pinned hosted R54 4.3.10 installer was executed ONCE and **did not install**: Inno Setup exit **7**, where official setup docs define the `Preparing to Install` rejection; private Inno log reports `Prepare-Upgrade.ps1` exit **43**, meaning old FreeNetHub UI/process closure was not verified in time. Source helper currently checks owned old processes after a 400ms sleep. A race is plausible but unproven. Immediately afterward read-only process/port audit showed zero owned UI/ports; installed registered version and RELEASE.json stayed R53 4.3.9 with ONE uninstall entry and original browser-profile directory presence. No reboot or global network mutation.

Exactly ONE different-prestate guarded retry was prepared, but it **aborted in preflight** because AnyDesk returned OFFLINE **before any installer launch**. Linux AnyDesk authenticated session had earlier started and received input permissions, but a subsequent log event reports `Session stopped`; therefore a persistent recoverable remote channel while CFON is off remains UNPROVEN despite successful Tailscale pings. No further installation retries.

**Physical service restore PASS:** The original installed R53 engine then ran `Connect CFON` (not replacement binaries), returned exit0, session `connected=true` mode CFON, 127.0.0.1:19414 listener, Google HTTPS over SOCKS5H 204. Windows remained R53 4.3.9, Tailscale Running and AnyDesk again Online. This closes *recovery to previously working browser CFON*, not R54 acceptance. Owner detailed log and transactions are private, outside Git. No passwords/AnyDesk IDs in source evidence.

**Method benchmark and guard:** Official Inno Setup Setup Exit Code 7 documents rejection BEFORE actual installation, and AnyDesk official Session ended unexpectedly guidance highlights network, firewall and VPN disruptions as possible causes, not proof of this exact cause. Keep active-connection guard and prestate/binary-hash verification. The minimum sufficient next code change, if justified by isolated reproducible evidence, is a bounded wait for exact-owned GUI/process shutdown under the existing safety policy; no blind kill or full-system mutation. Validate an authenticated unattended backup control channel across CFON shutdown *for the maintenance window* before any further physical R54 installer attempt. See `evidence/V457_R54_OWNER_FIELD_ABORT_AND_R53_RECOVERY_20261015.json`; reuse for publication, regression, incident prevention, and owner's field handoff.

**Roadmap:** ACCEPTED source/isolated CI → ACCEPTED limited R53 field stop/reconnect with critical settings preserved → ←CURRENT V457 evidence CI → OPEN independently stable Windows maintenance channel and owned-process close test → OPEN physical R54 upgrade+reconnect/rollback and owner rights/public release → OPEN full-device tunnel, Linux native WARP owner ToS/sudo and mobile real forwarding → FINAL=UNPROVEN. Installed runtime and public stable R53 remain unchanged.


## 2026-10-15 — V458 bounded owned-process wait candidate and isolated acceptance

**Previous accepted:** V457 GitHub main `28f3572e550f4e4a7e9baaa9582dddbc25df2795` with owner R53 CFON restored and R54 setup failure archived. V457 postmerge CI is a separate gate. Current ONE blocker is Inno Prepare-Upgrade exit43 on physical Windows due unverified timely old GUI shutdown; confirmed failure, asynchronous-stop race only probable.

**Evidence-first change:** Official Microsoft Stop-Process documentation states termination is asynchronous; Wait-Process supports a bounded timeout. Inno PrepareToInstall happens before the actual installer modifies files and can fail closed with exit7. Rather than disable the guard, `windows/installer/Prepare-Upgrade.ps1` now waits up to 8 seconds for *only the previously identified owned GUI/pwsh PIDs* after Stop-Process. The existing active-session, global gateway, foreign-listener and final owned-process/port exit42/43 guards remain unchanged; if still running, install remains blocked. No owner Windows runtime mutation was made.

**Verification vs validation:** A new Windows hermetic PowerShell test exercised five synthetic scenarios and observed 5/5 expected results: quiescent=0, delayed-owned-exit=0 with WAIT, persistently-owned=43, active-session=42, foreign listener=42. It does not prove field upgrade; hosted two-mode Windows R54 build, fresh/upgrade/R53 rollback still required. Linux static checks and public security scan PASS. Method sources: https://learn.microsoft.com/powershell/module/microsoft.powershell.management/stop-process ; https://learn.microsoft.com/powershell/module/microsoft.powershell.management/wait-process ; https://jrsoftware.org/ishelp/topic_scriptevents.htm.

**Immutable candidate rule:** Existing R54 unpublished Draft and SHA remain untouched. The earlier R54 app recipe was frozen to base `e4112be36d6cce97863c59a5dbe6a5d0bcdf5786`. Packaging of the *distinct* V458 fixed installer now checks original helper SHA `39f01a2cbcef9e15ae0d2b279a1965f8ec82f53d7c33527565417aa9e9274614` then injects exact updated helper SHA `98bd0a564ea8055960d3a5b6c8cb3b5737da391d88846f7562621b8e8dc1656c`; its binary will have a NEW SHA and cannot be relabeled the already accepted old R54 binary. Hosted GitHub isolated fresh/upgrade/rollback are the next verification gate. Current release promotion = UNPROVEN. See `evidence/V458_INNO_BOUNDED_OWNER_EXIT_20261015.json` for full rationale, tested cases, failure safeguards and future reuse.

**Roadmap** accepted owner R53 browser CFON → accepted failure/root-cause evidence → ← V458 code+mock regression candidate → open hosted exact-binary V&V and separate owner independent recovery → open physical corrected upgrade+rollback → open rights/public release, Windows/Linux full-system and mobile forwarding → FINAL UNPROVEN. Do not disconnect owner R53 to retest before recovery gate.


## 2026-10-15 — V460 owner Windows R54 field update and recovery, accepted physical milestone

**Previous accepted:** V458 merged source `7dd485267221f617beb48e09357e0321cd03510b`, exact-head CI and postmerge CI `38678432093` **10/10 SUCCESS**, hosted isolated Windows R54 fresh and explicit R53→R54→R53 rollback `38677740422` **2/2 SUCCESS**. Original R54 binary SHA `ED9B89C4...` once failed physical Inno PrepareToInstall 43; remain distinguishable from new V458 corrected helper SHA `98BD0A56...`, new owner-tested binary SHA `6D3F46C952EFCB0BB653454DA39F6E80754997BD15CB11376FC19E4535BF2DB5` (24,272,803 bytes).

**ONE owner mutation objective complete:** On actual owner's Windows, exact SHA-pinned R53 version 4.3.9 installed and CFON connected. Prior to install, current limited DPAPI-protected nine-file selected settings snapshot was refreshed after legitimate node/public-refresh file changes; new encrypted SHA `49E44E86520BE761AF300A22D0EF8ECEDE220F1DCEB570DCA75441DAC02F81C3`, 9/9 decrypt+hash and current-file equality PASS in separate process. This is not a backup of all browser-profile data. Original R53 rollback installer SHA `34A1A453...` preserved privately. AnyDesk authenticated Linux→Windows session established over Tailscale direct TCP/7070 and **survived actual CFON Stop**, alongside continuing Remote Commander and direct HTTPS204. An initial one-shot Windows R53 recovery experiment FAILed because strict PowerShell accessed optional JSON `connected` after Stop; manually restored R53 without reboot. Minimal PSObject.Properties guard was regression-tested on five synthetic cases and live self-recovery retested: `AUTO_RECOVERY_PASS`, engine exit0, CFON HTTPS204. Reusable correction is private; the original failed attempt and rationale retained in append-only private handoff.

The owner R53→R54 in-place installation was then performed ONCE with updated V458 SHA-pinned binary, one-shot safe fallback armed. Official R53 CFON Stop returned 0; Inno Setup returned **0**; registered and RELEASE.json version became **4.3.10**, release revision `4.3.10-r54-update-cache-retention`, exactly ONE HKCU uninstall entry. Existing settings.json SHA preserved, both existing top-level browser profile folders remain, **17 installed code files** and app manifest release hash chain verified independently, original new GUI reopened as precisely one FreeNetHub.exe, current R54 CFON Connect engine exit0 and HTTPS204. Google204, GitHub API200 and NVIDIA redirect→200 via SOCKS5H; Cloudflare trace direct country IR and scoped CFON AT, warp=off in both, **NOT** proof of global VPN or persistent country. Tailscale/AnyDesk Running, no reboot, DNS or default route manipulation. V460 local fallback eventually `SKIP_VERSION_CHANGED`, correct because R54 was installed and healthy. Linux installed R21 remains untouched, manifest files PASS and CFON HTTPS204.

**Verification vs validation:** Source tests/hosted clean install+rollback and actual owner Windows install/reconnect are now confirmed independently. Physical downgrading a healthy working owner R54 back to R53 is **deferred** as disproportionate; rollback exact binary is retained and isolated Windows rollback validated. Full bytewise integrity of ~7GiB mutable user browser profile not proven; only original settings hash and two original profile directory presences are proven. Windows full-PC TUN/route DNS leak, native Linux WARP Terms/sudo and coexisting Tailscale, real Android/iOS forwarding and Apple distribution, project-owned code license/third-party redistribution rights and public stable release remain OPEN. Avoid declaring global FINAL. Interactive ChatGPT login remains unproven because curl HTTP403 `cf-mitigated: challenge` is a Cloudflare bot challenge, not network failure.

**Evidence and method:** `evidence/V460_OWNER_R54_FIELD_ACCEPTANCE_20261015.json` records dates, source CI, field installer SHA, scope, independent proofs, uncertainties and citations. Host-only sensitive original scripts/logs, encrypted snapshots and user paths remain privately under project `.git`, not published. Official Inno Setup AppId/Same Application and PrepareToInstall, PowerShell Wait-Process, AnyDesk direct TCP7070 and Cloudflare Challenge docs used; rejected forced network reset, repeating unbounded installer, deleting user caches or promoting old known-bad binary. This is a **meaningful milestone**, so append-only knowledge is added once.

**Roadmap:** accepted V458 CI → accepted V460 real owner Windows R54 scoped install and critical config retention → ← CURRENT sanitized evidence CI+controlled release candidate reconciliation → OPEN owner rights/public Windows release and global Windows/Linux tunnel V&V → OPEN Android/iOS real network forwarding/signing → FINAL=UNPROVEN. Exact next: complete V460 evidence CI and controlled Draft correction (replacing, not duplicating stale unpublished R54 asset) while preserving one clean public stable release until legal and release acceptance.


## 2026-10-15 — V461 one R54 Draft exact-binary reconciliation, live updater check and open FINAL boundaries

**Previous accepted:** V460 owner Windows physical R53→corrected R54, source SHA `20c8213d3aec822e5deb6a2df7a483d9cfdd8ce9`, PR #62 exact-head 10/10 SUCCESS, postmerge CI separate/pending at this writing. Owner running R54 4.3.10 with one HKCU AppId/uninstall entry and one GUI, 17/17 installed code hashes PASS, settings SHA preserved, current CFON HTTPS204. Linux owner R21 scoped CFON unchanged. Hosted R54 fresh and R53→R54→R53 rollback `38677740422` 2/2 SUCCESS.

**ONE governance mutation, no stable publication:** Prior unpublished R54 Draft ID `412991602` with known owner-field failed installer SHA `ED9B89C4...` had three assets. REST metadata, body and all three OLD assets were downloaded and SHA-verified privately before mutation. Existing Draft/Prerelease then had exactly its three asset names replaced in place by new verified R54-V458 file SHA `6D3F46C952EFCB0BB653454DA39F6E80754997BD15CB11376FC19E4535BF2DB5`, 24,272,803 bytes, plus matched CI `EVIDENCE.json` and `SHA256SUMS.txt`. Source target updated to V458 fix commit `7dd485267221f617beb48e09357e0321cd03510b`; explanatory notes explicitly restrict acceptance to Windows browser CFON and label all remaining gates. Poststate independent GitHub REST verified draft=true/prerelease=true, exact 3 expected name/size/SHA digests, same release ID and tag, and a separate GitHub asset **re-download** verified the same installer SHA. Public Latest remains **v4.3.9-r53-windows-stable**. No duplicates, no public promotion. See `evidence/V461_R54_DRAFT_ASSET_RECONCILIATION_20261015.json`.

**Live update-channel regression:** Actual R54 installed engine `UpdateCheck` exit0: current revision R54 > public Latest R53, `updateAvailable=false`, remote latest R53; NO downgrade/install/download initiated. Source uses strict `remote_n > local_n`. This checks current channel correctness, not future R55 behavior.

**Release constraints by evidence and proportional rigor:** Windows installed gateway Status PASS but running=false, console Missing, default IPv4 route still local Ethernet; no whole-PC tunnel/leak PASS. Linux native `warp-cli status` requires explicit owner acceptance of WARP Terms, `sudo -n` fails, default route remains Wi-Fi, Tailscale Running; no ToS or root changes. Android/iOS VPN cores remain intentionally unlinked/fail-closed pending functional packet forwarding and Apple entitlements. Repo `THIRD_PARTY_NOTICES.md` identifies bundled upstream notices/third-party obligations, but root FreeNet Hub LICENSE is absent; owner source rights and redistribution decision remain OPEN, absence alone not automatic prohibition. Do not blindly publish or choose license. Bytewise validation of all mutable ~7GiB browser profiles UNPROVEN, though settings and two original profile dirs physically preserved. Physical downgrade of healthy R54 is deferred because a hosted isolated exact rollback PASS exists; unnecessary disruptive rerun rejected.

**Roadmap:** ACCEPTED source/CI and owner Windows R54 scoped physical upgrade → ACCEPTED exactly one correctly SHA-backed unpublished Draft → ←CURRENT V461 knowledge and release decision → OPEN owner rights/public Windows scoped release, Windows/Linux native full-device and Linux ToS/sudo, mobile Android/iOS functional forwarding and Apple signing → FINAL UNPROVEN. Exact next action: finish V461 evidence CI and merge; obtain rights determination and scope-restricted release decision, then continue remaining platform-critical gates.


## 2026-10-15 — V462 immutable Linux R21 continuity in one unpublished R54 Draft

**Previous accepted:** V461 release evidence PR #63 exact-head CI two runs 10/10 PASS, merged `4529690e223183394357ed182f3352ac66c3fa04`. Owner Windows R54 physical 4.3.10 installed and CFON HTTPS204. Owner Linux R21 4.2.0-linux.21-r54 CFON HTTPS204 and installed file manifests PASS. Stable public Latest remains R53; existing R54 release ID 412991602 is still DRAFT=true/PRERELEASE=true.

**One release continuity mutation:** GitHub REST `/releases/latest` explicitly returns the latest *published full* release, not Draft/Prerelease (official GitHub docs). Linux updater filters latest release assets for exact `_Linux_RN.zip`; publishing Windows R54 without a Linux asset would remove Linux upgrade visibility. Instead of rebuilding/republishing different Linux code, the exact already public Linux R21 ZIP was SHA-pinned (`82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A`, 254,833 bytes) and added to the SAME unpublished R54 Draft using `gh release upload` *without* clobber. Prestate verified three older exact assets; poststate REST verified same Draft ID/target, draft/prerelease true, exactly four assets, unchanged old three IDs/hash/size, R21 ZIP correct, release notes amended and public Stable untouched. Owner installation unchanged. Private prestate and transaction receipt stored in Windows project `.git/maintenance/FNH_V462_CROSS_PLATFORM_LINUX_R21_CONTINUITY`; public evidence in `evidence/V462_LINUX_R21_RELEASE_UPDATER_CONTINUITY_20261015.json`.

**Evidence and regression:** Existing Linux R21 ZIP integrity `testzip` PASS, 24/24 manifest content hashes/sizes PASS, NO bundled runtime binary, isolated R20→R21 fake-HOME upgrade PASS (five fixtures retained, rejects corrupt installer exit75). Linux installed `update_check()` reports R21 local=21 remote=21 updateAvailable=false. A new isolated external regression `tests/test_v462_mixed_release_update.py` mocks future latest with Windows R54 and Linux R21 assets: R21 no same-revision update, R20 recognizes R21, Windows EXE not ranked as Linux asset and missing Linux ZIP fails closed. Original immutable Linux R21 packaged `crossplatform/linux/test_update_revision.py` was retained byte-identical: an initial direct edit caused cross-platform manifest FAIL, so the added test was moved into repository `tests/`, and CI linux-static runs it without repackaging old R21. Existing tests retained. Isolated regression PASS; GitHub exact-head CI still required. Neither Linux owner nor Windows owner was reinstalled.

**Decision rationale/benchmarks:** GitHub official API definition https://docs.github.com/en/rest/releases/releases#get-the-latest-release, official release upload https://cli.github.com/manual/gh_release_upload. Cloudflare WARP official Linux setup requires separate owner registration/connection (https://developers.cloudflare.com/warp-client/get-started/linux/); don't silently accept ToS/sudo. For future Android and iOS real full-device tunnels, use Android VpnService.Builder packet routing and Apple NetworkExtension NEPacketTunnelProvider with entitlements (https://developer.android.com/reference/android/net/VpnService.Builder, https://developer.apple.com/documentation/networkextension/packet-tunnel-provider). CI mocks, Android build and iOS simulator alone are NOT owner real packet forwarding validation. No new guard beyond one regression for a concrete release failure mode.

**Roadmap:** accepted owner Windows R54 browser CFON with tested in-place update/settings retention → accepted R54 single corrected unpublished Draft → ←CURRENT Linux R21 continuity and V462 evidence CI → OPEN source/binary rights and scoped public R54 release decision; Windows global TUN/route leak tests; Linux WARP owner ToS/sudo, Tailscale coexistence; Android/iOS real packet tunnel and Apple signing → FINAL=UNPROVEN. No percentage without defined roadmap estimate. Exact next: exact-head V462 CI, squash merge and clean temporary audit branches, then owner rights release decision; continue read-only preparations for full-system/mobile gates.


## 2026-10-15 — V463 source-only Tailscale-preserving Windows full-device TUN candidate

**Previous accepted** main `7173e1ae48919e02cbd0355ed5d65bd310196874`; its postmerge CI run `38684206959` 10/10 SUCCESS. Owner Windows R54 4.3.10 and Linux R21 both retain browser-scoped CFON HTTP204; Tailscale/AnyDesk active and owner data unmodified. V462 single Draft retains exactly four assets (R54 Windows exact SHA + frozen R21 Linux exact SHA + CI metadata); public Stable still R53.

**ONE main blocker and proportional change:** Official Tailscale documentation (https://tailscale.com/docs/reference/faq/other-vpns) identifies coexisting VPN routing/firewall conflicts and gives split-tunnel exclusions `100.64.0.0/10` and `fd7a:115c:a1e0::/48`. Existing full-device Windows sing-box `auto_route` + `strict_route` Gateway lacked these explicit exclusions; this is a *probable disruption risk*, not previously physically confirmed. Official sing-box TUN route-exclude API https://sing-box.sagernet.org/configuration/inbound/tun/ supports narrow CIDR bypass. `gateway/generate_config.py` PC_TUNNEL now appends both ranges exactly once for WARP, NODE and WireGuard profile, preserving existing warp-plus endpoint exclusions. CONSOLE_ONLY unchanged; the explicit trade-off is that any traffic to the whole CGNAT /10 range uses bypass (not covered by global tunnel). Gateway 17-file manifest and only its release metadata hash plus public manifest were re-sealed. **Existing installed R54 binary was NOT replaced** and no original SHA relabeled.

**Verification:** Gateway unit tests 19/19 PASS, including dedicated PC WARP/NODE/profile+CONSOLE compatibility, installed sing-box `check -c` returned 0 for three generated fixture configurations, security scan/public manifest/release metadata verification PASS, no live route/DNS/firewall mutation. Windows Gateway Status current `running=false`, OS default route Ethernet, Wintun adapters 0; remote Commander Windows process `Elevated=false` and `Require-Admin` for StartPc is an AUTHORITY GATE. Tailscale exit-node conflicts, Windows DNS WFP strict_route and actual direct AnyDesk survival across new PC_TUNNEL still **UNPROVEN**. Avoid bypassing UAC, adding persistent privileged background tasks or changing current functional CFON without elevated maintenance+independent timed recovery.

**Method and open roadmap:** Tailscale official other-VPN FAQ, sing-box TUN official 1.14 DNS/strict-route docs and Microsoft UAC official docs are method authorities. ←CURRENT V463 exact-head CI source gate → elevated owner-approved physical Windows PC_TUN start/stop with authenticated independent recovery, DNS IPv4/IPv6 route/no-leak and Tailscale preservation → Linux native WARP ToS/root/Tailscale coexistence → Android/iOS real packet forwarding and Apple signing → owner rights/public release decision → FINAL=UNPROVEN. Reuse `evidence/V463_TAILSCALE_SAFE_PC_TUN_ROUTE_20261015.json` for limitations, source versions and citation rationale.


## 2026-10-15 — V464 full-device Gateway owner preflight and remote recovery (read-only)

**Previous accepted:** V463 source hardening [PR #65] squash commit `7257efd982a1b585f23630483eaf3fceff083c74`, postmerge Actions run `38690509266` **10/10 SUCCESS**. Windows and Linux project source trees clean at this SHA. Actual owner Windows remains *installed* R54 4.3.10, CFON connected, HTTPS204; Linux installed R21 manifest and CFON HTTPS204. R54 remains an UNPUBLISHED four-asset Draft and R53 public Latest unchanged.

**Authority read-only findings:** Official installed Windows `gateway/preflight.ps1 -Mode PC_TUNNEL` returned `elevated=false`, `singBoxPinned=true`, `projectTunExists=false`, `gatewayOwnerExists=false`, Ethernet default uplink. Installed Gateway generator SHA `A417D5C90FE2F5E37B3B32538576930E9E9214E64E520863382E67A37ED90827` and manifest SHA `3239178A...` do **NOT** match V463 source generator SHA `F17394E38F0F5E80321982EFC9A438988BBC8E8154E5DC35A079E3BE2449B1B6` and source gateway manifest SHA `440BFCE8...`. Thus GitHub source merge **did not** promote V463 into the installed Gateway, and live tests against current files cannot claim the Tailnet route fix is present. No blind source copy into a released package.

**Recovered independent control without touching CFON:** Initial authenticated Linux→Windows AnyDesk session had ended (no established TCP7070); Tailscale direct ping succeeded. Started existing Linux AnyDesk GUI to existing tailnet peer; Linux trace then reported authenticated Session started and established TCP7070, Windows observed one TCP7070 connection; user R54 CFON stayed connected, no route, DNS, service or OS privilege mutation.

**New DNS-critical-path risk (Probable, not a physical failure):** Tailscale Windows had no active exit node, but 67 of 68 NRPT policies matched Quad100. Tailscale official Quad100 (https://tailscale.com/docs/reference/quad100) is the MagicDNS local resolver on 100.100.100.100:53. sing-box official TUN docs (https://sing-box.sagernet.org/configuration/inbound/tun/) state Windows `dns_mode=hijack` with `strict_route` blocks off-TUN port-53 traffic. V463 excluded Tailscale routes 100.64.0.0/10 and fd7a:115c:a1e0::/48, but **that alone cannot prove MagicDNS survival under the WFP DNS guard**. Per Tailscale official coexistence guidance (https://tailscale.com/docs/reference/faq/other-vpns), do not operate with a Tailscale exit node or blindly enable a second route/firewall-altering VPN.

**One V464 audit, no feature mutation:** Evidence `evidence/V464_OWNER_GATEWAY_READINESS_20261015.json` separates raw observations, confirmed tests, probable DNS risk, missing admin and installer promotion gates. Minimum next physical controls: V463-inclusive SHA-pinned installer candidate with isolated upgrade+rollback test, explicit elevated maintenance/UAC, independently authenticated recovery and bounded rollback, then actual IPv4/IPv6 TCP/UDP/DNS/MagicDNS + tailscale + original CFON restoration tests. Native Linux WARP ToS+sudo, Android/iOS forwarding and Apple signing, code/third-party rights and public Stable decision remain OPEN. Do **not** label full-device FINAL accepted. Roadmap ← CURRENT owner full-tunnel packaged readiness and elevated control authority; exact next action is build/validate the V463-inclusive package, followed by user-approved supervised elevated field test.


## 2026-10-15 — V465 private V463-inclusive R54 installer candidate, hosted release-acceptance regression

**Previous accepted** source and owner audit: main `66e439ebcbe73ebb3b06d764d9cd5eefb236057d`, V464 PR66 exact-head two runs 10/10 PASS and postmerge `38692415207` 10/10 PASS. Windows R54 4.3.10 and Linux R21 browser-scoped CFON remain HTTPS204; Tailscale/AnyDesk running. Single public Stable still R53; four-asset R54 Draft stays unpublished. Windows installed R54 Gateway is still older than V463 source and non-admin PC_TUN live tests remain blocked.

**ONE packaging change objective:** Produced a *private dry-run* Inno installer by staging exact accepted R54 base `e4112be36d6cce97863c59a5dbe6a5d0bcdf5786` + unchanged V458 bounded-wait installer helper SHA `98BD0A...`, plus 17 exact V463 gateway sources and manifest SHA `440BFCE8...` from accepted main. New private review filename `FreeNetHub_4.3.10_R54_V465_GATEWAY_REVIEW_DO_NOT_RELEASE.exe`, SHA-256 `3FF751472142340828F0CA2193A344E2BC878EEF25F831B9CE0E9CCD821129E1`, 24,268,761 bytes, Authenticode NotSigned. Private stage `<private project .git>/maintenance/fnh-r54-v465-tun-dryrun`. Original R54 Draft binary SHA `6D3F46C9...` remains distinct/unchanged; **no owner runtime, system network or public release change**. Offline compiler success does not validate in-place installation or Tailscale DNS coexistence.

**Minimal hosted verification** for this exact source recipe: new isolated `tests/prepare_v465_gateway_review.py` checks exact gateway manifest, 17 file bytes/hashes, and stages the R54 candidate with a unique DO_NOT_RELEASE filename and updated package-local gatewayManifestSHA. Existing tested R54 upgrade/rollback harness has an **opt-in only** `-PrivateGatewayReview` path, preserving default R54 behavior, and checks installed Gateway 17-file manifest chain alongside single AppId, settings/fixture preservation and explicit R53 rollback. Dedicated `.github/workflows/v465-private-gateway-review.yml` runs fresh and upgrade jobs on separate ephemeral Windows runners, archives only SHA receipts, not a public binary. CI outcome PENDING until exact-head results.

**Failure prevention captured:** Initial private one-shot wrapper failed before writing the release metadata (bad PowerShell `WriteAllText` argument count); three restricted resume attempts stopped on an incorrectly evaluated inline native-command SHA guard despite actual hashes matching. Read-only stage audit proved exact SHA, source tree and 17 files; Microsoft operator precedence documentation motivated precomputing each native Git output in separate variables. Guarded resume then compiled successfully once. Repeated mutation retries prevented; do not auto rerun, regenerate or overwrite accepted release assets.

**Roadmap:** V463 Gateway route exclusions SOURCE PASS → V464 installed Gateway authority/MagicDNS baseline + recovery PASS read-only → ←CURRENT V465 privately built Gateway-inclusive candidate / disposable hosted fresh+upgrade/rollback CI → OPEN newly versioned updater-visible owner installation with elevated and independent recovery → OPEN Windows full-device packet, route, IPv4/IPv6, DNS/Quad100, Tailscale coexistence, stop/rollback → OPEN Linux native WARP user ToS/sudo, Android/iOS real forwarding and Apple entitlement → OPEN owner rights and public Stable release → FINAL UNPROVEN. Verification != live validation. Sources: Inno Setup command line, PrepareToInstall/exit code docs, Microsoft PowerShell operator precedence, sing-box TUN and Tailscale official reserved IP/DNS.


**V465 hosted exact-binary verification delta (2026-10-15):** First run `38696556232` completed 2/2 disposable Windows private candidate jobs PASS; default R54 baseline hosted run `38696556168` separately 2/2 PASS. Downloaded and SHA-validated both private test receipts into owner private project `.git/maintenance/FNH_V465_HOSTED_RECEIPTS_20261015`. However, SHA of fresh binary `CA18D7D9...` (24,267,316 bytes) differs from SHA of upgrade+rollback binary `2BEF1D4D...` (24,267,315 bytes), and local offline candidate SHA `3FF75147...` also differs: **Inno binaries are not proven byte-reproducible across builds**. Do not claim one specific binary passed both jobs or promote either SHA. To close exactly that gap without adding redundant install gates, extended only the opt-in disposable `-PrivateGatewayReview` upgrade path: after its R53→private R54→R53 rollback and selected owner fixture PASS, R53 is silently uninstalled in the ephemeral runner, registry absence verified, only the named disposable runner-temp install directory removed, then that **same compiled R54 review binary** is freshly installed and fully manifest checked. CI receipt now exposes `sameExactBinaryFreshAndRollbackValidated`; new hosted run PENDING. No owner-installed binary or repo stable release modified.


## 2026-10-15 — V466 reconcile accepted V465 CI and physical authority

Previous accepted main `19aded55745cb8d7396a383eabdbefc87cc0c319`; GitHub V465 postmerge run `38698020583` **10/10 PASS**, hosted private Gateway review `38697122720` **2/2 PASS**. In the *upgrade runner*, exactly ONE compiled binary passed R53→private R54→R53 rollback plus fresh install. The earlier V465 Brain sentence saying same-binary CI PENDING is superseded. The private Windows staged review binary SHA `3FF751472142340828F0CA2193A344E2BC878EEF25F831B9CE0E9CCD821129E1` differs from CI fresh SHA `CF0ADB1ECA1B2B465DC1BCA2B3B71D0AB35CAB153972BC96419CF24A9DDDE95D` and CI upgrade SHA `E873C624A5DE366DBED78F66E41282E49E8938410376EAFAFE02423AC0DDFC43`. They share the accepted V463 source/17-file gateway manifest, **not exact executable bytes**; do not present the local copy as exact CI-tested. CI archives receipts, not installer binary.

Windows owner still on installed R54 scoped CFON HTTPS204; Linux owner R21 scoped CFON HTTPS204. Windows current session has non-elevated token and no FreeNet Hub privileged task was found; similarly named privileged scheduled recovery task belongs to another gateway and was **not run or modified**. Existing installed Gateway still predates V463. Per official Tailscale Quad100 (https://tailscale.com/docs/reference/quad100) and sing-box Windows strict-route DNS docs (https://sing-box.sagernet.org/configuration/inbound/tun/), Tailscale route exclusions alone do not prove MagicDNS survival; previous owner pre-TUN DNS baseline passed but DURING/AFTER TUN remain UNPROVEN. No Windows network mutation, installation or public release promotion occurred. `evidence/V466_READ_ONLY_FIELD_AUTHORITY_20261015.json` is the reusable fact/authority record.

Roadmap: ACCEPTED V465 source/hosted CI and scoped owner browser internet → ←CURRENT exact candidate provenance and supervised elevated Windows field maintenance gate → OPEN actual TUN traffic + IPv4/IPv6/UDP/DNS/Quad100/Tailscale rollback tests; Linux native WARP ToS/sudo; Android/iOS functional packet forwarding and Apple signing; original-source/third-party distribution rights and public Stable decision → FINAL=UNPROVEN. Exact next: supervised Windows elevation and safely rollbackable field transaction with independent authenticated recovery; no claim of physical full-PC PASS beforehand.
