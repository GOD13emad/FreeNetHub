[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
$Pkg=Join-Path $Root 'artifacts\FNH_R36_DIRECT_DPI_FINAL_RUNNER'
$Stop=Join-Path $Pkg 'Stop-And-Restore.ps1'
$Run=Join-Path $Pkg 'Run-DirectDPI.ps1'
$State=Join-Path $Pkg 'state.json'
$Evidence=Join-Path $Root 'evidence\R36_DIRECT_DPI_CYCLE_ACCEPTANCE_20260929.json'
function IsAdmin{$id=[Security.Principal.WindowsIdentity]::GetCurrent();$p=[Security.Principal.WindowsPrincipal]::new($id);$p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)}
function Drivers(){@(Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '^WinDivert'}|Select-Object Name,State,StartMode,PathName)}
function ProjectWinws(){@(Get-CimInstance Win32_Process -Filter "Name='winws.exe'" -ErrorAction SilentlyContinue|Where-Object{$_.ExecutablePath -like '*FreeNetHub*' -or $_.CommandLine -like '*FreeNetHub*'}|Select-Object ProcessId,ExecutablePath,CommandLine)}
function DnsServers([string]$iface){@((Get-DnsClientServerAddress -InterfaceAlias $iface -AddressFamily IPv4 -ErrorAction Stop).ServerAddresses)}
function DohSnapshot(){@(Get-DnsClientDohServerAddress -ErrorAction SilentlyContinue|Where-Object{$_.ServerAddress -in @('76.76.10.11','76.76.2.11')}|Select-Object ServerAddress,DohTemplate,AllowFallbackToUdp,AutoUpgrade)}
function Curl([string]$u,[int]$t=12){$tmp=[IO.Path]::GetTempFileName();try{$m=& curl.exe -4 --interface 192.168.20.5 --noproxy '*' -sS -o $tmp -w '%{http_code}|%{remote_ip}|%{time_total}' --max-time $t $u 2>&1;$e=$LASTEXITCODE;[ordered]@{exit=$e;meta=($m -join [Environment]::NewLine);bytes=(Get-Item $tmp).Length}}finally{Remove-Item $tmp -Force -ErrorAction SilentlyContinue}}
function ChromePath(){
 $pf86=[Environment]::GetFolderPath('ProgramFilesX86')
 foreach($p in @((Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),(Join-Path $pf86 'Google\Chrome\Application\chrome.exe'),(Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe'))){if($p -and (Test-Path -LiteralPath $p)){return $p}}
 return $null
}
function ChromeGate(){
 $chrome=ChromePath;if(-not $chrome){throw 'CHROME_NOT_FOUND'}
 $dir=Join-Path $env:TEMP ('fnh-r36-chrome-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $out=Join-Path $dir 'dom.txt';$err=Join-Path $dir 'err.txt'
 try{
  $args=@('--headless=new','--disable-gpu','--no-first-run','--disable-default-apps','--disable-background-networking',('--user-data-dir='+$dir),'--dump-dom','https://www.youtube.com/')
  $p=Start-Process -FilePath $chrome -ArgumentList $args -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  if(-not $p.WaitForExit(30000)){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue;throw 'CHROME_TIMEOUT'}
  $dom=$(if(Test-Path $out){Get-Content -LiteralPath $out -Raw -ErrorAction SilentlyContinue}else{''})
  $stderr=$(if(Test-Path $err){Get-Content -LiteralPath $err -Raw -ErrorAction SilentlyContinue}else{''})
  $title='';if($dom -match '(?is)<title[^>]*>(.*?)</title>'){$title=($Matches[1] -replace '\s+',' ').Trim()}
  $ok=($title -eq 'YouTube' -and $dom -match 'ytInitialData' -and $dom -notmatch '(?i)ERR_[A-Z_]+|This site can.t be reached')
  return [ordered]@{ok=$ok;exit=$p.ExitCode;title=$title;bytes=[Text.Encoding]::UTF8.GetByteCount($dom);hasYtInitialData=($dom -match 'ytInitialData');hasErrorPage=($dom -match '(?i)ERR_[A-Z_]+|This site can.t be reached');stderrUsbNoise=($stderr -match 'usb_descriptors')}
 }finally{Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue}
}
if(-not(IsAdmin)){
 $a=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath)
 $p=Start-Process pwsh.exe -Verb RunAs -ArgumentList $a -PassThru -Wait
 exit $p.ExitCode
}
if(!(Test-Path $State)){throw 'ACTIVE_STATE_MISSING'}
$saved=Get-Content -LiteralPath $State -Raw|ConvertFrom-Json
$iface=[string]$saved.interface
$expectedPreDns=@($saved.preDns)
$expectedPreDoh=@($saved.preDoh)
$out=[ordered]@{schema=1;date='2026-09-29';status='FAIL';baseline=[ordered]@{activeStateSha256=(Get-FileHash $State -Algorithm SHA256).Hash;pid=$saved.pid;preDns=$expectedPreDns;preDoh=$expectedPreDoh};cleanup=$null;restart=$null;chrome=$null;error=''}
try{
 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Stop
 if($LASTEXITCODE -ne 0){throw ('STOP_EXIT_'+$LASTEXITCODE)}
 Start-Sleep -Seconds 1
 $cleanDns=@(DnsServers $iface);$cleanDoh=@(DohSnapshot);$cleanDrivers=@(Drivers);$cleanWinws=@(ProjectWinws);$split=@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')})
 $dnsExact=(@($cleanDns) -join ',') -eq (@($expectedPreDns) -join ',')
 $doh10=@($cleanDoh|Where-Object ServerAddress -eq '76.76.10.11')
 $doh2=@($cleanDoh|Where-Object ServerAddress -eq '76.76.2.11')
 $pre2=@($expectedPreDoh|Where-Object ServerAddress -eq '76.76.2.11')
 $dohExact=($doh10.Count -eq 0 -and $doh2.Count -eq $pre2.Count)
 if($pre2.Count -eq 1 -and $doh2.Count -eq 1){$dohExact=$dohExact -and ([string]$doh2[0].DohTemplate -eq [string]$pre2[0].DohTemplate) -and ([bool]$doh2[0].AllowFallbackToUdp -eq [bool]$pre2[0].AllowFallbackToUdp) -and ([bool]$doh2[0].AutoUpgrade -eq [bool]$pre2[0].AutoUpgrade)}
 $driverClean=@($cleanDrivers|Where-Object{$_.PathName -like '*FreeNetHub*'}).Count -eq 0
 $winwsClean=$cleanWinws.Count -eq 0
 $out.cleanup=[ordered]@{dns=$cleanDns;dnsExact=$dnsExact;doh=$cleanDoh;dohExact=$dohExact;projectDriverCount=@($cleanDrivers|Where-Object{$_.PathName -like '*FreeNetHub*'}).Count;projectWinwsCount=$cleanWinws.Count;splitRoutes=$split.Count;pass=($dnsExact -and $dohExact -and $driverClean -and $winwsClean -and $split.Count -eq 0)}
 if(-not $out.cleanup.pass){throw 'CLEANUP_NOT_EXACT'}

 & pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Run
 if($LASTEXITCODE -ne 0){throw ('RESTART_EXIT_'+$LASTEXITCODE)}
 Start-Sleep -Seconds 1
 $newState=Get-Content -LiteralPath $State -Raw|ConvertFrom-Json
 $yt=Curl 'https://www.youtube.com/generate_204' 10;$oa=Curl 'https://api.openai.com/v1/models' 8;$gh=Curl 'https://github.com/' 8
 $activeWinws=@(ProjectWinws);$activeDrivers=@(Drivers|Where-Object{$_.PathName -like '*FreeNetHub*'})
 $activeDns=DnsServers $iface
 $activePass=($activeWinws.Count -ge 1 -and $activeDrivers.Count -ge 1 -and (@($activeDns) -join ',') -eq '76.76.10.11,76.76.2.11' -and $yt.exit -eq 0 -and $yt.meta -match '^204\|' -and $oa.meta -match '^(200|401|403)\|' -and $gh.meta -match '^(200|301|302)\|')
 $out.restart=[ordered]@{pid=$newState.pid;dns=$activeDns;projectWinwsCount=$activeWinws.Count;projectDriverCount=$activeDrivers.Count;youtube=$yt;openai=$oa;github=$gh;pass=$activePass}
 if(-not $activePass){throw 'RESTART_ACTIVE_VERIFICATION_FAILED'}
 $cg=ChromeGate;$out.chrome=$cg
 if(-not $cg.ok){throw 'CHROME_GATE_FAILED'}
 $out.status='PASS_CLEANUP_RESTART_CHROME'
}catch{
 $out.error=$_.Exception.Message
 if(-not(Test-Path $State)){
  try{& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Run;$out.recoveryRestartExit=$LASTEXITCODE}catch{$out.recoveryRestartError=$_.Exception.Message}
 }
}finally{
 $out|ConvertTo-Json -Depth 14|Set-Content -LiteralPath $Evidence -Encoding UTF8
}
$out|ConvertTo-Json -Depth 14
if($out.status -ne 'PASS_CLEANUP_RESTART_CHROME'){exit 36}
