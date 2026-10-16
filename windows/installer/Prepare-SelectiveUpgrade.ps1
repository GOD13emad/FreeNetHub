[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$AppRoot)
$ErrorActionPreference='Stop'

# Read-only preinstall safety guard for the opt-in FreeNetHub PAC owner.
# The accepted V458 Prepare-Upgrade.ps1 remains byte-for-byte unchanged.
$state=Join-Path $AppRoot 'data\selective_windows\policy.json'
try{
  if(Test-Path -LiteralPath $state){
    $d=Get-Content -LiteralPath $state -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
    if($d -isnot [Collections.IDictionary]){exit 42}
    if(!$d.Contains('schema') -or [int]$d['schema'] -ne 1 -or
       !$d.Contains('enabled') -or $d['enabled'] -isnot [bool] -or
       [bool]$d['enabled'] -or [bool]$d['inFlight']){exit 42}
    # Disabled state still requires the owned loopback helper to be gone.
    $listeners=@(Get-NetTCPConnection -State Listen -LocalPort @(19416,19417) -ErrorAction SilentlyContinue)
    if($listeners.Count){exit 42}
  }
  $reg=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction Stop
  if($reg.PSObject.Properties['AutoConfigURL'] -and [string]$reg.PSObject.Properties['AutoConfigURL'].Value -like 'http://127.0.0.1:19416/route.pac*'){exit 42}
  exit 0
}catch{
  exit 42
}
