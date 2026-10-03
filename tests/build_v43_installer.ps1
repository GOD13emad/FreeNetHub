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
$Candidates=@(
 (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
 (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
 (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
 (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe')
)
$Iscc=$Candidates|Where-Object{$_ -and (Test-Path -LiteralPath $_)}|Select-Object -First 1
if(!$Iscc){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.3.0\FreeNetHub_4.3.0_R43_Setup.exe'
New-Item -ItemType Directory -Force -Path (Split-Path $Installer -Parent)|Out-Null
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){throw ('ISCC_EXIT_'+$LASTEXITCODE)}
if(!(Test-Path -LiteralPath $Installer)){throw 'V43_INSTALLER_MISSING'}
foreach($rel in $FreezeFiles){
 $now=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash
 if($now -ne $Freeze[$rel]){throw ('V43_SOURCE_CHANGED_DURING_BUILD_'+$rel)}
}
$r=[ordered]@{
 status='PASS'
 version='4.3.0'
 revision='R43'
 path='delivery/github_v4.3.0/FreeNetHub_4.3.0_R43_Setup.exe'
 bytes=(Get-Item -LiteralPath $Installer).Length
 sha256=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
 authenticode=[string](Get-AuthenticodeSignature -LiteralPath $Installer).Status
 frozenFiles=$FreezeFiles.Count
 built=(Get-Date).ToUniversalTime().ToString('o')
}
$r|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $Root 'evidence\V43_INSTALLER_BUILD_20261003.json') -Encoding UTF8
$r|ConvertTo-Json -Depth 4
