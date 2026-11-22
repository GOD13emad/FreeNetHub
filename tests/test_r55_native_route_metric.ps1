[CmdletBinding()]
param(
 [string]$SourcePath=(Join-Path $PSScriptRoot '..\gateway\apply_elevated.ps1'),
 [string]$ControllerPath=(Join-Path $PSScriptRoot '..\gateway\gateway_control.ps1')
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Test the exact currently shipped gateway route-selection snippet with bounded
# in-memory cmdlet mocks. No host route, adapter, firewall or tunnel is mutated.
$source=Get-Content -LiteralPath $SourcePath -Raw -Encoding UTF8
$start='# FNH_DEFAULT_ROUTE_SELECTION_BEGIN'
$end='# FNH_DEFAULT_ROUTE_SELECTION_END'
if($source.Split(@($start),[StringSplitOptions]::None).Count -ne 2 -or
   $source.Split(@($end),[StringSplitOptions]::None).Count -ne 2){throw 'ROUTE_SELECTION_SOURCE_MARKER_UNIQUE_FAIL'}
$begin=$source.IndexOf($start)+$start.Length
$endIndex=$source.IndexOf($end)
if($endIndex -le $begin){throw 'ROUTE_SELECTION_BLOCK_INVALID'}
$script:snippet=$source.Substring($begin,$endIndex-$begin)

function Fail([string]$message){throw $message}
function Get-NetRoute {
 [CmdletBinding()]
 param([string]$AddressFamily,[string]$DestinationPrefix)
 if($AddressFamily -ne 'IPv4' -or $DestinationPrefix -ne '0.0.0.0/0'){throw 'MOCK_GET_NET_ROUTE_BAD_QUERY'}
 return $script:fakeRoutes
}
function Get-NetIPInterface {
 [CmdletBinding()]
 param([int]$InterfaceIndex,[string]$AddressFamily)
 if($AddressFamily -ne 'IPv4'){throw 'MOCK_BAD_IP_FAMILY'}
 if(-not $script:fakeMetrics.ContainsKey([string]$InterfaceIndex)){throw 'MOCK_IP_METRIC_NOT_AVAILABLE'}
 [pscustomobject]@{InterfaceMetric=$script:fakeMetrics[[string]$InterfaceIndex]}
}
function Get-NetAdapter {
 [CmdletBinding()]
 param([int]$InterfaceIndex)
 [pscustomobject]@{Name=('MOCK-'+$InterfaceIndex);ifIndex=$InterfaceIndex}
}
function Test-Selection {
 param(
  [string]$CaseName,
  [ValidateSet('PC_TUNNEL','CONSOLE_ONLY')][string]$RequestedMode,
  [object[]]$Routes,
  [hashtable]$Metrics,
  [int]$ExpectedIndex=0,
  [string]$ExpectedError=''
 )
 $script:fakeRoutes=$Routes
 $script:fakeMetrics=$Metrics
 $Mode=$RequestedMode
 $def=$null
 $uplink=$null
 $thrown=$null
 try{Invoke-Expression $script:snippet}
 catch{$thrown=$_.Exception.Message}
 if($ExpectedError){
  if($thrown -notmatch [regex]::Escape($ExpectedError)){
   throw ("CASE_"+$CaseName+": expected error '"+$ExpectedError+"' got '"+$thrown+"'")
  }
 }else{
  if($thrown){throw ("CASE_"+$CaseName+": unexpected error '"+$thrown+"'")}
  if([int]$def.InterfaceIndex -ne $ExpectedIndex -or [int]$uplink.ifIndex -ne $ExpectedIndex){
   throw ("CASE_"+$CaseName+": wrong uplink: route="+[string]$def.InterfaceIndex+" adapter="+[string]$uplink.ifIndex)
  }
 }
 Write-Host ('PASS_'+$CaseName)
}
$route11=[pscustomobject]@{InterfaceIndex=11;InterfaceAlias='MOCK-11';RouteMetric=0;NextHop='192.0.2.1'}
$route12=[pscustomobject]@{InterfaceIndex=12;InterfaceAlias='MOCK-12';RouteMetric=1;NextHop='198.51.100.1'}
$route12zero=[pscustomobject]@{InterfaceIndex=12;InterfaceAlias='MOCK-12';RouteMetric=0;NextHop='198.51.100.1'}
Test-Selection 'NATIVE_METRIC_SUM_NOT_ROUTE_METRIC_ALONE' 'PC_TUNNEL' @($route11,$route12) @{'11'=45;'12'=10} 12
Test-Selection 'NATIVE_SAME_ROUTE_METRIC_PREFERS_LOWER_INTERFACE_METRIC' 'PC_TUNNEL' @($route11,$route12zero) @{'11'=45;'12'=10} 12
Test-Selection 'NATIVE_ONE_DEFAULT_ROUTE' 'PC_TUNNEL' @($route11) @{'11'=20} 11
Test-Selection 'NATIVE_EQUAL_TOTAL_METRIC_FAIL_CLOSED' 'PC_TUNNEL' @($route11,$route12) @{'11'=21;'12'=20} 0 'PC_TUNNEL_DEFAULT_UPLINK_METRIC_TIE'
Test-Selection 'NATIVE_UNREADABLE_METRIC_FAIL_CLOSED' 'PC_TUNNEL' @($route11,$route12) @{'11'=21} 0 'PC_TUNNEL_DEFAULT_UPLINK_METRIC_UNREADABLE'
Test-Selection 'NATIVE_MISSING_DEFAULT_FAIL_CLOSED' 'PC_TUNNEL' @() @{} 0 'NO_DEFAULT_ROUTE'
Test-Selection 'CONSOLE_RETAINS_LEGACY_SELECTION' 'CONSOLE_ONLY' @($route11,$route12) @{'11'=45;'12'=10} 11
# Exercise real gateway_control's pre-provider base-route selector, not just
# apply_elevated's independent last-chance route gate.
$controller=Get-Content -LiteralPath $ControllerPath -Raw -Encoding UTF8
$controlStart='# FNH_PC_BASE_ROUTE_SELECTION_BEGIN'
$controlEnd='# FNH_PC_BASE_ROUTE_SELECTION_END'
if($controller.Split(@($controlStart),[StringSplitOptions]::None).Count -ne 2 -or
   $controller.Split(@($controlEnd),[StringSplitOptions]::None).Count -ne 2){throw 'PC_CONTROLLER_ROUTE_SELECTION_BLOCK_UNIQUE_FAIL'}
$sectionBegin=$controller.IndexOf($controlStart)+$controlStart.Length
$sectionEnd=$controller.IndexOf($controlEnd)
if($sectionEnd -le $sectionBegin){throw 'PC_CONTROLLER_SOURCE_BLOCK_INVERTED'}
# Invoke-Expression defines the isolated real source's read-only function in this
# script's mock scope. No controller main program is invoked.
Invoke-Expression $controller.Substring($sectionBegin,$sectionEnd-$sectionBegin)
if($controller.IndexOf('[void](Get-BaseRouteSnapshot)') -lt 0 -or
   $controller.IndexOf('[void](Get-BaseRouteSnapshot)') -gt $controller.IndexOf("Run-Engine 'Verify' 'NODE'")){
 throw 'PC_ROUTE_PREFLIGHT_NOT_BEFORE_PROVIDER'
}
function Get-NetIPAddress {
 [CmdletBinding()]
 param([string]$AddressFamily,[int]$InterfaceIndex)
 if($AddressFamily -ne 'IPv4'){throw 'MOCK_BAD_ADDRESS_FAMILY'}
 if(@($script:fakeMissingSources|Where-Object{$_ -eq $InterfaceIndex}).Count){return}
 [pscustomobject]@{IPAddress=('192.0.2.'+$InterfaceIndex);SkipAsSource=$false;PrefixLength=24}
}
function Test-BaseRouteSnapshot {
 param(
  [string]$CaseName,
  [object[]]$Routes,
  [hashtable]$Metrics,
  [int]$ExpectedIndex=0,
  [string]$ExpectedError='',
  [int[]]$MissingSources=@()
 )
 $script:fakeRoutes=$Routes
 $script:fakeMetrics=$Metrics
 $script:fakeMissingSources=@($MissingSources)
 $got=$null;$err=$null
 try{$got=Get-BaseRouteSnapshot}catch{$err=$_.Exception.Message}
 if($ExpectedError){
  if($err -notmatch [regex]::Escape($ExpectedError)){throw ('CONTROLLER_'+$CaseName+': unexpected error '+$err)}
 }else{
  if($err){throw ('CONTROLLER_'+$CaseName+': unexpected exception '+$err)}
  if([int]$got.ifIndex -ne $ExpectedIndex){throw ('CONTROLLER_'+$CaseName+': index '+[string]$got.ifIndex)}
 }
 Write-Host ('PASS_CONTROLLER_'+$CaseName)
}
$route13=[pscustomobject]@{InterfaceIndex=13;InterfaceAlias='MOCK-13';RouteMetric=0;NextHop='203.0.113.1'}
# Current dual-wired uplink + Wi-Fi pattern: interface metrics 25,25,35;
# RouteMetric zero for every default means two equally preferred routes.
Test-BaseRouteSnapshot -CaseName 'THREE_WAY_TWO_EQUAL_TOTALS_DENIED' -Routes @($route11,$route12zero,$route13) -Metrics @{'11'=25;'12'=25;'13'=35} -ExpectedError 'BASE_ROUTE_METRIC_TIE'
Test-BaseRouteSnapshot -CaseName 'UNIQUE_LOWER_SUM_CHOSEN' -Routes @($route11,$route12zero) -Metrics @{'11'=35;'12'=25} -ExpectedIndex 12
Test-BaseRouteSnapshot -CaseName 'SOURCE_MISSING_REJECTED' -Routes @($route11,$route12zero) -Metrics @{'11'=35;'12'=25} -MissingSources @(11) -ExpectedError 'BASE_ROUTE_SOURCE_OR_METRIC_UNVERIFIED'
Test-BaseRouteSnapshot -CaseName 'METRIC_MISSING_REJECTED' -Routes @($route11,$route12zero) -Metrics @{'11'=35} -ExpectedError 'BASE_ROUTE_SOURCE_OR_METRIC_UNVERIFIED'
Test-BaseRouteSnapshot -CaseName 'NO_DEFAULT_REJECTED' -Routes @() -Metrics @{} -ExpectedError 'BASE_ROUTE_UNAVAILABLE'
Write-Host 'R55_NATIVE_DEFAULT_ROUTE_METRIC_FAIL_CLOSED_PASS'
