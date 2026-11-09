[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$p=(Resolve-Path (Join-Path $PSScriptRoot '..\stop_elevated.ps1')).Path
$t=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($p,[ref]$t,[ref]$errors)
if(@($errors).Count){throw 'NATIVE_STOP_PARSE_FAILED'}
$f=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Wait-OwnedSingBoxFinalIdentity'},$true)
if(!$f){throw 'BOUNDED_OWNER_IDENTITY_SETTLE_MISSING'}
if($f.Extent.Text -match '(?i)(Stop-Process|taskkill|Remove-Net|pnputil|Remove-Item)'){throw 'READONLY_PROCESS_SETTLE_MUST_NOT_MUTATE'}
. ([ScriptBlock]::Create($f.Extent.Text))
$script:Expected=@()
$script:Observed=0
$script:Slept=0
function Process-Identity($o){
 $script:Observed++
 if($null -eq $o -or $o.tag -ne 'isolated-owner'){throw 'INVALID_OWNER_FIXTURE'}
 $p=[Math]::Min($script:Observed - 1,$script:Expected.Count-1)
 return [string]$script:Expected[$p]
}
function Start-Sleep {
 param([int]$Milliseconds)
 if($Milliseconds -lt 0 -or $Milliseconds -gt 200){throw 'UNBOUNDED_SLEEP_ATTEMPT'}
 $script:Slept++
}
function Case([string]$label,[string[]]$states,[string]$want,[int]$queries,[int]$sleeps){
 $script:Expected=@($states)
 $script:Observed=0
 $script:Slept=0
 $r=Wait-OwnedSingBoxFinalIdentity ([pscustomobject]@{tag='isolated-owner'}) -Checks 5 -PollMs 1
 if($r -ne $want -or $script:Observed -ne $queries -or $script:Slept -ne $sleeps){
  throw ('IDENTITY_SETTLE_'+$label+'_RESULT_'+$r+'_OBS_'+$script:Observed+'_SLEEPS_'+$script:Slept)
 }
}
Case 'ABSENT_FIRST' @('ABSENT') 'ABSENT' 1 0
Case 'TRANSIENT_UNVERIFIED' @('UNVERIFIED','ABSENT') 'ABSENT' 2 1
Case 'EXACT_TO_DIFFERENT' @('EXACT','UNVERIFIED','DIFFERENT') 'DIFFERENT' 3 2
Case 'EXACT_PERSISTENT' @('EXACT') 'EXACT' 5 4
Case 'UNVERIFIED_PERSISTENT' @('UNVERIFIED') 'UNVERIFIED' 5 4
Case 'UNKNOWN_PERSISTENT' @('UNEXPECTED') 'UNEXPECTED' 5 4
$src=[IO.File]::ReadAllText($p)
foreach($mark in @(
 'if($settled -eq ''UNVERIFIED''){Fail ''OWNED_SINGBOX_IDENTITY_UNVERIFIED_AFTER_STOP'' $o}',
 'if($settled -eq ''EXACT''){Fail ''OWNED_SINGBOX_STOP_INCOMPLETE'' $o}',
 'if($settled -notin @(''ABSENT'',''DIFFERENT'')){Fail ''OWNED_SINGBOX_UNKNOWN_FINAL_IDENTITY'' $o}'
)){
 if(!$src.Contains($mark)){throw ('NATIVE_STOP_FAILCLOSED_BRANCH_MISSING_'+$mark)}
}
'V554_BOUNDED_OWNER_STOP_IDENTITY_CONVERGENCE_SIX_CASES_PASS'
