param(
  [ValidateSet('fresh','upgrade')][string]$Mode='upgrade',
  [switch]$PrivateGatewayReview
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$base='e4112be36d6cce97863c59a5dbe6a5d0bcdf5786'
$oldSha='34A1A45383F8E35F7D23CBD12A76440D063CE43D49E3A5CC23A3518F947353A2'
$rev53='4.3.9-r53-inno-root-guard'
$rev54='4.3.10-r54-update-cache-retention'
$guid='{BCE83A4E-8897-4D52-A650-BB67A2BB8142}_is1'
$reg="HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$guid"
$root=Split-Path $PSScriptRoot -Parent
if(-not $env:RUNNER_TEMP){throw 'DISPOSABLE_WINDOWS_GITHUB_RUNNER_REQUIRED'}
if($env:GITHUB_ACTIONS -ne 'true'){throw 'GITHUB_ACTIONS_ENV_REQUIRED'}
if(git -C $root status --porcelain){throw 'SOURCE_REPO_DIRTY'}
if((git -C $root rev-list -n 1 $base) -ne $base){throw 'BASE_COMMIT_UNAVAILABLE'}
if(Test-Path $reg){throw 'CI_APP_REGISTRY_PREEXISTS'}
$canonical=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
if(Test-Path $canonical){throw 'CI_CANONICAL_INSTALL_PREEXISTS'}
$stageName=if($PrivateGatewayReview){'fnh-r54-v481-'+$Mode}else{'fnh-r54-'+$Mode}
$work=Join-Path $env:RUNNER_TEMP ($stageName+'-worktree')
$probe=Join-Path $env:RUNNER_TEMP ($stageName+'-install')
if((Test-Path $work) -or (Test-Path $probe)){throw 'CI_STAGING_ALREADY_EXISTS'}
git -C $root worktree add --detach $work $base
if($LASTEXITCODE){throw 'WORKTREE_SETUP_FAILED'}
python (Join-Path $root 'tests\prepare_r54_isolated.py') $work
if($LASTEXITCODE){throw 'R54_SOURCE_PREP_FAILED'}
if($PrivateGatewayReview){
  python (Join-Path $root 'tests\prepare_private_gateway_review.py') $work
  if($LASTEXITCODE){throw 'V481_GATEWAY_PREP_FAILED'}
}
$stagedHelper=Join-Path $work 'windows\installer\Prepare-Upgrade.ps1'
$helperDigest='98BD0A564EA8055960D3A5B6C8CB3B5737DA391D88846F7562621B8E8DC1656C'
if((Get-FileHash -LiteralPath $stagedHelper -Algorithm SHA256).Hash -ne $helperDigest){throw 'V458_HELPER_IN_TESTED_INSTALLER_NOT_VERIFIED'}
$installScript=Join-Path $work 'windows\installer\FreeNetHub.iss'
$candidates=@(
  (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
  (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
  (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
  (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe')
)
$iscc=$candidates|Where-Object{$_ -and (Test-Path -LiteralPath $_)}|Select-Object -First 1
if(-not $iscc){
  choco install innosetup --no-progress -y
  if($LASTEXITCODE){throw 'CI_INNO_INSTALL_FAILED'}
  $iscc=$candidates|Where-Object{$_ -and (Test-Path -LiteralPath $_)}|Select-Object -First 1
}
if(-not $iscc){throw 'CI_INNO_NOT_FOUND'}
& $iscc /Qp $installScript
if($LASTEXITCODE){throw ('CI_INNO_BUILD_FAILED_'+$LASTEXITCODE)}
$installerName=if($PrivateGatewayReview){'FreeNetHub_4.3.10_R54_V481_GATEWAY_REVIEW_DO_NOT_RELEASE.exe'}else{'FreeNetHub_4.3.10_R54_Setup.exe'}
$r54=Join-Path $work ('delivery\release_candidate_v4.3.10\'+$installerName)
if(-not (Test-Path $r54)){throw 'R54_PRIVATE_BUILD_MISSING'}
$release=Get-Content -LiteralPath (Join-Path $work 'RELEASE.json') -Raw|ConvertFrom-Json
$app=Get-Content -LiteralPath (Join-Path $work 'app\manifest.json') -Raw|ConvertFrom-Json
if($release.releaseRevision -ne $rev54 -or $app.coreVersion -ne $rev54){throw 'R54_REVISION_MISMATCH'}
if($release.status -ne 'R54_UNSIGNED_WINDOWS_INSTALLER_RELEASE_LINE' -or $release.installerStatus -ne 'R54_UNSIGNED_VERSIONED_INSTALLER'){throw 'R54_RELEASE_METADATA_NOT_PROMOTABLE'}
if((Get-FileHash (Join-Path $work 'app\manifest.json') -Algorithm SHA256).Hash -ne $release.appManifestSha256){throw 'R54_MANIFEST_CHAIN_BAD'}
$info=(Get-Item $r54).VersionInfo
if($info.FileVersion.Trim() -ne '4.3.10.0'){throw 'R54_FILE_VERSION_BAD'}
function Install-Exact([string]$installer,[string]$destination) {
  $run=Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',("/DIR="+$destination)) -Wait -PassThru
  if($run.ExitCode -ne 0){throw ("INSTALL_EXIT_"+$run.ExitCode)}
}
function Verify-Installed([string]$expected){
  $out=Get-Content -LiteralPath (Join-Path $probe 'RELEASE.json') -Raw|ConvertFrom-Json
  $am=Get-Content -LiteralPath (Join-Path $probe 'app\manifest.json') -Raw|ConvertFrom-Json
  if($out.releaseRevision -ne $expected -or $am.coreVersion -ne $expected){throw ('INSTALLED_REV_BAD_'+$expected)}
  if($expected -eq $rev54 -and ($out.status -ne 'R54_UNSIGNED_WINDOWS_INSTALLER_RELEASE_LINE' -or $out.installerStatus -ne 'R54_UNSIGNED_VERSIONED_INSTALLER')){throw 'INSTALLED_RELEASE_LINE_STATUS_BAD'}
  if((Get-FileHash (Join-Path $probe 'app\manifest.json') -Algorithm SHA256).Hash -ne $out.appManifestSha256){throw 'INSTALLED_MANIFEST_DIGEST_BAD'}
  foreach($row in $am.code){
    $path=Join-Path (Join-Path $probe 'app') $row.file
    if(-not (Test-Path -LiteralPath $path)){throw ('INSTALLED_FILE_MISSING_'+$row.file)}
    if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne [string]$row.sha256){throw ('INSTALLED_FILE_SHA_BAD_'+$row.file)}
  }
  if($expected -eq $rev54 -and $PrivateGatewayReview){
    $gmanifest=Join-Path $probe 'gateway\manifest.json'
    $gsha='5D6D632EAB12C15252C4EAFCDCDF717CC327F39A9AE85E0CFE883FF43C152111'
    if((Get-FileHash $gmanifest -Algorithm SHA256).Hash -ne $gsha -or $out.gatewayManifestSha256 -ne $gsha){throw 'V481_INSTALLED_GATEWAY_MANIFEST_CHAIN_BAD'}
    $gm=Get-Content $gmanifest -Raw|ConvertFrom-Json
    if(@($gm.files).Count -ne 18){throw 'V481_GATEWAY_FILECOUNT_CHANGED'}
    foreach($e in $gm.files){
      $f=Join-Path (Join-Path $probe 'gateway') ([string]$e.file)
      if(!(Test-Path $f) -or (Get-FileHash $f -Algorithm SHA256).Hash -ne [string]$e.sha256){throw 'V481_INSTALLED_GATEWAY_SOURCE_MISMATCH'}
    }
  }
  if(-not (Test-Path -LiteralPath (Join-Path $probe 'FreeNetHub.exe'))){throw 'INSTALLED_UI_MISSING'}
  if(-not (Test-Path -LiteralPath (Join-Path $probe 'app\dependencies.json'))){throw 'INSTALLED_DEPENDENCIES_MISSING'}
  $entry=Get-ItemProperty -LiteralPath $reg -ErrorAction Stop
  if(([IO.Path]::GetFullPath($entry.InstallLocation).TrimEnd('\')) -ne ([IO.Path]::GetFullPath($probe).TrimEnd('\'))){throw 'SINGLE_INSTALL_REGISTRY_ROOT_BAD'}
  if([string]$entry.DisplayName -notmatch '^FreeNet Hub version [0-9]+(?:\.[0-9]+){1,3}$'){throw 'INNO_PRODUCT_DISPLAY_NAME_UNEXPECTED'}
  $entries=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' | ForEach-Object{Get-ItemProperty $_.PSPath} | Where-Object{$_.DisplayName -match '^FreeNet Hub version [0-9]+(?:\.[0-9]+){1,3}$'})
  if($entries.Count -ne 1){throw ('DUPLICATE_INSTALL_REGISTRATION_'+$entries.Count)}
  if(Test-Path $canonical){throw 'DUPLICATE_CANONICAL_INSTALL'}
}
if($Mode -eq 'upgrade'){
  $r53=Join-Path $env:RUNNER_TEMP 'FreeNetHub_4.3.9_R53_Setup.exe'
  $url='https://github.com/GOD13emad/FreeNetHub/releases/download/v4.3.9-r53-windows-stable/FreeNetHub_4.3.9_R53_Setup.exe'
  & curl.exe -fL --retry 2 --connect-timeout 12 --max-time 120 -o $r53 $url
  if($LASTEXITCODE){throw 'R53_PUBLIC_FETCH_FAILED'}
  if((Get-FileHash $r53 -Algorithm SHA256).Hash -ne $oldSha){throw 'R53_PUBLIC_PINNED_SHA_MISMATCH'}
  Install-Exact $r53 $probe
  Verify-Installed $rev53
  $fixture=Join-Path $probe 'data\owner-preservation-probe.txt'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $fixture)|Out-Null
  [IO.File]::WriteAllText($fixture,'r54-owner-profile-keep')
  $settings=Join-Path $probe 'settings.json'
  [IO.File]::WriteAllText($settings,'{"userProvided":"keep","proxy":"unchanged"}')
  Install-Exact $r54 $probe
  Verify-Installed $rev54
  if([IO.File]::ReadAllText($fixture) -ne 'r54-owner-profile-keep'){throw 'R54_LOST_USER_DATA'}
  if([IO.File]::ReadAllText($settings) -ne '{"userProvided":"keep","proxy":"unchanged"}'){throw 'R54_LOST_SETTINGS'}
  Install-Exact $r53 $probe
  Verify-Installed $rev53
  if([IO.File]::ReadAllText($fixture) -ne 'r54-owner-profile-keep' -or [IO.File]::ReadAllText($settings) -ne '{"userProvided":"keep","proxy":"unchanged"}'){throw 'ROLLBACK_LOST_PROFILE'}
  Write-Output 'R53_TO_R54_INPLACE_UPDATE_AND_R53_EXPLICIT_ROLLBACK_PROFILE_PASS'
  if($PrivateGatewayReview){
    # The SAME exact compiled binary must pass fresh and upgrade/rollback,
    # not two similar binaries built separately on different runners.
    $uninstaller=Join-Path $probe 'unins000.exe'
    if(!(Test-Path -LiteralPath $uninstaller)){throw 'PRIVATE_CI_R53_UNINSTALLER_MISSING'}
    $un=Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
    if($un.ExitCode -ne 0){throw ('PRIVATE_CI_R53_UNINSTALL_FAILED_'+$un.ExitCode)}
    if(Test-Path -LiteralPath $reg){throw 'PRIVATE_CI_R53_REGISTRY_RESIDUE'}
    $safeRoot=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')+'\'
    $safePath=[IO.Path]::GetFullPath($probe)
    if(!$safePath.StartsWith($safeRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'PRIVATE_CI_PROBE_NOT_UNDER_RUNNER_TEMP'}
    if(Test-Path -LiteralPath $probe){Remove-Item -LiteralPath $probe -Recurse -Force}
    Install-Exact $r54 $probe
    Verify-Installed $rev54
    Write-Output 'V481_EXACT_SAME_BINARY_R53_UPGRADE_ROLLBACK_AND_FRESH_PASS'
  }
}else{
  Install-Exact $r54 $probe
  Verify-Installed $rev54
  Write-Output 'R54_FRESH_INSTALL_SINGLE_REGISTRY_ENTRY_PASS'
}
$receipt=[ordered]@{
  status='PASS';mode=$Mode;sourceBase=$base;releaseRevision=$rev54
  r54InstallerBytes=(Get-Item $r54).Length
  r54InstallerSha256=(Get-FileHash $r54 -Algorithm SHA256).Hash
  gatewayReview=[bool]$PrivateGatewayReview
  sameExactBinaryFreshAndRollbackValidated=([bool]$PrivateGatewayReview -and $Mode -eq 'upgrade')
  gatewayManifestSHA256=if($PrivateGatewayReview){'5D6D632EAB12C15252C4EAFCDCDF717CC327F39A9AE85E0CFE883FF43C152111'}else{$null}
  reviewInstallerName=$installerName
  testedInstallerHelperSha256=$helperDigest
  officialR53PinnedHash=$oldSha
  physicalHost='GitHub hosted isolated Windows runner'
  updatedOwnerMachine=$false;scopedVPNMutation=$false
}
$receiptName=if($PrivateGatewayReview){'v481-'+$Mode+'-receipt.json'}else{'r54-'+$Mode+'-receipt.json'}
$receipt|ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $env:RUNNER_TEMP $receiptName) -Encoding utf8
$receipt|ConvertTo-Json -Depth 4
