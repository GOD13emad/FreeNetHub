# Test stop_elevated's exact process ownership classifier without host mutation.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\stop_elevated.ps1'
$txt=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$start=$txt.IndexOf('function Process-Identity($o){',[StringComparison]::Ordinal)
$end=$txt.IndexOf('function Process-Matches($o)',[Math]::Max(0,$start),[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'SOURCE_STOP_IDENTITY_FUNCTION_NOT_FOUND'}
. ([ScriptBlock]::Create($txt.Substring($start,$end-$start)))
if($txt.IndexOf("if((Process-Identity "+'$o'+") -eq 'UNVERIFIED'){Fail 'OWNED_SINGBOX_IDENTITY_UNVERIFIED'") -lt 0){throw 'STOP_ENTRY_UNVERIFIED_GATE_MISSING'}
if($txt.IndexOf("if((Process-Identity "+'$o'+") -eq 'UNVERIFIED'){Fail 'OWNED_SINGBOX_IDENTITY_UNVERIFIED_AFTER_STOP'") -lt 0){throw 'STOP_POST_UNVERIFIED_GATE_MISSING'}
$processFake=$null
$cimFake=$null
$throwCim=$false
$owner=[pscustomobject]@{pid=41444;path='C:\Test\sing-box.exe';startTicks=[datetime]::UtcNow.Ticks}
$time=[datetime]::new($owner.startTicks,[DateTimeKind]::Utc)
function Get-Process{param([int]$Id)if($Id -eq $owner.pid){return $processFake}}
function Get-CimInstance{param([string]$ClassName,[string]$Filter)if($throwCim){throw 'SIMULATED_CIM_FAILURE'};return $cimFake}
function Check([string]$wanted,[string]$marker){
 $status=Process-Identity $owner
 if($status -ne $wanted){throw "$marker expected=$wanted actual=$status"}
 ($marker+'_PASS')
}
$processFake=$null;$cimFake=$null
Check ABSENT 'STOP_PID_ABSENT'
$cimFake=[pscustomobject]@{ExecutablePath='C:\Test\sing-box.exe'}
Check UNVERIFIED 'STOP_CIM_SEES_PID_WHILE_GET_PROCESS_MISSES'
$cimFake=$null;$throwCim=$true
Check UNVERIFIED 'STOP_PROCESS_QUERY_MISSES_AND_CIM_THROW_RETENTION'
$throwCim=$false
$processFake=[pscustomobject]@{StartTime=$time}
$cimFake=[pscustomobject]@{ExecutablePath='C:\TEST\SING-BOX.EXE'}
Check EXACT 'STOP_EXACT_PID_PATH_CASE_INSENSITIVE'
$processFake=[pscustomobject]@{StartTime=$time.AddSeconds(-2)}
Check DIFFERENT 'STOP_PID_REUSE'
$processFake=[pscustomobject]@{StartTime=$time}
$cimFake=[pscustomobject]@{ExecutablePath='C:\unrelated\other.exe'}
Check DIFFERENT 'STOP_DIFFERENT_EXE'
$cimFake=$null
Check UNVERIFIED 'STOP_CIM_UNAVAILABLE_RETENTION'
$cimFake=[pscustomobject]@{ExecutablePath=''}
Check UNVERIFIED 'STOP_CIM_EMPTY_PATH_RETENTION'
$processFake=[pscustomobject]@{}
$processFake|Add-Member -MemberType ScriptProperty -Name StartTime -Value {throw 'ACCESS_DENIED'}
Check UNVERIFIED 'STOP_PROCESS_STARTTIME_UNREADABLE_RETENTION'
$processFake=[pscustomobject]@{StartTime=$time};$throwCim=$true
Check UNVERIFIED 'STOP_CIM_THROW_RETENTION'
'STOP_IDENTITY_EXACT_SOURCE_ALL_PASS'


# Exercise exact source cleanup guard without Windows network mutation.
$stableStart=$txt.IndexOf('function Test-OwnedTunAbsentStable(',[StringComparison]::Ordinal)
$stableEnd=$txt.IndexOf('$admin=',[Math]::Max(0,$stableStart),[StringComparison]::Ordinal)
if($stableStart -lt 0 -or $stableEnd -le $stableStart){throw 'STOP_TUN_ABSENCE_GUARD_MISSING'}
. ([ScriptBlock]::Create($txt.Substring($stableStart,$stableEnd-$stableStart)))
if(-not $txt.Contains("if(-not (Test-OwnedTunAbsentStable)){")){throw 'STOP_TUN_ABSENCE_CHECK_NOT_IN_LIFECYCLE'}
$script:adapterSteps=@()
$script:adapterStep=0
function Get-NetAdapter {
 param([switch]$IncludeHidden,[string]$ErrorAction)
 if($script:adapterStep -ge $script:adapterSteps.Count){throw 'NO_MORE_MOCK_STEPS'}
 $value=$script:adapterSteps[$script:adapterStep];$script:adapterStep++
 if($value -eq 'error'){throw 'TRANSIENT_ADAPTER_QUERY_ERROR'}
 if($value -eq 'present'){return [pscustomobject]@{Name='FreeNetHub'}}
 return @()
}
function Start-Sleep { param([int]$Milliseconds) }
function Check-Tun([string[]]$snapshots,[bool]$want,[string]$name){
 $script:adapterSteps=$snapshots;$script:adapterStep=0
 $actual=Test-OwnedTunAbsentStable -Checks $snapshots.Count -PollMs 0
 if($actual -ne $want){throw ($name+' unexpected='+$actual)}
 $name+'_PASS'
}
Check-Tun @('absent','absent') $true 'STOP_TUN_TWO_CLEAN_ABSENT'
Check-Tun @('absent','error','absent') $false 'STOP_TUN_RACE_RETAINS_DNS_GUARD'
Check-Tun @('error','absent','absent') $true 'STOP_TUN_QUERY_RECOVERY'
Check-Tun @('present','absent') $false 'STOP_TUN_LINGER_RETAINS_GUARD'
Check-Tun @('error','error') $false 'STOP_TUN_QUERY_UNKNOWN_RETAINS_GUARD'
'STOP_TUN_ABSENCE_SOURCE_MOCK_ALL_PASS'


# Source-branch test: a missing owner/apply receipt cannot yield a false
# NOT_OWNED PASS while TUN enumeration is broken or TUN still exists.
$recoverStart=$txt.IndexOf('$o=$null;$recovered=$false',[StringComparison]::Ordinal)
$recoverEnd=$txt.IndexOf('# Refuse destructive rollback',[Math]::Max(0,$recoverStart),[StringComparison]::Ordinal)
if($recoverStart -lt 0 -or $recoverEnd -le $recoverStart){throw 'STOP_RECOVERY_SOURCE_FRAGMENT_MISSING'}
$recover=([ScriptBlock]::Create($txt.Substring($recoverStart,$recoverEnd-$recoverStart)))
$Owner='X:\source-mock\owner.json'
$ApplyResult='X:\source-mock\apply_result.json'
function Test-Path {param([string]$Path);return $false}
function Fail {param([string]$m);throw $m}
$script:adapterSteps=@('error');$script:adapterStep=0
$expectedFailure=$false
try{. $recover}catch{if($_.Exception.Message -eq 'UNOWNED_TUN_QUERY_UNVERIFIED'){$expectedFailure=$true}else{throw}}
if(!$expectedFailure){throw 'STOP_UNOWNED_QUERY_ERROR_WAS_NOT_BLOCKED'}
'STOP_UNOWNED_TUN_QUERY_ERROR_FAIL_CLOSED_PASS'
$script:adapterSteps=@('present');$script:adapterStep=0
$expectedFailure=$false
try{. $recover}catch{if($_.Exception.Message -eq 'UNOWNED_TUN_PRESENT_REFUSE_FALSE_CLEAN_STOP'){$expectedFailure=$true}else{throw}}
if(!$expectedFailure){throw 'STOP_UNOWNED_PRESENT_TUN_WAS_NOT_BLOCKED'}
'STOP_UNOWNED_TUN_PRESENT_FAIL_CLOSED_PASS'


# Execute the exact source-owned DNS53 cleanup phase with only in-memory
# firewall mocks. Never mutate actual Windows Firewall or host networking.
$guardStart=$txt.IndexOf("if([string]"+'$o'+".mode -eq 'PC_TUNNEL' -and "+'$ownedDnsGuard'+".Count){",[StringComparison]::Ordinal)
$guardEnd=$txt.IndexOf("if([string]"+'$o'+".mode -eq 'CONSOLE_ONLY'",[Math]::Max(0,$guardStart),[StringComparison]::Ordinal)
if($guardStart -lt 0 -or $guardEnd -le $guardStart){throw 'STOP_DNS_GUARD_PHASE_NOT_FOUND'}
if($txt.IndexOf('Remove-Item $Owner -Force',$guardEnd) -lt 0){throw 'OWNER_DELETED_BEFORE_GUARD_PHASE'}
$exactGuard=[ScriptBlock]::Create($txt.Substring($guardStart,$guardEnd-$guardStart))
$guardNames=@('FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
$script:firewallRules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$script:guardScenario='normal'
$script:firewallReadCount=0
$script:removeCalls=0
function Get-NetFirewallRule {
 param([string]$PolicyStore,[string]$ErrorAction)
 $script:firewallReadCount++
 if($script:guardScenario -eq 'readError' -or ($script:guardScenario -in @('readbackError','finalReadError') -and $script:firewallReadCount -ge 2)){
  throw 'SIMULATED_ACTIVE_STORE_UNREADABLE'
 }
 foreach($n in @($script:firewallRules)){[pscustomobject]@{Name=$n}}
}
function Remove-NetFirewallRule {
 param([string]$Name,[string]$PolicyStore,[string]$ErrorAction)
 $script:removeCalls++
 if($script:guardScenario -eq 'removeFailed' -and $script:removeCalls -eq 1){throw 'SIMULATED_REMOVE_FAILED'}
 if(!$script:firewallRules.Remove($Name)){throw 'SIMULATED_ALREADY_ABSENT'}
 if($script:guardScenario -in @('concurrent','readbackError') -and $script:removeCalls -eq 1){throw 'SIMULATED_CONCURRENT_REMOVAL'}
}
function Check-Guard([string]$scenario,[string]$expected,[int]$remainingCount,[string]$name){
 $script:guardScenario=$scenario;$script:firewallReadCount=0;$script:removeCalls=0
 $script:firewallRules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($n in $guardNames){[void]$script:firewallRules.Add($n)}
 [void]$script:firewallRules.Add('Unrelated-Rule-Never-Delete')
 if($scenario -eq 'alreadyAbsent'){[void]$script:firewallRules.Remove($guardNames[0])}
 $o=[pscustomobject]@{mode='PC_TUNNEL'}
 $ownedDnsGuard=@($guardNames)
 $err=''
 try{& $exactGuard}catch{$err=$_.Exception.Message}
 if($expected -eq 'PASS'){
  if($err){throw ($name+'_UNEXPECTED_'+$err)}
 }else{
  if($err -ne $expected){throw ($name+'_WRONG_ERROR_'+$err)}
 }
 if(!$script:firewallRules.Contains('Unrelated-Rule-Never-Delete') -or $script:firewallRules.Count -ne $remainingCount){throw ($name+'_RULE_STATE_MISMATCH')}
 $name+'_PASS'
}
Check-Guard 'normal' 'PASS' 1 'STOP_DNS_GUARD_NORMAL'
Check-Guard 'alreadyAbsent' 'PASS' 1 'STOP_DNS_GUARD_PREDELETED'
Check-Guard 'concurrent' 'PASS' 1 'STOP_DNS_GUARD_CONCURRENT_REMOVE'
Check-Guard 'removeFailed' 'PC_DNS_GUARD_STOP_INCOMPLETE' 5 'STOP_DNS_GUARD_REMOVE_FAILURE_RETAINED'
Check-Guard 'readError' 'PC_DNS_GUARD_STORE_UNREADABLE' 5 'STOP_DNS_GUARD_QUERY_ERROR_RETAINED'
Check-Guard 'readbackError' 'PC_DNS_GUARD_STORE_UNREADABLE' 4 'STOP_DNS_GUARD_RACE_READBACK_ERROR'
Check-Guard 'finalReadError' 'PC_DNS_GUARD_STORE_UNREADABLE' 1 'STOP_DNS_GUARD_FINAL_READ_ERROR_FAIL_CLOSED'
'STOP_DNS_GUARD_EXACT_SOURCE_MOCK_ALL_PASS'


# Re-run the exact ownerless stop branch with in-memory adapter and ActiveStore
# mocks. A stranded DNS53 block must be reported FAIL, not NOT_OWNED/PASS.
$script:adapterSteps=@('absent')
$script:adapterStep=0
$script:guardScenario='normal'
$script:firewallRules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
[void]$script:firewallRules.Add('FreeNetHub-PC-DNS53-Guard-UDP-Wired')
$got=''
try{. $recover}catch{$got=$_.Exception.Message}
if($got -ne 'UNOWNED_DNS_GUARD_PRESENT_REFUSE_FALSE_CLEAN_STOP'){throw ('STOP_ORPHAN_GUARD_UNEXPECTED_'+$got)}
'STOP_OWNERLESS_TUN_ABSENT_DNS_GUARD_PRESENT_FAIL_CLOSED_PASS'
$script:adapterSteps=@('absent')
$script:adapterStep=0
$script:guardScenario='readError'
$got=''
try{. $recover}catch{$got=$_.Exception.Message}
if($got -ne 'UNOWNED_DNS_GUARD_QUERY_UNVERIFIED'){throw ('STOP_ORPHAN_GUARD_QUERY_UNEXPECTED_'+$got)}
'STOP_OWNERLESS_TUN_ABSENT_FIREWALL_QUERY_FAIL_CLOSED_PASS'
$script:adapterSteps=@('absent')
$script:adapterStep=0
$script:guardScenario='normal'
$script:firewallRules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
[void]$script:firewallRules.Add('Unrelated-Rule-Never-Delete')
# Only in the mock, replace the terminating exit with a sentinel; the
# owner's original source remains unchanged and exact decision branches run.
$recoverSource=$txt.Substring($recoverStart,$recoverEnd-$recoverStart)
if($recoverSource.Split('exit 0').Count -ne 2){throw 'RECOVERY_EXIT_CONTRACT_CHANGED'}
$positiveRecover=[ScriptBlock]::Create($recoverSource.Replace('exit 0',"'SAFE_CLEAN_STOP'"))
function Out-J{param($p,$x);$script:mockCleanReceipt=$x}
$Result='X:\source-mock\stop_result.json'
$script:mockCleanReceipt=$null
$testOutput=@(& $positiveRecover)
if($testOutput -notcontains 'SAFE_CLEAN_STOP' -or $script:mockCleanReceipt.status -ne 'PASS' -or $script:mockCleanReceipt.state -ne 'NOT_OWNED'){throw 'STOP_OWNERLESS_CLEAN_ABSENCE_NOT_RECOGNIZED'}
if(!$script:firewallRules.Contains('Unrelated-Rule-Never-Delete')){throw 'STOP_OWNERLESS_UNRELATED_RULE_MUTATED'}
'STOP_OWNERLESS_TUN_AND_GUARD_BOTH_ABSENT_PASS'
'STOP_OWNERLESS_GUARD_STATE_SOURCE_MOCK_ALL_PASS'
