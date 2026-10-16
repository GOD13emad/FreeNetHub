# Source-exact, unprivileged regression; mocks profile queries and does not change firewall settings.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$source=Join-Path $PSScriptRoot '..\gateway\apply_elevated.ps1'
$text=Get-Content -LiteralPath $source -Raw -Encoding UTF8
$start=$text.IndexOf(('if($pcNative){'+[char]10+' $activeProfiles='),[StringComparison]::Ordinal)
$end=$text.IndexOf(('if($pcNative -and'),[Math]::Max(0,$start),[StringComparison]::Ordinal)
if($start -lt 0 -or $end -le $start){throw 'FIREWALL_PROFILE_EXACT_SOURCE_BRANCH_NOT_FOUND'}
$predicate=[ScriptBlock]::Create($text.Substring($start,$end-$start))
$script:profiles=@()
$script:profileQueries=0
function Get-NetFirewallProfile {
 param([string]$PolicyStore,[string]$ErrorAction)
 if($PolicyStore -ne 'ActiveStore'){throw 'WRONG_POLICY_STORE'}
 $script:profileQueries++
 return $script:profiles
}
function Fail {param([string]$Message);throw $Message}
function Trial([string]$label,[array]$profiles,[bool]$expected) {
 $script:profiles=$profiles
 $script:profileQueries=0
 $pcNative=$true
 $errorText=''
 try { & $predicate } catch { $errorText=$_.Exception.Message }
 $passed=($errorText -eq '')
 if($passed -ne $expected){throw ('FIREWALL_PROFILE_'+$label+'_WRONG_RESULT_'+$errorText)}
 if($script:profileQueries -ne 1){throw ('FIREWALL_PROFILE_'+$label+'_NO_ACTIVE_QUERY')}
 if(!$passed -and $errorText -ne 'PC_NATIVE_FIREWALL_PROFILE_NOT_ENABLED'){throw ('FIREWALL_PROFILE_'+$label+'_WRONG_FAIL_REASON_'+$errorText)}
 'FIREWALL_PROFILE_'+$label+'_PASS'
}
function Profile([string]$name,[string]$enabled) { [pscustomobject]@{Name=$name;Enabled=$enabled} }
$all=@((Profile 'Domain' 'True'),(Profile 'Private' 'True'),(Profile 'Public' 'True'))
Trial 'ALL_ON' $all $true
Trial 'PUBLIC_OFF' @((Profile 'Domain' 'True'),(Profile 'Private' 'True'),(Profile 'Public' 'False')) $false
Trial 'PRIVATE_OFF' @((Profile 'Domain' 'True'),(Profile 'Private' 'False'),(Profile 'Public' 'True')) $false
Trial 'MISSING_PROFILE' @((Profile 'Domain' 'True'),(Profile 'Private' 'True')) $false
Trial 'UNEXPECTED_PROFILE' @((Profile 'Domain' 'True'),(Profile 'Private' 'True'),(Profile 'Unexpected' 'True')) $false
$script:profileQueries=0
$pcNative=$false
& $predicate
if($script:profileQueries -ne 0){throw 'CONSOLE_OR_NONNATIVE_SHOULD_NOT_QUERY_PROFILE'}
'FIREWALL_PROFILE_NONNATIVE_NOT_AFFECTED_PASS'
'FIREWALL_PROFILE_SOURCE_MOCK_ALL_PASS'
