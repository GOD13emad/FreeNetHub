# Production-only Inno signing of a previously signed and reconciled R52 stage.
# This is NOT a release/publish command. Needs a lawful HSM-backed store certificate.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$StageRoot,
 [Parameter(Mandatory=$true)][string]$SourceRoot,
 [Parameter(Mandatory=$true)][string]$PublisherThumbprint,
 [Parameter(Mandatory=$true)][string]$TimestampUrl,
 [Parameter(Mandatory=$true)][string]$SignToolPath,
 [Parameter(Mandatory=$true)][string]$IsccPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$stage=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $StageRoot).Path).TrimEnd('\','/')
$source=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SourceRoot).Path).TrimEnd('\','/')
if ($stage.Equals($source,[StringComparison]::OrdinalIgnoreCase) -or
 $stage.StartsWith(($source+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase) -or
 (Test-Path -LiteralPath (Join-Path $stage '.git'))) {throw 'REFUSE_SOURCE_TREE_SIGNING'}
if (!(Test-Path -LiteralPath $IsccPath -PathType Leaf) -or
 !(Test-Path -LiteralPath $SignToolPath -PathType Leaf)) {throw 'ISCC_OR_SIGNTOOL_UNAVAILABLE'}
if ($PublisherThumbprint -notmatch '^[0-9a-fA-F]{40}$' -or $TimestampUrl -notmatch '^http://[^ ]+$') {
 throw 'SIGNING_CONFIGURATION_INVALID'
}
$marker=Join-Path $stage '.signing-staging-authority.json'
if (!(Test-Path -LiteralPath $marker -PathType Leaf)) {throw 'STAGE_AUTHORITY_MISSING'}
$m=Get-Content -LiteralPath $marker -Raw -Encoding UTF8 | ConvertFrom-Json
if ($m.sourceCommit -ne '5f99c56e294ff225479ee0a828bd0e6050e13740' -or
 $m.purpose -ne 'SINGLE_USE_SIGNED_BUILD' -or $m.status -ne 'MANIFESTS_RECONCILED') {
 throw 'R52_EXACT_SIGNED_STAGE_NOT_AUTHORIZED'
}
$iss=Join-Path $stage 'windows/installer/FreeNetHub.iss'
if (!(Test-Path -LiteralPath $iss -PathType Leaf)) {throw 'INNO_SCRIPT_NOT_FOUND'}
$input=Get-Content -LiteralPath $iss -Raw -Encoding UTF8
if ($input -notmatch '(?m)^\[Setup\]\s*$' -or $input -match '(?im)^SignTool\s*=' -or
 $input -match '(?im)^SignedUninstaller\s*=') {throw 'INNO_SIGNING_CONFIGURATION_UNEXPECTED'}
if ($input -notmatch 'OutputBaseFilename=FreeNetHub_4\.3\.8_R52_Setup') {throw 'WRONG_R52_INNO_SCRIPT'}
$out=Join-Path $stage 'delivery/github_v4.3.8/FreeNetHub_4.3.8_R52_Setup.exe'
if (Test-Path -LiteralPath $out) {throw 'REFUSE_OVERWRITE_EXISTING_INSTALLER'}
$parent=Split-Path -Parent $out
if (!(Test-Path -LiteralPath $parent -PathType Container)) {
 New-Item -Path $parent -ItemType Directory -Force | Out-Null
}
# Inno's $f is a literal special placeholder evaluated by ISCC, not PowerShell.
$signerTool = '"' + $SignToolPath + '" sign /sha1 ' + $PublisherThumbprint +
              ' /fd SHA256 /tr ' + $TimestampUrl + ' /td SHA256 $f'
$addition="[Setup]"+[Environment]::NewLine+"SignTool=stagecert"+[Environment]::NewLine+"SignedUninstaller=yes"
$stagedIss=$input.Replace('[Setup]',$addition)
$m.status='INNO_SIGNING_IN_PROGRESS'
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $marker -Encoding UTF8
Set-Content -LiteralPath $iss -Value $stagedIss -Encoding UTF8 -NoNewline
& $IsccPath /Qp /NI ("/Sstagecert="+$signerTool) $iss
if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $out -PathType Leaf)) {
 throw 'INNO_SIGNED_BUILD_FAILED_HOLD'
}
$s=Get-AuthenticodeSignature -LiteralPath $out
if ($s.Status -ne 'Valid' -or !$s.SignerCertificate -or
 $s.SignerCertificate.Thumbprint -ine $PublisherThumbprint -or !$s.TimeStamperCertificate) {
 throw 'SIGNED_SETUP_PUBLIC_TRUST_GATE_FAILED_HOLD'
}
& $SignToolPath verify /pa /all /v $out
if ($LASTEXITCODE -ne 0) {throw 'SIGNED_SETUP_WINVERIFY_FAILED_HOLD'}
$m.status='SIGNED_INNO_SETUP_BUILT_UNINSTALLER_INSTALL_TEST_OPEN'
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $marker -Encoding UTF8
[pscustomobject]@{
 verdict='SIGNED_SETUP_ONLY_NO_PUBLIC_RELEASE'
 sourceCommit=$m.sourceCommit
 setupFile=$out
 setupSha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash
 setupPublisher=$s.SignerCertificate.Subject
 timestampAuthority=$s.TimeStamperCertificate.Subject
 nextGate='EXTRACT_UNINSTALLER_VERIFY_AND_SAC_ON_DISPOSABLE_VM'
} | ConvertTo-Json -Depth 4
