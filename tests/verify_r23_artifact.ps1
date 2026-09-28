$ErrorActionPreference='Stop'
$p=Join-Path (Split-Path $PSScriptRoot -Parent) 'delivery\github_v4.2.0\FreeNetHub_4.2.0_R23_StrictCountry_ShadowHub_Setup.exe'
if(!(Test-Path -LiteralPath $p)){throw 'R23_INSTALLER_MISSING'}
$h=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
$s=Get-AuthenticodeSignature -LiteralPath $p
$fs=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try {
 $b0=$fs.ReadByte();$b1=$fs.ReadByte();$len=$fs.Length
} finally {$fs.Dispose()}
if($b0 -ne 77 -or $b1 -ne 90){throw 'NOT_PE_MZ'}
Write-Output ('SHA256='+$h)
Write-Output ('BYTES='+$len)
Write-Output ('AUTH='+$s.Status)
Write-Output 'R23_ARTIFACT_VERIFY=PASS'
