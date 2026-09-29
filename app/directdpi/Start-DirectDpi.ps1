[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$AppDir=Split-Path -Parent $PSScriptRoot
$Root=Split-Path -Parent $AppDir
$Tools=Join-Path $PSScriptRoot 'tools'
$Winws=Join-Path $Tools 'winws.exe'
$HostList=Join-Path $PSScriptRoot 'hosts.txt'
$DirectDnsDir=Join-Path $AppDir 'directdns'
$Ctrld=Join-Path $DirectDnsDir 'ctrld.exe'
$CtrldTemplate=Join-Path $DirectDnsDir 'ctrld.toml'
$DnsRuntimeDir=Join-Path $env:ProgramData 'FreeNetHub\directdns'
$DnsRuntimeConfig=Join-Path $DnsRuntimeDir 'ctrld.toml'
$StateDir=Join-Path $env:ProgramData 'FreeNetHub\directdpi'
$StatePath=Join-Path $StateDir 'state.json'
$EvidencePath=Join-Path $Root 'evidence\R36_DIRECT_DPI_RUNTIME.json'
$Interface=''
$script:DirectLocalIp=''

$Expected=@{
 'winws.exe'='A14BFF1DF6234EA555D2E0C61B589F0707C0B12D6C9B7EECCDA76012154996E8'
 'WinDivert.dll'='C1E060EE19444A259B2162F8AF0F3FE8C4428A1C6F694DCE20DE194AC8D7D9A2'
 'WinDivert64.sys'='8DA085332782708D8767BCACE5327A6EC7283C17CFB85E40B03CD2323A90DDC2'
 'cygwin1.dll'='103104A52E5293CE418944725DF19E2BF81AD9269B9A120D71D39028E821499B'
}
$ExpectedCtrld='FC966FD7DD5EE850A9709F632789CFB5BBC06C45D903D24B8ECFCE3306B658CD'
$ExpectedCtrldConfig='2E1AF2EF934367465B15284DE93016B839849D717F9A8DC4AC18858FC123EAE2'

function Test-Admin{
 $id=[Security.Principal.WindowsIdentity]::GetCurrent()
 $p=[Security.Principal.WindowsPrincipal]::new($id)
 return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Write-JsonAtomic([string]$Path,$Value){
 $dir=Split-Path -Parent $Path
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
 [IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 18),[Text.UTF8Encoding]::new($false))
 [IO.File]::Move($tmp,$Path,$true)
}
function Resolve-PhysicalDefaultInterface{
 $routes=@(
  Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
   Where-Object {$_.State -eq 'Alive'} |
   Sort-Object @{Expression={[int]$_.RouteMetric+[int]$_.InterfaceMetric}},RouteMetric,InterfaceMetric
 )
 if(-not $routes.Count){throw 'DIRECT_DPI_NO_DEFAULT_ROUTE'}
 $r=$routes[0]
 $ip=Get-NetIPAddress -InterfaceIndex $r.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object {$_.IPAddress -and $_.IPAddress -notlike '169.254.*'} |
  Select-Object -First 1
 $ad=Get-NetAdapter -InterfaceIndex $r.InterfaceIndex -ErrorAction SilentlyContinue
 if(-not $ip -or -not $ad -or $ad.Status -ne 'Up'){throw 'DIRECT_DPI_DEFAULT_ROUTE_UNUSABLE'}
 if($ad.InterfaceDescription -match '(?i)Wintun|WireGuard|TAP|TUN|VPN|Loopback'){throw 'DIRECT_DPI_DEFAULT_ROUTE_NOT_PHYSICAL'}
 [pscustomobject]@{Alias=[string]$ad.Name;Index=[int]$r.InterfaceIndex;LocalIp=[string]$ip.IPAddress;NextHop=[string]$r.NextHop;Description=[string]$ad.InterfaceDescription}
}
function Get-OwnedDrivers{
 @(
  Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue |
   Where-Object {$_.Name -match '^WinDivert' -and $_.PathName -and $_.PathName.Contains($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)}
 )
}
function Stop-OwnedWinws{
 Get-Process winws -ErrorAction SilentlyContinue |
  Where-Object {$_.Path -and $_.Path.StartsWith($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)} |
  Stop-Process -Force -ErrorAction SilentlyContinue
 Start-Sleep -Milliseconds 350
 foreach($d in @(Get-OwnedDrivers)){
  & sc.exe stop $d.Name|Out-Null
  Start-Sleep -Milliseconds 200
  & sc.exe delete $d.Name|Out-Null
 }
 Start-Sleep -Milliseconds 500
}
function Get-CtrldService{
 Get-CimInstance Win32_Service -Filter "Name='ctrld'" -ErrorAction SilentlyContinue
}
function Test-OwnedCtrldService($svc){
 if(-not $svc -or -not $svc.PathName){return $false}
 return $svc.PathName.Contains($Ctrld,[StringComparison]::OrdinalIgnoreCase)
}
function Get-CtrldCatchAll{
 @(
  Get-DnsClientNrptRule -ErrorAction SilentlyContinue |
   Where-Object {
    $ns=@($_.Namespace)|ForEach-Object{[string]$_}
    $sv=@($_.NameServers)|ForEach-Object{[string]$_}
    ($ns -contains '.') -and ($sv -contains '::1')
   } |
   ForEach-Object {[pscustomobject]@{Name=[string]$_.Name;Namespace=@($_.Namespace);NameServers=@($_.NameServers)}}
 )
}
function Cleanup-OwnedCtrld([string]$Iface){
 $svc=Get-CtrldService
 if($svc -and -not(Test-OwnedCtrldService $svc)){throw 'DIRECT_DNS_FOREIGN_CTRLD_SERVICE'}
 if($svc){
  $out=@(& $Ctrld uninstall --iface $Iface -v 2>&1)
  $code=$LASTEXITCODE
  Start-Sleep -Seconds 2
  $svc2=Get-CtrldService
  if($svc2 -and (Test-OwnedCtrldService $svc2)){
   & sc.exe stop ctrld|Out-Null
   Start-Sleep -Milliseconds 500
   & sc.exe delete ctrld|Out-Null
   Start-Sleep -Milliseconds 700
  }
  if($code -ne 0 -and (Get-CtrldService)){throw ('DIRECT_DNS_UNINSTALL_EXIT_'+$code)}
 }
 Get-Process ctrld -ErrorAction SilentlyContinue |
  Where-Object {$_.Path -and $_.Path.StartsWith($DirectDnsDir,[StringComparison]::OrdinalIgnoreCase)} |
  Stop-Process -Force -ErrorAction SilentlyContinue
 Start-Sleep -Milliseconds 300
}
function Restore-Prestate($s){
 Stop-OwnedWinws
 try{Cleanup-OwnedCtrld ([string]$s.interface)}catch{}
 if([string]$s.preDnsMode -eq 'DHCP'){
  Set-DnsClientServerAddress -InterfaceAlias ([string]$s.interface) -ResetServerAddresses
 }elseif(@($s.preDns).Count){
  Set-DnsClientServerAddress -InterfaceAlias ([string]$s.interface) -ServerAddresses @($s.preDns)
 }
 Clear-DnsClientCache -ErrorAction SilentlyContinue
 Remove-Item -LiteralPath $DnsRuntimeDir -Recurse -Force -ErrorAction SilentlyContinue
}
function Curl-Probe([string]$Url,[int]$Timeout=8){
 $tmp=[IO.Path]::GetTempFileName()
 try{
  if(-not $script:DirectLocalIp){throw 'DIRECT_DPI_LOCAL_IP_UNRESOLVED'}
  $meta=& curl.exe -4 --interface $script:DirectLocalIp --noproxy '*' -sS -o $tmp -w '%{http_code}|%{remote_ip}|%{time_connect}|%{time_appconnect}|%{time_total}' --max-time $Timeout $Url 2>&1
  [ordered]@{url=$Url;exit=$LASTEXITCODE;meta=($meta -join [Environment]::NewLine);bytes=(Get-Item $tmp).Length}
 }finally{
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
 }
}
function Dns-Probe([string]$Name){
 try{
  $sw=[Diagnostics.Stopwatch]::StartNew()
  $a=@([System.Net.Dns]::GetHostAddresses($Name)|Where-Object AddressFamily -eq InterNetwork|ForEach-Object IPAddressToString|Select-Object -Unique)
  $sw.Stop()
  [ordered]@{
   name=$Name;ok=($a.Count -gt 0);ms=$sw.ElapsedMilliseconds;answers=$a
   private=@($a|Where-Object{$_ -match '^(10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)'})
  }
 }catch{
  [ordered]@{name=$Name;ok=$false;answers=@();private=@();error=$_.Exception.Message}
 }
}
function Get-IcsState{
 $s=Get-CimInstance Win32_Service -Filter "Name='SharedAccess'" -ErrorAction SilentlyContinue
 if(-not $s){return [ordered]@{exists=$false;state='';pid=0}}
 [ordered]@{exists=$true;state=[string]$s.State;pid=[int64]$s.ProcessId}
}

if(-not(Test-Admin)){
 $pwsh=(Get-Command pwsh.exe -ErrorAction Stop).Source
 $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath)
 $p=Start-Process -FilePath $pwsh -Verb RunAs -ArgumentList $args -PassThru -Wait
 exit $p.ExitCode
}

