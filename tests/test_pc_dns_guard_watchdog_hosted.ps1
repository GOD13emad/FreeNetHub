# Hosted Windows runner only: exercise real ActiveStore rule lifetime and exact-owner watchdog.
# Scope firewall filters to TEST-NET-1 (RFC 5737); never block live DNS servers.
# Never run this on an owner's workstation: Windows CI is a disposable hosted runner.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guard=Join-Path $PSScriptRoot '..\gateway\dns_guard_watchdog.ps1'
$ruleNames=@('FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
$testAddress='192.0.2.77'
$created=@()
$dummy=$null
$watch=$null
$failure=''
$passed=$false
function CurrentGuardRules {
 @(foreach($n in $ruleNames){
  $entry=Get-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction SilentlyContinue
  if($entry){$entry}
 })
}
function Check([bool]$condition,[string]$why){
 if(!$condition){throw $why}
}
try {
 Check ($env:GITHUB_ACTIONS -eq 'true' -and $env:RUNNER_OS -eq 'Windows') 'HOSTED_GITHUB_WINDOWS_ONLY'
 Check ([bool]$env:RUNNER_TEMP) 'GITHUB_TEMP_REQUIRED'
 Check (Test-Path -LiteralPath $guard) 'WATCHDOG_SOURCE_MISSING'
 $admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
 Check $admin 'HOSTED_WINDOWS_RUNNER_NOT_ADMIN'
 Check (@(CurrentGuardRules).Count -eq 0) 'EXACT_FIREWALL_RULE_NAMES_ALREADY_PRESENT'
 Check (@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object Name -eq 'FreeNetHub').Count -eq 0) 'FNH_TUN_ALREADY_EXISTS'
 $route=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction Stop|Sort-Object RouteMetric|Select-Object -First 1
 Check ([bool]$route) 'NO_IPV4_DEFAULT_ROUTE'
 $uplink=Get-NetAdapter -InterfaceIndex $route.InterfaceIndex -ErrorAction Stop
 Check ([bool]$uplink.Name -and $uplink.Status -eq 'Up') 'HOSTED_UPLINK_NOT_READY'
 $runtime=Join-Path (Split-Path $guard -Parent) 'runtime'
 New-Item -ItemType Directory -Path $runtime -Force|Out-Null
 $receipt=Join-Path $runtime 'dns-guard-watchdog-result.json'
 Remove-Item -LiteralPath $receipt -ErrorAction SilentlyContinue
 $dummy=Start-Process -FilePath pwsh.exe -ArgumentList @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 90') -PassThru -WindowStyle Hidden
 $owned=Get-Process -Id $dummy.Id -ErrorAction Stop
 foreach($item in @(
  @{Name=$ruleNames[0];Protocol='UDP';Type='Wired'},
  @{Name=$ruleNames[1];Protocol='TCP';Type='Wired'},
  @{Name=$ruleNames[2];Protocol='UDP';Type='Wireless'},
  @{Name=$ruleNames[3];Protocol='TCP';Type='Wireless'}
 )){
  New-NetFirewallRule -Name $item.Name -DisplayName $item.Name -Direction Outbound -Action Block -Protocol $item.Protocol -RemotePort 53 -RemoteAddress $testAddress -InterfaceType $item.Type -Profile Any -Enabled True -PolicyStore ActiveStore -ErrorAction Stop|Out-Null
  $filter=Get-NetFirewallInterfaceTypeFilter -AssociatedNetFirewallRule (Get-NetFirewallRule -Name $item.Name -PolicyStore ActiveStore -ErrorAction Stop) -ErrorAction Stop
  Check ([string]$filter.InterfaceType -eq [string]$item.Type) 'REAL_HOSTED_INTERFACE_TYPE_FILTER_NOT_EFFECTIVE'
  $created+= $item.Name
 }
 Check (@(CurrentGuardRules).Count -eq 4) 'GUARD_CREATION_FAILED'
 foreach($rule in @(CurrentGuardRules)){
  $addressFilter=Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
  Check (@($addressFilter.RemoteAddress) -contains $testAddress) 'FIREWALL_FILTER_SCOPE_NOT_TESTNET'
 }
 $args=@('-NoProfile','-NonInteractive','-File',('"' + $guard + '"'),'-TargetPid',([string]$owned.Id),'-StartTicks',([string]$owned.StartTime.ToUniversalTime().Ticks),'-ExpectedExe',('"' + [string]$owned.Path + '"'),'-UdpRule',$ruleNames[0],'-TcpRule',$ruleNames[1],'-UdpWirelessRule',$ruleNames[2],'-TcpWirelessRule',$ruleNames[3])
 $watch=Start-Process -FilePath pwsh.exe -ArgumentList $args -PassThru -WindowStyle Hidden
 Start-Sleep -Seconds 2
 Check (!$watch.HasExited) 'WATCHDOG_EXITED_WHILE_EXACT_OWNER_ALIVE'
 Check (!$dummy.HasExited) 'DUMMY_OWNER_PREMATURELY_EXITED'
 Check (@(CurrentGuardRules).Count -eq 4) 'RULES_NOT_RETAINED_FOR_LIVE_OWNER'
 'HOSTED_WIRED_WIRELESS_TYPED_GUARDS_COVER_BOTH_MEDIA_PASS'
 'HOSTED_GUARD_RULES_RETAINED_FOR_EXACT_OWNER_PASS'
 Stop-Process -Id $owned.Id -Force -ErrorAction Stop
 $deadline=[DateTime]::UtcNow.AddSeconds(28)
 $receiptData=$null
 do {
  if(Test-Path -LiteralPath $receipt){
   try {
    $candidate=Get-Content -LiteralPath $receipt -Raw -Encoding UTF8|ConvertFrom-Json -ErrorAction Stop
    if([int]$candidate.targetPid -eq [int]$owned.Id){$receiptData=$candidate}
   }catch{}
  }
  if($receiptData -and @(CurrentGuardRules).Count -eq 0){break}
  Start-Sleep -Milliseconds 350
 }while([DateTime]::UtcNow -lt $deadline)
 Check (@(CurrentGuardRules).Count -eq 0) 'RULES_REMAIN_AFTER_EXACT_OWNER_EXIT'
 Check ($null -ne $receiptData -and [string]$receiptData.status -eq 'EXACT_OWNER_EXITED_AND_RULES_CLEANED') 'WATCHDOG_CLEANUP_RECEIPT_FAILED'
 'HOSTED_GUARD_EXACT_OWNER_EXIT_AND_ACTIVE_STORE_RULE_CLEANUP_PASS'
 $passed=$true
}catch{
 $failure=$_.Exception.Message
}finally{
 if($dummy){try{
  $actual=Get-Process -Id $dummy.Id -ErrorAction SilentlyContinue
  if($actual -and [long]$actual.StartTime.ToUniversalTime().Ticks -eq [long]$dummy.StartTime.ToUniversalTime().Ticks){Stop-Process -Id $dummy.Id -Force -ErrorAction SilentlyContinue}
 }catch{}}
 foreach($n in $created){
  $existing=Get-NetFirewallRule -Name $n -PolicyStore ActiveStore -ErrorAction SilentlyContinue
  if($existing){$existing|Remove-NetFirewallRule -ErrorAction SilentlyContinue}
 }
 $left=@(CurrentGuardRules)
 if($left.Count -ne 0){$passed=$false;$failure+='; GUARD_RULES_REMAIN_AFTER_TEST_FINALLY'}
}
if(!$passed){
 if(!$failure){$failure='HOSTED_WATCHDOG_ACCEPTANCE_INCOMPLETE'}
 throw $failure
}
'HOSTED_GUARD_WATCHDOG_LIFECYCLE_PASS'
