[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][string]$Backup)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
$Root=(Resolve-Path -LiteralPath $Root).Path; $Backup=(Resolve-Path -LiteralPath $Backup).Path
$exe=Join-Path $Root 'FreeNetHub.exe'; $lnk=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FreeNet Hub.lnk'
Get-Process FreeNetHub -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
foreach($name in @('FreeNetHub.exe','FreeNetHub.ico','SHELL_HOST_STATUS.json')){
  $src=Join-Path $Backup $name; $dst=Join-Path $Root $name
  if(Test-Path -LiteralPath $src){ Copy-Item -LiteralPath $src -Destination $dst -Force } elseif(Test-Path -LiteralPath $dst){ Remove-Item -LiteralPath $dst -Force }
}
$old=Join-Path $Backup 'FreeNet Hub.lnk'
if(Test-Path -LiteralPath $old){ Copy-Item -LiteralPath $old -Destination $lnk -Force } elseif(Test-Path -LiteralPath $lnk){ Remove-Item -LiteralPath $lnk -Force }
Write-Host 'Rollback complete.'
