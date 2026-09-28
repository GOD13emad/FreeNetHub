$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Prefix=([IO.Path]::GetFullPath($Install).TrimEnd('\')+'\')
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R28_TransportFix2_Setup.exe'
$Expected='5F001C1D617D4122E50E1F0E6B99E0343005F3872193E2C1EC1A3D8115A3D4AA'
$Backup=Join-Path $Root 'delivery\prestate_r28_transportfix2_20260928'
New-Item -ItemType Directory -Force -Path $Backup|Out-Null
$ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
if(@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count){throw 'PROJECT_NETWORK_NOT_AT_REST'}
$primary=@(Get-CimInstance Win32_Process|Where-Object{
 ($_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath)).StartsWith($Prefix,[StringComparison]::OrdinalIgnoreCase)) -or
 ($_.CommandLine -and $_.CommandLine.Contains((Join-Path $Install 'app\FreeNetHub.ps1'),[StringComparison]::OrdinalIgnoreCase))
})
if($primary.Count){throw ('PRIMARY_INSTALL_PROCESS_ACTIVE_'+(($primary|ForEach-Object{$_.ProcessId}) -join ','))}
if((Get-FileHash $Installer -Algorithm SHA256).Hash -ne $Expected){throw 'INSTALLER_HASH_MISMATCH'}
$stateFiles=@('settings.json','data\nodes.json','data\node_public_refresh.json')
$pre=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');installerSha256=$Expected;state=@{}}
foreach($rel in $stateFiles){
 $p=Join-Path $Install $rel
 if(Test-Path $p){
  Copy-Item $p (Join-Path $Backup ($rel.Replace('\','__'))) -Force
  $pre.state[$rel]=[ordered]@{exists=$true;bytes=(Get-Item $p).Length;sha256=(Get-FileHash $p -Algorithm SHA256).Hash}
 }else{$pre.state[$rel]=[ordered]@{exists=$false}}
}
$pre|ConvertTo-Json -Depth 8|Set-Content (Join-Path $Backup 'prestate.json') -Encoding utf8
$installerProcess=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
if($installerProcess.ExitCode -ne 0){throw ('INSTALL_EXIT_'+$installerProcess.ExitCode)}
Start-Sleep -Milliseconds 700
$parity=[ordered]@{}
foreach($rel in @('app\engine.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json','RELEASE.json')){
 $src=Join-Path $Root $rel;$dst=Join-Path $Install $rel
 $sh=(Get-FileHash $src -Algorithm SHA256).Hash;$dh=(Get-FileHash $dst -Algorithm SHA256).Hash
 if($sh -ne $dh){throw ('PARITY_'+$rel)}
 $parity[$rel]=$true
}
$state=[ordered]@{}
foreach($rel in $stateFiles){
 $before=$pre.state[$rel];$p=Join-Path $Install $rel
 if($before.exists){
  if(!(Test-Path $p)){throw ('STATE_MISSING_'+$rel)}
  $after=(Get-FileHash $p -Algorithm SHA256).Hash
  if($after -ne $before.sha256){throw ('STATE_CHANGED_'+$rel)}
  $state[$rel]=[ordered]@{preserved=$true;sha256=$after}
 }else{$state[$rel]=[ordered]@{preserved=(-not (Test-Path $p))}}
}
$out=[ordered]@{schema=1;date='2026-09-28';status='PASS';candidate='R28_TRANSPORT_FIX2';installerSha256=$Expected;installExit=$installerProcess.ExitCode;parity=$parity;state=$state;trustedWindowsSigning='OPEN_NOTSIGNED'}
$out|ConvertTo-Json -Depth 10|Set-Content (Join-Path $Root 'evidence\R28_TRANSPORT_FIX2_INSTALL_ACCEPTANCE_20260928.json') -Encoding utf8
$out|ConvertTo-Json -Depth 10
