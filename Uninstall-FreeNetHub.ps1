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
 $dd=Join-Path $Root 'app\directdpi\Stop-DirectDpi.ps1'
 $ddState=Join-Path $env:ProgramData 'FreeNetHub\directdpi\state.json'
 $ddDnsRuntime=Join-Path $env:ProgramData 'FreeNetHub\directdns'
 $ctrld=Join-Path $Root 'app\directdns\ctrld.exe'
 $svc=Get-CimInstance Win32_Service -Filter "Name='ctrld'" -ErrorAction SilentlyContinue
 $ownedSvc=$false
 if($svc -and $svc.PathName -and (Test-Path -LiteralPath $ctrld)){$ownedSvc=$svc.PathName.Contains($ctrld,[StringComparison]::OrdinalIgnoreCase)}
 $ownedProc=@(Get-Process ctrld -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith((Join-Path $Root 'app\directdns'),[StringComparison]::OrdinalIgnoreCase)})
 $needDirectCleanup=(Test-Path -LiteralPath $ddState) -or $ownedSvc -or ($ownedProc.Count -gt 0) -or (Test-Path -LiteralPath $ddDnsRuntime)
 if((Test-Path -LiteralPath $dd) -and $needDirectCleanup){
  & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $dd|Out-Null
  if($LASTEXITCODE -ne 0){throw ('DIRECT_DPI_STOP_EXIT_'+$LASTEXITCODE)}
  if(Test-Path -LiteralPath $ddState){throw 'DIRECT_DPI_STATE_REMAINS'}
  $Actions+='Stopped Direct-DPI and encrypted DNS, then restored network prestate'
 }
}catch{Add-Err ('directdpi: '+$_.Exception.Message)}
try{
 $dep=Join-Path $Root 'app\dependencies.json';$eng=Join-Path $Root 'app\engine.py'
 if((Test-Path -LiteralPath $dep) -and (Test-Path -LiteralPath $eng)){
  $d=Get-Content -LiteralPath $dep -Raw -Encoding UTF8|ConvertFrom-Json
  $py='';if($d.pythonw){$candidate=Join-Path (Split-Path ([string]$d.pythonw) -Parent) 'python.exe';if(Test-Path -LiteralPath $candidate){$py=$candidate}}
  if(!$py){$g=Get-Command python.exe -ErrorAction SilentlyContinue;if($g){$py=$g.Source}}
  if($py){
   # A closed/crashed UI can leave one exact engine job finishing in the background.
   # Request cancellation by its own job id and wait boundedly before Stop, rather than
   # racing its writes or killing unrelated Python processes.
   function Get-OwnedEngineJobs{
    @(
     Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object {$_.CommandLine -and $_.CommandLine.Contains($eng,[StringComparison]::OrdinalIgnoreCase)} |
      ForEach-Object {
       $m=[regex]::Match([string]$_.CommandLine,'(?i)(?:^|\s)--job\s+([a-f0-9]{32})(?:\s|$)')
       [pscustomobject]@{Pid=[int]$_.ProcessId;Job=$(if($m.Success){$m.Groups[1].Value}else{''})}
      }
    )
   }
   $running=@(Get-OwnedEngineJobs)
   if($running.Count){
    foreach($x in $running){
     if($x.Job){[IO.File]::WriteAllText((Join-Path $Root ('jobs\'+$x.Job+'.cancel')),'uninstall cancel',[Text.UTF8Encoding]::new($false))}
    }
    $Actions+='Requested cancellation of active FreeNetHub engine jobs'
    $deadline=[DateTime]::UtcNow.AddSeconds(25)
    do{Start-Sleep -Milliseconds 250;$running=@(Get-OwnedEngineJobs)}while($running.Count -and [DateTime]::UtcNow -lt $deadline)
    if($running.Count){throw ('ENGINE_JOB_DRAIN_TIMEOUT_'+(($running|ForEach-Object{$_.Pid}) -join ','))}
    $Actions+='Drained active FreeNetHub engine jobs before cleanup'
   }
   $stopOk=$false;$lastStop=''
   for($attempt=1;$attempt -le 3;$attempt++){
    $job=[guid]::NewGuid().ToString('N')
    & $py $eng --action Stop --mode AUTO --job $job --budget 90|Out-Null
    $ec=$LASTEXITCODE;$jr=Join-Path $Root ('jobs\'+$job+'.json');$detail=''
    if(Test-Path -LiteralPath $jr){
     try{$rec=Get-Content -LiteralPath $jr -Raw -Encoding UTF8|ConvertFrom-Json;$detail=[string]$rec.result.error}catch{}
    }
    if($ec -eq 0){$stopOk=$true;break}
    $lastStop=('exit='+$ec+' error='+$detail)
    if($attempt -lt 3 -and $detail -match 'Permission denied|BUSY_ANOTHER_JOB'){Start-Sleep -Milliseconds (350*$attempt);continue}
    break
   }
   if(!$stopOk){throw ('ENGINE_STOP_FAILED_'+$lastStop)}
   $Actions+='Stopped FreeNetHub-owned browser/proxy providers'
  }
 }
}catch{Add-Err ('engine: '+$_.Exception.Message)}
try{
 $left=@()
 if(Get-Process sing-box -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($Root,[StringComparison]::OrdinalIgnoreCase)}){$left+='sing-box'}
 if(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}){$left+='FreeNetHub TUN'}
 if(Test-Path -LiteralPath (Join-Path $Root 'gateway\runtime\wsl-console-owner.json')){$left+='WSL console owner'}
 if(Test-Path -LiteralPath (Join-Path $env:ProgramData 'FreeNetHub\directdpi\state.json')){$left+='Direct-DPI state'}
 if(Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '^WinDivert' -and $_.PathName -and $_.PathName.Contains((Join-Path $Root 'app\directdpi'),[StringComparison]::OrdinalIgnoreCase)}){$left+='Direct-DPI WinDivert'}
 if(Get-Process ctrld -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith((Join-Path $Root 'app\directdns'),[StringComparison]::OrdinalIgnoreCase)}){$left+='Direct-DNS ctrld process'}
 $ctrldSvc=Get-CimInstance Win32_Service -Filter "Name='ctrld'" -ErrorAction SilentlyContinue
 $ctrldPath=Join-Path $Root 'app\directdns\ctrld.exe'
 if($ctrldSvc -and $ctrldSvc.PathName -and $ctrldSvc.PathName.Contains($ctrldPath,[StringComparison]::OrdinalIgnoreCase)){$left+='Direct-DNS ctrld service'}
 if(Test-Path -LiteralPath (Join-Path $env:ProgramData 'FreeNetHub\directdns')){$left+='Direct-DNS runtime'}
 if($left.Count){throw ('NETWORK_RUNTIME_REMAINS_'+($left -join ','))}
}catch{Add-Err ('verify: '+$_.Exception.Message)}
$r=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($Errors.Count){'FAIL'}else{'PASS'});actions=$Actions;errors=$Errors}
if(!$ResultPath){$ResultPath=Join-Path $Root 'UNINSTALL_CLEANUP_STATUS.json'}
try{$r|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ResultPath -Encoding UTF8}catch{}
$r|ConvertTo-Json -Depth 8
if($Errors.Count){exit 20}
