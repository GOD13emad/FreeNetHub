param(
  [Parameter(Mandatory=$true)][string]$InputPath
)
$ErrorActionPreference='Stop'
$subject='CN=FreeNetHub Virtual Signing Validation'
$probeDir=Join-Path $PSScriptRoot ('.virtual-sign-'+[guid]::NewGuid().ToString('N'))
$cert=$null
$rootCert=$null
New-Item -ItemType Directory -Path $probeDir|Out-Null
$probe=Join-Path $probeDir 'probe.exe'
$cer=Join-Path $probeDir 'virtual-signing.cer'
try {
  Copy-Item -LiteralPath $InputPath -Destination $probe
  $cert=New-SelfSignedCertificate -Subject $subject -Type CodeSigningCert -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddHours(2)
  Export-Certificate -Cert $cert -FilePath $cer|Out-Null
  $rootCert=Import-Certificate -FilePath $cer -CertStoreLocation 'Cert:\CurrentUser\Root'
  $signed=Set-AuthenticodeSignature -LiteralPath $probe -Certificate $cert -HashAlgorithm SHA256
  $verify=Get-AuthenticodeSignature -LiteralPath $probe
  $present=($verify.SignerCertificate -and $verify.SignerCertificate.Thumbprint -eq $cert.Thumbprint)
  $changed=((Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $InputPath -Algorithm SHA256).Hash)
  $valid=($verify.Status -eq 'Valid')
  [pscustomobject]@{
    schema=2
    status=$(if($present -and $changed -and $valid){'PASS'}else{'FAIL'})
    trust='EPHEMERAL_SELF_SIGNED_TEMPORARILY_TRUSTED'
    signatureStatus=[string]$verify.Status
    signerSubject=$verify.SignerCertificate.Subject
    signerThumbprint=$verify.SignerCertificate.Thumbprint
    inputSha256=(Get-FileHash -LiteralPath $InputPath -Algorithm SHA256).Hash
    signedSha256=(Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash
    cryptographicSignaturePresent=$present
    trustValidationPassed=$valid
  }|ConvertTo-Json -Compress
  if(-not ($present -and $changed -and $valid)){throw 'VIRTUAL_CODESIGN_VALIDATION_FAILED'}
}
finally {
  if($cert){
    $oldEA=$ErrorActionPreference
    $ErrorActionPreference='Continue'
    & certutil.exe -user -delstore Root $cert.Thumbprint | Out-Null
    & certutil.exe -user -delstore My $cert.Thumbprint | Out-Null
    $ErrorActionPreference=$oldEA
  }
  if([System.IO.Directory]::Exists($probeDir)){[System.IO.Directory]::Delete($probeDir,$true)}
}
