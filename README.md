# FreeNet Hub 4.2.0

FreeNet Hub is a multi-method connectivity control center with explicit Browser, Full System, and Console scopes, pre-connect measurement, fail-closed provider boundaries, and rollback-aware Windows network mutation.

## Evidence-backed Windows status

- R37 five-tab UI (Dashboard / Methods / Nodes / Tools / Settings): accepted from the installed product.
- Browser, Full System, and Console capability boundaries are explicit; unsupported paths remain fail-closed.
- Method-card Connect and pre-connect measurement actions invoke real backend operations.
- Node refresh fetch/parse/merge is separated from explicit endpoint Test All.
- Direct base-path speed measurement and browser WARP benchmark: accepted.
- Full-System WARP through the official gateway path: accepted; update/node retrieval during TUN is proven bound to the pre-TUN base route.
- Stop/rollback removes FreeNet Hub TUN/session state and restores the accepted route.
- Exact R37 installer lifecycle: install exit 0, runtime bootstrap PASS, 17 app + 17 gateway parity PASS, five UI smoke tabs PASS, route unchanged.
- Hosted CI #99: Windows, Linux, Android build/emulator fail-closed runtime, iOS static/simulator runtime, console virtual E2E, virtual signing, and aggregate virtual acceptance all PASS.
- Physical console/game/country field E2E and publicly trusted Windows Authenticode remain explicit external gates.

Current acceptance evidence is in `evidence/R37_WINDOWS_FINAL_ACCEPTANCE_20260929.json` and `evidence/R37_PUBLIC_RELEASE_ACCEPTANCE_20260929.json`.

## Install on Windows

The recommended path is `FreeNetHub_4.2.0_R37_Final_Setup.exe` from GitHub Release `v4.2.0-r37-final`. Its accepted SHA-256 is `35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64`; verify it against `SHA256SUMS.txt`.

The installer does not auto-connect networking. Network mutation is explicit and elevated only when Full PC or Console Gateway actions are requested.

Gateway core provisioning uses pinned sing-box 1.14.0. Browser provider binaries/configs such as WARP/Tor/GOOL/CFON are not redistributed by this repository; missing optional providers remain unavailable/fail-closed rather than silently falling back to DIRECT.

For source installation:

    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-Windows.ps1 -InstallMissingRuntime

## Cross-platform source

GitHub Release `v4.2.0-r37-final`, targeting commit `45e21a1bc64aefaf3276751754c0f4f4fd1fb649`, is the accepted public R37 authority. GitHub reports the release as `immutable=false`, so server-enforced release immutability is not claimed.

Native Linux 4.2.0-linux.9-r37 is the current Linux authority on Ubuntu 24.04. The GTK4/Libadwaita product UI now follows the R37 five-section architecture: Dashboard, Methods, Nodes, Tools and Settings. Browser scope has real Node Pool support through app-local hash-pinned sing-box, WARP/GOOL/CFON through app-local hash-pinned warp-plus, Tor/obfs4/Snowflake, Custom proxy and Direct. Node refresh is separated from explicit endpoint Test All; HTTPS proxy-health and throughput are separate gates. Raw/Base64 export, metadata, history, filtering/sorting and bounded batch benchmark are exposed in the UI.

Full-System remains WARP-only on Linux R9; a privileged Full-System Node helper is not claimed without separate CAP_NET_ADMIN/root acceptance. Console Gateway software policy, UUID ownership and rollback remain accepted while physical console DHCP/UDP/game/country validation is external. The installer does not auto-connect networking, verifies installed files through INSTALL.sha256, provisions sing-box 1.14.2 and warp-plus 1.2.6 from their official releases with pinned archive hashes, and reloads only the exact FreeNet Hub UI process. The accepted Linux R9 package is `FreeNetHub_4.2.0_Linux_R9.zip`; its release digest is recorded in the R9 acceptance evidence.

Android 4.2.0 clean build and hosted emulator lifecycle PASS with the VpnService permission flow exercised fail-closed; the production packet-forwarding core/signing remain open external gates. iOS static and hosted simulator build/install/launch/relaunch PASS with the Packet Tunnel extension present and fail-closed while its production forwarding core is unlinked; Apple production signing/provisioning and physical-device runtime remain open gates.

## Security boundary

Runtime identities, private profiles/keys, bridge files, browser state, local dependency paths and raw private evidence are excluded from Git history by construction. See SECURITY.md.


## Licensing and third-party components

This repository currently does not declare a project-wide software license. No license should be inferred from repository visibility alone.

Third-party software retains its own license terms. In particular, the Console Gateway setup can download the pinned upstream sing-box 1.14.0 release at setup time after SHA-256 verification; the sing-box binary is not embedded in the FreeNet Hub installer. See `THIRD_PARTY_NOTICES.md`.
