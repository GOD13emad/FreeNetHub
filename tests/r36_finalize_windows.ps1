[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
$InstallRoot=Join-Path $env:LOCALAPPDATA 'Programs\FreeNetHub'
$PrivateRoot=Join-Path $env:LOCALAPPDATA 'FreeNetHub\PrivateBackups\R36_FINAL_20260929'
$Backup=Join-Path $PrivateRoot 'installed-prestate'
$StatePath=Join-Path $env:ProgramData 'FreeNetHub\directdpi\state.json'
$DnsRuntimeDir=Join-Path $env:ProgramData 'FreeNetHub\directdns'
$SourceStart=Join-Path $Root 'app\directdpi\Start-DirectDpi.ps1'
$SourceStop=Join-Path $Root 'app\directdpi\Stop-DirectDpi.ps1'
$CandidateRel='delivery/github_v4.2.0/FreeNetHub_4.2.0_R36_DirectDPI_Final_Setup.exe'
$Candidate=Join-Path $Root ($CandidateRel -replace '/','\')
$CandidateSha='8BDB02AEEC09E8403AFCE6238EDDB1EC7891F7B88357BF3FF113CF6F225FD87A'
$FinalInstaller=$Candidate
$Evidence=Join-Path $Root 'evidence\R36_FINAL_WINDOWS_ACCEPTANCE_20260929.json'
$ReleasePath=Join-Path $Root 'RELEASE.json'
$ReleaseOriginal=[IO.File]::ReadAllBytes($ReleasePath)
$releaseMutated=$false
$finalBuildMade=$false
$script:Interface=''
$script:LocalIp=''

function Is-Admin {
 $id=[Security.Principal.WindowsIdentity]::GetCurrent()
 $p=[Security.Principal.WindowsPrincipal]::new($id)
 return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Assert([bool]$Condition,[string]$Message) {
 if(-not $Condition){throw $Message}
}
function Write-JsonAtomic([string]$Path,$Value) {
 $dir=Split-Path -Parent $Path
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
 [IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
 [IO.File]::Move($tmp,$Path,$true)
}
function Resolve-PhysicalDefaultInterface {
 $routes=@(
  Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
   Where-Object {$_.State -eq 'Alive'} |
   Sort-Object @{Expression={[int]$_.RouteMetric+[int]$_.InterfaceMetric}},RouteMetric,InterfaceMetric
 )
 Assert ($routes.Count -gt 0) 'FINAL_NO_DEFAULT_ROUTE'
 $r=$routes[0]
 $ip=Get-NetIPAddress -InterfaceIndex $r.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object {$_.IPAddress -and $_.IPAddress -notlike '169.254.*'} |
  Select-Object -First 1
 $ad=Get-NetAdapter -InterfaceIndex $r.InterfaceIndex -ErrorAction SilentlyContinue
 Assert ([bool]$ip -and [bool]$ad -and $ad.Status -eq 'Up') 'FINAL_DEFAULT_ROUTE_UNUSABLE'
 Assert ($ad.InterfaceDescription -notmatch '(?i)Wintun|WireGuard|TAP|TUN|VPN|Loopback') 'FINAL_DEFAULT_ROUTE_NOT_PHYSICAL'
 [pscustomobject]@{
  Alias=[string]$ad.Name
  Index=[int]$r.InterfaceIndex
  LocalIp=[string]$ip.IPAddress
  NextHop=[string]$r.NextHop
  Description=[string]$ad.InterfaceDescription
 }
}
function Get-IcsState {
 $s=Get-CimInstance Win32_Service -Filter "Name='SharedAccess'" -ErrorAction SilentlyContinue
 if(-not $s){return [ordered]@{exists=$false;state='';pid=0}}
 [ordered]@{exists=$true;state=[string]$s.State;pid=[int64]$s.ProcessId}
}
function Get-CtrldServiceSummary {
 $s=Get-CimInstance Win32_Service -Filter "Name='ctrld'" -ErrorAction SilentlyContinue
 if(-not $s){return [ordered]@{exists=$false;state='';owned=$false}}
 $installedCtrld=Join-Path $InstallRoot 'app\directdns\ctrld.exe'
 $sourceCtrld=Join-Path $Root 'app\directdns\ctrld.exe'
 $owned=[bool]($s.PathName -and (
  $s.PathName.Contains($installedCtrld,[StringComparison]::OrdinalIgnoreCase) -or
  $s.PathName.Contains($sourceCtrld,[StringComparison]::OrdinalIgnoreCase)
 ))
 [ordered]@{exists=$true;state=[string]$s.State;owned=$owned}
}
function Get-CtrldCatchAll {
 @(
  Get-DnsClientNrptRule -ErrorAction SilentlyContinue |
   Where-Object {
    $ns=@($_.Namespace)|ForEach-Object{[string]$_}
    $sv=@($_.NameServers)|ForEach-Object{[string]$_}
    ($ns -contains '.') -and ($sv -contains '::1')
   } |
   ForEach-Object {
    [ordered]@{
     name=[string]$_.Name
     namespace=@($_.Namespace|ForEach-Object{[string]$_})
     nameServers=@($_.NameServers|ForEach-Object{[string]$_})
    }
   }
 )
}
function Get-OwnedWinDivertCount {
 $roots=@(
  (Join-Path $Root 'app\directdpi'),
  (Join-Path $InstallRoot 'app\directdpi')
 )
 @(
  Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue |
   Where-Object {
    $p=[string]$_.PathName
    $p -and ($roots|Where-Object{$p.Contains($_,[StringComparison]::OrdinalIgnoreCase)})
   }
 ).Count
}
function Get-OwnedWinwsCount {
 $roots=@(
  (Join-Path $Root 'app\directdpi'),
  (Join-Path $InstallRoot 'app\directdpi')
 )
 @(
  Get-Process winws -ErrorAction SilentlyContinue |
   Where-Object {
    try{
     $p=[string]$_.Path
     $p -and ($roots|Where-Object{$p.StartsWith($_,[StringComparison]::OrdinalIgnoreCase)})
    }catch{$false}
   }
 ).Count
}
function Get-OwnedCtrldProcessCount {
 $roots=@(
  (Join-Path $Root 'app\directdns'),
  (Join-Path $InstallRoot 'app\directdns')
 )
 @(
  Get-Process ctrld -ErrorAction SilentlyContinue |
   Where-Object {
    try{
     $p=[string]$_.Path
     $p -and ($roots|Where-Object{$p.StartsWith($_,[StringComparison]::OrdinalIgnoreCase)})
    }catch{$false}
   }
 ).Count
}
function Get-Snapshot {
 $v4=@((Get-DnsClientServerAddress -InterfaceAlias $script:Interface -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses)
 $v6=@((Get-DnsClientServerAddress -InterfaceAlias $script:Interface -AddressFamily IPv6 -ErrorAction SilentlyContinue).ServerAddresses)
 [ordered]@{
  interface=$script:Interface
  localIp=$script:LocalIp
  dnsV4=$v4
  dnsV6=$v6
  stateExists=(Test-Path -LiteralPath $StatePath)
  dnsRuntimeExists=(Test-Path -LiteralPath $DnsRuntimeDir)
  winwsCount=Get-OwnedWinwsCount
  winDivertCount=Get-OwnedWinDivertCount
  ctrldProcessCount=Get-OwnedCtrldProcessCount
  ctrldService=Get-CtrldServiceSummary
  ctrldCatchAll=@(Get-CtrldCatchAll)
  ics=Get-IcsState
  broadRouteCount=@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')}).Count
  winHttpProxy=(netsh winhttp show proxy|Out-String).Trim()
 }
}
function Invoke-PwshFile([string]$Path) {
 Assert (Test-Path -LiteralPath $Path) ('SCRIPT_MISSING_'+(Split-Path $Path -Leaf))
 $out=@(& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $Path 2>&1)
 $code=$LASTEXITCODE
 if($code -ne 0){throw ('SCRIPT_FAIL_'+(Split-Path $Path -Leaf)+'_EXIT_'+$code+'_'+($out -join ' | '))}
 return $out
}
function Stop-FreeNetHubProcesses {
 Get-Process -ErrorAction SilentlyContinue |
  Where-Object {
   try{$_.Path -and $_.Path.StartsWith($InstallRoot,[StringComparison]::OrdinalIgnoreCase)}catch{$false}
  } | Stop-Process -Force -ErrorAction SilentlyContinue
 Start-Sleep -Milliseconds 600
}
function Stop-AnyDirectDpi {
 $need=(Test-Path -LiteralPath $StatePath)
 $svc=Get-CtrldServiceSummary
 if($svc.exists -and $svc.owned){$need=$true}
 if((Get-OwnedCtrldProcessCount) -gt 0){$need=$true}
 if((Get-OwnedWinwsCount) -gt 0){$need=$true}
 if(Test-Path -LiteralPath $DnsRuntimeDir){$need=$true}
 if(-not $need){return}
 $installedStop=Join-Path $InstallRoot 'app\directdpi\Stop-DirectDpi.ps1'
 $stop=if(Test-Path -LiteralPath $installedStop){$installedStop}else{$SourceStop}
 Invoke-PwshFile $stop|Out-Null
}
function Dns-Probe([string]$Name) {
 try{
  $sw=[Diagnostics.Stopwatch]::StartNew()
  $a=@([System.Net.Dns]::GetHostAddresses($Name)|Where-Object AddressFamily -eq InterNetwork|ForEach-Object IPAddressToString|Select-Object -Unique)
  $sw.Stop()
  $private=@($a|Where-Object{$_ -match '^(10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)'})
  [ordered]@{name=$Name;ok=($a.Count -gt 0 -and $private.Count -eq 0);ms=$sw.ElapsedMilliseconds;answers=$a;private=$private}
 }catch{
  [ordered]@{name=$Name;ok=$false;ms=-1;answers=@();private=@();error=$_.Exception.Message}
 }
}
function Curl-Probe([string]$Url,[int]$Timeout=7) {
 $m=& curl.exe -4 --interface $script:LocalIp --noproxy '*' -sS -o NUL -w '%{http_code}|%{remote_ip}|%{time_connect}|%{time_appconnect}|%{time_total}' --max-time $Timeout $Url 2>&1
 [ordered]@{url=$Url;exit=$LASTEXITCODE;meta=($m -join ' ')}
}
function Assert-Probe($p,[string]$Pattern,[string]$Name) {
 Assert ($p.exit -eq 0 -and $p.meta -match $Pattern) ('PROBE_FAIL_'+$Name+'_'+$p.meta)
}
function Assert-DirectRuntime {
 $svc=Get-CtrldServiceSummary
 Assert ($svc.exists -and $svc.owned -and $svc.state -eq 'Running') 'CTRLD_SERVICE_NOT_OWNED_RUNNING'
 $udp=@(Get-NetUDPEndpoint -LocalAddress '::1' -LocalPort 53 -ErrorAction SilentlyContinue)
 $tcp=@(Get-NetTCPConnection -LocalAddress '::1' -LocalPort 53 -State Listen -ErrorAction SilentlyContinue)
 Assert ($udp.Count -gt 0 -and $tcp.Count -gt 0) 'CTRLD_IPV6_LOOPBACK_53_NOT_LISTENING'
 Assert ((Get-OwnedCtrldProcessCount) -gt 0) 'CTRLD_PROCESS_MISSING'
 Assert ((Get-OwnedWinwsCount) -gt 0) 'WINWS_PROCESS_MISSING'
 Assert ((Get-OwnedWinDivertCount) -gt 0) 'WINDIVERT_DRIVER_MISSING'
 Assert (@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')}).Count -eq 0) 'BROAD_ROUTE_PRESENT'
 $proxy=(netsh winhttp show proxy|Out-String)
 Assert ($proxy -match 'Direct access') 'WINHTTP_PROXY_NOT_DIRECT'
 [ordered]@{
  ctrldService=$svc
  udp53=$udp.Count
  tcp53=$tcp.Count
  nrptCatchAll=@(Get-CtrldCatchAll).Count
  winwsCount=Get-OwnedWinwsCount
  winDivertCount=Get-OwnedWinDivertCount
 }
}
function Invoke-Stability([int]$Rounds,[string]$Label) {
 $rows=@()
 for($i=1;$i -le $Rounds;$i++){
  Clear-DnsClientCache -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 250
  foreach($name in @('www.youtube.com','github.com','api.openai.com')){
   $d=Dns-Probe $name
   $rows+=[ordered]@{round=$i;kind='dns';name=$name;ok=$d.ok;ms=$d.ms;answers=$d.answers}
   Assert $d.ok ('DNS_FAIL_'+$Label+'_'+$name+'_R'+$i)
  }
  foreach($spec in @(
   @('youtube','https://www.youtube.com/generate_204','^(200|204)\|'),
   @('openai','https://api.openai.com/v1/models','^(200|401|403)\|'),
   @('github','https://github.com/','^(200|301|302)\|')
  )){
   $p=Curl-Probe $spec[1] 7
   $rows+=[ordered]@{round=$i;kind='https';name=$spec[0];exit=$p.exit;meta=$p.meta}
   Assert-Probe $p $spec[2] ($Label+'_'+$spec[0]+'_R'+$i)
  }
 }
 $cd=Curl-Probe 'https://76.76.10.11/p0' 5
 Assert-Probe $cd '^(200|400)\|' ($Label+'_CONTROL_D')
 [ordered]@{rounds=$Rounds;rows=$rows;controlD=$cd}
}
function Invoke-ChromeYouTube([string]$Label) {
 $chrome=@(
  'C:\Program Files\Google\Chrome\Application\chrome.exe',
  'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
 )|Where-Object{Test-Path $_}|Select-Object -First 1
 Assert ([bool]$chrome) 'CHROME_NOT_FOUND'
 $base=Join-Path $env:LOCALAPPDATA ('FreeNetHub\PrivateRuntime\r36-chrome-'+$Label+'-'+[guid]::NewGuid().ToString('N'))
 $out=$base+'.out.txt'
 $err=$base+'.err.txt'
 New-Item -ItemType Directory -Force -Path (Split-Path $base -Parent)|Out-Null
 $args=@(
  '--headless=new','--disable-gpu','--disable-extensions','--disable-sync',
  '--no-first-run','--no-default-browser-check','--no-proxy-server',
  '--virtual-time-budget=7000',('--user-data-dir='+$base),'--dump-dom','https://www.youtube.com/'
 )
 $p=Start-Process -FilePath $chrome -ArgumentList $args -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
 try{Wait-Process -Id $p.Id -Timeout 16 -ErrorAction Stop}catch{Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}
 Start-Sleep -Milliseconds 400
 $raw=if(Test-Path $out){Get-Content -LiteralPath $out -Raw -ErrorAction SilentlyContinue}else{''}
 $ok=($raw.Length -gt 100000 -and $raw -match '<html' -and $raw -match 'YouTube' -and $raw -notmatch 'ERR_|This site can.t be reached')
 $kids=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'chrome.exe' -and $_.CommandLine -like ('*'+$base+'*')})
 foreach($k in $kids){Stop-Process -Id $k.ProcessId -Force -ErrorAction SilentlyContinue}
 Remove-Item -LiteralPath $base -Recurse -Force -ErrorAction SilentlyContinue
 Remove-Item -LiteralPath $out,$err -Force -ErrorAction SilentlyContinue
 Assert $ok ('CHROME_YOUTUBE_FAIL_'+$Label)
 [ordered]@{label=$Label;bytes=$raw.Length;hasYouTube=($raw -match 'YouTube');errorPage=($raw -match 'ERR_|This site can.t be reached')}
}
function Invoke-Installer([string]$Path) {
 Assert (Test-Path -LiteralPath $Path) 'INSTALLER_MISSING'
 $p=Start-Process -FilePath $Path -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CLOSEAPPLICATIONS') -Wait -PassThru
 Assert ($p.ExitCode -eq 0) ('INSTALLER_EXIT_'+$p.ExitCode)
}
function Invoke-InstalledSmoke {
 $p=Join-Path $InstallRoot 'app\FreeNetHub.ps1'
 Assert (Test-Path -LiteralPath $p) 'INSTALLED_UI_SCRIPT_MISSING'
 $o=@(& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $p -Smoke 2>&1)
 Assert ($LASTEXITCODE -eq 0) ('INSTALLED_SMOKE_FAIL_'+($o -join ' | '))
 $true
}
function Assert-InstalledParity {
 $manifest=Get-Content -LiteralPath (Join-Path $Root 'app\manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $bad=@()
 foreach($f in @($manifest.code)){
  $src=Join-Path (Join-Path $Root 'app') ([string]$f.file)
  $dst=Join-Path (Join-Path $InstallRoot 'app') ([string]$f.file)
  if(-not(Test-Path -LiteralPath $dst)){$bad+=('MISSING_'+$f.file);continue}
  $sh=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
  $dh=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
  if($sh -ne $dh){$bad+=('HASH_'+$f.file)}
 }
 Assert ($bad.Count -eq 0) ('INSTALLED_PARITY_FAIL_'+($bad -join ','))
 $true
}
function Assert-InstalledReleaseParity {
 $a=Get-FileHash -LiteralPath $ReleasePath -Algorithm SHA256
 $b=Get-FileHash -LiteralPath (Join-Path $InstallRoot 'RELEASE.json') -Algorithm SHA256
 Assert ($a.Hash -eq $b.Hash) 'INSTALLED_RELEASE_HASH_MISMATCH'
 $true
}
function Assert-CleanBaseline($Baseline,[string]$Label) {
 $s=Get-Snapshot
 Assert (-not $s.stateExists) ($Label+'_STATE_REMAINS')
 Assert (-not $s.dnsRuntimeExists) ($Label+'_DNS_RUNTIME_REMAINS')
 Assert ($s.winwsCount -eq 0) ($Label+'_WINWS_REMAINS')
 Assert ($s.winDivertCount -eq 0) ($Label+'_WINDIVERT_REMAINS')
 Assert ($s.ctrldProcessCount -eq 0) ($Label+'_CTRLD_PROCESS_REMAINS')
 Assert (-not($s.ctrldService.exists -and $s.ctrldService.owned)) ($Label+'_CTRLD_SERVICE_REMAINS')
 Assert ($s.broadRouteCount -eq 0) ($Label+'_BROAD_ROUTE_REMAINS')
 Assert (($s.dnsV4 -join '|') -eq ($Baseline.dnsV4 -join '|')) ($Label+'_DNSV4_MISMATCH')
 Assert (($s.dnsV6 -join '|') -eq ($Baseline.dnsV6 -join '|')) ($Label+'_DNSV6_MISMATCH')
 Assert ($s.ctrldCatchAll.Count -eq $Baseline.ctrldCatchAll.Count) ($Label+'_NRPT_CATCHALL_MISMATCH')
 if($Baseline.ics.exists){
  Assert ($s.ics.state -eq $Baseline.ics.state -and $s.ics.pid -eq $Baseline.ics.pid) ($Label+'_ICS_CHANGED')
 }
 Assert ($s.winHttpProxy -eq $Baseline.winHttpProxy) ($Label+'_WINHTTP_PROXY_CHANGED')
 [ordered]@{
  dnsV4=$s.dnsV4;dnsV6=$s.dnsV6;nrptCatchAll=$s.ctrldCatchAll.Count
  ics=$s.ics;winHttpProxy=$s.winHttpProxy
 }
}
function Backup-Installed {
 Assert (Test-Path -LiteralPath $InstallRoot) 'INSTALLED_BASELINE_MISSING'
 Stop-FreeNetHubProcesses
 Remove-Item -LiteralPath $Backup -Recurse -Force -ErrorAction SilentlyContinue
 New-Item -ItemType Directory -Force -Path $Backup|Out-Null
 & robocopy.exe $InstallRoot $Backup /MIR /COPY:DAT /DCOPY:DAT /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP|Out-Null
 $rc=$LASTEXITCODE
 Assert ($rc -le 7) ('BACKUP_ROBOCOPY_EXIT_'+$rc)
}
function Restore-InstalledBackup {
 if(-not(Test-Path -LiteralPath $Backup)){return}
 Stop-FreeNetHubProcesses
 New-Item -ItemType Directory -Force -Path $InstallRoot|Out-Null
 & robocopy.exe $Backup $InstallRoot /MIR /COPY:DAT /DCOPY:DAT /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP|Out-Null
 Assert ($LASTEXITCODE -le 7) ('RESTORE_ROBOCOPY_EXIT_'+$LASTEXITCODE)
}
function Set-Prop($Obj,[string]$Name,$Value) {
 if($Obj.PSObject.Properties.Name -contains $Name){$Obj.$Name=$Value}
 else{$Obj|Add-Member -NotePropertyName $Name -NotePropertyValue $Value}
}
function Promote-Release {
 $r=Get-Content -LiteralPath $ReleasePath -Raw -Encoding UTF8|ConvertFrom-Json
 $r.status='LOCAL_ACCEPTED_WINDOWS_4.2_R36_DIRECT_DNS_DPI_UNSIGNED'
 $r.acceptanceEvidence='evidence/R36_FINAL_WINDOWS_ACCEPTANCE_20260929.json'
 $r.installerStatus='LOCAL_ACCEPTED_FINAL_HASH_IN_ACCEPTANCE_EVIDENCE'
 $r.installerSha256=$null
 $r.r36DirectNetwork.status='LOCAL_ACCEPTED_INSTALLED'
 Set-Prop $r.r36DirectNetwork 'directDpiWindows' 'CTRLD_DOH_IPV6_LOOPBACK_NRPT_PLUS_ZAPRET_HOSTLIST_SCOPED'
 Set-Prop $r.r36DirectNetwork 'directDnsEngine' 'CTRLD_1.5.7_PINNED'
 Set-Prop $r.r36DirectNetwork 'directDnsListener' '[::1]:53'
 Set-Prop $r.r36DirectNetwork 'directDnsUpstream' 'CONTROL_D_P0_DOH_76.76.10.11'
 Set-Prop $r.r36DirectNetwork 'directDnsIntercept' 'DNS_MODE_NRPT_PLUS_LOOPBACK_WFP_PROTECT'
 Set-Prop $r.r36DirectNetwork 'directDnsIcsCoexistence' 'PASS_IPV6_LOOPBACK_VS_IPV4_SHAREDACCESS_53'
 Set-Prop $r.r36DirectNetwork 'directDpiLifecycle' 'PASS_START_STOP_EXACT_ROLLBACK_START'
 Set-Prop $r.r36DirectNetwork 'directDpiChrome' 'PASS_DEFAULT_CHROME_YOUTUBE'
 Set-Prop $r.r36DirectNetwork 'directDpiVpnProxy' $false
 Set-Prop $r.r36DirectNetwork 'publicRelease' $false
 $json=$r|ConvertTo-Json -Depth 100
 [IO.File]::WriteAllText($ReleasePath,$json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
}
function Invoke-SecurityScan {
 $py=(Get-Command python.exe -ErrorAction SilentlyContinue)
 Assert ([bool]$py) 'PYTHON_NOT_FOUND_FOR_SECURITY_SCAN'
 $o=@(& $py.Source (Join-Path $Root 'tests\security_scan_public.py') 2>&1)
 Assert ($LASTEXITCODE -eq 0) ('SECURITY_SCAN_FAIL_'+($o -join ' | '))
 $true
}
function Build-FinalInstaller {
 $freeze=@(
  'app\engine.py','app\directnet.py','app\nodehub.py','app\FreeNetHub.ps1','app\View.xaml','app\manifest.json',
  'app\directdpi\Start-DirectDpi.ps1','app\directdpi\Stop-DirectDpi.ps1','app\directdpi\hosts.txt','app\directdpi\LICENSE-zapret.txt',
  'app\directdpi\tools\winws.exe','app\directdpi\tools\WinDivert.dll','app\directdpi\tools\WinDivert64.sys','app\directdpi\tools\cygwin1.dll',
  'app\directdns\ctrld.exe','app\directdns\ctrld.toml','app\directdns\LICENSE-ctrld.txt',
  'gateway\manifest.json','windows\installer\FreeNetHub.iss','Uninstall-FreeNetHub.ps1','RELEASE.json'
 )
 $h=@{}
 foreach($f in $freeze){$h[$f]=(Get-FileHash -LiteralPath (Join-Path $Root $f) -Algorithm SHA256).Hash}
 $iscc=Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
 Assert (Test-Path -LiteralPath $iscc) 'ISCC_NOT_FOUND'
 Remove-Item -LiteralPath $FinalInstaller -Force -ErrorAction SilentlyContinue
 & $iscc /Qp (Join-Path $Root 'windows\installer\FreeNetHub.iss')
 Assert ($LASTEXITCODE -eq 0) ('FINAL_ISCC_EXIT_'+$LASTEXITCODE)
 Assert (Test-Path -LiteralPath $FinalInstaller) 'FINAL_INSTALLER_MISSING'
 foreach($f in $freeze){
  Assert ((Get-FileHash -LiteralPath (Join-Path $Root $f) -Algorithm SHA256).Hash -eq $h[$f]) ('FINAL_SOURCE_CHANGED_'+$f)
 }
 [ordered]@{
  relativePath=$CandidateRel
  bytes=(Get-Item -LiteralPath $FinalInstaller).Length
  sha256=(Get-FileHash -LiteralPath $FinalInstaller -Algorithm SHA256).Hash
  authenticode=[string](Get-AuthenticodeSignature -LiteralPath $FinalInstaller).Status
  frozenFiles=$freeze.Count
 }
}
function Get-InstalledReleaseRevision {
 $p=Join-Path $InstallRoot 'RELEASE.json'
 if(-not(Test-Path -LiteralPath $p)){return ''}
 try{return [string]((Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json).releaseRevision)}catch{return ''}
}

if(-not(Is-Admin)){
 $pwsh=(Get-Command pwsh.exe -ErrorAction Stop).Source
 $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath)
 $p=Start-Process -FilePath $pwsh -Verb RunAs -ArgumentList $args -Wait -PassThru
 exit $p.ExitCode
}

$route=Resolve-PhysicalDefaultInterface
$script:Interface=[string]$route.Alias
$script:LocalIp=[string]$route.LocalIp

$result=[ordered]@{
 schema=2
 date='2026-09-29'
 objective='ONE_ELEVATION_WINDOWS_R36_FINALIZATION'
 status='FAIL'
 candidate=[ordered]@{
  relativePath=$CandidateRel;expectedSha256=$CandidateSha;actualSha256=$null
  parity=$false;releaseParity=$false;uiSmoke=$false
  runtime=$null;stability=$null;chrome=$null;rollback=$null
 }
 baseline=$null
 backup=[ordered]@{
  location='PRIVATE_LOCALAPPDATA'
  created=$false
  installedRevisionBefore=$null
  keyHashes=@()
 }
 promotion=[ordered]@{release=$false;securityScan=$false}
 finalInstaller=$null
 finalInstalled=[ordered]@{
  parity=$false;releaseParity=$false;uiSmoke=$false
  runtime=$null;stability=$null;chrome=$null;active=$false
 }
 rollbackOnFailure=[ordered]@{network=$false;installedBackup=$false;release=$false}
 error=''
}

try{
 Assert (Test-Path -LiteralPath $Candidate) 'CANDIDATE_INSTALLER_MISSING'
 $candHash=(Get-FileHash -LiteralPath $Candidate -Algorithm SHA256).Hash
 $result.candidate.actualSha256=$candHash
 Assert ($candHash -eq $CandidateSha) 'CANDIDATE_INSTALLER_HASH_MISMATCH'

 $result.backup.installedRevisionBefore=Get-InstalledReleaseRevision
 foreach($rel in @('FreeNetHub.exe','app\engine.py','app\FreeNetHub.ps1','app\manifest.json','RELEASE.json')){
  $f=Join-Path $InstallRoot $rel
  if(Test-Path -LiteralPath $f){
   $result.backup.keyHashes+=,[ordered]@{
    file=$rel;sha256=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash;bytes=(Get-Item -LiteralPath $f).Length
   }
  }
 }
 Backup-Installed
 $result.backup.created=$true

 Stop-AnyDirectDpi
 $baseline=Get-Snapshot
 Assert (-not $baseline.stateExists) 'BASELINE_DIRECT_DPI_STATE_PRESENT'
 Assert (-not $baseline.dnsRuntimeExists) 'BASELINE_DIRECT_DNS_RUNTIME_PRESENT'
 Assert ($baseline.winwsCount -eq 0) 'BASELINE_WINWS_PRESENT'
 Assert ($baseline.winDivertCount -eq 0) 'BASELINE_WINDIVERT_PRESENT'
 Assert ($baseline.ctrldProcessCount -eq 0) 'BASELINE_CTRLD_PROCESS_PRESENT'
 Assert (-not($baseline.ctrldService.exists -and $baseline.ctrldService.owned)) 'BASELINE_CTRLD_SERVICE_PRESENT'
 Assert ($baseline.broadRouteCount -eq 0) 'BASELINE_BROAD_ROUTE_PRESENT'
 Assert ($baseline.winHttpProxy -match 'Direct access') 'BASELINE_WINHTTP_PROXY_NOT_DIRECT'
 $result.baseline=[ordered]@{
  interface=$baseline.interface;localIp=$baseline.localIp
  dnsV4=$baseline.dnsV4;dnsV6=$baseline.dnsV6
  nrptCatchAll=$baseline.ctrldCatchAll.Count;ics=$baseline.ics
  broadRouteCount=$baseline.broadRouteCount;winHttpDirect=$true
 }

 Stop-FreeNetHubProcesses
 Invoke-Installer $Candidate
 $result.candidate.parity=Assert-InstalledParity
 $result.candidate.releaseParity=Assert-InstalledReleaseParity
 $result.candidate.uiSmoke=Invoke-InstalledSmoke

 $installedStart=Join-Path $InstallRoot 'app\directdpi\Start-DirectDpi.ps1'
 $installedStop=Join-Path $InstallRoot 'app\directdpi\Stop-DirectDpi.ps1'
 Assert (Test-Path -LiteralPath $installedStart) 'INSTALLED_DIRECT_DPI_START_MISSING'
 Assert (Test-Path -LiteralPath $installedStop) 'INSTALLED_DIRECT_DPI_STOP_MISSING'

 Invoke-PwshFile $installedStart|Out-Null
 $result.candidate.runtime=Assert-DirectRuntime
 $icsLive=Get-IcsState
 if($baseline.ics.exists){Assert ($icsLive.state -eq $baseline.ics.state -and $icsLive.pid -eq $baseline.ics.pid) 'CANDIDATE_ICS_CHANGED'}
 $result.candidate.stability=Invoke-Stability 4 'candidate'
 $result.candidate.chrome=Invoke-ChromeYouTube 'candidate'

 Invoke-PwshFile $installedStop|Out-Null
 $result.candidate.rollback=Assert-CleanBaseline $baseline 'CANDIDATE_ROLLBACK'

 Promote-Release
 $releaseMutated=$true
 $result.promotion.release=$true
 $result.promotion.securityScan=Invoke-SecurityScan
 $result.finalInstaller=Build-FinalInstaller
 $finalBuildMade=$true

 Stop-FreeNetHubProcesses
 Invoke-Installer $FinalInstaller
 $result.finalInstalled.parity=Assert-InstalledParity
 $result.finalInstalled.releaseParity=Assert-InstalledReleaseParity
 $installedRel=Get-Content -LiteralPath (Join-Path $InstallRoot 'RELEASE.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ([string]$installedRel.status -eq 'LOCAL_ACCEPTED_WINDOWS_4.2_R36_DIRECT_DNS_DPI_UNSIGNED') 'FINAL_RELEASE_STATUS_NOT_INSTALLED'
 $result.finalInstalled.uiSmoke=Invoke-InstalledSmoke

 Invoke-PwshFile (Join-Path $InstallRoot 'app\directdpi\Start-DirectDpi.ps1')|Out-Null
 $result.finalInstalled.runtime=Assert-DirectRuntime
 $icsFinal=Get-IcsState
 if($baseline.ics.exists){Assert ($icsFinal.state -eq $baseline.ics.state -and $icsFinal.pid -eq $baseline.ics.pid) 'FINAL_ICS_CHANGED'}
 $result.finalInstalled.stability=Invoke-Stability 3 'final'
 $result.finalInstalled.chrome=Invoke-ChromeYouTube 'final'

 $st=Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ([string]$st.phase -eq 'ACTIVE') 'FINAL_DIRECT_DPI_NOT_ACTIVE'
 $result.finalInstalled.active=$true
 $result.finalInstalled.activeSummary=[ordered]@{
  phase=[string]$st.phase
  interface=[string]$st.interface
  listener='[::1]:53'
  dnsEngine='ctrld 1.5.7'
  dpiEngine='zapret/winws'
  noVpnProxy=$true
 }

 $result.status='PASS'
 Write-JsonAtomic $Evidence $result
 $result|ConvertTo-Json -Depth 40
 exit 0
}catch{
 $result.error=$_.Exception.Message
 try{
  Stop-AnyDirectDpi
  if($result.baseline){
   Assert-CleanBaseline $baseline 'FAILURE_ROLLBACK'|Out-Null
   $result.rollbackOnFailure.network=$true
  }
 }catch{}
 try{
  Restore-InstalledBackup
  $result.rollbackOnFailure.installedBackup=$true
 }catch{}
 if($releaseMutated){
  try{
   [IO.File]::WriteAllBytes($ReleasePath,$ReleaseOriginal)
   $result.rollbackOnFailure.release=$true
  }catch{}
 }
 Write-JsonAtomic $Evidence $result
 $result|ConvertTo-Json -Depth 40
 exit 10
}
