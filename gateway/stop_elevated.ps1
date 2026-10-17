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
function Wait-OwnedSingBoxFinalIdentity($ownerRecord,[int]$Checks=25,[int]$PollMs=200){
 # Process exit and CIM visibility can lag each other briefly after an exact,
 # identity-pinned stop; do not mistake that race for a confirmed foreign PID.
 # Never change/kill any PID here; only read identity until ABSENT/DIFFERENT.
 $state='UNVERIFIED'
 for($k=0;$k -lt $Checks;$k++){
  $state=Process-Identity $ownerRecord
  if($state -in @('ABSENT','DIFFERENT')){return $state}
  if($k+1 -lt $Checks){Start-Sleep -Milliseconds $PollMs}
 }
 return $state
}
function Assert-NoResidualPcDnsGuard($ownerRecord){
 # The list inside legacy owner.json may be absent or incomplete.
 # A successful STOP must independently prove all exact FreeNetHub DNS53
 # guard identities are absent, not merely the subset in owner.json.
 if([string]$ownerRecord.mode -ne 'PC_TUNNEL'){return}
 $allKnown=@(
  'FreeNetHub-PC-DNS53-Guard-UDP','FreeNetHub-PC-DNS53-Guard-TCP',
  'FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired',
  'FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless'
 )
 try{$remaining=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)}
 catch{Fail 'PC_DNS_GUARD_FINAL_QUERY_UNVERIFIED' $ownerRecord}
 if(@($remaining|Where-Object{$_.Name -in $allKnown}).Count){
  Fail 'PC_DNS_GUARD_FINAL_RESIDUAL_REFUSE_FALSE_STOP' $ownerRecord
 }
}
function Test-OwnedTunAbsentStable([int]$Checks=8,[int]$PollMs=250){
 # A transient NetAdapter/CIM read error during Wintun teardown is not
 # proof of removal. Preserve the physical DNS block until two clean
 # consecutive snapshots confirm that the dedicated name is absent.
 $clear=0
 for($k=0;$k -lt $Checks;$k++){
  try{
   $found=@(Get-NetAdapter -IncludeHidden -ErrorAction Stop|Where-Object{$_.Name -eq 'FreeNetHub'})
   if($found.Count -eq 0){
    $clear++
    if($clear -ge 2){return $true}
   }else{$clear=0}
  }catch{$clear=0}
  if($k+1 -lt $Checks){Start-Sleep -Milliseconds $PollMs}
 }
 return $false
}

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
  # Fail closed when owner.json disappeared during a transient adapter query.
  # A missing/failed query must never masquerade as a clean stop.
  try{
   $tun=Get-NetAdapter -IncludeHidden -ErrorAction Stop|Where-Object{$_.Name -eq [string]$candidate.tun.name -and $_.InterfaceDescription -eq [string]$candidate.tun.description}|Select-Object -First 1
  }catch{Fail 'APPLY_OWNER_TUN_QUERY_UNVERIFIED'}
  if((Process-Matches $candidate) -or $tun){$o=$candidate;$recovered=$true}
 }
}
if(!$o){
 try{
  $orphan=@(Get-NetAdapter -IncludeHidden -ErrorAction Stop|Where-Object{$_.Name -eq 'FreeNetHub'})
 }catch{Fail 'UNOWNED_TUN_QUERY_UNVERIFIED'}
 if($orphan.Count){Fail 'UNOWNED_TUN_PRESENT_REFUSE_FALSE_CLEAN_STOP'}
 # A missing owner receipt cannot justify reporting a clean stop while
 # exact FreeNetHub DNS guards still exist or ActiveStore is unreadable.
 # Do not delete these rules: their generation cannot be safely attributed
 # to the missing owner from a stale apply_result.json.
 $guardNames=@(
  'FreeNetHub-PC-DNS53-Guard-UDP','FreeNetHub-PC-DNS53-Guard-TCP',
  'FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired',
  'FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless'
 )
 try{$activeRules=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)}
 catch{Fail 'UNOWNED_DNS_GUARD_QUERY_UNVERIFIED'}
 if(@($activeRules|Where-Object{$_.Name -in $guardNames}).Count){
  Fail 'UNOWNED_DNS_GUARD_PRESENT_REFUSE_FALSE_CLEAN_STOP'
 }
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
$settled=Wait-OwnedSingBoxFinalIdentity $o
if($settled -eq 'UNVERIFIED'){Fail 'OWNED_SINGBOX_IDENTITY_UNVERIFIED_AFTER_STOP' $o}
if($settled -eq 'EXACT'){Fail 'OWNED_SINGBOX_STOP_INCOMPLETE' $o}
if($settled -notin @('ABSENT','DIFFERENT')){Fail 'OWNED_SINGBOX_UNKNOWN_FINAL_IDENTITY' $o}

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
if(-not (Test-OwnedTunAbsentStable)){
 Fail 'OWNED_TUN_ABSENCE_UNVERIFIED_DNS_RULES_RETAINED' $o
}

