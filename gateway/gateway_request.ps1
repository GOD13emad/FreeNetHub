[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('StartPc','StartConsole','Stop','StopConsole','SetupConsole')][string]$Action,[Parameter(Mandatory)][string]$Job)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=(Resolve-Path "$PSScriptRoot\..").Path
if($Job -notmatch '^[a-fA-F0-9]{32}$'){throw 'INVALID_JOB_ID'}
$Controller=Join-Path $PSScriptRoot 'gateway_control.ps1'
function Assert-GatewayIntegrity{
 $mp=Join-Path $PSScriptRoot 'manifest.json';if(!(Test-Path $mp)){throw 'GATEWAY_MANIFEST_MISSING'};$m=Get-Content $mp -Raw -Encoding UTF8|ConvertFrom-Json;if([string]$m.version -ne '4.2.0'){throw 'GATEWAY_MANIFEST_VERSION'};foreach($f in $m.files){$fp=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ([string]$f.file)));$base=[IO.Path]::GetFullPath($Root)+'\';if(!$fp.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw ('GATEWAY_MANIFEST_PATH_OUTSIDE_PROJECT '+$f.file)};if(!(Test-Path $fp -PathType Leaf)){throw ('GATEWAY_FILE_MISSING '+$f.file)};if((Get-Item $fp).Length -ne [long]$f.bytes){throw ('GATEWAY_SIZE_MISMATCH '+$f.file)};if((Get-FileHash $fp -Algorithm SHA256).Hash -ne [string]$f.sha256){throw ('GATEWAY_HASH_MISMATCH '+$f.file)}}
}
Assert-GatewayIntegrity
$Result=Join-Path $Root ('jobs\gateway-'+$Job+'.json')
$tmp=$Result+'.tmp'
try{
 if($Action -eq 'SetupConsole'){
  $setup=Join-Path $PSScriptRoot 'Setup-ConsoleGateway.ps1'
  $sr=Join-Path $PSScriptRoot ('runtime\setup-'+$Job+'.json')
  Remove-Item $sr -Force -ErrorAction SilentlyContinue
  $p=Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$setup,'-InstallPrerequisites','-ResultPath',$sr) -Verb RunAs -Wait -PassThru
  $payload=if(Test-Path $sr){Get-Content $sr -Raw -Encoding UTF8|ConvertFrom-Json}else{[pscustomobject]@{status='FAIL';error='CONSOLE_SETUP_RESULT_MISSING'}}
  [ordered]@{schema=1;action=$Action;utc=[DateTimeOffset]::UtcNow.ToString('o');exit=$(if($p.ExitCode -eq 0 -and [string]$payload.status -eq 'PASS'){0}else{20});result=$payload}|ConvertTo-Json -Depth 16|Set-Content -LiteralPath $tmp -Encoding UTF8
  Move-Item $tmp $Result -Force;Remove-Item $sr -Force -ErrorAction SilentlyContinue
  exit $(if($p.ExitCode -eq 0 -and [string]$payload.status -eq 'PASS'){0}else{20})
 }
 $p=Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$Controller,'-Action',$Action,'-ResultPath',$Result) -Verb RunAs -Wait -PassThru
 if(!(Test-Path $Result)){[ordered]@{schema=1;action=$Action;utc=[DateTimeOffset]::UtcNow.ToString('o');exit=$p.ExitCode;result=[ordered]@{error='GATEWAY_RESULT_MISSING'}}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item $tmp $Result -Force}
 exit $p.ExitCode
}catch{
 [ordered]@{schema=1;action=$Action;utc=[DateTimeOffset]::UtcNow.ToString('o');exit=20;result=[ordered]@{error='UAC_CANCELLED_OR_ELEVATION_FAILED';detail=$_.Exception.Message}}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item $tmp $Result -Force;exit 20
}
