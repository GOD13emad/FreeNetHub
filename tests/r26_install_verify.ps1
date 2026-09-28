$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Out=Join-Path $Root 'delivery\prestate_r26_20260928'
New-Item -ItemType Directory -Force -Path $Out|Out-Null
$settings=Join-Path $Install 'settings.json';$nodes=Join-Path $Install 'data\nodes.json'
$rec=[ordered]@{settings=$null;nodes=$null}
if(Test-Path $settings){Copy-Item $settings (Join-Path $Out 'settings.json') -Force;$rec.settings=(Get-FileHash $settings -Algorithm SHA256).Hash}
if(Test-Path $nodes){Copy-Item $nodes (Join-Path $Out 'nodes.json') -Force;$rec.nodes=(Get-FileHash $nodes -Algorithm SHA256).Hash}
$rec|ConvertTo-Json|Set-Content (Join-Path $Out 'prestate.json') -Encoding utf8
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R26_HY2_StrictCountry_Final_Setup.exe'
if((Get-FileHash $Installer -Algorithm SHA256).Hash -ne '22A072EDDCF1F24445AC2EFEC1FA6F3E64444C944A2F5DEF3BCA5927C422328F'){throw 'INSTALLER_HASH_MISMATCH'}
$p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($p.ExitCode -ne 0){throw ('INSTALL_EXIT_'+$p.ExitCode)}
Start-Sleep -Milliseconds 800
foreach($n in @('engine.py','nodehub.py','manifest.json')){
 $src=(Get-FileHash (Join-Path $Root ('app\'+$n)) -Algorithm SHA256).Hash
 $ins=(Get-FileHash (Join-Path $Install ('app\'+$n)) -Algorithm SHA256).Hash
 if($src -ne $ins){throw ('PARITY_'+$n)}
}
if($rec.settings -and (Get-FileHash $settings -Algorithm SHA256).Hash -ne $rec.settings){throw 'SETTINGS_NOT_PRESERVED'}
if($rec.nodes -and (Get-FileHash $nodes -Algorithm SHA256).Hash -ne $rec.nodes){throw 'NODES_NOT_PRESERVED'}
[pscustomobject]@{status='PASS';installerSha256='22A072EDDCF1F24445AC2EFEC1FA6F3E64444C944A2F5DEF3BCA5927C422328F';engine=(Get-FileHash (Join-Path $Install 'app\engine.py') -Algorithm SHA256).Hash;nodehub=(Get-FileHash (Join-Path $Install 'app\nodehub.py') -Algorithm SHA256).Hash;settingsSha=$rec.settings;nodesSha=$rec.nodes}|ConvertTo-Json -Compress
