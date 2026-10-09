# Zero-budget software signing and provenance (Iran-resident individual)

Scope: reusable release assurance for projects you lawfully maintain, without paying for public certificate issuance. This is NOT a claim of a Microsoft-trusted Authenticode publisher identity.

## What is actually free

- GitHub Actions in a PUBLIC repository and GitHub artifact attestations based on Sigstore public-good certificates are available at zero enrollment fee within provider limits. The new workflow `.github/workflows/zero-cost-source-provenance.yml` builds a tar archive of EXACT tracked Git commit source, hashes it and requests/verifies provenance attestation. The signature proves the archive's asserted CI origin; Windows does NOT treat it as a public EXE/installer Authenticode signature.
- SHA256 hashes and GPG/Minisign/Cosign detached release signatures can verify author-controlled bytes; users need an authenticated out-of-band source to trust your own public key.
- A self-signed development certificate is suitable only for development, controlled devices or explicitly enrolled trusted endpoints. Do not install self-signed roots on customer devices silently; it does not solve Windows SAC public-trust signing.
- Android APK local release signing is possible at no certificate cost, but Play Console and store policies are independent gates. Linux signed repositories can also be free. macOS ad-hoc signatures do NOT provide public Developer ID notarization, and iOS App Store distribution remains dependent on an authorized Apple account.

## Free public Windows trust candidates, conditional rather than guaranteed

1. SignPath Foundation: free public OSS publisher signature for separately approved projects. It will display SignPath Foundation as publisher, not an individual's personal name. Requires an OSI-approved license and verifiable source-to-binary build, no proprietary bundled components (system library exception), active maintenance, independent human approvals, documented security policy and acceptance. **Do not add any top-level OSS license** without legal owner approval. The project currently bundles vendor executables and a signed kernel driver: inventory, provenance, copyright/license compatibility, permission and security review are OPEN. Regional eligibility for Iran also remains UNKNOWN. Pre-application compliance inquiry submitted to support@signpath.io on 2026-10-10, not an application or acceptance.
2. Microsoft Store: its new Individual onboarding flow advertises zero enrollment fee in supported regions; publishing an MSIX to the Store can result in Store-signed packages. Eligibility for real residency/ID in Iran is UNKNOWN; an official pre-enrollment question was sent to storesupport@service.microsoft.com. The Store does **not** re-sign arbitrary external EXE/MSI installers, and driver/full-system networking constraints remain a separate acceptance issue.
3. Public CAs (Sectigo, DigiCert, Microsoft Artifact Signing) do not offer an established no-cost, Iran-resident personal public Authenticode issuance path. Certum replied with automated acknowledgement only; no human eligibility decision and no purchase.

## Reproducible zero-cost verification

The SOURCE-only workflow deliberately creates no EXE, R52 installer, signed Uninstaller, self-signed trusted root, public release or network modification. Its evidence is an SHA256 checksum plus GitHub/Sigstore provenance attached to the exact CI source commit.

If the workflow succeeds, a maintainer can reconstruct its archive from the same commit using `git archive --format=tar <SHA> > FreeNetHub-source.tar`, verify the exact recorded SHA256, and run:
```shell
gh attestation verify FreeNetHub-source.tar --repo GOD13emad/FreeNetHub
```
The reconstruction must run on an environment whose Git canonicalization is compatible; a GitHub-hosted run from the specific recorded commit is authoritative, not a name-only repository check.

## Release admission (immutable)

- Source provenance PASS is **not** binary provenance PASS.
- CI Authenticode negative tests PASS is **not** any trusted code signing certificate.
- Self-signed developer signatures PASS is **not** SAC enabled-machine behavior PASS.
- No legal eligibility or OSS rights determination may be inferred from a generic vendor auto-response.
- R52 remains UNRELEASED while upstream unsigned binary authorization, host GUI/SAC, full-system runtime, public publisher certificate/signing and signed installer+uninstaller gates remain open.

Official reference: https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations
Official reference: https://signpath.org/terms.html
Official reference: https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control
Official reference: https://learn.microsoft.com/en-us/windows/apps/publish/whats-new-individual-developer
