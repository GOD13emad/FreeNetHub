[CmdletBinding()]
param([string]$Root)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

function Get-FileSha256([string]$p){ (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Assert-PackageIntegrity{
  $mp=Join-Path $PSScriptRoot 'MANIFEST.json'
  if(!(Test-Path -LiteralPath $mp)){throw 'Package manifest missing.'}
  $m=Get-Content -LiteralPath $mp -Raw -Encoding UTF8|ConvertFrom-Json
  if($m.product -ne 'FreeNet Hub' -or $m.version -ne '4.1.2'){throw 'Package identity mismatch.'}
  foreach($f in $m.files){
    $p=Join-Path $PSScriptRoot ([string]$f.name)
    if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Package file missing: '+$f.name)}
    if((Get-Item -LiteralPath $p).Length -ne [int64]$f.bytes){throw ('Package size mismatch: '+$f.name)}
    if((Get-FileSha256 $p) -ine [string]$f.sha256){throw ('Package hash mismatch: '+$f.name)}
  }
}
Assert-PackageIntegrity
if(-not $Root){
  $roots=@(
    "$env:USERPROFILE\source\repos\FreeNetHub",
    "$env:LOCALAPPDATA\FreeTunnelLab\FreeNetHub"
  ) | Where-Object { Test-Path -LiteralPath $_ }
  if(-not $roots){ throw 'FreeNetHub project root not found.' }
  $Root=$roots[0]
}
$Root=(Resolve-Path -LiteralPath $Root).Path
$entry=@('app\FreeNetHub.ps1','FreeNetHub.ps1','App.ps1','app.ps1','App\App.ps1','src\App.ps1') | ForEach-Object { Join-Path $Root $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if(-not $entry){ throw 'UI PowerShell entry point not found.' }
$pwsh=@(
  "$env:ProgramFiles\PowerShell\7\pwsh.exe",
  "$env:ProgramFiles\PowerShell\7-preview\pwsh.exe",
  (Get-Command pwsh.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if(-not $pwsh){ throw 'PowerShell 7 (pwsh.exe) not found.' }
$backup=Join-Path $Root ('backup\shell-v41-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$out=Join-Path $Root 'FreeNetHub.exe'
$oldShortcut=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FreeNet Hub.lnk'
foreach($p in @($out,$oldShortcut,(Join-Path $Root 'FreeNetHub.ico'),(Join-Path $Root 'SHELL_HOST_STATUS.json'))){
  if(Test-Path -LiteralPath $p){ Copy-Item -LiteralPath $p -Destination $backup -Force }
}

$icon=Join-Path $Root 'FreeNetHub.ico'
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'FreeNetHub.ico') -Destination $icon -Force
$prebuilt=Join-Path $PSScriptRoot 'FreeNetHub.exe'
if(Test-Path -LiteralPath $prebuilt){
  Copy-Item -LiteralPath $prebuilt -Destination $out -Force
} else {
  $csc=@(
    "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe"
  ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if(-not $csc){ throw 'Neither prebuilt FreeNetHub.exe nor Windows C# compiler is available.' }
  $src=Join-Path $PSScriptRoot 'FreeNetHubShell.cs'
  $man=Join-Path $PSScriptRoot 'FreeNetHubShell.manifest'
  $compilerArgs=@('/nologo','/target:winexe','/optimize+','/platform:anycpu','/r:System.dll','/r:System.Drawing.dll','/r:System.Windows.Forms.dll',('/win32icon:'+$icon),('/win32manifest:'+$man),('/out:'+$out),$src)
  & $csc $compilerArgs
  if($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $out)){ throw 'Compilation failed.' }
}

$start=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$lnk=Join-Path $start 'FreeNet Hub.lnk'
$ws=New-Object -ComObject WScript.Shell
$s=$ws.CreateShortcut($lnk)
$s.TargetPath=$out
$s.Arguments='"'+$entry+'"'
$s.WorkingDirectory=$Root
$s.IconLocation="$out,0"
$s.Description='FreeNet Hub 4.1.2 — standalone desktop shell'
$s.Save()

$status=[ordered]@{
  product='FreeNet Hub'; shellVersion='4.1.2'; installed=(Get-Date).ToString('o'); root=$Root; exe=$out; entry=$entry; powershell=$pwsh; shortcut=$lnk; backup=$backup;
  exeSha256=(Get-FileSha256 $out); iconSha256=(Get-FileSha256 $icon); entrySha256=(Get-FileSha256 $entry); routeOrProxyMutation=$false; startupInstalled=$false
}
$status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Root 'SHELL_HOST_STATUS.json') -Encoding UTF8
Write-Host ('Installed: '+$out)
Write-Host ('SHA256: '+$status.exeSha256)
Write-Host ('Backup: '+$backup)
