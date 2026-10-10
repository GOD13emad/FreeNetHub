# Read-only, fail-closed public Windows Authenticode verification.
# No private keys, network configuration changes, or signing operations.
param(
  [Parameter(Mandatory = $true)][string]$ArtifactRoot,
  [Parameter(Mandatory = $true)][string]$ManifestPath,
  [string]$SignToolPath = '',
  [string]$ReportPath = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (!(Test-Path -LiteralPath $ArtifactRoot -PathType Container)) { throw 'ARTIFACT_ROOT_MISSING' }
if (!(Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'SIGNING_MANIFEST_MISSING' }
$root = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $ArtifactRoot).Path).TrimEnd('\','/')
$boundary = $root + [IO.Path]::DirectorySeparatorChar
$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 1 -or !($manifest.artifacts) -or !($manifest.publisherSubject) -or !($manifest.publisherThumbprint)) {
  throw 'SIGNING_MANIFEST_SCHEMA_INVALID'
}
if ([string]$manifest.publisherThumbprint -notmatch '^[0-9a-fA-F]{40}$') { throw 'PUBLISHER_THUMBPRINT_PIN_INVALID' }
$items = @($manifest.artifacts)
if ($items.Count -eq 0) { throw 'SIGNING_MANIFEST_EMPTY' }
if (!$SignToolPath) {
  $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
  if ($cmd) { $SignToolPath = $cmd.Source }
}
$results = [System.Collections.Generic.List[object]]::new()
$seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

