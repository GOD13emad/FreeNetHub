$ErrorActionPreference='Stop'
foreach($p in '.\gateway\apply_elevated.ps1','.\gateway\stop_elevated.ps1'){
 $t=$null;$e=$null
 [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $p),[ref]$t,[ref]$e)|Out-Null
 if(@($e).Count){$e|ForEach-Object{$_.Message};exit 11}
}
& 'C:\Python314\python.exe' '.\gateway\generate_config.py' --mode CONSOLE_ONLY --provider WARP --target-country NL --allow-unverified-console --output '.\gateway\runtime\console_warp.syntax.json'
if($LASTEXITCODE){exit $LASTEXITCODE}
$sb=(Get-Content '.\gateway\runtime\local_gateway.json' -Raw -Encoding UTF8|ConvertFrom-Json).singbox.path
& $sb check -c '.\gateway\runtime\console_warp.syntax.json'
exit $LASTEXITCODE
