$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Pre=Get-Content -LiteralPath (Join-Path $Root 'delivery\prestate_r25_20260928\prestate.json') -Raw|ConvertFrom-Json
foreach($n in @('engine.py','nodehub.py','manifest.json')){
 $s=Get-FileHash -LiteralPath (Join-Path $Root ('app\'+$n)) -Algorithm SHA256
 $i=Get-FileHash -LiteralPath (Join-Path $Install ('app\'+$n)) -Algorithm SHA256
 if($s.Hash -ne $i.Hash){throw ('INSTALLED_'+$n+'_MISMATCH')}
}
if($Pre.settings){if((Get-FileHash (Join-Path $Install 'settings.json') -Algorithm SHA256).Hash -ne $Pre.settings.sha256){throw 'SETTINGS_NOT_PRESERVED'}}
if($Pre.nodes){if((Get-FileHash (Join-Path $Install 'data\nodes.json') -Algorithm SHA256).Hash -ne $Pre.nodes.sha256){throw 'NODES_NOT_PRESERVED'}}
[pscustomobject]@{status='PASS';engine=(Get-FileHash (Join-Path $Install 'app\engine.py') -Algorithm SHA256).Hash;nodehub=(Get-FileHash (Join-Path $Install 'app\nodehub.py') -Algorithm SHA256).Hash;manifest=(Get-FileHash (Join-Path $Install 'app\manifest.json') -Algorithm SHA256).Hash;settingsPreserved=[bool]$Pre.settings;nodesPreserved=[bool]$Pre.nodes}|ConvertTo-Json -Compress
