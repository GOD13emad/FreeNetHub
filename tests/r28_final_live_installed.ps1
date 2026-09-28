$ErrorActionPreference='Stop'
Set-StrictMode -Version 3.0
$Project=Split-Path $PSScriptRoot -Parent
$Root=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
Set-Location $Root
$Evidence=Join-Path $Project 'evidence\R28_FINAL_LIVE_ACCEPTANCE_20260928.json'
$StateFiles=@('settings.json','data\nodes.json','data\node_public_refresh.json','last.json','session.json')
$Saved=@{}
foreach($rel in $StateFiles){
 $p=Join-Path $Root $rel;$ex=Test-Path -LiteralPath $p
 $Saved[$rel]=@{Exists=$ex;Bytes=$(if($ex){[IO.File]::ReadAllBytes($p)}else{$null});Sha=$(if($ex){(Get-FileHash $p -Algorithm SHA256).Hash}else{$null})}
}
$Warp=Join-Path $Root 'data\WARP';$WarpBackup=Join-Path $Project 'delivery\prestate_r28_live_warp'
if(Test-Path -LiteralPath $WarpBackup){Remove-Item -LiteralPath $WarpBackup -Recurse -Force}
$WarpEx=Test-Path -LiteralPath $Warp
if($WarpEx){Copy-Item -LiteralPath $Warp -Destination $WarpBackup -Recurse -Force}
function HV($H,[string]$K,$D=$null){if($H -is [Collections.IDictionary] -and $H.Contains($K)){return $H[$K]};return $D}
function Run-Engine([string]$Action,[string]$Mode='AUTO',[int]$Budget=600){
 $job=[guid]::NewGuid().ToString('N');$args=@('app\engine.py','--action',$Action,'--mode',$Mode,'--job',$job,'--budget',[string]$Budget)
 & python @args|Out-Null;$ec=$LASTEXITCODE;$jp=Join-Path $Root ('jobs\'+$job+'.json')
 if(!(Test-Path -LiteralPath $jp)){throw ('RESULT_MISSING_'+$Action)}
 $rec=Get-Content -LiteralPath $jp -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable
 $rx=[int](HV $rec 'exit' 999)
 Remove-Item -LiteralPath $jp,(Join-Path $Root ('jobs\'+$job+'.progress.json')),(Join-Path $Root ('jobs\'+$job+'.cancel')) -Force -ErrorAction SilentlyContinue
 if($ec -ne $rx){throw ($Action+'_EXIT_CONTRACT')}
 if($rx -ne 0){$rr=HV $rec 'result' @{};throw ($Action+'_FAILED_'+[string](HV $rr 'error' 'UNKNOWN'))}
 return (HV $rec 'result' @{})
}
function Write-J($o){[IO.File]::WriteAllText($Evidence,($o|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))}
function Active-Ports{
 @(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)|Where-Object{Get-NetTCPConnection -State Listen -LocalPort $_ -ErrorAction SilentlyContinue}
}
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';test='R28_FINAL_INSTALLED_LIVE';direct=@{};update=@{};warp=@{};publicRefresh=@{};nodeSample=@{};cleanup=@{};error='';privacy='No raw node URI, credential, server address, or exit IP is persisted.'}
try{
 if(@(Active-Ports).Count){throw 'PRETEST_PROJECT_LISTENER_ACTIVE'}
 $refresh=Run-Engine 'NodeRefreshPublic' 'NODE' 600
 $families=@(HV $refresh 'sourceFamilies' @());$sources=@(HV $refresh 'sources' @());$failed=@(HV $refresh 'failedSources' @())
 $out.publicRefresh=[ordered]@{
  status='PASS';families=$families;familyCount=$families.Count;successfulSources=$sources.Count;failedSources=$failed.Count
  parsedRaw=[int](HV $refresh 'parsedRaw' 0);importedUnique=[int](HV $refresh 'imported' 0);totalPool=[int](HV $refresh 'total' 0)
  reachableTcp=[int](HV $refresh 'reachable' 0);staleDropped=[int](HV $refresh 'staleDropped' 0);ttlSeconds=[int](HV $refresh 'ttlSeconds' 0)
 }
 if($families.Count -lt 5 -or $sources.Count -lt 3){throw 'PUBLIC_REFRESH_DIVERSITY_GATE_FAILED'}
 $direct=Run-Engine 'Speed' 'DIRECT' 90
 if(-not [bool](HV $direct 'ok' $false)){throw 'DIRECT_SPEED_INCOMPLETE'}
 $route=HV $direct 'defaultRoute' @{}
 $out.direct=[ordered]@{
  status='PASS';path=[string](HV $direct 'path' '');proxyUsed=[bool](HV $direct 'proxyUsed' $true)
  physicalRouteTrusted=[bool](HV $route 'trustedPhysical' $false);adapterName=[string](HV $route 'adapterName' '')
  cloudflareWarp=[string](HV $direct 'cloudflareWarp' '');cloudflareGateway=[string](HV $direct 'cloudflareGateway' '')
  country=[string](HV $direct 'country' '');pingMs=(HV $direct 'pingMs' $null);httpsLatencyMs=(HV $direct 'httpsLatencyMs' $null)
  downloadMbps=(HV $direct 'downloadMbps' $null);uploadMbps=(HV $direct 'uploadMbps' $null)
  downloadSampleBytes=(HV $direct 'downloadSampleBytes' 0);uploadSampleBytes=(HV $direct 'uploadSampleBytes' 0);pathProof=[string](HV $direct 'pathProof' '')
 }
 if($out.direct.proxyUsed -or -not $out.direct.physicalRouteTrusted -or $out.direct.cloudflareWarp -eq 'on' -or $out.direct.cloudflareGateway -eq 'on'){throw 'DIRECT_PATH_PROOF_FAILED'}
 $upd=Run-Engine 'UpdateCheck' 'AUTO' 60;$asset=HV $upd 'asset' $null
 $out.update=[ordered]@{
  status='PASS';tag=[string](HV $upd 'tag' '');currentRevision=[string](HV $upd 'currentRevision' '')
  currentRevisionNumber=[int](HV $upd 'currentRevisionNumber' 0);remoteRevisionNumber=[int](HV $upd 'remoteRevisionNumber' 0)
  updateAvailable=[bool](HV $upd 'updateAvailable' $false)
  asset=$(if($asset -is [Collections.IDictionary]){[ordered]@{name=[string](HV $asset 'name' '');digestPresent=([string](HV $asset 'digest' '')).StartsWith('sha256:');bytes=(HV $asset 'bytes' 0)}}else{$null})
 }
 $warp=Run-Engine 'ProviderBenchmark' 'WARP' 240;$wp=HV $warp 'performance' @{};$wh=HV $warp 'health' @{}
 if(-not [bool](HV $wp 'ok' $false)){throw 'WARP_BENCHMARK_INCOMPLETE'}
 $out.warp=[ordered]@{
  status='PASS';temporary=[bool](HV $warp 'temporary' $false);healthy=[bool](HV $wh 'healthy' $false);country=[string](HV $wp 'country' '')
  path=[string](HV $wp 'path' '');proxyUsed=[bool](HV $wp 'proxyUsed' $false);pingMs=(HV $wp 'pingMs' $null)
  downloadMbps=(HV $wp 'downloadMbps' $null);uploadMbps=(HV $wp 'uploadMbps' $null)
  downloadSampleBytes=(HV $wp 'downloadSampleBytes' 0);uploadSampleBytes=(HV $wp 'uploadSampleBytes' 0)
 }
 if(-not $out.warp.proxyUsed){throw 'WARP_PATH_NOT_PROXY'}
 $node=Run-Engine 'NodeBenchmarkBatch' 'NODE' 600
 $rows=@(HV $node 'results' @());$safeRows=@()
 foreach($rr in $rows){$safeRows+=[ordered]@{status=[string](HV $rr 'status' '');ok=[bool](HV $rr 'ok' $false);pingMs=(HV $rr 'pingMs' $null);downloadMbps=(HV $rr 'downloadMbps' $null);uploadMbps=(HV $rr 'uploadMbps' $null);country=[string](HV $rr 'country' '');error=[string](HV $rr 'error' '')}}
 $out.nodeSample=[ordered]@{
  status='OBSERVED';benchmarked=[int](HV $node 'benchmarked' 0);passed=[int](HV $node 'passed' 0);failed=[int](HV $node 'failed' 0)
  eligible=[int](HV $node 'eligible' 0);remainingUnbenchmarked=[int](HV $node 'remainingUnbenchmarked' 0);rows=$safeRows
  interpretation='Ephemeral public-node availability sample; zero pass is not by itself a deterministic product defect.'
 }
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{Run-Engine 'Stop' 'AUTO' 60|Out-Null}catch{}
 foreach($rel in $StateFiles){$p=Join-Path $Root $rel;$sv=$Saved[$rel];if([bool]$sv.Exists){$par=Split-Path $p -Parent;if(!(Test-Path $par)){New-Item -ItemType Directory -Force -Path $par|Out-Null};[IO.File]::WriteAllBytes($p,[byte[]]$sv.Bytes)}else{Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue}}
 Remove-Item -LiteralPath $Warp -Recurse -Force -ErrorAction SilentlyContinue
 if($WarpEx -and (Test-Path -LiteralPath $WarpBackup)){Copy-Item -LiteralPath $WarpBackup -Destination $Warp -Recurse -Force}
 Start-Sleep -Milliseconds 600
 $ports=@(Active-Ports);$owners=@(Get-ChildItem -LiteralPath (Join-Path $Root 'data') -Filter owner.json -Recurse -ErrorAction SilentlyContinue)
 $stateOk=$true
 foreach($rel in $StateFiles){$p=Join-Path $Root $rel;$sv=$Saved[$rel];if($sv.Exists){if(!(Test-Path $p) -or (Get-FileHash $p -Algorithm SHA256).Hash -ne $sv.Sha){$stateOk=$false}}elseif(Test-Path $p){$stateOk=$false}}
 $out.cleanup=[ordered]@{stateRestored=$stateOk;activeProjectPorts=$ports;ownerFiles=$owners.Count;pass=($stateOk -and $ports.Count -eq 0 -and $owners.Count -eq 0)}
 if(-not $out.cleanup.pass){$out.status='FAIL';if(!$out.error){$out.error='POSTTEST_CLEANUP_FAILED'}}
 Write-J $out;$out|ConvertTo-Json -Depth 30
}
if($out.status -ne 'PASS'){exit 20}
