[CmdletBinding()]
param(
 [ValidateSet('PC_TUNNEL','CONSOLE_ONLY')][string]$Mode='PC_TUNNEL',
 [string]$ConfigPath
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Defaults=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
$sbInfo=$null;try{$sbInfo=Get-FnhSingBox}catch{};$sb=if($sbInfo){$sbInfo.path}else{''};$cc=Get-FnhConsoleConfig $Defaults -AllowUnconfigured
$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$hash=if(Test-Path -LiteralPath $sb){(Get-FileHash -LiteralPath $sb -Algorithm SHA256).Hash}else{''}
$def=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue|Sort-Object RouteMetric|Select-Object -First 1
$uplink=if($def){Get-NetAdapter -InterfaceIndex $def.InterfaceIndex -ErrorAction SilentlyContinue}else{$null}
$console=if($cc.adapter_description){Get-NetAdapter -ErrorAction SilentlyContinue|Where-Object{$_.HardwareInterface -and $_.InterfaceDescription -eq $cc.adapter_description}|Select-Object -First 1}else{$null}
[pscustomobject]@{
 mode=$Mode
 elevated=$admin
 singBoxPath=$sb
 singBoxHash=$hash
 singBoxPinned=[bool]($sbInfo -and $hash -eq $sbInfo.sha256)
 configExists=if($ConfigPath){Test-Path -LiteralPath $ConfigPath}else{$false}
 consoleAdapter=if($console){[pscustomobject]@{Name=$console.Name;Description=$console.InterfaceDescription;Guid=$console.InterfaceGuid;Mac=$console.MacAddress;Status=$console.Status;IfIndex=$console.ifIndex}}else{$null}
 defaultUplink=if($uplink){[pscustomobject]@{Name=$uplink.Name;Description=$uplink.InterfaceDescription;IfIndex=$uplink.ifIndex;Gateway=$def.NextHop}}else{$null}
 gatewayOwnerExists=(Test-Path (Join-Path $PSScriptRoot 'runtime\owner.json'))
 projectTunExists=[bool](Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq $Defaults.tun.interface_name -or $_.InterfaceDescription -match 'sing-box|Wintun'})
}|ConvertTo-Json -Depth 6
