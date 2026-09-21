[CmdletBinding()]
param(
 [switch]$SkipUnitTests,
 [switch]$ConfigureConsoleGateway,
 [switch]$InstallMissingRuntime
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=(Resolve-Path $PSScriptRoot).Path
function Assert-StaticIntegrity{
 $am=Get-Content (Join-Path $Root 'app\manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
 foreach($f in $am.code){
  $p=Join-Path (Join-Path $Root 'app') ([string]$f.file)
  if(!(Test-Path $p -PathType Leaf) -or (Get-Item $p).Length -ne [long]$f.bytes -or (Get-FileHash $p -Algorithm SHA256).Hash -ne [string]$f.sha256){throw ('APP_INTEGRITY_FAIL_'+$f.file)}
 }
 $gm=Get-Content (Join-Path $Root 'gateway\manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
 foreach($f in $gm.files){
  $p=Join-Path (Join-Path $Root 'gateway') ([string]$f.file)
  if(!(Test-Path $p -PathType Leaf) -or (Get-Item $p).Length -ne [long]$f.bytes -or (Get-FileHash $p -Algorithm SHA256).Hash -ne [string]$f.sha256){throw ('GATEWAY_INTEGRITY_FAIL_'+$f.file)}
 }
}
Assert-StaticIntegrity
$setup=Join-Path $Root 'Setup-WindowsDependencies.ps1'
$pwsh=(Get-Command pwsh.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
if(!$pwsh -or !(Test-Path -LiteralPath $pwsh -PathType Leaf)){throw 'POWERSHELL7_PWSH_REQUIRED'}
$args=@('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$setup)
if($InstallMissingRuntime){$args+='-InstallMissingRuntime'}
$p=Start-Process -FilePath $pwsh -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
if($p.ExitCode -ne 0){throw ('RUNTIME_SETUP_FAIL_'+$p.ExitCode)}
$deps=Get-Content (Join-Path $Root 'app\dependencies.json') -Raw -Encoding UTF8|ConvertFrom-Json
$python=Join-Path (Split-Path ([string]$deps.pythonw) -Parent) 'python.exe'
if(!(Test-Path $python -PathType Leaf)){throw 'PYTHON_RUNTIME_MISSING'}
if(!$SkipUnitTests){
 & $python (Join-Path $Root 'tests\test_engine.py')
 if($LASTEXITCODE -ne 0){throw 'ENGINE_UNIT_TESTS_FAILED'}
 & $python (Join-Path $Root 'gateway\tests\test_gateway.py')
 if($LASTEXITCODE -ne 0){throw 'GATEWAY_UNIT_TESTS_FAILED'}
}
& (Join-Path $Root 'windows\standalone\Install-FreeNetHubShell.ps1') -Root $Root
if($LASTEXITCODE -ne 0){throw 'SHELL_INSTALL_FAILED'}
if($ConfigureConsoleGateway){
 $pw=[string]$deps.pwsh
 $cs=Join-Path $Root 'gateway\Setup-ConsoleGateway.ps1'
 $cr=Join-Path $Root 'gateway\runtime\install-console-setup.json'
 $ep=Start-Process -FilePath $pw -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$cs,'-InstallPrerequisites','-ResultPath',$cr) -Verb RunAs -Wait -PassThru
 if($ep.ExitCode -ne 0){throw ('CONSOLE_SETUP_FAILED_'+$ep.ExitCode)}
}
[pscustomobject]@{
 product='FreeNet Hub';version='4.2.0';status='PASS';root=$Root
 dependencies=(Join-Path $Root 'app\dependencies.json')
 shell=(Join-Path $Root 'FreeNetHub.exe')
 consoleConfigured=(Test-Path (Join-Path $Root 'gateway\runtime\local_gateway.json'))
 networkChangedByInstall=$false
}|ConvertTo-Json -Depth 6
