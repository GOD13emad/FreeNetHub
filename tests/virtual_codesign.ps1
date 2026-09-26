param(
  [Parameter(Mandatory=$true)][string]$InputPath
)
$ErrorActionPreference='Stop'
$subject='CN=FreeNetHub Virtual Signing Validation'
$probeDir=Join-Path $PSScriptRoot ('.virtual-sign-'+[guid]::NewGuid().ToString('N'))
$cert=$null
New-Item -ItemType Directory -Path $probeDir|Out-Null
$probe=Join-Path $probeDir 'probe.exe'
try {
  Copy-Item -LiteralPath $InputPath -Destination $probe
  $cert=New-SelfSignedCertificate -Subject $subject -Type CodeSigningCert -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddHours(2)
  $signed=Set-AuthenticodeSignature -LiteralPath $probe -Certificate $cert -HashAlgorithm SHA256
  $verify=Get-AuthenticodeSignature -LiteralPath $probe
  $present=($verify.SignerCertificate -and $verify.SignerCertificate.Thumbprint -eq $cert.Thumbprint)
  $changed=((Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $InputPath -Algorithm SHA256).Hash)
  $status=[string]$verify.Status
  $cryptographicSignaturePresent=$present -and $changed -and $status -ne 'NotSigned' -and $status -ne 'HashMismatch'
  [pscustomobject]@{
    schema=3
    status=$(if($cryptographicSignaturePresent){'PASS'}else{'FAIL'})
    trust='SELF_SIGNED_EPHEMERAL_UNTRUSTED'
    signatureStatus=$status
    signerSubject=$verify.SignerCertificate.Subject
    signerThumbprint=$verify.SignerCertificate.Thumbprint
    inputSha256=(Get-FileHash -LiteralPath $InputPath -Algorithm SHA256).Hash
    signedSha256=(Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash
    cryptographicSignaturePresent=$cryptographicSignaturePresent
    productionTrustValidated=$false
  }|ConvertTo-Json -Compress
  if(-not $cryptographicSignaturePresent){throw 'VIRTUAL_CODESIGN_VALIDATION_FAILED'}
}
finally {
  if($cert){
    $oldEA=$ErrorActionPreference
    $ErrorActionPreference='Continue'
    & certutil.exe -user -delstore My $cert.Thumbprint | Out-Null
    $ErrorActionPreference=$oldEA
  }
  if([System.IO.Directory]::Exists($probeDir)){[System.IO.Directory]::Delete($probeDir,$true)}
}
