# FreeNet Hub 4.3.9 — public desktop release

FreeNet Hub controls connectivity on Windows and Linux with explicit Browser, Full System, and Console capabilities. Availability differs by provider and platform.

## Installation authority

**Latest official release:** https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.9-r53-windows-stable

### Windows R53 (v4.3.9) — public

- Asset: `FreeNetHub_4.3.9_R53_Setup.exe`
- SHA-256: `34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2`
- Release revision: `4.3.9-r53-inno-root-guard`.
- Upgrade: R51/R52 may upgrade in place under the original Inno AppId only when the registered uninstall root agrees with the selected existing installation and the safe-upgrade preflight passes. Conflicting canonical and temporary install roots **fail closed before file replacement or provider shutdown**; they are not automatically merged or deleted.
- Verified: exact public-main commit `17daff34805b82bcae0c6e8d5e6cbed6258c50ff` passed [postmerge CI 10/10](https://github.com/GOD13emad/FreeNetHub/actions/runs/38521651247), including fresh Windows install, R51/R52 upgrade, pinned rollback, data/settings preservation, split-root denial, Android/iOS simulator runtime and virtual acceptance.
- Live Windows R51 `UpdateCheck` independently discovered public R53 and its SHA-256 with `updateAvailable=true`, without disconnecting an active CFON listener. **This does not constitute installing R53 on that owner host.**
- The Windows installer is **unsigned by publisher choice**. Windows SmartScreen or Smart App Control may warn or block it. Do not disable security protections merely to install.

### Linux R20 — public

- Asset: `FreeNetHub_4.2.0_Linux_R20.zip`
- SHA-256: `5973D721EC2D93F7D500187EBC9BB4A5CA06AD73A937BC9AAD936E7C1D745D3B`
- Accepted installed revision: `4.2.0-linux.20-r47`.
- Independent owner-host check (2026-10-14): all 9 installed manifest hashes PASS; HTTPS through the local CFON SOCKS5 proxy returned 200; the physical default route and Tailscale were preserved.
- **Browser-scoped CFON is not whole-system VPN coverage**. A DNS-leak-free Linux full-system VPN remains unverified.

### Windows R52 and R51 — previous releases

- R52 (`4.3.8`) and R51 (`4.3.7`) remain historical/rollback authorities, not the Latest Windows installer. Published assets and SHA-256 digests are retained unchanged.
- Do not force an R53 upgrade while a provider listener is active or if two installs share one AppId with conflicting uninstall history. Preserve user data and use controlled recovery with verified rollback.

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

The public Windows R53 and Linux R20 products are accepted only within the scopes verified by their own tests. Linux whole-system DNS-leak prevention, unsigned-Windows compatibility with Smart App Control, user-host installed R53 field GUI acceptance, physical console testing, production mobile forwarding/signing, and interactive Cloudflare challenge/login remain OPEN. A command-line HTTP 403 with cf-mitigated: challenge is not proof of a broken proxy or successful browser login.

No software can promise Internet access if all underlying paths are unavailable.

## Source and release authority

The exact asset names and SHA-256 digests of the official v4.3.9-r53-windows-stable release govern current installation; later source commits may update documentation without rebuilding the published installers. The repository has **no project-wide software license** (see `THIRD_PARTY_NOTICES.md`); third-party licenses are not a license grant for FreeNet Hub's own source. License choice is an owner/legal gate.

See SECURITY.md, issues #30/#32 and evidence/ for accepted and outstanding proof.
