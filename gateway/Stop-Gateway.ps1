[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime';$Owner=Join-Path $Runtime 'owner.json';$Result=Join-Path $Runtime 'stop_result.json'
$Python='C:\Python314\python.exe';$Engine=Join-Path $Root 'app\engine.py';$StopElevated=Join-Path $PSScriptRoot 'stop_elevated.ps1'
if(Test-Path $Owner){
 Remove-Item $Result -Force -ErrorAction SilentlyContinue
 try{$p=Start-Process pwsh.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$StopElevated) -PassThru}catch{throw 'UAC_CANCELLED_OR_FAILED'}
 $deadline=[DateTime]::UtcNow.AddSeconds(60)
 do{if(Test-Path $Result){break};if($p.HasExited -and !(Test-Path $Result)){break};Start-Sleep -Milliseconds 250}while([DateTime]::UtcNow -lt $deadline)
 if(!(Test-Path $Result)){throw 'ELEVATED_STOP_RESULT_MISSING'}
 $r=Get-Content $Result -Raw -Encoding UTF8|ConvertFrom-Json
 if($r.status -ne 'PASS'){throw 'ELEVATED_STOP_FAILED'}
}
# Stop only FreeNetHub-owned local providers.
$j=[guid]::NewGuid().ToString('N');& $Python $Engine --action Stop --mode AUTO --job $j --budget 60|Out-Null
$jr=Get-Content (Join-Path $Root ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
[pscustomobject]@{status='PASS';gatewayOwned=(Test-Path $Owner);providerStopExit=$jr.exit}|ConvertTo-Json -Compress
