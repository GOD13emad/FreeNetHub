[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Owner=Join-Path $Runtime 'owner.json'
$ApplyResult=Join-Path $Runtime 'apply_result.json'
$Pre=Join-Path $Runtime 'prestate.json'
$Result=Join-Path $Runtime 'stop_result.json'
function Out-J($p,$x){$x|ConvertTo-Json -Depth 14|Set-Content -LiteralPath $p -Encoding UTF8}
function Fail([string]$m,$o=$null){
 $r=[ordered]@{status='FAIL';error=$m;utc=[DateTimeOffset]::UtcNow.ToString('o');owner=$o}
 Out-J $Result $r
 throw $m
}
function Process-Identity($o){
 # A live PID with unreadable owner evidence is NOT proof of process exit.
 # Fail closed: do not remove its TUN or DNS firewall rules until identity is clear.
 $g=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue
 if(!$g){
  # A single process-query miss is not sufficient evidence of exit if CIM
  # still observes the PID or the independent query cannot be completed.
  try{
   $seen=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$o.pid) -ErrorAction SilentlyContinue
   if($seen){return 'UNVERIFIED'}
  }catch{return 'UNVERIFIED'}
  return 'ABSENT'
 }
 try{
  $ticks=[long]$g.StartTime.ToUniversalTime().Ticks
  if($ticks -ne [long]$o.startTicks){return 'DIFFERENT'}
 }catch{return 'UNVERIFIED'}
 try{
  $c=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$o.pid) -ErrorAction SilentlyContinue
  if(!$c){return 'UNVERIFIED'}
  $path=[string]$c.ExecutablePath
  if([string]::IsNullOrWhiteSpace($path)){return 'UNVERIFIED'}
  if(-not [string]::Equals($path,[string]$o.path,[StringComparison]::OrdinalIgnoreCase)){return 'DIFFERENT'}
 }catch{return 'UNVERIFIED'}
 return 'EXACT'
}
function Process-Matches($o){return (Process-Identity $o) -eq 'EXACT'}
$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(!$admin){throw 'ADMIN_REQUIRED'}
Remove-Item $Result -Force -ErrorAction SilentlyContinue

$o=$null;$recovered=$false
if(Test-Path $Owner){
 $o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json
}elseif(Test-Path $ApplyResult){
 $a=Get-Content $ApplyResult -Raw -Encoding UTF8|ConvertFrom-Json
 if($a.status -eq 'PASS' -and $a.owner){
  $candidate=$a.owner
  $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$candidate.tun.name -and $_.InterfaceDescription -eq [string]$candidate.tun.description}|Select-Object -First 1
  if((Process-Matches $candidate) -or $tun){$o=$candidate;$recovered=$true}
 }
}
if(!$o){
 Out-J $Result ([ordered]@{status='PASS';state='NOT_OWNED';utc=[DateTimeOffset]::UtcNow.ToString('o')})
 exit 0
}

# Refuse destructive rollback while the recorded PID is alive but its identity
# is unreadable; this may be the owned sing-box, not a safely stopped process.
if((Process-Identity $o) -eq 'UNVERIFIED'){Fail 'OWNED_SINGBOX_IDENTITY_UNVERIFIED' $o}
# Kill only the exact process recorded by apply.
if(Process-Matches $o){
 Stop-Process -Id ([int]$o.pid) -Force -ErrorAction SilentlyContinue
 $deadline=[DateTime]::UtcNow.AddSeconds(5)
 do{
  if(-not (Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue)){break}
  Start-Sleep -Milliseconds 150
 }while([DateTime]::UtcNow -lt $deadline)
 if(Process-Matches $o){
  & taskkill.exe /PID ([int]$o.pid) /T /F | Out-Null
  Start-Sleep -Milliseconds 500
 }
}
if((Process-Identity $o) -eq 'UNVERIFIED'){Fail 'OWNED_SINGBOX_IDENTITY_UNVERIFIED_AFTER_STOP' $o}
if(Process-Matches $o){Fail 'OWNED_SINGBOX_STOP_INCOMPLETE' $o}

