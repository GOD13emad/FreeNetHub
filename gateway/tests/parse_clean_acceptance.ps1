$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$files=@(
  (Join-Path $PSScriptRoot 'dns_policy_check.ps1'),
  (Join-Path $PSScriptRoot 'static_gateway_check.ps1'),
  (Join-Path $PSScriptRoot 'elevated_final_acceptance_42rc.ps1'),
  (Join-Path $PSScriptRoot 'elevated_pc_tunnel_acceptance_42c2.ps1'),
  (Join-Path $PSScriptRoot 'elevated_pc_tunnel_acceptance.ps1')
)
$bad=@()
foreach($f in $files){
  $tokens=$null;$errors=$null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f,[ref]$tokens,[ref]$errors)
  foreach($e in @($errors)){$bad+=[pscustomobject]@{file=$f;message=$e.Message;extent=$e.Extent.Text}}
}
if($bad.Count){$bad|ConvertTo-Json -Depth 4;exit 1}
'GATEWAY_ACCEPTANCE_SCRIPT_PARSE=PASS'
