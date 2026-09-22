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

The v4.2.0 tag and published release remain the accepted release authority, but GitHub currently reports the release as `immutable=false`; do not treat server-enforced release immutability as proven. Current `main` contains post-release hardening changes.

On Ubuntu 24.04.4 under WSL, Linux static checks, source install, Tk UI smoke, and Tor runtime passed. Direct Tor, Snowflake, and obfs4 each reached bootstrap 100%, carried HTTPS through the managed local SOCKS path, and stopped cleanly. Stale FreeNet Hub-owned listeners are recovered only after executable + command-line ownership proof. Real bridge material is runtime-only and is not stored in the public source tree.

Cloudflare WARP on native Ubuntu 24.04.5 is runtime accepted: baseline warp=off, explicit connect produced warp=on and YouTube 204, then explicit disconnect restored route, DNS and disconnected status. The sanitized evidence is in `evidence/LINUX_NATIVE_420_WARP_PUBLIC_ACCEPTANCE.json`. Android 4.2.0 has an evidence-backed clean debug build with SDK 35/JDK 17/Gradle 8.9 and a valid v2 debug signature; its VpnService shell remains intentionally fail-closed because the packet-forwarding core is not linked, so this is not Android VPN runtime acceptance. iOS metadata is aligned to 4.2.0 and its static fail-closed gate passes: the Packet Tunnel extension point and entitlement are present, while startTunnel rejects with coreNotLinked and does not configure tunnel network settings. Its forwarding core, macOS/Xcode build, Apple signing/provisioning and device runtime remain open gates.

## Security boundary

Runtime identities, private profiles/keys, bridge files, browser state, local dependency paths and raw private evidence are excluded from Git history by construction. See SECURITY.md.