# Wait for Wintun to be released. If it lingers after the exact process is gone,
# remove only the exact FreeNetHub Wintun device.
$deadline=[DateTime]::UtcNow.AddSeconds(12)
do{
 $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$o.tun.name -and $_.InterfaceDescription -eq [string]$o.tun.description}|Select-Object -First 1
 if(!$tun){break}
 Start-Sleep -Milliseconds 250
}while([DateTime]::UtcNow -lt $deadline)
if($tun){
 if($tun.ComponentID -eq 'Wintun' -and $tun.Virtual -and $tun.PnPDeviceID){
  & pnputil.exe /remove-device ([string]$tun.PnPDeviceID) | Out-Null
  Start-Sleep -Seconds 1
 }
}
$tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$o.tun.name -and $_.InterfaceDescription -eq [string]$o.tun.description}|Select-Object -First 1
if($tun){Fail 'TUN_ADAPTER_STOP_INCOMPLETE' $o}

if($o.firewallRule){
 Get-NetFirewallRule -DisplayName ([string]$o.firewallRule) -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction SilentlyContinue
 if(Get-NetFirewallRule -DisplayName ([string]$o.firewallRule) -ErrorAction SilentlyContinue){Fail 'FIREWALL_RULE_STOP_INCOMPLETE' $o}
}

# Release only the exact PC DNS guard rules after the owned TUN is gone.
# Older installed owner.json records do not have this optional field.
$ownedDnsGuard=@()
if($o.PSObject.Properties['dnsGuardNames']){$ownedDnsGuard=@($o.dnsGuardNames)}
if([string]$o.mode -eq 'PC_TUNNEL' -and $ownedDnsGuard.Count){
 $allowed=@('FreeNetHub-PC-DNS53-Guard-UDP','FreeNetHub-PC-DNS53-Guard-TCP','FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
 if(@($ownedDnsGuard|Where-Object{$_ -notin $allowed}).Count){Fail 'PC_DNS_GUARD_RULE_IDENTITY_MISMATCH' $o}
 foreach($n in $ownedDnsGuard){
  $rule=Get-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction SilentlyContinue
  if($rule){$rule|Remove-NetFirewallRule -ErrorAction SilentlyContinue}
 }
 if(@($ownedDnsGuard|Where-Object{Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore -ErrorAction SilentlyContinue}).Count){
  Fail 'PC_DNS_GUARD_STOP_INCOMPLETE' $o
 }
}

if([string]$o.mode -eq 'CONSOLE_ONLY' -and -not (Test-Path $Pre)){Fail 'PRESTATE_MISSING_FOR_CONSOLE_ROLLBACK' $o}
if(Test-Path $Pre){
 $x=Get-Content $Pre -Raw -Encoding UTF8|ConvertFrom-Json
 $c=$x.console
 if($c -and [string]$x.mode -eq 'CONSOLE_ONLY'){
  $d=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
  $cc=Get-FnhConsoleConfig $d
  $hadGateway=@($c.addresses|Where-Object{$_.IPAddress -eq [string]$cc.gateway}).Count -gt 0
  if(-not $hadGateway){
   Remove-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$cc.gateway) -PolicyStore ActiveStore -Confirm:$false -ErrorAction SilentlyContinue
   if(Get-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$cc.gateway) -ErrorAction SilentlyContinue){Fail 'CONSOLE_GATEWAY_IP_STOP_INCOMPLETE' $o}
  }
  Set-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -Forwarding $c.forwarding -PolicyStore ActiveStore -ErrorAction SilentlyContinue
  $restoredIf=Get-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object -First 1
  if(!$restoredIf -or [string]$restoredIf.Forwarding -ne [string]$c.forwarding){Fail 'CONSOLE_FORWARDING_RESTORE_INCOMPLETE' $o}
 }
}
Remove-Item $Owner -Force -ErrorAction SilentlyContinue
if(Test-Path $Owner){Fail 'OWNER_STATE_REMOVE_INCOMPLETE' $o}
Out-J $Result ([ordered]@{
 status='PASS';state='STOPPED';recoveredOwner=$recovered;stoppedPid=[int]$o.pid;
 tunRemoved=$true;utc=[DateTimeOffset]::UtcNow.ToString('o')
})
