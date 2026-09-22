# FreeNet Hub 4.2.0

FreeNet Hub is an explicit-connect Windows connectivity control center with browser/proxy modes, an optional full-PC WARP tunnel, and a console-gateway software path.

## Evidence-backed Windows status

- Browser/proxy control surface: accepted.
- Native Windows shell: single instance, Taskbar/Tray identity, Minimize-to-Tray/Restore, no new Windows Terminal/OpenConsole on launch.
- PC_TUNNEL with WARP: runtime accepted from a clean installer. Cloudflare reported warp=on, YouTube returned 204, UDP/STUN passed, and Stop restored the recorded network baseline.
- Installer lifecycle: clean install, runtime bootstrap, app-local pinned sing-box core, fail-closed cleanup, and uninstall passed.
- Console Gateway: WSL2 Linux-router simulation and Realtek USB GbE attach/detach passed. Physical console/game end-to-end validation is still open because the dedicated console link was disconnected during final acceptance.

The sanitized acceptance summary is in evidence/FINAL_420_PUBLIC_ACCEPTANCE.json.

## Install on Windows

The recommended path is the FreeNetHub_4.2.0_FINAL_Setup.exe asset from the v4.2.0 GitHub Release. Verify its SHA-256 against SHA256SUMS.txt.

The installer does not auto-connect networking. Network mutation is explicit and elevated only when Full PC or Console Gateway actions are requested.

Gateway core provisioning uses pinned sing-box 1.14.0. Browser provider binaries/configs such as WARP/Tor/GOOL/CFON are not redistributed by this repository; missing optional providers remain unavailable/fail-closed rather than silently falling back to DIRECT.

For source installation:

    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-Windows.ps1 -InstallMissingRuntime

## Cross-platform source

The v4.2.0 tag and published release remain the accepted release authority, but GitHub currently reports the release as `immutable=false`; do not treat server-enforced release immutability as proven. Current `main` contains post-release hardening changes, including the native Linux desktop line.

Native Linux 4.2.0-linux.5 is software-accepted on Ubuntu 24.04.5. The GTK4/Libadwaita UI is single-instance with explicit minimize/maximize/close controls. WARP safe-trial, token-scoped rollback, UUID-scoped Console Gateway ownership, strict legacy-profile migration, isolated Firefox proxy profile, integrity-checked install and uninstall lifecycle are accepted. AUTO probes Direct Tor for 30 seconds, then falls back to a resistant transport; under the final network condition Direct reached 55% within its 90-second manual window while AUTO fell back to obfs4 and reached bootstrap 100% with HTTPS egress in 38.91 seconds. The remaining Linux field gate is physical-console DHCP/UDP/game/country validation.

Snowflake support is retained and remains fail-closed when no valid runtime bridge is present. Historical WSL acceptance for Direct/Snowflake/obfs4 is preserved. Real obfs4/Snowflake bridge material is runtime-only and is never stored in the public tree. Sanitized native Linux evidence is in `evidence/LINUX_NATIVE_420_PUBLIC_ACCEPTANCE.json`, with WARP-specific evidence in `evidence/LINUX_NATIVE_420_WARP_PUBLIC_ACCEPTANCE.json`.

Android 4.2.0 has an evidence-backed clean debug build with SDK 35/JDK 17/Gradle 8.9 and a valid v2 debug signature; its VpnService shell remains intentionally fail-closed because the packet-forwarding core is not linked, so this is not Android VPN runtime acceptance. iOS metadata is aligned to 4.2.0 and its static fail-closed gate passes: the Packet Tunnel extension point and entitlement are present, while startTunnel rejects with coreNotLinked and does not configure tunnel network settings. Its forwarding core, macOS/Xcode build, Apple signing/provisioning and device runtime remain open gates.

## Security boundary

Runtime identities, private profiles/keys, bridge files, browser state, local dependency paths and raw private evidence are excluded from Git history by construction. See SECURITY.md.


## Licensing and third-party components

This repository currently does not declare a project-wide software license. No license should be inferred from repository visibility alone.

Third-party software retains its own license terms. In particular, the Console Gateway setup can download the pinned upstream sing-box 1.14.0 release at setup time after SHA-256 verification; the sing-box binary is not embedded in the FreeNet Hub installer. See `THIRD_PARTY_NOTICES.md`.
