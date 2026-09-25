[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Evidence=Join-Path $Root 'evidence\GATEWAY_PC_TUNNEL_42C1_ACCEPTANCE.json'
$Gateway=Join-Path $Root 'gateway'
$Runtime=Join-Path $Gateway 'runtime'
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
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Write-J($x){$x|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $Evidence -Encoding UTF8}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Optional($o,[string]$n){$p=$o.PSObject.Properties[$n];if($p){$p.Value}else{$null}}
function Snapshot{
 $def=@(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop|Select-Object NextHop,InterfaceIndex,RouteMetric|Sort-Object InterfaceIndex,NextHop,RouteMetric)
 $dns=@(Get-DnsClientServerAddress -ErrorAction Stop|ForEach-Object{[pscustomobject]@{InterfaceIndex=$_.InterfaceIndex;AddressFamily=[string]$_.AddressFamily;ServerAddresses=@($_.ServerAddresses)}}|Sort-Object InterfaceIndex,AddressFamily)
 $inet=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
 [pscustomobject]@{defaultRoutes=$def;dns=$dns;proxy=[pscustomobject]@{ProxyEnable=(Optional $inet 'ProxyEnable');ProxyServer=(Optional $inet 'ProxyServer');AutoConfigURL=(Optional $inet 'AutoConfigURL')}}
}
function Run-Engine([string]$a,[string]$m,[int]$budget){
 $j=[guid]::NewGuid().ToString('N')
 & $Python $Engine --action $a --mode $m --job $j --budget $budget|Out-Null
 $ec=$LASTEXITCODE
 $r=Get-Content (Join-Path $Root ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
 [pscustomobject]@{exit=$ec;record=$r}
}
$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(!$admin){throw 'RUNNER_NOT_ELEVATED'}
foreach($p in $Expected.Keys){Assert ((Sha $p) -eq $Expected[$p]) ('HASH_MISMATCH '+$p)}
$sb=(Get-Content (Join-Path $Runtime 'local_gateway.json') -Raw -Encoding UTF8|ConvertFrom-Json).singbox.path
Assert ((Test-Path $sb) -and (Sha $sb) -eq 'AAD0EDE010EAFA7B277E520464F3A66FDE820103D737EFF739F40F3CC9451DCC') 'SINGBOX_PIN_FAIL'
Assert (!(Test-Path (Join-Path $Runtime 'owner.json'))) 'GATEWAY_ALREADY_ACTIVE'
$ports=19410,19413,19414,19450,19452,19453
Assert (@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count -eq 0) 'PROJECT_PROVIDER_ALREADY_ACTIVE'
$pre=Snapshot
$startedProvider=$false
$testStatus='FAIL'
$err=''
$details=[ordered]@{}
try{
 $beforeStun=& $Python $Stun|Out-String
 $details.preStun=try{$beforeStun|ConvertFrom-Json}catch{$beforeStun}
 $con=Run-Engine 'Connect' 'WARP' 200
 Assert ($con.exit -eq 0 -and [bool]$con.record.result.healthy) 'WARP_PROVIDER_CONNECT_FAIL'
 $startedProvider=$true
 $details.provider=$con.record.result
 $cfg=Join-Path $Runtime 'pc_acceptance.json'
 & $Python $Generator --mode PC_TUNNEL --provider WARP --output $cfg|Out-Null
 Assert ($LASTEXITCODE -eq 0) 'CONFIG_GENERATE_FAIL'
 $ch=Sha $cfg
 & $Apply -Mode PC_TUNNEL -ConfigPath $cfg -ConfigSha256 $ch
 $ar=Get-Content (Join-Path $Runtime 'apply_result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ($ar.status -eq 'PASS') 'APPLY_FAIL'
 Start-Sleep -Seconds 2
 $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}|Select-Object -First 1
 Assert ($tun -and $tun.Status -eq 'Up') 'TUN_NOT_UP'
 $trace=& curl.exe -4 --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0) 'CLOUDFLARE_TRACE_FAIL'
 $td=@{}
 foreach($line in ($trace -split '\r?\n')){if($line -match '^([^=]+)=(.*)$'){$td[$matches[1]]=$matches[2]}}
 Assert ($td['warp'] -eq 'on') 'SYSTEM_TRACE_WARP_NOT_ON'
 $yt=& curl.exe -4 --max-time 20 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0 -and $yt.Trim() -eq '204') 'YOUTUBE_204_FAIL'
 $dns=Resolve-DnsName www.cloudflare.com -Type A -DnsOnly -ErrorAction Stop|Select-Object -First 1
 Assert ([bool]$dns.IPAddress) 'DNS_RESOLUTION_FAIL'
 $duringStun=& $Python $Stun|Out-String
 Assert ($LASTEXITCODE -eq 0) 'SYSTEM_UDP_STUN_FAIL'
 $sj=$duringStun|ConvertFrom-Json
 $dnsIface=Get-DnsClientServerAddress -InterfaceIndex $tun.ifIndex -ErrorAction SilentlyContinue|Select-Object InterfaceIndex,AddressFamily,ServerAddresses
 $routes=@(Get-NetRoute -InterfaceIndex $tun.ifIndex -ErrorAction SilentlyContinue|Select-Object DestinationPrefix,NextHop,RouteMetric)
 $details.tun=[ordered]@{Name=$tun.Name;IfIndex=$tun.ifIndex;Description=$tun.InterfaceDescription;Dns=$dnsIface;Routes=$routes}
 $details.trace=$td
 $details.youtubeCode=$yt.Trim()
 $details.dnsA=$dns.IPAddress
 $details.systemUdpStun=$sj
 $testStatus='PASS'
}catch{
 $err=$_.Exception.Message
}finally{
 try{
  if(Test-Path (Join-Path $Runtime 'owner.json')){& $Stop}
 }catch{$err+=('|STOP:'+ $_.Exception.Message)}
 try{
  if($startedProvider){$st=Run-Engine 'Stop' 'AUTO' 60;$details.providerStop=$st.record.result}
 }catch{$err+=('|PROVIDER_STOP:'+ $_.Exception.Message)}
 Start-Sleep -Seconds 1
 $post=Snapshot
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
 $tunLeft=@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub' -and $_.Status -ne 'Not Present'})
 $rollback=(($pre|ConvertTo-Json -Depth 10 -Compress) -eq ($post|ConvertTo-Json -Depth 10 -Compress))
 $final=[ordered]@{
  schema=1
  utc=[DateTimeOffset]::UtcNow.ToString('o')
  product='FreeNet Hub Gateway'
  candidate='4.2C1'
  test=$testStatus
  error=$err
  rollback=[ordered]@{networkPrePostUnchanged=$rollback;projectListeners=$listeners.Count;tunAdapters=$tunLeft.Count;ownerExists=(Test-Path (Join-Path $Runtime 'owner.json'))}
  details=$details
 }
 if(!$rollback -or $listeners.Count -ne 0 -or $tunLeft.Count -ne 0 -or (Test-Path (Join-Path $Runtime 'owner.json'))){$final.test='FAIL';if(!$final.error){$final.error='ROLLBACK_GATE_FAIL'}}
 Write-J $final
}
$r=Get-Content $Evidence -Raw -Encoding UTF8|ConvertFrom-Json
$r|ConvertTo-Json -Depth 20
if($r.test -ne 'PASS'){exit 20}
