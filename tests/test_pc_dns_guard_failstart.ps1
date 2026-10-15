# Unprivileged execution of the exact failed-start branch with mocked firewall/NIC functions.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\apply_elevated.ps1'
$text=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$startMarker='  if($pcNative){'+[char]10+'   # Fail closed: never release physical DNS blocks'
$endMarker="  if("+ '$Mode' +" -eq 'CONSOLE_ONLY' -and (Test-Path "+ '$Pre' +"))"
$start=$text.IndexOf($startMarker,[StringComparison]::Ordinal)
if($start -lt 0){throw 'FAILSTART_EXACT_BRANCH_START_MISSING'}
$end=$text.IndexOf($endMarker,$start,[StringComparison]::Ordinal)
if($end -lt 0){throw 'FAILSTART_EXACT_BRANCH_END_MISSING'}
$exact=$text.Substring($start,$end-$start)
if($exact.Split('AddSeconds(15)').Count -ne 2){throw 'FAILSTART_15_SECOND_DEADLINE_CHANGED'}
if($exact -notmatch 'APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED'){throw 'FAILSTART_RETENTION_MARKER_MISSING'}
$testCode=[ScriptBlock]::Create($exact.Replace('AddSeconds(15)','AddMilliseconds(40)'))
$script:rules=$null
$script:virtualTunPresent=$false
$script:removeCalls=@()
function Get-NetAdapter {
 param([switch]$IncludeHidden)
 if($script:virtualTunPresent){[pscustomobject]@{Name='FreeNetHub'}}
}
function Get-NetFirewallRule {
 param([string]$Name,[string]$PolicyStore)
 if($script:rules.Contains($Name)){[pscustomobject]@{Name=$Name}}
}
function Remove-NetFirewallRule {
 param([Parameter(ValueFromPipeline=$true)]$InputObject)
 process {
  if($null -eq $InputObject){throw 'NULL_MOCK_FIREWALL_OBJECT'}
  $script:removeCalls+= [string]$InputObject.Name
  [void]$script:rules.Remove([string]$InputObject.Name)
 }
}
function Start-Sleep {param([int]$Milliseconds,[int]$Seconds)}
function Fail {param([string]$Message); throw $Message}
function Run-Test([bool]$tunPresent,[bool]$expectFail){
 $script:virtualTunPresent=$tunPresent
 $script:rules=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 $script:removeCalls=@()
 $ownedCreatedDnsRules=@('FreeNetHub-PC-DNS53-Guard-UDP','FreeNetHub-PC-DNS53-Guard-TCP')
 foreach($n in @($ownedCreatedDnsRules+'Unrelated-Never-Touch')){[void]$script:rules.Add($n)}
 $pcNative=$true
 $D=[pscustomobject]@{tun=[pscustomobject]@{interface_name='FreeNetHub'}}
 $primaryError='MOCK_PRE_OWNER_STARTUP_FAILURE'
 $err=''
 try { & $testCode }catch{$err=$_.Exception.Message}
 if($expectFail){
  if($err -notlike 'APPLY_FAILED_TUN_LINGERED_DNS_RULES_RETAINED*'){throw 'LINGERING_TUN_FAILED_OPEN_OR_WRONG_FAILURE'}
  if($script:removeCalls.Count -ne 0){throw 'LINGERING_TUN_REMOVED_GUARD'}
  if($script:rules.Count -ne 3){throw 'LINGERING_TUN_MUTATED_RULE_SET'}
  'MOCK_PERSISTING_TUN_RULES_RETAINED_PASS'
 }else{
  if($err){throw ('ABSENT_TUN_UNEXPECTED_ERROR '+$err)}
  if($script:removeCalls.Count -ne 2){throw 'ABSENT_TUN_OWNED_CLEANUP_MISSING'}
  if(!$script:rules.Contains('Unrelated-Never-Touch') -or $script:rules.Count -ne 1){throw 'ABSENT_TUN_TOUCHED_UNRELATED_FIREWALL'}
  'MOCK_ABSENT_TUN_ONLY_OWNED_RULES_REMOVED_PASS'
 }
}
Run-Test $true $true
Run-Test $false $false
'EXACT_SOURCE_FAILSTART_MOCK_PASS'
