$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$backup=Join-Path $Root 'delivery\prestate_r35_node_pre_tun_20260928'
New-Item -ItemType Directory -Force -Path $backup|Out-Null
$rels=@('data\nodes.json','settings.json','data\node_public_refresh.json','session.json','last.json')
$pre=[ordered]@{}
foreach($rel in $rels){
 $p=Join-Path $Root $rel
 if(Test-Path $p){
  $dest=Join-Path $backup ($rel.Replace('\','__'));Copy-Item $p $dest -Force
  $pre[$rel]=[ordered]@{exists=$true;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}
 }else{$pre[$rel]=[ordered]@{exists=$false}}
}
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';stdout='';restored=$false;error=''}
try{
 $raw=& python .\tests\r33_prepare_live_node_state.py 2>&1|Out-String
 $out.stdout=$raw.Trim()
 if($LASTEXITCODE -ne 0){throw ('R35_PRE_TUN_FAIL '+$raw.Trim())}
 $j=$raw|ConvertFrom-Json
 $out.result=$j
 if([string]$j.status -ne 'PASS'){throw 'R35_PRE_TUN_NOT_PASS'}
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{
  $job=[guid]::NewGuid().ToString('N');python .\app\engine.py --action StopOne --mode NODE --job $job --budget 60 *> $null
 }catch{}
 foreach($rel in $rels){
  $before=$pre[$rel];$dest=Join-Path $Root $rel;$bp=Join-Path $backup ($rel.Replace('\','__'))
  if($before.exists){Copy-Item $bp $dest -Force}else{Remove-Item $dest -Force -ErrorAction SilentlyContinue}
 }
 Start-Sleep -Milliseconds 500
 $ok=$true
 foreach($rel in $rels){
  $before=$pre[$rel];$dest=Join-Path $Root $rel
  if($before.exists){if(!(Test-Path $dest) -or (Get-FileHash $dest -Algorithm SHA256).Hash -ne [string]$before.sha256){$ok=$false}}
  elseif(Test-Path $dest){$ok=$false}
 }
 if(@(Get-NetTCPConnection -State Listen -LocalPort 19460 -ErrorAction SilentlyContinue).Count){$ok=$false}
 if(Test-Path data\NODE\owner.json){$ok=$false}
 $out.restored=$ok
 if(!$ok){$out.status='FAIL';$out.error=($out.error+' RESTORE_FAILED').Trim()}
}
$out|ConvertTo-Json -Depth 12|Set-Content evidence\R35_NODE_PRE_TUN_ACCEPTANCE_20260928.json -Encoding utf8
$out|ConvertTo-Json -Depth 12
if($out.status -ne 'PASS'){exit 20}
