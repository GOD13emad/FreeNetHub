[CmdletBinding()]
param(
 [Parameter(Mandatory)][int]$TargetPid,
 [Parameter(Mandatory)][long]$StartTicks,
 [Parameter(Mandatory)][string]$ExpectedExe,
 [Parameter(Mandatory)][string]$UdpRule,
 [Parameter(Mandatory)][string]$TcpRule,
 [Parameter(Mandatory)][string]$UdpWirelessRule,
 [Parameter(Mandatory)][string]$TcpWirelessRule
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Receipt=Join-Path $Runtime 'dns-guard-watchdog-result.json'
$names=@($UdpRule,$TcpRule,$UdpWirelessRule,$TcpWirelessRule)
function Write-Receipt([string]$state,[string]$detail=''){
 [ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');status=$state;targetPid=$TargetPid;startTicks=$StartTicks;rules=$names;detail=$detail}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $Receipt -Encoding UTF8
}
function Is-ExactOwner {
 $p=Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
 if(!$p){
  # One process API miss must not disable the DNS guard if CIM still sees
  # the PID or the independent identity query itself fails.
  try{
   $c=Get-CimInstance Win32_Process -Filter ("ProcessId="+$TargetPid) -ErrorAction Stop
   if($c){return $true}
  }catch{return $true}
  return $false
 }
 # A running process with unreadable identity is NOT proof that it exited.
 # Keep the physical-DNS firewall blocks until the exact owner is verifiably gone.
 try {
  $ticks=[long]$p.StartTime.ToUniversalTime().Ticks
  if($ticks -ne $StartTicks){return $false}
 }catch{return $true}
 try {
  $path=[string]$p.Path
  if([string]::IsNullOrWhiteSpace($path)){return $true}
  return [string]::Equals($path,$ExpectedExe,[StringComparison]::OrdinalIgnoreCase)
 }catch{return $true}
}
function Test-TunAbsentStable([int]$Checks=50,[int]$PollMs=500){
 # Two independent clean adapter snapshots are required; an adapter-provider
 # exception during Wintun teardown is UNKNOWN, never evidence of removal.
 $consecutiveAbsent=0
 for($attempt=0;$attempt -lt $Checks;$attempt++){
  try{
   $present=@(Get-NetAdapter -IncludeHidden -ErrorAction Stop|Where-Object{$_.Name -eq 'FreeNetHub'})
   if($present.Count -eq 0){
    $consecutiveAbsent++
    if($consecutiveAbsent -ge 2){return $true}
   }else{$consecutiveAbsent=0}
  }catch{$consecutiveAbsent=0}
  if($attempt+1 -lt $Checks){Start-Sleep -Milliseconds $PollMs}
 }
 return $false
}
function Remove-OwnedDnsRulesConvergent {
 # Query only the FreeNetHub DNS53 guard namespace with terminating
 # provider errors. Missing exact rules are benign; store failure is UNKNOWN.
 $active=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)
 foreach($n in $names){
  if(@($active|Where-Object{$_.Name -eq $n}).Count -eq 0){continue}
  try{
   Remove-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction Stop
  }catch{
   $attemptError=$_.Exception.Message
   # The main stop path may have concurrently removed the same exact rule.
   # Only an independently successful readback proving absence is benign.
   $after=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)
   if(@($after|Where-Object{$_.Name -eq $n}).Count){throw ('OWNED_RULE_REMOVE_FAILED_'+$n+': '+$attemptError)}
  }
 }
 $current=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)
 return @($names|Where-Object{ $name=$_; @($current|Where-Object{$_.Name -eq $name}).Count -gt 0 })
}
try{
 if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMIN_REQUIRED'}
 if($names.Count -ne 4 -or $UdpRule -ne 'FreeNetHub-PC-DNS53-Guard-UDP-Wired' -or $TcpRule -ne 'FreeNetHub-PC-DNS53-Guard-TCP-Wired' -or $UdpWirelessRule -ne 'FreeNetHub-PC-DNS53-Guard-UDP-Wireless' -or $TcpWirelessRule -ne 'FreeNetHub-PC-DNS53-Guard-TCP-Wireless'){throw 'RULE_IDENTITY_MISMATCH'}
 # Keep the physical-DNS deny in place for the exact owned sing-box lifetime.
 while(Is-ExactOwner){Start-Sleep -Seconds 2}
 # A lingering virtual NIC is not an accepted safe state for removing the deny.
 if(-not (Test-TunAbsentStable)){
  Write-Receipt 'TUN_LINGERED_RULES_RETAINED' 'TUN absence not proven in two successive clean snapshots'
  exit 23
 }
 $remain=@(Remove-OwnedDnsRulesConvergent)
 if($remain.Count){Write-Receipt 'RULE_CLEANUP_FAILED' ($remain -join ',');exit 24}
 Write-Receipt 'EXACT_OWNER_EXITED_AND_RULES_CLEANED'
 exit 0
}catch {
 Write-Receipt 'WATCHDOG_FAILED_RULES_RETAINED' $_.Exception.Message
 exit 25
}
