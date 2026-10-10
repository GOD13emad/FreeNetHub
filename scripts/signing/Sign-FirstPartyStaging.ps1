# Sign only approved FIRST-PARTY files in a disposable staging tree.
# OV/EV HSM private key remains with Windows CNG/KSP; no PFX, PIN or key file parameters.
# For Microsoft Artifact Signing use its official provider-specific action instead.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$StageRoot,
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$PlanPath,
  [Parameter(Mandatory=$true)][string]$PublisherThumbprint,
  [Parameter(Mandatory=$true)][string]$PublisherSubject,
  [Parameter(Mandatory=$true)][string]$TimestampUrl,
  [Parameter(Mandatory=$true)][string]$SignToolPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$stage=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $StageRoot).Path).TrimEnd('\','/')
$source=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SourceRoot).Path).TrimEnd('\','/')
if ($stage.Equals($source,[StringComparison]::OrdinalIgnoreCase) -or
  $stage.StartsWith(($source+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) {
  throw 'REFUSE_SIGNING_INSIDE_SOURCE_TREE'
}
if (Test-Path -LiteralPath (Join-Path $stage '.git')) { throw 'REFUSE_SIGNING_GIT_WORKTREE' }
$marker=Join-Path $stage '.signing-staging-authority.json'
if (!(Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'STAGING_AUTHORITY_MARKER_REQUIRED' }
$m=Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
if ($m.purpose -cne 'SINGLE_USE_SIGNED_BUILD' -or !$m.sourceCommit -or $m.status -cne 'READY_TO_SIGN') {
  throw 'INVALID_STAGING_AUTHORITY'
}
if (!(Test-Path -LiteralPath $PlanPath -PathType Leaf)) { throw 'SIGNING_PLAN_MISSING' }
$plan=Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
if ($plan.schema -ne 1 -or @($plan.files).Count -eq 0) { throw 'SIGNING_PLAN_INVALID' }
if ([string]$PublisherThumbprint -notmatch '^[0-9A-Fa-f]{40}$') { throw 'INVALID_PUBLISHER_THUMBPRINT' }
if ([string]$PublisherSubject -eq '') { throw 'PUBLISHER_SUBJECT_REQUIRED' }
if ([string]$TimestampUrl -notmatch '^http://[^ ]+$') { throw 'HTTP_TIMESTAMP_SERVER_REQUIRED' }
if (!(Test-Path -LiteralPath $SignToolPath -PathType Leaf)) { throw 'SIGNTOOL_NOT_FOUND' }
$cert=@(
  foreach ($store in @('Cert:\CurrentUser\My','Cert:\LocalMachine\My')) {
    Get-ChildItem -Path $store -ErrorAction SilentlyContinue |
      Where-Object { $_.Thumbprint -ieq $PublisherThumbprint -and $_.HasPrivateKey }
  }
)
if ($cert.Count -ne 1) { throw 'EXACTLY_ONE_HSM_OR_STORE_CODE_SIGNING_CERT_REQUIRED' }
$c=$cert[0]
if ($c.Subject -cne $PublisherSubject) { throw 'PUBLISHER_IDENTITY_MISMATCH' }
if ($c.PublicKey.Oid.Value -notin @('1.2.840.113549.1.1.1','1.2.840.10045.2.1')) { throw 'RSA_OR_ECC_CODE_SIGNING_CERT_REQUIRED' }
if ($c.Subject -ceq $c.Issuer) { throw 'SELF_SIGNED_CERT_REJECTED' }
$eku=@($c.Extensions | Where-Object {$_.Oid.Value -eq '2.5.29.37'})
if (!$eku -or !$c.EnhancedKeyUsageList -or
   @($c.EnhancedKeyUsageList | Where-Object {$_.ObjectId.Value -eq '1.3.6.1.5.5.7.3.3'}).Count -eq 0) {
  throw 'CODE_SIGNING_EKU_MISSING'
}
if (!$c.Verify()) { throw 'SIGNER_CHAIN_NOT_TRUSTED_ON_BUILD_HOST' }
$files=[System.Collections.Generic.List[object]]::new()
$seen=[System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($f in @($plan.files)) {
  $rel=[string]$f.path
  if ($f.ownership -cne 'first-party' -or !$rel -or [IO.Path]::IsPathRooted($rel) -or
    $rel -match '(^|[\\/])\.\.?([\\/]|$)' -or $rel -match '[*?]' -or !$seen.Add($rel)) {
    throw 'REFUSE_THIRD_PARTY_OR_UNSAFE_FILE_PATH'
  }
  $full=[IO.Path]::GetFullPath((Join-Path $stage $rel))
  if (!$full.StartsWith(($stage+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) {
    throw 'STAGE_ESCAPE_REFUSED'
  }
  if (!(Test-Path -LiteralPath $full -PathType Leaf)) { throw 'STAGED_FILE_MISSING' }
  $item=Get-Item -LiteralPath $full
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'SYMLINK_REJECTED' }
  $ext=[IO.Path]::GetExtension($full).ToLowerInvariant()
  if ($ext -notin @('.exe','.dll','.ocx','.ps1','.psm1','.psd1')) {
    throw 'UNSUPPORTED_OR_DRIVER_FILE_REFUSED'
  }
  $hash=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
  if ([string]$f.expectedUnsignedSha256 -notmatch '^[0-9a-fA-F]{64}$' -or
    $hash -ine [string]$f.expectedUnsignedSha256) { throw 'PRESIGN_SOURCE_HASH_MISMATCH' }
  if ((Get-AuthenticodeSignature -LiteralPath $full).Status -ne 'NotSigned') {
    throw 'INPUT_ALREADY_SIGNED_OR_UNEXPECTED_SIGNATURE'
  }
  $files.Add([pscustomobject]@{path=$rel;full=$full;extension=$ext;unsignedSHA256=$hash})
}
# Preflight ALL targets before the first mutation.
# A failed signing attempt is single-use; never blindly re-run a partially signed stage.
$m.status='SIGN_IN_PROGRESS'
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $marker -Encoding UTF8
$results=[System.Collections.Generic.List[object]]::new()
foreach ($file in $files) {
  if ($file.extension -in @('.ps1','.psm1','.psd1')) {
    $s=Set-AuthenticodeSignature -LiteralPath $file.full -Certificate $c -HashAlgorithm SHA256 -IncludeChain NotRoot -TimestampServer $TimestampUrl
    if ($s.Status -ne 'Valid') { throw ('SCRIPT_SIGNING_FAILED_'+$file.path+'_'+$s.Status) }
  } else {
    & $SignToolPath sign /sha1 $PublisherThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $file.full
    if ($LASTEXITCODE -ne 0) { throw ('PE_SIGNING_FAILED_'+$file.path) }
  }
  $signature=Get-AuthenticodeSignature -LiteralPath $file.full
  if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Thumbprint -ine $PublisherThumbprint -or
    !$signature.TimeStamperCertificate) { throw ('SIGNED_PUBLIC_TRUST_TIMESTAMP_GATE_FAILED_'+$file.path) }
  $results.Add([pscustomobject]@{
    path=$file.path
    preSignSha256=$file.unsignedSHA256
    signedSha256=(Get-FileHash -LiteralPath $file.full -Algorithm SHA256).Hash
    publisher=$signature.SignerCertificate.Subject
    certificateThumbprint=$signature.SignerCertificate.Thumbprint
    timestampAuthority=$signature.TimeStamperCertificate.Subject
  })
}
$m.status='FILES_SIGNED'
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $marker -Encoding UTF8
# This receipt NEVER claims Smart App Control, public release or external user-device trust.
[pscustomobject]@{
  verdict='SIGNED_STAGING_ONLY'
  sourceCommit=$m.sourceCommit
  files=@($results)
  nextGate='REHASH_INTERNAL_MANIFESTS_SIGN_SETUP_UNINSTALLER_VERIFY_ON_CLEAN_WINDOWS'
} | ConvertTo-Json -Depth 8
