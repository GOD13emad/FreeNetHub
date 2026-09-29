$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$FreezeFiles=@(
 'app\engine.py','app\directnet.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json',
 'app\directdpi\Start-DirectDpi.ps1','app\directdpi\Stop-DirectDpi.ps1','app\directdpi\hosts.txt',
 'app\directdpi\tools\winws.exe','app\directdpi\tools\WinDivert.dll','app\directdpi\tools\WinDivert64.sys','app\directdpi\tools\cygwin1.dll',
 'app\directdns\ctrld.exe','app\directdns\ctrld.toml','app\directdns\LICENSE-ctrld.txt',
 'gateway\manifest.json','windows\installer\FreeNetHub.iss','Uninstall-FreeNetHub.ps1','RELEASE.json'
)
$Freeze=@{}
foreach($rel in $FreezeFiles){$Freeze[$rel]=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash}
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R38_DirectMethod_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){throw ('ISCC_EXIT_'+$LASTEXITCODE)}
if(!(Test-Path -LiteralPath $Installer)){throw 'R38_INSTALLER_MISSING'}
foreach($rel in $FreezeFiles){
 $now=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash
 if($now -ne $Freeze[$rel]){throw ('R38_SOURCE_CHANGED_DURING_BUILD_'+$rel)}
}
$r=[ordered]@{
 status='PASS'
 path='delivery/github_v4.2.0/FreeNetHub_4.2.0_R38_DirectMethod_Setup.exe'
 bytes=(Get-Item -LiteralPath $Installer).Length
 sha256=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
 authenticode=[string](Get-AuthenticodeSignature -LiteralPath $Installer).Status
 frozenFiles=$FreezeFiles.Count
 built=(Get-Date).ToString('o')
}
$r|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $Root 'evidence\R38_INSTALLER_BUILD_20260929.json') -Encoding UTF8
$r|ConvertTo-Json -Depth 4
