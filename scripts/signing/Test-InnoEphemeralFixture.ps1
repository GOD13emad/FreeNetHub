# CI-ONLY throwaway Windows Inno+SignTool integration validation.
# The ephemeral SELF-SIGNED certificate never becomes a public CA trust credential.
# Only a harmless generated fixture is installed, on the disposable GitHub runner.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-Tool([string]$Name) {
  $p = Get-Command $Name -ErrorAction SilentlyContinue
  if ($p) { return $p.Source }
  if ($Name -eq 'signtool.exe') {
    $sdk = Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $sdk) {
      $c = @(Get-ChildItem -LiteralPath $sdk -Recurse -Filter 'signtool.exe' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -match '\\x64$' } | Sort-Object FullName -Descending)
      if ($c.Count) { return $c[0].FullName }
    }
  }
  if ($Name -eq 'ISCC.exe') {
    $candidates = @(
      (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
      (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
      (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Inno Setup 6\ISCC.exe')
    )
    $c = @($candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) })
    if ($c.Count) { return $c[0] }
  }
  throw ('CI_TOOL_MISSING_'+$Name)
}

$work = Join-Path $env:RUNNER_TEMP ('fnh-inno-ephemeral-'+[guid]::NewGuid().ToString('N'))
$install = Join-Path $work 'install'
$dist = Join-Path $work 'dist'
$cert = $null
try {
  New-Item -ItemType Directory -Path $work,$dist -Force | Out-Null
  $iscc = Find-Tool 'ISCC.exe'
  $signTool = Find-Tool 'signtool.exe'
  $subject = 'CN=FNH EPHEMERAL CI FIXTURE NEVER PUBLICLY TRUSTED'
  $cert = New-SelfSignedCertificate -Subject $subject -Type CodeSigningCert -NotAfter (Get-Date).AddHours(2) -CertStoreLocation 'Cert:\CurrentUser\My'
  if (!$cert -or !$cert.HasPrivateKey -or $cert.Issuer -ne $cert.Subject) { throw 'SELF_SIGNED_ONLY_CI_GUARD' }
  $thumb = $cert.Thumbprint
  $text = Join-Path $work 'payload.txt'
  Set-Content -LiteralPath $text -Encoding ascii -Value 'SAFE_NON_EXECUTABLE_FIXTURE_ONLY'
  $file = Join-Path $work 'fixture.iss'
  $out = Join-Path $dist 'FnhInnoEphemeralSetup.exe'
  $script = @"
[Setup]
AppName=FNH Ephemeral Signing Fixture
AppVersion=0.0.0.1
DefaultDirName={localappdata}\FNH_EPHEMERAL_CI_TEST
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=$dist
OutputBaseFilename=FnhInnoEphemeralSetup
SignTool=fixture
SignedUninstaller=yes
Uninstallable=yes
[Files]
Source: "$text"; DestDir: "{app}"; Flags: ignoreversion
"@
  Set-Content -LiteralPath $file -Value $script -NoNewline -Encoding UTF8
  # The Inno $q special value avoids Windows-native argument parsing issues
  # for a SignTool.exe path containing whitespace; $f is substituted by ISCC.
  $signDef = '/Sfixture=' + '$q' + $signTool + '$q' + ' sign /sha1 ' + $thumb + ' /fd SHA256 $f'
  & $iscc /Qp /NI $signDef $file
  if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $out)) { throw 'INNO_FIXTURE_SIGNED_BUILD_FAILED' }
  $setupSig=Get-AuthenticodeSignature -LiteralPath $out
  if (!$setupSig.SignerCertificate -or $setupSig.SignerCertificate.Thumbprint -ine $thumb -or
      $setupSig.Status -in @('NotSigned','HashMismatch')) {throw ('EPHEMERAL_SETUP_SIGNATURE_MISSING_'+$setupSig.Status)}
  $proc = Start-Process -FilePath $out -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',("/DIR="+$install)) -PassThru -Wait
  if ($proc.ExitCode -ne 0) { throw ('EPHEMERAL_FIXTURE_INSTALL_FAILED_'+$proc.ExitCode) }
  $uninstaller=@(Get-ChildItem -LiteralPath $install -Filter 'unins*.exe' -File)
  if ($uninstaller.Count -ne 1) { throw 'SIGNABLE_INNO_UNINSTALLER_NOT_FOUND' }
  $unSig=Get-AuthenticodeSignature -LiteralPath $uninstaller[0].FullName
  if (!$unSig.SignerCertificate -or $unSig.SignerCertificate.Thumbprint -ine $thumb -or
      $unSig.Status -in @('NotSigned','HashMismatch')) {throw ('EPHEMERAL_UNINSTALLER_SIGNATURE_MISSING_'+$unSig.Status)}
  $unProc=Start-Process -FilePath $uninstaller[0].FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -PassThru -Wait
  if ($unProc.ExitCode -ne 0) {throw ('EPHEMERAL_UNINSTALL_FAILED_'+$unProc.ExitCode)}
  [pscustomobject]@{
    verdict='CI_EPHEMERAL_INNO_SETUP_AND_UNINSTALLER_CRYPTOSIGN_PASS'
    certificateTrust='SELF_SIGNED_EPHEMERAL_NOT_PUBLIC_TRUST'
    setupSignatureStatus=[string]$setupSig.Status
    uninstallerSignatureStatus=[string]$unSig.Status
    setupSHA256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash
    publicCertificatePresent=$false
    r52Built=$false
    smartAppControlValidated=$false
    localMachineRootStoreModified=$false
  } | ConvertTo-Json -Depth 4
} finally {
  if ($cert) {
    $localCert=Join-Path 'Cert:\CurrentUser\My' $cert.Thumbprint
    if (Test-Path -LiteralPath $localCert) {Remove-Item -LiteralPath $localCert -DeleteKey -Force}
  }
  if (Test-Path -LiteralPath $work) {Remove-Item -LiteralPath $work -Recurse -Force}
}
