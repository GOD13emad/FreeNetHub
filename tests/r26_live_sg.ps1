$ErrorActionPreference='Stop'
$Root=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
Set-Location $Root
$Settings=Join-Path $Root 'settings.json';$Nodes=Join-Path $Root 'data\nodes.json'
$SB=if(Test-Path $Settings){[IO.File]::ReadAllBytes($Settings)}else{$null}
$NB=if(Test-Path $Nodes){[IO.File]::ReadAllBytes($Nodes)}else{$null}
function WJ($p,$o){$tmp=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllText($tmp,($o|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false));[IO.File]::Move($tmp,$p,$true)}
function RunE($a,$m='AUTO',$b=180){
 $j=[guid]::NewGuid().ToString('N')
 & python app\engine.py --action $a --mode $m --job $j --budget $b | Out-Null
 $ec=$LASTEXITCODE
 $jp=Join-Path $Root ('jobs\'+$j+'.json')
 if(!(Test-Path $jp)){throw 'ENGINE_RESULT_MISSING'}
 $r=Get-Content $jp -Raw|ConvertFrom-Json -AsHashtable
 return @{ec=$ec;r=$r;job=$j}
}
$ev=[ordered]@{schema=1;date='2026-09-28';status='FAIL';target='SG';actual='';mode='';healthy=$false;error='';refresh=[ordered]@{};cleanup=[ordered]@{};privacy='No raw node credentials or raw exit IP persisted.'}
try{
 $cfg=Get-Content $Settings -Raw|ConvertFrom-Json -AsHashtable
 $cfg.country='SG';WJ $Settings $cfg
 $rf=RunE 'NodeRefreshPublic' 'NODE' 100
 $rr=$rf.r.result
 $ev.refresh=[ordered]@{exit=$rf.ec;total=$rr.total;imported=$rr.imported;sources=$rr.sources;failedSources=$rr.failedSources}
 if($rf.ec -ne 0){throw ('REFRESH_FAIL_'+$rf.ec)}
 $cn=RunE 'Connect' 'AUTO' 180
 $x=$cn.r.result
 $ev.mode=[string]$x.mode;$ev.actual=[string]$x.country;$ev.healthy=[bool]$x.healthy
 if($cn.ec -ne 0 -or !$ev.healthy -or $ev.actual -ne 'SG'){throw ('STRICT_COUNTRY_FAIL exit='+$cn.ec+' mode='+$ev.mode+' actual='+$ev.actual)}
 $ev.status='PASS'
}catch{$ev.error=$_.Exception.Message}
finally{
 try{RunE 'Stop' 'AUTO' 30|Out-Null}catch{}
 if($SB){[IO.File]::WriteAllBytes($Settings,$SB)}
 if($NB){[IO.File]::WriteAllBytes($Nodes,$NB)}
 Start-Sleep -Milliseconds 700
 $ev.cleanup=[ordered]@{nodePort19460=[bool](Get-NetTCPConnection -State Listen -LocalPort 19460 -ErrorAction SilentlyContinue);warpPort19410=[bool](Get-NetTCPConnection -State Listen -LocalPort 19410 -ErrorAction SilentlyContinue);settingsRestored=$true;nodesRestored=$true}
 if($ev.cleanup.nodePort19460 -or $ev.cleanup.warpPort19410){$ev.status='FAIL';$ev.error='CLEANUP_RESIDUE'}
 WJ (Join-Path $Root 'evidence\R26_STRICT_COUNTRY_SG_ACCEPTANCE_20260928.json') $ev
 $ev|ConvertTo-Json -Depth 20
}
if($ev.status -ne 'PASS'){exit 26}
