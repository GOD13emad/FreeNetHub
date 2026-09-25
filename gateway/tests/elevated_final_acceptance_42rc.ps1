[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Gateway=Join-Path $Root 'gateway'
$Runtime=Join-Path $Gateway 'runtime'
$Evidence=Join-Path $Root 'evidence\GATEWAY_FINAL_42RC_ACCEPTANCE.json'
$Engine=Join-Path $Root 'app\engine.py'
$Generator=Join-Path $Gateway 'generate_config.py'
$Apply=Join-Path $Gateway 'apply_elevated.ps1'
$Stop=Join-Path $Gateway 'stop_elevated.ps1'
$ConsoleProvider=Join-Path $Gateway 'console_provider.ps1'
$DirectStun=Join-Path $Gateway 'tests\direct_stun.py'
$BoundStun=Join-Path $Gateway 'tests\bound_stun.py'
$Defaults=Join-Path $Gateway 'gateway_defaults.json'
$ProgressFile=Join-Path $Runtime 'final_acceptance_progress.json'
$UnhandledFile=Join-Path $Root 'evidence\GATEWAY_FINAL_42RC_UNHANDLED.json'
function Mark([string]$stage,$extra=$null){
 [ordered]@{stage=$stage;utc=[DateTimeOffset]::UtcNow.ToString('o');extra=$extra}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ProgressFile -Encoding UTF8
}
trap {
 $e=[ordered]@{status='UNHANDLED';utc=[DateTimeOffset]::UtcNow.ToString('o');error=$_.Exception.Message;line=$_.InvocationInfo.ScriptLineNumber;position=$_.InvocationInfo.PositionMessage;progress=if(Test-Path $ProgressFile){Get-Content $ProgressFile -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}}
 $e|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $UnhandledFile -Encoding UTF8
 exit 99
}
Mark 'SCRIPT_START'
$Expected=@{
 $Engine='F6FB91C4714A73D6A42BF15BC9F41D134352978380B536CF586327052221C1A7'
 $Generator='A0CB20B18FB2D6AA48499F8D7BE69C4C6A105E94DA4FB14178C80B02C9BF7A29'
 $Apply='36B8474E9A8546A99B089A3031B11E1F7B19F1A7B5C93970E39FC93D79945596'
 $Stop='7D019A0E4D5737DFE3B28B48F49609A85E83DADF3CF642403CE18475A2C2B112'
 $ConsoleProvider='CEEE84242621A5AF43C48F4B352C9C79EDBADFD3E8EA0AC9C4EB255A9312D9F2'
 $DirectStun='8B24DAC139E85681BE8ECC3A5E47068E37837480EEFEACAB6F6CF1C407D7582F'
 $BoundStun='DB3915FB593FE7512B3A701DD1424CA24246541EEA7C7137A233C37202098947'
}
$Ports=19410,19413,19414,19450,19452,19453,19591,19592
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Optional($o,[string]$n){$p=$o.PSObject.Properties[$n];if($p){$p.Value}else{$null}}
function Parse-Trace([string]$t){
 $d=[ordered]@{};foreach($line in ($t -split '\r?\n')){if($line -match '^([^=]+)=(.*)$'){$d[$matches[1]]=$matches[2]}};return $d
}
function Curl-Trace([string]$bind=''){
 $a=@('-4','--noproxy','*','--max-time','25','-fsS')
 if($bind){$a+=@('--interface',$bind)}
 $a+='https://www.cloudflare.com/cdn-cgi/trace'
 $t=& curl.exe @a 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw ('TRACE_FAIL'+$(if($bind){'_BIND_'+$bind}else{''}))}
 return (Parse-Trace $t)
}
function Curl-YouTube([string]$bind=''){
 $a=@('-4','--noproxy','*','--max-time','25','-sS','-o','NUL','-w','%{http_code}')
 if($bind){$a+=@('--interface',$bind)}
 $a+='https://www.youtube.com/generate_204'
 $x=& curl.exe @a 2>&1|Out-String
 if($LASTEXITCODE -ne 0 -or $x.Trim() -ne '204'){throw ('YOUTUBE_FAIL'+$(if($bind){'_BIND_'+$bind}else{''}))}
 return $x.Trim()
}
function Geo([string]$ip){
 $x=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ("https://ipwho.is/"+$ip) 2>&1|Out-String
 if($LASTEXITCODE -ne 0){throw 'GEO_LOOKUP_FAIL'}
 $j=$x|ConvertFrom-Json
 if(!$j.success){throw 'GEO_LOOKUP_UNSUCCESSFUL'}
 [ordered]@{country=[string]$j.country;countryCode=[string]$j.country_code;city=[string]$j.city}
}
function Run-Engine([string]$Action,[string]$Mode,[int]$Budget){
 $j=[guid]::NewGuid().ToString('N')
 & $Python $Engine --action $Action --mode $Mode --job $j --budget $Budget|Out-Null
 $ec=$LASTEXITCODE
 $rec=Get-Content (Join-Path $Root ('jobs\'+$j+'.json')) -Raw -Encoding UTF8|ConvertFrom-Json
 [pscustomobject]@{exit=$ec;record=$rec}
}
function Run-ConsoleProvider([string]$Action){
 $psi=[Diagnostics.ProcessStartInfo]::new()
 $psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
 foreach($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$ConsoleProvider,'-Action',$Action)){[void]$psi.ArgumentList.Add($a)}
 $p=[Diagnostics.Process]::Start($psi)
 if(!$p.WaitForExit(120000)){try{$p.Kill($true)}catch{};throw ('CONSOLE_PROVIDER_'+$Action.ToUpper()+'_TIMEOUT')}
 $ec=$p.ExitCode
 $rec=if(Test-Path (Join-Path $Runtime 'console-provider-result.json')){Get-Content (Join-Path $Runtime 'console-provider-result.json') -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
 [pscustomobject]@{exit=$ec;record=$rec}
}
function Tun(){@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'})}
function GatewaySingBox(){@(Get-CimInstance Win32_Process|Where-Object{$_.Name -eq 'sing-box.exe'}|Select-Object ProcessId,ExecutablePath,CreationDate)}
function Snapshot-Core{
 $def=@(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop|Select-Object NextHop,InterfaceIndex,RouteMetric|Sort-Object InterfaceIndex,NextHop,RouteMetric)
 $d=Get-Content $Defaults -Raw -Encoding UTF8|ConvertFrom-Json
 $console=Get-NetAdapter -IncludeHidden|Where-Object{$_.InterfaceDescription -eq [string]$d.console.adapter_description}|Select-Object -First 1
 $cip=$null
 if($console){
  $ipif=Get-NetIPInterface -InterfaceIndex $console.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue
  $cip=[ordered]@{ifIndex=$console.ifIndex;name=$console.Name;status=[string]$console.Status;dhcp=if($ipif){[string]$ipif.Dhcp}else{$null};forwarding=if($ipif){[string]$ipif.Forwarding}else{$null};addresses=@(Get-NetIPAddress -InterfaceIndex $console.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object IPAddress,PrefixLength|Sort-Object IPAddress)}
 }
 $dns=@(Get-DnsClientServerAddress -ErrorAction Stop|Where-Object{$_.InterfaceAlias -ne 'FreeNetHub'}|ForEach-Object{[pscustomobject]@{InterfaceIndex=$_.InterfaceIndex;AddressFamily=[string]$_.AddressFamily;ServerAddresses=@($_.ServerAddresses)}}|Sort-Object InterfaceIndex,AddressFamily)
 $inet=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
 [ordered]@{defaultRoutes=$def;dns=$dns;console=$cip;proxy=[ordered]@{ProxyEnable=(Optional $inet 'ProxyEnable');ProxyServer=(Optional $inet 'ProxyServer');AutoConfigURL=(Optional $inet 'AutoConfigURL')}}
}
function Same-Core($a,$b){(($a|ConvertTo-Json -Depth 15 -Compress) -eq ($b|ConvertTo-Json -Depth 15 -Compress))}
function Stop-Gateway{
 $err=''
 try{
  if((Test-Path (Join-Path $Runtime 'owner.json')) -or @(Tun).Count -gt 0 -or @(GatewaySingBox).Count -gt 0){& $Stop|Out-Null}
 }catch{$err=$_.Exception.Message}
 if(@(Tun).Count -gt 0 -or @(GatewaySingBox).Count -gt 0){throw ('GATEWAY_CLEANUP_INCOMPLETE '+$err)}
}
function Reset-Providers{
 try{Run-Engine 'Stop' 'AUTO' 90|Out-Null}catch{}
 try{Run-ConsoleProvider 'Stop'|Out-Null}catch{}
}
function Preclean{
 Reset-Providers
 Stop-Gateway
 Start-Sleep -Seconds 1
 Assert (@(Tun).Count -eq 0) 'PRECLEAN_TUN_LEFT'
 Assert (@(GatewaySingBox).Count -eq 0) 'PRECLEAN_SINGBOX_LEFT'
 Assert (@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort}).Count -eq 0) 'PRECLEAN_PROJECT_LISTENER_LEFT'
 Remove-Item (Join-Path $Runtime 'owner.json') -Force -ErrorAction SilentlyContinue
}
$admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(!$admin){throw 'RUNNER_NOT_ELEVATED'}
foreach($p in $Expected.Keys){Assert ((Sha $p) -eq $Expected[$p]) ('HASH_MISMATCH '+$p)}
$sb=(Get-Content (Join-Path $Runtime 'local_gateway.json') -Raw -Encoding UTF8|ConvertFrom-Json).singbox.path
Assert ((Test-Path $sb) -and (Sha $sb) -eq 'AAD0EDE010EAFA7B277E520464F3A66FDE820103D737EFF739F40F3CC9451DCC') 'SINGBOX_PIN_FAIL'
Mark 'PRECLEAN_BEGIN'
Preclean
Mark 'PRECLEAN_PASS'

$base=Snapshot-Core
Mark 'BASELINE_SNAPSHOT_PASS'
$baseTrace=Curl-Trace
$baseStun=(& $Python $DirectStun|Out-String)|ConvertFrom-Json
$baseDefault=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0'|Sort-Object RouteMetric|Select-Object -First 1
$baseAdapter=Get-NetAdapter -InterfaceIndex $baseDefault.InterfaceIndex
Mark 'BASELINE_NETWORK_PASS' ([ordered]@{ip=$baseTrace.ip;loc=$baseTrace.loc;defaultIf=$baseDefault.InterfaceIndex})
$result=[ordered]@{
 schema=2;utc=[DateTimeOffset]::UtcNow.ToString('o');candidate='4.2.0-rc2';product='FreeNet Hub Gateway';
 baseline=[ordered]@{trace=$baseTrace;stun=$baseStun;default=[ordered]@{ifIndex=$baseDefault.InterfaceIndex;name=$baseAdapter.Name;description=$baseAdapter.InterfaceDescription;gateway=$baseDefault.NextHop}};
 pcTunnel=[ordered]@{status='NOT_RUN'};consoleOnly=[ordered]@{status='NOT_RUN'};final=[ordered]@{}
}
$overall='PASS'

# ---- Full PC ----
Mark 'PC_BEGIN'
$pc=[ordered]@{status='FAIL';error='';checks=[ordered]@{}}
try{
 $con=Run-Engine 'Connect' 'WARP' 240
 Assert ($con.exit -eq 0 -and [bool]$con.record.result.healthy) 'PC_WARP_PROVIDER_CONNECT_FAIL'
 $pc.checks.providerBefore=$con.record.result
 $cfg=Join-Path $Runtime 'pc_final_42rc.json'
 & $Python $Generator --mode PC_TUNNEL --provider WARP --output $cfg|Out-Null
 Assert ($LASTEXITCODE -eq 0) 'PC_CONFIG_GENERATE_FAIL'
 & $sb check -c $cfg;Assert ($LASTEXITCODE -eq 0) 'PC_CONFIG_CHECK_FAIL'
 & $Apply -Mode PC_TUNNEL -ConfigPath $cfg -ConfigSha256 (Sha $cfg)|Out-Null
 $ar=Get-Content (Join-Path $Runtime 'apply_result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ($ar.status -eq 'PASS') 'PC_APPLY_FAIL'
 Start-Sleep -Seconds 3
 $tun=Tun|Select-Object -First 1;Assert ($tun -and $tun.Status -eq 'Up') 'PC_TUN_NOT_UP'
 Assert ([bool](Get-NetTCPConnection -State Listen -LocalPort 19410 -ErrorAction SilentlyContinue)) 'PC_WARP_LISTENER_DIED'
 $under=@(Find-NetRoute -RemoteIPAddress '162.159.192.165' -ErrorAction Stop|Where-Object{$_.PSObject.Properties['DestinationPrefix'] -and $_.DestinationPrefix}|Select-Object -First 1)
 Assert (@($under).Count -eq 1 -and [int]$under[0].InterfaceIndex -eq [int]$baseDefault.InterfaceIndex) 'PC_WARP_UNDERLAY_CAPTURED'
 $under=$under[0]
 $pc.checks.underlay=[ordered]@{interfaceIndex=$under.InterfaceIndex;interfaceAlias=$under.InterfaceAlias;nextHop=$under.NextHop}
 $tr=Curl-Trace;Assert ([string]$tr.warp -eq 'on') 'PC_SYSTEM_WARP_NOT_ON'
 $pc.checks.trace=$tr
 $pc.checks.youtube=Curl-YouTube
 $st=(& $Python $DirectStun|Out-String)|ConvertFrom-Json
 Assert ($st.status -eq 'PASS') 'PC_SYSTEM_UDP_STUN_FAIL'
 $pc.checks.udp=$st
 $ver=Run-Engine 'Verify' 'WARP' 90
 Assert ($ver.exit -eq 0 -and [bool]$ver.record.result.healthy) 'PC_WARP_PROVIDER_VERIFY_FAIL'
 $pc.checks.providerAfter=$ver.record.result
 $pc.status='PASS'
 Mark 'PC_RUNTIME_PASS'
}catch{$pc.error=$_.Exception.Message;$overall='FAIL'}
finally{
 try{Stop-Gateway}catch{$pc.cleanupError=$_.Exception.Message;$overall='FAIL'}
 try{$x=Run-Engine 'Stop' 'AUTO' 90;$pc.providerStop=$x.record.result}catch{$pc.providerStopError=$_.Exception.Message;$overall='FAIL'}
 Start-Sleep -Seconds 2
 $post=Snapshot-Core
 $pc.rollback=[ordered]@{networkUnchanged=(Same-Core $base $post);tunCount=@(Tun).Count;singBoxCount=@(GatewaySingBox).Count;listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort}).Count}
 if(!$pc.rollback.networkUnchanged -or $pc.rollback.tunCount -or $pc.rollback.singBoxCount -or $pc.rollback.listeners){$pc.status='FAIL';if(!$pc.error){$pc.error='PC_ROLLBACK_GATE_FAIL'};$overall='FAIL'}
}
$result.pcTunnel=$pc
Mark ('PC_PHASE_'+$pc.status) ([ordered]@{error=$pc.error;rollback=$pc.rollback})

