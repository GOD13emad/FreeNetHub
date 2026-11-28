[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$repoRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$source=Join-Path $repoRoot 'windows\standalone\FreeNetHubShell.cs'
$test=Join-Path $PSScriptRoot 'ShellLaunchContractTest.cs'
$csc=@("$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe","$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe") |
    Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if(-not $csc){ throw 'NET Framework C# compiler is required for this Windows-only test.' }
$work=Join-Path ([IO.Path]::GetTempPath()) ('fnh-shell-contract-test-'+[Guid]::NewGuid().ToString('N'))
New-Item -Path $work -ItemType Directory | Out-Null
try {
    $out=Join-Path $work 'ShellLaunchContractTest.exe'
    & $csc /nologo /optimize+ /platform:anycpu /target:exe /main:ShellLaunchContractTest /r:System.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll ("/out:$out") $source $test
    if($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $out)){throw 'Contract-test compilation failed.'}
    & $out
    if($LASTEXITCODE -ne 0){throw 'Shell launch-contract selftest failed.'}
} finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
