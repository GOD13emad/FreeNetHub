param([Parameter(Mandatory)][string]$ResultPath)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$Ctl=Join-Path $Root 'gateway\gateway_control.ps1'
$StartResult=Join-Path $Root ('jobs\r33-live-start-'+[guid]::NewGuid().ToString('N')+'.json')
$StopResult=Join-Path $Root ('jobs\r33-live-stop-'+[guid]::NewGuid().ToString('N')+'.json')
$Backup=Join-Path $Root 'delivery\prestate_r33_live_tun_20260928'
New-Item -ItemType Directory -Path $Backup -Force|Out-Null
$StateFiles=@('data\nodes.json','settings.json','data\node_public_refresh.json','session.json','last.json')
$Pre=[ordered]@{}
foreach($rel in $StateFiles){
 $p=Join-Path $Root $rel
 if(Test-Path $p){
  $bp=Join-Path $Backup ($rel.Replace('\','__'));Copy-Item $p $bp -Force
  $Pre[$rel]=[ordered]@{exists=$true;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}
 }else{$Pre[$rel]=[ordered]@{exists=$false}}
}
$out=[ordered]@{schema=2;date='2026-09-28';status='FAIL';preflight=$null;start=$null;post=@{};stop=$null;rollbackPass=$false;stateRestored=$false}
try{
 $prep=& python .\tests\r33_prepare_live_node_state.py 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw ('R33_PREP_FAIL '+$prep.Trim())}
 try{$out.preflight=$prep|ConvertFrom-Json}catch{$out.preflight=[ordered]@{raw=$prep.Trim()}}
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Ctl -Action StartPc -Provider NODE -NodePolicy AUTO -ResultPath $StartResult | Out-Null
 $startEc=$LASTEXITCODE
 if(Test-Path $StartResult){$out.start=Get-Content $StartResult -Raw -Encoding UTF8|ConvertFrom-Json}
 if($startEc -ne 0 -or -not $out.start -or [int]$out.start.exit -ne 0){throw ('R33_STARTPC_FAIL_'+$startEc)}
 $trace=& curl.exe -4 --noproxy '*' --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'R33_POST_TRACE_FAIL'}
 $td=[ordered]@{};foreach($l in ($trace -split '\r?\n')){if($l -match '^([^=]+)=(.*)$'){$td[$matches[1]]=$matches[2]}}
 $yt=& curl.exe -4 --noproxy '*' --max-time 20 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204|Out-String
 if($LASTEXITCODE -ne 0 -or $yt.Trim() -ne '204'){throw 'R33_POST_YOUTUBE_FAIL'}
 $udpRaw=& python (Join-Path $Root 'gateway\tests\direct_stun.py') 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'R33_POST_UDP_FAIL'}
 $udp=$udpRaw|ConvertFrom-Json
 $geo=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ('https://ipwho.is/'+[string]$udp.public_ip) 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'R33_POST_GEO_FAIL'}
 $gj=$geo|ConvertFrom-Json
 $out.post=[ordered]@{tcpCountry=[string]$td.loc;youtube=$yt.Trim();udpCountry=[string]$gj.country_code;warp=[string]$td.warp;provider='NODE'}
 if([string]$td.loc -ne 'SG'){throw ('R33_POST_TCP_COUNTRY_'+[string]$td.loc)}
 if([string]$gj.country_code -ne 'SG'){throw ('R33_POST_UDP_COUNTRY_'+[string]$gj.country_code)}
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{
  & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Ctl -Action Stop -ResultPath $StopResult | Out-Null
  $stopEc=$LASTEXITCODE
  if(Test-Path $StopResult){$out.stop=Get-Content $StopResult -Raw -Encoding UTF8|ConvertFrom-Json}
 }catch{$stopEc=99;$out.stop=[ordered]@{error=$_.Exception.Message}}
 try{
  $job=[guid]::NewGuid().ToString('N');python .\app\engine.py --action StopOne --mode NODE --job $job --budget 60 *> $null
 }catch{}
 foreach($rel in $StateFiles){
  $before=$Pre[$rel];$dest=Join-Path $Root $rel;$bp=Join-Path $Backup ($rel.Replace('\','__'))
  if($before.exists){Copy-Item $bp $dest -Force}else{Remove-Item $dest -Force -ErrorAction SilentlyContinue}
 }
 Start-Sleep -Milliseconds 600
 $tun=@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'})
 $owner=Test-Path (Join-Path $Root 'gateway\runtime\owner.json')
 $session=Test-Path (Join-Path $Root 'gateway\runtime\gateway-session.json')
 $listener=@(Get-NetTCPConnection -State Listen -LocalPort 19460 -ErrorAction SilentlyContinue).Count
 $stateOk=$true
 foreach($rel in $StateFiles){
  $before=$Pre[$rel];$dest=Join-Path $Root $rel
  if($before.exists){if(!(Test-Path $dest) -or (Get-FileHash $dest -Algorithm SHA256).Hash -ne [string]$before.sha256){$stateOk=$false}}
  elseif(Test-Path $dest){$stateOk=$false}
 }
 $out.stateRestored=$stateOk
 $out.rollbackPass=($stopEc -eq 0 -and $tun.Count -eq 0 -and -not $owner -and -not $session -and $listener -eq 0 -and $stateOk)
 if(-not $out.rollbackPass){$out.status='FAIL';$out.rollbackError='R33_ROLLBACK_INCOMPLETE'}
 Remove-Item $StartResult,$StopResult -Force -ErrorAction SilentlyContinue
 $out|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $ResultPath -Encoding UTF8
}
exit $(if($out.status -eq 'PASS' -and $out.rollbackPass){0}else{33})
