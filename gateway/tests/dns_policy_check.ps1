$ErrorActionPreference='Stop'
& 'C:\Python314\python.exe' '.\gateway\tests\test_gateway.py'
if($LASTEXITCODE){exit $LASTEXITCODE}
& 'C:\Python314\python.exe' '.\gateway\generate_config.py' --mode PC_TUNNEL --provider WARP --output '.\gateway\runtime\pc_warp.test.json'
if($LASTEXITCODE){exit $LASTEXITCODE}
$sb=(Get-Content '.\gateway\runtime\local_gateway.json' -Raw -Encoding UTF8|ConvertFrom-Json).singbox.path
& $sb check -c '.\gateway\runtime\pc_warp.test.json'
exit $LASTEXITCODE
