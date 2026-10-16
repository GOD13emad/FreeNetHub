[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$Gateway=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $Gateway 'runtime_config.ps1')
foreach($name in @('apply_elevated.ps1','stop_elevated.ps1')){
 $path=Join-Path $Gateway $name
 $tokens=$null;$errors=$null
 [System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)|Out-Null
 if(@($errors).Count){$errors|ForEach-Object{$_.Message};throw ('GATEWAY_POWERSHELL_PARSE_FAILED '+$name)}
}
$Python=if(Test-Path -LiteralPath (Join-Path (Split-Path $Gateway -Parent) 'app\dependencies.json')){Get-FnhPython}else{
 $cmd=Get-Command python.exe -ErrorAction SilentlyContinue
 if(!$cmd){throw 'PYTHON_RUNTIME_MISSING'}
 $cmd.Source
}
$SingBox=Get-FnhSingBox
$Config=Join-Path ([IO.Path]::GetTempPath()) ('fnh-gateway-syntax-'+[guid]::NewGuid().ToString('N')+'.json')
try{
 & $Python (Join-Path $Gateway 'generate_config.py') --mode CONSOLE_ONLY --provider WARP --target-country NL --allow-unverified-console --output $Config
 if($LASTEXITCODE -ne 0){throw ('GATEWAY_CONFIG_GENERATION_FAILED_'+$LASTEXITCODE)}
 & $SingBox.path check -c $Config
 if($LASTEXITCODE -ne 0){throw ('SINGBOX_CONFIG_CHECK_FAILED_'+$LASTEXITCODE)}
}finally{
 Remove-Item -LiteralPath $Config -Force -ErrorAction SilentlyContinue
}
