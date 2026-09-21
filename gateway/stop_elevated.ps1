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
function Process-Matches($o){
 $c=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$o.pid) -ErrorAction SilentlyContinue
 $g=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue
 if(!$c -and !$g){return $false}
 if(!$c -or !$g){return $false}
 return ($c.ExecutablePath -eq [string]$o.path -and $g.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks)
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
  $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$candidate.tun.name -and $_.InterfaceDescription -eq [string]$candidate.tun.description}|Select-Object -First 1
  if((Process-Matches $candidate) -or $tun){$o=$candidate;$recovered=$true}
 }
}
if(!$o){
 Out-J $Result ([ordered]@{status='PASS';state='NOT_OWNED';utc=[DateTimeOffset]::UtcNow.ToString('o')})
 exit 0
}

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
}

if(Test-Path $Pre){
 $x=Get-Content $Pre -Raw -Encoding UTF8|ConvertFrom-Json
 $c=$x.console
 if($c -and [string]$x.mode -eq 'CONSOLE_ONLY'){
  $d=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
  $cc=Get-FnhConsoleConfig $d
  $hadGateway=@($c.addresses|Where-Object{$_.IPAddress -eq [string]$cc.gateway}).Count -gt 0
  if(-not $hadGateway){Remove-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$cc.gateway) -PolicyStore ActiveStore -Confirm:$false -ErrorAction SilentlyContinue}
  Set-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -Forwarding $c.forwarding -PolicyStore ActiveStore -ErrorAction SilentlyContinue
 }
}
Remove-Item $Owner -Force -ErrorAction SilentlyContinue
Out-J $Result ([ordered]@{
 status='PASS';state='STOPPED';recoveredOwner=$recovered;stoppedPid=[int]$o.pid;
 tunRemoved=$true;utc=[DateTimeOffset]::UtcNow.ToString('o')
})
