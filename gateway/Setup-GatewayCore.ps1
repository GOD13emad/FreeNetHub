[CmdletBinding()]
param([string]$ResultPath='')
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Gateway=(Resolve-Path $PSScriptRoot).Path
$Runtime=Join-Path $Gateway 'runtime'
$Local=Join-Path $Runtime 'local_gateway.json'
$SbVersion='1.14.0'
$ArchiveSha='3FFB56267DA14E287BE48BD10CF7E6505260125BAD940B75101FBB4D5D58E5D6'
$BinarySha='AAD0EDE010EAFA7B277E520464F3A66FDE820103D737EFF739F40F3CC9451DCC'
function WJ([string]$p,$o){$tmp=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$o|ConvertTo-Json -Depth 16|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -LiteralPath $tmp -Destination $p -Force}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Valid-SingBox([string]$p){
 if(!$p -or !(Test-Path -LiteralPath $p -PathType Leaf)){return $false}
 try{
  if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $BinarySha){return $false}
  $v=& $p version 2>$null|Out-String
  return ($LASTEXITCODE -eq 0 -and $v -match ('sing-box version '+[regex]::Escape($SbVersion)))
 }catch{return $false}
}
function Download-Pinned([string]$Url,[string]$Path,[string]$Sha){
 & curl.exe -L --fail --retry 2 --connect-timeout 15 --max-time 180 -o $Path $Url
 if($LASTEXITCODE -ne 0){throw 'SINGBOX_DOWNLOAD_FAILED'}
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Sha){Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue;throw 'SINGBOX_ARCHIVE_HASH_MISMATCH'}
}
$r=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');status='FAIL';error='';networkMutation=$false;source=''}
try{
 New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
 $dir=Join-Path $Runtime ('bin\sing-box-'+$SbVersion);$target=Join-Path $dir 'sing-box.exe'
 if(!(Valid-SingBox $target)){
  $candidates=@()
  if(Test-Path -LiteralPath $Local){
   try{$old=Get-Content -LiteralPath $Local -Raw -Encoding UTF8|ConvertFrom-Json;if(($old.PSObject.Properties.Name -contains 'singbox') -and $old.singbox -and ($old.singbox.PSObject.Properties.Name -contains 'path') -and $old.singbox.path){$candidates+=[string]$old.singbox.path}}catch{}
  }
  $src=$candidates|Where-Object{Valid-SingBox $_}|Select-Object -First 1
  if($src){
   New-Item -ItemType Directory -Path $dir -Force|Out-Null;Copy-Item -LiteralPath $src -Destination $target -Force;$r.source='REUSED_PINNED_LOCAL'
  }else{
   $tmp=Join-Path $env:TEMP ('FreeNetHub-core-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $tmp -Force|Out-Null
   try{
    $zip=Join-Path $tmp 'sing-box.zip'
    Download-Pinned ('https://github.com/SagerNet/sing-box/releases/download/v'+$SbVersion+'/sing-box-'+$SbVersion+'-windows-amd64.zip') $zip $ArchiveSha
    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
    $bin=Get-ChildItem -LiteralPath $tmp -Recurse -File -Filter sing-box.exe|Select-Object -First 1
    Assert ($null -ne $bin) 'SINGBOX_BINARY_NOT_FOUND'
    Assert ((Get-FileHash -LiteralPath $bin.FullName -Algorithm SHA256).Hash -eq $BinarySha) 'SINGBOX_BINARY_HASH_MISMATCH'
    New-Item -ItemType Directory -Path $dir -Force|Out-Null;Copy-Item -LiteralPath $bin.FullName -Destination $target -Force;$r.source='DOWNLOADED_PINNED_RELEASE'
   }finally{Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue}
  }
 }
 Assert (Valid-SingBox $target) 'SINGBOX_RUNTIME_VALIDATION_FAIL'
 $old=$null;if(Test-Path -LiteralPath $Local){try{$old=Get-Content -LiteralPath $Local -Raw -Encoding UTF8|ConvertFrom-Json}catch{}}
 $cfg=[ordered]@{schema=$(if($old -and [int]$old.schema -ge 2){2}else{1});singbox=[ordered]@{path=(Resolve-Path -LiteralPath $target).Path;sha256=$BinarySha;version=$SbVersion;archiveSha256=$ArchiveSha}}
 if($old -and ($old.PSObject.Properties.Name -contains 'console') -and $old.console){$cfg.console=$old.console}
 if($old -and ($old.PSObject.Properties.Name -contains 'wsl') -and $old.wsl){$cfg.wsl=$old.wsl;$cfg.schema=2}
 WJ $Local $cfg
 $r.status='PASS';$r.path=(Resolve-Path -LiteralPath $target).Path;$r.sha256=$BinarySha;$r.version=$SbVersion;$r.localGateway=$Local
}catch{$r.error=$_.Exception.Message}
if(!$ResultPath){$ResultPath=Join-Path $Runtime 'gateway-core-setup.json'}
WJ $ResultPath $r
$r|ConvertTo-Json -Depth 12
if($r.status -ne 'PASS'){exit 20}
