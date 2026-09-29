[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Ctrld=Join-Path $Root 'app\directdns\ctrld.exe'
$Template=Join-Path $Root 'app\directdns\ctrld.toml'
$RuntimeDir=Join-Path $env:ProgramData 'FreeNetHub\directdns'
$RuntimeConfig=Join-Path $RuntimeDir 'ctrld.toml'
$Evidence=Join-Path $Root 'evidence\R36_CTRLD_MANAGED_DNS_TRIAL_20260929.json'
$ExpectedCtrld='FC966FD7DD5EE850A9709F632789CFB5BBC06C45D903D24B8ECFCE3306B658CD'
$ExpectedTemplate='78D723EAD775B2D1854DB9FE651191B18C26ED1E33DBA9B01B042F61BAB36BF4'
$Interface='Ethernet 3'
function IsAdmin{$id=[Security.Principal.WindowsIdentity]::GetCurrent();$p=[Security.Principal.WindowsPrincipal]::new($id);$p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)}
function WJ($x){$x|ConvertTo-Json -Depth 16|Set-Content -LiteralPath $Evidence -Encoding UTF8}
function NRPT{@(Get-DnsClientNrptRule -ErrorAction SilentlyContinue|Select-Object Name,Namespace,NameServers,Comment,DisplayName)}
function Curl([string]$u,[int]$t=6){$m=& curl.exe -4 --noproxy '*' -sS -o NUL -w '%{http_code}|%{remote_ip}|%{time_connect}|%{time_appconnect}|%{time_total}' --max-time $t $u 2>&1;[ordered]@{url=$u;exit=$LASTEXITCODE;meta=($m -join ' ')}}
function Dns([string]$n){try{$sw=[Diagnostics.Stopwatch]::StartNew();$a=@([System.Net.Dns]::GetHostAddresses($n)|Where-Object AddressFamily -eq InterNetwork|ForEach-Object IPAddressToString|Select-Object -Unique);$sw.Stop();[ordered]@{name=$n;ok=($a.Count -gt 0);ms=$sw.ElapsedMilliseconds;answers=$a;private=@($a|Where-Object{$_ -match '^(10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)'})}}catch{[ordered]@{name=$n;ok=$false;error=$_.Exception.Message;answers=@();private=@()}}}
if(-not(IsAdmin)){$a=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath);$p=Start-Process pwsh.exe -Verb RunAs -ArgumentList $a -Wait -PassThru;exit $p.ExitCode}
if(!(Test-Path $Ctrld)){throw 'CTRLD_MISSING'}
if((Get-FileHash $Ctrld -Algorithm SHA256).Hash -ne $ExpectedCtrld){throw 'CTRLD_HASH_MISMATCH'}
if(!(Test-Path $Template)){throw 'CTRLD_TEMPLATE_MISSING'}
if((Get-FileHash $Template -Algorithm SHA256).Hash -ne $ExpectedTemplate){throw 'CTRLD_TEMPLATE_HASH_MISMATCH'}
if(Test-Path $RuntimeDir){throw 'DIRECTDNS_RUNTIME_PREEXISTING'}
if(Get-Service -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '(?i)ctrld|controld'}){throw 'CTRLD_PREEXISTING_SERVICE'}
if(Get-Process ctrld -ErrorAction SilentlyContinue){throw 'CTRLD_PREEXISTING_PROCESS'}
$preDns=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4).ServerAddresses)
$preNetsh=(netsh interface ipv4 show dnsservers name=$Interface|Out-String)
$preMode=$(if($preNetsh -match 'DHCP'){'DHCP'}else{'STATIC'})
$preNrpt=@(NRPT)
$ics=Get-Service SharedAccess
$pre=[ordered]@{dns=$preDns;dnsMode=$preMode;nrpt=$preNrpt;icsStatus=[string]$ics.Status;icsPid=(Get-CimInstance Win32_Service -Filter "Name='SharedAccess'").ProcessId;udp53=@(Get-NetUDPEndpoint -LocalPort 53 -ErrorAction SilentlyContinue|Select-Object LocalAddress,LocalPort,OwningProcess)}
$r=[ordered]@{schema=1;status='FAIL';pre=$pre;start=$null;during=$null;cleanup=$null;error=''}
try{
 New-Item -ItemType Directory -Force -Path $RuntimeDir|Out-Null
 Copy-Item -LiteralPath $Template -Destination $RuntimeConfig -Force
 $runtimeBefore=(Get-Content -LiteralPath $RuntimeConfig -Raw -Encoding UTF8)
 $start=@(& $Ctrld start --config $RuntimeConfig --intercept-mode dns --iface $Interface -v 2>&1)
 $startCode=$LASTEXITCODE
 $r.start=[ordered]@{exit=$startCode;output=$start}
 if($startCode -ne 0){throw ('CTRLD_START_EXIT_'+$startCode)}
 Start-Sleep -Seconds 3
 Clear-DnsClientCache -ErrorAction SilentlyContinue
 $dy=Dns 'www.youtube.com';$dg=Dns 'github.com';$do=Dns 'api.openai.com'
 $icsNow=Get-Service SharedAccess
 $r.during=[ordered]@{
   runtimeConfigPath=$RuntimeConfig
   runtimeConfigSha256=(Get-FileHash $RuntimeConfig -Algorithm SHA256).Hash
   runtimeConfig=(Get-Content -LiteralPath $RuntimeConfig -Raw -Encoding UTF8)
   services=@(Get-Service -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '(?i)ctrld|controld'}|Select-Object Name,DisplayName,Status,StartType)
   processes=@(Get-Process ctrld -ErrorAction SilentlyContinue|Select-Object Id,StartTime,Path)
   udp1053=@(Get-NetUDPEndpoint -LocalPort 1053 -ErrorAction SilentlyContinue|Select-Object LocalAddress,LocalPort,OwningProcess)
   tcp1053=@(Get-NetTCPConnection -LocalPort 1053 -State Listen -ErrorAction SilentlyContinue|Select-Object LocalAddress,LocalPort,OwningProcess)
   dnsServers=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4).ServerAddresses)
   nrpt=@(NRPT)
   dns=@($dy,$dg,$do)
   controlD=Curl 'https://76.76.10.11/p0' 5
   github=Curl 'https://github.com/' 6
   openai=Curl 'https://api.openai.com/v1/models' 6
   icsStatus=[string]$icsNow.Status
   icsPid=(Get-CimInstance Win32_Service -Filter "Name='SharedAccess'").ProcessId
 }
 if(@($r.during.processes).Count -lt 1){throw 'CTRLD_PROCESS_MISSING'}
 if(@($r.during.udp1053).Count -lt 1){throw 'CTRLD_UDP_LISTENER_MISSING'}
 if(-not $dy.ok -or $dy.private.Count){throw 'YOUTUBE_DNS_NOT_CLEAN'}
 if(-not $dg.ok -or $dg.private.Count){throw 'GITHUB_DNS_NOT_CLEAN'}
 if(-not $do.ok -or $do.private.Count){throw 'OPENAI_DNS_NOT_CLEAN'}
 if($r.during.icsStatus -ne $pre.icsStatus){throw 'ICS_STATUS_CHANGED'}
 if([int64]$r.during.icsPid -ne [int64]$pre.icsPid){throw 'ICS_PID_CHANGED'}
 if($r.during.github.exit -ne 0 -or $r.during.github.meta -notmatch '^(200|301|302)\|'){throw 'GITHUB_HTTPS_FAIL'}
 if($r.during.openai.exit -ne 0 -or $r.during.openai.meta -notmatch '^(200|401|403)\|'){throw 'OPENAI_HTTPS_FAIL'}
 $r.status='PASS_MANAGED_DNS'
}catch{$r.error=$_.Exception.Message}finally{
 $un=@(& $Ctrld uninstall --iface $Interface -v 2>&1);$unCode=$LASTEXITCODE
 Start-Sleep -Seconds 2
 if($preMode -eq 'DHCP'){Set-DnsClientServerAddress -InterfaceAlias $Interface -ResetServerAddresses}else{Set-DnsClientServerAddress -InterfaceAlias $Interface -ServerAddresses $preDns}
 Clear-DnsClientCache -ErrorAction SilentlyContinue
 Start-Sleep -Seconds 1
 $icsAfter=Get-Service SharedAccess
 $afterNrpt=@(NRPT)
 $r.cleanup=[ordered]@{
   runtimeConfigExists=(Test-Path $RuntimeConfig)
   uninstallExit=$unCode;uninstallOutput=$un
   dns=@((Get-DnsClientServerAddress -InterfaceAlias $Interface -AddressFamily IPv4).ServerAddresses)
   services=@(Get-Service -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '(?i)ctrld|controld'}|Select-Object Name,Status,StartType)
   processes=@(Get-Process ctrld -ErrorAction SilentlyContinue|Select-Object Id,Path)
   udp1053=@(Get-NetUDPEndpoint -LocalPort 1053 -ErrorAction SilentlyContinue|Select-Object OwningProcess)
   nrpt=$afterNrpt
   icsStatus=[string]$icsAfter.Status
   icsPid=(Get-CimInstance Win32_Service -Filter "Name='SharedAccess'").ProcessId
 }
 if(Test-Path $RuntimeDir){Remove-Item -LiteralPath $RuntimeDir -Recurse -Force -ErrorAction SilentlyContinue}
 $r.cleanup.runtimeDirExistsAfterRemove=(Test-Path $RuntimeDir)
 $clean=($r.cleanup.dns -join '|') -eq ($preDns -join '|') -and @($r.cleanup.processes).Count -eq 0 -and $r.cleanup.icsStatus -eq $pre.icsStatus -and [int64]$r.cleanup.icsPid -eq [int64]$pre.icsPid -and -not $r.cleanup.runtimeDirExistsAfterRemove
 if(-not $clean){$r.status='FAIL_CLEANUP';if(-not $r.error){$r.error='CLEANUP_NOT_EXACT'}}
 WJ $r
}
if($r.status -eq 'PASS_MANAGED_DNS'){Write-Host 'PASS_MANAGED_DNS';exit 0}else{Write-Host ('FAIL '+$r.error);exit 9}
