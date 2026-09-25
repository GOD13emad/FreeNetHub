[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Gateway=Join-Path $Root 'gateway'
$Runtime=Join-Path $Gateway 'runtime'
$Evidence=Join-Path $Root 'evidence\GATEWAY_PC_TUNNEL_42C2_ACCEPTANCE.json'
$Engine=Join-Path $Root 'app\engine.py'
$Generator=Join-Path $Gateway 'generate_config.py'
$Apply=Join-Path $Gateway 'apply_elevated.ps1'
$Stop=Join-Path $Gateway 'stop_elevated.ps1'
$Stun=Join-Path $Gateway 'tests\direct_stun.py'
$Expected=@{
 $Engine='F6FB91C4714A73D6A42BF15BC9F41D134352978380B536CF586327052221C1A7'
 $Generator='A0CB20B18FB2D6AA48499F8D7BE69C4C6A105E94DA4FB14178C80B02C9BF7A29'
 $Apply='36B8474E9A8546A99B089A3031B11E1F7B19F1A7B5C93970E39FC93D79945596'
 $Stop='7D019A0E4D5737DFE3B28B48F49609A85E83DADF3CF642403CE18475A2C2B112'
 $Stun='8B24DAC139E85681BE8ECC3A5E47068E37837480EEFEACAB6F6CF1C407D7582F'
}
$Ports=19410,19413,19414,19450,19452,19453
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Optional($o,[string]$n){$p=$o.PSObject.Properties[$n];if($p){$p.Value}else{$null}}
function Write-J($x){$x|ConvertTo-Json -Depth 25|Set-Content -LiteralPath $Evidence -Encoding UTF8}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Snapshot-Network{
 $routes=@(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop|
   Select-Object NextHop,InterfaceIndex,RouteMetric|Sort-Object InterfaceIndex,NextHop,RouteMetric)
 $dns=@(Get-DnsClientServerAddress -ErrorAction Stop|ForEach-Object{
   [pscustomobject]@{InterfaceIndex=$_.InterfaceIndex;AddressFamily=[string]$_.AddressFamily;ServerAddresses=@($_.ServerAddresses)}
 }|Sort-Object InterfaceIndex,AddressFamily)
 $inet=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
 [pscustomobject]@{
  routes=$routes;dns=$dns;
  proxy=[pscustomobject]@{ProxyEnable=(Optional $inet 'ProxyEnable');ProxyServer=(Optional $inet 'ProxyServer');AutoConfigURL=(Optional $inet 'AutoConfigURL')}
 }
}
function Run-Engine([string]$Action,[string]$Mode,[int]$Budget){
 $j=[guid]::NewGuid().ToString('N')
 & $Python $Engine --action $Action --mode $Mode --job $j --budget $Budget|Out-Null
 $ec=$LASTEXITCODE
 $rec=Get-Content (Join-Path $Root ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
 [pscustomobject]@{exit=$ec;record=$rec}
}
function Listener([int]$Port){
 @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}
function Tun{
 @(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'})
}
function Emergency-Cleanup{
 $actions=@();$errs=@()
 try{
  $a=$null
  $ar=Join-Path $Runtime 'apply_result.json'
  if(Test-Path $ar){$a=Get-Content $ar -Raw -Encoding UTF8|ConvertFrom-Json}
  if($a -and $a.status -eq 'PASS' -and $a.owner){
   $o=$a.owner
   $gp=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue
   $cp=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$o.pid) -ErrorAction SilentlyContinue
   if($gp -and $cp -and $cp.ExecutablePath -eq [string]$o.path -and $gp.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks){
    Stop-Process -Id ([int]$o.pid) -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    if(Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue){& taskkill.exe /PID ([int]$o.pid) /T /F|Out-Null}
    $actions+=('Killed exact sing-box '+$o.pid)
   }
  }
  Start-Sleep -Seconds 1
  $t=Tun|Select-Object -First 1
  if($t -and $t.ComponentID -eq 'Wintun' -and $t.Virtual -and $t.PnPDeviceID){
   & pnputil.exe /remove-device ([string]$t.PnPDeviceID)|Out-Null
   Start-Sleep -Seconds 1
   $actions+='Removed exact FreeNetHub Wintun device'
  }
  Remove-Item (Join-Path $Runtime 'owner.json') -Force -ErrorAction SilentlyContinue
 }catch{$errs+=$_.Exception.Message}
 [pscustomobject]@{actions=$actions;errors=$errs}
}

$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(!$admin){throw 'RUNNER_NOT_ELEVATED'}
foreach($p in $Expected.Keys){Assert ((Sha $p) -eq $Expected[$p]) ('HASH_MISMATCH '+$p)}
$sb=(Get-Content (Join-Path $Runtime 'local_gateway.json') -Raw -Encoding UTF8|ConvertFrom-Json).singbox.path
Assert ((Test-Path $sb) -and (Sha $sb) -eq 'AAD0EDE010EAFA7B277E520464F3A66FDE820103D737EFF739F40F3CC9451DCC') 'SINGBOX_PIN_FAIL'
Assert ((Tun).Count -eq 0) 'PREEXISTING_FREENETHUB_TUN'
Assert (@(Get-Process -Name sing-box -ErrorAction SilentlyContinue).Count -eq 0) 'PREEXISTING_SINGBOX'
Assert (@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort}).Count -eq 0) 'PREEXISTING_PROVIDER'
Remove-Item $Evidence -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $Runtime 'singbox.stdout.log'),(Join-Path $Runtime 'singbox.stderr.log'),(Join-Path $Runtime 'apply_result.json'),(Join-Path $Runtime 'stop_result.json') -Force -ErrorAction SilentlyContinue

