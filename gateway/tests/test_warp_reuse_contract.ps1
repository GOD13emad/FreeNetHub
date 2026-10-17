[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$rootDir=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$control=Join-Path $rootDir 'gateway\gateway_control.ps1'
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($control,[ref]$tokens,[ref]$parseErrors)
if(@($parseErrors).Count){throw 'CONTROLLER_POWERSHELL_PARSE_FAILED'}
$functionAst=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-VerifiedInstalledWarp'},$true)
if(!$functionAst){throw 'REUSE_FUNCTION_MISSING'}
. ([ScriptBlock]::Create($functionAst.Extent.Text))
function Assert([bool]$ok,[string]$message){if(!$ok){throw $message}}
function Get-NetTCPConnection{
 param([int]$LocalPort,[string]$State,$ErrorAction)
 if($LocalPort -ne 19410 -or $State -ne 'Listen'){throw 'UNEXPECTED_NETWORK_READ'}
 $script:QueryCount++
 return [pscustomobject]@{LocalAddress=$script:ListenerAddress;OwningProcess=$(if($script:ChangeOwner -and $script:QueryCount -gt 1){4322}else{4321})}
}
function Get-CimInstance{
 param($ClassName,[string]$Filter,$ErrorAction)
 if($ClassName -ne 'Win32_Process' -or $Filter -ne 'ProcessId=4321'){throw 'UNEXPECTED_CIM'}
 return [pscustomobject]@{Name=$script:ExeName;ExecutablePath=$script:ExecutablePath;CommandLine=$script:CommandLine}
}
function Get-Process{
 param([int]$Id,$ErrorAction)
 if($Id -ne 4321){throw 'UNEXPECTED_PID'}
 return [pscustomobject]@{StartTime=$script:StartTime}
}
function Verify-ProviderUdp{throw 'IDENTITY_ONLY_MUST_NOT_USE_NETWORK'}
function curl.exe{throw 'IDENTITY_ONLY_MUST_NOT_USE_CURL'}
$td=Join-Path ([IO.Path]::GetTempPath()) ('fnh-warp-reuse-test-'+[guid]::NewGuid().ToString('N'))
try{
 [IO.Directory]::CreateDirectory((Join-Path $td 'app'))|Out-Null
 $bin=Join-Path $td 'warp-plus.exe'
 [IO.File]::WriteAllBytes($bin,[byte[]](0x4d,0x5a,0x53,0x41,0x46,0x45))
 $sha=(Get-FileHash $bin -Algorithm SHA256).Hash
 $Root=$td
 $Defaults=[pscustomobject]@{providers=[pscustomobject]@{WARP=[pscustomobject]@{type='socks';host='127.0.0.1';port=19410;udp=$true}}}
 $deps=Join-Path $td 'app\dependencies.json'
 $pinned=[ordered]@{warp=[ordered]@{path=$bin;sha256=$sha}}
 [IO.File]::WriteAllText($deps,($pinned|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
 function Reset-Fixture{
  $script:QueryCount=0;$script:ListenerAddress='127.0.0.1';$script:ChangeOwner=$false
  $script:ExeName='warp-plus.exe';$script:ExecutablePath=$bin
  $script:CommandLine='"warp-plus.exe" -4 --bind 127.0.0.1:19410 --cache-dir C:\FnhTest'
  $script:StartTime=[datetime]'2026-10-17T00:00:00Z'
 }
 function Assert-Failed([string]$expected){
  try{$null=Get-VerifiedInstalledWarp -IdentityOnly;throw 'UNSAFE_FALSE_PASS'}
  catch{if($_.Exception.Message -notlike ('*'+$expected+'*')){throw ('WRONG_FAILURE:'+ $_.Exception.Message)}}
 }
 Reset-Fixture
 $positive=Get-VerifiedInstalledWarp -IdentityOnly
 if($positive.status -ne 'REUSE_PINNED_INSTALLED_WARP_PASS' -or $positive.pid -ne 4321 -or $positive.engineOwnershipTransferred -ne $false -or $positive.udpVerified -ne $false){throw 'PINNED_IDENTITY_POSITIVE_INVALID'}
 Reset-Fixture;$script:ListenerAddress='0.0.0.0';Assert-Failed 'REUSE_WARP_LISTENER_NOT_EXCLUSIVE_LOOPBACK'
 Reset-Fixture;$script:ExeName='not-warp.exe';Assert-Failed 'REUSE_WARP_WRONG_PROCESS'
 Reset-Fixture;$script:ExecutablePath=Join-Path $td 'other-warp.exe';Assert-Failed 'REUSE_WARP_FOREIGN_BINARY'
 Reset-Fixture;$script:CommandLine='"warp-plus.exe" --bind 0.0.0.0:19410';Assert-Failed 'REUSE_WARP_BIND_NOT_VERIFIED'
 Reset-Fixture;$script:ChangeOwner=$true;Assert-Failed 'REUSE_WARP_LISTENER_CHANGED'
 $pinned.warp.sha256='0'*64
 [IO.File]::WriteAllText($deps,($pinned|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
 Reset-Fixture;Assert-Failed 'REUSE_WARP_BINARY_HASH_CHANGED'
 'WARP_REUSE_IDENTITY_POSITIVE_AND_SIX_NEGATIVES_PASS'
}
finally{
 if(Test-Path -LiteralPath $td){Remove-Item -LiteralPath $td -Recurse -Force -ErrorAction SilentlyContinue}
}
