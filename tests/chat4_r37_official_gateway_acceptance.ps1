$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Req=Join-Path $Install 'gateway\gateway_request.ps1'
$Engine=Join-Path $Install 'app\engine.py'
$Deps=Get-Content (Join-Path $Install 'app\dependencies.json') -Raw -Encoding UTF8|ConvertFrom-Json
$Py=[string]$Deps.pythonw
if($Py -and $Py.EndsWith('pythonw.exe',[StringComparison]::OrdinalIgnoreCase)){$Py=$Py.Substring(0,$Py.Length-11)+'python.exe'}
if(!$Py -or !(Test-Path $Py)){$Py=(Get-Command python.exe -ErrorAction Stop).Source}
$ProjectRoot=Split-Path $PSScriptRoot -Parent
$Evidence=Join-Path $ProjectRoot 'evidence\CHAT4_R37_FS_OFFICIAL_GATEWAY_ACCEPTANCE_20260929.json'
$StartJob='c4a12929c4a12929c4a12929c4a12929'
$UpdateJob='c4b22929c4b22929c4b22929c4b22929'
$SpeedJob='c4c32929c4c32929c4c32929c4c32929'
$StopJob='c4d42929c4d42929c4d42929c4d42929'
function Route{Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue|Sort-Object RouteMetric|Select-Object -First 1 InterfaceIndex,InterfaceAlias,NextHop,RouteMetric}
function ReadJ([string]$p){if(Test-Path $p){Get-Content $p -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}}
function RunEngine([string]$a,[string]$m,[string]$j,[int]$b){
 & $Py $Engine --action $a --mode $m --job $j --budget $b|Out-Null
 $ec=$LASTEXITCODE;$r=ReadJ (Join-Path $Install ('jobs\'+$j+'.json'))
 [pscustomobject]@{exit=$ec;record=$r}
}
$errors=New-Object System.Collections.Generic.List[string]
$pre=Route;$start=$null;$update=$null;$speed=$null;$stop=$null;$post=$null
try{
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Req -Action StartPc -Job $StartJob -Provider WARP
 $start=ReadJ (Join-Path $Install ('jobs\gateway-'+$StartJob+'.json'))
 if(!$start -or [int]$start.exit -ne 0){throw ('START_FAIL '+[string]$start.result.error)}
 $update=RunEngine 'UpdateCheck' 'AUTO' $UpdateJob 60
 if($update.exit -ne 0 -or !$update.record -or [int]$update.record.exit -ne 0){throw ('UPDATE_FAIL '+[string]$update.record.result.error)}
 if(-not [bool]$update.record.result.rootPath.bound){throw 'ROOT_NOT_BOUND'}
 if([string]$update.record.result.rootPath.proof -notmatch '^BOUND_PRE_TUN_'){throw 'ROOT_PROOF_MISSING'}
 $speed=RunEngine 'SystemSpeed' 'WARP' $SpeedJob 120
 if($speed.exit -ne 0 -or !$speed.record -or [int]$speed.record.exit -ne 0){throw ('SPEED_FAIL '+[string]$speed.record.result.error)}
 if(-not [bool]$speed.record.result.ok -or [string]$speed.record.result.warp -ne 'on'){throw 'SYSTEM_WARP_VERIFY_FAIL'}
}catch{$errors.Add($_.Exception.Message)}
finally{
 try{
  & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Req -Action Stop -Job $StopJob
  $stop=ReadJ (Join-Path $Install ('jobs\gateway-'+$StopJob+'.json'))
  if(!$stop -or [int]$stop.exit -ne 0){$errors.Add('STOP_FAIL')}
 }catch{$errors.Add('STOP_EXCEPTION '+$_.Exception.Message)}
 Start-Sleep -Seconds 2;$post=Route
}
$restored=[bool]($pre -and $post -and $pre.InterfaceIndex -eq $post.InterfaceIndex -and [string]$pre.NextHop -eq [string]$post.NextHop)
if(!$restored){$errors.Add('ROUTE_NOT_RESTORED')}
$out=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($errors.Count -eq 0){'PASS'}else{'FAIL'});pre=$pre;start=$start;update=$update;systemSpeed=$speed;stop=$stop;post=$post;routeRestored=$restored;errors=@($errors)}
$out|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $Evidence -Encoding UTF8
$out|ConvertTo-Json -Depth 20
exit $(if($errors.Count -eq 0){0}else{20})
