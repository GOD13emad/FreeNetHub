[CmdletBinding()]
param(
 [Parameter(Mandatory)][string]$InstallRoot,
 [Parameter(Mandatory)][string]$EvidencePath
)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class FNHInstallU32 {
[DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h,int n);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,IntPtr l);
[DllImport("user32.dll", EntryPoint="GetClassLongPtrW")] public static extern IntPtr GetClassLongPtr64(IntPtr h,int n);
[DllImport("user32.dll", EntryPoint="GetClassLongW")] public static extern IntPtr GetClassLong32(IntPtr h,int n);
public static IntPtr GCL(IntPtr h,int n){return IntPtr.Size==8?GetClassLongPtr64(h,n):GetClassLong32(h,n);}
}
'@
$InstallRoot=(Resolve-Path -LiteralPath $InstallRoot).Path
$exe=Join-Path $InstallRoot 'FreeNetHub.exe';$app=Join-Path $InstallRoot 'app\FreeNetHub.ps1'
function Assert([bool]$ok,[string]$m){if(!$ok){throw $m}}
function Verify-Manifest([string]$Base,[string]$Manifest,[string]$Kind){
 $m=Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8|ConvertFrom-Json
 $rows=if($Kind -eq 'app'){@($m.code)}else{@($m.files)}
 foreach($f in $rows){
  $rel=if($Kind -eq 'app'){[string]$f.file}else{[string]$f.file}
  $fp=[IO.Path]::GetFullPath((Join-Path $Base $rel));$bp=[IO.Path]::GetFullPath($Base)+'\'
  Assert ($fp.StartsWith($bp,[StringComparison]::OrdinalIgnoreCase)) ($Kind+'_MANIFEST_PATH')
  Assert (Test-Path -LiteralPath $fp -PathType Leaf) ($Kind+'_MISSING_'+$rel)
  Assert ((Get-Item -LiteralPath $fp).Length -eq [long]$f.bytes) ($Kind+'_SIZE_'+$rel)
  Assert ((Get-FileHash -LiteralPath $fp -Algorithm SHA256).Hash -eq [string]$f.sha256) ($Kind+'_HASH_'+$rel)
 }
 return $rows.Count
}
Assert (Test-Path -LiteralPath $exe -PathType Leaf) 'EXE_MISSING'
Assert (Test-Path -LiteralPath $app -PathType Leaf) 'APP_MISSING'
$pwshPathFile=Join-Path $InstallRoot 'PWSH_PATH.txt'
Assert (Test-Path -LiteralPath $pwshPathFile -PathType Leaf) 'PWSH_PATH_RECORD_MISSING'
$storedPwsh=(Get-Content -LiteralPath $pwshPathFile -Raw -Encoding UTF8).Trim()
Assert ($storedPwsh -and (Test-Path -LiteralPath $storedPwsh -PathType Leaf)) 'PWSH_PATH_RECORD_INVALID'
$status=Get-Content -LiteralPath (Join-Path $InstallRoot 'INSTALL_RUNTIME_STATUS.json') -Raw -Encoding UTF8|ConvertFrom-Json
Assert ([string]$status.status -eq 'PASS') 'INSTALL_RUNTIME_NOT_PASS'
Assert ($status.gatewayCore -and [string]$status.gatewayCore.status -eq 'PASS' -and -not [bool]$status.gatewayCore.networkMutation) 'GATEWAY_CORE_NOT_ACCEPTED'
$appCount=Verify-Manifest (Join-Path $InstallRoot 'app') (Join-Path $InstallRoot 'app\manifest.json') 'app'
$gatewayCount=Verify-Manifest (Join-Path $InstallRoot 'gateway') (Join-Path $InstallRoot 'gateway\manifest.json') 'gateway'
$lg=Get-Content -LiteralPath (Join-Path $InstallRoot 'gateway\runtime\local_gateway.json') -Raw -Encoding UTF8|ConvertFrom-Json
$sb=[string]$lg.singbox.path
Assert ($sb.StartsWith(([IO.Path]::GetFullPath((Join-Path $InstallRoot 'gateway\runtime'))+'\'),[StringComparison]::OrdinalIgnoreCase)) 'SINGBOX_NOT_APP_LOCAL'
Assert (Test-Path -LiteralPath $sb -PathType Leaf) 'SINGBOX_MISSING'
Assert ((Get-FileHash -LiteralPath $sb -Algorithm SHA256).Hash -eq 'AAD0EDE010EAFA7B277E520464F3A66FDE820103D737EFF739F40F3CC9451DCC') 'SINGBOX_HASH'
$beforeTerm=@(Get-Process WindowsTerminal,OpenConsole -ErrorAction SilentlyContinue|Select-Object Id)
$p=$null;$child=$null
try{
 $p=Start-Process -FilePath $exe -ArgumentList @($app) -WorkingDirectory $InstallRoot -PassThru
 $deadline=[DateTime]::UtcNow.AddSeconds(12)
 do{
  Start-Sleep -Milliseconds 250
  $child=Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$p.Id) -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'pwsh.exe' -and $_.CommandLine -and $_.CommandLine.Contains($app,[StringComparison]::OrdinalIgnoreCase)}|Select-Object -First 1
  if($child){$cp=Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue;if($cp -and $cp.MainWindowHandle -ne 0){break}}
 }while([DateTime]::UtcNow -lt $deadline)
 Assert ($null -ne $child) 'UI_CHILD_NOT_FOUND'
 $cp=Get-Process -Id $child.ProcessId -ErrorAction Stop;$h=$cp.MainWindowHandle;Assert ($h -ne 0) 'UI_WINDOW_NOT_FOUND'
 $owner=Get-Content -LiteralPath (Join-Path $InstallRoot 'jobs\ui-owner.json') -Raw -Encoding UTF8|ConvertFrom-Json
 Assert ([int]$owner.pid -eq [int]$child.ProcessId) 'UI_OWNER_PID_MISMATCH'
 $big=[FNHInstallU32]::SendMessage($h,0x7F,[IntPtr]1,[IntPtr]0);if($big -eq [IntPtr]::Zero){$big=[FNHInstallU32]::GCL($h,-14)}
 $small=[FNHInstallU32]::SendMessage($h,0x7F,[IntPtr]0,[IntPtr]0);if($small -eq [IntPtr]::Zero){$small=[FNHInstallU32]::GCL($h,-34)}
 [void](Start-Process -FilePath $exe -ArgumentList @($app) -WorkingDirectory $InstallRoot -PassThru);Start-Sleep -Seconds 2
 $shells=@(Get-CimInstance Win32_Process|Where-Object{$_.ExecutablePath -eq $exe})
 $children=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -eq 'pwsh.exe' -and $_.CommandLine -and $_.CommandLine.Contains($app,[StringComparison]::OrdinalIgnoreCase)})
 $single=($shells.Count -eq 1 -and $shells[0].ProcessId -eq $p.Id -and $children.Count -eq 1 -and $children[0].ProcessId -eq $child.ProcessId)
 [void][FNHInstallU32]::ShowWindowAsync($h,6);Start-Sleep -Seconds 2;$hidden=(-not [FNHInstallU32]::IsWindowVisible($h))
 [void](Start-Process -FilePath $exe -ArgumentList @($app) -WorkingDirectory $InstallRoot -PassThru);Start-Sleep -Seconds 2
 $restored=[FNHInstallU32]::IsWindowVisible($h) -and -not [FNHInstallU32]::IsIconic($h)
 $afterTerm=@(Get-Process WindowsTerminal,OpenConsole -ErrorAction SilentlyContinue|Select-Object Id)
 $newTerm=@($afterTerm|Where-Object{$id=$_.Id;-not ($beforeTerm|Where-Object{$_.Id -eq $id})})
 $ports=@(19410,19413,19414,19450,19452,19453,19591,19594)
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$ports -contains $_.LocalPort})
 $tun=@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'})
 $r=[ordered]@{
  schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');installRoot=$InstallRoot
  version=[Diagnostics.FileVersionInfo]::GetVersionInfo($exe).FileVersion;exeSha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
  appManifestFiles=$appCount;gatewayManifestFiles=$gatewayCount;runtimeBootstrap='PASS';gatewayCore='PASS';pwshPathRecorded=$storedPwsh;singBoxSha256=(Get-FileHash -LiteralPath $sb -Algorithm SHA256).Hash
  shell=[ordered]@{singleInstance=$single;minimizeHiddenToTray=$hidden;restoredVisible=$restored;taskbarWindowIconSet=($big -ne [IntPtr]::Zero -and $small -ne [IntPtr]::Zero);appUserModelId=[string]$owner.appUserModelId;appUserModelIdResult=[int]$owner.appUserModelIdResult;noNewTerminalProcesses=($newTerm.Count -eq 0)}
  network=[ordered]@{requested=$false;tunCount=$tun.Count;projectPortListeners=$listeners.Count;wslOwner=(Test-Path -LiteralPath (Join-Path $InstallRoot 'gateway\runtime\wsl-console-owner.json'));providerOwner=(Test-Path -LiteralPath (Join-Path $InstallRoot 'gateway\runtime\console-provider-owner.json'))}
 }
 $r.accepted=($single -and $hidden -and $restored -and $big -ne [IntPtr]::Zero -and $small -ne [IntPtr]::Zero -and [int]$owner.appUserModelIdResult -eq 0 -and $newTerm.Count -eq 0 -and $tun.Count -eq 0 -and $listeners.Count -eq 0 -and -not $r.network.wslOwner -and -not $r.network.providerOwner)
 $r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $EvidencePath -Encoding UTF8
 $r|ConvertTo-Json -Depth 12
 if(!$r.accepted){exit 20}
}finally{
 if($child){Stop-Process -Id ([int]$child.ProcessId) -Force -ErrorAction SilentlyContinue}
 if($p){Stop-Process -Id ([int]$p.Id) -Force -ErrorAction SilentlyContinue}
}
