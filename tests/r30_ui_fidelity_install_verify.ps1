$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R30_UIFidelity_Setup.exe'
$Expected='466AFC6AAD92B6E7F29DD6BCEF9AA6F00935D15D196C8F3B7E69B23A583FC3D5'
$Backup=Join-Path $Root 'delivery\prestate_r30_ui_fidelity_final_20260928'
New-Item -ItemType Directory -Force -Path $Backup|Out-Null
$ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
if(@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count){throw 'R30_PROJECT_NETWORK_NOT_AT_REST'}
if(Test-Path (Join-Path $Install 'gateway\runtime\owner.json')){throw 'R30_GATEWAY_OWNER_ACTIVE'}
if(Test-Path (Join-Path $Install 'gateway\runtime\gateway-session.json')){throw 'R30_GATEWAY_SESSION_ACTIVE'}
$actual=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
if($actual -ne $Expected){throw 'R30_INSTALLER_HASH_MISMATCH'}

$stateFiles=@('settings.json','data\nodes.json','data\node_public_refresh.json')
$pre=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');installerSha256=$actual;state=@{}}
foreach($rel in $stateFiles){
 $p=Join-Path $Install $rel
 if(Test-Path -LiteralPath $p){
  Copy-Item -LiteralPath $p -Destination (Join-Path $Backup ($rel.Replace('\','__'))) -Force
  $pre.state[$rel]=[ordered]@{exists=$true;bytes=(Get-Item $p).Length;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}
 } else {$pre.state[$rel]=[ordered]@{exists=$false}}
}
$pre|ConvertTo-Json -Depth 8|Set-Content (Join-Path $Backup 'prestate.json') -Encoding utf8

$scriptPath=Join-Path $Install 'app\FreeNetHub.ps1'
$owned=@(Get-CimInstance Win32_Process|Where-Object{
 ($_.ExecutablePath -and $_.ExecutablePath -ieq (Join-Path $Install 'FreeNetHub.exe')) -or
 ($_.CommandLine -and $_.CommandLine.Contains($scriptPath,[StringComparison]::OrdinalIgnoreCase))
}|Sort-Object ParentProcessId -Descending)
foreach($p in $owned){Stop-Process -Id ([int]$p.ProcessId) -Force -ErrorAction SilentlyContinue}
Start-Sleep -Milliseconds 800

$p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($p.ExitCode -ne 0){throw ('R30_INSTALL_EXIT_'+$p.ExitCode)}

$parity=[ordered]@{}
foreach($rel in @('app\engine.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json','RELEASE.json')){
 $src=Join-Path $Root $rel;$dst=Join-Path $Install $rel
 if(!(Test-Path $dst)){throw ('R30_INSTALLED_MISSING_'+$rel)}
 $sh=(Get-FileHash $src -Algorithm SHA256).Hash;$dh=(Get-FileHash $dst -Algorithm SHA256).Hash
 $parity[$rel]=($sh -eq $dh);if($sh -ne $dh){throw ('R30_PARITY_'+$rel)}
}
$preserved=[ordered]@{}
foreach($rel in $stateFiles){
 $before=$pre.state[$rel];$p2=Join-Path $Install $rel
 if($before.exists){
  if(!(Test-Path $p2)){throw ('R30_STATE_MISSING_'+$rel)}
  $after=(Get-FileHash $p2 -Algorithm SHA256).Hash
  if($after -ne $before.sha256){throw ('R30_STATE_CHANGED_'+$rel)}
  $preserved[$rel]=[ordered]@{preserved=$true;sha256=$after}
 } else {$preserved[$rel]=[ordered]@{preserved=(-not (Test-Path $p2))}}
}
$out=[ordered]@{
 schema=1;date='2026-09-28';status='PASS';candidate='R30_UI_FIDELITY_OWNER_REVIEW';
 installerSha256=$Expected;installExit=$p.ExitCode;parity=$parity;state=$preserved;
 projectListenersAfterInstall=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count;
 trustedWindowsSigning=(Get-AuthenticodeSignature -LiteralPath $Installer).Status.ToString()
}
$out|ConvertTo-Json -Depth 10|Set-Content (Join-Path $Root 'evidence\R30_UI_FIDELITY_FINAL_INSTALL_ACCEPTANCE_20260928.json') -Encoding utf8
$out|ConvertTo-Json -Depth 10
