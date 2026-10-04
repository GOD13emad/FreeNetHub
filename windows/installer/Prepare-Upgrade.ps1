param([Parameter(Mandatory=$true)][string]$AppRoot)
$ErrorActionPreference='Stop'
$ports=19410,19413,19414,19450,19452,19453,19460,9909

function Get-ActiveListeners {
  @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort })
}
function Get-ProcessByIdSafe([int]$Id) {
  Get-CimInstance Win32_Process -Filter ("ProcessId="+$Id) -ErrorAction SilentlyContinue
}
function Test-OwnedRuntimeProcess($Proc) {
  if(!$Proc -or !$Proc.ExecutablePath){ return $false }
  try{$exe=[IO.Path]::GetFullPath([string]$Proc.ExecutablePath)}catch{return $false}
  $runtime=[IO.Path]::GetFullPath((Join-Path $AppRoot 'runtime')) + [IO.Path]::DirectorySeparatorChar
  $gatewayRuntime=[IO.Path]::GetFullPath((Join-Path $AppRoot 'gateway\runtime')) + [IO.Path]::DirectorySeparatorChar
  return $exe.StartsWith($runtime,[StringComparison]::OrdinalIgnoreCase) -or
         $exe.StartsWith($gatewayRuntime,[StringComparison]::OrdinalIgnoreCase)
}

$gatewayCtl=Join-Path $AppRoot 'gateway\gateway_control.ps1'
if(Test-Path -LiteralPath $gatewayCtl){
  $raw=& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $gatewayCtl -Action Status 2>$null|Out-String
  if($LASTEXITCODE -ne 0 -or !$raw){ exit 44 }
  try{$gatewayStatus=$raw|ConvertFrom-Json}catch{exit 44}
  if($gatewayStatus.result -and [bool]$gatewayStatus.result.running){ exit 42 }
}

$directDpiState=Join-Path $env:ProgramData 'FreeNetHub\directdpi\state.json'
if(Test-Path -LiteralPath $directDpiState){ exit 42 }

# A verified connected session is always an upgrade blocker.
$sessionPath=Join-Path $AppRoot 'session.json'
$session=$null
$sessionKnown=$false
$sessionConnected=$false
if(Test-Path -LiteralPath $sessionPath){
  try{
    $session=Get-Content -Raw -LiteralPath $sessionPath -Encoding UTF8 | ConvertFrom-Json
    if($null -ne $session.connected){
      $sessionKnown=$true
      $sessionConnected=[bool]$session.connected
    }
  }catch{
    $sessionKnown=$false
  }
}
if($sessionConnected){ exit 42 }

# Listener policy:
# - unknown ownership => fail closed
# - owned runtime with a live parent => fail closed
# - owned runtime with no live parent may be cleaned only when session is
#   explicitly known disconnected; this handles orphaned WARP/CFON runtimes.
$active=Get-ActiveListeners
if($active.Count){
  if(!$sessionKnown){ exit 42 }
  foreach($listener in @($active)){
    $proc=Get-ProcessByIdSafe ([int]$listener.OwningProcess)
    if(!$proc){ exit 42 }
    if(!(Test-OwnedRuntimeProcess $proc)){ exit 42 }
    $parent=$null
    if([int]$proc.ParentProcessId -gt 0){ $parent=Get-ProcessByIdSafe ([int]$proc.ParentProcessId) }
    if($parent){ exit 42 }
    Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop
  }
  Start-Sleep -Milliseconds 400
  if((Get-ActiveListeners).Count){ exit 42 }
}

$script=[IO.Path]::GetFullPath((Join-Path $AppRoot 'app\FreeNetHub.ps1'))
$launcher=[IO.Path]::GetFullPath((Join-Path $AppRoot 'FreeNetHub.exe'))
$owned=Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -ieq 'pwsh.exe' -and $_.CommandLine -and
   $_.CommandLine.IndexOf($script,[StringComparison]::OrdinalIgnoreCase) -ge 0) -or
  ($_.Name -ieq 'FreeNetHub.exe' -and $_.ExecutablePath -and
   [IO.Path]::GetFullPath($_.ExecutablePath).Equals($launcher,[StringComparison]::OrdinalIgnoreCase))
}
foreach($p in @($owned | Sort-Object { if($_.Name -ieq 'pwsh.exe'){0}else{1} })){
  Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
}
Start-Sleep -Milliseconds 400
$left=Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -ieq 'pwsh.exe' -and $_.CommandLine -and
   $_.CommandLine.IndexOf($script,[StringComparison]::OrdinalIgnoreCase) -ge 0) -or
  ($_.Name -ieq 'FreeNetHub.exe' -and $_.ExecutablePath -and
   [IO.Path]::GetFullPath($_.ExecutablePath).Equals($launcher,[StringComparison]::OrdinalIgnoreCase))
}
if(@($left).Count){ exit 43 }

# No provider listener may remain after preparation.
if((Get-ActiveListeners).Count){ exit 42 }
exit 0
