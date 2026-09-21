[CmdletBinding()]
param([string]$ResultPath='')
$ErrorActionPreference='Continue'
Set-StrictMode -Version Latest
$Root=(Resolve-Path $PSScriptRoot).Path
$Errors=@();$Actions=@()
function Add-Err([string]$m){$script:Errors+=$m}
try{
 $ctl=Join-Path $Root 'gateway\gateway_control.ps1'
 if(Test-Path -LiteralPath $ctl){
  $raw=& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $ctl -Action Status 2>$null|Out-String
  if($LASTEXITCODE -ne 0){throw ('GATEWAY_STATUS_EXIT_'+$LASTEXITCODE)}
  if(!$raw){throw 'GATEWAY_STATUS_EMPTY'}
  $st=$raw|ConvertFrom-Json
  if(!$st.result){throw 'GATEWAY_STATUS_INVALID'}
  if([bool]$st.result.running){
   $job=[guid]::NewGuid().ToString('N')
   & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'gateway\gateway_request.ps1') -Action Stop -Job $job|Out-Null
   if($LASTEXITCODE -ne 0){throw 'GATEWAY_STOP_FAILED'}
   $jr=Join-Path $Root ('jobs\gateway-'+$job+'.json')
   if(!(Test-Path -LiteralPath $jr)){throw 'GATEWAY_STOP_RESULT_MISSING'}
   $j=Get-Content -LiteralPath $jr -Raw -Encoding UTF8|ConvertFrom-Json
   if([int]$j.exit -ne 0){throw ('GATEWAY_STOP_REJECTED_'+[string]$j.result.error)}
   $Actions+='Stopped active FreeNetHub gateway with verified rollback'
  }
 }
}catch{Add-Err ('gateway: '+$_.Exception.Message)}
try{
 $dep=Join-Path $Root 'app\dependencies.json';$eng=Join-Path $Root 'app\engine.py'
 if((Test-Path -LiteralPath $dep) -and (Test-Path -LiteralPath $eng)){
  $d=Get-Content -LiteralPath $dep -Raw -Encoding UTF8|ConvertFrom-Json
  $py='';if($d.pythonw){$candidate=Join-Path (Split-Path ([string]$d.pythonw) -Parent) 'python.exe';if(Test-Path -LiteralPath $candidate){$py=$candidate}}
  if(!$py){$g=Get-Command python.exe -ErrorAction SilentlyContinue;if($g){$py=$g.Source}}
  if($py){
   $job=[guid]::NewGuid().ToString('N')
   & $py $eng --action Stop --mode AUTO --job $job --budget 90|Out-Null
   if($LASTEXITCODE -ne 0){throw ('ENGINE_STOP_EXIT_'+$LASTEXITCODE)}
   $Actions+='Stopped FreeNetHub-owned browser/proxy providers'
  }
 }
}catch{Add-Err ('engine: '+$_.Exception.Message)}
try{
 $left=@()
 if(Get-Process sing-box -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($Root,[StringComparison]::OrdinalIgnoreCase)}){$left+='sing-box'}
 if(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}){$left+='FreeNetHub TUN'}
 if(Test-Path -LiteralPath (Join-Path $Root 'gateway\runtime\wsl-console-owner.json')){$left+='WSL console owner'}
 if($left.Count){throw ('NETWORK_RUNTIME_REMAINS_'+($left -join ','))}
}catch{Add-Err ('verify: '+$_.Exception.Message)}
$r=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($Errors.Count){'FAIL'}else{'PASS'});actions=$Actions;errors=$Errors}
if(!$ResultPath){$ResultPath=Join-Path $Root 'UNINSTALL_CLEANUP_STATUS.json'}
try{$r|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ResultPath -Encoding UTF8}catch{}
$r|ConvertTo-Json -Depth 8
if($Errors.Count){exit 20}