if($o.firewallRule){
 Get-NetFirewallRule -DisplayName ([string]$o.firewallRule) -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction SilentlyContinue
 if(Get-NetFirewallRule -DisplayName ([string]$o.firewallRule) -ErrorAction SilentlyContinue){Fail 'FIREWALL_RULE_STOP_INCOMPLETE' $o}
}

# Release only the exact PC DNS guard rules after the owned TUN is gone.
# Older installed owner.json records do not have this optional field.
$ownedDnsGuard=@()
# Older hijack owner receipts can encode an empty conditional as JSON null.
# @($null) is one unknown rule; distinguish absence from an actual invalid name.
if($o.PSObject.Properties['dnsGuardNames'] -and $null -ne $o.dnsGuardNames){
 $ownedDnsGuard=@($o.dnsGuardNames)
}
if([string]$o.mode -eq 'PC_TUNNEL' -and $ownedDnsGuard.Count){
 $allowed=@('FreeNetHub-PC-DNS53-Guard-UDP','FreeNetHub-PC-DNS53-Guard-TCP','FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
 if(@($ownedDnsGuard|Where-Object{$_ -notin $allowed}).Count){Fail 'PC_DNS_GUARD_RULE_IDENTITY_MISMATCH' $o}
 # ActiveStore enumeration errors are UNKNOWN, not evidence that the
 # owned DNS53 rules are absent. Never emit STOPPED/PASS on a failed read.
 try{$allActive=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)}
 catch{Fail 'PC_DNS_GUARD_STORE_UNREADABLE' $o}
 foreach($n in $ownedDnsGuard){
  if(@($allActive|Where-Object{$_.Name -eq $n}).Count -eq 0){continue}
  try{
   Remove-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction Stop
  }catch{
   # Another exact owner cleanup may already have deleted the rule.
   # Converge only when a new successful read verifies name absence.
   try{$afterDelete=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)}
   catch{Fail 'PC_DNS_GUARD_STORE_UNREADABLE' $o}
   if(@($afterDelete|Where-Object{$_.Name -eq $n}).Count){
    Fail 'PC_DNS_GUARD_STOP_INCOMPLETE' $o
   }
  }
 }
 try{$remaining=@(Get-NetFirewallRule -Name 'FreeNetHub-PC-DNS53-Guard-*' -PolicyStore ActiveStore -ErrorAction Stop)}
 catch{Fail 'PC_DNS_GUARD_STORE_UNREADABLE' $o}
 if(@($ownedDnsGuard|Where-Object{$name=$_;@($remaining|Where-Object{$_.Name -eq $name}).Count -gt 0}).Count){
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
Assert-NoResidualPcDnsGuard $o
Remove-Item $Owner -Force -ErrorAction SilentlyContinue
if(Test-Path $Owner){Fail 'OWNER_STATE_REMOVE_INCOMPLETE' $o}
Out-J $Result ([ordered]@{
 status='PASS';state='STOPPED';recoveredOwner=$recovered;stoppedPid=[int]$o.pid;
 tunRemoved=$true;utc=[DateTimeOffset]::UtcNow.ToString('o')
})
