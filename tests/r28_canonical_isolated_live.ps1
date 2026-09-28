$ErrorActionPreference='Stop'
Set-StrictMode -Version 3.0
$Project=Split-Path $PSScriptRoot -Parent
$Primary=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Root=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub-R28-LiveQual'
$Evidence=Join-Path $Project 'evidence\R28_CANONICAL_ISOLATED_LIVE_ACCEPTANCE_20260928.json'
$ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
if(@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count){throw 'QUAL_PRETEST_PROJECT_LISTENER_ACTIVE'}
if(Test-Path $Root){Remove-Item $Root -Recurse -Force}
New-Item -ItemType Directory -Force -Path $Root,(Join-Path $Root 'data'),(Join-Path $Root 'jobs'),(Join-Path $Root 'gateway\runtime')|Out-Null
Copy-Item (Join-Path $Primary 'app') (Join-Path $Root 'app') -Recurse -Force
Copy-Item (Join-Path $Primary 'RELEASE.json') (Join-Path $Root 'RELEASE.json') -Force
Copy-Item (Join-Path $Primary 'settings.json') (Join-Path $Root 'settings.json') -Force
Copy-Item (Join-Path $Primary 'data\nodes.json') (Join-Path $Root 'data\nodes.json') -Force
Copy-Item (Join-Path $Primary 'data\node_public_refresh.json') (Join-Path $Root 'data\node_public_refresh.json') -Force
Copy-Item (Join-Path $Primary 'gateway\runtime\local_gateway.json') (Join-Path $Root 'gateway\runtime\local_gateway.json') -Force
$map=@{
 engine='app\engine.py';nodehub='app\nodehub.py';ui='app\FreeNetHub.ps1';view='app\View.xaml';manifest='app\manifest.json';release='RELEASE.json'
}
$parity=[ordered]@{}
foreach($k in $map.Keys){
 $rel=$map[$k];$a=(Get-FileHash (Join-Path $Primary $rel) -Algorithm SHA256).Hash;$b=(Get-FileHash (Join-Path $Root $rel) -Algorithm SHA256).Hash
 $parity[$k]=$a;if($a -ne $b){throw ('QUAL_COPY_PARITY_'+$k)}
}
if(Test-Path (Join-Path $Root 'data\Browser_Primary')){throw 'QUAL_BROWSER_PROFILE_COPIED'}
function HV($H,[string]$K,$D=$null){if($H -is [Collections.IDictionary] -and $H.Contains($K)){return $H[$K]};return $D}
function Run-E([string]$Action,[string]$Mode='AUTO',[int]$Budget=600){
 $job=[guid]::NewGuid().ToString('N')
 & python (Join-Path $Root 'app\engine.py') --action $Action --mode $Mode --job $job --budget $Budget | Out-Null
 $ec=$LASTEXITCODE;$jp=Join-Path $Root ('jobs\'+$job+'.json')
 if(!(Test-Path $jp)){throw ('QUAL_RESULT_MISSING_'+$Action)}
 $rec=Get-Content $jp -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable;$rx=[int](HV $rec 'exit' 999)
 if($ec -ne $rx){throw ($Action+'_EXIT_CONTRACT')}
 if($rx -ne 0){$rr=HV $rec 'result' @{};throw ($Action+'_FAILED_'+[string](HV $rr 'error' 'UNKNOWN'))}
 return (HV $rec 'result' @{})
}
$out=[ordered]@{schema=2;date='2026-09-28';status='FAIL';artifactSha256='2AA91D849A513A21D3BF9903F8E72FFB6A184D378FB357CE4FA7A9D6F7EB0073';runtimeCopyParity=$parity;browserProfileCopied=$false;direct=@{};update=@{};warp=@{};nodeSample=@{};cleanup=@{};error='';privacy='No raw node URI, credential, server address, user IP, or raw exit IP is persisted.'}
try{
 $d=Run-E 'Speed' 'DIRECT' 90;$route=HV $d 'defaultRoute' @{}
 if(-not [bool](HV $d 'ok' $false) -or [bool](HV $d 'proxyUsed' $true) -or -not [bool](HV $route 'trustedPhysical' $false)){throw 'QUAL_DIRECT_PROOF_FAILED'}
 $out.direct=[ordered]@{status='PASS';pingMs=(HV $d 'pingMs' $null);downloadMbps=(HV $d 'downloadMbps' $null);uploadMbps=(HV $d 'uploadMbps' $null);physicalRouteTrusted=$true;cloudflareWarp=[string](HV $d 'cloudflareWarp' '');cloudflareGateway=[string](HV $d 'cloudflareGateway' '')}
 $u=Run-E 'UpdateCheck' 'AUTO' 60;$asset=HV $u 'asset' $null
 $out.update=[ordered]@{status='PASS';currentRevisionNumber=[int](HV $u 'currentRevisionNumber' 0);remoteRevisionNumber=[int](HV $u 'remoteRevisionNumber' 0);updateAvailable=[bool](HV $u 'updateAvailable' $false);digestPresent=[bool]($asset -is [Collections.IDictionary] -and ([string](HV $asset 'digest' '')).StartsWith('sha256:'))}
 if($out.update.currentRevisionNumber -ne 28){throw 'QUAL_UPDATE_LOCAL_REVISION_WRONG'}
 $w=Run-E 'ProviderBenchmark' 'WARP' 300;$wp=HV $w 'performance' @{};$wh=HV $w 'health' @{}
 if(-not [bool](HV $wp 'ok' $false) -or -not [bool](HV $wp 'proxyUsed' $false) -or -not [bool](HV $wh 'healthy' $false)){throw 'QUAL_WARP_FAILED'}
 $out.warp=[ordered]@{status='PASS';temporary=[bool](HV $w 'temporary' $false);pingMs=(HV $wp 'pingMs' $null);downloadMbps=(HV $wp 'downloadMbps' $null);uploadMbps=(HV $wp 'uploadMbps' $null);proxyUsed=$true}
 $n=Run-E 'NodeBenchmarkBatch' 'NODE' 600;$rows=@()
 foreach($rr in @(HV $n 'results' @())){$rows+=[ordered]@{status=[string](HV $rr 'status' '');ok=[bool](HV $rr 'ok' $false);pingMs=(HV $rr 'pingMs' $null);downloadMbps=(HV $rr 'downloadMbps' $null);uploadMbps=(HV $rr 'uploadMbps' $null);country=[string](HV $rr 'country' '');error=[string](HV $rr 'error' '')}}
 $out.nodeSample=[ordered]@{status='OBSERVED';benchmarked=[int](HV $n 'benchmarked' 0);passed=[int](HV $n 'passed' 0);failed=[int](HV $n 'failed' 0);eligible=[int](HV $n 'eligible' 0);remaining=[int](HV $n 'remainingUnbenchmarked' 0);rows=$rows;interpretation='Ephemeral public-node sample; invalid paths retain Ping/TCP delay where available and throughput stays N/A.'}
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 try{Run-E 'Stop' 'AUTO' 60|Out-Null}catch{}
 Start-Sleep -Milliseconds 500
 $active=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort});$owners=@(Get-ChildItem (Join-Path $Root 'data') -Filter owner.json -Recurse -ErrorAction SilentlyContinue)
 $out.cleanup=[ordered]@{activeProjectPorts=$active.Count;ownerFiles=$owners.Count;pass=($active.Count -eq 0 -and $owners.Count -eq 0)}
 if(-not $out.cleanup.pass){$out.status='FAIL';if(!$out.error){$out.error='QUAL_CLEANUP_FAILED'}}
 [IO.File]::WriteAllText($Evidence,($out|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
 Remove-Item $Root -Recurse -Force -ErrorAction SilentlyContinue
 $out.cleanup['qualificationRootRemoved']=(-not (Test-Path $Root))
 if(-not $out.cleanup.qualificationRootRemoved){$out.status='FAIL';if(!$out.error){$out.error='QUAL_ROOT_NOT_REMOVED'}}
 [IO.File]::WriteAllText($Evidence,($out|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false));$out|ConvertTo-Json -Depth 30
}
if($out.status -ne 'PASS'){exit 28}
