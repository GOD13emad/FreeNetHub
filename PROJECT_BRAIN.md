# PROJECT BRAIN — Open Internet Gateway / FreeNet Hub

Status: CURRENT
Brain version: R28-local-accepted-2026-09-28
Authority: working tree R28 candidate + evidence/R28_FINAL_ACCEPTANCE_20260928.json
Installer: FreeNetHub_4.2.0_R28_Final_Setup.exe
Installer SHA-256: 2AA91D849A513A21D3BF9903F8E72FFB6A184D378FB357CE4FA7A9D6F7EB0073

## Objective / DoD
A self-contained Windows gateway with browser-only default, explicit WARP full-system mode, separate console gateway, provider-specific connection UI, refreshed/tested public node pool, real path metrics, safe update and evidence-backed install/uninstall.

## Roadmap
1. Browser identity/proxy baseline — Completed.
2. Full-system WARP with rollback — Completed.
3. Separate console gateway software path — Completed; physical-console field gate remains external.
4. Strict country + Node Hub — Completed.
5. R28 provider-specific UI / metrics / refresh / self-update — Completed.
6. Exact final installer clean-install/upgrade/uninstall/live validation — Completed.
7. Public-tree/security verification — Completed.
8. Hosted CI + GitHub R28 release — ← CURRENT.

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
Commit and push the security-clean R28 candidate, validate hosted CI on that exact commit, then publish the exact accepted R28 installer asset.

## HISTORY
- R28: provider-capability UI, 10-source/5-family public refresh, TTL/stale pruning, real Ping/Download/Upload metrics, bounded diverse node benchmarking and GitHub self-update.
- R28: transport compatibility expanded and fail-closed semantics strengthened.
- R28: concurrent build supersede prevented with source-freeze guard.
- R28: uninstall race root-caused to a finishing background engine job and fixed with exact-job cancel/drain plus narrow retry.
- R28: exact final installer qualified and production-upgraded with state preservation and installed live validation.

- 2026-09-28 R28: final public security/integrity gate PASS; no sensitive path/token hits and all public/release manifests verified.