foreach ($item in $items) {
  $rel = [string]$item.path
  $owner = [string]$item.ownership
  $record = [ordered]@{
    path = $rel; ownership = $owner; status = 'FAIL'; reasons = @()
    sha256 = $null; authenticode = $null; subject = $null
    thumbprint = $null; timestampAuthority = $null; expectedSha256 = [string]$item.expectedSha256
    signtool = 'NOT_RUN'
  }
  $reasons = [System.Collections.Generic.List[string]]::new()
  try {
    if (!$rel -or [IO.Path]::IsPathRooted($rel) -or $rel -match '(^|[\\/])\.\.?([\\/]|$)' -or $rel -match '[*?]') {
      throw 'UNSAFE_RELATIVE_PATH'
    }
    if (!$seen.Add($rel)) { throw 'DUPLICATE_ARTIFACT' }
    $full = [IO.Path]::GetFullPath((Join-Path $root $rel))
    if (!$full.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) {
      throw 'ARTIFACT_PATH_ESCAPES_ROOT'
    }
    if (!(Test-Path -LiteralPath $full -PathType Leaf)) { throw 'ARTIFACT_MISSING' }
    if ($owner -notin @('first-party','third-party')) { throw 'OWNERSHIP_NOT_CLASSIFIED' }
    $ext = [IO.Path]::GetExtension($full).ToLowerInvariant()
    if ($ext -eq '.sys' -and $owner -ne 'third-party') { throw 'FIRST_PARTY_KERNEL_DRIVER_REQUIRES_HARDWARE_DEV_CENTER_GATE' }
    if ($ext -notin @('.exe','.dll','.ocx','.sys','.msi','.msix','.msp','.cab','.ps1','.psm1','.psd1')) {
      throw 'ARTIFACT_TYPE_NOT_APPROVED'
    }
    if ((Get-Item -LiteralPath $full).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_POINT_NOT_ALLOWED' }
    $record.sha256 = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
    if ([string]$item.expectedSha256 -notmatch '^[0-9a-fA-F]{64}$' -or $record.sha256 -ine [string]$item.expectedSha256) {
      throw 'FINAL_SIGNED_SHA256_MISMATCH'
    }
    $sig = Get-AuthenticodeSignature -LiteralPath $full
    $record.authenticode = [string]$sig.Status
    if (!$sig.SignerCertificate -or $sig.Status -ne 'Valid') { throw ('PUBLIC_AUTHENTICODE_'+$sig.Status) }
    $record.subject = $sig.SignerCertificate.Subject
    $record.thumbprint = $sig.SignerCertificate.Thumbprint
    $expected = if ($owner -eq 'first-party') { [string]$manifest.publisherSubject } else { [string]$item.expectedPublisherSubject }
    if (!$expected) { throw 'EXPECTED_PUBLISHER_MISSING' }
    if ($record.subject -cne $expected) { throw 'PUBLISHER_MISMATCH' }
    if ($owner -eq 'first-party' -and $record.thumbprint -ine [string]$manifest.publisherThumbprint) {
      throw 'PUBLISHER_CERT_PIN_MISMATCH'
    }
    if ($owner -eq 'third-party') {
      if ([string]$item.expectedPublisherThumbprint -notmatch '^[0-9a-fA-F]{40}$' -or
          $record.thumbprint -ine [string]$item.expectedPublisherThumbprint) { throw 'UPSTREAM_CERT_PIN_MISMATCH' }
    }
    if (!$sig.TimeStamperCertificate) { throw 'RFC3161_OR_AUTHENTICODE_TIMESTAMP_NOT_OBSERVED' }
    $record.timestampAuthority = $sig.TimeStamperCertificate.Subject
    if ($ext -notin @('.ps1','.psm1','.psd1')) {
      if (!$SignToolPath -or !(Test-Path -LiteralPath $SignToolPath -PathType Leaf)) {
        throw 'SIGNTOOL_REQUIRED_FOR_PE_OR_PACKAGE_VALIDATION'
      }
      # Microsoft WDK documents /kp for existing embedded-signed upstream kernel drivers.
      # This DOES NOT replace runtime load/install test or publisher's rights evidence.
      if ($ext -eq '.sys') {
        $output = & $SignToolPath verify /kp /v $full 2>&1 | Out-String
      } else {
        $output = & $SignToolPath verify /pa /all /v $full 2>&1 | Out-String
      }
      $exit = $LASTEXITCODE
      $record.signtool = "EXIT_$exit"
      if ($exit -ne 0) { throw ('SIGNTOOL_VERIFY_FAILED_'+$exit) }
    }
    $record.status = 'PASS'
  }
  catch {
    $reasons.Add([string]$_.Exception.Message)
  }
  $record.reasons = @($reasons.ToArray())
  $results.Add([pscustomobject]$record)
}
# Fail closed on code not explicitly accounted for by the release manifest.
$codeExts = @('.exe','.dll','.ocx','.sys','.msi','.msix','.msp','.cab','.ps1','.psm1','.psd1')
$inventoryMissing = [System.Collections.Generic.List[string]]::new()
Get-ChildItem -LiteralPath $root -File -Recurse -Force | ForEach-Object {
  if ($codeExts -contains $_.Extension.ToLowerInvariant()) {
    $relativeFile = [IO.Path]::GetRelativePath($root,$_.FullName)
    if (!$seen.Contains($relativeFile)) { $inventoryMissing.Add($relativeFile) }
  }
}
$passed = @($results | Where-Object status -eq 'PASS').Count
$report = [ordered]@{
  schema = 1
  verdict = $(if ($passed -eq $items.Count -and $inventoryMissing.Count -eq 0) { 'PASS' } else { 'FAIL' })
  trust = 'PUBLIC_AUTHENTICODE_VERIFICATION'
  publisherSubject = [string]$manifest.publisherSubject
  publisherThumbprint = [string]$manifest.publisherThumbprint
  missingFromManifest = @($inventoryMissing.ToArray())
  sourceManifest = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash
  files = @($results)
  count = $items.Count
  passed = $passed
  generatedUtc = (Get-Date).ToUniversalTime().ToString('o')
}
$json = $report | ConvertTo-Json -Depth 8
if ($ReportPath) {
  $reportDir = Split-Path -Parent $ReportPath
  if ($reportDir -and !(Test-Path -LiteralPath $reportDir)) { throw 'REPORT_DIRECTORY_MISSING' }
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($ReportPath), $json, [Text.UTF8Encoding]::new($false))
}
Write-Output $json
if ($report.verdict -ne 'PASS') { exit 1 }
exit 0
