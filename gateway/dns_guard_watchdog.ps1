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
 if(!$p){return $false}
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
try{
 if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMIN_REQUIRED'}
 if($names.Count -ne 4 -or $UdpRule -ne 'FreeNetHub-PC-DNS53-Guard-UDP-Wired' -or $TcpRule -ne 'FreeNetHub-PC-DNS53-Guard-TCP-Wired' -or $UdpWirelessRule -ne 'FreeNetHub-PC-DNS53-Guard-UDP-Wireless' -or $TcpWirelessRule -ne 'FreeNetHub-PC-DNS53-Guard-TCP-Wireless'){throw 'RULE_IDENTITY_MISMATCH'}
 # Keep the physical-DNS deny in place for the exact owned sing-box lifetime.
 while(Is-ExactOwner){Start-Sleep -Seconds 2}
 # A lingering virtual NIC is not an accepted safe state for removing the deny.
 $deadline=[DateTime]::UtcNow.AddSeconds(25)
 do{
  $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}|Select-Object -First 1
  if(!$tun){break}
  Start-Sleep -Milliseconds 500
 }while([DateTime]::UtcNow -lt $deadline)
 if($tun){Write-Receipt 'TUN_LINGERED_RULES_RETAINED';exit 23}
 foreach($n in $names) {
  $r=Get-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction SilentlyContinue
  if($r){$r|Remove-NetFirewallRule -ErrorAction Stop}
 }
 $remain=@($names|Where-Object{Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore -ErrorAction SilentlyContinue})
 if($remain.Count){Write-Receipt 'RULE_CLEANUP_FAILED' ($remain -join ',');exit 24}
 Write-Receipt 'EXACT_OWNER_EXITED_AND_RULES_CLEANED'
 exit 0
}catch {
 Write-Receipt 'WATCHDOG_FAILED_RULES_RETAINED' $_.Exception.Message
 exit 25
}
