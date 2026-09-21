$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$script:FnhGatewayDir=(Resolve-Path $PSScriptRoot).Path
$script:FnhProjectRoot=(Split-Path $script:FnhGatewayDir -Parent)
$script:FnhLocalGatewayConfig=Join-Path $script:FnhGatewayDir 'runtime\local_gateway.json'
function Get-FnhLocalGatewayConfig([switch]$AllowMissing){
 if(!(Test-Path -LiteralPath $script:FnhLocalGatewayConfig)){if($AllowMissing){return $null};throw 'LOCAL_GATEWAY_CONFIG_MISSING'}
 $j=Get-Content -LiteralPath $script:FnhLocalGatewayConfig -Raw -Encoding UTF8|ConvertFrom-Json
 if([int]$j.schema -notin @(1,2)){throw 'LOCAL_GATEWAY_CONFIG_SCHEMA'};return $j
}
function Get-FnhPython{
 $dep=Join-Path $script:FnhProjectRoot 'app\dependencies.json'
 if(!(Test-Path -LiteralPath $dep)){throw 'APP_DEPENDENCIES_MISSING'}
 $d=Get-Content -LiteralPath $dep -Raw -Encoding UTF8|ConvertFrom-Json
 $py='';if($d.pythonw){$candidate=Join-Path (Split-Path ([string]$d.pythonw) -Parent) 'python.exe';if(Test-Path -LiteralPath $candidate){$py=(Resolve-Path -LiteralPath $candidate).Path}}
 if(!$py){$g=Get-Command python.exe -ErrorAction SilentlyContinue;if($g){$py=$g.Source}}
 if(!$py -or !(Test-Path -LiteralPath $py -PathType Leaf)){throw 'PYTHON_RUNTIME_MISSING'}
 return $py
}
function Get-FnhSingBox{
 $l=Get-FnhLocalGatewayConfig
 if(!$l.PSObject.Properties['singbox'] -or !$l.singbox -or ![string]$l.singbox.path -or [string]$l.singbox.sha256 -notmatch '^[A-Fa-f0-9]{64}$'){throw 'LOCAL_SINGBOX_CONFIG_INVALID'}
 $p=[string]$l.singbox.path;if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'SINGBOX_MISSING'};$p=(Resolve-Path -LiteralPath $p).Path
 $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash;if($actual -ne [string]$l.singbox.sha256){throw 'SINGBOX_HASH_MISMATCH'}
 return [pscustomobject]@{path=$p;sha256=$actual}
}
function Get-FnhConsoleConfig([object]$Defaults,[switch]$AllowUnconfigured){
 $l=Get-FnhLocalGatewayConfig -AllowMissing
 $desc='';$name='';$mac='';$hid='';$busid='';if($l -and $l.PSObject.Properties['console'] -and $l.console){$desc=[string]$l.console.adapter_description;$name=[string]$l.console.adapter_name;$mac=[string]$l.console.mac_address;$hid=[string]$l.console.hardware_id;$busid=[string]$l.console.busid}
 if(!$desc -and [string]$Defaults.console.adapter_description -ne 'CONFIGURE_IN_RUNTIME'){$desc=[string]$Defaults.console.adapter_description}
 if(!$name -and [string]$Defaults.console.adapter_name -ne 'CONFIGURE_IN_RUNTIME'){$name=[string]$Defaults.console.adapter_name}
 if(!$desc -and !$AllowUnconfigured){throw 'CONSOLE_ADAPTER_NOT_CONFIGURED'}
 return [pscustomobject]@{adapter_name=$name;adapter_description=$desc;mac_address=$mac;hardware_id=$hid;busid=$busid;subnet=[string]$Defaults.console.subnet;gateway=[string]$Defaults.console.gateway;suggested_console_ip=[string]$Defaults.console.suggested_console_ip;dns=[string]$Defaults.console.dns}
}
function Get-FnhWslConfig{
 $l=Get-FnhLocalGatewayConfig;if([int]$l.schema -lt 2 -or !$l.PSObject.Properties['wsl'] -or !$l.wsl){throw 'WSL_GATEWAY_NOT_CONFIGURED'}
 $d=[string]$l.wsl.distro;if($d -notmatch '^[A-Za-z0-9._-]{1,80}$'){throw 'WSL_DISTRO_INVALID'}
 $u=[string]$l.wsl.usbipd.path;$us=[string]$l.wsl.usbipd.sha256;if(!(Test-Path -LiteralPath $u -PathType Leaf) -or $us -notmatch '^[A-Fa-f0-9]{64}$'){throw 'USBIPD_CONFIG_INVALID'};$u=(Resolve-Path -LiteralPath $u).Path;$ua=(Get-FileHash -LiteralPath $u -Algorithm SHA256).Hash;if($ua -ne $us){throw 'USBIPD_HASH_MISMATCH'}
 $lp=[string]$l.wsl.linuxSingBox.path;$ls=[string]$l.wsl.linuxSingBox.sha256;if($lp -notmatch '^/[A-Za-z0-9._/-]+$' -or $ls -notmatch '^[A-Fa-f0-9]{64}$'){throw 'WSL_SINGBOX_CONFIG_INVALID'}
 $mods=@($l.wsl.modules|ForEach-Object{[string]$_});foreach($m in $mods){if($m -notmatch '^[A-Za-z0-9_-]+$'){throw 'WSL_MODULE_INVALID'}}
 return [pscustomobject]@{distro=$d;usbipd=[pscustomobject]@{path=$u;sha256=$ua;version=[string]$l.wsl.usbipd.version};linuxSingBox=[pscustomobject]@{path=$lp;sha256=$ls;archiveSha256=[string]$l.wsl.linuxSingBox.archiveSha256;version=[string]$l.wsl.linuxSingBox.version};modules=$mods}
}
