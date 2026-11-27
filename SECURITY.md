# Security and privacy

Do not commit runtime state or credentials. This repository excludes machine-local dependency paths, provider identities/private keys, bridge material, browser profiles, jobs, logs, backups, gateway runtime state and local status exports.

## Reporting a vulnerability

Use the [private vulnerability reporting form](https://github.com/GOD13emad/FreeNetHub/security/advisories/new) (Security → Report a vulnerability) rather than a public issue. Include the affected version/platform, impact and a minimized reproduction with redacted diagnostics. Never include credentials, private keys, provider identities, network captures or unredacted runtime logs. If the form is unavailable, request a confidential contact channel without revealing vulnerability details publicly.

## Release and acceptance notes

FreeNet Hub 4.2.0 has evidence-backed Windows software acceptance for browser/proxy operation and WARP PC_TUNNEL. Console Gateway software routing/USB handoff is accepted, but physical console/game end-to-end validation remains open until a console is connected.

The release installer is not Authenticode-signed because no trusted code-signing certificate was available to this project. Verify release assets with the published SHA-256 file.
