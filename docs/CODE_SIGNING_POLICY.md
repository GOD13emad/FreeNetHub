# Code signing policy and evidence record — Windows-first

**Date:** 2026-10-10. **State:** PREPARED / NOT PUBLICLY SIGNED / NO RELEASE PROMOTION.
**Canonical R52 source SHA:** `5f99c56e294ff225479ee0a828bd0e6050e13740`.
**Main release:** R51 remains publicly distributed; R52 must not replace it until all acceptance gates pass.

## Objective and definition of done
Use one **legally verified publisher identity** across first-party projects. Every shipped first-party Windows PE and script with executable behavior must be signed using a publicly trusted code-signing provider, with durable timestamp, exact publisher identity, source-to-artifact provenance and verified SHA-256. Signed setup **and** signed uninstaller must be checked after a safe disposable install. Run Smart App Control on a disposable test machine without changing user protections. Do not modify Tailscale, host routes or DNS for signing tests.

## Current facts and risks
- R52 `RELEASE.json` at the referenced SHA says `R52_UNRELEASED_STAGED_INSTALLER_ACCEPTANCE_OPEN`; its `evidence/V438_R52_STAGED_CANDIDATE_ACCEPTANCE_20261009.json` records `trustedPublisherSigning=OPEN` and an unsigned, local setup SHA256 `7214F7AE832539924B58A6750584079DD859DB5CDA53A59A345B5C9DA3D24DD0`. This is the **pre-sign** hash, not an authentic signed-release hash.
- Current `tests/virtual_codesign.ps1` is a valid negative/cryptographic CI experiment. Its temporary self-signed key is not a public release credential.
- Current `tests/build_v438_installer.ps1` freezes original source hashes and enforces `app/manifest.json` byte hashes. Signing packaged PowerShell or `windows/standalone/FreeNetHub.exe` changes bytes. **Do not sign those tracked sources in place.** First create an isolated signed staging tree, regenerate its content-integrity metadata from final signed bytes and validate the installed runtime against the signed manifest. Existing R52 build cannot be certified without this integration.
- Inno Setup currently has no `SignTool=` configuration. Add a production-only `SignTool` directive and `SignedUninstaller=yes` **after** a real approved signing service exists. Inno can sign Setup and the generated Uninstaller during compilation. Signing only the resulting setup EXE does NOT sign its extracted files or its uninstaller.
- Third-party `winws.exe`, `WinDivert.dll`, `WinDivert64.sys`, `ctrld.exe`, bundled TOR/WARP executables and associated licensing must be inventoried separately. Preserve genuine upstream signatures and record upstream hashes. **Do not re-sign vendor binaries** without an explicit right and a justified chain-of-trust plan. Kernel drivers need driver-specific signing/attestation verification, not ordinary Authenticode `/pa` alone.

