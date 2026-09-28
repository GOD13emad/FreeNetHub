$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R23_StrictCountry_ShadowHub_Setup.exe'
$p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
Write-Output ('INSTALL_EXIT='+$p.ExitCode)
if($p.ExitCode -ne 0){exit $p.ExitCode}
