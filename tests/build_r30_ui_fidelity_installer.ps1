$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
python tests\build_r30_ui_fidelity_metadata.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
pwsh.exe -NoProfile -File .\tests\verify_r28_static.ps1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$FreezeFiles=@('app\engine.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json','RELEASE.json','gateway\manifest.json','windows\standalone\FreeNetHub.exe','windows\installer\FreeNetHub.iss','Uninstall-FreeNetHub.ps1')
$Freeze=@{}
foreach($rel in $FreezeFiles){$Freeze[$rel]=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash}
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R30_UIFidelity_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
if(!(Test-Path -LiteralPath $Installer)){throw 'R30_INSTALLER_MISSING'}
foreach($rel in $FreezeFiles){$now=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash;if($now -ne $Freeze[$rel]){throw ('R30_SOURCE_CHANGED_DURING_BUILD_'+$rel)}}
Write-Output 'R30_SOURCE_FREEZE=PASS'
Write-Output ('R30_SHA256='+(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)
Write-Output ('R30_BYTES='+(Get-Item -LiteralPath $Installer).Length)
Write-Output ('R30_AUTH='+(Get-AuthenticodeSignature -LiteralPath $Installer).Status)
Write-Output 'R30_BUILD=PASS'
