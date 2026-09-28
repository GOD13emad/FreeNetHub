$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Project=Split-Path $PSScriptRoot -Parent\n$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
Set-Location $Install
function Run-E([string]$Action,[string]$Mode='NODE',[int]$Budget=420){
 $job=[guid]::NewGuid().ToString('N')
 & python app\engine.py --action $Action --mode $Mode --job $job --budget $Budget | Out-Null
 $ec=$LASTEXITCODE;$jp=Join-Path $Install ('jobs\'+$job+'.json')
 if(!(Test-Path $jp)){throw ('RESULT_MISSING_'+$Action)}
 $o=Get-Content $jp -Raw|ConvertFrom-Json
 return [pscustomobject]@{exit=$ec;result=$o.result}
}
function Pool-Summary{
 $j=Get-Content data\nodes.json -Raw|ConvertFrom-Json
 $nodes=@($j.nodes)
 $rawGroups=@($nodes|Where-Object{$_.raw}|Group-Object raw|Where-Object{$_.Count -gt 1})
 return [ordered]@{
  total=$nodes.Count
  favorite=@($nodes|Where-Object{$_.favorite}).Count
  pinned=@($nodes|Where-Object{$_.pinned}).Count
  rated=@($nodes|Where-Object{[int]$_.rating -gt 0}).Count
  tagged=@($nodes|Where-Object{@($_.tags).Count -gt 0}).Count
  noted=@($nodes|Where-Object{![string]::IsNullOrWhiteSpace([string]$_.note)}).Count
  duplicateRawGroups=$rawGroups.Count
 }
}
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';pre=@{};refresh=@{};post=@{};benchmark=@{};cleanup=@{};privacy='No raw URI, server, credential, path, key or exit IP persisted.'}
try{
 $out.pre=Pool-Summary
 $r=Run-E 'NodeRefreshPublic' 'NODE' 220
 $out.refresh=[ordered]@{exit=$r.exit;refreshed=[bool]$r.result.refreshed;fresh=[bool]$r.result.fresh;parsedRaw=[int]$r.result.parsedRaw;imported=[int]$r.result.imported;staleDropped=[int]$r.result.staleDropped;total=[int]$r.result.total;reachable=[int]$r.result.reachable;sources=@($r.result.sources);failed=@($r.result.failedSources);families=@($r.result.sourceFamilies)}
 if($r.exit -ne 0){throw 'FORCED_REFRESH_FAILED'}
 $out.post=Pool-Summary
 foreach($k in @('favorite','pinned','rated','tagged','noted')){
  if([int]$out.post[$k] -lt [int]$out.pre[$k]){throw ('USER_METADATA_REGRESSED_'+$k)}
 }
 if([int]$out.post.duplicateRawGroups -gt [int]$out.pre.duplicateRawGroups){throw 'RAW_DUPLICATES_INCREASED'}
 $b=Run-E 'NodeBenchmarkBatch' 'NODE' 520
 if($b.exit -ne 0){throw 'BENCHMARK_FAILED'}
 $store=Get-Content data\nodes.json -Raw|ConvertFrom-Json
 $by=@{};foreach($n in @($store.nodes)){$by[[string]$n.id]=$n}
 $rows=@()
 foreach($x in @($b.result.results)){
  $n=$by[[string]$x.id]
  $rows+=[ordered]@{protocol=$(if($n){[string]$n.protocol}else{'?'});source=$(if($n){[string]$n.source}else{'?'});status=[string]$x.status;ok=[bool]$x.ok;pingMs=$x.pingMs;downloadMbps=$x.downloadMbps;uploadMbps=$x.uploadMbps;country=[string]$x.country;error=$(if($x.error){[string]$x.error}else{''})}
 }
 $out.benchmark=[ordered]@{benchmarked=[int]$b.result.benchmarked;passed=[int]$b.result.passed;failed=[int]$b.result.failed;eligible=[int]$b.result.eligible;remaining=[int]$b.result.remainingUnbenchmarked;results=$rows}
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{$j=[guid]::NewGuid().ToString('N');& python app\engine.py --action Stop --mode AUTO --job $j --budget 45|Out-Null}catch{}
 Start-Sleep -Milliseconds 500
 $ports=@(19410,19413,19414,19450,19452,19453,19460)
 $ls=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
 $out.cleanup=[ordered]@{projectListenerCount=$ls.Count;singboxCount=@(Get-Process sing-box -ErrorAction SilentlyContinue).Count;pass=($ls.Count -eq 0)}
 if(!$out.cleanup.pass){$out.status='FAIL';$out.error='CLEANUP_RESIDUE'}
}
$ev=Join-Path $Project 'evidence\R28_TRANSPORT_FIX2_LIVE_ACCEPTANCE_20260928.json'
$out|ConvertTo-Json -Depth 14|Set-Content $ev -Encoding utf8
$out|ConvertTo-Json -Depth 14
if($out.status -ne 'PASS'){exit 28}
