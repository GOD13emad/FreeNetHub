$ErrorActionPreference='Stop'
$files='.\gateway\preflight.ps1','.\gateway\apply_elevated.ps1','.\gateway\stop_elevated.ps1','.\gateway\Start-Gateway.ps1','.\gateway\Stop-Gateway.ps1'
$rows=@()
foreach($p in $files){
 $t=$null;$e=$null
 [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $p),[ref]$t,[ref]$e)|Out-Null
 $rows+=[pscustomobject]@{File=$p;Errors=@($e|ForEach-Object{$_.Message});Count=@($e).Count}
}
$rows|ConvertTo-Json -Compress
