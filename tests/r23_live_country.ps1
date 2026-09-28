$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
Set-Location $Install
$Settings=Join-Path $Install 'settings.json'
$HadSettings=Test-Path -LiteralPath $Settings
$SettingsBytes=if($HadSettings){[IO.File]::ReadAllBytes($Settings)}else{$null}
$Evidence=Join-Path $Install 'evidence\R23_STRICT_COUNTRY_ACCEPTANCE_20260928.json'
function WJ([string]$Path,$Value){
 $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
 [IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 18),[Text.UTF8Encoding]::new($false))
 [IO.File]::Move($tmp,$Path,$true)
}
function Run-Engine([string]$Action,[string]$Mode='AUTO',[string]$Payload='',[int]$Budget=120){
 $job=[guid]::NewGuid().ToString('N')
 $args=@('app\engine.py','--action',$Action,'--mode',$Mode,'--job',$job,'--budget',[string]$Budget)
 if($Payload){$args+=@('--payload',$Payload)}
 & python @args | Out-Null
 $exit=$LASTEXITCODE
 $path=Join-Path $Install ('jobs\'+$job+'.json')
 if(!(Test-Path -LiteralPath $path)){return @{exit=$exit;record=$null}}
 $r=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable
 return @{exit=$exit;record=$r}
}
function PortActive{
 $lines=& netstat.exe -ano -p tcp
 return [bool]($lines|Select-String -SimpleMatch ':19460 ' | Select-String -Pattern 'LISTENING')
}
function Test-Target([string]$Country){
 if(PortActive){try{Run-Engine 'StopOne' 'NODE' '' 30|Out-Null}catch{};Start-Sleep -Milliseconds 400}
 WJ $Settings @{country=$Country;order=@('NODE','CFON','WARP','TOR','GOOL')}
 $r=Run-Engine 'Connect' 'NODE' '' 120
 $o=[ordered]@{target=$Country;outcome='';actual='';healthy=$false;error='';acceptedWrongCountry=$false}
 if($r.record -and $r.record.result){
   $h=$r.record.result
   $o.actual=[string]$h.country;$o.healthy=[bool]$h.healthy;$o.error=[string]$h.error
   if($r.exit -eq 0 -and $h.healthy -and ([string]$h.country).ToUpperInvariant() -eq $Country){$o.outcome='MATCH_ACCEPTED'}
   elseif($r.exit -eq 0 -and $h.healthy -and ([string]$h.country).ToUpperInvariant() -ne $Country){$o.outcome='WRONG_COUNTRY_ACCEPTED';$o.acceptedWrongCountry=$true}
   else{$o.outcome='FAIL_CLOSED'}
 } else {$o.outcome='FAIL_CLOSED';$o.error='NO_SUCCESS_RESULT'}
 try{Run-Engine 'StopOne' 'NODE' '' 30|Out-Null}catch{}
 Start-Sleep -Milliseconds 500
 $o['listenerAfter']=[bool](PortActive)
 return $o
}
$sum=[ordered]@{schema=1;date='2026-09-28';status='FAIL';tests=@();settingsRestored=$false;tcp19460ActiveAfter=$true;privacy='No raw node credential or raw exit IP is stored.'}
try{
 $sum.tests=@((Test-Target 'SG'),(Test-Target 'DE'))
 if(@($sum.tests|Where-Object{$_.acceptedWrongCountry -or $_.listenerAfter}).Count -gt 0){throw 'STRICT_COUNTRY_VIOLATION'}
 $sum.status='PASS'
} finally {
 try{Run-Engine 'StopOne' 'NODE' '' 30|Out-Null}catch{}
 if($HadSettings){[IO.File]::WriteAllBytes($Settings,$SettingsBytes)}else{Remove-Item -LiteralPath $Settings -Force -ErrorAction SilentlyContinue}
 Start-Sleep -Milliseconds 500
 $sum.settingsRestored=$true
 $sum.tcp19460ActiveAfter=[bool](PortActive)
 if($sum.tcp19460ActiveAfter){$sum.status='FAIL'}
 WJ $Evidence $sum
 Write-Output ($sum|ConvertTo-Json -Depth 18)
}
if($sum.status -ne 'PASS'){exit 20}
