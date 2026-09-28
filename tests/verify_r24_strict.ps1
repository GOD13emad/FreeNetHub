$ErrorActionPreference='Stop'
function Run-Checked([string]$Exe,[string[]]$ArgumentList){
 & $Exe @ArgumentList
 $code=$LASTEXITCODE
 if($code -ne 0){throw ("FAILED: "+$Exe+" "+($ArgumentList -join " ")+" exit="+$code)}
}
Run-Checked 'python' @('-m','py_compile','app\nodehub.py','app\engine.py','tests\test_r24_hysteria2.py')
Run-Checked 'python' @('tests\test_r24_hysteria2.py')
Run-Checked 'python' @('tests\test_nodehub.py')
Run-Checked 'python' @('tests\test_country_policy.py')
Run-Checked 'python' @('-m','unittest','discover','-s','tests','-p','test_*.py')
Run-Checked 'python' @('-m','unittest','discover','-s','gateway\tests','-p','test_*.py')
Run-Checked 'python' @('crossplatform\common\verify_fail_closed.py')
Write-Output 'R24_STRICT_REGRESSION=PASS'
