[CmdletBinding()]
param([string]$Root)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
if(-not $Root){
  $Root=@("$env:LOCALAPPDATA\Programs\FreeNetHub","$env:USERPROFILE\source\repos\FreeNetHub") | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if(-not $Root){ throw 'FreeNetHub root not found.' }
$Root=(Resolve-Path -LiteralPath $Root).Path
$exe=Join-Path $Root 'FreeNetHub.exe'; $status=Join-Path $Root 'SHELL_HOST_STATUS.json'; $lnk=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FreeNet Hub.lnk'
$checks=[ordered]@{}
$checks.ExeExists=Test-Path -LiteralPath $exe
$checks.StatusExists=Test-Path -LiteralPath $status; if($checks.StatusExists){$st=Get-Content -LiteralPath $status -Raw -Encoding UTF8|ConvertFrom-Json;$checks.StatusShellVersion=$st.shellVersion;$checks.StatusShellVersionExpected=($st.shellVersion -eq '4.2.0')}
$checks.ShortcutExists=Test-Path -LiteralPath $lnk
if($checks.ExeExists){
  $v=[Diagnostics.FileVersionInfo]::GetVersionInfo($exe)
  $checks.ProductName=$v.ProductName
  $checks.FileVersion=$v.FileVersion; $checks.FileVersionExpected=($v.FileVersion -eq '4.2.0.0')
  $checks.ExeSha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
}
if($checks.ShortcutExists){
  $ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut($lnk)
  $checks.ShortcutTarget=$s.TargetPath; $checks.ShortcutIcon=$s.IconLocation
  $checks.ShortcutTargetsExe=([IO.Path]::GetFullPath($s.TargetPath) -eq [IO.Path]::GetFullPath($exe))
}
$checks.NoStartupInstalled = -not (Test-Path -LiteralPath (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\FreeNet Hub.lnk'))
$checks | ConvertTo-Json -Depth 4
