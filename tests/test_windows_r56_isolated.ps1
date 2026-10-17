[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$StageRoot,
  [Parameter(Mandatory=$true)][string]$ExpectedSourceSha
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

function Require([bool]$condition,[string]$code){
  if(-not $condition){throw $code}
}
function Read-Json([string]$path){
  Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
}
function Digest([string]$path){
  (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
function UserProxySnapshot {
  $reg=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction Stop
  $result=[ordered]@{}
  foreach($k in @('AutoConfigURL','ProxyEnable')){
    $found=$reg.PSObject.Properties[$k]
    $result[$k]=if($null -ne $found) {@{present=$true; value=$found.Value}}else{@{present=$false}}
  }
  $result | ConvertTo-Json -Depth 5 -Compress
}
function AssertNoSelectiveListener{
  $connections=@(Get-NetTCPConnection -State Listen -LocalPort @(19416,19417) -ErrorAction SilentlyContinue)
  Require ($connections.Count -eq 0) 'R56_UNEXPECTED_LIVE_PAC_OR_CONNECT_BRIDGE'
}
function Install([string]$installer,[string]$folder){
  Require (!(Test-Path -LiteralPath $folder)) 'R56_TARGET_PREEXISTS'
  $p=Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',("/DIR="+$folder)) -Wait -PassThru
  Require ($p.ExitCode -eq 0) ('R56_INSTALL_FAILED_'+$p.ExitCode)
}
function Upgrade([string]$installer,[string]$folder){
  $p=Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',("/DIR="+$folder)) -Wait -PassThru
  Require ($p.ExitCode -eq 0) ('R56_UPGRADE_OR_ROLLBACK_FAILED_'+$p.ExitCode)
}
function AssertVersion([string]$folder,[string]$version,[string]$revision){
  $release=Read-Json (Join-Path $folder 'RELEASE.json')
  $manifest=Read-Json (Join-Path $folder 'app\manifest.json')
  Require ($release.version -eq $version -and $manifest.version -eq $version) 'R56_VERSION_NOT_INSTALLED'
  Require ($release.releaseRevision -eq $revision -and $manifest.coreVersion -eq $revision) 'R56_CORE_REVISION_NOT_INSTALLED'
  foreach($row in @($manifest.code)){
    $target=Join-Path (Join-Path $folder 'app') ([string]$row.file)
    Require (Test-Path -LiteralPath $target -PathType Leaf) ('R56_CODE_MISSING_'+$row.file)
    Require ((Digest $target) -eq [string]$row.sha256) ('R56_CODE_SHA_MISMATCH_'+$row.file)
  }
  if($revision -match 'r56'){
    foreach($file in @('selective_http_bridge.py','selective_route_windows.py')){
      Require (Test-Path -LiteralPath (Join-Path $folder ('app\'+$file))) ('R56_SELECTIVE_MODULE_MISSING_'+$file)
    }
  }
}
function SmokeUI([string]$folder){
  $launcherPath=Join-Path $folder 'FreeNetHub.exe'
  $ui=Join-Path $folder 'app\FreeNetHub.ps1'
  Require (Test-Path -LiteralPath $launcherPath) 'R56_SHELL_MISSING'
  $launcher=$null
  $children=@()
  try {
    $launcher=Start-Process -FilePath $launcherPath -ArgumentList @('"' + $ui + '"') -PassThru
    Start-Sleep -Seconds 6
    Require (!$launcher.HasExited) ('R56_UI_EXITED_'+$launcher.ExitCode)
    $children=@(Get-CimInstance Win32_Process -ErrorAction Stop |
      Where-Object {$_.ParentProcessId -eq $launcher.Id -and $_.Name -ieq 'pwsh.exe'})
    Require ($children.Count -ge 1) 'R56_WPF_CHILD_NOT_RUNNING'
    $errorFile=Join-Path $folder 'logs\ui-error.txt'
    Require (!(Test-Path -LiteralPath $errorFile)) 'R56_WPF_RUNTIME_ERROR_LOGGED'
    AssertNoSelectiveListener
    Write-Output 'R56_INSTALLED_UI_SMOKE_AND_DEFAULT_NO_TUNNEL_PASS'
  }finally{
    foreach($child in $children){Stop-Process -Id ([int]$child.ProcessId) -Force -ErrorAction SilentlyContinue}
    if($null -ne $launcher){Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue}
    Start-Sleep -Milliseconds 300
  }
}

$source=Read-Json (Join-Path $StageRoot 'R56_ISOLATED_BUILD_SOURCE.json')
Require ($source.sourceSHA -eq $ExpectedSourceSha) 'R56_SOURCE_SHA_UNVERIFIED'
Require ($source.version -eq '4.3.12') 'R56_STAGE_VERSION_UNEXPECTED'
$installer=Join-Path $StageRoot 'delivery\release_candidate_v4.3.12\FreeNetHub_4.3.12_R56_SELECTIVE_Setup.exe'
Require (Test-Path -LiteralPath $installer -PathType Leaf) 'R56_INSTALLER_FILE_MISSING'
$sha=Digest $installer
Require ($sha.Length -eq 64) 'R56_INSTALLER_DIGEST_MISSING'
$baseline=UserProxySnapshot
AssertNoSelectiveListener
$fresh=Join-Path $env:RUNNER_TEMP 'fnh-r56-selective-fresh'
$upgrade=Join-Path $env:RUNNER_TEMP 'fnh-r56-selective-upgrade'

Install $installer $fresh
AssertVersion $fresh '4.3.12' '4.3.12-r56-google-403-selective-routing'
Require ((UserProxySnapshot) -eq $baseline) 'R56_FRESH_INSTALL_MUTATED_USER_PROXY'
SmokeUI $fresh
Require ((UserProxySnapshot) -eq $baseline) 'R56_UI_LAUNCH_MUTATED_USER_PROXY'
Write-Output ('R56_FRESH_INSTALL_EXACT_SHA_PASS '+$sha)

# Same AppId only supports one registered root. Retire the disposable fresh
# instance through its actual uninstaller before preparing the upgrade trial.
$uninstall=Join-Path $fresh 'unins000.exe'
Require (Test-Path -LiteralPath $uninstall) 'R56_FRESH_UNINSTALLER_MISSING'
$un=Start-Process -FilePath $uninstall -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
Require ($un.ExitCode -eq 0) ('R56_TEST_FRESH_UNINSTALL_FAILED_'+$un.ExitCode)
Require (!(Test-Path -LiteralPath (Join-Path $fresh 'RELEASE.json'))) 'R56_FRESH_UNINSTALL_NOT_RETIRED'
AssertNoSelectiveListener

$old=Join-Path $env:RUNNER_TEMP 'FreeNetHub_4.3.9_R53_PINNED_Setup.exe'
Require (!(Test-Path -LiteralPath $old)) 'R56_PRIOR_R53_FILE_PREEXISTS'
$oldUrl='https://github.com/GOD13emad/FreeNetHub/releases/download/v4.3.9-r53-windows-stable/FreeNetHub_4.3.9_R53_Setup.exe'
& curl.exe -fL --retry 2 --connect-timeout 12 --max-time 120 -o $old $oldUrl
Require ($LASTEXITCODE -eq 0) 'R56_PUBLIC_R53_DOWNLOAD_FAILED'
Require ((Digest $old) -eq '34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2') 'R56_PUBLIC_R53_SHA_BAD'
Install $old $upgrade
AssertVersion $upgrade '4.3.9' '4.3.9-r53-inno-root-guard'
[IO.Directory]::CreateDirectory((Join-Path $upgrade 'data'))|Out-Null
$settingsFile=Join-Path $upgrade 'settings.json'
$nodesFile=Join-Path $upgrade 'data\nodes.json'
[IO.File]::WriteAllText($settingsFile,'{"schema":1,"country":"AUTO","home":"https://example.com/","monitor":false}',[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($nodesFile,'{"schema":1,"selected":"","nodes":[]}',[Text.UTF8Encoding]::new($false))
$settingsSHA=Digest $settingsFile
$nodesSHA=Digest $nodesFile

Upgrade $installer $upgrade
AssertVersion $upgrade '4.3.12' '4.3.12-r56-google-403-selective-routing'
Require ((Digest $settingsFile) -eq $settingsSHA -and (Digest $nodesFile) -eq $nodesSHA) 'R56_UPGRADE_DID_NOT_PRESERVE_PRIVATE_STATE'
Require ((UserProxySnapshot) -eq $baseline) 'R56_UPGRADE_CHANGED_SYSTEM_PROXY'
AssertNoSelectiveListener
Write-Output 'R53_TO_R56_UPGRADE_PRIVATE_SETTINGS_AND_NO_AUTO_TUNNEL_PASS'

# Explicit controlled rollback of the one exact candidate through the
# independently SHA256-pinned public R53, no user machine involved.
Upgrade $old $upgrade
AssertVersion $upgrade '4.3.9' '4.3.9-r53-inno-root-guard'
Require ((Digest $settingsFile) -eq $settingsSHA -and (Digest $nodesFile) -eq $nodesSHA) 'R56_EXPLICIT_ROLLBACK_LOST_PRIVATE_DATA'
Require ((UserProxySnapshot) -eq $baseline) 'R56_ROLLBACK_CHANGED_SYSTEM_PROXY'
AssertNoSelectiveListener
Write-Output 'R56_TO_PINNED_R53_EXPLICIT_ROLLBACK_PASS'

$receipt=[ordered]@{
  schema=1
  status='CI_SOURCE_AND_DISPOSABLE_INSTALL_ACCEPTED_NOT_RELEASED'
  sourceSHA=$ExpectedSourceSha
  r56InstallerSha256=$sha
  r56InstallerBytes=(Get-Item -LiteralPath $installer).Length
  r53InstallerSha256=(Digest $old)
  sourceVersion=$source.version
  codeHashValidation='PASS_FRESH_UPGRADE_ROLLBACK'
  freshUiLaunch='PASS'
  versionedUpgrade='PASS'
  exactRollback='PASS'
  settingsPreserved=$true
  nodeFixturePreserved=$true
  systemProxyUnchanged=$true
  noAutoListener=$true
  released=$false
  ownerFieldAccepted=$false
  publisherSigned=$false
}
$receipt|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $env:RUNNER_TEMP 'R56_TESTED_RECEIPT.json') -Encoding utf8
Write-Output ('R56_CI_SOURCE_DISPOSABLE_TEST_PASS_SHA256='+$sha)
