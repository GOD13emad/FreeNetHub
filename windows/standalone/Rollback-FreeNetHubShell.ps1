[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][string]$Backup)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
$Root=(Resolve-Path -LiteralPath $Root).Path; $Backup=(Resolve-Path -LiteralPath $Backup).Path
$backupParent=Join-Path $Root 'backup'
$prefix=[IO.Path]::GetFullPath($backupParent).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if(-not $Backup.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or
   (Split-Path -Leaf $Backup) -cnotmatch '^shell-v42-\d{8}-\d{6}$'){
    throw 'Refusing rollback: backup is not an installer-created folder under this root.'
}
foreach($p in @($backupParent,$Backup)){
    if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){
        throw 'Refusing rollback: backup path contains a reparse point.'
    }
}
$exe=Join-Path $Root 'FreeNetHub.exe'; $lnk=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\FreeNet Hub.lnk'
# Never stop other sessions or projects by process name. Fail closed if this
# exact installation's executable is still running; the owner closes it first.
$target=[IO.Path]::GetFullPath($exe)
$active=@(Get-CimInstance Win32_Process -Filter "Name = 'FreeNetHub.exe'" -ErrorAction Stop | Where-Object {
    $_.ExecutablePath -and
    [String]::Equals([IO.Path]::GetFullPath([string]$_.ExecutablePath),$target,[StringComparison]::OrdinalIgnoreCase)
})
if($active.Count -gt 0){
    throw 'Refusing rollback: close the FreeNetHub executable under this root first.'
}
foreach($name in @('FreeNetHub.exe','FreeNetHub.ico','SHELL_HOST_STATUS.json')){
  $src=Join-Path $Backup $name; $dst=Join-Path $Root $name
  if(Test-Path -LiteralPath $src){ Copy-Item -LiteralPath $src -Destination $dst -Force } elseif(Test-Path -LiteralPath $dst){ Remove-Item -LiteralPath $dst -Force }
}
$old=Join-Path $Backup 'FreeNet Hub.lnk'
if(Test-Path -LiteralPath $old){ Copy-Item -LiteralPath $old -Destination $lnk -Force } elseif(Test-Path -LiteralPath $lnk){ Remove-Item -LiteralPath $lnk -Force }
Write-Host 'Rollback complete.'
