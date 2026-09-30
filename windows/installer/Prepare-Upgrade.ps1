param([Parameter(Mandatory=$true)][string]$AppRoot)
$ErrorActionPreference='Stop'
$ports=19410,19413,19414,19450,19452,19453,19460,9909
$active=Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort }
if(@($active).Count){ exit 42 }
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
exit 0
