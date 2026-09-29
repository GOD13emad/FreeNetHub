$ErrorActionPreference='Stop'
$Name='Ethernet 3'
$Component='ms_tcpip6'
$Root=Split-Path $PSScriptRoot -Parent`r`n$Evidence=Join-Path $Root 'evidence\R34_IPV6_BINDING_POSTSTATE_20260928.json'
$before=Get-NetAdapterBinding -Name $Name -ComponentID $Component -ErrorAction Stop
if(-not $before.Enabled){
  Enable-NetAdapterBinding -Name $Name -ComponentID $Component -ErrorAction Stop | Out-Null
}
Start-Sleep -Seconds 3
$after=Get-NetAdapterBinding -Name $Name -ComponentID $Component -ErrorAction Stop
$ips=@(Get-NetIPAddress -InterfaceAlias $Name -AddressFamily IPv6 -ErrorAction SilentlyContinue | ForEach-Object {
  [ordered]@{ip=$_.IPAddress;prefixLength=$_.PrefixLength;state=[string]$_.AddressState;prefixOrigin=[string]$_.PrefixOrigin;suffixOrigin=[string]$_.SuffixOrigin}
})
$routes=@(Get-NetRoute -InterfaceAlias $Name -AddressFamily IPv6 -ErrorAction SilentlyContinue | Where-Object DestinationPrefix -eq '::/0' | ForEach-Object {
  [ordered]@{destination=$_.DestinationPrefix;nextHop=$_.NextHop;routeMetric=$_.RouteMetric}
})
[ordered]@{
 schema=1
 checked=(Get-Date).ToString('o')
 interface=$Name
 componentId=$Component
 beforeEnabled=[bool]$before.Enabled
 afterEnabled=[bool]$after.Enabled
 ipv6Addresses=$ips
 ipv6DefaultRoutes=$routes
 mutation='Enable-NetAdapterBinding only'
 rollback="Disable-NetAdapterBinding -Name '$Name' -ComponentID $Component"
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Evidence -Encoding UTF8
