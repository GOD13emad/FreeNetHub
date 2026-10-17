# FreeNet Hub — Current Public Release: Windows R53 and Linux R21

**Official GitHub Latest release (verified 17 October 2026):** [Free Net Hub 4.3.9 R53](https://github.com/GOD13emad/FreeNetHub/releases/tag/v4.3.9-r53-windows-stable)

Use the exact asset names and SHA-256 values below for **public stable** installations. Newer `main` source code, pre-release builds and owner-only field candidates are **not** automatically public stable installers. [راهنمای نصب فارسی](README_FA.md).

## Windows R53 — Public Stable Installer

- Asset: `FreeNetHub_4.3.9_R53_Setup.exe`
- SHA-256: `34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2`
- Release revision: `4.3.9-r53-inno-root-guard`
- In-place upgrades require a disconnected FreeNet Hub session and a consistent, canonical uninstall/install identity. Conflicting roots or active owned listeners must fail closed rather than silently replace files or modify unrelated state.
- This Windows installer is **not signed with a trusted publisher certificate**. Do not disable SmartScreen, Smart App Control or other security protections to install it.

## Linux R21 — Current Public Package

- Asset: `FreeNetHub_4.2.0_Linux_R21.zip`
- SHA-256: `82305E1A15684662B7711B53A84522122C6A11D618366314D9DD297B3A7FEC1A`
- Accepted installed revision: `4.2.0-linux.21-r54`
- Real owner-host GTK, package-integrity, R20→R21 in-place data-preserving update and browser-scoped CFON were verified in their recorded scope. Original routes and independent Tailscale continuity were preserved.
- R20 remains attached to the same stable release only as an older rollback/reference asset; **it is not the current Linux public version**. Do not force an upgrade during an active tunnel/session.

## Development and Preview Builds — Not the Latest Stable Release

- Windows R54 has separate **Pre-release** listings on GitHub. These are not the official Latest stable installer.
- Windows `4.3.13 R57` has been installed on an owner Windows host and scoped CFON/selective transport tested. That field result does **not** make R57 a stable public installer.
- Linux `4.2.0-linux.24-r57` is a distinct CI-tested preview ZIP. Fresh installation, R21→R24 upgrade and R24→R21 rollback were tested with disposable HOME environments on actual Ubuntu hardware, not by replacing the owner's active R21 CFON installation.
- After rolling back R24 to frozen R21, two inert R24-only modules can remain. Their optional, exact-SHA, reversible quarantine process is described in [Linux rollback residue guidance](docs/LINUX_ROLLBACK_RESIDUE.md). It is not bundled into the frozen R21 public archive or applied automatically.

## Capabilities and Acceptance Boundaries

The desktop product uses Dashboard / Methods / Nodes / Tools / Settings with explicit browser, full-system and console scopes. Supported options across revisions may include AUTO, Node Pool, WARP, GOOL, CFON, Tor/bridges, Custom and Direct. Node import, refresh, health and performance tests, sorting, and revision-aware updates depend on the installed platform, runtime and feature version. **A visible UI option is not proof of end-to-end physical acceptance.**

Recorded CFON HTTP tests establish scoped browser/proxy transport only. Whole-device TUN routing, DNS/UDP leak protection, physical console routing, real Android/iOS forwarding and authenticated Google Cloud access remain separate open gates. An anonymous HTTP 403 changing to a 302/200 via a private tunnel does not establish account authorization or guarantee that every restricted site is usable. No software can guarantee external Internet access if all upstream paths are unavailable.

Native Windows Administrator/root authorization and explicit Cloudflare WARP Terms consent are required when applicable. Do not work around operating-system security dialogs or disable security protections.

## Source, Evidence and Rights

Official asset digests are published as GitHub Release asset metadata; a passing source CI is not interchangeable with installation, publisher signing or hardware acceptance. See `PROJECT_BRAIN.md`, `evidence/`, `SECURITY.md` and `THIRD_PARTY_NOTICES.md` for scoped results and third-party obligations. This repository currently **does not declare a project-wide source-code license**; third-party licenses do not grant a license to the FreeNet Hub project itself.
