[CmdletBinding()]
param(
  [string]$WarpPlus,
  [string]$TorExe,
  [string]$Lyrebird,
  [string]$TorRc,
  [string]$OldRoot,
  [string]$Chrome,
  [string]$Pythonw,
  [string]$Pwsh
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=$PSScriptRoot
function First-Existing([object[]]$Candidates){
  foreach($x in $Candidates){ if($x -and (Test-Path -LiteralPath ([string]$x) -PathType Leaf)){ return (Resolve-Path -LiteralPath ([string]$x)).Path } }
  return $null
}
function Require-File([string]$Name,[string]$Path){
  if(-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)){ throw "$Name not found. Supply it explicitly." }
  return (Resolve-Path -LiteralPath $Path).Path
}
$lab=Join-Path $env:LOCALAPPDATA 'FreeTunnelLab'
if(-not $WarpPlus){$WarpPlus=First-Existing @((Join-Path $lab 'WarpPlusFast\warp-plus.exe'))}
if(-not $TorExe){$TorExe=First-Existing @((Join-Path $lab 'TorSnowflake\bundle\tor\tor.exe'))}
if(-not $Lyrebird){$Lyrebird=First-Existing @((Join-Path $lab 'TorSnowflake\bundle\tor\pluggable_transports\lyrebird.exe'))}
if(-not $TorRc){$TorRc=First-Existing @((Join-Path $lab 'TorSnowflake\torrc'))}
if(-not $OldRoot -and (Test-Path -LiteralPath $lab -PathType Container)){$OldRoot=(Resolve-Path -LiteralPath $lab).Path}
if(-not $Chrome){$Chrome=First-Existing @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",(Get-Command chrome.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue))}
if(-not $Pythonw){$Pythonw=First-Existing @((Get-Command pythonw.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue))}
if(-not $Pwsh){$Pwsh=First-Existing @("$env:ProgramFiles\PowerShell\7\pwsh.exe",(Get-Command pwsh.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue))}
$WarpPlus=Require-File 'warp-plus.exe' $WarpPlus
$TorExe=Require-File 'tor.exe' $TorExe
$Lyrebird=Require-File 'lyrebird.exe' $Lyrebird
$TorRc=Require-File 'torrc' $TorRc
$Chrome=Require-File 'Chrome' $Chrome
$Pythonw=Require-File 'pythonw.exe' $Pythonw
$Pwsh=Require-File 'pwsh.exe' $Pwsh
if(-not $OldRoot -or -not (Test-Path -LiteralPath $OldRoot -PathType Container)){throw 'Provider root (OldRoot) not found. Supply -OldRoot.'}
$OldRoot=(Resolve-Path -LiteralPath $OldRoot).Path
$d=[ordered]@{
 pythonw=$Pythonw
 lyrebird=[ordered]@{path=$Lyrebird;sha256=(Get-FileHash -LiteralPath $Lyrebird -Algorithm SHA256).Hash}
 torrc=$TorRc
 pwsh=$Pwsh
 oldRoot=$OldRoot
 chrome=$Chrome
 warp=[ordered]@{path=$WarpPlus;sha256=(Get-FileHash -LiteralPath $WarpPlus -Algorithm SHA256).Hash}
 tor=[ordered]@{path=$TorExe;sha256=(Get-FileHash -LiteralPath $TorExe -Algorithm SHA256).Hash}
}
$out=Join-Path $Root 'app\dependencies.json'
$d|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Created runtime-local dependency configuration: $out"
Write-Host 'This file is intentionally excluded from Git.'
