$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Helper=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\windows\installer\Prepare-SelectiveUpgrade.ps1')).Path
$Temp=Join-Path ([IO.Path]::GetTempPath()) ('fnh-selective-preflight-'+[guid]::NewGuid().ToString('N'))
$Policy=Join-Path $Temp 'data\selective_windows\policy.json'
$Reg=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction Stop
if($Reg.PSObject.Properties['AutoConfigURL'] -and [string]$Reg.PSObject.Properties['AutoConfigURL'].Value -like 'http://127.0.0.1:19416/route.pac*'){
 throw 'UNSAFE_RUNNER_PAC_PRESTATE'
}
function Test-ExpectedExit([string]$tag,[int]$want){
 $proc=& pwsh.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Helper -AppRoot $Temp 2>&1
 $got=$LASTEXITCODE
 if($got -ne $want){throw ("SELECTIVE_UPGRADE_GUARD_"+$tag+"_EXPECTED_"+$want+"_GOT_"+$got)}
 Write-Output ("SELECTIVE_UPGRADE_GUARD_"+$tag+"_PASS")
}
try{
 [IO.Directory]::CreateDirectory((Split-Path $Policy -Parent))|Out-Null
 Test-ExpectedExit 'NO_STATE' 0
 '{"schema":1,"enabled":false,"inFlight":false}'|Set-Content -LiteralPath $Policy -Encoding UTF8
 Test-ExpectedExit 'DISABLED' 0
 '{"schema":1,"enabled":true,"inFlight":false}'|Set-Content -LiteralPath $Policy -Encoding UTF8
 Test-ExpectedExit 'ACTIVE_BLOCKED' 42
 '{"schema":1,"enabled":false,"inFlight":true}'|Set-Content -LiteralPath $Policy -Encoding UTF8
 Test-ExpectedExit 'INTERRUPTED_BLOCKED' 42
 '{"schema":1,"enabled":"false"}'|Set-Content -LiteralPath $Policy -Encoding UTF8
 Test-ExpectedExit 'UNTRUSTED_TYPE_BLOCKED' 42
 '{"schema":1,"enabled":false'|Set-Content -LiteralPath $Policy -Encoding UTF8
 Test-ExpectedExit 'CORRUPT_BLOCKED' 42
}finally{
 if((Test-Path -LiteralPath $Temp) -and (Split-Path $Temp -Parent) -eq [IO.Path]::GetTempPath().TrimEnd('\')){
  Remove-Item -LiteralPath $Temp -Recurse -Force
 }
}
# Nested pwsh fixtures intentionally exit 42 in blocked cases. Return an
# explicit success code so GitHub Actions does not inherit their LASTEXITCODE.
exit 0
