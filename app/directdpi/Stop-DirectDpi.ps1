[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$AppDir=Split-Path -Parent $PSScriptRoot
$Root=Split-Path -Parent $AppDir
$DirectDnsDir=Join-Path $AppDir 'directdns'
$Ctrld=Join-Path $DirectDnsDir 'ctrld.exe'
$DnsRuntimeDir=Join-Path $env:ProgramData 'FreeNetHub\directdns'
$StateDir=Join-Path $env:ProgramData 'FreeNetHub\directdpi'
$StatePath=Join-Path $StateDir 'state.json'
$EvidencePath=Join-Path $Root 'evidence\R36_DIRECT_DPI_STOP.json'
$ExpectedCtrld='FC966FD7DD5EE850A9709F632789CFB5BBC06C45D903D24B8ECFCE3306B658CD'

function Test-Admin{
 $id=[Security.Principal.WindowsIdentity]::GetCurrent()
 $p=[Security.Principal.WindowsPrincipal]::new($id)
 return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Write-JsonAtomic([string]$Path,$Value){
 $dir=Split-Path -Parent $Path
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
 [IO.File]::WriteAllText($tmp,($Value|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
 [IO.File]::Move($tmp,$Path,$true)
}
function Get-OwnedDrivers{
 @(
  Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue |
   Where-Object {$_.Name -match '^WinDivert' -and $_.PathName -and $_.PathName.Contains($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)}
 )
}
function Stop-OwnedWinws{
 Get-Process winws -ErrorAction SilentlyContinue |
  Where-Object {$_.Path -and $_.Path.StartsWith($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)} |
  Stop-Process -Force -ErrorAction SilentlyContinue
 Start-Sleep -Milliseconds 350
 foreach($d in @(Get-OwnedDrivers)){
  & sc.exe stop $d.Name|Out-Null
  Start-Sleep -Milliseconds 200
  & sc.exe delete $d.Name|Out-Null
 }
 Start-Sleep -Milliseconds 500
}
function Get-CtrldService{
 Get-CimInstance Win32_Service -Filter "Name='ctrld'" -ErrorAction SilentlyContinue
}
function Test-OwnedCtrldService($svc){
 if(-not $svc -or -not $svc.PathName){return $false}
 return $svc.PathName.Contains($Ctrld,[StringComparison]::OrdinalIgnoreCase)
}
function Get-CtrldCatchAll{
 @(
  Get-DnsClientNrptRule -ErrorAction SilentlyContinue |
   Where-Object {
    $ns=@($_.Namespace)|ForEach-Object{[string]$_}
    $sv=@($_.NameServers)|ForEach-Object{[string]$_}
    ($ns -contains '.') -and ($sv -contains '::1')
   } |
   ForEach-Object {[pscustomobject]@{Name=[string]$_.Name;Namespace=@($_.Namespace);NameServers=@($_.NameServers)}}
 )
}
function Cleanup-OwnedCtrld([string]$Iface){
 if(-not(Test-Path -LiteralPath $Ctrld)){throw 'DIRECT_DNS_BINARY_MISSING'}
 if((Get-FileHash -LiteralPath $Ctrld -Algorithm SHA256).Hash -ne $ExpectedCtrld){throw 'DIRECT_DNS_BINARY_HASH_MISMATCH'}
 $svc=Get-CtrldService
 if($svc -and -not(Test-OwnedCtrldService $svc)){throw 'DIRECT_DNS_FOREIGN_CTRLD_SERVICE'}
 if($svc){
  if($Iface){$out=@(& $Ctrld uninstall --iface $Iface -v 2>&1)}
  else{$out=@(& $Ctrld uninstall -v 2>&1)}
  $code=$LASTEXITCODE
  Start-Sleep -Seconds 2
  $svc2=Get-CtrldService
  if($svc2 -and (Test-OwnedCtrldService $svc2)){
   & sc.exe stop ctrld|Out-Null
   Start-Sleep -Milliseconds 500
   & sc.exe delete ctrld|Out-Null
   Start-Sleep -Milliseconds 700
  }
  if($code -ne 0 -and (Get-CtrldService)){throw ('DIRECT_DNS_UNINSTALL_EXIT_'+$code+'_'+($out -join ' | '))}
 }
 Get-Process ctrld -ErrorAction SilentlyContinue |
  Where-Object {$_.Path -and $_.Path.StartsWith($DirectDnsDir,[StringComparison]::OrdinalIgnoreCase)} |
  Stop-Process -Force -ErrorAction SilentlyContinue
 Start-Sleep -Milliseconds 300
}
function Get-IcsState{
 $s=Get-CimInstance Win32_Service -Filter "Name='SharedAccess'" -ErrorAction SilentlyContinue
 if(-not $s){return [ordered]@{exists=$false;state='';pid=0}}
 [ordered]@{exists=$true;state=[string]$s.State;pid=[int64]$s.ProcessId}
}

if(-not(Test-Admin)){
 $pwsh=(Get-Command pwsh.exe -ErrorAction Stop).Source
 $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath)
 $p=Start-Process -FilePath $pwsh -Verb RunAs -ArgumentList $args -PassThru -Wait
 exit $p.ExitCode
}

$actions=@()
if(-not(Test-Path -LiteralPath $StatePath)){
 Stop-OwnedWinws
 $svc=Get-CtrldService
 if($svc -and -not(Test-OwnedCtrldService $svc)){throw 'DIRECT_DNS_FOREIGN_CTRLD_SERVICE'}
 if($svc){
  Cleanup-OwnedCtrld ''
  $actions+='Removed FreeNetHub-owned encrypted DNS residue without touching interface DNS'
 }
 Remove-Item -LiteralPath $DnsRuntimeDir -Recurse -Force -ErrorAction SilentlyContinue
 $r=[ordered]@{
  schema=2;status='PASS_NO_STATE';actions=$actions
  ctrldCatchAll=@(Get-CtrldCatchAll)
 }
 Write-JsonAtomic $EvidencePath $r
 $r|ConvertTo-Json -Depth 8
 exit 0
}

$s=Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8|ConvertFrom-Json
try{
 if($s.pid){Stop-Process -Id ([int]$s.pid) -Force -ErrorAction SilentlyContinue}
 Stop-OwnedWinws
 $actions+='Stopped Direct-DPI winws and owned WinDivert driver'

 Cleanup-OwnedCtrld ([string]$s.interface)
 $actions+='Stopped and uninstalled FreeNetHub-owned encrypted DNS service'

 if([string]$s.preDnsMode -eq 'DHCP'){
  Set-DnsClientServerAddress -InterfaceAlias ([string]$s.interface) -ResetServerAddresses
 }elseif(@($s.preDns).Count){
  Set-DnsClientServerAddress -InterfaceAlias ([string]$s.interface) -ServerAddresses @($s.preDns)
 }
 Clear-DnsClientCache -ErrorAction SilentlyContinue
 $actions+='Restored pre-Direct-DPI interface DNS state'

 Remove-Item -LiteralPath $DnsRuntimeDir -Recurse -Force -ErrorAction SilentlyContinue
 Remove-Item -LiteralPath $StatePath -Force

 $leftProc=@(Get-Process winws -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($PSScriptRoot,[StringComparison]::OrdinalIgnoreCase)})
 $leftDrv=@(Get-OwnedDrivers)
 $leftRoute=@(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue|Where-Object{$_.DestinationPrefix -in @('0.0.0.0/1','128.0.0.0/1')})
 $leftCtrldProc=@(Get-Process ctrld -ErrorAction SilentlyContinue|Where-Object{$_.Path -and $_.Path.StartsWith($DirectDnsDir,[StringComparison]::OrdinalIgnoreCase)})
 $leftCtrldSvc=Get-CtrldService
 $catchAll=@(Get-CtrldCatchAll)
 $allowedCatchAll=[int]$s.preCtrldCatchAllCount
 $ics=Get-IcsState

 if($leftProc.Count -or $leftDrv.Count -or $leftRoute.Count -or $leftCtrldProc.Count){throw 'DIRECT_DPI_ROLLBACK_INCOMPLETE'}
 if($leftCtrldSvc -and (Test-OwnedCtrldService $leftCtrldSvc)){throw 'DIRECT_DNS_SERVICE_REMAINS'}
 if($catchAll.Count -gt $allowedCatchAll){throw 'DIRECT_DNS_NRPT_RESIDUE'}
 if($s.preIcs.exists -and ($ics.state -ne [string]$s.preIcs.state -or $ics.pid -ne [int64]$s.preIcs.pid)){throw 'DIRECT_DNS_ICS_CHANGED_ON_STOP'}

 $r=[ordered]@{
  schema=2;status='PASS';actions=$actions
  dns=@((Get-DnsClientServerAddress -InterfaceAlias ([string]$s.interface) -AddressFamily IPv4).ServerAddresses)
  ctrldCatchAll=$catchAll;ics=$ics
 }
 Write-JsonAtomic $EvidencePath $r
 $r|ConvertTo-Json -Depth 10
 exit 0
}catch{
 $r=[ordered]@{schema=2;status='FAIL';actions=$actions;error=$_.Exception.Message}
 Write-JsonAtomic $EvidencePath $r
 $r|ConvertTo-Json -Depth 8
 exit 9
}
