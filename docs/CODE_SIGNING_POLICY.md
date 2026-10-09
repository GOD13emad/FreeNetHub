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
2. **Commercial CA OV (DigiCert, Sectigo, GlobalSign):** real verified legal identity required. **Sectigo officially supports BOTH individuals and legal organizations for OV code signing; DigiCert and GlobalSign products must be checked separately for the proposed subscriber category**. Do not misclassify all OV as company-only; HSM/token-based private-key protection. DigiCert official catalog lists a 12-month OV token offering with USD 840 subscription and own-token/HSM with USD 696 subscription (catalog's dynamic monthly teaser amounts can differ from checkout total). Sectigo says from USD 536.25/yr on five-year subscription; actual 1-year quote and token/shipping must be checked. GlobalSign issues in legally registered organization name only and 366-day certificates. **Verify sanctions/jurisdiction, permitted payments, service geography, and all fees in writing with the CA before paying.** No assumption of eligibility from an Internet location.
**Special case — original kernel drivers:** if the publisher develops and submits a new Windows kernel driver (unlike merely bundling a legitimate upstream WinDivert driver), the Microsoft Hardware Dev Center requires a hardware-program account associated with an **EV** certificate for submissions, plus Microsoft attestation/WHQL signing. This EV requirement is distinct from the fact that EV gives **no automatic SmartScreen reputation** for ordinary EXEs. Source: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-reqs
3. **SignPath Foundation OSS:** USD 0 for approved eligible projects, publisher shown as **SignPath Foundation** rather than your own unified identity. Only fully compliant open-source source-built artifacts; excludes unapproved upstream binary re-signing and requires approval of each release. It is not a universal publisher certificate. Suitability of FreeNet Hub's bundled network/DPI tools is unverified.
4. **Microsoft Store:** consumer MSIX submissions are re-signed by Microsoft if publisher is legally eligible; externally hosted MSI/EXE submissions still require own CA-trusted signature. Store distribution is not a general signing service for GitHub releases. Individual onboarding fee waived in eligible markets; Iran-specific registration eligibility is not verified.

## Planned pipeline (not yet enabled for public signing)
`source SHA + dependencies/SBOM` -> clean hermetic **BUILD** -> stage own binaries/PS scripts -> **SIGN inner first-party files** -> **TIMESTAMP** -> reconcile embedded integrity manifests and signed bytes -> Inno Setup `SignTool` signs **Setup and Uninstaller** -> **VERIFY** with `signtool verify /pa /all /v`, Authenticode signer/TSA, third-party provenance and SHA256 -> isolated install/upgrade/uninstall + Smart App Control audit/enforcement observation -> release immutable artifact/attestation -> verify downloaded release byte identity.

Use `scripts/signing/Test-PublicAuthenticode.ps1` on the actual distribution tree with a concrete manifest containing exact relative filenames, `ownership=first-party` or `third-party`, publisherSubject (exact X.509 Subject), and for third-party entries `expectedPublisherSubject`. For PE files supply the installed SDK `signtool.exe` path. The verifier rejects unsigned, expired/untrusted, wrong-publisher, missing timestamp, missing artifacts, unsupported types and drivers not subjected to a separate driver gate. Each item needs a post-sign exact SHA-256 and pinned signer identity; complete coverage of runnable files under ArtifactRoot is mandatory. The sample manifest uses intentionally INVALID hash placeholders and must not be treated as ready for use. A passing verifier is **necessary, not sufficient** for a signed release.

Example manifest schema (replace all illustrative values before actual use):
```json
{
  "schema": 1,
  "publisherSubject": "CN=YOUR REAL LEGAL PUBLISHER, O=YOUR REGISTERED ORGANIZATION, C=XX",
  "publisherThumbprint": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "artifacts": [
    {"path": "FreeNetHub_4.3.8_R52_Setup.exe", "ownership": "first-party", "expectedSha256": "REPLACE_WITH_64_HEX_FINAL_SHA256"},
    {"path": "installed/FreeNetHub.exe", "ownership": "first-party", "expectedSha256": "REPLACE_WITH_64_HEX_FINAL_SHA256"},
    {"path": "installed/app/FreeNetHub.ps1", "ownership": "first-party", "expectedSha256": "REPLACE_WITH_64_HEX_FINAL_SHA256"},
    {"path": "installed/unins000.exe", "ownership": "first-party", "expectedSha256": "REPLACE_WITH_64_HEX_FINAL_SHA256"}
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

## Non-Windows signing matrix (separate trust ecosystems)
- **Linux:** sign release-tag commits with GPG/SSH (GitHub verified commits), and publish a detached `.asc` signature for tar/ZIP/SHA256SUMS using a dedicated project GPG signing key; for distribution through package repos use the repository's APT `Release/InRelease` GPG signature or RPM package signing. These prove provenance to users who trust/import the key, **not** Windows Authenticode public CA trust. Maintain a trusted key fingerprint outside the archive; GitHub artifact attestations (Sigstore) can supplement, not replace package-manager trust.
- **Android:** sign AAB/APK with Android upload key from controlled Keystore; Google Play App Signing manages the app-signing key for Play releases. The Play identity/account and Android app keys are **separate** from Windows Authenticode. APKs outside Play need your own Android signing cert and package update compatibility; do not reuse Windows private keys.
- **macOS:** independently enroll with Apple Developer Program, create **Developer ID Application** and if using PKG **Developer ID Installer**, apply hardened runtime where required, `codesign`, `notarytool submit --wait`, `stapler staple`, and `spctl` checks. These Apple credentials and the notarization ticket are **not** Windows CA certs.
- **iOS:** Apple Developer Team, provisioning profile, correct entitlements and Apple Distribution certificate/automatic Xcode signing for IPA/TestFlight/App Store (or other explicitly authorized distribution). A macOS Developer ID does not authorize iOS builds; both generally use the same paid Apple Developer membership but distinct certificate/profile types. For a VPN/Network Extension, Apple entitlements and App Review form an **additional** product gate.
- **Shared governance:** one project signing inventory, publisher ownership record, release manifest, branch protection, review, evidence records, and key rotation plan; retain **separate platform-specific signing keys/credentials** with least privilege. Cross-platform software version names do not imply one universal certificate or cross-trust.

**FreeNet Hub SignPath eligibility caution:** no top-level OSI `LICENSE` file was found in the audited R52 Git tree; upstream licenses exist for separate components but do not by themselves license every first-party file. SignPath Foundation's published terms demand OSI licensing of all relevant components and expressly exclude certain hacking/security-circumvention tools. Whether FreeNet Hub's DPI/network functionality is eligible requires direct approval; do not assume acceptance, and do not publish a new license without a rights review.

### Cross-platform primary references
- https://docs.github.com/en/actions/concepts/security/artifact-attestations
- https://developer.android.com/studio/publish/app-signing
- https://developer.apple.com/developer-id/
- https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- https://developer.apple.com/help/account/membership/program-enrollment/

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
- https://www.sectigo.com/faqs/detail/OV-Code-Signing-Validation-for-Organizations-and-Individuals
- https://www.globalsign.com/en/code-signing-certificate

**Knowledge provenance:** authoritative project source at stated SHA, official CA/Microsoft/Inno docs inspected 2026-10-10. Pricing may change; CA sanctions and legal eligibility cannot be inferred from documentation silence. This record is scoped to the signing blocker and is not approval to mutate active network settings or release artifacts.


## Implemented tools and source-linked R52 signing evidence — 2026-10-10

Status: DEVELOPMENT_PREPARED_ONLY / NOT_SIGNED / NOT_PUBLISHED.

Implemented under scripts/signing:
1. New-R52SigningStage.ps1: creates an isolated single-use stage from exact R52 source SHA after checking tracked source cleanliness. The source tree stays immutable.
2. Sign-FirstPartyStaging.ps1: preflights exact first-party paths and their unsigned SHA256, validates one non-self-signed code-signing certificate in Windows store/HSM, signs staged PS1, PSM1, PSD1, EXE, DLL, or OCX, and requires signing and timestamp evidence. Third-party and kernel-driver files are refused. Signing transitions the stage to SIGN_IN_PROGRESS then FILES_SIGNED; do not resume failed partial signing.
3. Update-R52StagedIntegrity.ps1: reconciles app, gateway and standalone manifests, preserves original sourceSha256 provenance where defined, updates relevant staged RELEASE.json fields and transitions stage to MANIFESTS_RECONCILED. Installer SHA must be recorded outside the installer rather than inside its own payload.
4. Invoke-R52SignedInno.ps1: for exact R52 in a reconciled signing stage only, injects Inno SignTool and SignedUninstaller=yes, compiles a new installer using a Windows HSM-backed certificate, checks publisher, timestamp and SignTool verification, and refuses to overwrite prior installer bytes. The resulting receipt is SIGNED_SETUP_ONLY; extracted Uninstaller and SAC still require independent evidence.
5. Test-PublicAuthenticode.ps1: release verification with explicit post-sign SHA256 per file, certificate thumbprint and subject pins, full runnable-file inventory, upstream-specific publisher identities; for embedded upstream SYS drivers uses the Microsoft /kp kernel signature policy. It cannot override hardware driver signing requirements or legal rights.

Production integration prerequisites:
- Generate a human-reviewed, first-party-only signing plan with exact pre-sign hashes for the CLEAN signed stage. Do not copy or expose a PFX/private key, cloud credential, HSM PIN, identity document, or password in the repository or conversation.
- For CA OV with Windows HSM/CNG/KSP key, run the staged signer only after legal publisher eligibility and CA trust are confirmed. Microsoft Artifact Signing is a DIFFERENT provider backend requiring Azure subscription, legal public-trust identity validation and the official signing client; do not treat this Windows store script as automatically compatible with a cloud key.
- After staged signatures: recalculate runtime hash manifests, verify the product still launches with signed bytes, build and sign Inno Setup and generated Uninstaller, independently inspect complete extracted installed payload (including upstream drivers/binaries), test with Smart App Control on disposable VM and verify exact final asset SHA after GitHub publishing.
- Do not mark R52 FINAL until legal third-party binary rights, CA public trust, exact issuer name, trusted timestamp, uninstaller trust, signed file inventory, SAC and immutable release proof ALL pass.

Important reconciled baseline: local evidence R52_CANDIDATE_GATE_RECEIPT_20261009.json reports an unsigned installer of 24,260,213 bytes (SHA256 7214F7AE832539924B58A6750584079DD859DB5CDA53A59A345B5C9DA3D24DD0), with 176 Windows native tests and hosted clean/upgrade checks. A DIFFERENT later unsigned QA compilation R52_PUBLIC_SIGNED_RELEASE_GATE_V3_20261010.json reports 24,273,164 bytes (SHA256 C3FA52249A0F6B703D45752492AE49E426566BBA39EBBD0C7BAE26C02B60609B). They are NOT interchangeable nor the post-sign release hash. R52_SIGNING_ADMISSION_INVENTORY_20261010.json records nine PE candidates: two Authenticode Valid, seven NotSigned; 17 unsigned PowerShell scripts among a 25-script mixed-language inventory. Third-party WinDivert64.sys upstream was reported signed Valid but independent kernel-policy validation remains open. These are local historical audit observations, not newly performed trusted signing operations.

Official kernel verification reference: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/verifying-the-release-signature


## 2026-10-10 legal publisher eligibility — REAL INDIVIDUAL RESIDENT IN IRAN

Source-verified CA availability facts for any issuance to an individual declaring genuine Iranian residence:
- Microsoft Artifact Signing PUBLIC Trust: ineligible as individual unless located in United States or Canada. See https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
- Sectigo: official banned-country list explicitly disallows certificate issuance to individuals and entities in Iran. See https://www.sectigo.com/knowledge-base/detail/Banned-Country-List-1527076085907
- DigiCert: Iran is an embargoed country under its current comprehensive-sanctions conditions. See https://knowledge.digicert.com/solution/embargoed-countries-and-regions
- GlobalSign: its current publicly advertised Code Signing product is only offered to legally registered organizations, not direct individual purchasers. See https://shop.globalsign.com/en/code-signing
- Certum by Asseco (Poland): official Standard Code Signing does accommodate individuals and lists starting €139 for token/e-code and €209 for cloud, but country/export/sanctions eligibility for Iranian residents is UNCONFIRMED. See https://www.certum.eu/en/code-signing-certificates/ and https://shop.certum.eu/buy-a-code-signing-certyficate. A PRE-PURCHASE, NON-TRANSACTIONAL, no-identity-document inquiry was sent to the vendor's verified official address infolinia@certum.pl on 2026-10-10. No issuance or approval may be inferred.
- Certum Open Source Code Signing is cheaper but unsuitable for a blanket all-software commercial use: its terms require publicly evidenced OSS association and disallow commercial signing, with revocation for commercial misuse. See https://support.certum.eu/en/code-signing-required-documents/
- The U.S. OFAC 31 CFR 560.540 framework permits certain personal-communications-related software/services, but does NOT by itself constitute issuance approval by any specific CA, and its scope would require legal advice for a signing service. See https://ofac.treasury.gov/faqs/1110
- SignPath Foundation uses the FOUNDATION's publisher identity, not the individual developer's, and requires OSI-compliant OSS with additional conditions; not a blanket solution for proprietary projects. See https://signpath.org/terms.html

PUBLISHER GATE: NO PURCHASE, NO PERSONAL ID UPLOAD, NO CERTIFICATE PROFILE CREATION UNTIL CA ISSUER WRITTEN AUTHORIZATION FOR DECLARED RESIDENCE + REAL ID + PROPOSED SOFTWARE TYPES, payment and lawful cloud/token provisioning.

Technical contingency if all public CAs reject: self-signed development trust only on user-controlled endpoints, with manual explicit import when appropriate; GPG release signatures and SHA256 for software authenticity; never describe self-signed Authenticode as generally trusted by Windows or compliant with public Smart App Control.

All issuer prices are public STARTING points only and depend on order type, tax, key custody, and identity eligibility. Issuance feasibility takes precedence over cost.