$route=Resolve-PhysicalDefaultInterface
$Interface=[string]$route.Alias
$script:DirectLocalIp=[string]$route.LocalIp

foreach($n in $Expected.Keys){
 $f=Join-Path $Tools $n
 if(-not(Test-Path -LiteralPath $f)){throw ('DIRECT_DPI_BINARY_MISSING_'+$n)}
 if((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash -ne $Expected[$n]){throw ('DIRECT_DPI_HASH_MISMATCH_'+$n)}
}
if(-not(Test-Path -LiteralPath $Ctrld)){throw 'DIRECT_DNS_BINARY_MISSING'}
if((Get-FileHash -LiteralPath $Ctrld -Algorithm SHA256).Hash -ne $ExpectedCtrld){throw 'DIRECT_DNS_BINARY_HASH_MISMATCH'}
if(-not(Test-Path -LiteralPath $CtrldTemplate)){throw 'DIRECT_DNS_CONFIG_MISSING'}
if((Get-FileHash -LiteralPath $CtrldTemplate -Algorithm SHA256).Hash -ne $ExpectedCtrldConfig){throw 'DIRECT_DNS_CONFIG_HASH_MISMATCH'}
if(@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')}).Count){throw 'DIRECT_DPI_REFUSE_FULL_ROUTE_OVERRIDE'}

$svcPre=Get-CtrldService
if($svcPre -and -not(Test-OwnedCtrldService $svcPre)){throw 'DIRECT_DNS_FOREIGN_CTRLD_SERVICE'}

if(Test-Path -LiteralPath $StatePath){
 $old=Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8|ConvertFrom-Json
 $svc=Get-CtrldService
 $winwsAlive=$false
 if($old.pid){$winwsAlive=[bool](Get-Process -Id ([int]$old.pid) -ErrorAction SilentlyContinue)}
 if([string]$old.phase -eq 'ACTIVE' -and $winwsAlive -and $svc -and (Test-OwnedCtrldService $svc) -and $svc.State -eq 'Running'){
  [ordered]@{schema=1;status='ALREADY_ACTIVE';pid=[int]$old.pid;state=$StatePath}|ConvertTo-Json -Depth 5
  exit 0
 }
 Restore-Prestate $old
 Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
}

if(Get-CtrldService){throw 'DIRECT_DNS_STALE_SERVICE_WITHOUT_STATE'}
if(Get-Process ctrld -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($DirectDnsDir,[StringComparison]::OrdinalIgnoreCase)}){throw 'DIRECT_DNS_STALE_PROCESS_WITHOUT_STATE'}

New-Item -ItemType Directory -Force -Path $StateDir,(Join-Path $Root 'evidence')|Out-Null
$preDns=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4 -ErrorAction Stop).ServerAddresses)
$preNetsh=(netsh interface ipv4 show dnsservers name=$Interface|Out-String)
$preDnsMode=$(if($preNetsh -match 'DHCP'){'DHCP'}else{'STATIC'})
$preCatchAll=@(Get-CtrldCatchAll)
$preIcs=Get-IcsState
$runtimeState=[ordered]@{
 schema=2;phase='PREPARED';interface=$Interface;pid=0
 preDns=$preDns;preDnsMode=$preDnsMode;preNetsh=$preNetsh
 preCtrldCatchAllCount=$preCatchAll.Count
 preIcs=$preIcs
 dnsRuntimeConfig=$DnsRuntimeConfig
 directDns=[ordered]@{engine='ctrld';version='1.5.7';listener='[::1]:53';upstream='https://76.76.10.11/p0'}
 route=[ordered]@{interfaceIndex=$route.Index;localIp=$route.LocalIp;nextHop=$route.NextHop}
 hostlist=$HostList;winws=$Winws;prepared=(Get-Date).ToString('o')
}
Write-JsonAtomic $StatePath $runtimeState

