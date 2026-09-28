$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$Iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if(!(Test-Path -LiteralPath $Iscc)){throw 'ISCC_NOT_FOUND'}
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R22_Country_ShadowHub_Setup.exe'
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
& $Iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
$Code=$LASTEXITCODE
Write-Output ('BUILD_EXIT='+$Code)
if($Code -ne 0){exit $Code}
if(!(Test-Path -LiteralPath $Installer)){throw 'R22_INSTALLER_MISSING'}
Write-Output ('BUILD_BYTES='+(Get-Item -LiteralPath $Installer).Length)
Write-Output ('BUILD_SHA256='+(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)
exit 0
