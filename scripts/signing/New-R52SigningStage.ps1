# Materialize a single-use R52 signing stage from the exact approved source commit.
# Does not sign, install, publish, update Windows configuration or copy .git.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$SourceRoot,
 [Parameter(Mandatory=$true)][string]$StageRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$expected='5f99c56e294ff225479ee0a828bd0e6050e13740'
$source=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SourceRoot).Path).TrimEnd('\','/')
$stage=[IO.Path]::GetFullPath($StageRoot).TrimEnd('\','/')
if ($source.Equals($stage,[StringComparison]::OrdinalIgnoreCase) -or
 $stage.StartsWith(($source+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase) -or
 $source.StartsWith(($stage+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) {
 throw 'STAGE_SOURCE_OVERLAP_REJECTED'
}
if (Test-Path -LiteralPath $stage) {throw 'REFUSE_EXISTING_STAGE_OR_BLIND_RERUN'}
$head=(& git -C $source rev-parse HEAD)
if ($LASTEXITCODE -ne 0 -or [string]$head.Trim() -ne $expected) {throw 'R52_EXACT_SOURCE_SHA_REQUIRED'}
$changes=@(& git -C $source status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or @($changes | Where-Object {$_}).Count -ne 0) {
 throw 'R52_WORKTREE_TRACKED_DIRTY_REFUSED'
}
$meta=Get-Content -LiteralPath (Join-Path $source 'RELEASE.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($meta.version -ne '4.3.8' -or $meta.status -notmatch 'UNRELEASED|CANDIDATE|OPEN') {
 throw 'R52_SOURCE_RELEASE_AUTHORITY_MISMATCH'
}
$dirs=@('app','gateway','windows','docs')
$files=@('RELEASE.json','Setup-WindowsDependencies.ps1','Uninstall-FreeNetHub.ps1')
foreach ($dir in $dirs) {
 if (!(Test-Path -LiteralPath (Join-Path $source $dir) -PathType Container)) {throw ('MISSING_SOURCE_DIR_'+$dir)}
}
foreach ($file in $files) {
 if (!(Test-Path -LiteralPath (Join-Path $source $file) -PathType Leaf)) {throw ('MISSING_SOURCE_FILE_'+$file)}
}
New-Item -ItemType Directory -Path $stage | Out-Null
foreach ($dir in $dirs) {
 Copy-Item -LiteralPath (Join-Path $source $dir) -Destination (Join-Path $stage $dir) -Recurse -Force
}
foreach ($file in $files) {
 Copy-Item -LiteralPath (Join-Path $source $file) -Destination (Join-Path $stage $file)
}
# Do not inherit old installer bytes: new signed Setup must come from new compilation.
$oldDelivery=Join-Path $stage 'delivery'
if (Test-Path -LiteralPath $oldDelivery) {throw 'STAGED_DELIVERY_UNEXPECTED'}
@{
 schema=1
 purpose='SINGLE_USE_SIGNED_BUILD'
 sourceCommit=$expected
 status='READY_TO_SIGN'
 recordedUtc=(Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $stage '.signing-staging-authority.json') -Encoding UTF8
[pscustomobject]@{
 verdict='SINGLE_USE_STAGE_READY_UNTRUSTED_UNSIGNED'
 sourceCommit=$expected
 root=$stage
 nextGate='OWNER_APPROVED_SIGNING_PLAN_AND_REAL_CODE_SIGNING_CREDENTIAL'
} | ConvertTo-Json -Depth 4
