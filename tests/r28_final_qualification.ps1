$ErrorActionPreference='Stop'
Set-StrictMode -Version 3.0
$Root=Split-Path $PSScriptRoot -Parent
$QualIss=Join-Path $Root 'windows\installer\FreeNetHub.R28FinalQualification.iss'
$QualDir=Join-Path $Root 'delivery\qualification_r28_final'
$Qual=Join-Path $QualDir 'FreeNetHub_4.2.0_R28_Final_Qualification_Setup.exe'
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub-R28-Final-Qualification'
$Evidence=Join-Path $Root 'evidence\R28_FINAL_QUALIFICATION_ACCEPTANCE_20260928.json'
$Smoke=Join-Path $Root 'evidence\R28_FINAL_QUALIFICATION_SMOKE_20260928.json'
$Expected=@{
 'app\engine.py'='9D9DC7724D05BF8C58986ABE760C9CF0A127F09816046D8984617CBE9A9C8658'
 'app\nodehub.py'='A5C5A1D62B63EA3806D3B2C8BF53A31D7AD491F057DD353EE666A38791320A07'
 'app\FreeNetHub.ps1'='6D37EEDAFBE475C785176B50CEBEE11EBA455CF8E6760E0C95DE9D1A0E446C60'
 'app\View.xaml'='3B170D89488940EEF41503E00FD6DD7AC9C0EAFDCDB7CF53532BDDEBF8AE7E0C'
 'app\manifest.json'='F82910D2755B78F34FAD59463832F2A7CA8D2849EBBF1E2EBD81F8EF1BDE84EF'
 'gateway\manifest.json'='ACBC3A9622A75A7807C07A9DEC6D6A9FC310A527AEA185A1C4ED7552FB4E4966'
 'Uninstall-FreeNetHub.ps1'='DA9DF80E9AE19627BC665659306C9AB94EDAD25E5BD61E3E8AB90634F3532532'
 'windows\installer\FreeNetHub.iss'='DF2548625BADA16AE05AA35D80CD60E263B3E8DC5AFBB3AAA5B37B48DA8E6FC9'
 'RELEASE.json'='599378B4C9E6D5A92E7817AEBC08A3709E8EA60807ABD61C177238609CFEDF89'
}
function Get-Sha256Local([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Assert-Source{foreach($k in $Expected.Keys){$p=Join-Path $Root $k;if((Get-Sha256Local $p) -ne $Expected[$k]){throw ('SOURCE_DRIFT_'+$k)}}}
function WJ($o){[IO.File]::WriteAllText($Evidence,($o|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))}
$out=[ordered]@{schema=3;date='2026-09-28';status='FAIL';compile=$false;install=$false;smoke=$false;uninstall=$false;residue=@{};error=''}
try{
 Assert-Source
 if(Test-Path $Install){throw 'QUAL_ROOT_NOT_CLEAN'}
 New-Item -ItemType Directory -Force -Path $QualDir|Out-Null
 Remove-Item $Qual -Force -ErrorAction SilentlyContinue
 $iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
 & $iscc /Qp $QualIss
 if($LASTEXITCODE -ne 0 -or !(Test-Path $Qual)){throw 'QUAL_COMPILE_FAILED'}
 Assert-Source
 $out.compile=$true;$out.installerSha256=Get-Sha256Local $Qual;$out.installerBytes=(Get-Item $Qual).Length
 $p=Start-Process $Qual -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/TASKS=') -Wait -PassThru
 if($p.ExitCode -ne 0){throw ('QUAL_INSTALL_EXIT_'+$p.ExitCode)}
 $out.install=$true
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'windows\installer\Test-CleanInstall420.ps1') -InstallRoot $Install -EvidencePath $Smoke
 if($LASTEXITCODE -ne 0){throw 'QUAL_SMOKE_FAILED'}
 $sj=Get-Content $Smoke -Raw -Encoding UTF8|ConvertFrom-Json
 if(-not [bool]$sj.accepted){throw 'QUAL_SMOKE_NOT_ACCEPTED'}
 $out.smoke=$true
 $u=Join-Path $Install 'unins000.exe'
 $up=Start-Process $u -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
 if($up.ExitCode -ne 0){throw ('QUAL_UNINSTALL_EXIT_'+$up.ExitCode)}
 Start-Sleep -Milliseconds 800
 $ports=@(19410,19413,19414,19420,19430,19440,19450,19452,19453,19460,19591,19594)
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
 $out.uninstall=$true;$out.residue=[ordered]@{rootExists=Test-Path $Install;listeners=$listeners.Count}
 if($out.residue.rootExists -or $listeners.Count){throw 'QUAL_RESIDUE'}
 Assert-Source
 $out.status='PASS'
}catch{$out.error=$_.Exception.Message}
finally{WJ $out;$out|ConvertTo-Json -Depth 20}
if($out.status -ne 'PASS'){exit 20}
