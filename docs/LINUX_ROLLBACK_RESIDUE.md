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

The R24-only helper was also physically exercised on the separate MMZ
Ubuntu owner installation: R25 → R24 → R21, exact two-module quarantine,
idempotent apply/restore, and R25 reinstatement all passed while Tailscale,
routes, GNOME proxy and three sampled private files were preserved.
This is **not** permission to interrupt the primary laptop's active CFON.

## R25-exclusive module after rolling back to R24 or R21

A separate, distinct R25 client source module, `tailnet_client_browser.py`,
is not part of the frozen R24 or R21 installer. When reverting from the
CI-tested **R25 preview** to either older version, that module may remain
as an inert orphan. It is **not** covered by the two-module R24 cleanup.

The new `tests/cleanup_r25_rollback_residue.py` helper checks the SHA-256
of all three exact release ZIPs, validates the *currently installed* R21 or
R24 code against its frozen manifest, and accepts only the original,
unchanged R25 module. It is read-only unless `--apply` is explicitly added.

    python3 tests/cleanup_r25_rollback_residue.py \
      --app-home "$HOME/.local/share/FreeNetHub" \
      --r21-package delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R21.zip \
      --r24-package delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R24.zip \
      --r25-package delivery/github_v4.2.0/FreeNetHub_4.2.0_Linux_R25.zip

When the actual installed R21/R24 is idle, a positive dry run is eligible for
`--apply`. The exact R25 bytes move to private directory
`.r25-to-old-orphan-quarantine/` (0700), with a pinned receipt (0600).
`--restore` explicitly reverses that move while the same frozen base
version remains installed and idle. Repeated actions reconcile the receipt.
An unknown/quarantined file, a symlink, an active owner session, a running
R25 Firefox profile, a changed code manifest or a mismatched target revision
causes refusal. Only the single R25 module is affected: the existing R24
quarantine and other user data are not changed.

The old R21/R24/R25 public/previews and their ZIP bytes are immutable. The
new helper is an opt-in source tool, not part of those older installers.
Do not claim general no-leak or full-device tunnel acceptance from these
file-cleanup tests. Full owner-host execution has its own acceptance gate.
