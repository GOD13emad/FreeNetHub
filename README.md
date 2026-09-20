# FreeNet Hub

FreeNet Hub 4.1.2 is an explicit-connect desktop connectivity control center. The accepted Windows scope is browser/proxy routing, not a system-wide VPN.

## Current evidence-backed status

Windows: runtime accepted for browser/proxy scope. WARP, GOOL, CFON and Tor HTTPS probes passed. Standalone EXE, Start Menu, taskbar icon, tray restore and single-instance passed.

Linux: source/static validation passed; runtime provider acceptance remains open.

Android: native VpnService integration/build pack. The forwarding core is intentionally not linked, so no TUN is established.

iOS: native NEPacketTunnelProvider integration/build pack. It fails closed until forwarding core, signing and entitlement runtime gates are completed.

The current Windows acceptance authority is in evidence/STATE_VERIFY_UX_412_ACCEPTANCE.json. Version 4.1.2 also fixes connection-state verification: verifying a disconnected managed path now reports NOT_CONNECTED without probing a dead local proxy or displaying failed-request time as latency. Full-system TUN, system kill-switch, DNS/IPv6 leak capture, UDP/game acceptance, long soak, and mobile runtime gates remain explicitly unproven/open.

## Windows

Prerequisites: PowerShell 7, Python, Chrome, a pinned warp-plus.exe, and a Tor bundle containing tor.exe, lyrebird.exe, and a working torrc. Provider binaries are not redistributed by this repository.

On a machine that already has the project FreeTunnelLab provider bundle in the default location, run:

    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-Windows.ps1

If provider binaries are elsewhere, pass their paths to Setup-WindowsDependencies.ps1 first. The generated app/dependencies.json contains machine-local paths and hashes and is intentionally ignored by Git.

The UI is launched through FreeNetHub.exe. Its PowerShell backend is hidden. Opening the UI does not automatically connect a provider.

## Cross-platform source

See crossplatform/README_FA.md and crossplatform/common/METHOD_EVIDENCE.md. Android/iOS packages are deliberately fail-closed until a real packet-forwarding core is integrated and runtime-tested; they are not presented as signed production VPN apps.

## Safety and state model

FreeNet Hub owns only processes it can prove belong to pinned binaries and project-specific command lines. Provider operations are bounded, cleanup is verified, and the accepted Windows run showed no global route/DNS/WinINET proxy drift before versus after the test.

Runtime state, browser profiles, bridge material, logs, job files, local dependency paths, and backups are excluded from the public repository.
