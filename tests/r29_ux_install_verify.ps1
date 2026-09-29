$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$InstallPrefix=([IO.Path]::GetFullPath($Install).TrimEnd('\')+'\')
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R29_UX_Setup.exe'
$Expected='0CFBE81F5B59CC51E16914257FF4125B965512CC50FF46B80B89F2F3762E278B'
$Backup=Join-Path $Root 'delivery\prestate_r29_ux_20260928'
New-Item -ItemType Directory -Force -Path $Backup|Out-Null

$ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
if($listeners.Count){throw 'R29_PROJECT_NETWORK_NOT_AT_REST'}

$scriptPath=Join-Path $Install 'app\FreeNetHub.ps1'
$procs=@(Get-CimInstance Win32_Process|Where-Object{
  ($_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath)).StartsWith($InstallPrefix,[StringComparison]::OrdinalIgnoreCase)) -or
  ($_.CommandLine -and $_.CommandLine.Contains($scriptPath,[StringComparison]::OrdinalIgnoreCase))
})
if($procs.Count){throw ('R29_PRIMARY_INSTALL_PROCESS_ACTIVE_'+(($procs|ForEach-Object{$_.ProcessId}) -join ','))}

$actual=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
if($actual -ne $Expected){throw 'R29_INSTALLER_HASH_MISMATCH'}

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

$installerProcess=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($installerProcess.ExitCode -ne 0){throw ('R29_INSTALL_EXIT_'+$installerProcess.ExitCode)}
Start-Sleep -Milliseconds 700

$parity=[ordered]@{}
foreach($rel in @('app\engine.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json','RELEASE.json')){
  $src=Join-Path $Root $rel;$dst=Join-Path $Install $rel
  if(!(Test-Path $dst)){throw ('R29_INSTALLED_MISSING_'+$rel)}
  $sh=(Get-FileHash $src -Algorithm SHA256).Hash;$dh=(Get-FileHash $dst -Algorithm SHA256).Hash
  $parity[$rel]=($sh -eq $dh)
  if($sh -ne $dh){throw ('R29_PARITY_'+$rel)}
}

$preserved=[ordered]@{}
foreach($rel in $stateFiles){
  $before=$pre.state[$rel];$p=Join-Path $Install $rel
  if($before.exists){
    if(!(Test-Path $p)){throw ('R29_STATE_MISSING_'+$rel)}
    $after=(Get-FileHash $p -Algorithm SHA256).Hash
    if($after -ne $before.sha256){throw ('R29_STATE_CHANGED_'+$rel)}
    $preserved[$rel]=[ordered]@{preserved=$true;sha256=$after}
  } else {$preserved[$rel]=[ordered]@{preserved=(-not (Test-Path $p))}}
}

$out=[ordered]@{
 schema=1;date='2026-09-28';status='PASS';candidate='R29_UX_OWNER_REVIEW';
 installerSha256=$Expected;installExit=$installerProcess.ExitCode;parity=$parity;state=$preserved;
 projectListenersAfterInstall=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count;
 trustedWindowsSigning=(Get-AuthenticodeSignature -LiteralPath $Installer).Status.ToString()
}
$out|ConvertTo-Json -Depth 10|Set-Content (Join-Path $Root 'evidence\R29_UX_INSTALL_ACCEPTANCE_20260928.json') -Encoding utf8
$out|ConvertTo-Json -Depth 10
