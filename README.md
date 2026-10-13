# FreeNet Hub 4.3.8 — public desktop release

FreeNet Hub controls connectivity on Windows and Linux with explicit Browser, Full System, and Console capabilities. Availability differs by provider and platform.

## Installation authority

**Latest official release:** https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.8-r52-windows-stable

### Windows R52 (v4.3.8) — public

- Asset: `FreeNetHub_4.3.8_R52_Setup.exe`
- SHA-256: `A48F689B22940C9D752FADB6372B849948B18192F3A30D4FC3971C15827F9883`
- Release revision: `4.3.8-r52-stale-node-health-ttl`.
- Upgrade: replaces R51 in place under the same Inno AppId when its safe-upgrade preflight passes; an active FreeNet Hub provider listener blocks upgrade to avoid breaking an ongoing connection.
- Verified: hosted CI run [#363](https://github.com/GOD13emad/FreeNetHub/actions/runs/38477116892) completed SUCCESS on exact public main commit `0a89fbbab80e603191040471531d6ef1e287df26`, including Windows installer tests and cross-platform virtual acceptance.
- This installer is **unsigned by publisher choice**. Windows SmartScreen or Smart App Control may warn or block it. Do not disable security protections merely to install.

### Linux R20 — public

- Asset: `FreeNetHub_4.2.0_Linux_R20.zip`
- SHA-256: `5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B`
- Accepted installed revision: `4.2.0-linux.20-r47`.
- Independent owner-host check (2026-10-14): all 9 installed manifest hashes PASS; HTTPS through the local CFON SOCKS5 proxy returned 200; the physical default route and Tailscale were preserved.
- **Browser-scoped CFON is not whole-system VPN coverage**. A DNS-leak-free Linux full-system VPN remains unverified.

### Windows R51 — previous release

- R51 (`4.3.7`) remains historical/rollback authority only, not the latest public installer.
- Do not force an R52 upgrade while a provider listener is active. The installer intentionally fails closed to protect the session.

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

The public Windows R52 and Linux R20 products are accepted only within the scopes verified by their own tests. Linux whole-system DNS-leak prevention, unsigned-Windows compatibility with Smart App Control, user-host installed R52 field GUI acceptance, physical console testing, production mobile forwarding/signing, and interactive Cloudflare challenge/login remain OPEN. A command-line HTTP 403 with cf-mitigated: challenge is not proof of a broken proxy or successful browser login.

No software can promise Internet access if all underlying paths are unavailable.

## Source and release authority

The exact asset names and SHA-256 digests of the official v4.3.8-r52-windows-stable release govern installation; later source commits may update documentation without rebuilding the published installers. The repository has **no project-wide software license** (see `THIRD_PARTY_NOTICES.md`); third-party licenses are not a license grant for FreeNet Hub's own source. License choice is an owner/legal gate.

See SECURITY.md, issues #30/#32 and evidence/ for accepted and outstanding proof.
