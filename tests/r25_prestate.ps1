$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Out=Join-Path $Root 'delivery\prestate_r25_20260928'
New-Item -ItemType Directory -Force -Path $Out|Out-Null
$rec=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');settings=$null;nodes=$null}
foreach($x in @(@{name='settings';path=(Join-Path $Install 'settings.json')},@{name='nodes';path=(Join-Path $Install 'data\nodes.json')})){
 if(Test-Path -LiteralPath $x.path){
  $dst=Join-Path $Out ([IO.Path]::GetFileName($x.path));Copy-Item -LiteralPath $x.path -Destination $dst -Force
  $rec[$x.name]=[ordered]@{sha256=(Get-FileHash -LiteralPath $x.path -Algorithm SHA256).Hash;bytes=(Get-Item -LiteralPath $x.path).Length;backup=$dst}
 }
}
$rec|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $Out 'prestate.json') -Encoding utf8
$rec|ConvertTo-Json -Depth 5 -Compress
