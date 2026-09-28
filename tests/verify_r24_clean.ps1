$ErrorActionPreference='Stop'
python -m py_compile app\nodehub.py app\engine.py tests\test_r24_hysteria2.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python tests\test_r24_hysteria2.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python tests\test_nodehub.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python tests\test_country_policy.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python -m unittest discover -s tests -p 'test_*.py'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python -m unittest discover -s gateway\tests -p 'test_*.py'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python crossplatform\common\verify_fail_closed.py
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Write-Output 'R24_STRICT_REGRESSION=PASS'
