[CmdletBinding()]
param(
 [Parameter(Mandatory)][ValidateSet('Start','Verify','Stop','Status')][string]$Action,
 [string]$ProfilePath='',
 [string]$ResultPath=''
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Runtime=Join-Path $PSScriptRoot 'runtime'
$Owner=Join-Path $Runtime 'wsl-console-owner.json'
$Defaults=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
$Console=Get-FnhConsoleConfig $Defaults
$Wsl=Get-FnhWslConfig
$ProviderScript=Join-Path $PSScriptRoot 'console_provider.ps1'
$ProfileValidator=Join-Path $PSScriptRoot 'validate_console_profile.ps1'
$ProviderPort=19594
$LinuxState='/root/.local/state/freenethub'
$LinuxCfg=$LinuxState+'/console-router.json'
$LinuxRunner=$LinuxState+'/console-router.sh'
$LinuxReady=$LinuxState+'/console-ready.env'
$LinuxToken=$LinuxState+'/console-token'
$LinuxPid=$LinuxState+'/console-wrapper.pid'
$LinuxSbPid=$LinuxState+'/console-singbox.pid'
$StepLog=Join-Path $Runtime 'wsl-console-steps.log'
function Step([string]$Name,[object]$Data=$null){$row=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');step=$Name;data=$Data};Add-Content -LiteralPath $StepLog -Value ($row|ConvertTo-Json -Depth 8 -Compress) -Encoding UTF8}
if($ResultPath){$full=[IO.Path]::GetFullPath($ResultPath);$base=[IO.Path]::GetFullPath($Runtime)+'\';if(!$full.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw 'WSL_RESULT_OUTSIDE_RUNTIME'};$ResultPath=$full}else{$ResultPath=Join-Path $Runtime 'wsl-console-result.json'}
function WJ([string]$p,$o){$tmp=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$o|ConvertTo-Json -Depth 24|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item -LiteralPath $tmp -Destination $p -Force}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Require-Admin{if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMIN_REQUIRED'}}
function Trace-Windows{
 $t=& curl.exe -4 --noproxy '*' --max-time 20 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'WINDOWS_TRACE_FAIL'};$d=[ordered]@{};foreach($l in ($t -split '\r?\n')){if($l -match '^([^=]+)=(.*)$'){$d[$matches[1]]=$matches[2]}};return $d
}
function Invoke-Process([string]$File,[string[]]$ArgList,[int]$TimeoutMs=30000){
 $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$File;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
 foreach($a in $ArgList){[void]$psi.ArgumentList.Add($a)}
 $p=[Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();$done=$p.WaitForExit($TimeoutMs);if(!$done){try{$p.Kill($true)}catch{};try{$p.WaitForExit(5000)|Out-Null}catch{}};$o=$ot.GetAwaiter().GetResult();$e=$et.GetAwaiter().GetResult();if(!$done){throw ('PROCESS_TIMEOUT '+[IO.Path]::GetFileName($File))};[pscustomobject]@{exit=$p.ExitCode;stdout=$o;stderr=$e}
}
function Invoke-Wsl([string[]]$ArgList,[int]$TimeoutMs=30000){Invoke-Process 'wsl.exe' (@('-d',$Wsl.distro,'-u','root','--')+$ArgList) $TimeoutMs}
function Invoke-WslBash([string]$Script,[int]$TimeoutMs=30000){$b=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Script.Replace("`r`n","`n")));Invoke-Wsl @('bash','-lc',('echo '+$b+' | base64 -d | bash')) $TimeoutMs}
function Invoke-Usb([string[]]$ArgList,[int]$TimeoutMs=30000){Invoke-Process $Wsl.usbipd.path $ArgList $TimeoutMs}
function Get-UsbDevice{
 $x=Invoke-Usb @('list');Assert ($x.exit -eq 0) 'USBIPD_LIST_FAIL';$rows=@()
 foreach($line in ($x.stdout -split '\r?\n')){
  $parts=@($line.Trim() -split '\s{2,}');if($parts.Count -ge 4 -and $parts[1] -match '^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}$'){
   $rows+=[pscustomobject]@{busid=$parts[0];hardware_id=$parts[1].ToLowerInvariant();description=($parts[2..($parts.Count-2)] -join '  ');state=$parts[-1]}
  }
 }
 $match=@($rows|Where-Object{$_.hardware_id -eq ([string]$Console.hardware_id).ToLowerInvariant()})
 if($match.Count -eq 0){throw 'CONSOLE_USB_DEVICE_NOT_FOUND'}
 if($match.Count -gt 1){$exact=@($match|Where-Object{$_.busid -eq [string]$Console.busid});if($exact.Count -ne 1){throw 'CONSOLE_USB_DEVICE_AMBIGUOUS'};return $exact[0]}
 return $match[0]
}
function Start-WslKeeper{
 $p=Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d',$Wsl.distro,'-u','root','--','sleep','45') -WindowStyle Hidden -PassThru
 Start-Sleep -Milliseconds 900;return $p
}
function Get-WslHostIp{
 $x=Invoke-Wsl @('ip','-4','route','show','default') 15000
 Assert ($x.exit -eq 0) 'WSL_DEFAULT_ROUTE_FAIL';$m=[regex]::Match($x.stdout,'(?m)^default via ([0-9.]+) ');Assert ($m.Success) 'WSL_DEFAULT_GATEWAY_PARSE_FAIL';$ip=$m.Groups[1].Value;Assert ($ip -match '^(?:10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)\d{1,3}\.\d{1,3}$') 'WSL_HOST_IP_INVALID';return $ip
}
function Test-LinuxBinary{
 $x=Invoke-Wsl @('sha256sum',$Wsl.linuxSingBox.path) 15000;Assert ($x.exit -eq 0) 'WSL_SINGBOX_MISSING';$sha=($x.stdout.Trim() -split '\s+')[0].ToUpperInvariant();Assert ($sha -eq [string]$Wsl.linuxSingBox.sha256) 'WSL_SINGBOX_HASH_MISMATCH'
 foreach($c in @('modprobe','nft','python3','curl','base64')){$q=Invoke-Wsl @('sh','-lc',('command -v '+$c+' >/dev/null 2>&1'));Assert ($q.exit -eq 0) ('WSL_TOOL_MISSING_'+$c.ToUpperInvariant())}
}
function Get-LinuxInterface{
 $mac=([string]$Console.mac_address).Replace('-',':').ToLowerInvariant();Assert ($mac -match '^[0-9a-f]{2}(:[0-9a-f]{2}){5}$') 'CONSOLE_MAC_INVALID'
 $code="import glob,pathlib; m='"+$mac+"'; print('\n'.join(pathlib.Path(p).parent.name for p in glob.glob('/sys/class/net/*/address') if pathlib.Path(p).read_text().strip().lower()==m))"
 $x=Invoke-Wsl @('python3','-c',$code) 15000;Assert ($x.exit -eq 0) 'WSL_INTERFACE_QUERY_FAIL';$names=@($x.stdout -split '\r?\n'|Where-Object{$_ -match '^[A-Za-z0-9_.:-]{1,32}$'});Assert ($names.Count -eq 1) 'CONSOLE_WSL_INTERFACE_NOT_FOUND';return $names[0]
}
function Get-Carrier([string]$Iface){$x=Invoke-Wsl @('cat',('/sys/class/net/'+$Iface+'/carrier')) 10000;if($x.exit -eq 0 -and $x.stdout.Trim() -eq '1'){return $true};return $false}
function Provider-Call([string]$Verb,[string]$HostIp){
 $rp=Join-Path $Runtime ('provider-'+[guid]::NewGuid().ToString('N')+'.json')
 $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
 foreach($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$ProviderScript,'-Action',$Verb,'-ListenAddress',$HostIp,'-PortOverride',[string]$ProviderPort,'-ResultPath',$rp)){[void]$psi.ArgumentList.Add($a)}
 $p=[Diagnostics.Process]::Start($psi);$deadline=[DateTime]::UtcNow.AddSeconds(120);$j=$null
 try{
  do{
   if(Test-Path $rp){try{$j=Get-Content $rp -Raw -Encoding UTF8|ConvertFrom-Json}catch{};if($j){break}}
   if($p.HasExited -and !(Test-Path $rp)){break}
   Start-Sleep -Milliseconds 150
  }while([DateTime]::UtcNow -lt $deadline)
  if(!$j){if(-not $p.HasExited){try{$p.Kill($true)}catch{}};throw 'CONSOLE_PROVIDER_RESULT_TIMEOUT'}
  if(-not $p.HasExited){try{$p.WaitForExit(1200)|Out-Null}catch{};if(-not $p.HasExited){try{$p.Kill($true)}catch{}}}
  return [pscustomobject]@{exit=if([string]$j.status -eq 'PASS'){0}else{20};record=$j}
 }finally{Remove-Item $rp -Force -ErrorAction SilentlyContinue}
}
function Test-WslProvider([string]$HostIp){
 $t=Invoke-Wsl @('curl','-4','--socks5-hostname',($HostIp+':'+$ProviderPort),'--max-time','25','-fsS','https://www.cloudflare.com/cdn-cgi/trace') 35000;Assert ($t.exit -eq 0) 'WSL_PROVIDER_TCP_FAIL';$loc='';foreach($l in ($t.stdout -split '\r?\n')){if($l -match '^loc=(.+)$'){$loc=$matches[1].Trim()}};Assert ($loc -eq 'DE') ('WSL_PROVIDER_TCP_COUNTRY_'+$loc)
 $probe=[Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'socks_udp_probe.py')));$code="import base64,sys;sys.argv=['probe','"+$ProviderPort+"','"+$HostIp+"'];exec(base64.b64decode('"+$probe+"'))"
 $u=Invoke-Wsl @('python3','-c',$code) 35000;Assert ($u.exit -eq 0) 'WSL_PROVIDER_UDP_FAIL';$uj=$u.stdout|ConvertFrom-Json
 $g=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ('https://ipwho.is/'+[string]$uj.udp_public_ip) 2>&1|Out-String;Assert ($LASTEXITCODE -eq 0) 'WSL_PROVIDER_UDP_GEO_FAIL';$geo=$g|ConvertFrom-Json;Assert ($geo.success -and [string]$geo.country_code -eq 'DE') ('WSL_PROVIDER_UDP_COUNTRY_'+[string]$geo.country_code)
 return [ordered]@{tcpCountry='DE';udpCountry='DE';udp=$uj}
}
function Test-LocalProviderPortable([string]$HostIp){
 $po=Join-Path $Runtime 'console-provider-owner.json';Assert (Test-Path $po) 'CONSOLE_PROVIDER_OWNER_MISSING';$o=Get-Content $po -Raw -Encoding UTF8|ConvertFrom-Json;$p=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue;Assert ($p -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks) 'CONSOLE_PROVIDER_IDENTITY_MISMATCH';Assert ([string]$o.listen -eq $HostIp -and [int]$o.port -eq $ProviderPort) 'CONSOLE_PROVIDER_BINDING_MISMATCH';Assert ((Test-Path ([string]$o.path)) -and (Get-FileHash ([string]$o.path) -Algorithm SHA256).Hash -eq [string]$o.binarySha256) 'CONSOLE_PROVIDER_BINARY_HASH_MISMATCH';Assert ([bool](Get-NetTCPConnection -State Listen -LocalAddress $HostIp -LocalPort $ProviderPort -OwningProcess ([int]$o.pid) -ErrorAction SilentlyContinue)) 'CONSOLE_PROVIDER_LISTENER_MISSING';return Test-WslProvider $HostIp
}
function Stop-LocalProviderExact{
 $po=Join-Path $Runtime 'console-provider-owner.json';if(!(Test-Path $po)){return}
 $o=Get-Content $po -Raw -Encoding UTF8|ConvertFrom-Json;$p=Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue;Assert ($p -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks) 'CONSOLE_PROVIDER_IDENTITY_MISMATCH'
 Assert ((Test-Path ([string]$o.path)) -and (Get-FileHash ([string]$o.path) -Algorithm SHA256).Hash -eq [string]$o.binarySha256) 'CONSOLE_PROVIDER_BINARY_HASH_MISMATCH'
 $c=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$o.pid) -ErrorAction SilentlyContinue;if($c -and $c.ExecutablePath){Assert ($c.ExecutablePath -eq [string]$o.path) 'CONSOLE_PROVIDER_PATH_MISMATCH'}
 $ls=@(Get-NetTCPConnection -State Listen -LocalAddress ([string]$o.listen) -LocalPort ([int]$o.port) -OwningProcess ([int]$o.pid) -ErrorAction SilentlyContinue);Assert ($ls.Count -gt 0) 'CONSOLE_PROVIDER_LISTENER_IDENTITY_MISMATCH'
 Stop-Process -Id ([int]$o.pid) -Force -ErrorAction Stop;$deadline=[DateTime]::UtcNow.AddSeconds(6);do{if(!(Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue)){break};Start-Sleep -Milliseconds 150}while([DateTime]::UtcNow -lt $deadline);Assert (-not (Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue)) 'CONSOLE_PROVIDER_STOP_INCOMPLETE'
 Remove-Item $po -Force;Assert (@(Get-NetTCPConnection -State Listen -LocalPort ([int]$o.port) -ErrorAction SilentlyContinue).Count -eq 0) 'CONSOLE_PROVIDER_LISTENER_REMAINS'
}
function Test-Owner{
 if(!(Test-Path $Owner)){return $false};try{$o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json;$p=Get-Process -Id ([int]$o.wslPid) -ErrorAction SilentlyContinue;$c=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$o.wslPid) -ErrorAction SilentlyContinue;return [bool]($p -and $c -and $c.Name -ieq 'wsl.exe' -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$o.startTicks -and [string]$o.token -match '^[a-f0-9]{32}$')}catch{return $false}
}
function Read-LinuxReady{
 $x=Invoke-Wsl @('cat',$LinuxReady) 10000;if($x.exit -ne 0){return $null};$d=@{};foreach($l in ($x.stdout -split '\r?\n')){if($l -match '^([A-Z_]+)=(.*)$'){$d[$matches[1]]=$matches[2]}};return $d
}
function Build-LinuxConfig([string]$HostIp,[object]$Profile){
 $rules=@([ordered]@{ip_is_private=$true;action='route';outbound='direct'},[ordered]@{source_ip_cidr=@([string]$Console.subnet);action='route';outbound='provider'})
 $cfg=[ordered]@{log=[ordered]@{level='warn';timestamp=$true};inbounds=@([ordered]@{type='tun';tag='fnh-tun';interface_name='fnh-tun';address=@('172.31.254.1/30');mtu=1400;auto_route=$true;auto_redirect=$true;strict_route=$true;stack='system'});outbounds=@([ordered]@{type='direct';tag='direct'});route=[ordered]@{rules=$rules;final='direct';auto_detect_interface=$true}}
 if($Profile){$cfg.endpoints=@($Profile.endpoint)}else{$cfg.outbounds=@([ordered]@{type='socks';tag='provider';server=$HostIp;server_port=$ProviderPort;version='5'},[ordered]@{type='direct';tag='direct'})}
 return $cfg
}
function Write-LinuxFile([string]$Path,[string]$Text,[string]$Mode='0600'){
 $b=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Text.Replace("`r`n","`n")));$script="mkdir -p '$LinuxState'`nprintf '%s' '$b' | base64 -d > '$Path'`nchmod $Mode '$Path'";$x=Invoke-WslBash $script 20000;Assert ($x.exit -eq 0) ('WSL_WRITE_FAIL '+$Path)
}
function Stop-LinuxOwned([object]$O){
 if(!$O){return}
 $token=[string]$O.token;if($token -notmatch '^[a-f0-9]{32}$'){throw 'WSL_OWNER_TOKEN_INVALID'}
 $cmd=('if [ -r ''{0}'' ] && [ "$(cat ''{0}'')" = ''{1}'' ]; then p=$(cat ''{2}'' 2>/dev/null || true); [ -n "$p" ] && kill -TERM "$p" 2>/dev/null || true; fi' -f $LinuxToken,$token,$LinuxPid)
 try{[void](Invoke-WslBash $cmd 15000)}catch{}
 $p=Get-Process -Id ([int]$O.wslPid) -ErrorAction SilentlyContinue;if($p){$deadline=[DateTime]::UtcNow.AddSeconds(10);do{Start-Sleep -Milliseconds 200;$p=Get-Process -Id ([int]$O.wslPid) -ErrorAction SilentlyContinue}while($p -and [DateTime]::UtcNow -lt $deadline);if($p -and (Test-Owner)){Stop-Process -Id ([int]$O.wslPid) -Force -ErrorAction SilentlyContinue}}
}
function Cleanup-LocalArtifacts([object]$O,[bool]$Detach,[bool]$StopProvider){
 if($O){Stop-LinuxOwned $O}
 try{[void](Invoke-WslBash "nft delete table inet fnh_guard 2>/dev/null || true`nip link show fnh-tun >/dev/null 2>&1 && ip link del fnh-tun 2>/dev/null || true`nrm -f '$LinuxReady' '$LinuxToken' '$LinuxPid' '$LinuxSbPid'" 15000)}catch{}
 if($Detach){try{$d=Get-UsbDevice;if($d.state -eq 'Attached'){[void](Invoke-Usb @('detach','--busid',$d.busid) 30000)}}catch{}}
 if($StopProvider){Stop-LocalProviderExact}
}
function Get-Status{
 $owned=Test-Owner;$o=if(Test-Path $Owner){try{Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json}catch{$null}}else{$null};$usb=$null;$usbError='';try{$usb=Get-UsbDevice}catch{$usbError=$_.Exception.Message};$ready=$null;if($owned){try{$ready=Read-LinuxReady}catch{}}
 $carrier=$false;if($ready -and $ready.ContainsKey('IFACE')){try{$carrier=Get-Carrier ([string]$ready.IFACE)}catch{}}
 [ordered]@{status='PASS';running=$owned;usbError=$usbError;usb=if($usb){[ordered]@{busid=$usb.busid;hardware_id=$usb.hardware_id;description=$usb.description;state=$usb.state}}else{$null};distro=$Wsl.distro;router=if($ready){[ordered]@{iface=$ready.IFACE;uplink=$ready.UPLINK;carrier=$carrier;tokenMatch=($o -and [string]$ready.TOKEN -eq [string]$o.token)}}else{$null};providerKind=if($o){[string]$o.providerKind}else{''};country=if($o){[string]$o.country}else{''};manual=[ordered]@{ip=[string]$Console.suggested_console_ip;prefix=24;gateway=[string]$Console.gateway;dns=[string]$Console.dns}}
}
New-Item -ItemType Directory -Path $Runtime -Force|Out-Null
$out=[ordered]@{schema=1;action=$Action;utc=[DateTimeOffset]::UtcNow.ToString('o');exit=1;result=$null}
try{
 if($Action -eq 'Status'){$out.exit=0;$out.result=Get-Status}
 elseif($Action -eq 'Stop'){
  Require-Admin;$o=if(Test-Path $Owner){Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json}else{$null};$stopProv=[bool]($o -and [string]$o.providerKind -eq 'LOCAL_MIHOMO' -and -not [bool]$o.providerPreexisting);$beforeIp=if($o){[string]$o.windowsIp}else{''};Cleanup-LocalArtifacts $o $true $stopProv;Remove-Item $Owner -Force -ErrorAction SilentlyContinue
  $usbPost=$null;$deadline=[DateTime]::UtcNow.AddSeconds(8);do{try{$usbPost=Get-UsbDevice}catch{$usbPost=$null};if($usbPost -and [string]$usbPost.state -ne 'Attached'){break};Start-Sleep -Milliseconds 300}while([DateTime]::UtcNow -lt $deadline)
  $post=Get-Status;Assert (-not $post.running) 'WSL_CONSOLE_STOP_OWNER_REMAINS';Assert ($usbPost -and [string]$usbPost.state -ne 'Attached') 'WSL_CONSOLE_USB_STILL_ATTACHED';if($stopProv){Assert (!(Test-Path (Join-Path $Runtime 'console-provider-owner.json'))) 'WSL_CONSOLE_PROVIDER_OWNER_REMAINS';Assert (@(Get-NetTCPConnection -State Listen -LocalPort $ProviderPort -ErrorAction SilentlyContinue).Count -eq 0) 'WSL_CONSOLE_PROVIDER_LISTENER_REMAINS'};$lt=Invoke-Wsl @('ip','link','show','fnh-tun') 10000;Assert ($lt.exit -ne 0) 'WSL_CONSOLE_TUN_REMAINS';$ng=Invoke-Wsl @('nft','list','table','inet','fnh_guard') 10000;Assert ($ng.exit -ne 0) 'WSL_CONSOLE_GUARD_REMAINS';$tr=Trace-Windows;if($beforeIp){Assert ([string]$tr.ip -eq $beforeIp -and [string]$tr.warp -eq 'off') 'WSL_CONSOLE_WINDOWS_ROLLBACK_FAIL'};$post.rollback=[ordered]@{usbState=$usbPost.state;providerListener=@(Get-NetTCPConnection -State Listen -LocalPort $ProviderPort -ErrorAction SilentlyContinue).Count;tun=$false;guard=$false;windowsIp=[string]$tr.ip};$out.exit=0;$out.result=$post
 }
 elseif($Action -eq 'Verify'){
  Assert (Test-Owner) 'WSL_CONSOLE_NOT_RUNNING';$o=Get-Content $Owner -Raw -Encoding UTF8|ConvertFrom-Json;$ready=Read-LinuxReady;Assert ($ready -and [string]$ready.TOKEN -eq [string]$o.token) 'WSL_CONSOLE_READY_MISMATCH';$usb=Get-UsbDevice;Assert ([string]$usb.state -eq 'Attached') 'WSL_CONSOLE_USB_NOT_ATTACHED'
  $iface=[string]$ready.IFACE;$carrier=Get-Carrier $iface;$guard=Invoke-Wsl @('nft','list','table','inet','fnh_guard') 10000;Assert ($guard.exit -eq 0) 'WSL_CONSOLE_GUARD_MISSING';$tun=Invoke-Wsl @('ip','link','show','fnh-tun') 10000;Assert ($tun.exit -eq 0) 'WSL_CONSOLE_TUN_MISSING'
  $tr=Trace-Windows;Assert ([string]$tr.ip -eq [string]$o.windowsIp -and [string]$tr.warp -eq 'off') 'WSL_CONSOLE_WINDOWS_ROUTE_CHANGED'
  if([string]$o.providerKind -eq 'LOCAL_MIHOMO'){$pv=Test-LocalProviderPortable ([string]$o.hostIp);Assert ([string]$pv.tcpCountry -eq 'DE' -and [string]$pv.udpCountry -eq 'DE') 'WSL_CONSOLE_PROVIDER_VERIFY_FAIL'}
  $out.exit=0;$out.result=[ordered]@{status='PASS';running=$true;carrier=$carrier;iface=$iface;usbState=$usb.state;guard=$true;tun=$true;windowsTrace=$tr;providerKind=[string]$o.providerKind;country=[string]$o.country}
 }
 else{
  Require-Admin;Assert (-not (Test-Owner)) 'WSL_CONSOLE_ALREADY_RUNNING';if(Test-Path $Owner){Remove-Item $Owner -Force -ErrorAction SilentlyContinue}
  $providerStarted=$false;$attachedByUs=$false;$keeper=$null;$router=$null;$provPre=$false;$hostIp='';$usb=$null;$token=[guid]::NewGuid().ToString('N');Step 'START_BEGIN' @{token=$token};$baseline=Trace-Windows;Assert ([string]$baseline.warp -eq 'off') 'WINDOWS_BASELINE_NOT_DIRECT';Step 'BASELINE_OK' @{ip=$baseline.ip;loc=$baseline.loc}
  try{
   $dist=Invoke-Process 'wsl.exe' @('-l','-q') 15000;Assert ($dist.exit -eq 0 -and @($dist.stdout -split '\r?\n'|ForEach-Object{$_.Trim([char]0).Trim()}|Where-Object{$_ -eq $Wsl.distro}).Count -eq 1) 'WSL_DISTRO_MISSING'
   $keeper=Start-WslKeeper;$hostIp=Get-WslHostIp;Step 'WSL_HOST_OK' @{hostIp=$hostIp;distro=$Wsl.distro};Test-LinuxBinary;Step 'LINUX_BINARY_OK' @{sha=$Wsl.linuxSingBox.sha256}
   $usb=Get-UsbDevice;Step 'USB_DISCOVERED' @{busid=$usb.busid;state=$usb.state;hardware_id=$usb.hardware_id};if([string]$usb.state -eq 'Not shared'){$b=Invoke-Usb @('bind','--busid',$usb.busid) 60000;Assert ($b.exit -eq 0) 'USBIPD_BIND_FAIL';$usb=Get-UsbDevice}
   if([string]$usb.state -eq 'Attached'){throw 'CONSOLE_USB_ALREADY_ATTACHED_EXTERNALLY'}
   Assert ([string]$usb.state -eq 'Shared') 'CONSOLE_USB_NOT_SHARED'
   $a=Invoke-Usb @('attach','--wsl','--busid',$usb.busid,'--host-ip',$hostIp) 45000;Assert ($a.exit -eq 0) ('USBIPD_ATTACH_FAIL '+$a.stderr.Trim());$attachedByUs=$true;Step 'USB_ATTACHED' @{busid=$usb.busid};Start-Sleep -Seconds 2
   foreach($m in $Wsl.modules){$q=Invoke-Wsl @('modprobe',[string]$m) 15000;Assert ($q.exit -eq 0) ('WSL_MODULE_LOAD_FAIL_'+[string]$m)}
   $iface=Get-LinuxInterface;Step 'LINUX_INTERFACE_OK' @{iface=$iface;mac=$Console.mac_address}
   $profile=$null;$providerKind='LOCAL_MIHOMO';$country='DE';$providerVerify=$null
   if($ProfilePath){$pf=(Resolve-Path -LiteralPath $ProfilePath -ErrorAction Stop).Path;$rt=[IO.Path]::GetFullPath($Runtime)+'\';Assert ($pf.StartsWith($rt,[StringComparison]::OrdinalIgnoreCase)) 'PROFILE_MUST_BE_IN_RUNTIME';& pwsh.exe -NoProfile -ExecutionPolicy Bypass -File $ProfileValidator -ProfilePath $pf|Out-Null;Assert ($LASTEXITCODE -eq 0) 'CONSOLE_PROFILE_VALIDATION_FAIL';$profile=Get-Content $pf -Raw -Encoding UTF8|ConvertFrom-Json;Assert ([bool]$profile.capabilities.country_verified -and [bool]$profile.capabilities.tcp -and [bool]$profile.capabilities.udp) 'CONSOLE_PROFILE_NOT_VERIFIED';$providerKind='WIREGUARD_PROFILE';$country=[string]$profile.country;$providerVerify=[ordered]@{profileSha256=(Get-FileHash $pf -Algorithm SHA256).Hash;country=$country}}
   else{
    $po=Join-Path $Runtime 'console-provider-owner.json';if(Test-Path $po){$old=Get-Content $po -Raw -Encoding UTF8|ConvertFrom-Json;if([string]$old.listen -eq $hostIp -and [int]$old.port -eq $ProviderPort){$provPre=$true}else{[void](Provider-Call 'Stop' $hostIp)}}
    $ps=Provider-Call 'Start' $hostIp;Assert ($ps.exit -eq 0 -and $ps.record.status -eq 'PASS' -and [string]$ps.record.verification.tcpCountry -eq 'DE' -and [string]$ps.record.verification.udpCountry -eq 'DE') 'CONSOLE_PROVIDER_START_FAIL';$providerStarted=(-not $provPre);Step 'PROVIDER_WINDOWS_OK' @{tcp=$ps.record.verification.tcpCountry;udp=$ps.record.verification.udpCountry};$providerVerify=Test-WslProvider $hostIp;Step 'PROVIDER_WSL_OK' $providerVerify
   }
   $cfg=Build-LinuxConfig $hostIp $profile;$cfgText=$cfg|ConvertTo-Json -Depth 24 -Compress;Write-LinuxFile $LinuxCfg $cfgText '0600';Step 'LINUX_CONFIG_WRITTEN' @{path=$LinuxCfg}
   $runner=@'
#!/usr/bin/env bash
set -euo pipefail
SB='__SB__'
CFG='__CFG__'
STATE='__STATE__'
READY='__READY__'
TOKENFILE='__TOKENFILE__'
PIDFILE='__PIDFILE__'
SBPIDFILE='__SBPIDFILE__'
TOKEN="$1"
IFACE="$2"
SUBNET='192.168.77.0/24'
GW='192.168.77.1/24'
BASE_FWD="$(cat /proc/sys/net/ipv4/ip_forward)"
UPLINK="$(ip -4 route show default | awk 'NR==1{print $5}')"
cleanup(){
 set +e
 nft delete table inet fnh_guard 2>/dev/null || true
 [ -n "${SBPID:-}" ] && kill "$SBPID" 2>/dev/null || true
 sleep .3
 ip addr del "$GW" dev "$IFACE" 2>/dev/null || true
 echo "$BASE_FWD" > /proc/sys/net/ipv4/ip_forward 2>/dev/null || true
 rm -f "$READY" "$TOKENFILE" "$PIDFILE" "$SBPIDFILE"
}
trap cleanup EXIT INT TERM
mkdir -p "$STATE"
printf '%s' "$TOKEN" > "$TOKENFILE"
printf '%s' "$$" > "$PIDFILE"
ip link set "$IFACE" up
ip addr replace "$GW" dev "$IFACE"
echo 1 > /proc/sys/net/ipv4/ip_forward
"$SB" check -c "$CFG"
"$SB" run -c "$CFG" >>"$STATE/console-router.log" 2>&1 &
SBPID=$!
printf '%s' "$SBPID" > "$SBPIDFILE"
for i in $(seq 1 80); do
 kill -0 "$SBPID" 2>/dev/null || { tail -80 "$STATE/console-router.log"; exit 31; }
 ip link show fnh-tun >/dev/null 2>&1 && break
 sleep .2
done
ip link show fnh-tun >/dev/null 2>&1 || exit 32
nft delete table inet fnh_guard 2>/dev/null || true
nft add table inet fnh_guard
nft 'add chain inet fnh_guard forward { type filter hook forward priority 0; policy accept; }'
nft add rule inet fnh_guard forward iifname "$IFACE" oifname "$UPLINK" drop
CARRIER=0; [ -r "/sys/class/net/$IFACE/carrier" ] && CARRIER="$(cat "/sys/class/net/$IFACE/carrier" 2>/dev/null || echo 0)"
printf 'TOKEN=%s\nIFACE=%s\nUPLINK=%s\nCARRIER=%s\nSBPID=%s\n' "$TOKEN" "$IFACE" "$UPLINK" "$CARRIER" "$SBPID" > "$READY"
wait "$SBPID"
'@
   Step 'RUNNER_TEMPLATE_READY' @{iface=$iface};$runner=$runner.Replace('__SB__',[string]$Wsl.linuxSingBox.path).Replace('__CFG__',$LinuxCfg).Replace('__STATE__',$LinuxState).Replace('__READY__',$LinuxReady).Replace('__TOKENFILE__',$LinuxToken).Replace('__PIDFILE__',$LinuxPid).Replace('__SBPIDFILE__',$LinuxSbPid);Write-LinuxFile $LinuxRunner $runner '0700'
   $stdout=Join-Path $Runtime ('wsl-console-'+$token+'.stdout.log');$stderr=Join-Path $Runtime ('wsl-console-'+$token+'.stderr.log');Step 'RUNNER_WRITTEN' @{path=$LinuxRunner};$router=Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d',$Wsl.distro,'-u','root','--','bash',$LinuxRunner,$token,$iface) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
   if($keeper -and -not $keeper.HasExited){Stop-Process -Id $keeper.Id -Force -ErrorAction SilentlyContinue};$keeper=$null;Step 'ROUTER_PROCESS_STARTED' @{pid=$router.Id}
   $deadline=[DateTime]::UtcNow.AddSeconds(25);$ready=$null;do{if($router.HasExited){$err=if(Test-Path $stderr){Get-Content $stderr -Raw}else{''};throw ('WSL_ROUTER_EXIT_'+$router.ExitCode+' '+$err)};try{$ready=Read-LinuxReady}catch{};if($ready -and [string]$ready.TOKEN -eq $token){break};Start-Sleep -Milliseconds 300}while([DateTime]::UtcNow -lt $deadline);Assert ($ready -and [string]$ready.TOKEN -eq $token) 'WSL_ROUTER_READY_TIMEOUT';Step 'ROUTER_READY' $ready
   $rtun=Invoke-Wsl @('ip','link','show','fnh-tun') 10000;Assert ($rtun.exit -eq 0) 'WSL_ROUTER_TUN_MISSING';$guard=Invoke-Wsl @('nft','list','table','inet','fnh_guard') 10000;Assert ($guard.exit -eq 0) 'WSL_ROUTER_GUARD_MISSING'
   $after=Trace-Windows;Assert ([string]$after.ip -eq [string]$baseline.ip -and [string]$after.warp -eq 'off') 'WINDOWS_ROUTE_CHANGED_BY_CONSOLE';Step 'WINDOWS_DIRECT_CONFIRMED' @{ip=$after.ip;loc=$after.loc}
   $rp=Get-Process -Id $router.Id;$ownerObj=[ordered]@{schema=2;token=$token;wslPid=$router.Id;startTicks=$rp.StartTime.ToUniversalTime().Ticks;distro=$Wsl.distro;busid=$usb.busid;hardware_id=$usb.hardware_id;iface=$iface;mac=[string]$Console.mac_address;hostIp=$hostIp;providerPort=$ProviderPort;providerKind=$providerKind;providerPreexisting=$provPre;country=$country;windowsIp=[string]$baseline.ip;windowsLoc=[string]$baseline.loc;profileSha256=if($profile){(Get-FileHash $ProfilePath -Algorithm SHA256).Hash}else{$null};providerVerify=$providerVerify;created=[DateTimeOffset]::UtcNow.ToString('o')};WJ $Owner $ownerObj;Step 'OWNER_COMMITTED' @{wslPid=$router.Id;iface=$iface;carrier=(Get-Carrier $iface)}
   $out.exit=0;$out.result=[ordered]@{status='PASS';running=$true;state=if(Get-Carrier $iface){'READY_LINK_UP'}else{'READY_WAITING_FOR_CABLE'};carrier=(Get-Carrier $iface);iface=$iface;usbState='Attached';country=$country;providerKind=$providerKind;windowsTrace=$after;manual=[ordered]@{ip=[string]$Console.suggested_console_ip;prefix=24;gateway=[string]$Console.gateway;dns=[string]$Console.dns}}
  }catch{
   if($keeper -and -not $keeper.HasExited){Stop-Process -Id $keeper.Id -Force -ErrorAction SilentlyContinue}
   if($router -and -not $router.HasExited){Stop-Process -Id $router.Id -Force -ErrorAction SilentlyContinue}
   try{[void](Invoke-WslBash "nft delete table inet fnh_guard 2>/dev/null || true`nip link show fnh-tun >/dev/null 2>&1 && ip link del fnh-tun 2>/dev/null || true`nrm -f '$LinuxReady' '$LinuxToken' '$LinuxPid' '$LinuxSbPid'" 15000)}catch{}
   if($attachedByUs -and $usb){try{[void](Invoke-Usb @('detach','--busid',$usb.busid) 30000)}catch{}}
   if($providerStarted){try{Stop-LocalProviderExact}catch{}}
   throw
  }
 }
}catch{$out.exit=20;$out.result=[ordered]@{status='FAIL';error=$_.Exception.Message;current=try{Get-Status}catch{$null}}}
WJ $ResultPath $out
$out|ConvertTo-Json -Depth 24
exit $out.exit
