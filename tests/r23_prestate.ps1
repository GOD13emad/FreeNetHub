$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$Out=Join-Path $Root 'delivery\prestate_r23_country_20260928'
New-Item -ItemType Directory -Force -Path $Out|Out-Null
$Installer=Join-Path $Root 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R23_StrictCountry_ShadowHub_Setup.exe'
$Expected='A7DFF977B695ABC608FE5A5D471E41ED1012FA77F490127001A52C52980809B4'
$ih=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
if($ih -ne $Expected){throw 'R23_INSTALLER_HASH_MISMATCH'}
$rec=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');install=$Install;installerSha256=$ih;settings=$null;nodes=$null;installedEngine=$null;installedManifest=$null}
foreach($x in @(@{name='settings';path=(Join-Path $Install 'settings.json')},@{name='nodes';path=(Join-Path $Install 'data\nodes.json')})){
 if(Test-Path -LiteralPath $x.path){
  $dst=Join-Path $Out ([IO.Path]::GetFileName($x.path))
  Copy-Item -LiteralPath $x.path -Destination $dst -Force
  $rec[$x.name]=[ordered]@{path=$x.path;sha256=(Get-FileHash -LiteralPath $x.path -Algorithm SHA256).Hash;bytes=(Get-Item -LiteralPath $x.path).Length;backup=$dst}
 }
}
$ep=Join-Path $Install 'app\engine.py';if(Test-Path $ep){$rec.installedEngine=(Get-FileHash $ep -Algorithm SHA256).Hash}
$mp=Join-Path $Install 'app\manifest.json';if(Test-Path $mp){$rec.installedManifest=(Get-FileHash $mp -Algorithm SHA256).Hash}
$rec|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $Out 'prestate.json') -Encoding utf8
Write-Output ($rec|ConvertTo-Json -Depth 6 -Compress)
