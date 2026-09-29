$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Engine=Join-Path $Install 'app\engine.py'
$Probe=Join-Path $Install 'gateway\socks_udp_probe.py'
$Data=Join-Path $Install 'data\nodes.json'
$Session=Join-Path $Install 'session.json'
$Last=Join-Path $Install 'last.json'
$Evidence=Join-Path $Root 'evidence\R33_NODE_PROVIDER_UDP_PREFLIGHT_20260928.json'
$backup=Join-Path $env:TEMP ('FNH-R33-preflight-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $backup -Force|Out-Null
$state=@{}
foreach($p in @($Data,$Session,$Last)){
 $key=[IO.Path]::GetFileName($p)
 if(Test-Path $p){Copy-Item $p (Join-Path $backup $key) -Force;$state[$key]=[ordered]@{exists=$true;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}}else{$state[$key]=[ordered]@{exists=$false}}
}
function Run-Engine([string]$Action,[string]$Mode,[int]$Budget){
 $j=[guid]::NewGuid().ToString('N')
 & $Python $Engine --action $Action --mode $Mode --job $j --budget $Budget | Out-Null
 $ec=$LASTEXITCODE
 $rec=Get-Content (Join-Path $Install ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
 [pscustomobject]@{exit=$ec;record=$rec;job=$j}
}
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';prestate=$state;connect=$null;udp=$null;geo=$null;stop=$null;restored=$false;error=''}
try{
 $listeners=@(Get-NetTCPConnection -State Listen -LocalPort 19460 -ErrorAction SilentlyContinue)
 if($listeners.Count){throw 'NODE_LISTENER_PREEXISTING'}
 $c=Run-Engine 'Connect' 'NODE' 240
 $out.connect=$c.record
 if($c.exit -ne 0 -or -not [bool]$c.record.result.healthy){throw ('NODE_CONNECT_FAIL '+[string]$c.record.result.error)}
 $raw=& $Python $Probe 19460 127.0.0.1 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw ('NODE_UDP_PROBE_FAIL '+$raw)}
 $udp=$raw|ConvertFrom-Json;$out.udp=$udp
 if([string]$udp.status -ne 'PASS'){throw 'NODE_UDP_PROBE_NOT_PASS'}
 $g=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ('https://ipwho.is/'+[string]$udp.udp_public_ip) 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'NODE_UDP_GEO_FAIL'}
 $geo=$g|ConvertFrom-Json;$out.geo=[ordered]@{success=[bool]$geo.success;country=[string]$geo.country_code;ip=[string]$geo.ip}
 if(!$geo.success){throw 'NODE_UDP_GEO_INVALID'}
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{$st=Run-Engine 'StopOne' 'NODE' 60;$out.stop=$st.record}catch{$out.stop=[ordered]@{error=$_.Exception.Message}}
 foreach($p in @($Data,$Session,$Last)){
  $key=[IO.Path]::GetFileName($p);$before=$state[$key]
  if($before.exists){Copy-Item (Join-Path $backup $key) $p -Force}else{Remove-Item $p -Force -ErrorAction SilentlyContinue}
 }
 $restored=$true
 foreach($p in @($Data,$Session,$Last)){
  $key=[IO.Path]::GetFileName($p);$before=$state[$key]
  if($before.exists){if(!(Test-Path $p) -or (Get-FileHash $p -Algorithm SHA256).Hash -ne [string]$before.sha256){$restored=$false}}
  elseif(Test-Path $p){$restored=$false}
 }
 if(@(Get-NetTCPConnection -State Listen -LocalPort 19460 -ErrorAction SilentlyContinue).Count){$restored=$false}
 $out.restored=$restored
 $out|ConvertTo-Json -Depth 20|Set-Content $Evidence -Encoding utf8
 try{if([IO.Directory]::Exists($backup)){[IO.Directory]::Delete($backup,$true)}}catch{$out.cleanupWarning=$_.Exception.Message;$out|ConvertTo-Json -Depth 20|Set-Content $Evidence -Encoding utf8}
}
$out|ConvertTo-Json -Depth 20
if($out.status -ne 'PASS' -or -not $out.restored){exit 20}