# Ensure exact clean boundary between modes.
Preclean
Assert (Same-Core $base (Snapshot-Core)) 'BOUNDARY_BASELINE_NOT_RESTORED'

# ---- Console only ----
Mark 'CONSOLE_BEGIN'
$co=[ordered]@{status='FAIL';error='';checks=[ordered]@{}}
try{
 $cp=Run-ConsoleProvider 'Start'
 Assert ($cp.exit -eq 0 -and $cp.record.status -eq 'PASS' -and [bool]$cp.record.verification.healthy) 'CONSOLE_PROVIDER_START_FAIL'
 Assert ([string]$cp.record.verification.tcpCountry -eq 'DE' -and [string]$cp.record.verification.udpCountry -eq 'DE') 'CONSOLE_PROVIDER_COUNTRY_CONTRACT_FAIL'
 $co.checks.providerBefore=$cp.record.verification

 $cfg=Join-Path $Runtime 'console_final_42rc.json'
 & $Python $Generator --mode CONSOLE_ONLY --provider FNH_DE --target-country DE --output $cfg|Out-Null
 Assert ($LASTEXITCODE -eq 0) 'CONSOLE_CONFIG_GENERATE_FAIL'
 & $sb check -c $cfg;Assert ($LASTEXITCODE -eq 0) 'CONSOLE_CONFIG_CHECK_FAIL'
 & $Apply -Mode CONSOLE_ONLY -ConfigPath $cfg -ConfigSha256 (Sha $cfg)|Out-Null
 $ar=Get-Content (Join-Path $Runtime 'apply_result.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ($ar.status -eq 'PASS') 'CONSOLE_APPLY_FAIL'
 Start-Sleep -Seconds 3

 $tun=Tun|Select-Object -First 1;Assert ($tun -and $tun.Status -eq 'Up') 'CONSOLE_TUN_NOT_UP'
 $d=Get-Content $Defaults -Raw -Encoding UTF8|ConvertFrom-Json
 $ca=Get-NetAdapter -IncludeHidden|Where-Object{$_.InterfaceDescription -eq [string]$d.console.adapter_description}|Select-Object -First 1
 Assert ($null -ne $ca) 'CONSOLE_ADAPTER_NOT_FOUND_RUNTIME'
 Assert ($ca.ifIndex -ne $baseDefault.InterfaceIndex) 'CONSOLE_ADAPTER_IS_UPLINK_RUNTIME'
 $cip=Get-NetIPAddress -InterfaceIndex $ca.ifIndex -AddressFamily IPv4 -IPAddress '192.168.77.1' -ErrorAction SilentlyContinue
 Assert ($cip -and $cip.PrefixLength -eq 24) 'CONSOLE_GATEWAY_IP_NOT_SET'
 $fwr=Get-NetFirewallRule -DisplayName 'FreeNetHub Console Leak Guard' -ErrorAction SilentlyContinue
 Assert ($null -ne $fwr) 'CONSOLE_LEAK_GUARD_MISSING'
 $co.checks.adapter=[ordered]@{ifIndex=$ca.ifIndex;name=$ca.Name;description=$ca.InterfaceDescription;status=[string]$ca.Status;gatewayIp='192.168.77.1/24'}
 $co.checks.leakGuard=$true

 # PC must retain direct public route/IP even while the policy TUN is active.
 $pcDirect=Curl-Trace
 Assert ([string]$pcDirect.ip -eq [string]$baseTrace.ip) 'CONSOLE_MODE_PC_PUBLIC_IP_CHANGED'
 $co.checks.pcDirectTrace=$pcDirect

 # Synthetic source-bound TCP from the console gateway address must select DE.
 $ct=Curl-Trace '192.168.77.1'
 Assert ([string]$ct.loc -eq 'DE') ('CONSOLE_TCP_COUNTRY_'+[string]$ct.loc)
 $co.checks.consoleTcpTrace=$ct
 $co.checks.consoleYoutube=Curl-YouTube '192.168.77.1'

 # Source-bound UDP must select the same country.
 $us=& $Python $BoundStun '192.168.77.1' 2>&1|Out-String
 Assert ($LASTEXITCODE -eq 0) 'CONSOLE_BOUND_UDP_STUN_FAIL'
 $uj=$us|ConvertFrom-Json
 $ug=Geo ([string]$uj.public_ip)
 Assert ([string]$ug.countryCode -eq 'DE') ('CONSOLE_UDP_COUNTRY_'+[string]$ug.countryCode)
 $co.checks.consoleUdp=[ordered]@{stun=$uj;geo=$ug}

 # Existing isolated provider must remain healthy through the policy TUN.
 $cv=Run-ConsoleProvider 'Verify'
 Assert ($cv.exit -eq 0 -and $cv.record.status -eq 'PASS' -and [string]$cv.record.verification.tcpCountry -eq 'DE' -and [string]$cv.record.verification.udpCountry -eq 'DE') 'CONSOLE_PROVIDER_VERIFY_AFTER_TUN_FAIL'
 $co.checks.providerAfter=$cv.record.verification
 $co.status='PASS'
 Mark 'CONSOLE_RUNTIME_PASS'
}catch{$co.error=$_.Exception.Message;$overall='FAIL'}
finally{
 try{Stop-Gateway}catch{$co.cleanupError=$_.Exception.Message;$overall='FAIL'}
 try{$x=Run-ConsoleProvider 'Stop';$co.providerStop=$x.record}catch{$co.providerStopError=$_.Exception.Message;$overall='FAIL'}
 Start-Sleep -Seconds 2
 $post=Snapshot-Core
 $co.rollback=[ordered]@{networkUnchanged=(Same-Core $base $post);tunCount=@(Tun).Count;singBoxCount=@(GatewaySingBox).Count;listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort}).Count;firewallLeft=@(Get-NetFirewallRule -DisplayName 'FreeNetHub Console Leak Guard' -ErrorAction SilentlyContinue).Count}
 if(!$co.rollback.networkUnchanged -or $co.rollback.tunCount -or $co.rollback.singBoxCount -or $co.rollback.listeners -or $co.rollback.firewallLeft){$co.status='FAIL';if(!$co.error){$co.error='CONSOLE_ROLLBACK_GATE_FAIL'};$overall='FAIL'}
}
$result.consoleOnly=$co
Mark ('CONSOLE_PHASE_'+$co.status) ([ordered]@{error=$co.error;rollback=$co.rollback})
$result.final=[ordered]@{status=$overall;clean=(@(Tun).Count -eq 0 -and @(GatewaySingBox).Count -eq 0 -and @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$Ports -contains $_.LocalPort}).Count -eq 0);networkBaselineRestored=(Same-Core $base (Snapshot-Core));utc=[DateTimeOffset]::UtcNow.ToString('o')}
if(!$result.final.clean -or !$result.final.networkBaselineRestored){$result.final.status='FAIL'}
$result|ConvertTo-Json -Depth 25|Set-Content -LiteralPath $Evidence -Encoding UTF8
Mark ('FINAL_'+$result.final.status)
$result|ConvertTo-Json -Depth 25
if($result.final.status -ne 'PASS'){exit 20}
