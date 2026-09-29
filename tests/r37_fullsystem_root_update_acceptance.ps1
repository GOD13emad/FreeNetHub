$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ProjectRoot=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Gateway=Join-Path $Install 'gateway\gateway_control.ps1'
$Engine=Join-Path $Install 'app\engine.py'
$DepsPath=Join-Path $Install 'app\dependencies.json'
$Evidence=Join-Path $ProjectRoot 'evidence\R37_FULLSYSTEM_ROOT_UPDATE_ACCEPTANCE_20260929.json'
function Write-JsonAtomic([string]$Path,$Value){
  $tmp=$Path+'.tmp'
  $Value|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $tmp -Encoding UTF8
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Get-DefaultRoute{
  $rows=@()
  foreach($r in @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue)){
    try{
      $ifi=Get-NetIPInterface -AddressFamily IPv4 -InterfaceIndex ([int]$r.InterfaceIndex) -ErrorAction Stop
      $rows += [pscustomobject]@{
        ifIndex=[int]$r.InterfaceIndex;interfaceAlias=[string]$r.InterfaceAlias
        nextHop=[string]$r.NextHop;routeMetric=[int]$r.RouteMetric
        interfaceMetric=[int]$ifi.InterfaceMetric
        totalMetric=([int]$r.RouteMetric+[int]$ifi.InterfaceMetric)
      }
    }catch{}
  }
  $rows|Sort-Object totalMetric,routeMetric,interfaceMetric|Select-Object -First 1
}
function Get-Trace{
  $raw=& curl.exe -4 --noproxy '*' --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
  if($LASTEXITCODE -ne 0){throw 'TRACE_FAIL'}
  $o=[ordered]@{}
  foreach($line in ($raw -split '\r?\n')){if($line -match '^([^=]+)=(.*)$'){$o[$matches[1]]=$matches[2]}}
  [pscustomobject]$o
}
function Run-Gateway([string]$Action,[string]$ResultPath,[string]$Provider='WARP'){
  Remove-Item -LiteralPath $ResultPath -Force -ErrorAction SilentlyContinue
  $args=@('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$Gateway,'-Action',$Action,'-ResultPath',$ResultPath)
  if($Action -eq 'StartPc'){$args+=@('-Provider',$Provider)}
  $p=Start-Process -FilePath 'pwsh.exe' -ArgumentList $args -WindowStyle Hidden -Wait -PassThru
  $rec=if(Test-Path -LiteralPath $ResultPath){Get-Content -LiteralPath $ResultPath -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
  [pscustomobject]@{processExit=$p.ExitCode;record=$rec}
}
function Run-Engine([string]$Action,[string]$Mode,[int]$Budget=180){
  $deps=Get-Content -LiteralPath $DepsPath -Raw -Encoding UTF8|ConvertFrom-Json
  $py=[string]$deps.pythonw
  if($py -and $py.EndsWith('pythonw.exe',[StringComparison]::OrdinalIgnoreCase)){$py=$py.Substring(0,$py.Length-11)+'python.exe'}
  if(!$py -or !(Test-Path -LiteralPath $py)){$py=[string](Get-Command python.exe -ErrorAction Stop).Source}
  $job=[guid]::NewGuid().ToString('N')
  $result=Join-Path $Install ('jobs\'+$job+'.json')
  $p=Start-Process -FilePath $py -ArgumentList @($Engine,'--action',$Action,'--mode',$Mode,'--job',$job,'--budget',[string]$Budget) -WindowStyle Hidden -Wait -PassThru
  $rec=if(Test-Path -LiteralPath $result){Get-Content -LiteralPath $result -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
  [pscustomobject]@{processExit=$p.ExitCode;record=$rec;job=$job}
}
function Route-Public($r){
  if(!$r){return $null}
  [ordered]@{ifIndex=$r.ifIndex;interfaceAlias=$r.interfaceAlias;nextHop=$r.nextHop;routeMetric=$r.routeMetric;interfaceMetric=$r.interfaceMetric}
}
function Trace-Public($t){
  if(!$t){return $null}
  [ordered]@{loc=$t.loc;colo=$t.colo;warp=$t.warp;gateway=$t.gateway}
}
$errors=New-Object System.Collections.Generic.List[string]
$preRoute=$null;$preTrace=$null;$duringRoute=$null;$duringTrace=$null;$start=$null;$update=$null;$speed=$null;$stop=$null;$postRoute=$null;$postTrace=$null
try{
  if(!(Test-Path -LiteralPath $Gateway)){throw 'INSTALLED_GATEWAY_MISSING'}
  if(!(Test-Path -LiteralPath $Engine)){throw 'INSTALLED_ENGINE_MISSING'}
  $preRoute=Get-DefaultRoute;if(!$preRoute){throw 'PRE_DEFAULT_ROUTE_MISSING'};$preTrace=Get-Trace
  $startPath=Join-Path $Install ('jobs\gateway-r37fs-start-'+[guid]::NewGuid().ToString('N')+'.json')
  $start=Run-Gateway 'StartPc' $startPath 'WARP'
  if($start.processExit -ne 0 -or !$start.record -or [int]$start.record.exit -ne 0){throw ('START_PC_FAILED '+[string]$start.record.result.error)}
  Start-Sleep -Seconds 2
  $duringRoute=Get-DefaultRoute;$duringTrace=Get-Trace
  $update=Run-Engine 'UpdateCheck' 'AUTO' 60
  if($update.processExit -ne 0 -or !$update.record -or [int]$update.record.exit -ne 0){throw ('UPDATECHECK_ACTIVE_TUN_FAILED '+[string]$update.record.result.error)}
  if(-not [bool]$update.record.result.rootPath.bound){throw 'UPDATE_ROOT_NOT_BOUND'}
  if([string]$update.record.result.rootPath.interfaceAlias -ne [string]$preRoute.interfaceAlias){throw 'UPDATE_ROOT_INTERFACE_MISMATCH'}
  if([string]$update.record.result.rootPath.proof -notmatch '^BOUND_PRE_TUN_'){throw 'UPDATE_ROOT_PROOF_MISSING'}
  $speed=Run-Engine 'SystemSpeed' 'WARP' 120
  if($speed.processExit -ne 0 -or !$speed.record -or [int]$speed.record.exit -ne 0){throw ('SYSTEM_SPEED_FAILED '+[string]$speed.record.result.error)}
  if(-not [bool]$speed.record.result.ok){throw ('SYSTEM_SPEED_NOT_OK '+[string]$speed.record.result.error)}
  if([string]$speed.record.result.warp -ne 'on'){throw 'SYSTEM_SPEED_WARP_NOT_ON'}
}catch{$errors.Add($_.Exception.Message)}
finally{
  try{
    $stopPath=Join-Path $Install ('jobs\gateway-r37fs-stop-'+[guid]::NewGuid().ToString('N')+'.json')
    $stop=Run-Gateway 'Stop' $stopPath
    if($stop.processExit -ne 0 -or !$stop.record -or [int]$stop.record.exit -ne 0){$errors.Add('STOP_FAILED')}
  }catch{$errors.Add('STOP_EXCEPTION '+$_.Exception.Message)}
  Start-Sleep -Seconds 2
  try{$postRoute=Get-DefaultRoute}catch{$errors.Add('POST_ROUTE_FAIL')}
  try{$postTrace=Get-Trace}catch{$errors.Add('POST_TRACE_FAIL')}
}
$routeRestored=[bool]($preRoute -and $postRoute -and [int]$preRoute.ifIndex -eq [int]$postRoute.ifIndex -and [string]$preRoute.nextHop -eq [string]$postRoute.nextHop -and [string]$preRoute.interfaceAlias -eq [string]$postRoute.interfaceAlias)
if(-not $routeRestored){$errors.Add('DEFAULT_ROUTE_NOT_RESTORED')}
$warpRestored=[bool]($preTrace -and $postTrace -and [string]$preTrace.warp -eq [string]$postTrace.warp)
if(-not $warpRestored){$errors.Add('TRACE_WARP_STATE_NOT_RESTORED')}
$out=[ordered]@{
  schema=2;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($errors.Count -eq 0){'PASS'}else{'FAIL'})
  installedRoot='%LOCALAPPDATA%\Programs\FreeNetHub'
  installedManifestSha256=(Get-FileHash -LiteralPath (Join-Path $Install 'app\manifest.json') -Algorithm SHA256).Hash
  installedEngineSha256=(Get-FileHash -LiteralPath $Engine -Algorithm SHA256).Hash
  installedGatewayManifestSha256=(Get-FileHash -LiteralPath (Join-Path $Install 'gateway\manifest.json') -Algorithm SHA256).Hash
  pre=[ordered]@{route=(Route-Public $preRoute);trace=(Trace-Public $preTrace)}
  start=[ordered]@{processExit=$start.processExit;exit=$(if($start.record){$start.record.exit}else{$null});error=$(if($start.record){$start.record.result.error}else{'RESULT_MISSING'})}
  during=[ordered]@{route=(Route-Public $duringRoute);trace=(Trace-Public $duringTrace)}
  update=$(if($update){[ordered]@{processExit=$update.processExit;exit=$update.record.exit;currentRevision=$update.record.result.currentRevision;updateAvailable=$update.record.result.updateAvailable;rootPath=$update.record.result.rootPath}}else{$null})
  systemSpeed=$(if($speed){[ordered]@{processExit=$speed.processExit;exit=$speed.record.exit;ok=$speed.record.result.ok;pingMs=$speed.record.result.pingMs;downloadMbps=$speed.record.result.downloadMbps;uploadMbps=$speed.record.result.uploadMbps;country=$speed.record.result.country;warp=$speed.record.result.warp;error=$speed.record.result.error}}else{$null})
  stop=[ordered]@{processExit=$stop.processExit;exit=$(if($stop.record){$stop.record.exit}else{$null})}
  post=[ordered]@{route=(Route-Public $postRoute);trace=(Trace-Public $postTrace)}
  routeRestored=$routeRestored;warpStateRestored=$warpRestored;errors=@($errors)
}
Write-JsonAtomic $Evidence $out
$out|ConvertTo-Json -Depth 20
exit $(if($errors.Count -eq 0){0}else{20})
