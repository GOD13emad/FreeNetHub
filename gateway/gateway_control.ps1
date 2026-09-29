[CmdletBinding()]
param(
 [Parameter(Mandatory)][ValidateSet('StartPc','StartConsole','Stop','StopConsole','Status')][string]$Action,
 [ValidateSet('WARP','NODE')][string]$Provider='WARP',
 [ValidateSet('SELECTED','AUTO')][string]$NodePolicy='SELECTED',
 [string]$ResultPath=''
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Session=Join-Path $Runtime 'gateway-session.json'
$Owner=Join-Path $Runtime 'owner.json'
$Defaults=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
$Python=Get-FnhPython
$Engine=Join-Path $Root 'app\engine.py'
$Generator=Join-Path $PSScriptRoot 'generate_config.py'
$Apply=Join-Path $PSScriptRoot 'apply_elevated.ps1'
$StopScript=Join-Path $PSScriptRoot 'stop_elevated.ps1'
$DirectStun=Join-Path $PSScriptRoot 'tests\direct_stun.py'
$ConsoleProfile=Join-Path $Runtime 'console.profile.json'
$WslConsole=Join-Path $PSScriptRoot 'wsl_console.ps1'
function Assert-GatewayIntegrity{
 $mp=Join-Path $PSScriptRoot 'manifest.json';if(!(Test-Path $mp)){throw 'GATEWAY_MANIFEST_MISSING'}
 $m=Get-Content $mp -Raw -Encoding UTF8|ConvertFrom-Json;if([string]$m.version -ne '4.2.0'){throw 'GATEWAY_MANIFEST_VERSION'}
 foreach($f in $m.files){
  $fp=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ([string]$f.file)));$base=[IO.Path]::GetFullPath($Root)+'\'
  if(!$fp.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw ('GATEWAY_MANIFEST_PATH_OUTSIDE_PROJECT '+$f.file)}
  if(!(Test-Path $fp -PathType Leaf)){throw ('GATEWAY_FILE_MISSING '+$f.file)}
  if((Get-Item $fp).Length -ne [long]$f.bytes){throw ('GATEWAY_SIZE_MISMATCH '+$f.file)}
  if((Get-FileHash $fp -Algorithm SHA256).Hash -ne [string]$f.sha256){throw ('GATEWAY_HASH_MISMATCH '+$f.file)}
 }
}
function Write-J([string]$p,$o){$tmp=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$o|ConvertTo-Json -Depth 24|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -LiteralPath $tmp -Destination $p -Force}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Get-BaseRouteSnapshot{
 $routes=@(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue)
 $rows=@()
 foreach($r in $routes){
  try{
   $ifi=Get-NetIPInterface -AddressFamily IPv4 -InterfaceIndex ([int]$r.InterfaceIndex) -ErrorAction Stop
   $src=Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex ([int]$r.InterfaceIndex) -ErrorAction SilentlyContinue |
    Where-Object {$_.IPAddress -and $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'} |
    Sort-Object SkipAsSource,PrefixLength | Select-Object -First 1
   if($src){
    $rows += [pscustomobject]@{
     totalMetric=([int]$r.RouteMetric+[int]$ifi.InterfaceMetric)
     ifIndex=[int]$r.InterfaceIndex;interfaceAlias=[string]$r.InterfaceAlias
     sourceAddress=[string]$src.IPAddress;nextHop=[string]$r.NextHop
     routeMetric=[int]$r.RouteMetric;interfaceMetric=[int]$ifi.InterfaceMetric
    }
   }
  }catch{}
 }
 $best=$rows|Sort-Object totalMetric,routeMetric,interfaceMetric|Select-Object -First 1
 if(!$best){throw 'BASE_ROUTE_UNAVAILABLE'}
 [ordered]@{ifIndex=$best.ifIndex;interfaceAlias=$best.interfaceAlias;sourceAddress=$best.sourceAddress;nextHop=$best.nextHop;routeMetric=$best.routeMetric;interfaceMetric=$best.interfaceMetric}
}
function Trace{
 $t=& curl.exe -4 --noproxy '*' --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'TRACE_FAIL'}
 $d=[ordered]@{};foreach($l in ($t -split '\r?\n')){if($l -match '^([^=]+)=(.*)$'){$d[$matches[1]]=$matches[2]}};return $d
}
function Target-Country{
 $p=Join-Path $Root 'settings.json'
 if(!(Test-Path $p)){return 'AUTO'}
 try{$v=[string](Get-Content $p -Raw -Encoding UTF8|ConvertFrom-Json).country;if($v){return $v.ToUpperInvariant()}}catch{}
 return 'AUTO'
}
function Geo-Country([string]$ip){
 if(!$ip){throw 'GEO_IP_MISSING'}
 $raw=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ('https://ipwho.is/'+$ip) 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'GEO_LOOKUP_FAIL'}
 $j=$raw|ConvertFrom-Json
 if(!$j.success -or -not [string]$j.country_code){throw 'GEO_LOOKUP_INVALID'}
 ([string]$j.country_code).ToUpperInvariant()
}
function Verify-ProviderUdp([string]$p,[string]$target){
 $cfg=$Defaults.providers.$p
 Assert ($null -ne $cfg) ($p+'_PROVIDER_CONFIG_MISSING')
 $port=[int]$cfg.port
 $raw=& $Python (Join-Path $PSScriptRoot 'socks_udp_probe.py') $port '127.0.0.1' 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0) ($p+'_UDP_PREFLIGHT_FAIL')
 $j=$raw|ConvertFrom-Json
 Assert ([string]$j.status -eq 'PASS') ($p+'_UDP_PREFLIGHT_FAIL')
 $country='UNVERIFIED_AUTO'
 if($target -and $target -ne 'AUTO'){
  $country=Geo-Country ([string]$j.udp_public_ip)
  Assert ($country -eq $target) ($p+'_UDP_COUNTRY_'+$country)
 }
 [ordered]@{status='PASS';publicIp=[string]$j.udp_public_ip;country=$country;countryVerified=($target -and $target -ne 'AUTO');seconds=$j.seconds;relay=$j.relay}
}
function Run-Engine([string]$a,[string]$m,[int]$budget=120){
 $j=[guid]::NewGuid().ToString('N');& $Python $Engine --action $a --mode $m --job $j --budget $budget|Out-Null;$ec=$LASTEXITCODE
 $rec=Get-Content (Join-Path $Root ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
 [pscustomobject]@{exit=$ec;record=$rec}
}
function Owner-Valid{
 if(!(Test-Path $Owner)){return $false}
 try{$o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json;$p=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue;$c=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$o.pid) -ErrorAction SilentlyContinue;return [bool]($p -and $c -and $c.ExecutablePath -eq [string]$o.path -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks)}catch{return $false}
}
function Run-WslConsole([string]$Verb,[string]$Profile=''){
 $rp=Join-Path $Runtime ('controller-wsl-'+[guid]::NewGuid().ToString('N')+'.json')
 $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
 foreach($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$WslConsole,'-Action',$Verb,'-ResultPath',$rp)){[void]$psi.ArgumentList.Add($a)}
 if($Profile){[void]$psi.ArgumentList.Add('-ProfilePath');[void]$psi.ArgumentList.Add($Profile)}
 $p=[Diagnostics.Process]::Start($psi);$deadline=[DateTime]::UtcNow.AddSeconds($(if($Verb -in @('Start','Stop')){240}else{120}));$j=$null
 try{
  do{
   if(Test-Path $rp){try{$j=Get-Content $rp -Raw -Encoding UTF8|ConvertFrom-Json}catch{};if($j){break}}
   if($p.HasExited -and !(Test-Path $rp)){break}
   Start-Sleep -Milliseconds 150
  }while([DateTime]::UtcNow -lt $deadline)
  if(!$j){if(-not $p.HasExited){try{$p.Kill($true)}catch{}};throw ('WSL_CONSOLE_'+$Verb.ToUpperInvariant()+'_RESULT_TIMEOUT')}
  if(-not $p.HasExited){try{$p.WaitForExit(1200)|Out-Null}catch{};if(-not $p.HasExited){try{$p.Kill($true)}catch{}}}
  return [pscustomobject]@{exit=[int]$j.exit;record=$j}
 }finally{Remove-Item $rp -Force -ErrorAction SilentlyContinue}
}
function Get-Status{
 $d=Get-FnhConsoleConfig $Defaults -AllowUnconfigured
 $ca=if($d.adapter_description){Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.InterfaceDescription -eq [string]$d.adapter_description}|Select-Object -First 1}else{$null}
 $tun=Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$Defaults.tun.interface_name}|Select-Object -First 1
 $s=if(Test-Path $Session){Get-Content $Session -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
 $wc=$null;try{$x=Run-WslConsole 'Status';if($x.exit -eq 0){$wc=$x.record.result}}catch{}
 $pcRunning=Owner-Valid;$consoleRunning=[bool]($wc -and $wc.running);$running=($pcRunning -or $consoleRunning)
 $mode=if($consoleRunning){'CONSOLE_ONLY'}elseif($pcRunning){'PC_TUNNEL'}elseif($s){[string]$s.mode}else{''}
 $tunView=if($tun){[ordered]@{name=$tun.Name;status=[string]$tun.Status;ifIndex=$tun.ifIndex;backend='WINDOWS_TUN'}}elseif($consoleRunning){[ordered]@{name='WSL:fnh-tun';status='Up';ifIndex=$null;backend='WSL2_AUTO_REDIRECT'}}else{$null}
 $manual=if($wc -and $wc.manual){$wc.manual}else{[ordered]@{ip=[string]$d.suggested_console_ip;prefix=24;gateway=[string]$d.gateway;dns=[string]$d.dns}}
 $cStatus=if($consoleRunning){if($wc.router -and [bool]$wc.router.carrier){'Up'}else{'Disconnected'}}elseif($ca){[string]$ca.Status}elseif($wc -and $wc.usb -and [string]$wc.usb.state -eq 'Shared'){'Disconnected'}else{'Missing'}
 [ordered]@{
  status='PASS';running=$running;mode=$mode;tun=$tunView
  console=[ordered]@{
   name=if($ca){$ca.Name}else{[string]$d.adapter_name}
   description=if($wc -and $wc.usb){[string]$wc.usb.description}else{[string]$d.adapter_description}
   status=$cStatus;ifIndex=if($ca){$ca.ifIndex}else{$null};manual=$manual
   backend='WSL2_AUTO_REDIRECT';usb=if($wc){$wc.usb}else{$null};router=if($wc){$wc.router}else{$null};distro=if($wc){$wc.distro}else{$null}
  }
  session=$s
 }
}
function Require-Admin{if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMIN_REQUIRED'}}
function Cleanup-Failed([string]$mode,[bool]$providerStarted,[string]$provider='WARP'){
 if($mode -eq 'PC_TUNNEL'){
  try{if((Test-Path $Owner) -or (Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$Defaults.tun.interface_name})){& $StopScript|Out-Null}}catch{}
  if($providerStarted){try{Run-Engine 'StopOne' $provider 60|Out-Null}catch{}}
 }else{
  try{[void](Run-WslConsole 'Stop')}catch{}
 }
}
Assert-GatewayIntegrity
New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
if($ResultPath){$full=[IO.Path]::GetFullPath($ResultPath);$jobs=[IO.Path]::GetFullPath((Join-Path $Root 'jobs'))+'\';if(!$full.StartsWith($jobs,[StringComparison]::OrdinalIgnoreCase)){throw 'RESULT_PATH_OUTSIDE_JOBS'};$ResultPath=$full}
$out=[ordered]@{schema=1;action=$Action;utc=[DateTimeOffset]::UtcNow.ToString('o');exit=1;result=$null}
try{
 if($Action -eq 'Status'){$out.exit=0;$out.result=Get-Status}
 elseif($Action -eq 'Stop'){
  Require-Admin;$s=if(Test-Path $Session){Get-Content $Session -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
  $ws=$null;try{$ws=Run-WslConsole 'Status'}catch{}
  if(($s -and [string]$s.mode -eq 'CONSOLE_ONLY') -or ($ws -and $ws.exit -eq 0 -and [bool]$ws.record.result.running)){
   $stop=Run-WslConsole 'Stop';Assert ($stop.exit -eq 0) 'WSL_CONSOLE_STOP_FAIL'
  }
  if((Test-Path $Owner) -or (Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq [string]$Defaults.tun.interface_name})){& $StopScript|Out-Null}
  if($s -and [string]$s.mode -eq 'PC_TUNNEL' -and -not [bool]$s.providerPreexisting){$sp=[string]$s.provider;if($sp -in @('WARP','NODE')){Run-Engine 'StopOne' $sp 60|Out-Null}}
  Remove-Item $Session -Force -ErrorAction SilentlyContinue;$out.exit=0;$out.result=Get-Status
 }
 elseif($Action -eq 'StopConsole'){
  Require-Admin
  $ws=$null;try{$ws=Run-WslConsole 'Status'}catch{}
  if($ws -and $ws.exit -eq 0 -and [bool]$ws.record.result.running){
   $stop=Run-WslConsole 'Stop';Assert ($stop.exit -eq 0) 'WSL_CONSOLE_STOP_FAIL'
  }
  $s=if(Test-Path $Session){Get-Content $Session -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
  if($s -and [string]$s.mode -eq 'CONSOLE_ONLY'){Remove-Item $Session -Force -ErrorAction SilentlyContinue}
  $out.exit=0;$out.result=Get-Status
 }

 else{
  Require-Admin;$st=Get-Status;Assert (-not [bool]$st.running) 'GATEWAY_ALREADY_RUNNING'
  if(Test-Path $Owner){Remove-Item $Owner -Force -ErrorAction SilentlyContinue}
  $mode=if($Action -eq 'StartPc'){'PC_TUNNEL'}else{'CONSOLE_ONLY'};$started=$false;$preexisting=$false
  try{
   if($mode -eq 'CONSOLE_ONLY'){
    $profilePath=if(Test-Path $ConsoleProfile){$ConsoleProfile}else{''};$before=Trace
    $wc=Run-WslConsole 'Start' $profilePath;Assert ($wc.exit -eq 0 -and [string]$wc.record.result.status -eq 'PASS') 'WSL_CONSOLE_START_FAIL'
    $wr=$wc.record.result;$after=Trace;Assert ([string]$after.ip -eq [string]$before.ip -and [string]$after.warp -eq 'off') 'CONSOLE_MODE_HOST_ROUTE_CHANGED'
    $cc=Get-FnhConsoleConfig $Defaults;$sess=[ordered]@{
     schema=2;mode='CONSOLE_ONLY';provider='WSL2';providerKind=[string]$wr.providerKind;providerPreexisting=$false
     profileSha256=if($profilePath){(Get-FileHash $profilePath -Algorithm SHA256).Hash}else{$null}
     started=[DateTimeOffset]::UtcNow.ToString('o')
     verify=[ordered]@{hostTrace=$after;state=[string]$wr.state;carrier=[bool]$wr.carrier;usbState=[string]$wr.usbState;country=[string]$wr.country;backend='WSL2_AUTO_REDIRECT'}
     manual=[ordered]@{ip=[string]$cc.suggested_console_ip;prefix=24;gateway=[string]$cc.gateway;dns=[string]$cc.dns}
    };Write-J $Session $sess;$out.exit=0;$out.result=Get-Status
   }else{
    Assert ($Provider -in @('WARP','NODE')) 'PC_PROVIDER_UNSUPPORTED'
    $target=Target-Country
    if($Provider -eq 'NODE'){
     $v=Run-Engine 'Verify' 'NODE' 70
     $preexisting=($v.exit -eq 0 -and [bool]$v.record.result.healthy -and ($target -eq 'AUTO' -or [string]$v.record.result.country -eq $target))
     if(!$preexisting){
      if($NodePolicy -eq 'AUTO'){
       $c=Run-Engine 'Connect' 'NODE' 240
       Assert ($c.exit -eq 0 -and [bool]$c.record.result.healthy) 'NODE_AUTO_CONNECT_FAIL'
       $started=$true
      }else{
       $c=Run-Engine 'ConnectSelectedNode' 'NODE' 160
       Assert ($c.exit -eq 0 -and [bool]$c.record.result.healthy) 'NODE_SELECTED_CONNECT_FAIL'
       $started=[bool]$c.record.result.startedHere
      }
      Assert ($target -eq 'AUTO' -or [string]$c.record.result.country -eq $target) 'NODE_TCP_COUNTRY_FAIL'
     }
    }else{
     $v=Run-Engine 'Verify' 'WARP' 60;$preexisting=($v.exit -eq 0 -and [bool]$v.record.result.healthy)
     if(!$preexisting){$c=Run-Engine 'ConnectProvider' 'WARP' 220;Assert ($c.exit -eq 0 -and [bool]$c.record.result.healthy) 'WARP_CONNECT_FAIL';$started=$true}
    }

    $udpBefore=Verify-ProviderUdp $Provider $(if($Provider -eq 'NODE'){$target}else{'AUTO'})
    $baseRoute=Get-BaseRouteSnapshot
    $before=Trace
    $cfg=Join-Path $Runtime ('pc_product_'+$Provider.ToLowerInvariant()+'.json')
    & $Python $Generator --mode PC_TUNNEL --provider $Provider --output $cfg|Out-Null;Assert ($LASTEXITCODE -eq 0) 'CONFIG_GENERATE_FAIL'
    $SB=[string](Get-FnhSingBox).path;& $SB check -c $cfg;Assert ($LASTEXITCODE -eq 0) 'CONFIG_CHECK_FAIL'
    & $Apply -Mode PC_TUNNEL -ConfigPath $cfg -ConfigSha256 ((Get-FileHash $cfg -Algorithm SHA256).Hash)|Out-Null
    $ar=Get-Content (Join-Path $Runtime 'apply_result.json') -Raw -Encoding UTF8|ConvertFrom-Json;Assert ($ar.status -eq 'PASS') 'APPLY_FAIL';Start-Sleep -Seconds 2

    $tr=Trace
    if($Provider -eq 'WARP'){Assert ([string]$tr.warp -eq 'on') 'PC_WARP_NOT_ON'}
    if($Provider -eq 'NODE' -and $target -ne 'AUTO'){Assert ([string]$tr.loc -eq $target) ('PC_NODE_TCP_COUNTRY_'+[string]$tr.loc)}
    $yt=& curl.exe -4 --noproxy '*' --max-time 20 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204|Out-String
    Assert ($LASTEXITCODE -eq 0 -and $yt.Trim() -eq '204') 'PC_YOUTUBE_FAIL'
    $udp=& $Python $DirectStun|Out-String;Assert ($LASTEXITCODE -eq 0) 'PC_UDP_FAIL';$udpPost=$udp|ConvertFrom-Json
    $udpCountry='UNVERIFIED_AUTO'
    if($Provider -eq 'NODE' -and $target -ne 'AUTO'){
     $udpCountry=Geo-Country ([string]$udpPost.public_ip)
     Assert ($udpCountry -eq $target) ('PC_NODE_UDP_COUNTRY_'+$udpCountry)
    }

    $kind=$(if($Provider -eq 'NODE'){'NODE_SOCKS'}else{'WARP_SOCKS'})
    $sess=[ordered]@{schema=4;mode='PC_TUNNEL';provider=$Provider;baseRoute=$baseRoute;baseTrace=$before;providerKind=$kind;nodePolicy=$(if($Provider -eq 'NODE'){$NodePolicy}else{$null});providerPreexisting=$preexisting;profileSha256=$null;started=[DateTimeOffset]::UtcNow.ToString('o');verify=[ordered]@{targetCountry=$target;providerUdpBefore=$udpBefore;trace=$tr;youtube='204';udp=$udpPost;udpCountry=$udpCountry};manual=$null}
    Write-J $Session $sess
    $out.exit=0;$out.result=Get-Status
   }
  }catch{Cleanup-Failed $mode $started $Provider;throw}
 }
}catch{$out.exit=20;$out.result=[ordered]@{error=$_.Exception.Message;status=try{Get-Status}catch{$null}}}
if($ResultPath){Write-J $ResultPath $out}
$out|ConvertTo-Json -Depth 24
exit $out.exit
