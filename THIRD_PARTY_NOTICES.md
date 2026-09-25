# Third-Party Notices

FreeNet Hub uses or bundles third-party software. Third-party components remain subject to their own license terms.

## warp-plus

- Upstream project: `bepass-org/warp-plus`.
- Distribution model in R16 Clean: the pinned `warp-plus.exe` runtime is bundled inside `windows/runtime/WarpPlusFast/` so the installed application does not depend on an external legacy folder.
- The accompanying upstream `LICENSE` and `README.md` are preserved next to the binary.
- FreeNet Hub verifies the bundled binary SHA-256 before accepting it at install/runtime setup.

## Tor / lyrebird runtime

- Distribution model in R16 Clean: the minimal Tor runtime needed by FreeNet Hub is bundled under `windows/runtime/TorSnowflake/bundle/`.
- The bundle contains the required Tor executable, lyrebird pluggable transport, GeoIP data, and upstream notice files needed by this distribution.
- Upstream notice/license material is preserved under `windows/runtime/TorSnowflake/bundle/docs/`.
- Build-only or unused legacy executables such as `tor-gencert` and `conjure-client` are intentionally not shipped in R16 Clean.

## sing-box

- Upstream project: SagerNet/sing-box.
- Pinned runtime version used by the Console Gateway setup: 1.14.0.
- Upstream license: GNU General Public License, version 3 or (at your option) any later version (GPL-3.0-or-later).
- Integration model: `gateway/Setup-GatewayCore.ps1` downloads the pinned upstream Windows release when needed, verifies the archive and binary SHA-256 values, and installs the validated binary into the local FreeNet Hub runtime directory.
- Distribution boundary: the current FreeNet Hub installer does not embed the sing-box binary.

## FreeNet Hub project license

This notice does not grant a license to FreeNet Hub's own source code. The repository currently does not declare a project-wide software license.
