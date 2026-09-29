$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$App=Join-Path $Install 'app\FreeNetHub.ps1'
function Route{Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue|Sort-Object RouteMetric|Select-Object -First 1 InterfaceIndex,InterfaceAlias,NextHop,RouteMetric}
$pre=Route;$rows=@()
foreach($i in 0..4){
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $App -Smoke -SmokeTab $i
 $rows += [pscustomobject]@{tab=$i;exit=$LASTEXITCODE}
 if($LASTEXITCODE -ne 0){throw ('SMOKE_TAB_FAIL_'+$i)}
}
$post=Route
$restored=[bool]($pre -and $post -and $pre.InterfaceIndex -eq $post.InterfaceIndex -and [string]$pre.NextHop -eq [string]$post.NextHop)
if(!$restored){throw 'ROUTE_CHANGED_BY_SMOKE'}
[pscustomobject]@{status='PASS';tabs=$rows;pre=$pre;post=$post;routeUnchanged=$restored}|ConvertTo-Json -Depth 5
