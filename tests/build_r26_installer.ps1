$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
python tests\build_r26_metadata.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
pwsh.exe -NoProfile -File .\tests\verify_r24_clean.ps1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R26_HY2_StrictCountry_Final_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Write-Output ('R26_SHA256='+(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)
Write-Output ('R26_BYTES='+(Get-Item -LiteralPath $Installer).Length)
Write-Output 'R26_BUILD=PASS'
