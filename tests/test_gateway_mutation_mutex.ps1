# Exact source and cross-process mutex regression; no NIC, firewall or service changes.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$src=Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\gateway\gateway_control.ps1') -Raw -Encoding UTF8
$first=$src.IndexOf('$script:GatewayMutationMutex=$null',[StringComparison]::Ordinal)
$end=$src.IndexOf('function Cleanup-Failed(',[Math]::Max(0,$first),[StringComparison]::Ordinal)
if($first -lt 0 -or $end -le $first){throw 'MUTATION_GUARD_SOURCE_MISSING'}
function Assert([bool]$ok,[string]$reason){if(-not $ok){throw $reason}}
. ([scriptblock]::Create($src.Substring($first,$end-$first)))
if(-not $src.Contains('if($Action -ne ''Status''){Enter-GatewayMutationGuard}')){throw 'MUTATION_ACQUIRE_NOT_WIRED'}
if(-not $src.Contains('finally{Exit-GatewayMutationGuard}')){throw 'MUTATION_RELEASE_NOT_WIRED'}
$name='Local\FreeNetHub_Gateway_Mutation_v1'
$td=Join-Path ([IO.Path]::GetTempPath()) ('fnh-mutex-regression-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $td|Out-Null
$child=Join-Path $td 'child.ps1'
@'
param([Parameter(Mandatory)][string]$MutexName,[string]$Mode='check')
$lock=[System.Threading.Mutex]::new($false,$MutexName)
try{
 if(-not $lock.WaitOne(0)){exit 37}
 if($Mode -eq 'abandon'){[System.Environment]::Exit(19)}
 $lock.ReleaseMutex()
 exit 0
}finally{$lock.Dispose()}
'@|Set-Content -LiteralPath $child -Encoding UTF8
try{
 Enter-GatewayMutationGuard
 & pwsh.exe -NoLogo -NoProfile -NonInteractive -File $child -MutexName $name
 if($LASTEXITCODE -ne 37){throw ('CONCURRENT_MUTATION_NOT_DENIED '+$LASTEXITCODE)}
 'CONCURRENT_SECOND_PROCESS_DENIED_PASS'
 Exit-GatewayMutationGuard
 & pwsh.exe -NoLogo -NoProfile -NonInteractive -File $child -MutexName $name
 if($LASTEXITCODE -ne 0){throw ('MUTEX_NOT_RELEASED '+$LASTEXITCODE)}
 'AFTER_RELEASE_SECOND_PROCESS_ALLOWED_PASS'
 # Reacquiring and releasing the source guard itself must remain idempotent.
 Enter-GatewayMutationGuard
 if(-not $script:GatewayMutationHeld){throw 'SOURCE_ACQUIRE_FALSE'}
 Exit-GatewayMutationGuard
 if($script:GatewayMutationHeld -or $script:GatewayMutationMutex){throw 'SOURCE_RELEASE_LEAK'}
 'SOURCE_REACQUIRE_AND_RELEASE_PASS'
 # Keep an unowned observer handle alive so the abandoned named mutex
 # remains present after the worker exits without releasing ownership.
 $observer=[System.Threading.Mutex]::new($false,$name)
 try{
  & pwsh.exe -NoLogo -NoProfile -NonInteractive -File $child -MutexName $name -Mode abandon
  if($LASTEXITCODE -ne 19){throw 'ABANDONMENT_FIXTURE_FAILED'}
  $caught=$false
  try{Enter-GatewayMutationGuard}catch{
   if($_.Exception.Message -ne 'GATEWAY_MUTATION_LOCK_ABANDONED_REVIEW_REQUIRED'){throw}
   $caught=$true
  }
  if(-not $caught){throw 'ABANDONED_LOCK_NOT_REJECTED'}
  Exit-GatewayMutationGuard
  'ABANDONED_MUTEX_FAIL_CLOSED_PASS'
 }finally{$observer.Dispose()}
 'GATEWAY_CROSS_PROCESS_MUTEX_ALL_PASS'
}finally{
 Exit-GatewayMutationGuard
 Remove-Item -LiteralPath $td -Recurse -Force -ErrorAction SilentlyContinue
}

# Do not let the intentional child-process exit 19 poison the CI task exit.
exit 0
