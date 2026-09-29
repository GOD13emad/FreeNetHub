$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R32_AuditClosure_Setup.exe'
$Expected='23DA773095F54BD0F2AEBF17815E0F9783CF00CDCADDCF17211E84F1154E1B34'
$Backup=Join-Path $Root 'delivery\prestate_r32_audit_closure_final_20260928'
New-Item -ItemType Directory -Force -Path $Backup|Out-Null
$ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
if($listeners.Count){throw 'R32_PROJECT_NETWORK_NOT_AT_REST'}
foreach($rel in @('gateway\runtime\owner.json','gateway\runtime\gateway-session.json','gateway\runtime\wsl-console-owner.json','gateway\runtime\console-provider-owner.json')){
 if(Test-Path (Join-Path $Install $rel)){throw ('R32_ACTIVE_STATE_'+$rel)}
}
$scriptPath=Join-Path $Install 'app\FreeNetHub.ps1'
$owned=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{
 ($_.ExecutablePath -and $_.ExecutablePath -ieq (Join-Path $Install 'FreeNetHub.exe')) -or
 ($_.CommandLine -and $_.CommandLine.Contains($scriptPath,[StringComparison]::OrdinalIgnoreCase))
})
if($owned.Count){throw ('R32_INSTALLED_UI_ACTIVE_'+(($owned|ForEach-Object{$_.ProcessId}) -join ','))}
$actual=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
if($actual -ne $Expected){throw 'R32_INSTALLER_HASH_MISMATCH'}

$stateFiles=@('settings.json','data\nodes.json','data\node_public_refresh.json','gateway\runtime\local_gateway.json','gateway\runtime\local_provider.json','gateway\runtime\console.profile.json')
$pre=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');installerSha256=$actual;state=@{}}
foreach($rel in $stateFiles){
 $p=Join-Path $Install $rel
 if(Test-Path -LiteralPath $p){
  Copy-Item -LiteralPath $p -Destination (Join-Path $Backup ($rel.Replace('\','__'))) -Force
  $pre.state[$rel]=[ordered]@{exists=$true;bytes=(Get-Item $p).Length;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}
 }else{$pre.state[$rel]=[ordered]@{exists=$false}}
}
$pre|ConvertTo-Json -Depth 8|Set-Content (Join-Path $Backup 'prestate.json') -Encoding utf8

$p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($p.ExitCode -ne 0){throw ('R32_INSTALL_EXIT_'+$p.ExitCode)}
Start-Sleep -Milliseconds 700

$parity=[ordered]@{}
foreach($rel in @('app\engine.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json','RELEASE.json')){
 $src=Join-Path $Root $rel;$dst=Join-Path $Install $rel
 if(!(Test-Path $dst)){throw ('R32_INSTALLED_MISSING_'+$rel)}
 $sh=(Get-FileHash $src -Algorithm SHA256).Hash;$dh=(Get-FileHash $dst -Algorithm SHA256).Hash
 $parity[$rel]=($sh -eq $dh);if($sh -ne $dh){throw ('R32_PARITY_'+$rel)}
}
$preserved=[ordered]@{}
foreach($rel in $stateFiles){
 $before=$pre.state[$rel];$p2=Join-Path $Install $rel
 if($before.exists){
  if(!(Test-Path $p2)){throw ('R32_STATE_MISSING_'+$rel)}
  $after=(Get-FileHash $p2 -Algorithm SHA256).Hash
  if($after -ne $before.sha256){throw ('R32_STATE_CHANGED_'+$rel)}
  $preserved[$rel]=[ordered]@{preserved=$true;sha256=$after}
 }else{
  if((Test-Path $p2) -and $rel -notin @('gateway\runtime\local_gateway.json')){throw ('R32_UNEXPECTED_STATE_CREATED_'+$rel)}
  $preserved[$rel]=[ordered]@{preserved=(-not (Test-Path $p2))}
 }
}

$smoke=Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Install 'app\FreeNetHub.ps1'),'-Smoke') -WorkingDirectory $Install -Wait -PassThru
if($smoke.ExitCode -ne 0){throw ('R32_INSTALLED_SMOKE_EXIT_'+$smoke.ExitCode)}
$release=Get-Content (Join-Path $Install 'RELEASE.json') -Raw -Encoding utf8|ConvertFrom-Json
if([string]$release.releaseRevision -ne '4.2.0-local-r32-audit-closure'){throw 'R32_INSTALLED_RELEASE_REVISION_MISMATCH'}
$left=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
if($left.Count){throw 'R32_LISTENER_REMAINS_AFTER_INSTALL_SMOKE'}

$out=[ordered]@{
 schema=1;date='2026-09-28';status='PASS';candidate='R32_AUDIT_CLOSURE_OWNER_REVIEW';
 installer=[ordered]@{file='FreeNetHub_4.2.0_R32_AuditClosure_Setup.exe';sha256=$Expected;bytes=(Get-Item $Installer).Length;authenticode=(Get-AuthenticodeSignature -LiteralPath $Installer).Status.ToString()};
 installExit=$p.ExitCode;installedSmoke='PASS';releaseRevision=[string]$release.releaseRevision;
 parity=$parity;statePreservation=$preserved;projectListenersAfterInstall=0;
 consoleCapability=[ordered]@{localGateway=(Test-Path (Join-Path $Install 'gateway\runtime\local_gateway.json'));localProvider=(Test-Path (Join-Path $Install 'gateway\runtime\local_provider.json'));consoleProfile=(Test-Path (Join-Path $Install 'gateway\runtime\console.profile.json'));policy='FAIL_CLOSED_WITHOUT_PROVIDER_OR_PROFILE'};
 openGates=@('ALL_PROVIDER_FULL_SYSTEM','WIREGUARD_PROFILE_PRECONNECT_SPEED','TRUSTED_WINDOWS_AUTHENTICODE','PHYSICAL_CONSOLE_FIELD_E2E','PUBLIC_GITHUB_PROMOTION')
}
$out|ConvertTo-Json -Depth 10|Set-Content (Join-Path $Root 'evidence\R32_AUDIT_CLOSURE_ACCEPTANCE_20260928.json') -Encoding utf8
$out|ConvertTo-Json -Depth 10
