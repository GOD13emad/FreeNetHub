[CmdletBinding()]
param(
 [string]$WarpPlus='',[string]$TorExe='',[string]$Lyrebird='',[string]$TorRc='',[string]$OldRoot='',
 [string]$Browser='',[string]$Pythonw='',[string]$Pwsh='',
 [switch]$InstallMissingRuntime,[string]$ResultPath=''
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Root=(Resolve-Path $PSScriptRoot).Path
$App=Join-Path $Root 'app'
$PF86=[Environment]::GetFolderPath('ProgramFilesX86')
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
function DepObj([string]$Path){
 if(!$Path -or !(Test-Path -LiteralPath $Path -PathType Leaf)){return $null}
 $p=(Resolve-Path -LiteralPath $Path).Path
 [ordered]@{path=$p;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
}
if(!$Pwsh){$Pwsh=Find-Pwsh}
if(!$Pythonw){$Pythonw=Find-Pythonw}
if($InstallMissingRuntime -and !$Pwsh){Install-WingetPackage 'Microsoft.PowerShell';$Pwsh=Find-Pwsh}
if($InstallMissingRuntime -and !$Pythonw){Install-WingetPackage 'Python.Python.3.13';$Pythonw=Find-Pythonw}
if(!$Pwsh){throw 'PWSH_RUNTIME_MISSING'}
if(!$Pythonw){throw 'PYTHONW_RUNTIME_MISSING'}
if(!$Browser){$Browser=Find-Browser}
$lab=Join-Path $env:LOCALAPPDATA 'FreeTunnelLab'
if(!$WarpPlus){$WarpPlus=First-File @((Join-Path $lab 'WarpPlusFast\warp-plus.exe'))}
if(!$TorExe){$TorExe=First-File @((Join-Path $lab 'TorSnowflake\bundle\tor\tor.exe'))}
if(!$Lyrebird){$Lyrebird=First-File @((Join-Path $lab 'TorSnowflake\bundle\tor\pluggable_transports\lyrebird.exe'))}
if(!$TorRc){$TorRc=First-File @((Join-Path $lab 'TorSnowflake\torrc'))}
if(!$OldRoot -and (Test-Path $lab -PathType Container)){$OldRoot=(Resolve-Path $lab).Path}
$Pythonw=(Resolve-Path $Pythonw).Path;$Pwsh=(Resolve-Path $Pwsh).Path
$pythonExe=Join-Path (Split-Path $Pythonw -Parent) 'python.exe'
if(!(Test-Path $pythonExe -PathType Leaf)){throw 'PYTHON_EXE_MISSING_NEXT_TO_PYTHONW'}
$d=[ordered]@{
 schema=2
 pythonw=$Pythonw
 pwsh=$Pwsh
 chrome=$(if($Browser){(Resolve-Path $Browser).Path}else{''})
 warp=(DepObj $WarpPlus)
 tor=(DepObj $TorExe)
 lyrebird=(DepObj $Lyrebird)
 torrc=$(if($TorRc -and (Test-Path $TorRc -PathType Leaf)){(Resolve-Path $TorRc).Path}else{''})
 oldRoot=$(if($OldRoot -and (Test-Path $OldRoot -PathType Container)){(Resolve-Path $OldRoot).Path}else{''})
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
 schema=2;utc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($ec -eq 0){'PASS'}else{'FAIL'})
 dependencies=$out;pythonw=$Pythonw;pwsh=$Pwsh;browser=$d.chrome
 optional=[ordered]@{warp=[bool]$d.warp;tor=[bool]$d.tor;lyrebird=[bool]$d.lyrebird;torrc=[bool]$d.torrc;providerRoot=[bool]$d.oldRoot}
 gatewayCore=$gw
 inventory=$rec
}
if(!$ResultPath){$ResultPath=Join-Path $Root 'INSTALL_RUNTIME_STATUS.json'}
$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $ResultPath -Encoding UTF8
$r|ConvertTo-Json -Depth 12
if($ec -ne 0){exit 20}
