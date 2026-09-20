[CmdletBinding()]
param(
  [string]$WarpPlus,[string]$TorExe,[string]$Lyrebird,[string]$TorRc,[string]$OldRoot,
  [string]$Chrome,[string]$Pythonw,[string]$Pwsh,[switch]$SkipUnitTests
)
$ErrorActionPreference='Stop'
$Root=$PSScriptRoot
$dep=Join-Path $Root 'app\dependencies.json'
if(-not (Test-Path -LiteralPath $dep)){
  $args=@{}
  foreach($n in 'WarpPlus','TorExe','Lyrebird','TorRc','OldRoot','Chrome','Pythonw','Pwsh'){
    $v=Get-Variable -Name $n -ValueOnly
    if($v){$args[$n]=$v}
  }
  & (Join-Path $Root 'Setup-WindowsDependencies.ps1') @args
}
if(-not $SkipUnitTests){
  $pythonwPath=(Get-Content -LiteralPath $dep -Raw -Encoding UTF8|ConvertFrom-Json).pythonw
  $pythonExe=Join-Path (Split-Path $pythonwPath -Parent) 'python.exe'
  if(-not (Test-Path -LiteralPath $pythonExe)){throw 'python.exe not found next to pythonw.exe.'}
  & $pythonExe (Join-Path $Root 'tests\test_engine.py')
  if($LASTEXITCODE -ne 0){throw 'Unit tests failed; install aborted.'}
}
& (Join-Path $Root 'windows\standalone\Install-FreeNetHubShell.ps1') -Root $Root
Write-Host 'FreeNet Hub installed. Open it from Start Menu: FreeNet Hub'
