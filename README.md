# FreeNet Hub 4.3.7

FreeNet Hub is a multi-method connectivity control center for Windows and Linux with explicit Browser, Full System, and Console scopes, pre-connect measurement, fail-closed provider boundaries, rollback-aware network mutation, node management, and online update checks.

## Final desktop install authority

The current public desktop release is **v4.3.7**.

### Windows

Install exactly:

`FreeNetHub_4.3.7_R51_Setup.exe`

SHA-256:

`4CCAE665D9F641BEC3FACF2BFDB908F5E727BDC32F278A91EA2E6C3BFE8208A3`

Accepted product revision: `4.3.7-r51-protocol-expansion-2`.

Fresh owner-host verification on 2026-10-06:
- full regression: **252/252 PASS**
- installed/source RELEASE parity: PASS
- installed/source app manifest parity: PASS
- installed/source gateway manifest parity: PASS
- current update revision: 51 / remote revision: 51 / no update pending

The Windows installer is currently **not publicly Authenticode-signed** because no trusted external signing identity is provisioned. This is an external signing gate, not a desktop runtime defect.

### Linux

Install exactly:

`FreeNetHub_4.2.0_Linux_R17.zip`

SHA-256:

`1646C70FBF2CA3C7EAAC9D6470BEED3D53063D9E5D9FF50A830D0507420C6EA6`

Accepted installed version: `4.2.0-linux.17-r44`.

Fresh owner-host verification on 2026-10-06:
- installed integrity: **9/9 PASS**
- selftest: PASS
- scope policy: PASS
- browser profile: PASS
- console policy: PASS
- private-state permissions: PASS
- Windows/Linux source parity: PASS
- update-revision regression: PASS
- source checkout aligned with Windows on `main`

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

The final desktop release is evidence-backed for the accepted Windows and Linux owner installations. Separate external gates remain for publicly trusted Windows Authenticode, physical console field/game/country E2E, and production mobile forwarding/signing/real-device operation.

No product can guarantee connectivity when every physical/upstream path is unavailable.

## Source authority

Current public source authority: `main` at or after final owner acceptance commit `09b8483851ed900e16784f2ef0cd837ecee90c9b`.

Historical evidence remains in the repository for auditability. Superseded release artifacts are not installation authority; use **v4.3.7** only for new desktop installs.

See `SECURITY.md` and the release evidence under `evidence/` for detailed validation records.
