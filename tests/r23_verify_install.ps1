$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Pre=Get-Content -LiteralPath (Join-Path $Root 'delivery\prestate_r23_country_20260928\prestate.json') -Raw|ConvertFrom-Json
$srcE=(Get-FileHash -LiteralPath (Join-Path $Root 'app\engine.py') -Algorithm SHA256).Hash
$insE=(Get-FileHash -LiteralPath (Join-Path $Install 'app\engine.py') -Algorithm SHA256).Hash
$srcM=(Get-FileHash -LiteralPath (Join-Path $Root 'app\manifest.json') -Algorithm SHA256).Hash
$insM=(Get-FileHash -LiteralPath (Join-Path $Install 'app\manifest.json') -Algorithm SHA256).Hash
if($srcE -ne $insE){throw 'INSTALLED_ENGINE_MISMATCH'}
if($srcM -ne $insM){throw 'INSTALLED_MANIFEST_MISMATCH'}
if($Pre.settings){
 $h=(Get-FileHash -LiteralPath (Join-Path $Install 'settings.json') -Algorithm SHA256).Hash
 if($h -ne $Pre.settings.sha256){throw 'SETTINGS_NOT_PRESERVED'}
}
if($Pre.nodes){
 $h=(Get-FileHash -LiteralPath (Join-Path $Install 'data\nodes.json') -Algorithm SHA256).Hash
 if($h -ne $Pre.nodes.sha256){throw 'NODES_NOT_PRESERVED'}
}
if(!(Test-Path -LiteralPath (Join-Path $Install 'app\dependencies.json'))){throw 'DEPENDENCIES_MISSING'}
[pscustomobject]@{status='PASS';engine=$insE;manifest=$insM;settingsPreserved=[bool]$Pre.settings;nodesPreserved=[bool]$Pre.nodes}|ConvertTo-Json -Compress
