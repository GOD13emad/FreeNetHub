# FreeNet Hub 4.3.7 — public desktop release

FreeNet Hub controls connectivity on Windows and Linux with explicit Browser, Full System, and Console capabilities. Availability differs by provider and platform.

## Installation authority

**Latest public release:** https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.7-r20-linux-cfon-smart

### Windows R51 — public

- Asset: `FreeNetHub_4.3.7_R51_Setup.exe`
- SHA-256: `8283803146E1625A31F0223487A63C05D7B7D9C3D8B59D1A7432D14AB9D4FF11`
- Accepted installed revision: `4.3.7-r51-protocol-expansion-2`
- Read-only live host check (2026-10-09): installed app code integrity 17/17 PASS, CFON browser GitHub HTTP 200 and Tailscale running.
- Public Authenticode publisher signing not established.

### Linux R20 — public

- Asset: `FreeNetHub_4.2.0_Linux_R20.zip`
- SHA-256: `5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B`
- Accepted installed revision: `4.2.0-linux.20-r47`
- Read-only live host check (2026-10-09): installed file integrity 9/9 PASS; CFON Austria browser proxy GitHub HTTP 200 and Google HTTP 204, Tailscale preserved.
- **Browser-only CFON:** a working scoped Riseup UID trial is not evidence of safe all-host Linux VPN. Global DNS leak remains OPEN.

### Windows R52 (v4.3.8) — NOT PUBLIC

PR #34 (https://github.com/GOD13emad/FreeNetHub/pull/34) remains Draft/unmerged. Exact-head CI run https://github.com/GOD13emad/FreeNetHub/actions/runs/37972493989 is 10/10 PASS, including fresh Windows R52, R51->R52 upgrade, and explicitly pinned R52->R51 restore on isolated runners. Public publisher signature and field GUI acceptance remain OPEN. Do not install this candidate as the public release.

## Current capabilities

- Dashboard / Methods / Nodes / Tools / Settings desktop UI
- Browser, Full System, and Console scopes with explicit boundaries
- AUTO, Node Pool, WARP, GOOL, CFON, Tor/obfs4/Snowflake, Custom, and Direct paths where platform/runtime support is validated
- Node imports for SS, VMess, VLESS, Trojan, Hysteria v1/v2, TUIC, AnyTLS, plus validated standalone sing-box JSON imports for ShadowTLS, SSH, Snell, SOCKS, HTTP CONNECT, and Naive
- fail-closed handling for unsupported or unsafe imported local credential/certificate paths
- explicit node refresh, endpoint testing, performance testing, ranking, favorites/pins, metadata, filtering/sorting, and export
- revision-aware online update checks with downgrade protection
- normal application launch does not auto-connect networking

## Validation boundary

The installed and published Windows R51 and Linux R20 products are accepted only for their tested scopes. Linux global VPN DNS-leak prevention, public Windows R52 signing, field GUI validation, physical console acceptance, production mobile forwarding/signing, and interactive Cloudflare challenge/login remain OPEN. A Cloudflare HTTP 403 does not demonstrate login success.

No software can promise Internet access if all underlying paths are unavailable.

## Source and release authority

The immutable asset names and SHA-256 digests of release v4.3.7-r20-linux-cfon-smart govern public installation; source `main` may be newer. The repository has **no project-wide software license** (see `THIRD_PARTY_NOTICES.md`); third-party licenses are not a license grant for FreeNet Hub's own source. License choice is an owner/legal gate.

See SECURITY.md, issues #30/#32 and evidence/ for accepted and outstanding proof.
