$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$FreezeFiles=@(
 'app\engine.py','app\directnet.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json',
 'app\directdpi\Start-DirectDpi.ps1','app\directdpi\Stop-DirectDpi.ps1','app\directdpi\hosts.txt',
 'app\directdpi\tools\winws.exe','app\directdpi\tools\WinDivert.dll','app\directdpi\tools\WinDivert64.sys','app\directdpi\tools\cygwin1.dll',
 'app\directdns\ctrld.exe','app\directdns\ctrld.toml','app\directdns\LICENSE-ctrld.txt',
 'gateway\manifest.json','windows\standalone\FreeNetHub.exe','windows\standalone\FreeNetHubShell.cs','windows\standalone\FreeNetHubShell.manifest','windows\standalone\MANIFEST.json',
 'windows\installer\FreeNetHub.iss','windows\installer\Prepare-Upgrade.ps1','Uninstall-FreeNetHub.ps1','RELEASE.json'
)
$Freeze=@{}
foreach($rel in $FreezeFiles){$Freeze[$rel]=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash}

# Fail closed if raw Windows build-source bytes differ from the integrity
# manifest that will be installed. This prevents CRLF working-copy drift from
# producing an installer that passes packaging but cannot launch its UI.
$AppManifestPath=Join-Path $Root 'app\manifest.json'
$AppManifest=Get-Content -Raw -LiteralPath $AppManifestPath -Encoding UTF8 | ConvertFrom-Json
foreach($entry in @($AppManifest.code)){
 $rel=[string]$entry.file
 $src=Join-Path (Join-Path $Root 'app') $rel
 if(!(Test-Path -LiteralPath $src -PathType Leaf)){throw ('V435_BUILD_SOURCE_MISSING_'+$rel)}
 $actualHash=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
 $actualBytes=(Get-Item -LiteralPath $src).Length
 if($actualHash -ne [string]$entry.sha256 -or $actualBytes -ne [int64]$entry.bytes){
  throw ('V435_BUILD_SOURCE_MANIFEST_MISMATCH_'+$rel)
 }
}
$Candidates=@(
 (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
 (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
 (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
 (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe')
)
$Iscc=$Candidates|Where-Object{$_ -and (Test-Path -LiteralPath $_)}|Select-Object -First 1
if(!$Iscc){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.3.5\FreeNetHub_4.3.5_R49_Setup.exe'
New-Item -ItemType Directory -Force -Path (Split-Path $Installer -Parent)|Out-Null
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){throw ('ISCC_EXIT_'+$LASTEXITCODE)}
if(!(Test-Path -LiteralPath $Installer)){throw 'V435_INSTALLER_MISSING'}
foreach($rel in $FreezeFiles){
 $now=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash
 if($now -ne $Freeze[$rel]){throw ('V435_SOURCE_CHANGED_DURING_BUILD_'+$rel)}
}
$r=[ordered]@{
 status='PASS'
 version='4.3.5'
 revision='R49'
 path='delivery/github_v4.3.5/FreeNetHub_4.3.5_R49_Setup.exe'
 bytes=(Get-Item -LiteralPath $Installer).Length
 sha256=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
 authenticode=[string](Get-AuthenticodeSignature -LiteralPath $Installer).Status
 frozenFiles=$FreezeFiles.Count
 manifestPreflight='PASS_RAW_BYTES_MATCH_APP_MANIFEST'
 built=(Get-Date).ToUniversalTime().ToString('o')
}
$r|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $Root 'evidence\V435_R49_INSTALLER_BUILD_20261005.json') -Encoding UTF8
$r|ConvertTo-Json -Depth 4
