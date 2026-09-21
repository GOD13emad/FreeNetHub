[CmdletBinding()]
param(
 [switch]$InstallPrerequisites,
 [string]$Distro='',
 [string]$HardwareId='',
 [string]$ResultPath=''
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$Gateway=(Resolve-Path $PSScriptRoot).Path
$Root=(Split-Path $Gateway -Parent)
$Runtime=Join-Path $Gateway 'runtime'
$Local=Join-Path $Runtime 'local_gateway.json'
$SbVersion='1.14.0'
$WinArchiveSha='3FFB56267DA14E287BE48BD10CF7E6505260125BAD940B75101FBB4D5D58E5D6'
$LinuxArchiveSha='2375DE6999F4F56AB46B4FC5DDF26A6ABA1D3E61A0F4E7DDEC2F4690457D5F63'
$LinuxBinarySha='57B3DA14E264B6E05E8F46AEE027C02D7DD7F1594D19AA39E2F4D2B9459BBD04'
$UsbMsiSha='1C984914AEC944DE19B64EFF232421439629699F8138E3DDC29301175BC6D938'
$UsbVersion='5.3.0'
function WJ([string]$p,$o){$tmp=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';$o|ConvertTo-Json -Depth 16|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item $tmp $p -Force}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Require-Admin{
 $a=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
 if(!$a){throw 'ADMIN_REQUIRED'}
}
function Run([string]$File,[string[]]$ArgList,[int]$TimeoutMs=120000){
 $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$File;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
 foreach($a in $ArgList){[void]$psi.ArgumentList.Add($a)}
 $p=[Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();$done=$p.WaitForExit($TimeoutMs)
 if(!$done){try{$p.Kill($true)}catch{};try{$p.WaitForExit(3000)|Out-Null}catch{}}
 $o=$ot.GetAwaiter().GetResult();$e=$et.GetAwaiter().GetResult()
 if(!$done){throw ('PROCESS_TIMEOUT_'+[IO.Path]::GetFileName($File))}
 [pscustomobject]@{exit=$p.ExitCode;stdout=$o;stderr=$e}
}
function Wsl([string[]]$ArgList,[int]$TimeoutMs=120000){Run 'wsl.exe' (@('-d',$script:DistroName,'-u','root','--')+$ArgList) $TimeoutMs}
function Download-Pinned([string]$Url,[string]$Path,[string]$Sha){
 New-Item -ItemType Directory -Path (Split-Path $Path -Parent) -Force|Out-Null
 & curl.exe -L --fail --retry 2 --connect-timeout 15 --max-time 180 -o $Path $Url
 if($LASTEXITCODE -ne 0){throw 'DOWNLOAD_FAILED'}
 $h=(Get-FileHash $Path -Algorithm SHA256).Hash
 if($h -ne $Sha){Remove-Item $Path -Force -ErrorAction SilentlyContinue;throw 'DOWNLOAD_HASH_MISMATCH'}
 return $h
}
function Get-Distros{
 $x=Run 'wsl.exe' @('-l','-q') 20000
 if($x.exit -ne 0){return @()}
 @($x.stdout.Replace([char]0,'') -split '\r?\n'|ForEach-Object{$_.Trim()}|Where-Object{$_})
}
function Find-Usbipd{
 foreach($p in @('C:\Program Files\usbipd-win\usbipd.exe','C:\Program Files (x86)\usbipd-win\usbipd.exe')){if(Test-Path $p -PathType Leaf){return (Resolve-Path $p).Path}}
 return ''
}
function Usb-Rows([string]$Usb){
 $x=Run $Usb @('list') 20000;Assert ($x.exit -eq 0) 'USBIPD_LIST_FAIL';$rows=@()
 foreach($line in ($x.stdout -split '\r?\n')){
  $parts=@($line.Trim() -split '\s{2,}')
  if($parts.Count -ge 4 -and $parts[1] -match '^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}$'){
   $rows+=[pscustomobject]@{busid=$parts[0];hardware_id=$parts[1].ToLowerInvariant();description=($parts[2..($parts.Count-2)] -join '  ');state=$parts[-1]}
  }
 }
 return $rows
}
$r=[ordered]@{schema=2;utc=[DateTimeOffset]::UtcNow.ToString('o');status='FAIL';error='';steps=@();networkMutation=$false}
try{
 Require-Admin;New-Item -ItemType Directory -Path $Runtime -Force|Out-Null

 $winDir=Join-Path $Runtime ('bin\sing-box-'+$SbVersion);$winSb=Join-Path $winDir 'sing-box.exe'
 $needWin=$true
 if(Test-Path $winSb -PathType Leaf){
  $v=Run $winSb @('version') 15000
  if($v.exit -eq 0 -and $v.stdout -match ('sing-box version '+[regex]::Escape($SbVersion))){$needWin=$false}
 }
 if($needWin){
  $tmp=Join-Path $env:TEMP ('FreeNetHub-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $tmp -Force|Out-Null
  try{
   $zip=Join-Path $tmp 'sing-box-windows.zip'
   [void](Download-Pinned ('https://github.com/SagerNet/sing-box/releases/download/v'+$SbVersion+'/sing-box-'+$SbVersion+'-windows-amd64.zip') $zip $WinArchiveSha)
   Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
   $src=Get-ChildItem $tmp -Recurse -File -Filter sing-box.exe|Select-Object -First 1
   Assert ($null -ne $src) 'WINDOWS_SINGBOX_BINARY_NOT_FOUND'
   New-Item -ItemType Directory -Path $winDir -Force|Out-Null;Copy-Item $src.FullName $winSb -Force
  }finally{Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue}
 }
 $winSha=(Get-FileHash $winSb -Algorithm SHA256).Hash;$wv=Run $winSb @('version') 15000
 Assert ($wv.exit -eq 0 -and $wv.stdout -match ('sing-box version '+[regex]::Escape($SbVersion))) 'WINDOWS_SINGBOX_VERSION_FAIL'
 $r.steps+=@([ordered]@{name='windowsSingBox';status='PASS';path=$winSb;sha256=$winSha;version=$SbVersion})

 $distros=Get-Distros
 if(!$Distro -and (Test-Path $Local)){
  try{$old=Get-Content $Local -Raw -Encoding UTF8|ConvertFrom-Json;if($old.wsl -and @($distros) -contains [string]$old.wsl.distro){$Distro=[string]$old.wsl.distro}}catch{}
 }
 if(!$Distro){
  $pick=@($distros|Where-Object{$_ -eq 'PCMClawUbuntu'}|Select-Object -First 1)
  if(!$pick){$pick=@($distros|Where-Object{$_ -match '^Ubuntu'}|Select-Object -First 1)}
  if(!$pick){$pick=@($distros|Where-Object{$_ -notmatch 'docker|podman'}|Select-Object -First 1)}
  if($pick){$Distro=[string]$pick[0]}
 }
 Assert ([bool]$Distro) 'WSL_DISTRO_MISSING_INSTALL_WSL_FIRST'
 Assert (@($distros) -contains $Distro) 'WSL_DISTRO_NOT_FOUND'
 $script:DistroName=$Distro
 $r.steps+=@([ordered]@{name='wslDistro';status='PASS';distro=$Distro})

 $usb=Find-Usbipd
 if(!$usb -and $InstallPrerequisites){
  $tmp=Join-Path $env:TEMP ('FreeNetHub-usbipd-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $tmp -Force|Out-Null
  try{
   $msi=Join-Path $tmp 'usbipd-win.msi'
   [void](Download-Pinned ('https://github.com/dorssel/usbipd-win/releases/download/v'+$UsbVersion+'/usbipd-win_'+$UsbVersion+'_x64.msi') $msi $UsbMsiSha)
   $p=Start-Process msiexec.exe -ArgumentList @('/i',$msi,'/qn','/norestart') -Wait -PassThru
   if($p.ExitCode -notin @(0,3010)){throw ('USBIPD_INSTALL_FAILED_'+$p.ExitCode)}
  }finally{Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue}
  $usb=Find-Usbipd
 }
 Assert ([bool]$usb) 'USBIPD_MISSING_RUN_SETUP_WITH_INSTALLPREREQUISITES'
 $uv=Run $usb @('--version') 15000;Assert ($uv.exit -eq 0) 'USBIPD_VERSION_FAIL'
 $usbSha=(Get-FileHash $usb -Algorithm SHA256).Hash
 $r.steps+=@([ordered]@{name='usbipd';status='PASS';path=$usb;sha256=$usbSha;version=$uv.stdout.Trim()})

 $tools=@('modprobe','nft','python3','curl','base64','tar','sha256sum')
 $missing=@()
 foreach($c in $tools){$q=Wsl @('sh','-lc',('command -v '+$c+' >/dev/null 2>&1'));if($q.exit -ne 0){$missing+=$c}}
 if($missing.Count -and $InstallPrerequisites){
  $a=Wsl @('apt-get','install','-y','-qq','kmod','nftables','python3','curl','coreutils','tar') 240000
  if($a.exit -ne 0){throw ('WSL_TOOLS_INSTALL_FAIL '+$a.stderr)}
  $missing=@();foreach($c in $tools){$q=Wsl @('sh','-lc',('command -v '+$c+' >/dev/null 2>&1'));if($q.exit -ne 0){$missing+=$c}}
 }
 Assert ($missing.Count -eq 0) ('WSL_TOOLS_MISSING_'+($missing -join '_'))
 $r.steps+=@([ordered]@{name='wslTools';status='PASS';tools=$tools})

 $linuxPath='/root/.local/lib/freenethub/sing-box-'+$SbVersion+'/sing-box'
 $chk=Wsl @('sha256sum',$linuxPath) 15000
 $linuxOk=($chk.exit -eq 0 -and (($chk.stdout.Trim() -split '\s+')[0].ToUpperInvariant() -eq $LinuxBinarySha))
 if(!$linuxOk){
  $tmpLinux='/tmp/freenethub-sing-box-'+[guid]::NewGuid().ToString('N')
  [void](Wsl @('mkdir','-p',$tmpLinux) 15000)
  try{
   $tgz=$tmpLinux+'/sb.tgz'
   $dl=Wsl @('curl','-L','--fail','--retry','2','--connect-timeout','15','--max-time','180','-o',$tgz,('https://github.com/SagerNet/sing-box/releases/download/v'+$SbVersion+'/sing-box-'+$SbVersion+'-linux-amd64.tar.gz')) 240000
   Assert ($dl.exit -eq 0) ('WSL_SINGBOX_DOWNLOAD_FAIL '+$dl.stderr)
   $hs=Wsl @('sha256sum',$tgz) 15000;Assert ($hs.exit -eq 0) 'WSL_SINGBOX_ARCHIVE_HASH_QUERY_FAIL'
   $archiveHash=(($hs.stdout.Trim() -split '\s+')[0]).ToUpperInvariant();Assert ($archiveHash -eq $LinuxArchiveSha) 'WSL_SINGBOX_ARCHIVE_HASH_FAIL'
   $ex=Wsl @('tar','-xzf',$tgz,'-C',$tmpLinux) 60000;Assert ($ex.exit -eq 0) ('WSL_SINGBOX_EXTRACT_FAIL '+$ex.stderr)
   $find=Wsl @('find',$tmpLinux,'-type','f','-name','sing-box','-print') 15000;Assert ($find.exit -eq 0) 'WSL_SINGBOX_FIND_FAIL'
   $src=@($find.stdout -split '\r?\n'|Where-Object{$_})|Select-Object -First 1;Assert ([bool]$src) 'WSL_SINGBOX_BINARY_NOT_FOUND'
   $dir=[IO.Path]::GetDirectoryName($linuxPath).Replace('\','/')
   $mk=Wsl @('mkdir','-p',$dir) 15000;Assert ($mk.exit -eq 0) 'WSL_SINGBOX_MKDIR_FAIL'
   $ins=Wsl @('install','-m','0755',$src,$linuxPath) 30000;Assert ($ins.exit -eq 0) ('WSL_SINGBOX_INSTALL_FAIL '+$ins.stderr)
  }finally{[void](Wsl @('rm','-rf',$tmpLinux) 15000)}
 }
 $chk=Wsl @('sha256sum',$linuxPath) 15000;Assert ($chk.exit -eq 0) 'WSL_SINGBOX_HASH_QUERY_FAIL'
 $linuxSha=(($chk.stdout.Trim() -split '\s+')[0]).ToUpperInvariant();Assert ($linuxSha -eq $LinuxBinarySha) 'WSL_SINGBOX_HASH_FAIL'
 $r.steps+=@([ordered]@{name='linuxSingBox';status='PASS';path=$linuxPath;sha256=$linuxSha;version=$SbVersion})

 $rows=@(Usb-Rows $usb)
 if(!$HardwareId -and (Test-Path $Local)){try{$old=Get-Content $Local -Raw -Encoding UTF8|ConvertFrom-Json;if($old.console -and [string]$old.console.hardware_id){$HardwareId=[string]$old.console.hardware_id}}catch{}}
 if(!$HardwareId -and @($rows|Where-Object{$_.hardware_id -eq '0bda:8153'}).Count -eq 1){$HardwareId='0bda:8153'}
 if(!$HardwareId){
  $ids=@()
  foreach($pnp in @(Get-PnpDevice -Class Net -PresentOnly -ErrorAction SilentlyContinue)){
   if([string]$pnp.InstanceId -match '^USB\\VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})'){$ids+=($matches[1]+':'+$matches[2]).ToLowerInvariant()}
  }
  $cand=@($rows|Where-Object{$ids -contains $_.hardware_id})
  if($cand.Count -eq 1){$HardwareId=$cand[0].hardware_id}
 }
 Assert ($HardwareId -match '^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}$') 'CONSOLE_USB_HARDWARE_ID_REQUIRED'
 $HardwareId=$HardwareId.ToLowerInvariant();$dev=@($rows|Where-Object{$_.hardware_id -eq $HardwareId})
 Assert ($dev.Count -eq 1) 'CONSOLE_USB_DEVICE_AMBIGUOUS_OR_MISSING';$dev=$dev[0]
 $vid=$HardwareId.Split(':')[0];$pid=$HardwareId.Split(':')[1]
 $cim=@(Get-CimInstance Win32_NetworkAdapter -ErrorAction SilentlyContinue|Where-Object{[string]$_.PNPDeviceID -match ('VID_'+$vid) -and [string]$_.PNPDeviceID -match ('PID_'+$pid)})
 $na=$cim|Where-Object{$_.MACAddress}|Select-Object -First 1
 $name=if($na -and $na.NetConnectionID){[string]$na.NetConnectionID}else{[string]$dev.description}
 $desc=if($na){[string]$na.Name}else{[string]$dev.description}
 $mac=if($na -and $na.MACAddress){[string]$na.MACAddress}else{''}
 Assert ($mac -match '^[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}$') 'CONSOLE_USB_MAC_NOT_FOUND'
 $mods=if($HardwareId -eq '0bda:8153'){@('usbnet','cdc_ether','r8153_ecm')}else{@()}
 $cfg=[ordered]@{
  schema=2
  singbox=[ordered]@{path=$winSb;sha256=$winSha;version=$SbVersion;archiveSha256=$WinArchiveSha}
  console=[ordered]@{adapter_name=$name;adapter_description=$desc;mac_address=$mac;hardware_id=$HardwareId;busid=[string]$dev.busid}
  wsl=[ordered]@{
   distro=$Distro
   usbipd=[ordered]@{path=$usb;sha256=$usbSha;version=$uv.stdout.Trim()}
   linuxSingBox=[ordered]@{path=$linuxPath;sha256=$linuxSha;archiveSha256=$LinuxArchiveSha;version=$SbVersion}
   modules=$mods
  }
 }
 WJ $Local $cfg
 $r.steps+=@([ordered]@{name='consoleAdapter';status='PASS';busid=$dev.busid;hardware_id=$HardwareId;description=$desc;mac=$mac;state=$dev.state})
 $r.status='PASS';$r.localGateway=$Local;$r.distro=$Distro;$r.console=[ordered]@{busid=$dev.busid;hardware_id=$HardwareId;description=$desc;mac=$mac;state=$dev.state}
 $r.note='Setup changed no route, DNS, proxy, TUN, or USB attachment. Start Console remains an explicit elevated action.'
}catch{$r.error=$_.Exception.Message}
if(!$ResultPath){$ResultPath=Join-Path $Runtime 'console-setup-result.json'}
WJ $ResultPath $r
$r|ConvertTo-Json -Depth 16
if($r.status -ne 'PASS'){exit 20}
