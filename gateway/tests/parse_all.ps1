$ErrorActionPreference='Stop'
$files=@(Get-ChildItem -LiteralPath '.\gateway' -File -Filter '*.ps1' | Sort-Object Name | Select-Object -ExpandProperty FullName)
$rows=@()
foreach($p in $files){
 $t=$null;$e=$null
 [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $p),[ref]$t,[ref]$e)|Out-Null
 $rows+=[pscustomobject]@{File=$p;Errors=@($e|ForEach-Object{$_.Message});Count=@($e).Count}
}
$rows|ConvertTo-Json -Compress
