[CmdletBinding()]
param(
 [ValidateSet('PC_TUNNEL','CONSOLE_ONLY')][string]$Mode='PC_TUNNEL',
 [ValidateSet('WARP','GOOL','CFON')][string]$Provider='WARP',
 [string]$Profile,
 [string]$TargetCountry=''
)
$ErrorActionPreference='Stop'
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Python='C:\Python314\python.exe'
$Engine=Join-Path $Root 'app\engine.py'
$Generator=Join-Path $PSScriptRoot 'generate_config.py'
$Apply=Join-Path $PSScriptRoot 'apply_elevated.ps1'
$Result=Join-Path $Runtime 'apply_result.json'
if(Test-Path (Join-Path $Runtime 'owner.json')){throw 'GATEWAY_ALREADY_ACTIVE'}
New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
Remove-Item $Result -Force -ErrorAction SilentlyContinue
$providerStarted=$false
try{
 if(!$Profile){
  if($Mode -eq 'CONSOLE_ONLY' -and $TargetCountry){
   & $Python $Generator --mode $Mode --provider $Provider --target-country $TargetCountry --output (Join-Path $Runtime 'active.json')
  }else{
   & $Python $Generator --mode $Mode --provider $Provider --output (Join-Path $Runtime 'active.json')
  }
  if($LASTEXITCODE -ne 0){throw 'GATEWAY_CONFIG_GENERATION_FAILED'}
  # Local SOCKS provider must exist before TUN starts. Connect is bounded and owned by FreeNetHub.
  $job=[guid]::NewGuid().ToString('N')
  & $Python $Engine --action Connect --mode $Provider --job $job --budget 220|Out-Null
  $jr=Get-Content (Join-Path $Root ('jobs\'+$job+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
  if($jr.exit -ne 0 -or -not $jr.result.healthy){throw ('PROVIDER_CONNECT_FAILED_'+$Provider)}
  $providerStarted=$true
 }else{
  $args=@('--mode',$Mode,'--profile',$Profile,'--output',(Join-Path $Runtime 'active.json'))
  if($TargetCountry){$args+=@('--target-country',$TargetCountry)}
  & $Python $Generator @args
  if($LASTEXITCODE -ne 0){throw 'PROFILE_GATEWAY_CONFIG_GENERATION_FAILED'}
 }
 $cfg=(Resolve-Path (Join-Path $Runtime 'active.json')).Path
 $hash=(Get-FileHash $cfg -Algorithm SHA256).Hash
 $arg=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Apply,'-Mode',$Mode,'-ConfigPath',$cfg,'-ConfigSha256',$hash)
 try{$p=Start-Process pwsh.exe -Verb RunAs -ArgumentList $arg -PassThru}catch{throw 'UAC_CANCELLED_OR_FAILED'}
 $deadline=[DateTime]::UtcNow.AddSeconds(90)
 do{
  if(Test-Path $Result){break}
  if($p.HasExited -and !(Test-Path $Result)){break}
  Start-Sleep -Milliseconds 250
 }while([DateTime]::UtcNow -lt $deadline)
 if(!(Test-Path $Result)){throw 'ELEVATED_APPLY_RESULT_MISSING'}
 $r=Get-Content $Result -Raw -Encoding UTF8|ConvertFrom-Json
 if($r.status -ne 'PASS'){throw ('ELEVATED_APPLY_FAILED_'+$r.error)}
 [pscustomobject]@{status='PASS';mode=$Mode;provider=if($Profile){'LOCAL_PROFILE'}else{$Provider};owner=$r.owner;consoleManual=$r.consoleManual}|ConvertTo-Json -Depth 10
}catch{
 if($providerStarted -and !(Test-Path (Join-Path $Runtime 'owner.json'))){
  $job=[guid]::NewGuid().ToString('N');& $Python $Engine --action Stop --mode AUTO --job $job --budget 60|Out-Null
 }
 throw
}
