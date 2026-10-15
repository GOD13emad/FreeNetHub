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
