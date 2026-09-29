$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R37_Final_Setup.exe'
$Expected='35491B9BCAD06263C063DA7559D67B206F01028E613232F101D249D552BA0C64'
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Backup=Join-Path $env:LOCALAPPDATA 'FreeNetHub_R37_Verify_Backup_20260929_113607'
$Evidence=Join-Path $Root 'evidence\R37_PUBLIC_METADATA_INSTALL_ACCEPTANCE_20260929.json'
function FileHash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Route{Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue|Sort-Object RouteMetric|Select-Object -First 1 InterfaceIndex,InterfaceAlias,NextHop,RouteMetric}
function Parity{
 $am=Get-Content (Join-Path $Root 'app\manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $gm=Get-Content (Join-Path $Root 'gateway\manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
 foreach($x in $am.code){$s=Join-Path (Join-Path $Root 'app') ([string]$x.file);$i=Join-Path (Join-Path $Install 'app') ([string]$x.file);if(!(Test-Path $s) -or !(Test-Path $i) -or (FileHash $s) -ne (FileHash $i) -or (FileHash $s) -ne [string]$x.sha256){return $false}}
 foreach($x in $gm.files){$s=Join-Path (Join-Path $Root 'gateway') ([string]$x.file);$i=Join-Path (Join-Path $Install 'gateway') ([string]$x.file);if(!(Test-Path $s) -or !(Test-Path $i) -or (FileHash $s) -ne (FileHash $i) -or (FileHash $s) -ne [string]$x.sha256){return $false}}
 return ((FileHash (Join-Path $Root 'RELEASE.json')) -eq (FileHash (Join-Path $Install 'RELEASE.json')))
}
$pre=Route;$post=$null;$runtime=$null;$exit=$null;$parity=$false;$smoke=@();$errors=New-Object System.Collections.Generic.List[string]
try{
 if(!(Test-Path $Backup)){throw 'ACCEPTED_BACKUP_MISSING'}
 if(!(Test-Path $Installer) -or (FileHash $Installer) -ne $Expected){throw 'INSTALLER_HASH_MISMATCH'}
 $p=Start-Process -FilePath $Installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS','/RESTARTAPPLICATIONS=0') -Wait -PassThru
 $exit=$p.ExitCode;if($exit -ne 0){throw ('INSTALLER_EXIT_'+$exit)}
 $runtime=Get-Content (Join-Path $Install 'INSTALL_RUNTIME_STATUS.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$runtime.status -ne 'PASS'){throw 'RUNTIME_BOOTSTRAP_FAIL'}
 $rel=Get-Content (Join-Path $Install 'RELEASE.json') -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$rel.releaseRevision -ne '4.2.0-local-r37-final'){throw 'RELEASE_REVISION_MISMATCH'}
 $parity=Parity;if(!$parity){throw 'PARITY_FAIL'}
 foreach($i in 0..4){& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Install 'app\FreeNetHub.ps1') -Smoke -SmokeTab $i;$smoke+=@([pscustomobject]@{tab=$i;exit=$LASTEXITCODE});if($LASTEXITCODE -ne 0){throw ('SMOKE_'+$i)}}
 $post=Route
 if(!$pre -or !$post -or $pre.InterfaceIndex -ne $post.InterfaceIndex -or [string]$pre.NextHop -ne [string]$post.NextHop){throw 'ROUTE_CHANGED'}
}catch{
 $errors.Add($_.Exception.Message)
 try{if(Test-Path $Install){Remove-Item -LiteralPath $Install -Recurse -Force};Copy-Item -LiteralPath $Backup -Destination $Install -Recurse -Force}catch{$errors.Add('ROLLBACK_FAIL')}
}
if(!$post){$post=Route}
$out=[ordered]@{schema=1;date='2026-09-29';status=$(if($errors.Count -eq 0){'PASS'}else{'FAIL'});installerSha256=$Expected;installerExit=$exit;runtimeStatus=$(if($runtime){$runtime.status}else{$null});parity=$parity;smoke=$smoke;preRoute=$pre;postRoute=$post;rollbackBackup='%LOCALAPPDATA%\FreeNetHub_R37_Verify_Backup_20260929_113607';errors=@($errors)}
$out|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $Evidence -Encoding UTF8
$out|ConvertTo-Json -Depth 10
exit $(if($errors.Count -eq 0){0}else{20})
