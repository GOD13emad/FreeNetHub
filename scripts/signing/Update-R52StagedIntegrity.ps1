# Reconcile signed-stage content hashes; never edit the tracked source checkout.
# SourceSha256 stays as original source provenance, while sha256/bytes become
# final signed-stage values used by FreeNet Hub runtime integrity checks.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$StageRoot,
 [Parameter(Mandatory=$true)][string]$SourceRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$stage=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $StageRoot).Path).TrimEnd('\','/')
$source=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SourceRoot).Path).TrimEnd('\','/')
if ($stage.Equals($source,[StringComparison]::OrdinalIgnoreCase) -or
 $stage.StartsWith(($source+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase) -or
 (Test-Path -LiteralPath (Join-Path $stage '.git'))) {throw 'REFUSE_MUTATING_SOURCE_WORKTREE'}
$marker=Join-Path $stage '.signing-staging-authority.json'
if (!(Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'STAGE_MARKER_MISSING' }
$m=Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
if ($m.purpose -cne 'SINGLE_USE_SIGNED_BUILD' -or !$m.sourceCommit -or $m.status -cne 'READY_TO_SIGN') {
 throw 'STAGE_AUTHORITY_INVALID'
}
$records=[System.Collections.Generic.List[object]]::new()
$plans=@(
 @{ file='app/manifest.json'; base='app'; key='code'; col='file' },
 @{ file='gateway/manifest.json'; base='gateway'; key='files'; col='file' },
 @{ file='windows/standalone/MANIFEST.json'; base='windows/standalone'; key='files'; col='name' }
)
# Reject incomplete inputs before any metadata mutation.
$pending=[System.Collections.Generic.List[object]]::new()
foreach ($plan in $plans) {
 $manifestPath=Join-Path $stage $plan.file
 if (!(Test-Path -LiteralPath $manifestPath -PathType Leaf)) {throw 'MANIFEST_MISSING'}
 $json=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
 $rows=@($json.($plan.key))
 if ($rows.Count -eq 0) {throw 'MANIFEST_ROWS_EMPTY'}
 $base=Join-Path $stage $plan.base
 foreach ($row in $rows) {
  $rel=[string]$row.($plan.col)
  if (!$rel -or [IO.Path]::IsPathRooted($rel) -or $rel -match '(^|[\\/])\.\.?([\\/]|$)') {
    throw 'UNSAFE_MANIFEST_PATH'
  }
  $file=[IO.Path]::GetFullPath((Join-Path $base $rel))
  if (!$file.StartsWith(($base+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase) -or
      !(Test-Path -LiteralPath $file -PathType Leaf)) {throw 'MANIFEST_FILE_NOT_FOUND_OR_OUTSIDE_STAGE'}
  $info=Get-Item -LiteralPath $file
  if ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'SYMLINK_NOT_ALLOWED'}
  $pending.Add([pscustomobject]@{row=$row;file=$file;info=$info;relative=($plan.base+'/'+$rel)})
 }
 $records.Add([pscustomobject]@{path=$manifestPath;schema=$json;rows=$rows})
}
$releaseFile=Join-Path $stage 'RELEASE.json'
if (!(Test-Path -LiteralPath $releaseFile -PathType Leaf)) {throw 'RELEASE_METADATA_MISSING'}
$release=Get-Content -LiteralPath $releaseFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($release.version -ne '4.3.8' -or $release.releaseRevision -notmatch '^4\.3\.8-r52-') {
  throw 'EXACT_R52_METADATA_EXPECTED'
}
foreach ($p in $pending) {
 $p.row.sha256=(Get-FileHash -LiteralPath $p.file -Algorithm SHA256).Hash
 $p.row.bytes=[int64]$p.info.Length
}
foreach ($r in $records) {
 $r.schema | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $r.path -Encoding UTF8
}
$release.uiSha256=(Get-FileHash -LiteralPath (Join-Path $stage 'app/FreeNetHub.ps1') -Algorithm SHA256).Hash
$release.desktopShellSha256=(Get-FileHash -LiteralPath (Join-Path $stage 'windows/standalone/FreeNetHub.exe') -Algorithm SHA256).Hash
$release.gatewayManifestSha256=(Get-FileHash -LiteralPath (Join-Path $stage 'gateway/manifest.json') -Algorithm SHA256).Hash
# The SHA of the installer must NOT be embedded inside itself (circular checksum).
$release.installerSha256=$null
$release.status='R52_SIGNED_STAGE_NOT_PUBLIC_RELEASE'
$release | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $releaseFile -Encoding UTF8
[pscustomobject]@{
 verdict='STAGE_MANIFESTS_RECONCILED_NOT_RELEASED'
 sourceCommit=$m.sourceCommit
 hashedItems=$pending.Count
 manifests=@($records | ForEach-Object { $_.path })
 releaseMetadataSha256=(Get-FileHash -LiteralPath $releaseFile -Algorithm SHA256).Hash
 nextGate='INNO_SIGNED_SETUP_AND_UNINSTALLER_VERIFICATION'
} | ConvertTo-Json -Depth 5
