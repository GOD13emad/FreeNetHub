param([switch]$Smoke)
# FreeNet Hub 4.0. One UI; explicit browser-scoped operations. No automatic system VPN.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$script:Root=Split-Path $PSScriptRoot -Parent
$script:Task=$null;$script:Lease=$null;$script:Timer=$null;$script:Tray=$null;$script:AppIcon=$null;$script:CurrentMode='';$script:Health=$null;$script:Last=$null;$script:C=@{};$script:Tick=0;$script:Failures=0;$script:Repairs=0;$script:AllowClose=$false;$script:ShellHosted=($env:FREENETHUB_SHELL_HOST -eq '1')
function Read-Json([string]$p){if(!(Test-Path -LiteralPath $p)){return $null};if((Get-Item $p).Length -gt 4194304){throw 'RESULT_TOO_LARGE'};Get-Content -LiteralPath $p -Raw -Encoding utf8|ConvertFrom-Json -AsHashtable}
function Write-Json([string]$p,$v){$t=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllText($t,($v|ConvertTo-Json -Depth 18),[Text.UTF8Encoding]::new($false));[IO.File]::Move($t,$p,$true)}
function Sanitize($v){if($v -is [Collections.IDictionary]){$r=@{};foreach($k in $v.Keys){$r[$k]=if($k -in @('private_key','token','password','secret','home','localProxy')){'[redacted]'}elseif($k -in @('ip','endpoint') -and !$script:C.ShowIp.IsChecked){'[hidden]'}else{Sanitize $v[$k]}};return $r};if($v -is [array]){return ,@(foreach($x in $v){Sanitize $x})};if($v -is [string]){return $v.Replace($env:USERPROFILE,'[USER]')};return $v}
try{
 $script:Deps=Read-Json (Join-Path $PSScriptRoot 'dependencies.json')
 $manifest=Read-Json (Join-Path $PSScriptRoot 'manifest.json')
 if(!$manifest){throw 'APP_MANIFEST_MISSING'}
 foreach($f in $manifest.code){$p=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot $f.file));if(!$p.StartsWith($PSScriptRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path $p) -or (Get-FileHash $p).Hash -ine $f.sha256){throw ('APP_FILE_CHANGED: '+$f.file)}}
 Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase,System.Windows.Forms,System.Drawing
 Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class FNHWindow { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h,int cmd); [DllImport("shell32.dll", CharSet=CharSet.Unicode)] public static extern int SetCurrentProcessExplicitAppUserModelID(string appId); }
