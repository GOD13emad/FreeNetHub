$ErrorActionPreference='Stop'
$Project=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Installer=Join-Path $Project 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R27_Country_ShadowShare_Final_Setup.exe'
$Expected='151444A7694D4BB9F3774B0767029F6F4AC8F8ECC2E0A858BED0C2A83D238996'
$Pre=Join-Path $Project 'delivery\prestate_r27_20260928'
New-Item -ItemType Directory -Force -Path $Pre|Out-Null
$settings=Join-Path $Install 'settings.json';$nodes=Join-Path $Install 'data\nodes.json'
$projectPorts=@(19410,19413,19414,19450,19452,19453,19460,19591,19594)
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$projectPorts -contains $_.LocalPort})
if($listeners.Count){throw 'PROJECT_NETWORK_NOT_AT_REST'}
$rec=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');installerSha256=(Get-FileHash $Installer -Algorithm SHA256).Hash;settings=$null;nodes=$null}
if($rec.installerSha256 -ne $Expected){throw 'INSTALLER_HASH_MISMATCH'}
if(Test-Path $settings){Copy-Item $settings (Join-Path $Pre 'settings.json') -Force;$rec.settings=(Get-FileHash $settings -Algorithm SHA256).Hash}
if(Test-Path $nodes){Copy-Item $nodes (Join-Path $Pre 'nodes.json') -Force;$rec.nodes=(Get-FileHash $nodes -Algorithm SHA256).Hash}
$rec|ConvertTo-Json -Depth 5|Set-Content (Join-Path $Pre 'prestate.json') -Encoding utf8
$p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($p.ExitCode -ne 0){throw ('INSTALL_EXIT_'+$p.ExitCode)}
Start-Sleep -Milliseconds 800
$parity=[ordered]@{}
foreach($n in @('engine.py','nodehub.py','FreeNetHub.ps1','View.xaml','manifest.json')){
 $src=(Get-FileHash (Join-Path $Project ('app\'+$n)) -Algorithm SHA256).Hash
 $ins=(Get-FileHash (Join-Path $Install ('app\'+$n)) -Algorithm SHA256).Hash
 $parity[$n]=($src -eq $ins)
 if($src -ne $ins){throw ('PARITY_'+$n)}
}
if($rec.settings -and (Get-FileHash $settings -Algorithm SHA256).Hash -ne $rec.settings){throw 'SETTINGS_NOT_PRESERVED'}
if($rec.nodes -and (Get-FileHash $nodes -Algorithm SHA256).Hash -ne $rec.nodes){throw 'NODES_NOT_PRESERVED'}
$out=[ordered]@{schema=1;date='2026-09-28';status='PASS';installerSha256=$Expected;installExit=$p.ExitCode;parity=$parity;settingsPreserved=[bool]$rec.settings;nodesPreserved=[bool]$rec.nodes;engineSha256=(Get-FileHash (Join-Path $Install 'app\engine.py') -Algorithm SHA256).Hash;nodeHubSha256=(Get-FileHash (Join-Path $Install 'app\nodehub.py') -Algorithm SHA256).Hash;manifestSha256=(Get-FileHash (Join-Path $Install 'app\manifest.json') -Algorithm SHA256).Hash}
$out|ConvertTo-Json -Depth 8|Set-Content (Join-Path $Project 'evidence\R27_INSTALL_ACCEPTANCE_20260928.json') -Encoding utf8
$out|ConvertTo-Json -Depth 8
