[CmdletBinding()]
param(
 [string]$Browser='',[string]$Pythonw='',[string]$Pwsh='',
 [switch]$InstallMissingRuntime,[string]$ResultPath=''
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=(Resolve-Path $PSScriptRoot).Path
$App=Join-Path $Root 'app'
$Runtime=Join-Path $Root 'runtime'
$PF86=[Environment]::GetFolderPath('ProgramFilesX86')
$WarpSha='FFE76F545317E7E511C9B1723D935F0C0DCA6D355403E30101720F1A5882C47C'
$TorSha='60C45B01938C799862E511A9A5BAB12F959A819C6264A24502EDC342165F570C'
$LyrebirdSha='6E218E85F9A7AE2481F5402DED822471A9A9D0C7E66B05DB3842B93FA5C1F02E'
function First-File([object[]]$Candidates){
 foreach($x in $Candidates){if($x -and (Test-Path -LiteralPath ([string]$x) -PathType Leaf)){return (Resolve-Path -LiteralPath ([string]$x)).Path}}
 return ''
}
function Find-Pwsh{
 $c=@(
  "$env:ProgramFiles\PowerShell\7\pwsh.exe",
  "$env:ProgramFiles\PowerShell\7-preview\pwsh.exe",
  (Get-Command pwsh.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
 )
 try{
  $pkg=Get-AppxPackage -Name Microsoft.PowerShell -ErrorAction SilentlyContinue|Sort-Object Version -Descending|Select-Object -First 1
  if($pkg -and $pkg.InstallLocation){$c+=(Join-Path ([string]$pkg.InstallLocation) 'pwsh.exe')}
 }catch{}
 First-File $c
}
function Find-Pythonw{
 $c=@(
  (Get-Command pythonw.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
  "$env:LOCALAPPDATA\Programs\Python\Python314\pythonw.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
  "$env:ProgramFiles\Python314\pythonw.exe",
  "$env:ProgramFiles\Python313\pythonw.exe",
  "$env:ProgramFiles\Python312\pythonw.exe",
  "C:\Python314\pythonw.exe"
 )
 $p=First-File $c;if($p){return $p}
 $py=Get-Command py.exe -ErrorAction SilentlyContinue
 if($py){
  try{
   $paths=& $py.Source -0p 2>$null
   foreach($line in @($paths)){
    if($line -match '([A-Za-z]:\\.*?python\.exe)\s*$'){
     $w=Join-Path (Split-Path $matches[1] -Parent) 'pythonw.exe'
     if(Test-Path $w -PathType Leaf){return (Resolve-Path $w).Path}
    }
   }
  }catch{}
 }
 return ''
}
function Find-Browser{
 First-File @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  (Join-Path $PF86 'Google\Chrome\Application\chrome.exe'),
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  (Join-Path $PF86 'Microsoft\Edge\Application\msedge.exe'),
  (Get-Command chrome.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
  (Get-Command msedge.exe -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
 )
}
function Install-WingetPackage([string]$Id){
 $wg=Get-Command winget.exe -ErrorAction SilentlyContinue
 if(!$wg){throw ('WINGET_MISSING_FOR_'+$Id)}
 $p=Start-Process -FilePath $wg.Source -ArgumentList @('install','--id',$Id,'--exact','--source','winget','--accept-source-agreements','--accept-package-agreements','--silent','--disable-interactivity') -PassThru -Wait -WindowStyle Hidden
 if($p.ExitCode -ne 0){throw ('WINGET_INSTALL_FAILED_'+$Id+'_'+$p.ExitCode)}
}
function Assert-Pinned([string]$Path,[string]$Sha,[string]$Name){
 if(!(Test-Path -LiteralPath $Path -PathType Leaf)){throw ($Name+'_RUNTIME_MISSING')}
 $actual=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
 if($actual -ne $Sha){throw ($Name+'_RUNTIME_HASH_MISMATCH')}
 return (Resolve-Path -LiteralPath $Path).Path
}
function DepObj([string]$Path){[ordered]@{path=$Path;sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash}}
if(!$Pwsh){$Pwsh=Find-Pwsh}
if(!$Pythonw){$Pythonw=Find-Pythonw}
if($InstallMissingRuntime -and !$Pwsh){Install-WingetPackage 'Microsoft.PowerShell';$Pwsh=Find-Pwsh}
if($InstallMissingRuntime -and !$Pythonw){Install-WingetPackage 'Python.Python.3.13';$Pythonw=Find-Pythonw}
if(!$Pwsh){throw 'PWSH_RUNTIME_MISSING'}
if(!$Pythonw){throw 'PYTHONW_RUNTIME_MISSING'}
if(!$Browser){$Browser=Find-Browser}
$Pythonw=(Resolve-Path $Pythonw).Path;$Pwsh=(Resolve-Path $Pwsh).Path
$pythonExe=Join-Path (Split-Path $Pythonw -Parent) 'python.exe'
if(!(Test-Path $pythonExe -PathType Leaf)){throw 'PYTHON_EXE_MISSING_NEXT_TO_PYTHONW'}

$WarpPlus=Assert-Pinned (Join-Path $Runtime 'WarpPlusFast\warp-plus.exe') $WarpSha 'WARPPLUS'
$TorExe=Assert-Pinned (Join-Path $Runtime 'TorSnowflake\bundle\tor\tor.exe') $TorSha 'TOR'
$Lyrebird=Assert-Pinned (Join-Path $Runtime 'TorSnowflake\bundle\tor\pluggable_transports\lyrebird.exe') $LyrebirdSha 'LYREBIRD'
$GeoIP=Join-Path $Runtime 'TorSnowflake\bundle\data\geoip'
$GeoIPv6=Join-Path $Runtime 'TorSnowflake\bundle\data\geoip6'
if(!(Test-Path -LiteralPath $GeoIP -PathType Leaf)){throw 'TOR_GEOIP_MISSING'}
if(!(Test-Path -LiteralPath $GeoIPv6 -PathType Leaf)){throw 'TOR_GEOIP6_MISSING'}
$TorRc=Join-Path $Runtime 'TorSnowflake\torrc'
$torDir=Split-Path $TorRc -Parent
New-Item -ItemType Directory -Path $torDir -Force|Out-Null
function TorPath([string]$p){return ((Resolve-Path -LiteralPath $p).Path -replace '\\','/')}
$torLines=@(
 'ClientOnly 1',
 'AvoidDiskWrites 1',
 'SocksPolicy accept 127.0.0.1',
 'SocksPolicy reject *',
 'SafeSocks 1',
 'TestSocks 1',
 ('GeoIPFile "'+(TorPath $GeoIP)+'"'),
 ('GeoIPv6File "'+(TorPath $GeoIPv6)+'"'),
 'UseBridges 1',
 ('ClientTransportPlugin meek_lite,obfs4,snowflake,webtunnel exec '+(TorPath $Lyrebird)),
 'Bridge snowflake 192.0.2.3:80 2B280B23E1107BB62ABFC40DDCC8824814F80A72 fingerprint=2B280B23E1107BB62ABFC40DDCC8824814F80A72 url=https://1098762253.rsc.cdn77.org front=www.phpmyadmin.net,cdn.zk.mk ice=stun:stun.antisip.com:3478,stun:stun.epygi.com:3478,stun:stun.uls.co.za:3478,stun:stun.voipgate.com:3478,stun:stun.mixvoip.com:3478,stun:stun.nextcloud.com:3478,stun:stun.bethesda.net:3478,stun:stun.nextcloud.com:443 utls-imitate=hellorandomizedalpn',
 'Log notice stdout'
)
$torLines|Set-Content -LiteralPath $TorRc -Encoding UTF8

$d=[ordered]@{
 schema=3
 runtime='SELF_CONTAINED'
 pythonw=$Pythonw
 pwsh=$Pwsh
 chrome=$(if($Browser){(Resolve-Path $Browser).Path}else{''})
 warp=(DepObj $WarpPlus)
 tor=(DepObj $TorExe)
 lyrebird=(DepObj $Lyrebird)
 torrc=(Resolve-Path $TorRc).Path
 runtimeRoot=$Runtime
}
$out=Join-Path $App 'dependencies.json'
$tmp=$out+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$d|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item $tmp $out -Force
$invJob=[guid]::NewGuid().ToString('N')
& $pythonExe (Join-Path $App 'engine.py') --action Inventory --mode AUTO --job $invJob --budget 30|Out-Null
$ec=$LASTEXITCODE;$recPath=Join-Path $Root ('jobs\'+$invJob+'.json')
$rec=if(Test-Path $recPath){Get-Content $recPath -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
$gwSetup=Join-Path $Root 'gateway\Setup-GatewayCore.ps1'
$gwResult=Join-Path $Root 'gateway\runtime\gateway-core-setup.json'
if(!(Test-Path -LiteralPath $gwSetup -PathType Leaf)){throw 'GATEWAY_CORE_SETUP_MISSING'}
& $Pwsh -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $gwSetup -ResultPath $gwResult|Out-Null
$gwEc=$LASTEXITCODE
$gw=if(Test-Path -LiteralPath $gwResult){Get-Content -LiteralPath $gwResult -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
if($gwEc -ne 0 -or !$gw -or [string]$gw.status -ne 'PASS'){throw ('GATEWAY_CORE_SETUP_FAILED_'+$(if($gw){[string]$gw.error}else{'NO_RESULT'}))}
$r=[ordered]@{
 schema=3;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($ec -eq 0){'PASS'}else{'FAIL'})
 runtime='SELF_CONTAINED';dependencies=$out;pythonw=$Pythonw;pwsh=$Pwsh;browser=$d.chrome
 bundled=[ordered]@{warp=$d.warp;tor=$d.tor;lyrebird=$d.lyrebird;torrc=$d.torrc}
 externalLegacyRuntimeRequired=$false
 gatewayCore=$gw
 inventory=$rec
}
if(!$ResultPath){$ResultPath=Join-Path $Root 'INSTALL_RUNTIME_STATUS.json'}
$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $ResultPath -Encoding UTF8
$r|ConvertTo-Json -Depth 12
if($ec -ne 0){exit 20}