'@
 $script:AppUserModelIdResult=[FNHWindow]::SetCurrentProcessExplicitAppUserModelID('FreeNetHub.Desktop')
 try{$script:Lease=[IO.File]::Open((Join-Path $script:Root 'jobs\ui.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}catch{
  $old=Read-Json (Join-Path $script:Root 'jobs\ui-owner.json')
  if($old){$p=Get-Process -Id $old.pid -ErrorAction SilentlyContinue;if($p -and $p.Path -ieq $old.path -and $p.StartTime.ToUniversalTime().Ticks -eq $old.created -and $p.MainWindowHandle -ne 0){[void][FNHWindow]::ShowWindowAsync($p.MainWindowHandle,9);[void][FNHWindow]::SetForegroundWindow($p.MainWindowHandle);exit 0}}
  throw 'FreeNet Hub is already starting. No lock takeover was performed.'
 }
 $self=Get-Process -Id $PID;Write-Json (Join-Path $script:Root 'jobs\ui-owner.json') @{pid=$PID;created=$self.StartTime.ToUniversalTime().Ticks;path=$self.Path;appUserModelId='FreeNetHub.Desktop';appUserModelIdResult=$script:AppUserModelIdResult}
 $script:Window=[Windows.Markup.XamlReader]::Parse([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'View.xaml')))
 $icoPath=Join-Path $PSScriptRoot 'assets\FreeNetHub.ico'
 if(Test-Path -LiteralPath $icoPath){$script:Window.Icon=[Windows.Media.Imaging.BitmapFrame]::Create([Uri]::new($icoPath,[UriKind]::Absolute))}
 [xml]$x=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'View.xaml'))
 foreach($e in $x.SelectNodes('//*[@Name]')){$n=$e.GetAttribute('Name');$script:C[$n]=$script:Window.FindName($n)}
 $work=[Windows.SystemParameters]::WorkArea;$script:Window.MinWidth=[Math]::Min(850,$work.Width);$script:Window.MinHeight=[Math]::Min(600,$work.Height);$script:Window.Width=[Math]::Min(1180,$work.Width);$script:Window.Height=[Math]::Min(840,$work.Height)
 $script:Settings=@{theme='dark';country='AT';home='https://www.youtube.com/';monitor=$false;autoRepair=$false;showIp=$false;minimizeToTray=$true;order=@('WARP','TOR','GOOL','CFON');localProxy='socks5h://127.0.0.1:9909';includeDirect=$false}
 $stored=Read-Json (Join-Path $script:Root 'settings.json');if($stored){foreach($k in @($script:Settings.Keys)){if($stored.ContainsKey($k)){$script:Settings[$k]=$stored[$k]}}}
 $script:C.Home.Text=$script:Settings.home;$script:C.CustomProxy.Text=$script:Settings.localProxy;$script:C.ShowIp.IsChecked=$script:Settings.showIp;$script:C.TrayOption.IsChecked=$(if($script:ShellHosted){$true}else{$script:Settings.minimizeToTray});if($script:ShellHosted){$script:C.TrayOption.IsEnabled=$false;$script:C.TrayOption.ToolTip='Tray is managed by FreeNetHub.exe'};$script:C.Monitor.IsChecked=$script:Settings.monitor;$script:C.AutoRepair.IsChecked=$script:Settings.autoRepair
 foreach($i in $script:C.Country.Items){if($i.Content -eq $script:Settings.country){$script:C.Country.SelectedItem=$i}}
 function Theme-Apply([string]$name){$script:Settings.theme=$name;$colors=if($name -eq 'light'){@{Bg='#F3F6FA';Panel='#FFFFFF';Ink='#173047';Muted='#536B82';Line='#CFDAE5';Accent='#137E72';Soft='#E8F0F7'}}else{@{Bg='#0B1423';Panel='#132135';Ink='#ECF2FA';Muted='#A4B8CF';Line='#2D435C';Accent='#39CDB4';Soft='#1C3046'}};foreach($k in $colors.Keys){$script:Window.Resources[$k]=[Windows.Media.BrushConverter]::new().ConvertFromString($colors[$k])}}
 Theme-Apply $script:Settings.theme
 $script:Research=Read-Json (Join-Path $script:Root 'docs\research.json')
 function Research-Show{$q=$script:C.Search.Text;$rows=@($script:Research.products|Where-Object{!$q -or (($_|ConvertTo-Json -Compress) -match [regex]::Escape($q))});$script:C.ResearchText.Text=($rows|ForEach-Object{$_.name+"`r`n"+$_.features+"`r`n"+'نیاز / محدودیت: '+$_.requirements+"`r`n"+'تصمیم برای این محصول: '+$_.decision+"`r`n"+$_.source+"`r`n"}) -join "`r`n---------------------------`r`n"}
 Research-Show
 function Set-Busy{
  $busy=$null -ne $script:Task
  foreach($n in @('Connect','QuickConnect','QuickStop','Browser','Verify','Scan','Inventory','Doctor','Speed','Updates','Export','ImportWeb','ImportObfs','Save','Mode','Country')){$script:C[$n].IsEnabled=!$busy}
  $script:C.Cancel.IsEnabled=$busy;$script:C.Progress.IsIndeterminate=$busy
 }
 function Paint-Health{
  $h=$script:Health;if(!$h -or !$h.ContainsKey('mode') -or !$h.ContainsKey('checked')){return}
  $fresh=$false;try{$age=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($h.checked)).TotalSeconds;$fresh=$age -ge 0 -and $age -lt 65}catch{}
  $script:C.RouteValue.Text=[string]$h.mode;$script:C.CountryValue.Text=if($h.country -eq 'T1'){'Tor / کشور نامعلوم'}elseif($h.country){$h.country}else{'نامشخص'}
  $script:C.LatencyValue.Text=([math]::Round([double]$h.seconds*1000)).ToString()+' ms'
  $script:C.IpValue.Text=if($script:C.ShowIp.IsChecked -and $h.ip){$h.ip}else{'IP پنهان'}
  $script:C.StatusTitle.Text=if($h.healthy -and $fresh){'مسیر HTTPS تأیید شد'}elseif($h.healthy){'شاهد قبلی؛ وضعیت اکنون بررسی نشده'}else{'مسیر در آزمون اخیر تأیید نشد'}
  $script:C.StatusDetail.Text=if($h.mode -eq 'CFON'){'کشور خروجی مطابق سیاست بررسی می‌شود؛ ترافیک بازی UDP تأیید نشده.'}else{'این نتیجهٔ آزمون وب است؛ ورود به حساب، رسانه و همهٔ انواع نشت آزمون جدا دارند.'}
  $script:C.SidebarState.Text=if($h.healthy -and $fresh){'بررسی موفق'}else{'نیاز به بررسی'}
  $script:C.SidebarDetail.Text='آخرین شاهد: '+$h.checked
 }
 function Start-Work([string]$action,[string]$mode='AUTO',[string]$payload=''){
  if($script:Task){return}
  $script:Job=[guid]::NewGuid().ToString('N');$script:Action=$action;$script:Started=[DateTime]::UtcNow;$script:Cancelled=$false
  $p=[Diagnostics.ProcessStartInfo]::new();$p.FileName=$script:Deps.pythonw;$p.UseShellExecute=$false;$p.CreateNoWindow=$true;$p.WorkingDirectory=$script:Root
  foreach($a in @((Join-Path $PSScriptRoot 'engine.py'),'--action',$action,'--mode',$mode,'--job',$script:Job,'--budget',$(if($action -eq 'Scan'){'500'}else{'240'}))){[void]$p.ArgumentList.Add($a)}
  if($payload){[void]$p.ArgumentList.Add('--payload');[void]$p.ArgumentList.Add($payload)}
  try{$script:Task=[Diagnostics.Process]::Start($p);$script:C.StatusTitle.Text='در حال انجام درخواست';$script:C.SidebarState.Text='در حال بررسی';$script:C.StatusDetail.Text='پنجره پاسخ‌گو می‌ماند؛ لغو عملیات در دسترس است.';$script:C.Details.Text='Job: '+$script:Job+"`r`nAction: "+$action;Set-Busy}
  catch{$script:Task=$null;$script:C.StatusTitle.Text='شروع عملیات ناموفق';$script:C.StatusDetail.Text=$_.Exception.Message;Set-Busy}
 }
 function Selected{return [string]$script:C.Mode.SelectedItem.Tag}
 function Cancel-Work{if($script:Task){[IO.File]::WriteAllText((Join-Path $script:Root ('jobs\'+$script:Job+'.cancel')),'user cancel');$script:Cancelled=$true;$script:C.Cancel.IsEnabled=$false;$script:C.StatusDetail.Text='لغو درخواست شد؛ منتظر ثبت نتیجه و پاک‌سازی محدود هستیم.'}}
 function Open-Doc([string]$file){$p=Join-Path $script:Root ('docs\'+$file);$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='notepad.exe';$psi.UseShellExecute=$false;[void]$psi.ArgumentList.Add($p);[void][Diagnostics.Process]::Start($psi)}
 $script:C.QuickConnect.Add_Click({Start-Work 'Connect' 'AUTO'})
 $script:C.Connect.Add_Click({$m=Selected;if($m -eq 'DIRECT' -and [Windows.MessageBox]::Show('این حالت IP اصلی را به سایت‌ها نشان می‌دهد و تونل نیست. ادامه؟','FreeNet Hub','YesNo','Warning') -ne 'Yes'){return};$script:Repairs=0;Start-Work 'Connect' $m})
 $script:C.Verify.Add_Click({$m=Selected;if($m -eq 'AUTO'){$m=$script:CurrentMode};if(!$m){$script:C.StatusDetail.Text='ابتدا یک مسیر مشخص انتخاب کنید.';return};Start-Work 'Verify' $m})
 $script:C.Browser.Add_Click({if(!$script:CurrentMode){$script:C.StatusDetail.Text='ابتدا مسیر را متصل و تأیید کنید.';return};Start-Work 'Browser' $script:CurrentMode})
 $script:C.QuickStop.Add_Click({if([Windows.MessageBox]::Show('فقط پردازش‌های متعلق به FreeNet Hub 4 متوقف شوند؟ سایر VPNها و Firefox تغییر نمی‌کنند.','توقف محدود','YesNo','Question') -eq 'Yes'){Start-Work 'Stop'}})
 $script:C.Cancel.Add_Click({Cancel-Work})
 $script:C.Scan.Add_Click({Start-Work 'Scan'})
 $script:C.Inventory.Add_Click({Start-Work 'Inventory'})
 $script:C.Doctor.Add_Click({Start-Work 'Doctor'})
 $script:C.Speed.Add_Click({if(!$script:CurrentMode){$script:C.StatusDetail.Text='ابتدا یک مسیر متصل انتخاب کنید.';return};Start-Work 'Speed' $script:CurrentMode})
 $script:C.Updates.Add_Click({Start-Work 'Updates'})
 $script:C.Export.Add_Click({Start-Work 'Export'})
 $script:C.ShowIp.Add_Click({Paint-Health;if($script:Last){$script:C.Details.Text=(Sanitize $script:Last)|ConvertTo-Json -Depth 15}})
 $script:C.Search.Add_TextChanged({Research-Show})
 $script:C.Theme.Add_Click({Theme-Apply $(if($script:Settings.theme -eq 'dark'){'light'}else{'dark'})})
 $script:C.Help.Add_Click({Open-Doc 'HELP_FA.txt'})
 $script:C.BridgeHelp.Add_Click({Open-Doc 'BRIDGES_FA.txt'})
 $script:C.AdvancedHelp.Add_Click({Open-Doc 'ADVANCED_FA.txt'})
 $script:C.Copy.Add_Click({[Windows.Clipboard]::SetText($script:C.Details.Text)})
 $script:C.Logs.Add_Click({$p=[Diagnostics.ProcessStartInfo]::new();$p.FileName='explorer.exe';$p.UseShellExecute=$false;[void]$p.ArgumentList.Add((Join-Path $script:Root 'evidence'));[void][Diagnostics.Process]::Start($p)})
 foreach($n in @('ImportWeb','ImportObfs')){$script:C[$n].Tag=if($n -eq 'ImportWeb'){'WEBTUNNEL'}else{'OBFS4'};$script:C[$n].Add_Click({param($sender,$event)$d=[Microsoft.Win32.OpenFileDialog]::new();$d.Filter='Text files (*.txt)|*.txt';if($d.ShowDialog($script:Window)){Start-Work 'Import' ([string]$sender.Tag) $d.FileName}})}
 $script:C.Save.Add_Click({$script:Settings.country=[string]$script:C.Country.SelectedItem.Content;$script:Settings.home=$script:C.Home.Text;$script:Settings.localProxy=$script:C.CustomProxy.Text;$script:Settings.monitor=[bool]$script:C.Monitor.IsChecked;$script:Settings.autoRepair=[bool]$script:C.AutoRepair.IsChecked;$script:Settings.showIp=[bool]$script:C.ShowIp.IsChecked;$script:Settings.minimizeToTray=[bool]$script:C.TrayOption.IsChecked;$p=Join-Path $script:Root 'jobs\settings-request.json';Write-Json $p $script:Settings;Start-Work 'Settings' 'AUTO' $p})
 if(!$script:ShellHosted){
  $script:Tray=[Windows.Forms.NotifyIcon]::new();if(Test-Path -LiteralPath $icoPath){$script:AppIcon=[Drawing.Icon]::new($icoPath);$script:Tray.Icon=$script:AppIcon}else{$script:Tray.Icon=[Drawing.SystemIcons]::Application};$script:Tray.Text='FreeNet Hub — browser routes';$script:Tray.Visible=$false
  $menu=[Windows.Forms.ContextMenuStrip]::new();$show=$menu.Items.Add('Open FreeNet Hub');$show.add_Click({$script:Window.Show();$script:Window.WindowState='Normal';[void]$script:Window.Activate();$script:Tray.Visible=$false})
  $exit=$menu.Items.Add('Close panel (leave tunnel unchanged)');$exit.add_Click({$script:AllowClose=$true;$script:Window.Close()});$script:Tray.ContextMenuStrip=$menu
  $script:Tray.Add_DoubleClick({$script:Window.Show();$script:Window.WindowState='Normal';[void]$script:Window.Activate();$script:Tray.Visible=$false})
  $script:Window.Add_StateChanged({if($script:Window.WindowState -eq 'Minimized' -and $script:C.TrayOption.IsChecked){$script:Tray.Visible=$true;$script:Window.Hide()}})
 }
 $script:Window.Add_Closing({param($s,$e)if($script:Task){$e.Cancel=$true;Cancel-Work;return};if(!$Smoke -and !$script:AllowClose -and $script:CurrentMode){$a=[Windows.MessageBox]::Show('بستن پنل، تونل را قطع نمی‌کند و پایش متوقف می‌شود. پنل بسته شود؟ برای حفظ پایش، Cancel و سپس Minimize را بزنید.','FreeNet Hub','OKCancel','Information');if($a -ne 'OK'){$e.Cancel=$true}}})
 $script:Timer=[Windows.Threading.DispatcherTimer]::new();$script:Timer.Interval=[TimeSpan]::FromMilliseconds(400);$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45)
 $script:Timer.Add_Tick({
  try{
   $script:Tick++
   if($script:Task){
    $script:C.Elapsed.Text=('زمان سپری‌شده: {0:0} ثانیه' -f ([DateTime]::UtcNow-$script:Started).TotalSeconds)
    $p=Join-Path $script:Root ('jobs\'+$script:Job+'.progress.json');$s=Read-Json $p
    if($s -and $s.job -eq $script:Job -and !$script:Cancelled){$script:C.StatusDetail.Text=$s.message}
    if($script:Task.HasExited){
     $ec=$script:Task.ExitCode;$script:Task.Dispose();$script:Task=$null;$r=Read-Json (Join-Path $script:Root ('jobs\'+$script:Job+'.json'))
     if(!$r -or $r.job -ne $script:Job -or $r.action -ne $script:Action -or $r.exit -ne $ec){$r=@{exit=1;result=@{error='RESULT_PROTOCOL_MISMATCH'};action=$script:Action}}
     $script:Last=$r;$script:C.Details.Text=(Sanitize $r)|ConvertTo-Json -Depth 16
     if($r.exit -ne 0){if($r.result.ContainsKey('healthy') -and $r.result.ContainsKey('mode')){$script:Health=$r.result}elseif($script:Action -in @('Verify','Connect') -and $script:Health){$script:Health.healthy=$false};$script:C.StatusTitle.Text=if($r.exit -eq 20){'عملیات لغو شد'}elseif($r.exit -eq 124){'مهلت تلاش تمام شد'}else{'درخواست تأیید نشد'};$script:C.StatusDetail.Text=if($r.result.ContainsKey('error')){[string]$r.result.error}else{'برای جزئیات، زبانهٔ ابزارها را ببینید.'};$script:C.SidebarState.Text='تأیید نشده';if($script:Action -eq 'Verify'){$script:Failures++}}
     elseif($r.result.ContainsKey('healthy')){$script:Health=$r.result;if($r.result.healthy){$script:CurrentMode=$r.result.mode;$script:Failures=0};Paint-Health}
     else{$script:C.StatusTitle.Text='درخواست انجام شد';$script:C.StatusDetail.Text='نتیجهٔ دقیق در زبانهٔ ابزارها ثبت شد؛ این پیام لزوماً اتصال موفق نیست.';if($r.action -eq 'Stop'){$script:CurrentMode='';$script:Health=$null;$script:C.SidebarState.Text='قطع شده'};if($r.action -eq 'Scan'){$script:C.ScanSummary.Text='ترتیب نمونهٔ اخیر: '+($r.result.rank -join ' → ')};if($r.action -eq 'Inventory'){$script:C.BridgeStatus.Text=($r.result.providers|Where-Object{$_.mode -in @('WEBTUNNEL','OBFS4')}|ForEach-Object{$_.mode+': '+$_.state}) -join "`r`n"}}
     Set-Busy;$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45);$script:C.Elapsed.Text='عملیات پایان یافت؛ اتصال کل سیستم تغییر نکرد.'
    }
   }else{
    if($script:Tick % 25 -eq 0){Paint-Health}
    if(!$Smoke -and $script:C.Monitor.IsChecked -and $script:CurrentMode -and [DateTime]::UtcNow -ge $script:NextCheck){
     $script:NextCheck=[DateTime]::UtcNow.AddSeconds(90)
     if($script:C.AutoRepair.IsChecked -and $script:Failures -ge 3 -and $script:Repairs -lt 2){$script:Repairs++;$script:Failures=0;Start-Work 'Connect' $script:CurrentMode}else{Start-Work 'Verify' $script:CurrentMode}
    }
   }
   if($Smoke -and $script:Tick -ge 6 -and !$script:Task){
    $script:Window.UpdateLayout();$b=[Windows.Media.Imaging.RenderTargetBitmap]::new([int]$script:Window.ActualWidth,[int]$script:Window.ActualHeight,96,96,[Windows.Media.PixelFormats]::Pbgra32);$b.Render($script:Window)
    $encoder=[Windows.Media.Imaging.PngBitmapEncoder]::new();$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($b));$f=[IO.File]::Create((Join-Path $script:Root 'evidence\UI.png'));try{$encoder.Save($f)}finally{$f.Dispose()}
    Write-Json (Join-Path $script:Root 'evidence\gui.json') @{utc=[DateTime]::UtcNow.ToString('o');visible=$script:Window.IsVisible;controls=$script:C.Count;width=$script:Window.ActualWidth;height=$script:Window.ActualHeight;ticks=$script:Tick;topmost=$script:Window.Topmost;networkRequested=$false;theme=$script:Settings.theme;workerAction=$(if($script:Last){$script:Last.action}else{''});workerExit=$(if($script:Last){$script:Last.exit}else{-1})};$script:AllowClose=$true;$script:Window.Close()
   }
  }catch{$script:C.StatusTitle.Text='خطای نمایش نتیجه';$script:C.Details.Text=$_.Exception.ToString()}
 })
 $script:Window.Add_ContentRendered({[void]$script:Window.Activate();[void]$script:C.Connect.Focus();if($Smoke){Start-Work 'Inventory'}})
 Set-Busy;$script:Timer.Start();[void]$script:Window.ShowDialog()
}catch{
 $msg=$_.Exception.ToString();[IO.File]::WriteAllText((Join-Path $script:Root 'logs\ui-error.txt'),$msg,[Text.UTF8Encoding]::new($false));try{Add-Type -AssemblyName PresentationFramework;[Windows.MessageBox]::Show($msg,'FreeNet Hub — startup error')|Out-Null}catch{};exit 1
}finally{if($script:Timer){$script:Timer.Stop()};if($script:Tray){$script:Tray.Visible=$false;$script:Tray.Dispose()};if($script:AppIcon){$script:AppIcon.Dispose()};if($script:Lease){$script:Lease.Dispose()}}
