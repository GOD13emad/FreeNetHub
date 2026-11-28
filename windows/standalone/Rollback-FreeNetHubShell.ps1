[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][string]$Backup)
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
$Root=(Resolve-Path -LiteralPath $Root).Path; $Backup=(Resolve-Path -LiteralPath $Backup).Path
$backupParent=Join-Path $Root 'backup'
$expectedParent=[IO.Path]::GetFullPath($backupParent).TrimEnd([IO.Path]::DirectorySeparatorChar)
$actualParent=[IO.Path]::GetFullPath((Split-Path -Parent $Backup)).TrimEnd([IO.Path]::DirectorySeparatorChar)
if(-not [String]::Equals($actualParent,$expectedParent,[StringComparison]::OrdinalIgnoreCase) -or
   (Split-Path -Leaf $Backup) -cnotmatch '^shell-v42-\d{8}-\d{6}$'){
    throw 'Refusing rollback: backup is not an installer-created folder immediately under this root.'
}
foreach($p in @($Root,$backupParent,$Backup)){
    $item=Get-Item -LiteralPath $p -Force
    if($item -isnot [IO.DirectoryInfo] -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){
        throw 'Refusing rollback: root or backup is not a regular directory (reparse point or other type).'
    }
}
function Get-RegularFileOrNull([string]$Path){
    try { $item=Get-Item -LiteralPath $Path -Force -ErrorAction Stop }
    catch [System.Management.Automation.ItemNotFoundException] { return $null }
    if($item -isnot [IO.FileInfo] -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){
        throw ('Refusing rollback: not a regular file: '+$Path)
    }
    return $item
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
# Validate every source and destination before the first mutation. Never treat
# a directory or a linked item as a package file.
$plan=@(foreach($name in @('FreeNetHub.exe','FreeNetHub.ico','SHELL_HOST_STATUS.json')){
    $src=Join-Path $Backup $name; $dst=Join-Path $Root $name
    $sourceItem=Get-RegularFileOrNull $src
    $destItem=Get-RegularFileOrNull $dst
    [pscustomobject]@{Source=$src;Destination=$dst;HasSource=($null -ne $sourceItem);HasDestination=($null -ne $destItem)}
})
$old=Join-Path $Backup 'FreeNet Hub.lnk'
$oldItem=Get-RegularFileOrNull $old
$linkItem=Get-RegularFileOrNull $lnk
# The Start Menu shortcut is shared across installations. A later install may
# own it now; never replace or remove a link whose current target is not ours.
$ownsShortcut=$true
if($null -ne $linkItem){
    try {
        $ws=New-Object -ComObject WScript.Shell
        $currentTarget=[string]$ws.CreateShortcut($lnk).TargetPath
        $ownsShortcut=(-not [string]::IsNullOrWhiteSpace($currentTarget)) -and
            [String]::Equals($currentTarget,$target,[StringComparison]::OrdinalIgnoreCase)
    }catch{ $ownsShortcut=$false }
}
if(-not $ownsShortcut){ Write-Warning 'Preserving shared Start Menu shortcut: ownership not established for this root.' }
foreach($action in $plan){
    if($action.HasSource){ Copy-Item -LiteralPath $action.Source -Destination $action.Destination -Force }
    elseif($action.HasDestination){ Remove-Item -LiteralPath $action.Destination -Force }
}
if($ownsShortcut){
    if($null -ne $oldItem){ Copy-Item -LiteralPath $old -Destination $lnk -Force }
    elseif($null -ne $linkItem){ Remove-Item -LiteralPath $lnk -Force }
}
Write-Host 'Rollback complete.'
