$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
python tests\build_r23_countryfix_metadata.py
python tests\test_country_policy.py
python -m unittest discover -s tests -p 'test_*.py'
python -m unittest discover -s gateway\tests -p 'test_*.py'
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R23_StrictCountry_ShadowHub_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
if(!(Test-Path -LiteralPath $Installer)){throw 'R23_INSTALLER_MISSING'}
Write-Output ('R23_SHA256='+(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)
Write-Output ('R23_BYTES='+(Get-Item -LiteralPath $Installer).Length)
Write-Output 'R23_BUILD=PASS'