$pre=Snapshot-Network
$details=[ordered]@{}
$status='FAIL';$error='';$providerStarted=$false;$gatewayApplied=$false
try{
 $preTrace=& curl.exe -4 --max-time 15 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 $details.preTrace=$preTrace
 $preStun=& $Python $Stun|Out-String
 $details.preStun=try{$preStun|ConvertFrom-Json}catch{$preStun}

 $con=Run-Engine 'Connect' 'WARP' 220
 Assert ($con.exit -eq 0 -and [bool]$con.record.result.healthy) 'WARP_PROVIDER_CONNECT_FAIL'
 $providerStarted=$true
 $details.providerBeforeTun=$con.record.result
 Assert ((Listener 19410).Count -eq 1) 'WARP_LISTENER_MISSING_BEFORE_TUN'

 $cfg=Join-Path $Runtime 'pc_warp_42c2.json'
 & $Python $Generator --mode PC_TUNNEL --provider WARP --output $cfg|Out-Null
 Assert ($LASTEXITCODE -eq 0) 'CONFIG_GENERATE_FAIL'
 $cj=Get-Content $cfg -Raw -Encoding UTF8|ConvertFrom-Json
 $excluded=@($cj.inbounds[0].route_exclude_address)
 Assert ($excluded -contains '162.159.192.0/24') 'UNDERLAY_EXCLUSION_MISSING'
 $details.routeExclude=$excluded
 & $sb check -c $cfg
 Assert ($LASTEXITCODE -eq 0) 'CONFIG_CHECK_FAIL'

 & $Apply -Mode PC_TUNNEL -ConfigPath $cfg -ConfigSha256 (Sha $cfg)
 $ar=Get-Content (Join-Path $Runtime 'apply_result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ($ar.status -eq 'PASS') 'APPLY_FAIL'
 $gatewayApplied=$true
 Start-Sleep -Seconds 3

 $tun=Tun|Select-Object -First 1
 Assert ($tun -and $tun.Status -eq 'Up') 'TUN_NOT_UP'
 Assert ((Listener 19410).Count -eq 1) 'WARP_LISTENER_DIED_AFTER_TUN'

 # Provider itself must still work through loopback while its underlay bypasses TUN.
 $providerTrace=& curl.exe -4 --socks5-hostname 127.0.0.1:19410 --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0) 'PROVIDER_TRACE_DIED_AFTER_TUN'
 $details.providerTraceDuringTun=$providerTrace

 # System-wide traffic must traverse FreeNetHub TUN -> WARP SOCKS.
 $trace=& curl.exe -4 --max-time 25 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0) 'SYSTEM_CLOUDFLARE_TRACE_FAIL'
 $td=[ordered]@{}
 foreach($line in ($trace -split '\r?\n')){if($line -match '^([^=]+)=(.*)$'){$td[$matches[1]]=$matches[2]}}
 Assert ($td['warp'] -eq 'on') 'SYSTEM_TRACE_WARP_NOT_ON'
 $details.systemTrace=$td

 $yt=& curl.exe -4 --max-time 25 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0 -and $yt.Trim() -eq '204') 'SYSTEM_YOUTUBE_204_FAIL'
 $details.youtubeCode=$yt.Trim()

 $dns=Resolve-DnsName www.cloudflare.com -Type A -DnsOnly -ErrorAction Stop|Select-Object -First 1
 Assert ([bool]$dns.IPAddress) 'SYSTEM_DNS_FAIL'
 $details.dnsA=$dns.IPAddress

 $udp=& $Python $Stun|Out-String
 Assert ($LASTEXITCODE -eq 0) 'SYSTEM_UDP_STUN_FAIL'
 $details.systemUdpStun=$udp|ConvertFrom-Json

 # Prove provider remained alive after all system tests.
 Assert ((Listener 19410).Count -eq 1) 'WARP_LISTENER_DIED_DURING_TEST'
 $ver=Run-Engine 'Verify' 'WARP' 60
 Assert ($ver.exit -eq 0 -and [bool]$ver.record.result.healthy) 'WARP_PROVIDER_VERIFY_AFTER_TUN_FAIL'
 $details.providerAfterTun=$ver.record.result

 $details.tun=[ordered]@{
  name=$tun.Name;ifIndex=$tun.ifIndex;description=$tun.InterfaceDescription;
  ipv4=@(Get-NetIPAddress -InterfaceIndex $tun.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object IPAddress,PrefixLength);
  defaultRoutes=@(Get-NetRoute -InterfaceIndex $tun.ifIndex -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/0','::/0')}|Select-Object AddressFamily,DestinationPrefix,NextHop,RouteMetric)
 }
 $status='PASS'
}catch{
 $error=$_.Exception.Message
 $details.failureState=[ordered]@{
  warpListener=(Listener 19410).Count
  tun=@(Tun|Select-Object Name,Status,ifIndex,InterfaceDescription)
  singBox=@(Get-Process -Name sing-box -ErrorAction SilentlyContinue|Select-Object Id,ProcessName)
  singBoxErrors=@(Select-String -LiteralPath (Join-Path $Runtime 'singbox.stderr.log') -Pattern 'ERROR|WARN' -ErrorAction SilentlyContinue|Select-Object -Last 40|ForEach-Object{$_.Line})
  warpTail=if(Test-Path (Join-Path $Root 'data\WARP\stdout.log')){Get-Content (Join-Path $Root 'data\WARP\stdout.log') -Tail 60|Out-String}else{''}
 }
}finally{
 $details.stop=[ordered]@{}
 try{
  if((Test-Path (Join-Path $Runtime 'owner.json')) -or (Tun).Count -gt 0 -or @(Get-Process -Name sing-box -ErrorAction SilentlyContinue).Count -gt 0){
   & $Stop|Out-Null
   $details.stop.primary=if(Test-Path (Join-Path $Runtime 'stop_result.json')){Get-Content (Join-Path $Runtime 'stop_result.json') -Raw|ConvertFrom-Json}else{$null}
  }
 }catch{
  $details.stop.primaryError=$_.Exception.Message
  $details.stop.emergency=Emergency-Cleanup
 }
 try{
  if($providerStarted){
   $st=Run-Engine 'Stop' 'AUTO' 90
   $details.providerStop=$st.record.result
  }
 }catch{$details.providerStopError=$_.Exception.Message}
 Start-Sleep -Seconds 2

 $post=Snapshot-Network
 $leftTun=@(Tun)
 $leftSb=@(Get-Process -Name sing-box -ErrorAction SilentlyContinue)
 $leftListeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort})
 $networkSame=(($pre|ConvertTo-Json -Depth 12 -Compress) -eq ($post|ConvertTo-Json -Depth 12 -Compress))
 $rollback=[ordered]@{
  networkPrePostUnchanged=$networkSame
  tunCount=$leftTun.Count
  singBoxCount=$leftSb.Count
  projectListenerCount=$leftListeners.Count
  ownerExists=(Test-Path (Join-Path $Runtime 'owner.json'))
 }
 if(!$networkSame -or $leftTun.Count -ne 0 -or $leftSb.Count -ne 0 -or $leftListeners.Count -ne 0 -or $rollback.ownerExists){
  $status='FAIL'
  if(!$error){$error='ROLLBACK_GATE_FAIL'}
 }
 $final=[ordered]@{
  schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');product='FreeNet Hub Gateway';
  candidate='4.2C2';scope='PC_TUNNEL';test=$status;error=$error;rollback=$rollback;details=$details
 }
 Write-J $final
}
$r=Get-Content $Evidence -Raw -Encoding UTF8|ConvertFrom-Json
$r|ConvertTo-Json -Depth 25
if($r.test -ne 'PASS'){exit 20}
