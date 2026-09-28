$ErrorActionPreference='Stop'
$Install=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
Set-Location $Install
$job=[guid]::NewGuid().ToString('N')
& python app\engine.py --action NodeRefreshPublic --mode NODE --job $job --budget 90
$ec=$LASTEXITCODE
$p=Join-Path $Install ('jobs\'+$job+'.json')
if(!(Test-Path -LiteralPath $p)){throw 'REFRESH_JOB_RESULT_MISSING'}
$r=Get-Content -LiteralPath $p -Raw|ConvertFrom-Json -AsHashtable
[pscustomobject]@{job=$job;exit=$ec;result=$r.result}|ConvertTo-Json -Depth 8 -Compress
exit $ec
