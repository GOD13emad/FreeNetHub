$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$p=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R25_CountryAvailability_ShadowShare_HY2_Setup.exe'
$x=Start-Process -FilePath $p -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
Write-Output ('INSTALL_EXIT='+$x.ExitCode)
if($x.ExitCode -ne 0){exit $x.ExitCode}
