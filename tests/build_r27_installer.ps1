$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
python tests\build_r27_metadata.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
pwsh.exe -NoProfile -File .\tests\verify_r24_strict.ps1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R27_Country_ShadowShare_Final_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
if(!(Test-Path -LiteralPath $Installer)){throw 'R27_INSTALLER_MISSING'}
Write-Output ('R27_SHA256='+(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)
Write-Output ('R27_BYTES='+(Get-Item -LiteralPath $Installer).Length)
Write-Output ('R27_AUTH='+(Get-AuthenticodeSignature -LiteralPath $Installer).Status)
Write-Output 'R27_BUILD=PASS'
