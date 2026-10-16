# Exact-source unprivileged stop-guard regression. No Firewall/NIC/service mutation.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\stop_elevated.ps1'
$txt=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$start=$txt.IndexOf('function Assert-NoResidualPcDnsGuard($ownerRecord){',[StringComparison]::Ordinal)
$end=$txt.IndexOf('function Test-OwnedTunAbsentStable(',[Math]::Max(0,$start),[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'FINAL_GUARD_SOURCE_MISSING'}
. ([scriptblock]::Create($txt.Substring($start,$end-$start)))
$call=$txt.IndexOf('Assert-NoResidualPcDnsGuard $o',[StringComparison]::Ordinal)
$delete=$txt.IndexOf('Remove-Item $Owner -Force -ErrorAction SilentlyContinue',[StringComparison]::Ordinal)
if($call -lt 0 -or $delete -le $call){throw 'FINAL_GUARD_NOT_BEFORE_OWNER_DELETE'}
$script:rules=@()
$script:queryError=$false
$script:queries=0
function Fail([string]$message,$owner){throw $message}
function Get-NetFirewallRule{
 param([string]$PolicyStore,[string]$ErrorAction)
 if($PolicyStore -ne 'ActiveStore' -or $ErrorAction -ne 'Stop'){throw 'NON_TERMINATING_FIREWALL_QUERY'}
 $script:queries++
 if($script:queryError){throw 'SIMULATED_ACTIVESTORE_READ_DENIED'}
 return $script:rules
}
function Check([string]$name,[string]$mode,[string[]]$ruleNames,[bool]$queryFails,[bool]$expectSuccess,[string]$expectedError=''){
 $script:rules=@($ruleNames|ForEach-Object { [pscustomobject]@{Name=$_} })
 $script:queryError=$queryFails
 $script:queries=0
 $ok=$false
 try{Assert-NoResidualPcDnsGuard ([pscustomobject]@{mode=$mode});$ok=$true}
 catch{
  if($expectSuccess){throw}
  if($_.Exception.Message -ne $expectedError){throw ($name+'_WRONG_FAIL_'+$_.Exception.Message)}
 }
 if($ok -ne $expectSuccess){throw ($name+'_WRONG_OUTCOME')}
 if($mode -eq 'PC_TUNNEL' -and $script:queries -ne 1){throw ($name+'_NO_ACTIVE_QUERY')}
 if($mode -ne 'PC_TUNNEL' -and $script:queries -ne 0){throw ($name+'_CONSOLE_QUERY_SIDE_EFFECT')}
 $name+'_PASS'
}
Check 'LEGACY_OWNER_CLEAN_STOP' 'PC_TUNNEL' @() $false $true
Check 'LEGACY_OWNER_WIRED_GUARD_RETAINED' 'PC_TUNNEL' @('FreeNetHub-PC-DNS53-Guard-UDP-Wired') $false $false 'PC_DNS_GUARD_FINAL_RESIDUAL_REFUSE_FALSE_STOP'
Check 'LEGACY_OWNER_OLD_GUARD_RETAINED' 'PC_TUNNEL' @('FreeNetHub-PC-DNS53-Guard-TCP') $false $false 'PC_DNS_GUARD_FINAL_RESIDUAL_REFUSE_FALSE_STOP'
Check 'LEGACY_OWNER_WIRELESS_GUARD_RETAINED' 'PC_TUNNEL' @('FreeNetHub-PC-DNS53-Guard-TCP-Wireless') $false $false 'PC_DNS_GUARD_FINAL_RESIDUAL_REFUSE_FALSE_STOP'
Check 'OWNER_UNRELATED_FIREWALL_RULE' 'PC_TUNNEL' @('OtherApplication-Rule') $false $true
Check 'OWNER_ACTIVESTORE_QUERY_FAILURE' 'PC_TUNNEL' @() $true $false 'PC_DNS_GUARD_FINAL_QUERY_UNVERIFIED'
Check 'CONSOLE_NO_PC_DNS_QUERY' 'CONSOLE_ONLY' @('FreeNetHub-PC-DNS53-Guard-TCP-Wired') $true $true
'SOURCE_STOP_FINAL_DNS53_ALL_PASS'
