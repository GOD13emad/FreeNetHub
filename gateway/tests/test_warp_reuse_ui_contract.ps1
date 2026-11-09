[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ui=Join-Path $repo 'app\FreeNetHub.ps1'
$request=Join-Path $repo 'gateway\gateway_request.ps1'
$controller=Join-Path $repo 'gateway\gateway_control.ps1'
$uast=$null
foreach($p in @($ui,$request,$controller)){
 $tokens=$null;$errors=$null
 $ast=[Management.Automation.Language.Parser]::ParseFile($p,[ref]$tokens,[ref]$errors)
 if(@($errors).Count){throw ('SCRIPT_PARSE_ERROR_'+(Split-Path $p -Leaf))}
 if($p -eq $ui){$uast=$ast}
}
$fn=$uast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-WarpLoopbackPortCandidate'},$true)
if(!$fn){throw 'UI_WARP_REUSE_CANDIDATE_HELPER_MISSING'}
. ([ScriptBlock]::Create($fn.Extent.Text))
$script:ListenRows=@()
$script:QueryThrows=$false
function Get-NetTCPConnection{
 param([string]$State,[int]$LocalPort,$ErrorAction)
 if($State -ne 'Listen' -or $LocalPort -ne 19410){throw 'UNEXPECTED_LOOPBACK_QUERY'}
 if($script:QueryThrows){throw 'INJECTED_UNRELIABLE_NETTCP_QUERY'}
 return $script:ListenRows
}
function Expect-WarpPort([bool]$want,[string]$case){
 $got=Test-WarpLoopbackPortCandidate
 if([bool]$got -ne $want){throw ('WARP_LOOPBACK_CANDIDATE_'+$case+'_EXPECTED_'+$want+'_GOT_'+$got)}
}
$script:ListenRows=@([pscustomobject]@{LocalAddress='127.0.0.1';OwningProcess=4221})
Expect-WarpPort $true 'VALID_PIN_CANDIDATE'
if(Test-WarpLoopbackPortCandidate -port 19415){throw 'WRONG_PORT_ADMITTED'}
$script:ListenRows=@()
Expect-WarpPort $false 'NO_LISTENER'
$script:ListenRows=@([pscustomobject]@{LocalAddress='0.0.0.0';OwningProcess=4221})
Expect-WarpPort $false 'WILDCARD_LISTENER'
$script:ListenRows=@([pscustomobject]@{LocalAddress='::1';OwningProcess=4221})
Expect-WarpPort $false 'IPV6_ONLY'
$script:ListenRows=@([pscustomobject]@{LocalAddress='127.0.0.1';OwningProcess=0})
Expect-WarpPort $false 'UNOWNED_PID'
$script:ListenRows=@(
 [pscustomobject]@{LocalAddress='127.0.0.1';OwningProcess=4221}
 [pscustomobject]@{LocalAddress='::1';OwningProcess=4221}
)
Expect-WarpPort $false 'MULTIPLE_LISTENERS'
$script:QueryThrows=$true
Expect-WarpPort $false 'UNRELIABLE_DISCOVERY'
$script:QueryThrows=$false
$uiSource=[IO.File]::ReadAllText($ui)
$requestSource=[IO.File]::ReadAllText($request)
$controlSource=[IO.File]::ReadAllText($controller)
foreach($source in @($uiSource,$requestSource)){
 if(!$source.Contains('-ReuseVerifiedWarp')){throw 'UI_REQUEST_CHAIN_MISSING_REUSE_SWITCH'}
}
if(!$uiSource.Contains('$reuseExistingWarp=Test-WarpLoopbackPortCandidate')){throw 'UI_NOT_CONDITIONED_ON_READONLY_PORT'}
if(!$uiSource.Contains('if($provider -eq ''WARP'' -and $reuseExistingWarp)')){throw 'UI_NONWARP_FLAG_SCOPE_UNVERIFIED'}
if(!$uiSource.Contains('SHA-256') -or !$uiSource.Contains('[Windows.MessageBox]::Show($notice')){throw 'USER_EXPLICIT_CONSENT_BROKEN'}
if(!$requestSource.Contains('if($ReuseVerifiedWarp -and ($Action -ne ''StartPc'' -or $Provider -ne ''WARP''))')){throw 'REQUEST_NONWARP_REUSE_NOT_REJECTED'}
if(!$requestSource.Contains('if($ReuseVerifiedWarp){$args+= ''-ReuseVerifiedWarp''}')){throw 'REQUEST_SWITCH_NOT_FORWARDED'}
if(!$controlSource.Contains('if($ReuseVerifiedWarp -and ($Action -ne ''StartPc'' -or $Provider -ne ''WARP''))')){throw 'CONTROLLER_REUSE_SCOPE_BROKEN'}
if(!$controlSource.Contains('function Get-VerifiedInstalledWarp')){throw 'CONTROLLER_STRICT_OWNER_IDENTITY_BROKEN'}
'WARP_REUSE_UI_READONLY_CANDIDATE_AND_7_NEGATIVE_CASES_PASS'
'WARP_REUSE_UI_REQUEST_CONTROLLER_CONSENT_AND_SCOPE_CHAIN_PASS'
