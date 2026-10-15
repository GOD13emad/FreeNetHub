# Execute exact pre-owner apply rollback source with in-memory mocks only.
# No real NIC, process, DNS or Windows Firewall mutation occurs.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\apply_elevated.ps1'
$text=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$startMarker='  if($pcNative){'+[char]10+'   # Fail closed: never release physical DNS blocks'
$endMarker="  if("+'$Mode'+" -eq 'CONSOLE_ONLY' -and (Test-Path "+'$Pre'+"))"
$start=$text.IndexOf($startMarker,[StringComparison]::Ordinal)
if($start -lt 0){throw 'FAILSTART_EXACT_BRANCH_START_MISSING'}
$end=$text.IndexOf($endMarker,$start,[StringComparison]::Ordinal)
if($end -lt 0){throw 'FAILSTART_EXACT_BRANCH_END_MISSING'}
$exact=$text.Substring($start,$end-$start)
if($exact.Split('AddSeconds(15)').Count -ne 2){throw 'FAILSTART_15_SECOND_DEADLINE_CHANGED'}
if($exact -notmatch 'APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED'){throw 'FAILSTART_RETENTION_MARKER_MISSING'}
if($exact -notmatch 'Get-NetAdapter -IncludeHidden -ErrorAction Stop'){throw 'FAILSTART_REQUIRES_TERMINATING_ADAPTER_QUERY'}
if($exact -notmatch 'Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction Stop'){throw 'FAILSTART_REQUIRES_TERMINATING_FIREWALL_QUERY'}
$testCode=[ScriptBlock]::Create($exact.Replace('AddSeconds(15)','AddMilliseconds(45)'))
$script:rules=$null
$script:virtualTunPresent=$false
$script:adapterReadError=$false
$script:firewallReadError=$false
$script:removeCalls=@()
$script:firewallMode='normal'
function Get-NetAdapter {
 param([switch]$IncludeHidden,[string]$ErrorAction)
 if($script:adapterReadError){throw 'SIMULATED_ADAPTER_QUERY_FAILURE'}
 if($script:virtualTunPresent){[pscustomobject]@{Name='FreeNetHub'}}
}
function Get-NetFirewallRule {
 param([string]$Name,[string]$PolicyStore,[string]$ErrorAction)
 if($script:firewallReadError){throw 'SIMULATED_FIREWALL_QUERY_FAILURE'}
 foreach($n in $script:rules){if(!$Name -or $n -eq $Name){[pscustomobject]@{Name=$n}}}
}
function Remove-NetFirewallRule {
 param([string]$Name,[string]$PolicyStore,[string]$ErrorAction)
 if(!$script:rules.Contains($Name)){throw 'MUST_NOT_REMOVE_UNOWNED_RULE'}
 $script:removeCalls+= $Name
 if($script:firewallMode -eq 'failed'){throw 'SIMULATED_RULE_REMOVE_FAILED'}
 [void]$script:rules.Remove($Name)
 if($script:firewallMode -eq 'concurrent' -and $script:removeCalls.Count -eq 1){throw 'SIMULATED_CONCURRENT_REMOVAL'}
}
function Start-Sleep {param([int]$Milliseconds,[int]$Seconds)}
function Fail {param([string]$Message);throw $Message}
function Run-Test([string]$label,[bool]$tunPresent,[bool]$adapterFails,[string]$firewallMode,[string]$expectedFailure,[int]$expectedRemoved){
 $script:virtualTunPresent=$tunPresent
 $script:adapterReadError=$adapterFails
 $script:firewallReadError=($firewallMode -eq 'queryFailed')
 $script:firewallMode=$firewallMode
 $script:rules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 $script:removeCalls=@()
 $ownedCreatedDnsRules=@('FreeNetHub-PC-DNS53-Guard-UDP-Wired','FreeNetHub-PC-DNS53-Guard-TCP-Wired','FreeNetHub-PC-DNS53-Guard-UDP-Wireless','FreeNetHub-PC-DNS53-Guard-TCP-Wireless')
 foreach($n in @($ownedCreatedDnsRules+'Unrelated-Never-Touch')){[void]$script:rules.Add($n)}
 $pcNative=$true
 $D=[pscustomobject]@{tun=[pscustomobject]@{interface_name='FreeNetHub'}}
 $primaryError='MOCK_PRE_OWNER_STARTUP_FAILURE'
 $err=''
 try{& $testCode}catch{$err=$_.Exception.Message}
 if($expectedFailure){
  if($err -notlike ($expectedFailure+'*')){throw ($label+'_FAILURE_WRONG_'+$err)}
 }elseif($err){throw ($label+'_UNEXPECTED_'+$err)}
 if($script:removeCalls.Count -ne $expectedRemoved){throw ($label+'_REMOVALS_'+$script:removeCalls.Count)}
 if(!$script:rules.Contains('Unrelated-Never-Touch')){throw ($label+'_UNRELATED_RULE_TOUCHED')}
 $actualRemoved=if($firewallMode -eq 'failed'){0}else{$expectedRemoved}
 if($script:rules.Count -ne (5-$actualRemoved)){throw ($label+'_BAD_REMAINING_RULES')}
 $label+'_PASS'
}
Run-Test 'MOCK_PERSISTING_TUN_RULES_RETAINED' $true $false 'normal' 'APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED' 0
Run-Test 'MOCK_ABSENT_TUN_ONLY_OWNED_RULES_REMOVED' $false $false 'normal' '' 4
Run-Test 'MOCK_ADAPTER_ENUMERATION_ERROR_RULES_RETAINED' $false $true 'normal' 'APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED' 0
Run-Test 'MOCK_CONCURRENT_RULE_REMOVAL_VERIFIED_CONVERGENCE' $false $false 'concurrent' '' 4
Run-Test 'MOCK_FIREWALL_QUERY_ERROR_RULES_RETAINED' $false $false 'queryFailed' 'SIMULATED_FIREWALL_QUERY_FAILURE' 0
Run-Test 'MOCK_FIREWALL_REMOVE_ERROR_RULES_RETAINED' $false $false 'failed' 'APPLY_FAILED_PC_DNS_GUARD_ROLLBACK_INCOMPLETE' 1
# A failed removal is attempted, but all rules must remain present.
# Preflight query must also fail rather than mistake an inaccessible NIC for absence.
$preStart=$text.IndexOf('try{'+[char]10+' $existingTun=',[StringComparison]::Ordinal)
$preEnd=$text.IndexOf('$D=Get-Content',[Math]::Max(0,$preStart),[StringComparison]::Ordinal)
if($preStart -lt 0 -or $preEnd -le $preStart){throw 'PRE_START_TUN_QUERY_BRANCH_MISSING'}
$preTest=[ScriptBlock]::Create($text.Substring($preStart,$preEnd-$preStart))
$script:adapterReadError=$true
$script:virtualTunPresent=$false
$actual=''
try{& $preTest}catch{$actual=$_.Exception.Message}
if($actual -ne 'TUN_PREFLIGHT_QUERY_UNVERIFIED'){throw 'PREFLIGHT_ADAPTER_QUERY_FAILED_OPEN'}
'MOCK_PREFLIGHT_ADAPTER_QUERY_FAIL_CLOSED_PASS'
'EXACT_SOURCE_FAILSTART_MOCK_PASS'
