$ErrorActionPreference='Stop'
Set-StrictMode -Version 3.0
$Project=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Installer=Join-Path $Project 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R28_Final_Setup.exe'
$Evidence=Join-Path $Project 'evidence\R28_FINAL_INSTALL_ACCEPTANCE_20260928.json'
$Backup=Join-Path $Project 'delivery\prestate_r28_final_20260928'
$ExpectedInstaller='2AA91D849A513A21D3BF9903F8E72FFB6A184D378FB357CE4FA7A9D6F7EB0073'
$Expected=@{
 'app\engine.py'='9D9DC7724D05BF8C58986ABE760C9CF0A127F09816046D8984617CBE9A9C8658'
 'app\nodehub.py'='A5C5A1D62B63EA3806D3B2C8BF53A31D7AD491F057DD353EE666A38791320A07'
 'app\FreeNetHub.ps1'='6D37EEDAFBE475C785176B50CEBEE11EBA455CF8E6760E0C95DE9D1A0E446C60'
 'app\View.xaml'='3B170D89488940EEF41503E00FD6DD7AC9C0EAFDCDB7CF53532BDDEBF8AE7E0C'
 'app\manifest.json'='F82910D2755B78F34FAD59463832F2A7CA8D2849EBBF1E2EBD81F8EF1BDE84EF'
 'Uninstall-FreeNetHub.ps1'='DA9DF80E9AE19627BC665659306C9AB94EDAD25E5BD61E3E8AB90634F3532532'
 'RELEASE.json'='599378B4C9E6D5A92E7817AEBC08A3709E8EA60807ABD61C177238609CFEDF89'
}
function Get-Sha256([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Assert-Source{foreach($rel in $Expected.Keys){$p=Join-Path $Project $rel;if((Get-Sha256 $p) -ne $Expected[$rel]){throw ('SOURCE_DRIFT_'+$rel)}}}
function Write-J($o){[IO.File]::WriteAllText($Evidence,($o|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))}
$out=[ordered]@{schema=1;date='2026-09-28';status='FAIL';installerSha256='';installExit=$null;prestate=@{};parity=@{};preserved=@{};smoke=$false;stateRestored=$false;error=''}
$State=@('settings.json','data\nodes.json','data\node_public_refresh.json');$Saved=@{}
try{
 Assert-Source
 if((Get-Sha256 $Installer) -ne $ExpectedInstaller){throw 'FINAL_INSTALLER_HASH_MISMATCH'}
 $out.installerSha256=$ExpectedInstaller
 $ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
 if(@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort}).Count){throw 'PROJECT_NETWORK_NOT_AT_REST'}
 New-Item -ItemType Directory -Force -Path $Backup|Out-Null
 foreach($rel in $State){
  $p=Join-Path $Install $rel;$exists=Test-Path -LiteralPath $p
  $bytes=$(if($exists){[IO.File]::ReadAllBytes($p)}else{$null})
  $Saved[$rel]=@{Exists=$exists;Bytes=$bytes;Sha=$(if($exists){Get-Sha256 $p}else{$null})}
  $out.prestate[$rel]=[ordered]@{exists=$exists;sha=$Saved[$rel].Sha}
  if($exists){$dst=Join-Path $Backup ($rel -replace '[\\/]','__');[IO.File]::WriteAllBytes($dst,[byte[]]$bytes)}
 }
 $p=Start-Process -FilePath $Installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS','/SP-') -Wait -PassThru
 $out.installExit=$p.ExitCode
 if($p.ExitCode -ne 0){throw ('FINAL_INSTALL_EXIT_'+$p.ExitCode)}
 foreach($rel in $Expected.Keys){
  $src=Join-Path $Project $rel;$dst=Join-Path $Install $rel
  $ok=(Test-Path -LiteralPath $dst) -and ((Get-Sha256 $src) -eq (Get-Sha256 $dst))
  $out.parity[$rel]=$ok
  if(!$ok){throw ('FINAL_PARITY_'+$rel)}
 }
 foreach($rel in $State){
  $p2=Join-Path $Install $rel;$sv=$Saved[$rel]
  $ok=$(if($sv.Exists){(Test-Path -LiteralPath $p2) -and ((Get-Sha256 $p2) -eq $sv.Sha)}else{-not (Test-Path -LiteralPath $p2)})
  $out.preserved[$rel]=$ok
  if(!$ok){throw ('FINAL_STATE_NOT_PRESERVED_'+$rel)}
 }
 $Smoke=Join-Path $Project 'evidence\R28_FINAL_INSTALLED_SMOKE_20260928.json'
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Project 'windows\installer\Test-CleanInstall420.ps1') -InstallRoot $Install -EvidencePath $Smoke
 if($LASTEXITCODE -ne 0){throw 'FINAL_INSTALLED_SMOKE_FAILED'}
 $sj=Get-Content -LiteralPath $Smoke -Raw -Encoding UTF8|ConvertFrom-Json
 if(-not [bool]$sj.accepted){throw 'FINAL_INSTALLED_SMOKE_NOT_ACCEPTED'}
 $out.smoke=$true
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{
 foreach($rel in $State){
  if(!$Saved.ContainsKey($rel)){continue}
  $p=Join-Path $Install $rel;$sv=$Saved[$rel]
  if([bool]$sv.Exists){$parent=Split-Path $p -Parent;if(!(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null};[IO.File]::WriteAllBytes($p,[byte[]]$sv.Bytes)}
  else{Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue}
 }
 $restored=$true
 foreach($rel in $State){
  if(!$Saved.ContainsKey($rel)){continue}
  $p=Join-Path $Install $rel;$sv=$Saved[$rel]
  if($sv.Exists){if(!(Test-Path $p) -or (Get-Sha256 $p) -ne $sv.Sha){$restored=$false}}
  elseif(Test-Path $p){$restored=$false}
 }
 $out.stateRestored=$restored
 if(!$restored){$out.status='FAIL';if(!$out.error){$out.error='FINAL_STATE_RESTORE_FAILED'}}
 Write-J $out;$out|ConvertTo-Json -Depth 20
}
if($out.status -ne 'PASS'){exit 20}
