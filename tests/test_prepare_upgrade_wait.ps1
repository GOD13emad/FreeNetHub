param(
  [ValidateSet('','quiescent','slow-owned-exit','stuck-owned','active-session','foreign-listener')]
  [string]$Case='',
  [string]$Marker=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$helper=Join-Path (Split-Path $PSScriptRoot -Parent) 'windows/installer/Prepare-Upgrade.ps1'
if(-not $Case){
  if(-not $IsWindows){throw 'WINDOWS_ONLY_ISOLATED_TEST'}
  $cases=@(
    @{Name='quiescent';Code=0;Stop=$false;Wait=$false},
    @{Name='slow-owned-exit';Code=0;Stop=$true;Wait=$true},
    @{Name='stuck-owned';Code=43;Stop=$true;Wait=$true},
    @{Name='active-session';Code=42;Stop=$false;Wait=$false},
    @{Name='foreign-listener';Code=42;Stop=$false;Wait=$false}
  )
  $pwdPath=Join-Path $env:TEMP ('fnh-v458-regression-'+[guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $pwdPath | Out-Null
  try {
    foreach($test in $cases){
      $mark=Join-Path $pwdPath ($test.Name+'.trace')
      & (Get-Command pwsh).Source -NoProfile -NonInteractive -File $PSCommandPath -Case $test.Name -Marker $mark
      $actual=$LASTEXITCODE
      if($actual -ne $test.Code){throw "CASE_$($test.Name)_EXPECTED_$($test.Code)_ACTUAL_$actual"}
      $observed=if(Test-Path $mark){Get-Content $mark -Raw}else{''}
      $sawStop=$observed.Contains('STOP')
      $sawWait=$observed.Contains('WAIT')
      if($sawStop -ne $test.Stop -or $sawWait -ne $test.Wait){
        throw "CASE_$($test.Name)_SIDE_EFFECT_POLICY_FAILED"
      }
      Write-Output "PASS_$($test.Name)_EXIT_$actual"
    }
    Write-Output 'PREPARE_UPGRADE_BOUNDED_WAIT_5_CASES_PASS'
  }finally{
    Remove-Item -LiteralPath $pwdPath -Recurse -Force -ErrorAction SilentlyContinue
  }
  exit 0
}
$fake=Join-Path (Split-Path -Parent $Marker) ('fixture-'+$Case)
New-Item -ItemType Directory -Path $fake | Out-Null
try {
  $state=if($Case -eq 'active-session'){'{"connected":true}'}else{'{"connected":false,"stopped":true}'}
  Set-Content -LiteralPath (Join-Path $fake 'session.json') -Value $state -Encoding utf8
  $global:FnhWaitCase=$Case
  $global:FnhTarget=Join-Path $fake 'FreeNetHub.exe'
  $global:FnhProcessWasStopped=$false
  $global:FnhProcessHasExited=$false
  $global:FnhMarker=$Marker
  function Get-NetTCPConnection {
    if($global:FnhWaitCase -eq 'foreign-listener'){
      return [PSCustomObject]@{LocalPort=19414;OwningProcess=45455;LocalAddress='127.0.0.1'}
    }
    return @()
  }
  function Get-CimInstance {
    param([string]$ClassName,[string]$Filter)
    if($ClassName -ne 'Win32_Process'){ throw 'UNEXPECTED_CLASS' }
    if($global:FnhWaitCase -eq 'foreign-listener'){
      return [PSCustomObject]@{Name='foreign.exe';ProcessId=45455;ParentProcessId=0;ExecutablePath='C:\Windows\System32\foreign.exe';CommandLine=''}
    }
    if($global:FnhWaitCase -in @('slow-owned-exit','stuck-owned') -and -not $global:FnhProcessHasExited){
      return [PSCustomObject]@{Name='FreeNetHub.exe';ProcessId=51234;ParentProcessId=0;ExecutablePath=$global:FnhTarget;CommandLine=''}
    }
    return @()
  }
  function Stop-Process {
    param([int]$Id,[switch]$Force,[string]$ErrorAction)
    if($Id -ne 51234){throw 'FOREIGN_STOP_GUARD'}
    $global:FnhProcessWasStopped=$true
    Add-Content -LiteralPath $global:FnhMarker -Value 'STOP'
  }
  function Wait-Process {
    param([int[]]$Id,[int]$Timeout,[string]$ErrorAction)
    if(@($Id).Count -ne 1 -or $Id[0] -ne 51234 -or $Timeout -lt 1 -or $Timeout -gt 10){throw 'UNBOUNDED_WAIT_OR_WRONG_PROCESS'}
    if(-not $global:FnhProcessWasStopped){throw 'WAIT_BEFORE_STOP'}
    Add-Content -LiteralPath $global:FnhMarker -Value 'WAIT'
    if($global:FnhWaitCase -eq 'slow-owned-exit'){
      Start-Sleep -Milliseconds 25
      $global:FnhProcessHasExited=$true
    }
  }
  # Installer runs this helper without caller StrictMode. Reproduce that process mode.
  Set-StrictMode -Off
  & $helper -AppRoot $fake
  $helperExit=$LASTEXITCODE
}finally{
  Remove-Item -LiteralPath $fake -Recurse -Force -ErrorAction SilentlyContinue
}
exit $helperExit
