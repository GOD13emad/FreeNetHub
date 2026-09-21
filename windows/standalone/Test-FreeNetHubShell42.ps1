$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class U32 {
[DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h,int n);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,IntPtr l);
[DllImport("user32.dll", EntryPoint="GetClassLongPtrW")] public static extern IntPtr GetClassLongPtr64(IntPtr h,int n);
[DllImport("user32.dll", EntryPoint="GetClassLongW")] public static extern IntPtr GetClassLong32(IntPtr h,int n);
public static IntPtr GCL(IntPtr h,int n){return IntPtr.Size==8?GetClassLongPtr64(h,n):GetClassLong32(h,n);}
}
'@
$Root=(Resolve-Path "$PSScriptRoot\..\..").Path;$exe=Join-Path $PSScriptRoot 'FreeNetHub.exe';$app=Join-Path $Root 'app\FreeNetHub.ps1'
Get-CimInstance Win32_Process|Where-Object{($_.ExecutablePath -eq $exe) -or ($_.Name -eq 'pwsh.exe' -and $_.CommandLine -match 'FreeNetHub\\app\\FreeNetHub.ps1')}|ForEach-Object{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue};Start-Sleep -Milliseconds 600
$beforeTerm=@(Get-Process WindowsTerminal,OpenConsole -ErrorAction SilentlyContinue|Select-Object Id,StartTime)
$p=Start-Process -FilePath $exe -ArgumentList @($app) -PassThru;Start-Sleep -Seconds 4
$shell1=Get-Process -Id $p.Id -ErrorAction Stop
$child1=Get-CimInstance Win32_Process|Where-Object{$_.ParentProcessId -eq $shell1.Id -and $_.Name -eq 'pwsh.exe' -and $_.CommandLine -match 'FreeNetHub\\app\\FreeNetHub.ps1'}|Select-Object -First 1
if(!$child1){throw 'UI_CHILD_NOT_FOUND'};$cp=Get-Process -Id $child1.ProcessId -ErrorAction Stop;$h=$cp.MainWindowHandle;if($h -eq 0){throw 'UI_WINDOW_NOT_FOUND'}
$owner=Get-Content (Join-Path $Root 'jobs\ui-owner.json') -Raw -Encoding UTF8|ConvertFrom-Json
$big=[U32]::SendMessage($h,0x7F,[IntPtr]1,[IntPtr]0);if($big -eq [IntPtr]::Zero){$big=[U32]::GCL($h,-14)}
$small=[U32]::SendMessage($h,0x7F,[IntPtr]0,[IntPtr]0);if($small -eq [IntPtr]::Zero){$small=[U32]::GCL($h,-34)}
$p2=Start-Process -FilePath $exe -ArgumentList @($app) -PassThru;Start-Sleep -Seconds 2
$shell2=@(Get-CimInstance Win32_Process|Where-Object{$_.ExecutablePath -eq $exe})
$child2=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -eq 'pwsh.exe' -and $_.CommandLine -match 'FreeNetHub\\app\\FreeNetHub.ps1'})
$single=($shell2.Count -eq 1 -and $shell2[0].ProcessId -eq $shell1.Id -and $child2.Count -eq 1 -and $child2[0].ProcessId -eq $child1.ProcessId)
[void][U32]::ShowWindowAsync($h,6);Start-Sleep -Seconds 2;$hidden=(-not [U32]::IsWindowVisible($h))
$p3=Start-Process -FilePath $exe -ArgumentList @($app) -PassThru;Start-Sleep -Seconds 2;$restored=[U32]::IsWindowVisible($h) -and -not [U32]::IsIconic($h)
$afterTerm=@(Get-Process WindowsTerminal,OpenConsole -ErrorAction SilentlyContinue|Select-Object Id,StartTime)
$newTerm=@($afterTerm|Where-Object{$id=$_.Id;-not ($beforeTerm|Where-Object{$_.Id -eq $id})})
$usbState='';$u='C:\Program Files\usbipd-win\usbipd.exe';if(Test-Path $u){$line=& $u list 2>$null|Select-String '0bda:8153'|Select-Object -First 1;if($line){$usbState=([string]$line.Line -split '\s{2,}')[-1]}};$net=[ordered]@{tun=@(Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue|Where-Object{$_.Name -eq 'FreeNetHub'}).Count;p19410=@(Get-NetTCPConnection -State Listen -LocalPort 19410 -ErrorAction SilentlyContinue).Count;p19591=@(Get-NetTCPConnection -State Listen -LocalPort 19591 -ErrorAction SilentlyContinue).Count;p19594=@(Get-NetTCPConnection -State Listen -LocalPort 19594 -ErrorAction SilentlyContinue).Count;wslOwner=(Test-Path (Join-Path $Root 'gateway\runtime\wsl-console-owner.json'));providerOwner=(Test-Path (Join-Path $Root 'gateway\runtime\console-provider-owner.json'));usbAttached=($usbState -eq 'Attached')}
$r=[ordered]@{schema=1;utc=[DateTimeOffset]::UtcNow.ToString('o');exeVersion=[Diagnostics.FileVersionInfo]::GetVersionInfo($exe).FileVersion;exeSha256=(Get-FileHash $exe -Algorithm SHA256).Hash;shellPid=$shell1.Id;childPid=$child1.ProcessId;singleInstance=$single;minimizeHiddenToTray=$hidden;restoredVisible=$restored;taskbarWindowIconSet=($big -ne [IntPtr]::Zero -and $small -ne [IntPtr]::Zero);ownerAppUserModelId=[string]$owner.appUserModelId;ownerAppUserModelIdResult=[int]$owner.appUserModelIdResult;processAppUserModelIdSet=([int]$owner.appUserModelIdResult -eq 0);noNewTerminalProcesses=($newTerm.Count -eq 0);networkRequested=$false;networkArtifacts=$net;accepted=($single -and $hidden -and $restored -and $big -ne [IntPtr]::Zero -and $small -ne [IntPtr]::Zero -and [int]$owner.appUserModelIdResult -eq 0 -and $newTerm.Count -eq 0 -and $net.tun -eq 0 -and $net.p19410 -eq 0 -and $net.p19591 -eq 0 -and $net.p19594 -eq 0 -and -not $net.wslOwner -and -not $net.providerOwner -and -not $net.usbAttached)}
$r|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Root 'evidence\SHELL_420_ACCEPTANCE.json') -Encoding UTF8
$r|ConvertTo-Json -Depth 8
Get-CimInstance Win32_Process|Where-Object{($_.ExecutablePath -eq $exe) -or ($_.Name -eq 'pwsh.exe' -and $_.CommandLine -match 'FreeNetHub\\app\\FreeNetHub.ps1')}|ForEach-Object{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
if(!$r.accepted){exit 20}