## Providers and eligibility — confirmed constraints, not a purchase authorization
1. **Microsoft Artifact Signing Public Trust:** Basic USD 9.99/month (5,000 operations), Premium USD 99.99/month (100,000); USD 0.005 overage. Individual publishers only US/Canada; organizations include the officially listed supported jurisdictions but *not Iran*. Identity validation, Azure subscription and policy-governed cloud signing required. Public Trust required; Private Trust is not a replacement. Short-lived certs renew daily; RFC3161 timestamp mandatory. Use Azure OIDC federation to avoid long-lived CI credentials when eligible.
2. **Commercial CA OV (DigiCert, Sectigo, GlobalSign):** real legal identity and validated organization required under their current product terms; HSM/token-based private-key protection. DigiCert official catalog lists a 12-month OV token offering with USD 840 subscription and own-token/HSM with USD 696 subscription (catalog's dynamic monthly teaser amounts can differ from checkout total). Sectigo says from USD 536.25/yr on five-year subscription; actual 1-year quote and token/shipping must be checked. GlobalSign issues in legally registered organization name only and 366-day certificates. **Verify sanctions/jurisdiction, permitted payments, service geography, and all fees in writing with the CA before paying.** No assumption of eligibility from an Internet location.
3. **SignPath Foundation OSS:** USD 0 for approved eligible projects, publisher shown as **SignPath Foundation** rather than your own unified identity. Only fully compliant open-source source-built artifacts; excludes unapproved upstream binary re-signing and requires approval of each release. It is not a universal publisher certificate. Suitability of FreeNet Hub's bundled network/DPI tools is unverified.
4. **Microsoft Store:** consumer MSIX submissions are re-signed by Microsoft if publisher is legally eligible; externally hosted MSI/EXE submissions still require own CA-trusted signature. Store distribution is not a general signing service for GitHub releases. Individual onboarding fee waived in eligible markets; Iran-specific registration eligibility is not verified.

## Planned pipeline (not yet enabled for public signing)
`source SHA + dependencies/SBOM` -> clean hermetic **BUILD** -> stage own binaries/PS scripts -> **SIGN inner first-party files** -> **TIMESTAMP** -> reconcile embedded integrity manifests and signed bytes -> Inno Setup `SignTool` signs **Setup and Uninstaller** -> **VERIFY** with `signtool verify /pa /all /v`, Authenticode signer/TSA, third-party provenance and SHA256 -> isolated install/upgrade/uninstall + Smart App Control audit/enforcement observation -> release immutable artifact/attestation -> verify downloaded release byte identity.

Use `scripts/signing/Test-PublicAuthenticode.ps1` on the actual distribution tree with a concrete manifest containing exact relative filenames, `ownership=first-party` or `third-party`, publisherSubject (exact X.509 Subject), and for third-party entries `expectedPublisherSubject`. For PE files supply the installed SDK `signtool.exe` path. The verifier rejects unsigned, expired/untrusted, wrong-publisher, missing timestamp, missing artifacts, unsupported types and drivers not subjected to a separate driver gate. A passing verifier is **necessary, not sufficient** for a signed release.

Example manifest schema (replace all illustrative values before actual use):
```json
{
  "schema": 1,
  "publisherSubject": "CN=YOUR REAL LEGAL PUBLISHER, O=YOUR REGISTERED ORGANIZATION, C=XX",
  "artifacts": [
    {"path": "FreeNetHub_4.3.8_R52_Setup.exe", "ownership": "first-party"},
    {"path": "installed/FreeNetHub.exe", "ownership": "first-party"},
    {"path": "installed/app/FreeNetHub.ps1", "ownership": "first-party"},
    {"path": "installed/unins000.exe", "ownership": "first-party"}
  ]
}
```
`installed/` is a **test extraction directory**, not currently present in the source checkout. Do not attempt to verify this example as though it were current release evidence.

### Native HSM/token signing commands — *examples, not executable in CI without a key*
```powershell
# On a securely provisioned controlled signing worker:
signtool.exe sign /sha1 <CERT_THUMBPRINT> /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 .\STAGED_FIRST_PARTY.exe
signtool.exe verify /pa /all /v .\STAGED_FIRST_PARTY.exe

# PowerShell script, on a separate staged copy only:
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object Thumbprint -eq '<CERT_THUMBPRINT>'
Set-AuthenticodeSignature -LiteralPath '.\STAGED_OWN_SCRIPT.ps1' -Certificate $cert -HashAlgorithm SHA256 -TimestampServer '<PROVIDER_SUPPORTED_TIMESTAMP_URL>'
Get-AuthenticodeSignature -LiteralPath '.\STAGED_OWN_SCRIPT.ps1'
```
Do not put any private key, PFX, password, device PIN, cloud credential or certificate issuance document into a public repository or conversation. For Azure signing use repository-environment-scoped OIDC federation, restricted subject, least-privileged certificate-profile signer RBAC, approved event/branch and protected environment.

## Acceptance and roadmap ← CURRENT
- Confirm actual identity, issuer jurisdiction, and whether the issuer will serve this legal publisher and project use case (OPEN; OWNER/CA).
- Obtain verified public trust certificate/service and sign a sample first-party staged PE + PS1 with RFC3161/approved timestamp (OPEN; OWNER/CA).
- Integrate signer into content manifest regeneration and production-only Inno build; preserve raw R52 evidence and prevent silent signed/unsigned substitution (OPEN).
- Verify binaries, dependency signers, Inno uninstaller, final hashes and full clean/upgrade/uninstall regression (OPEN).
- Test Smart App Control on disposable Windows test image; collect CodeIntegrity events and verdict without altering user's Smart App Control setting (OPEN).
- Promote signed immutable release only after all gates PASS; update PROJECT_BRAIN and publish verifiable checksums/attestation (OPEN).

### Official references
- https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
- https://learn.microsoft.com/en-us/azure/artifact-signing/how-to-change-sku
- https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation
- https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/test-your-app-with-smart-app-control
- https://learn.microsoft.com/en-us/windows/desktop/seccrypto/signtool
- https://jrsoftware.org/ishelp/topic_setup_signtool.htm
- https://jrsoftware.org/ishelp/topic_setup_signeduninstaller.htm
- https://signpath.org/terms.html
- https://www.digicert.com/signing/compare-code-signing-certificates
- https://www.sectigo.com/ssl-certificates-tls/code-signing
- https://www.globalsign.com/en/code-signing-certificate

**Knowledge provenance:** authoritative project source at stated SHA, official CA/Microsoft/Inno docs inspected 2026-10-10. Pricing may change; CA sanctions and legal eligibility cannot be inferred from documentation silence. This record is scoped to the signing blocker and is not approval to mutate active network settings or release artifacts.
