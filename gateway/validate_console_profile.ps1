[CmdletBinding()]
param([string]$ProfilePath='')
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'runtime_config.ps1')
$Root=(Resolve-Path "$PSScriptRoot\..").Path;$Runtime=Join-Path $PSScriptRoot 'runtime'
if(!$ProfilePath){$ProfilePath=Join-Path $Runtime 'console.profile.json'}
$ProfilePath=(Resolve-Path -LiteralPath $ProfilePath -ErrorAction Stop).Path
$runtimeFull=[IO.Path]::GetFullPath($Runtime)+'\';if(!$ProfilePath.StartsWith($runtimeFull,[StringComparison]::OrdinalIgnoreCase)){throw 'PROFILE_MUST_BE_IN_RUNTIME'}
$Defaults=Get-Content (Join-Path $PSScriptRoot 'gateway_defaults.json') -Raw -Encoding UTF8|ConvertFrom-Json
$S=Get-FnhSingBox;$SB=[string]$S.path;$Expected=[string]$S.sha256;$Python=Get-FnhPython
$Result=Join-Path $Runtime 'console-profile-validation.json';$Cfg=Join-Path $Runtime 'console-profile-validation.singbox.json';$Err=Join-Path $Runtime 'console-profile-validation.stderr.log';$Out=Join-Path $Runtime 'console-profile-validation.stdout.log'
function WJ([string]$p,$o){$o|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $p -Encoding UTF8}
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
$r=[ordered]@{status='FAIL';error='';utc=[DateTimeOffset]::UtcNow.ToString('o')};$sp=$null
try{
 Assert ((Test-Path $SB) -and (Get-FileHash $SB -Algorithm SHA256).Hash -eq $Expected) 'SINGBOX_PIN_FAIL'
 $p=Get-Content $ProfilePath -Raw -Encoding UTF8|ConvertFrom-Json;Assert ([string]$p.kind -eq 'wireguard') 'PROFILE_KIND_UNSUPPORTED';$country=[string]$p.country;Assert ($country -match '^[A-Z]{2}$') 'PROFILE_COUNTRY_INVALID'
 $cfg=[ordered]@{log=[ordered]@{level='warn';timestamp=$true};inbounds=@([ordered]@{type='socks';tag='probe';listen='127.0.0.1';listen_port=19593});outbounds=@([ordered]@{type='direct';tag='direct'});endpoints=@($p.endpoint);route=[ordered]@{final='provider';auto_detect_interface=$true}}
 WJ $Cfg $cfg;& $SB check -c $Cfg;Assert ($LASTEXITCODE -eq 0) 'PROFILE_SINGBOX_CHECK_FAIL'
 Remove-Item $Out,$Err -Force -ErrorAction SilentlyContinue;$sp=Start-Process -FilePath $SB -ArgumentList @('run','-c',$Cfg) -WindowStyle Hidden -RedirectStandardOutput $Out -RedirectStandardError $Err -PassThru
 $deadline=[DateTime]::UtcNow.AddSeconds(12);do{if($sp.HasExited){throw ('PROFILE_SINGBOX_EXIT_'+$sp.ExitCode)};if(Get-NetTCPConnection -State Listen -LocalPort 19593 -OwningProcess $sp.Id -ErrorAction SilentlyContinue){break};Start-Sleep -Milliseconds 200}while([DateTime]::UtcNow -lt $deadline);Assert ([bool](Get-NetTCPConnection -State Listen -LocalPort 19593 -OwningProcess $sp.Id -ErrorAction SilentlyContinue)) 'PROFILE_PROXY_LISTENER_TIMEOUT'
 $t=& curl.exe -4 --socks5-hostname 127.0.0.1:19593 --max-time 25 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>&1|Out-String;Assert ($LASTEXITCODE -eq 0) 'PROFILE_TCP_TRACE_FAIL';$td=@{};foreach($l in ($t -split '\r?\n')){if($l -match '^([^=]+)=(.*)$'){$td[$matches[1]]=$matches[2]}};Assert ([string]$td.loc -eq $country) ('PROFILE_TCP_COUNTRY_'+[string]$td.loc)
 $yt=& curl.exe -4 --socks5-hostname 127.0.0.1:19593 --max-time 25 -sS -o NUL -w '%{http_code}' https://www.youtube.com/generate_204 2>&1|Out-String;Assert ($LASTEXITCODE -eq 0 -and $yt.Trim() -eq '204') 'PROFILE_YOUTUBE_FAIL'
 $u=& $Python (Join-Path $PSScriptRoot 'socks_udp_probe.py') 19593 2>&1|Out-String;Assert ($LASTEXITCODE -eq 0) 'PROFILE_UDP_STUN_FAIL';$uj=$u|ConvertFrom-Json
 $g=& curl.exe -4 --noproxy '*' --max-time 15 -fsS ('https://ipwho.is/'+[string]$uj.udp_public_ip) 2>&1|Out-String;Assert ($LASTEXITCODE -eq 0) 'PROFILE_UDP_GEO_FAIL';$geo=$g|ConvertFrom-Json;Assert ($geo.success -and [string]$geo.country_code -eq $country) ('PROFILE_UDP_COUNTRY_'+[string]$geo.country_code)
 $p.capabilities.tcp=$true;$p.capabilities.udp=$true;$p.capabilities.country_verified=$true;$p|Add-Member -NotePropertyName validation -NotePropertyValue ([pscustomobject]@{utc=[DateTimeOffset]::UtcNow.ToString('o');tcpCountry=$country;udpCountry=$country;youtube='204';singBoxSha256=$Expected}) -Force;WJ $ProfilePath $p
 $r=[ordered]@{status='PASS';country=$country;tcp=$true;udp=$true;countryVerified=$true;profileSha256=(Get-FileHash $ProfilePath -Algorithm SHA256).Hash;utc=[DateTimeOffset]::UtcNow.ToString('o')}
}catch{$r.error=$_.Exception.Message}finally{if($sp -and -not $sp.HasExited){Stop-Process -Id $sp.Id -Force -ErrorAction SilentlyContinue};Start-Sleep -Milliseconds 400;Remove-Item $Cfg,$Out,$Err -Force -ErrorAction SilentlyContinue;WJ $Result $r}
$r|ConvertTo-Json -Depth 12;if($r.status -ne 'PASS'){exit 20}
