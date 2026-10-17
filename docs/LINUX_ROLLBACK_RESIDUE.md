# FreeNet Hub Linux — R24 → R21 rollback residue

The public R21 and CI-tested R24 ZIPs remain immutable. Reinstalling frozen R21
after R24 restores R21's entry points and installed integrity hashes. However,
R21's older installer cannot recognize two added R24 source modules:
selective_tunnel.py and tailnet_cfon_gateway.py. Neither is imported from the
tested R21 launch path, but both remain as orphan source files.

The separate source-repository helper tests/cleanup_r24_rollback_residue.py
offers an explicit, user-local cleanup path. It is not bundled into or applied
by either immutable installer. Its default action is READ ONLY.

From a trusted FreeNetHub source checkout with both approved ZIPs present:

    python3 tests/cleanup_r24_rollback_residue.py \
      --app-home "$HOME/.local/share/FreeNetHub" \
      --r21-package delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R21.zip \
      --r24-package delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R24.zip

Only after the actual R21 installation is fully idle and the output identifies
exactly the two frozen R24 module hashes, append --apply to quarantine those
modules. This tool refuses active CFON, selective routing, owner proxy
listeners, tailnet sharing, changed modules, symlinks, unknown owner state,
invalid receipts and untrusted frozen package bytes. It never changes DNS,
routes, NetworkManager, Tailscale, system proxy or any privileged service.

Quarantine is reversible under the app's private directory
.r24-to-r21-orphan-quarantine/, with a package-SHA-pinned receipt. No other
user state or R21 runtime is deleted. To explicitly restore quarantined
source files while R21 remains idle, use the same command with --restore.
Repeating either action reconciles an existing receipt; unknown outcomes
are refused.

This helper does not install R24 and does not claim real physical rollback
acceptance. Its fully isolated HOME regression is part of Linux CI.
