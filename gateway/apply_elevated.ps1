[CmdletBinding()]
param(
 [Parameter(Mandatory)][ValidateSet('PC_TUNNEL','CONSOLE_ONLY')][string]$Mode,
 [Parameter(Mandatory)][string]$ConfigPath,
 [Parameter(Mandatory)][string]$ConfigSha256
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime'
New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
$Result=Join-Path $Runtime 'apply_result.json'
$Owner=Join-Path $Runtime 'owner.json'
$Pre=Join-Path $Runtime 'prestate.json'
function Out-J($p,$x){$x|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $p -Encoding UTF8}
function Fail([string]$m){Out-J $Result ([ordered]@{status='FAIL';error=$m;utc=[DateTimeOffset]::UtcNow.ToString('o')});throw $m}
$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(!$admin){Fail 'ADMIN_REQUIRED'}
if(Test-Path $Owner){Fail 'GATEWAY_ALREADY_OWNED'}
if(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}){Fail 'STALE_TUN_PRESENT'}
$D=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
$S=Get-FnhSingBox;$sb=[string]$S.path
$ConsoleCfg=if($Mode -eq 'CONSOLE_ONLY'){Get-FnhConsoleConfig $D}else{Get-FnhConsoleConfig $D -AllowUnconfigured}
$cfg=(Resolve-Path -LiteralPath $ConfigPath).Path
if((Get-FileHash $cfg -Algorithm SHA256).Hash -ne $ConfigSha256){Fail 'CONFIG_HASH_MISMATCH'}
& $sb check -c $cfg
if($LASTEXITCODE -ne 0){Fail 'SINGBOX_CONFIG_CHECK_FAILED'}
$def=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0'|Sort-Object RouteMetric|Select-Object -First 1
if(!$def){Fail 'NO_DEFAULT_ROUTE'}
$uplink=Get-NetAdapter -InterfaceIndex $def.InterfaceIndex
$console=Get-NetAdapter|Where-Object{$_.HardwareInterface -and $_.InterfaceDescription -eq [string]$ConsoleCfg.adapter_description}|Select-Object -First 1
if($Mode -eq 'CONSOLE_ONLY' -and !$console){Fail 'CONSOLE_ADAPTER_NOT_FOUND'}
if($Mode -eq 'CONSOLE_ONLY' -and $console.ifIndex -eq $uplink.ifIndex){Fail 'CONSOLE_ADAPTER_IS_DEFAULT_UPLINK'}
$prestate=[ordered]@{
 utc=[DateTimeOffset]::UtcNow.ToString('o');mode=$Mode
 default=[ordered]@{ifIndex=$def.InterfaceIndex;alias=$uplink.Name;gateway=$def.NextHop}
 console=$null
}
if($console){
 $ipif=Get-NetIPInterface -InterfaceIndex $console.ifIndex -AddressFamily IPv4
 $prestate.console=[ordered]@{
  ifIndex=$console.ifIndex;guid=[string]$console.InterfaceGuid;name=$console.Name;description=$console.InterfaceDescription
  dhcp=[string]$ipif.Dhcp;forwarding=[string]$ipif.Forwarding
  addresses=@(Get-NetIPAddress -InterfaceIndex $console.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object IPAddress,PrefixLength,PrefixOrigin,SuffixOrigin)
 }
}
Out-J $Pre $prestate
$fwName='FreeNetHub Console Leak Guard'
$pcDnsGuardNames=@('FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
$cfgObject=Get-Content -LiteralPath $cfg -Raw -Encoding UTF8|ConvertFrom-Json
$pcNative=($Mode -eq 'PC_TUNNEL' -and @($cfgObject.inbounds|Where-Object { $_.type -eq 'tun' -and $_.dns_mode -eq 'native' }).Count -eq 1)
# Reject unknown/nonphysical default routes rather than assert DNS53 protection on an unsupported uplink.
if($pcNative){
 $activeProfiles=@(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop)
 $requiredProfiles=@('Domain','Private','Public')
 if($activeProfiles.Count -ne $requiredProfiles.Count -or @($activeProfiles|Where-Object{$_.Name -notin $requiredProfiles -or [string]$_.Enabled -ne 'True'}).Count -ne 0){
  Fail 'PC_NATIVE_FIREWALL_PROFILE_NOT_ENABLED'
 }
}
if($pcNative -and (-not $uplink.HardwareInterface -or [int]$uplink.InterfaceType -notin @(6,71))){Fail 'PC_NATIVE_DEFAULT_UPLINK_NOT_WIRED_OR_WIFI'}
$p=$null
$guardProc=$null
$ownedCreatedDnsRules=@()
try{
 if($Mode -eq 'CONSOLE_ONLY'){
  # Minimal mutation: preserve DHCP and every pre-existing address. Add only the
  # dedicated FreeNetHub gateway address and enable forwarding for this session.
  if(-not (Get-NetIPAddress -InterfaceIndex $console.ifIndex -AddressFamily IPv4 -IPAddress ([string]$ConsoleCfg.gateway) -ErrorAction SilentlyContinue)){
   New-NetIPAddress -InterfaceIndex $console.ifIndex -IPAddress ([string]$ConsoleCfg.gateway) -PrefixLength 24 -Type Unicast -PolicyStore ActiveStore -ErrorAction Stop|Out-Null
  }
  Set-NetIPInterface -InterfaceIndex $console.ifIndex -AddressFamily IPv4 -Forwarding Enabled -PolicyStore ActiveStore -ErrorAction Stop
  Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue|Remove-NetFirewallRule
  New-NetFirewallRule -DisplayName $fwName -Direction Outbound -Action Block -Protocol Any -LocalAddress ([string]$ConsoleCfg.subnet) -InterfaceAlias $uplink.Name -Profile Any|Out-Null
 }
 if($pcNative){
  $exists=@($pcDnsGuardNames|Where-Object{Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore -ErrorAction SilentlyContinue})
  if($exists.Count -gt 0){Fail 'PC_DNS_GUARD_PREEXISTS_REFUSE_TO_OVERWRITE'}
  # Protect both physical media types across route changes. The overlay Tailscale
  # tunnel is not a Wired/Wireless egress. Never pin only the initial uplink alias.
  foreach($spec in @(
   @{name=$pcDnsGuardNames[0];protocol='UDP';interfaceType='Wired'},
   @{name=$pcDnsGuardNames[1];protocol='TCP';interfaceType='Wired'},
   @{name=$pcDnsGuardNames[2];protocol='UDP';interfaceType='Wireless'},
   @{name=$pcDnsGuardNames[3];protocol='TCP';interfaceType='Wireless'}
  )){
   New-NetFirewallRule -Name $spec.name -DisplayName $spec.name -Direction Outbound -Action Block -Protocol $spec.protocol -RemotePort 53 -InterfaceType $spec.interfaceType -Enabled True -Profile Any -PolicyStore ActiveStore -ErrorAction Stop|Out-Null
   $ownedCreatedDnsRules+= $spec.name
   $actualType=Get-NetFirewallInterfaceTypeFilter -AssociatedNetFirewallRule (Get-NetFirewallRule -Name $spec.name -PolicyStore ActiveStore -ErrorAction Stop) -ErrorAction Stop
   if([string]$actualType.InterfaceType -ne [string]$spec.interfaceType){Fail 'PC_DNS_GUARD_INTERFACE_TYPE_MISMATCH'}
  }
  $active=@($pcDnsGuardNames|Where-Object{Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore -ErrorAction SilentlyContinue})
  if($active.Count -ne 4){Fail 'PC_DNS_GUARD_RULE_COUNT_WRONG'}
 }
 $stdout=Join-Path $Runtime 'singbox.stdout.log';$stderr=Join-Path $Runtime 'singbox.stderr.log'
 $p=Start-Process -FilePath $sb -ArgumentList @('run','-c',$cfg) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
 if($pcNative){
  $watch=Join-Path $PSScriptRoot 'dns_guard_watchdog.ps1'
  $gp=Get-Process -Id $p.Id -ErrorAction Stop
  $watchArgs=@('-NoProfile','-NonInteractive','-File',('"' + $watch + '"'),'-TargetPid',([string]$p.Id),'-StartTicks',([string]$gp.StartTime.ToUniversalTime().Ticks),'-ExpectedExe',('"' + $sb + '"'),'-UdpRule',$pcDnsGuardNames[0],'-TcpRule',$pcDnsGuardNames[1],'-UdpWirelessRule',$pcDnsGuardNames[2],'-TcpWirelessRule',$pcDnsGuardNames[3])
  $guardProc=Start-Process -FilePath 'pwsh.exe' -ArgumentList $watchArgs -WindowStyle Hidden -PassThru
  Start-Sleep -Milliseconds 250
  if(!$guardProc -or $guardProc.HasExited){Fail 'PC_DNS_GUARD_WATCHDOG_DID_NOT_START'}
 }
 Start-Sleep -Milliseconds 1200
 if($p.HasExited){Fail ('SINGBOX_EXITED_'+$p.ExitCode)}
 $deadline=[DateTime]::UtcNow.AddSeconds(12);$tun=$null
 do{
  $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$D.tun.interface_name}|Select-Object -First 1
  if($tun){break};Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 if(!$tun){Fail 'TUN_ADAPTER_NOT_CREATED'}
 $proc=Get-CimInstance Win32_Process -Filter ("ProcessId="+$p.Id)
 $gp=Get-Process -Id $p.Id
 $owner=[ordered]@{
  schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');mode=$Mode;pid=$p.Id;path=$proc.ExecutablePath;startTicks=$gp.StartTime.ToUniversalTime().Ticks
  config=$cfg;configSha256=$ConfigSha256;singBoxSha256=(Get-FileHash $sb -Algorithm SHA256).Hash
  tun=[ordered]@{name=$tun.Name;ifIndex=$tun.ifIndex;description=$tun.InterfaceDescription}
  consoleIfIndex=if($console){$console.ifIndex}else{$null};uplinkIfIndex=$uplink.ifIndex;uplinkName=$uplink.Name;firewallRule=if($Mode -eq 'CONSOLE_ONLY'){$fwName}else{$null};dnsGuardNames=if($pcNative){$pcDnsGuardNames}else{@()};dnsGuardPid=if($guardProc){$guardProc.Id}else{$null}
 }
 Out-J $Owner $owner
 Out-J $Result ([ordered]@{status='PASS';owner=$owner;consoleManual=if($Mode -eq 'CONSOLE_ONLY'){[ordered]@{ip=$ConsoleCfg.suggested_console_ip;prefix=24;gateway=$ConsoleCfg.gateway;dns=$ConsoleCfg.dns}}else{$null}})
}catch{
 $primaryError=$_.Exception.Message
 # Fail closed: any start failure must restore prestate before returning failure.
 if(Test-Path $Owner){
  $stopScript=Join-Path $PSScriptRoot 'stop_elevated.ps1'
  & pwsh.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $stopScript
  $stopExit=$LASTEXITCODE
  $stopResult=Join-Path $Runtime 'stop_result.json'
  $stopRecord=$null
  if(Test-Path $stopResult){try{$stopRecord=Get-Content $stopResult -Raw -Encoding UTF8|ConvertFrom-Json}catch{}}
  if($stopExit -ne 0 -or !$stopRecord -or [string]$stopRecord.status -ne 'PASS'){Fail ('APPLY_FAILED_PROMOTED_ROLLBACK_INCOMPLETE: '+$primaryError)}
 } else {
  if($Mode -eq 'CONSOLE_ONLY'){
   Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue|Remove-NetFirewallRule -ErrorAction SilentlyContinue
   if(Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue){Fail ('APPLY_FAILED_FIREWALL_ROLLBACK_INCOMPLETE: '+$primaryError)}
  }
  if($p -and -not $p.HasExited){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}
  if($p -and (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)){Fail ('APPLY_FAILED_PROCESS_ROLLBACK_INCOMPLETE: '+$primaryError)}
  if($pcNative){
   # Fail closed: never release physical DNS blocks while a TUN can still
   # route traffic, even if sing-box terminated before owner.json was written.
   $tunRollbackDeadline=[DateTime]::UtcNow.AddSeconds(15)
   $lingeringTun=$null
   do{
    $lingeringTun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$D.tun.interface_name}|Select-Object -First 1
    if(!$lingeringTun){break}
    Start-Sleep -Milliseconds 250
   }while([DateTime]::UtcNow -lt $tunRollbackDeadline)
   if($lingeringTun){Fail ('APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED: '+$primaryError)}
   foreach($n in $ownedCreatedDnsRules){
    $r=Get-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction SilentlyContinue
    if($r){$r|Remove-NetFirewallRule -ErrorAction SilentlyContinue}
   }
   if(@($ownedCreatedDnsRules|Where-Object{Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore -ErrorAction SilentlyContinue}).Count){
    Fail ('APPLY_FAILED_PC_DNS_GUARD_ROLLBACK_INCOMPLETE: '+$primaryError)
   }
  }
  if($Mode -eq 'CONSOLE_ONLY' -and (Test-Path $Pre)){
   $x=Get-Content $Pre -Raw -Encoding UTF8|ConvertFrom-Json;$c=$x.console
   if($c){
    $hadGateway=@($c.addresses|Where-Object{$_.IPAddress -eq [string]$ConsoleCfg.gateway}).Count -gt 0
    if(-not $hadGateway){
     Remove-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$ConsoleCfg.gateway) -PolicyStore ActiveStore -Confirm:$false -ErrorAction SilentlyContinue
     if(Get-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$ConsoleCfg.gateway) -ErrorAction SilentlyContinue){Fail ('APPLY_FAILED_GATEWAY_IP_ROLLBACK_INCOMPLETE: '+$primaryError)}
    }
    Set-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -Forwarding $c.forwarding -PolicyStore ActiveStore -ErrorAction SilentlyContinue
    $restoredIf=Get-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object -First 1
    if(!$restoredIf -or [string]$restoredIf.Forwarding -ne [string]$c.forwarding){Fail ('APPLY_FAILED_FORWARDING_ROLLBACK_INCOMPLETE: '+$primaryError)}
   }
  }
 }
 throw
}
