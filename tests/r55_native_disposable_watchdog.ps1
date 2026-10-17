[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$InstallRoot,
 [Parameter(Mandatory)][int]$StartPid,
 [Parameter(Mandatory)][long]$StartTicks,
 [ValidateRange(30,600)][int]$Seconds=150
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=[IO.Path]::GetFullPath($InstallRoot)
$gateway=Join-Path $root 'gateway'
$stopScript=Join-Path $gateway 'stop_elevated.ps1'
$runtime=Join-Path $gateway 'runtime'
$armed=Join-Path $runtime 'r55-runner-watchdog-armed'
$disarmed=Join-Path $runtime 'r55-runner-watchdog-disarmed'
$receipt=Join-Path $runtime 'r55-runner-watchdog-receipt.json'
function Save([string]$state,[string]$detail){
 [ordered]@{state=$state;detail=$detail;utc=[DateTimeOffset]::UtcNow.ToString('o');source='DISPOSABLE_RUNNER_ONLY'}|
  ConvertTo-Json -Compress|Set-Content -LiteralPath $receipt -Encoding utf8
}
if(!(Test-Path -LiteralPath $stopScript -PathType Leaf)){throw 'WATCHDOG_STOP_SCRIPT_MISSING'}
if(!(Test-Path -LiteralPath $armed -PathType Leaf)){throw 'WATCHDOG_NOT_ARMED'}
$end=[DateTime]::UtcNow.AddSeconds($Seconds)
while([DateTime]::UtcNow -lt $end){
 if(Test-Path -LiteralPath $disarmed){Save 'DISARMED' 'normal_cleanup_completed';exit 0}
 Start-Sleep -Milliseconds 250
}
if(Test-Path -LiteralPath $disarmed){Save 'DISARMED' 'normal_cleanup_completed';exit 0}
Save 'TRIGGERED' 'deadline_passed'
# Own only this exact controller process, never a PID reused by an unrelated process.
try{
 $p=Get-Process -Id $StartPid -ErrorAction SilentlyContinue
 if($p -and $p.StartTime.ToUniversalTime().Ticks -eq $StartTicks){
  Stop-Process -Id $StartPid -Force -ErrorAction Stop
 }
}catch{Save 'TRIGGERED_PROCESS_STOP_UNVERIFIED' $_.Exception.Message}
# Controller mutex is process-local; direct stop_elevated checks sing-box identity
# and only releases FreeNetHub owned TUN/rules after verified teardown.
$psi=[Diagnostics.ProcessStartInfo]::new()
$psi.FileName='pwsh.exe'
$psi.UseShellExecute=$false
$psi.CreateNoWindow=$true
foreach($a in @('-NoProfile','-NonInteractive','-File',$stopScript)){[void]$psi.ArgumentList.Add($a)}
$p=[Diagnostics.Process]::Start($psi)
if(!$p.WaitForExit(60000)){
 try{$p.Kill($true);[void]$p.WaitForExit(3000)}catch{}
 Save 'CLEANUP_TIMEOUT' 'stop_elevated_exceeded_60s'
 exit 26
}
$stopReceipt=Join-Path $runtime 'stop_result.json'
$record=$null
if(Test-Path -LiteralPath $stopReceipt){try{$record=Get-Content $stopReceipt -Raw|ConvertFrom-Json}catch{}}
if($p.ExitCode -ne 0 -or !$record -or [string]$record.status -ne 'PASS'){
 Save 'CLEANUP_FAILED' ('stop_exit='+$p.ExitCode)
 exit 27
}
try {
 $adapters=@(Get-NetAdapter -IncludeHidden -ErrorAction Stop|Where-Object Name -eq 'FreeNetHub')
 $rules=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)
}catch{Save 'FINAL_NETWORK_STATE_UNVERIFIED' $_.Exception.GetType().Name;exit 29}
if($adapters.Count -or $rules.Count){Save 'RESIDUAL_NETWORK_MUTATION' ('tun='+$adapters.Count+';guards='+$rules.Count);exit 28}
Save 'TIMEOUT_CLEANUP_VERIFIED' 'not_a_native_pass'
exit 0
