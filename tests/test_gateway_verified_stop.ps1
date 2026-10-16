# Source-exact, unprivileged mock of native Stop receipt validation.
# Does not interact with NICs, Firewall, VPN processes, system services or owner state.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$gateway=Join-Path $PSScriptRoot '..\gateway\gateway_control.ps1'
$src=Get-Content -LiteralPath $gateway -Raw -Encoding UTF8
$start=$src.IndexOf('function Invoke-VerifiedNativeStop{',[StringComparison]::Ordinal)
$end=$src.IndexOf('function Cleanup-Failed(',[Math]::Max(0,$start),[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'SOURCE_VERIFIED_STOP_FUNCTION_MISSING'}
. ([scriptblock]::Create($src.Substring($start,$end-$start)))
function Assert([bool]$ok,[string]$reason){if(-not $ok){throw $reason}}
if($src.IndexOf("if(Test-Path "+'$Owner'+"){Remove-Item "+'$Owner', [StringComparison]::Ordinal) -ge 0){throw 'SOURCE_DELETES_UNVERIFIED_OWNER'}
$stopBlock=$src.Substring($src.IndexOf("elseif("+'$Action'+" -eq 'Stop'){"),$src.IndexOf("elseif("+'$Action'+" -eq 'StopConsole'){")-$src.IndexOf("elseif("+'$Action'+" -eq 'Stop'){"))
if(-not $stopBlock.Contains('Invoke-VerifiedNativeStop')){throw 'STOP_ROUTE_MISSING_VERIFIED_CLEANUP'}
if($stopBlock.IndexOf('Invoke-VerifiedNativeStop') -gt $stopBlock.IndexOf('Remove-Item $Session')){throw 'SESSION_REMOVED_BEFORE_VERIFIED_STOP'}
$cleanupStart=$src.IndexOf('function Cleanup-Failed(')
$cleanupEnd=$src.IndexOf('}else{',$cleanupStart)
if($cleanupStart -lt 0 -or $cleanupEnd -le $cleanupStart){throw 'CLEANUP_BLOCK_EXTRACTION_FAILED'}
$cleanup=$src.Substring($cleanupStart,$cleanupEnd-$cleanupStart)
if(-not $cleanup.Contains('Invoke-VerifiedNativeStop') -or $cleanup.IndexOf('Invoke-VerifiedNativeStop') -gt $cleanup.IndexOf('if($providerStarted)')){throw 'FAILED_START_IGNORES_STOP_ERROR'}
if(-not $src.Contains("'GATEWAY_OWNER_EVIDENCE_PRESENT_REFUSE_START'")){throw 'UNVERIFIED_OWNER_START_GUARD_MISSING'}
$script:Runtime=Join-Path ([IO.Path]::GetTempPath()) ('fnh-source-stop-test-'+[guid]::NewGuid().ToString('N'))
$script:StopScript='MOCK_ONLY'
$script:nextExit=0
$script:nextRecord=$null
New-Item -ItemType Directory -Path $script:Runtime|Out-Null
function pwsh.exe {
 param([Parameter(ValueFromRemainingArguments=$true)][string[]]$unused)
 if($null -ne $script:nextRecord){
  Set-Content -LiteralPath (Join-Path $script:Runtime 'stop_result.json') -Value $script:nextRecord -Encoding UTF8
 }
 $global:LASTEXITCODE=$script:nextExit
}
function Check([string]$marker,[int]$exit,[AllowNull()][string]$record,[bool]$expectPass){
 $script:nextExit=$exit;$script:nextRecord=$record
 $pass=$false
 try{Invoke-VerifiedNativeStop;$pass=$true}catch{if($expectPass){throw}}
 if($pass -ne $expectPass){throw ($marker+'_WRONG_OUTCOME')}
 ($marker+'_PASS')
}
try{
 $stale=Join-Path $script:Runtime 'stop_result.json'
 Set-Content -LiteralPath $stale -Value '{"status":"PASS","state":"STOPPED"}'
 Check 'MISSING_FRESH_RECEIPT' 0 $null $false
 Check 'NONZERO_EXIT_WITH_PASS_RECEIPT' 19 '{"status":"PASS","state":"STOPPED"}' $false
 Check 'MALFORMED_RECEIPT' 0 'not-json' $false
 Check 'FAIL_RECEIPT' 0 '{"status":"FAIL","state":"STOPPED"}' $false
 Check 'UNKNOWN_STATE' 0 '{"status":"PASS","state":"UNKNOWN"}' $false
 Check 'EXACT_STOPPED' 0 '{"status":"PASS","state":"STOPPED"}' $true
 Check 'CLEAN_NOT_OWNED' 0 '{"status":"PASS","state":"NOT_OWNED"}' $true
 'SOURCE_VERIFIED_NATIVE_STOP_ALL_PASS'
}finally{Remove-Item -LiteralPath $script:Runtime -Force -Recurse -ErrorAction SilentlyContinue}
