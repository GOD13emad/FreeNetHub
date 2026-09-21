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
$p=$null
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
 $stdout=Join-Path $Runtime 'singbox.stdout.log';$stderr=Join-Path $Runtime 'singbox.stderr.log'
 $p=Start-Process -FilePath $sb -ArgumentList @('run','-c',$cfg) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
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
  consoleIfIndex=if($console){$console.ifIndex}else{$null};uplinkIfIndex=$uplink.ifIndex;uplinkName=$uplink.Name;firewallRule=if($Mode -eq 'CONSOLE_ONLY'){$fwName}else{$null}
 }
 Out-J $Owner $owner
 Out-J $Result ([ordered]@{status='PASS';owner=$owner;consoleManual=if($Mode -eq 'CONSOLE_ONLY'){[ordered]@{ip=$ConsoleCfg.suggested_console_ip;prefix=24;gateway=$ConsoleCfg.gateway;dns=$ConsoleCfg.dns}}else{$null}})
}catch{
 # Best-effort immediate rollback if ownership was not promoted.
 if(Test-Path $Owner){ } else {
  Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue|Remove-NetFirewallRule
  if($p -and -not $p.HasExited){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}
  if($Mode -eq 'CONSOLE_ONLY' -and (Test-Path $Pre)){
   $x=Get-Content $Pre -Raw -Encoding UTF8|ConvertFrom-Json;$c=$x.console
   if($c){
    $hadGateway=@($c.addresses|Where-Object{$_.IPAddress -eq [string]$ConsoleCfg.gateway}).Count -gt 0
    if(-not $hadGateway){Remove-NetIPAddress -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -IPAddress ([string]$ConsoleCfg.gateway) -PolicyStore ActiveStore -Confirm:$false -ErrorAction SilentlyContinue}
    Set-NetIPInterface -InterfaceIndex $c.ifIndex -AddressFamily IPv4 -Forwarding $c.forwarding -PolicyStore ActiveStore -ErrorAction SilentlyContinue
   }
  }
 }
 throw
}