$ev=[ordered]@{
 schema=2;status='FAIL';mode='DIRECT_ENCRYPTED_DNS_PLUS_DPI_NO_VPN_NO_PROXY'
 pre=[ordered]@{dns=$preDns;dnsMode=$preDnsMode;ctrldCatchAll=$preCatchAll;ics=$preIcs}
 dnsStage=$null;live=$null;cleanup=$null;error=''
}
$proc=$null
try{
 Stop-OwnedWinws
 New-Item -ItemType Directory -Force -Path $DnsRuntimeDir|Out-Null
 Copy-Item -LiteralPath $CtrldTemplate -Destination $DnsRuntimeConfig -Force
 if((Get-FileHash -LiteralPath $DnsRuntimeConfig -Algorithm SHA256).Hash -ne $ExpectedCtrldConfig){throw 'DIRECT_DNS_RUNTIME_CONFIG_COPY_MISMATCH'}

 $startOut=@(& $Ctrld start --config $DnsRuntimeConfig --intercept-mode dns --iface $Interface -v 2>&1)
 $startCode=$LASTEXITCODE
 if($startCode -ne 0){throw ('DIRECT_DNS_START_EXIT_'+$startCode+'_'+($startOut -join ' | '))}
 Start-Sleep -Seconds 3

 $svc=Get-CtrldService
 if(-not $svc -or -not(Test-OwnedCtrldService $svc) -or $svc.State -ne 'Running'){throw 'DIRECT_DNS_SERVICE_NOT_RUNNING'}
 $udp=@(Get-NetUDPEndpoint -LocalAddress '::1' -LocalPort 53 -ErrorAction SilentlyContinue)
 $tcp=@(Get-NetTCPConnection -LocalAddress '::1' -LocalPort 53 -State Listen -ErrorAction SilentlyContinue)
 if(-not $udp.Count -or -not $tcp.Count){throw 'DIRECT_DNS_IPV6_LOOPBACK_LISTENER_MISSING'}

 $icsNow=Get-IcsState
 if($preIcs.exists -and ($icsNow.state -ne $preIcs.state -or $icsNow.pid -ne $preIcs.pid)){throw 'DIRECT_DNS_ICS_CHANGED'}

 Clear-DnsClientCache
 Start-Sleep -Seconds 1
 $dy=Dns-Probe 'www.youtube.com'
 $dg=Dns-Probe 'github.com'
 $do=Dns-Probe 'api.openai.com'
 foreach($d in @($dy,$dg,$do)){if(-not $d.ok -or $d.private.Count){throw ('DIRECT_DNS_RESOLUTION_FAIL_'+$d.name)}}
 $cd0=Curl-Probe 'https://76.76.10.11/p0' 5
 if($cd0.exit -ne 0 -or $cd0.meta -notmatch '^(200|400)\|'){throw 'DIRECT_DNS_UPSTREAM_HTTPS_FAIL'}
 $ev.dnsStage=[ordered]@{
  startOutput=$startOut;service=$svc|Select-Object Name,State,StartMode,PathName
  listener=[ordered]@{udp=$udp;tcp=$tcp}
  dns=@($dy,$dg,$do);controlD=$cd0
  nrpt=@(Get-CtrldCatchAll);ics=$icsNow
 }

 $args=@(
  '--wf-l3=ipv4','--wf-tcp=443',
  '--filter-l3=ipv4','--filter-tcp=443',
  ('--hostlist='+$HostList),
  '--ipset-exclude-ip=76.76.10.11',
  '--dpi-desync=fake,multidisorder',
  '--dpi-desync-split-pos=1,midsld',
  '--dpi-desync-fooling=badseq,md5sig'
 )
 $proc=Start-Process -FilePath $Winws -ArgumentList $args -WorkingDirectory $Tools -WindowStyle Hidden -PassThru
 Start-Sleep -Seconds 3
 if($proc.HasExited){throw ('DIRECT_DPI_WINWS_EXITED_'+$proc.ExitCode)}

 Clear-DnsClientCache
 Start-Sleep -Milliseconds 500
 $dy2=Dns-Probe 'www.youtube.com'
 $yt=Curl-Probe 'https://www.youtube.com/generate_204' 8
 $oa=Curl-Probe 'https://api.openai.com/v1/models' 6
 $gh=Curl-Probe 'https://github.com/' 6
 $routes=@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')})
 $proxy=(netsh winhttp show proxy|Out-String)
 $icsLive=Get-IcsState

 $ytOk=($yt.exit -eq 0 -and $yt.meta -match '^(200|204)\|')
 $dnsOk=($dy2.ok -and $dy2.private.Count -eq 0)
 $oaOk=($oa.meta -match '^(200|401|403)\|')
 $ghOk=($gh.meta -match '^(200|301|302)\|')
 $direct=($routes.Count -eq 0 -and $proxy -match 'Direct access')
 $icsOk=(-not $preIcs.exists) -or ($icsLive.state -eq $preIcs.state -and $icsLive.pid -eq $preIcs.pid)
 if(-not($ytOk -and $dnsOk -and $oaOk -and $ghOk -and $direct -and $icsOk)){throw 'DIRECT_DPI_END_TO_END_NOT_PASS'}

 $ev.live=[ordered]@{
  pid=$proc.Id;dns=$dy2;youtube=$yt;openai=$oa;github=$gh
  broadRoutes=$routes.Count;proxy=$proxy;ics=$icsLive
  drivers=@(Get-OwnedDrivers|Select-Object Name,State,StartMode,PathName)
 }
 $runtimeState.phase='ACTIVE'
 $runtimeState.pid=$proc.Id
 $runtimeState.started=(Get-Date).ToString('o')
 Write-JsonAtomic $StatePath $runtimeState
 $ev.status='PASS_ACTIVE_DIRECT_DPI'
 Write-JsonAtomic $EvidencePath $ev
 [ordered]@{schema=2;status=$ev.status;pid=$proc.Id;state=$StatePath;evidence=$EvidencePath}|ConvertTo-Json -Depth 6
 exit 0
}catch{
 $ev.error=$_.Exception.Message
 try{
  if(Test-Path -LiteralPath $StatePath){
   $s=Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8|ConvertFrom-Json
   Restore-Prestate $s
  }else{
   if($proc -and -not $proc.HasExited){Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}
   Stop-OwnedWinws
  }
 }catch{$ev.cleanup=[ordered]@{rollbackError=$_.Exception.Message}}
 Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
 $ev.cleanup=[ordered]@{
  dns=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses)
  ctrldService=@(Get-CtrldService|Select-Object Name,State,PathName)
  ctrldProcess=@(Get-Process ctrld -ErrorAction SilentlyContinue|Select-Object Id,Path)
  ctrldCatchAll=@(Get-CtrldCatchAll)
  ics=Get-IcsState
  winws=@(Get-Process winws -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)}|Select-Object Id)
  drivers=@(Get-OwnedDrivers)
 }
 Write-JsonAtomic $EvidencePath $ev
 [ordered]@{schema=2;status='FAIL_ROLLED_BACK';error=$ev.error;evidence=$EvidencePath}|ConvertTo-Json -Depth 6
 exit 8
}
