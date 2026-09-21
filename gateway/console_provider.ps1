[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('Start','Verify','Stop','Status')][string]$Action,[string]$ListenAddress='127.0.0.1',[int]$PortOverride=0,[string]$ResultPath='')
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Owner=Join-Path $Runtime 'console-provider-owner.json'
$Result=if($ResultPath){$full=[IO.Path]::GetFullPath($ResultPath);$base=[IO.Path]::GetFullPath($Runtime)+'\';if(!$full.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw 'PROVIDER_RESULT_OUTSIDE_RUNTIME'};$full}else{Join-Path $Runtime 'console-provider-result.json'}
$Builder=Join-Path $PSScriptRoot 'build_isolated_mihomo.py'
$Python=Get-FnhPython
$LocalConfig=Join-Path $Runtime 'local_provider.json'
$Cfg=Join-Path $Runtime 'mihomo_DE.yaml'
$Data=Join-Path $Runtime 'mihomo_DE_data'
$Port=if($PortOverride -gt 0){$PortOverride}else{19591};$Controller=if($PortOverride -gt 0){$PortOverride+1}else{19592};if($ListenAddress -notmatch '^(?:127\.0\.0\.1|(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9]{1,3}\.[0-9]{1,3})$'){throw 'CONSOLE_PROVIDER_LISTEN_INVALID'}
function Out-J($x){$tmp=$Result+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$x|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -LiteralPath $tmp -Destination $Result -Force}
function Exact($o){
 $g=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue
 $c=Get-CimInstance Win32_Process -Filter ("ProcessId="+[int]$o.pid) -ErrorAction SilentlyContinue
 if(!$g -or !$c){return $false}
 return ($c.ExecutablePath -eq [string]$o.path -and $g.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks)
}
function Read-Trace([int]$p,[string]$h){
 $t=& curl.exe -4 --socks5-hostname ($h+":"+$p) --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'CONSOLE_PROVIDER_HTTPS_FAIL'}
 $d=@{};foreach($line in ($t -split '\r?\n')){if($line -match '^([^=]+)=(.*)$'){$d[$matches[1]]=$matches[2]}}
 return $d
}
function Verify-Provider{
 if(!(Test-Path $Owner)){throw 'CONSOLE_PROVIDER_NOT_OWNED'}
 $o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json
 if(!(Exact $o)){throw 'CONSOLE_PROVIDER_OWNER_MISMATCH'}
 $vp=[int]$o.port;$vh=if($o.PSObject.Properties['listen']){[string]$o.listen}else{'127.0.0.1'}
 if(-not (Get-NetTCPConnection -State Listen -LocalAddress $vh -LocalPort $vp -OwningProcess ([int]$o.pid) -ErrorAction SilentlyContinue)){throw 'CONSOLE_PROVIDER_LISTENER_MISSING'}
 $tr=Read-Trace $vp $vh
 if([string]$tr.loc -ne 'DE'){throw ('CONSOLE_PROVIDER_TCP_COUNTRY_'+[string]$tr.loc)}
 $yt=& curl.exe -4 --socks5-hostname ($vh+":"+$vp) --max-time 20 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204 2>&1|Out-String
 if($LASTEXITCODE -ne 0 -or $yt.Trim() -ne '204'){throw 'CONSOLE_PROVIDER_YOUTUBE_FAIL'}
 $st=& $Python (Join-Path $PSScriptRoot 'socks_udp_probe.py') $vp $vh 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'CONSOLE_PROVIDER_UDP_FAIL'}
 $sj=$st|ConvertFrom-Json
 $gj=& curl.exe -4 --max-time 15 -fsS ("https://ipwho.is/"+$sj.udp_public_ip) 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'CONSOLE_PROVIDER_UDP_GEO_FAIL'}
 $geo=$gj|ConvertFrom-Json
 if(!$geo.success -or [string]$geo.country_code -ne 'DE'){throw ('CONSOLE_PROVIDER_UDP_COUNTRY_'+[string]$geo.country_code)}
 [ordered]@{healthy=$true;country='DE';tcpCountry=[string]$tr.loc;udpCountry=[string]$geo.country_code;youtube='204';udp=$sj;pid=[int]$o.pid}
}
New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
try{
 if($Action -eq 'Status'){
  $oo=if(Test-Path $Owner){Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json}else{$null};$sp=if($oo){[int]$oo.port}else{$Port};$sh=if($oo -and $oo.PSObject.Properties['listen']){[string]$oo.listen}else{$ListenAddress};$r=[ordered]@{status='PASS';owned=[bool]$oo;listen=$sh;port=$sp;listening=[bool](Get-NetTCPConnection -State Listen -LocalAddress $sh -LocalPort $sp -ErrorAction SilentlyContinue)}
  Out-J $r;$r|ConvertTo-Json -Depth 12;exit 0
 }
 if($Action -eq 'Stop'){
  if(!(Test-Path $Owner)){$r=[ordered]@{status='PASS';state='NOT_OWNED'};Out-J $r;$r|ConvertTo-Json -Depth 12;exit 0}
  $o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json
  if(Exact $o){Stop-Process -Id ([int]$o.pid) -Force}
  elseif(Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue){throw 'CONSOLE_PROVIDER_IDENTITY_MISMATCH'}
  $deadline=[DateTime]::UtcNow.AddSeconds(5);do{if(!(Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue)){break};Start-Sleep -Milliseconds 150}while([DateTime]::UtcNow -lt $deadline)
  if(Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue){throw 'CONSOLE_PROVIDER_STOP_INCOMPLETE'}
  Remove-Item $Owner -Force
  $r=[ordered]@{status='PASS';state='STOPPED';pid=[int]$o.pid;utc=[DateTimeOffset]::UtcNow.ToString('o')};Out-J $r;$r|ConvertTo-Json -Depth 12;exit 0
 }
 if($Action -eq 'Verify'){
  $v=Verify-Provider;$r=[ordered]@{status='PASS';verification=$v;utc=[DateTimeOffset]::UtcNow.ToString('o')};Out-J $r;$r|ConvertTo-Json -Depth 12;exit 0
 }
 # Start
 if(Test-Path $Owner){
  $v=Verify-Provider;$r=[ordered]@{status='PASS';state='ALREADY_HEALTHY';verification=$v};Out-J $r;$r|ConvertTo-Json -Depth 12;exit 0
 }
 if(!(Test-Path $LocalConfig)){throw 'LOCAL_CONSOLE_PROVIDER_NOT_CONFIGURED'}
 $lc=Get-Content $LocalConfig -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$lc.type -ne 'mihomo_source' -or [string]$lc.country -ne 'DE'){throw 'LOCAL_CONSOLE_PROVIDER_CONFIG_INVALID'}
 $Bin=[string]$lc.binary;$BinSha=[string]$lc.binarySha256;$Source=[string]$lc.sourceConfig;if($PortOverride -le 0){$Port=[int]$lc.port;$Controller=[int]$lc.controllerPort}
 if(!(Test-Path $Bin)){throw 'CONSOLE_PROVIDER_BINARY_MISSING'}
 if((Get-FileHash $Bin -Algorithm SHA256).Hash -ne $BinSha){throw 'CONSOLE_PROVIDER_BINARY_HASH_MISMATCH'}
 if(!(Test-Path $Source)){throw 'CONSOLE_PROVIDER_SOURCE_MISSING'}
 & $Python $Builder --source-config $Source --country DE --port $Port --controller $Controller --listen $ListenAddress --output $Cfg|Out-Null
 if($LASTEXITCODE -ne 0){throw 'CONSOLE_PROVIDER_CONFIG_BUILD_FAIL'}
 Remove-Item $Data -Recurse -Force -ErrorAction SilentlyContinue;New-Item -ItemType Directory -Path $Data -Force|Out-Null
 $stdout=Join-Path $Data 'stdout.log';$stderr=Join-Path $Data 'stderr.log'
 $p=Start-Process -FilePath $Bin -ArgumentList @('-d',$Data,'-f',$Cfg) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
 $deadline=[DateTime]::UtcNow.AddSeconds(12);do{if($p.HasExited){throw ('CONSOLE_PROVIDER_EXIT_'+$p.ExitCode)};if(Get-NetTCPConnection -State Listen -LocalAddress $ListenAddress -LocalPort $Port -OwningProcess $p.Id -ErrorAction SilentlyContinue){break};Start-Sleep -Milliseconds 250}while([DateTime]::UtcNow -lt $deadline)
 if(-not (Get-NetTCPConnection -State Listen -LocalAddress $ListenAddress -LocalPort $Port -OwningProcess $p.Id -ErrorAction SilentlyContinue)){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue;throw 'CONSOLE_PROVIDER_LISTENER_TIMEOUT'}
 $gp=Get-Process -Id $p.Id;$cp=Get-CimInstance Win32_Process -Filter ("ProcessId="+$p.Id)
 $o=[ordered]@{schema=1;pid=$p.Id;path=$cp.ExecutablePath;startTicks=$gp.StartTime.ToUniversalTime().Ticks;binarySha256=$BinSha;configSha256=(Get-FileHash $Cfg -Algorithm SHA256).Hash;sourceSha256=(Get-FileHash $Source -Algorithm SHA256).Hash;country='DE';listen=$ListenAddress;port=$Port;utc=[DateTimeOffset]::UtcNow.ToString('o')}
 $o|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $Owner -Encoding UTF8
 try{$v=Verify-Provider}catch{Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue;Remove-Item $Owner -Force -ErrorAction SilentlyContinue;throw}
 $r=[ordered]@{status='PASS';state='STARTED';verification=$v;utc=[DateTimeOffset]::UtcNow.ToString('o')};Out-J $r;$r|ConvertTo-Json -Depth 12
}catch{
 $r=[ordered]@{status='FAIL';error=$_.Exception.Message;utc=[DateTimeOffset]::UtcNow.ToString('o')};Out-J $r;$r|ConvertTo-Json -Depth 12;exit 20
}
