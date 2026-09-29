$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Root=Split-Path $PSScriptRoot -Parent
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Engine=Join-Path $Install 'app\engine.py'
$Data=Join-Path $Install 'data\nodes.json'
$Session=Join-Path $Install 'session.json'
$Last=Join-Path $Install 'last.json'
$Evidence=Join-Path $Root 'evidence\R33_V2CROSS_TARGETED_PATH_ACCEPTANCE_20260928.json'
$backup=Join-Path $env:TEMP ('FNH-R33-v2cross-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $backup -Force|Out-Null
$state=@{}
foreach($p in @($Data,$Session,$Last)){
 $key=[IO.Path]::GetFileName($p)
 if(Test-Path $p){Copy-Item $p (Join-Path $backup $key) -Force;$state[$key]=[ordered]@{exists=$true;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}}else{$state[$key]=[ordered]@{exists=$false}}
}
function Run-E([string]$Action,[string]$Mode,[string]$Payload='',[int]$Budget=180){
 $j=[guid]::NewGuid().ToString('N')
 $args=@($Engine,'--action',$Action,'--mode',$Mode,'--job',$j,'--budget',[string]$Budget)
 if($Payload){$args+=@('--payload',$Payload)}
 & $Python @args | Out-Null
 $ec=$LASTEXITCODE;$rp=Join-Path $Install ('jobs\'+$j+'.json')
 if(!(Test-Path $rp)){throw ('RESULT_MISSING_'+$Action)}
 [pscustomobject]@{exit=$ec;record=(Get-Content $rp -Raw -Encoding UTF8|ConvertFrom-Json)}
}
$candidates=@(
 [ordered]@{id='e704f17ab6dc42a47190';protocol='trojan';source='V2CROSS_PAGE'},
 [ordered]@{id='44bdc29c5ff349d0d6f9';protocol='vless';source='V2CROSS_PAGE'},
 [ordered]@{id='017e0eca11e89f5651c9';protocol='ss';source='V2CROSS_PAGE'}
)
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';results=@();restored=$false}
try{
 foreach($c in $candidates){
  $sel=Run-E 'NodeSelect' 'NODE' $c.id 60
  if($sel.exit -ne 0){$out.results+=,[ordered]@{id=$c.id;protocol=$c.protocol;status='SELECT_FAIL'};continue}
  $sp=Run-E 'NodeSpeed' 'NODE' '' 180
  $perf=$sp.record.result.performance
  $out.results+=,[ordered]@{id=$c.id;protocol=$c.protocol;status=$(if($sp.exit -eq 0 -and $perf.ok){'PASS'}else{'FAIL'});pingMs=$perf.pingMs;downloadMbps=$perf.downloadMbps;uploadMbps=$perf.uploadMbps;country=$perf.country;error=$perf.error}
  if($sp.exit -eq 0 -and $perf.ok){$out.status='PASS';break}
 }
}catch{$out.error=$_.Exception.Message}
finally{
 try{Run-E 'StopOne' 'NODE' '' 60|Out-Null}catch{}
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
 $out|ConvertTo-Json -Depth 12|Set-Content $Evidence -Encoding utf8
 try{if([IO.Directory]::Exists($backup)){[IO.Directory]::Delete($backup,$true)}}catch{}
}
$out|ConvertTo-Json -Depth 12
if($out.status -ne 'PASS' -or -not $out.restored){exit 20}
