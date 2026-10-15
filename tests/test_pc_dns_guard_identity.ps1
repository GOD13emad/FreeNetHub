# Execute actual source predicate with mocks; no real process or firewall mutation.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\dns_guard_watchdog.ps1'
$content=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$start=$content.IndexOf('function Is-ExactOwner {',[StringComparison]::Ordinal)
$end=$content.IndexOf(([string][char]10+'try{'),[Math]::Max(0,$start),[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'WATCHDOG_OWNER_FUNCTION_EXTRACTION_CHANGED'}
$predicate=$content.Substring($start,$end-$start)
if($predicate -notmatch 'return \$true' -or $predicate -notmatch 'StartTime'){throw 'MISSING_FAIL_CLOSED_IDENTITY_BRANCH'}
. ([ScriptBlock]::Create($predicate))
$TargetPid=41444
$StartTicks=[datetime]::UtcNow.Ticks
$ExpectedExe='C:\Test\sing-box.exe'
$script:mockProcess=$null
$script:mockCim=$null
$script:cimThrows=$false
function Get-CimInstance { param([string]$ClassName,[string]$Filter,[string]$ErrorAction) if($script:cimThrows){throw 'SIMULATED_CIM_QUERY_FAILED'};return $script:mockCim }
function Get-Process { param([int]$Id) if($Id -eq $TargetPid){$script:mockProcess} }
function Verify([bool]$wanted,[string]$name) {
 $result=Is-ExactOwner
 if($result -ne $wanted){throw ($name + '_INVALID_EXPECTED_'+$wanted+'_ACTUAL_'+$result)}
 $name+'_PASS'
}
$time=[datetime]::new($StartTicks,[DateTimeKind]::Utc)
$script:mockProcess=[pscustomobject]@{StartTime=$time;Path=$ExpectedExe}
Verify $true 'IDENTITY_EXACT_ALIVE'
$script:mockProcess=[pscustomobject]@{StartTime=$time}
$script:mockProcess|Add-Member -MemberType ScriptProperty -Name Path -Value {throw 'SIMULATED_PATH_ACCESS_DENIED'}
Verify $true 'IDENTITY_PATH_INACCESSIBLE_FAIL_CLOSED'
$script:mockProcess=[pscustomobject]@{Path=$ExpectedExe}
$script:mockProcess|Add-Member -MemberType ScriptProperty -Name StartTime -Value {throw 'SIMULATED_STARTTIME_ACCESS_DENIED'}
Verify $true 'IDENTITY_STARTTIME_INACCESSIBLE_FAIL_CLOSED'
$script:mockProcess=[pscustomobject]@{StartTime=$time;Path=''}
Verify $true 'IDENTITY_EMPTY_PATH_FAIL_CLOSED'
$script:mockProcess=[pscustomobject]@{StartTime=$time.AddSeconds(-1);Path=$ExpectedExe}
Verify $false 'IDENTITY_PID_REUSE_PROVEN'
$script:mockProcess=[pscustomobject]@{StartTime=$time;Path='C:\Other\unrelated.exe'}
Verify $false 'IDENTITY_DIFFERENT_EXECUTABLE_PROVEN'
$script:mockProcess=$null
$script:mockCim=[pscustomobject]@{ProcessId=$TargetPid}
Verify $true 'IDENTITY_PROCESS_MISS_CIM_PID_LIVE_FAIL_CLOSED'
$script:mockCim=$null
$script:cimThrows=$true
Verify $true 'IDENTITY_PROCESS_MISS_CIM_EXCEPTION_FAIL_CLOSED'
$script:cimThrows=$false
Verify $false 'IDENTITY_PROCESS_GONE_PROVEN'
'WATCHDOG_IDENTITY_SOURCE_MOCK_ALL_PASS'

# Direct source test: transient adapter enumeration errors must not make
# firewall guards disappear before two clean TUN-absent snapshots.
$script:snapshots=@()
$script:snapshotIndex=0
function Get-NetAdapter {
 param([switch]$IncludeHidden,[string]$ErrorAction)
 if($script:snapshotIndex -ge $script:snapshots.Count){throw 'MISSING_MOCK_SNAPSHOT'}
 $next=$script:snapshots[$script:snapshotIndex];$script:snapshotIndex++
 if($next -eq 'error'){throw 'SIMULATED_ADAPTER_QUERY_ERROR'}
 if($next -eq 'present'){return [pscustomobject]@{Name='FreeNetHub'}}
 return @()
}
function Start-Sleep { param([int]$Milliseconds) }
function Verify-Tun([string[]]$snapshots,[bool]$expected,[string]$name){
 $script:snapshots=$snapshots
 $script:snapshotIndex=0
 $got=Test-TunAbsentStable -Checks $snapshots.Count -PollMs 0
 if($got -ne $expected){throw ($name+'_EXPECTED_'+$expected+'_GOT_'+$got)}
 $name+'_PASS'
}
Verify-Tun @('absent','absent') $true 'TUN_TWO_CLEAN_SNAPSHOTS'
Verify-Tun @('absent','error','absent') $false 'TUN_ERROR_BREAKS_ABSENCE_STREAK'
Verify-Tun @('error','absent','absent') $true 'TUN_RECOVERY_REQUIRES_TWO_CLEAN'
Verify-Tun @('present','absent') $false 'TUN_LINGERED_ONE_ABSENT_NOT_ENOUGH'
Verify-Tun @('error','error') $false 'TUN_ALL_QUERY_ERRORS_RETAIN_GUARD'
'WATCHDOG_TUN_SNAPSHOT_SOURCE_MOCK_ALL_PASS'


# Exact-source firewall cleanup regression. All NetSecurity calls here are
# mocks, not a request to modify the owner's real firewall.
$names=@('FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
$script:ownedRules=@{}
$script:deleteMode='normal'
$script:readFails=$false
$script:deleteCount=0
function Get-NetFirewallRule {
 param([string]$PolicyStore,[string]$ErrorAction)
 if($script:readFails){throw 'SIMULATED_FIREWALL_READ_ERROR'}
 foreach($n in @($script:ownedRules.Keys)){[pscustomobject]@{Name=$n}}
}
function Remove-NetFirewallRule {
 param([string]$Name,[string]$PolicyStore,[string]$ErrorAction)
 $script:deleteCount++
 if($script:deleteMode -eq 'concurrent' -and $script:deleteCount -eq 1){
  [void]$script:ownedRules.Remove($Name)
  throw 'SIMULATED_CONCURRENT_RULE_DISAPPEARED'
 }
 if($script:deleteMode -eq 'persistentFailure'){throw 'SIMULATED_FIREWALL_REMOVE_FAILED'}
 if($script:deleteMode -eq 'readbackFailure'){
  [void]$script:ownedRules.Remove($Name)
  $script:readFails=$true
  throw 'SIMULATED_CONCURRENT_RULE_DISAPPEARED'
 }
 [void]$script:ownedRules.Remove($Name)
}
function Reset-FirewallMock([string]$mode){
 $script:deleteMode=$mode;$script:deleteCount=0;$script:readFails=$false
 $script:ownedRules=@{}
 foreach($n in $names){$script:ownedRules[$n]=$true}
}
Reset-FirewallMock 'normal'
if(@(Remove-OwnedDnsRulesConvergent).Count -ne 0 -or $script:ownedRules.Count -ne 0){throw 'RULE_NORMAL_CLEANUP_BAD'}
'OWNED_RULE_NORMAL_STOP_PASS'
Reset-FirewallMock 'concurrent'
if(@(Remove-OwnedDnsRulesConvergent).Count -ne 0 -or $script:ownedRules.Count -ne 0){throw 'RULE_CONCURRENT_CLEANUP_BAD'}
'OWNED_RULE_CONCURRENT_REMOVAL_CONVERGENCE_PASS'
Reset-FirewallMock 'normal'
[void]$script:ownedRules.Remove($names[0])
if(@(Remove-OwnedDnsRulesConvergent).Count -ne 0){throw 'RULE_ALREADY_ABSENT_BAD'}
'OWNED_RULE_ALREADY_ABSENT_NOOP_PASS'
Reset-FirewallMock 'persistentFailure'
$failed=$false
try{[void](Remove-OwnedDnsRulesConvergent)}catch{if($_.Exception.Message -like 'OWNED_RULE_REMOVE_FAILED_*'){$failed=$true}else{throw}}
if(!$failed -or $script:ownedRules.Count -ne 4){throw 'PERSISTENT_RULE_MUST_NOT_REPORT_PASS'}
'OWNED_RULE_PERSISTENT_REMOVE_FAILURE_CLOSED_PASS'
Reset-FirewallMock 'normal'
$script:readFails=$true
$failed=$false
try{[void](Remove-OwnedDnsRulesConvergent)}catch{if($_.Exception.Message -eq 'SIMULATED_FIREWALL_READ_ERROR'){$failed=$true}else{throw}}
if(!$failed -or $script:deleteCount -ne 0){throw 'FIREWALL_READ_FAILURE_NOT_CLOSED'}
'OWNED_RULE_STORE_READ_ERROR_CLOSED_PASS'
Reset-FirewallMock 'readbackFailure'
$failed=$false
try{[void](Remove-OwnedDnsRulesConvergent)}catch{if($_.Exception.Message -eq 'SIMULATED_FIREWALL_READ_ERROR'){$failed=$true}else{throw}}
if(!$failed){throw 'FIREWALL_READBACK_FAILURE_NOT_CLOSED'}
'OWNED_RULE_RACE_READBACK_ERROR_CLOSED_PASS'
'WATCHDOG_OWNED_RULE_SOURCE_MOCK_ALL_PASS'
