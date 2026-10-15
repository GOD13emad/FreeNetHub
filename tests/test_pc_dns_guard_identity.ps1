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
Verify $false 'IDENTITY_PROCESS_GONE_PROVEN'
'WATCHDOG_IDENTITY_SOURCE_MOCK_ALL_PASS'
