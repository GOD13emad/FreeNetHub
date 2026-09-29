param()
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$result=Join-Path $Root 'evidence\R33_LIVE_NODE_SYSTEM_ACCEPTANCE_20260928.json'
Remove-Item $result -Force -ErrorAction SilentlyContinue
$p=Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Root 'tests\r33_live_node_tun_elevated.ps1'),'-ResultPath',$result) -Verb RunAs -Wait -PassThru
if(!(Test-Path $result)){throw 'R33_LIVE_RESULT_MISSING'}
Get-Content $result -Raw
exit $p.ExitCode
