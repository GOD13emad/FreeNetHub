param([switch]$Smoke)

# FreeNet Hub 4.2. One UI; browser routes plus explicit elevated PC/console gateway. No network change on launch.

Set-StrictMode -Version Latest

$ErrorActionPreference='Stop'

$script:Root=Split-Path $PSScriptRoot -Parent
New-Item -ItemType Directory -Path (Join-Path $script:Root 'logs'),(Join-Path $script:Root 'jobs'),(Join-Path $script:Root 'evidence') -Force|Out-Null

$script:Task=$null;$script:GatewayTask=$null;$script:GatewayJob='';$script:GatewayAction='';$script:Lease=$null;$script:Timer=$null;$script:Tray=$null;$script:AppIcon=$null;$script:CurrentMode='';$script:DesiredMode='';$script:FullSystemActive=$false;$script:Health=$null;$script:Last=$null;$script:C=@{};$script:Tick=0;$script:Failures=0;$script:Repairs=0;$script:AllowClose=$false;$script:ShellHosted=($env:FREENETHUB_SHELL_HOST -eq '1');$script:SmokeVerifyMode=$(if($Smoke){[string]$env:FREENETHUB_SMOKE_VERIFY_MODE}else{''})

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

 $script:C.Home.Text=$script:Settings.home;$script:C.CustomProxy.Text=$script:Settings.localProxy;$script:C.ShowIp.IsChecked=$script:Settings.showIp;$script:C.FullSystem.IsChecked=$false;$script:C.ScopeText.Text='خاموش · فقط مرورگر (پیش‌فرض)';$script:C.TrayOption.IsChecked=$(if($script:ShellHosted){$true}else{$script:Settings.minimizeToTray});if($script:ShellHosted){$script:C.TrayOption.IsEnabled=$false;$script:C.TrayOption.ToolTip='Tray is managed by FreeNetHub.exe'};$script:C.Monitor.IsChecked=$script:Settings.monitor;$script:C.AutoRepair.IsChecked=$script:Settings.autoRepair

 foreach($i in $script:C.Country.Items){if($i.Content -eq $script:Settings.country){$script:C.Country.SelectedItem=$i}}

 function Theme-Apply([string]$name){$script:Settings.theme=$name;$colors=if($name -eq 'light'){@{Bg='#F3F6FA';Panel='#FFFFFF';Ink='#173047';Muted='#536B82';Line='#CFDAE5';Accent='#137E72';Soft='#E8F0F7'}}else{@{Bg='#0B1423';Panel='#132135';Ink='#ECF2FA';Muted='#A4B8CF';Line='#2D435C';Accent='#39CDB4';Soft='#1C3046'}};foreach($k in $colors.Keys){$script:Window.Resources[$k]=[Windows.Media.BrushConverter]::new().ConvertFromString($colors[$k])}}

 Theme-Apply $script:Settings.theme

 $script:Research=Read-Json (Join-Path $script:Root 'docs\research.json')

 function Research-Show{$q=$script:C.Search.Text;$rows=@($script:Research.products|Where-Object{!$q -or (($_|ConvertTo-Json -Compress) -match [regex]::Escape($q))});$script:C.ResearchText.Text=($rows|ForEach-Object{$_.name+"`r`n"+$_.features+"`r`n"+'نیاز / محدودیت: '+$_.requirements+"`r`n"+'تصمیم برای این محصول: '+$_.decision+"`r`n"+$_.source+"`r`n"}) -join "`r`n---------------------------`r`n"}

 Research-Show

 function Set-Busy{

  $busy=($null -ne $script:Task -or $null -ne $script:GatewayTask)

  foreach($n in @('Connect','QuickConnect','QuickStop','EmergencyChatGPT','Browser','Verify','Scan','Inventory','Doctor','Speed','Updates','Export','ImportWeb','ImportObfs','Save','Mode','Country','FullSystem','GatewayConsoleStart','GatewayStop','GatewayRefresh','GatewayImportProfile')){if($script:C.ContainsKey($n)){$script:C[$n].IsEnabled=!$busy}}

  $script:C.Cancel.IsEnabled=($null -ne $script:Task);$script:C.Progress.IsIndeterminate=$busy

 }

 function Friendly-Error([string]$code,$h=$null){

  switch($code){

   'NOT_CONNECTED'{return 'مسیر انتخاب‌شده متصل نیست. ابتدا «شروع اتصال» را بزنید، سپس دوباره بررسی کنید.'}

   'PATH_NOT_READY'{return 'پردازش مسیر شروع شده اما پروکسی محلی هنوز آماده نیست. چند ثانیه صبر کنید یا اتصال را دوباره برقرار کنید.'}

   'LOCAL_PROXY_UNREACHABLE'{return 'پروکسی محلی این مسیر در دسترس نیست؛ وضعیت اتصال با اجرای واقعی مسیر هم‌خوان نیست.'}

   'PORT_OWNED_BY_ANOTHER_PROCESS'{return 'پورت محلی این مسیر توسط پردازشی خارج از مالکیت تأییدشدهٔ FreeNet Hub اشغال شده است.'}

   'COUNTRY_MISMATCH_OR_UNKNOWN'{return 'HTTPS برقرار است، اما کشور خروجی با سیاست انتخاب‌شده تطابق ندارد یا قابل تأیید نیست.'}

   'HTTPS_VERIFICATION_FAILED'{return 'مسیر متصل است، اما آزمون HTTPS کامل تأیید نشد. جزئیات آزمون را بررسی کنید.'}

   'ALL_PATHS_FAILED'{

    if($h -and $h.ContainsKey('attempts')){$x=@($h.attempts|ForEach-Object{$_.mode+': '+$_.reason});if($x.Count){return 'هیچ مسیر قابل‌قبولی برقرار نشد. '+($x -join ' | ')}}

    return 'هیچ مسیر قابل‌قبولی برقرار نشد.'

   }

   'ALL_CHATGPT_PATHS_FAILED'{if($h -and $h.ContainsKey('attempts')){$x=@($h.attempts|ForEach-Object{$_.mode+': '+$_.reason});if($x.Count){return 'هیچ مسیر فعلی به لبهٔ ChatGPT نرسید. '+($x -join ' | ')}};return 'هیچ مسیر فعلی به لبهٔ ChatGPT نرسید.'}
   'CHATGPT_UNREACHABLE'{return 'تونل عمومی سالم است، اما لبه‌های ChatGPT/OpenAI از این مسیر در دسترس تأیید نشدند.'}

   'CONNECT_FIRST'{return 'این عملیات به یک مسیر فعال نیاز دارد. ابتدا اتصال را برقرار کنید.'}

   'BROWSER_BLOCKED_PATH_UNHEALTHY'{return 'مرورگر باز نشد چون مسیر فعلی آزمون HTTPS را پاس نکرد.'}

   'CONSOLE_LINK_DOWN'{return 'کابل کنسول وصل نیست. Gateway می‌تواند آماده بماند و پس از اتصال کابل فعال شود.'}

   'CONSOLE_USB_DEVICE_NOT_FOUND'{return 'آداپتور USB کنسول پیدا نشد. اتصال USB یا تنظیمات Gateway کنسول را بررسی کنید.'}

   'CONSOLE_USB_ALREADY_ATTACHED_EXTERNALLY'{return 'آداپتور USB کنسول توسط یک نشست دیگر WSL/USBIP در حال استفاده است.'}

   'WSL_DISTRO_MISSING'{return 'توزیع WSL پیکربندی‌شده پیدا نشد. Setup Console Gateway را اجرا کنید.'}

   'WSL_GATEWAY_NOT_CONFIGURED'{return 'Gateway کنسول برای WSL هنوز پیکربندی نشده است. Setup Console Gateway را اجرا کنید.'}
   'WSL_DISTRO_MISSING_INSTALL_WSL_FIRST'{return 'WSL نصب است اما هیچ توزیع Linux آماده‌ای وجود ندارد. ابتدا یک Ubuntu WSL نصب کنید؛ reboot خودکار انجام نمی‌شود.'}
   'USBIPD_MISSING_RUN_SETUP_WITH_INSTALLPREREQUISITES'{return 'usbipd-win نصب نیست. «راه‌اندازی پیش‌نیازهای کنسول» را اجرا کنید.'}
   'WSL_TOOLS_INSTALL_FAIL'{return 'نصب ابزارهای لازم داخل WSL کامل نشد. جزئیات فنی setup را بررسی کنید.'}

   'WSL_CONSOLE_START_FAIL'{return 'Router کنسول در WSL کامل راه‌اندازی نشد؛ rollback خودکار اجرا شد.'}

   'CONSOLE_PROVIDER_START_FAIL'{return 'مسیر خروجی کنسول نتوانست TCP و UDP کشور هدف را تأیید کند.'}

   'LOCAL_CONSOLE_PROVIDER_NOT_CONFIGURED'{return 'برای این سیستم provider محلی تنظیم نشده است؛ یک WireGuard profile معتبر برای کنسول وارد کنید.'}

   'CONSOLE_ADAPTER_NOT_FOUND'{return 'آداپتور آداپتور اختصاصی کنسول مخصوص کنسول پیدا نشد.'}

   'GATEWAY_ALREADY_RUNNING'{return 'یک Gateway از قبل فعال است. ابتدا همان را قطع کنید.'}

   'UAC_CANCELLED_OR_ELEVATION_FAILED'{return 'تأیید مدیریتی ویندوز انجام نشد؛ هیچ Gateway جدیدی فعال نشد.'}

   'PC_WARP_NOT_ON'{return 'تونل کل سیستم ساخته شد اما WARP در آزمون نهایی تأیید نشد؛ rollback اجرا شد.'}

   'CONSOLE_PROVIDER_FAIL'{return 'مسیر ثابت کنسول نتوانست TCP و UDP کشور DE را هم‌زمان تأیید کند.'}

   default{return $(if($code){'خطا: '+$code}else{'عملیات کامل نشد. جزئیات فنی را بررسی کنید.'})}

  }

 }

 function Paint-Health{

  $h=$script:Health;if(!$h -or !$h.ContainsKey('mode') -or !$h.ContainsKey('checked')){return}

  $state=$(if($h.ContainsKey('state')){[string]$h.state}else{''});$connected=$(if($h.ContainsKey('connected')){[bool]$h.connected}else{$true})

  $fresh=$false;try{$age=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($h.checked)).TotalSeconds;$fresh=$age -ge 0 -and $age -lt 65}catch{}

  $script:C.RouteValue.Text=[string]$h.mode

  if(!$connected -or $state -in @('NOT_CONNECTED','STARTING_OR_UNREADY','FOREIGN_OR_STALE_LISTENER','CONNECT_FAILED')){

   $script:C.CountryValue.Text='—';$script:C.LatencyValue.Text='—';$script:C.IpValue.Text='—'

   $script:C.StatusTitle.Text=$(switch($state){'STARTING_OR_UNREADY'{'مسیر هنوز آماده نیست'}'CONNECT_FAILED'{'اتصال برقرار نشد'}'FOREIGN_OR_STALE_LISTENER'{'تعارض روی پروکسی محلی'}default{'مسیر متصل نیست'}})

   $script:C.StatusDetail.Text=Friendly-Error ([string]$h.error) $h

   $script:C.SidebarState.Text='متصل نیست';$script:C.SidebarDetail.Text='آخرین بررسی: '+$h.checked

   return

  }

  $script:C.CountryValue.Text=if($h.country -eq 'T1'){'Tor / کشور نامعلوم'}elseif($h.country){$h.country}else{'نامشخص'}

  $script:C.LatencyValue.Text=if($h.healthy -and $null -ne $h.seconds){([math]::Round([double]$h.seconds*1000)).ToString()+' ms'}else{'—'}

  $script:C.IpValue.Text=if($script:C.ShowIp.IsChecked -and $h.ip){$h.ip}else{'IP پنهان'}

  $script:C.StatusTitle.Text=if($h.healthy -and $fresh){'مسیر HTTPS تأیید شد'}elseif($h.healthy){'شاهد قبلی؛ وضعیت اکنون بررسی نشده'}else{'مسیر متصل است؛ HTTPS تأیید نشد'}

  $script:C.StatusDetail.Text=if(!$h.healthy){Friendly-Error ([string]$h.error) $h}elseif($h.mode -eq 'CFON'){'کشور خروجی مطابق سیاست بررسی می‌شود؛ ترافیک بازی UDP تأیید نشده.'}else{'این نتیجهٔ آزمون وب است؛ ورود به حساب، رسانه و همهٔ انواع نشت آزمون جدا دارند.'}

  $script:C.SidebarState.Text=if($h.healthy -and $fresh){'بررسی موفق'}elseif($h.healthy){'متصل / شاهد قدیمی'}else{'متصل / نیاز به بررسی'}

  $script:C.SidebarDetail.Text='آخرین شاهد: '+$h.checked

 }

 function Start-Work([string]$action,[string]$mode='AUTO',[string]$payload=''){

  if($script:Task -or $script:GatewayTask){return}

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



 function Gateway-Refresh{

  try{

   $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true

   foreach($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $script:Root 'gateway\gateway_control.ps1'),'-Action','Status')){[void]$psi.ArgumentList.Add($a)}

   $p=[Diagnostics.Process]::Start($psi);if(!$p.WaitForExit(8000)){try{$p.Kill($true)}catch{};throw 'GATEWAY_STATUS_TIMEOUT'};$raw=$p.StandardOutput.ReadToEnd();if($p.ExitCode -ne 0){throw 'GATEWAY_STATUS_FAILED'}

   $j=$raw|ConvertFrom-Json -AsHashtable;$g=$j.result

   $script:FullSystemActive=[bool]($g.running -and [string]$g.mode -eq 'PC_TUNNEL');$script:C.FullSystem.IsChecked=$script:FullSystemActive;$script:C.ScopeText.Text=$(if($script:FullSystemActive){'روشن · WARP کل سیستم فعال'}else{'خاموش · فقط مرورگر (پیش‌فرض)'});if($g.running -and [string]$g.mode -eq 'CONSOLE_ONLY'){$script:C.GatewayState.Text='اتصال کنسول فعال است';$script:C.GatewayDetail.Text='Mode: CONSOLE_ONLY · مسیر میزبان جداگانه راستی‌آزمایی شده است.'}elseif($script:FullSystemActive){$script:C.GatewayState.Text='اتصال کنسول خاموش است';$script:C.GatewayDetail.Text='تونل کل سیستم از صفحهٔ اتصال فعال است؛ این صفحه فقط کنسول را مدیریت می‌کند.'}else{$script:C.GatewayState.Text='اتصال کنسول خاموش است';$script:C.GatewayDetail.Text='هیچ اتصال کنسول متعلق به FreeNetHub فعال نیست.'}

   $cs=[string]$g.console.status;$an=$(if([string]$g.console.description){[string]$g.console.description}else{'آداپتور اختصاصی کنسول'});$script:C.ConsoleLinkState.Text=$an+': '+$(if($cs -eq 'Up'){'لینک برقرار'}elseif($cs -eq 'Disconnected'){'کابل متصل نیست'}elseif($cs -eq 'Missing'){'پیکربندی/سخت‌افزار پیدا نشد'}else{$cs})

   $m=$g.console.manual;$script:C.ConsoleInstructions.Text='IP: '+$m.ip+'   |   Mask: 255.255.255.0   |   Gateway: '+$m.gateway+'   |   DNS: '+$m.dns

   return $g

  }catch{$script:C.GatewayState.Text='وضعیت اتصال کنسول قابل خواندن نیست';$script:C.GatewayDetail.Text=$_.Exception.Message;return $null}

 }

 function Start-GatewayRequest([string]$action){

  if($script:Task -or $script:GatewayTask){return}

  if($action -eq 'StartPc' -and [Windows.MessageBox]::Show('تمام ترافیک این کامپیوتر وارد TUN می‌شود. در صورت شکست آزمون، rollback خودکار اجرا می‌شود. ادامه؟','FreeNet Hub · Full PC','YesNo','Warning') -ne 'Yes'){return}
  if($action -eq 'SetupConsole' -and [Windows.MessageBox]::Show('پیش‌نیازهای Gateway کنسول بررسی و در صورت نیاز نصب می‌شوند: usbipd و sing-box pinned و ابزارهای WSL. این عملیات هیچ تونلی را روشن نمی‌کند. ادامه؟','FreeNet Hub · Console Setup','YesNo','Question') -ne 'Yes'){return}

  if($action -eq 'StartConsole'){

   $g=Gateway-Refresh;if($g -and [string]$g.console.status -ne 'Up'){$script:C.GatewayDetail.Text='Gateway کنسول آماده می‌شود؛ کابل را می‌توانید بعداً وصل کنید. تا برقراری لینک، مسیر در حالت انتظار می‌ماند.'}

  }

  if($action -eq 'Stop' -and [Windows.MessageBox]::Show('Gateway متعلق به FreeNetHub قطع و تنظیمات موقت آن rollback شود؟','FreeNet Hub · Stop Gateway','YesNo','Question') -ne 'Yes'){return}

  $script:GatewayJob=[guid]::NewGuid().ToString('N');$script:GatewayAction=$action;$script:GatewayStarted=[DateTime]::UtcNow

  $result=Join-Path $script:Root ('jobs\gateway-'+$script:GatewayJob+'.json');Remove-Item $result -Force -ErrorAction SilentlyContinue

  $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WorkingDirectory=$script:Root

  foreach($a in @('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',(Join-Path $script:Root 'gateway\gateway_request.ps1'),'-Action',$action,'-Job',$script:GatewayJob)){[void]$psi.ArgumentList.Add($a)}

  try{$script:GatewayTask=[Diagnostics.Process]::Start($psi);$script:C.GatewayState.Text='در انتظار تأیید UAC / اجرای Gateway';$script:C.GatewayDetail.Text='Job: '+$script:GatewayJob+' · '+$action;$script:C.SidebarState.Text='عملیات شبکه در حال اجرا';Set-Busy}catch{$script:GatewayTask=$null;$script:C.GatewayState.Text='شروع Gateway ناموفق';$script:C.GatewayDetail.Text=$_.Exception.Message;Set-Busy}

 }



 $script:C.GatewayConsoleStart.Add_Click({Start-GatewayRequest 'StartConsole'})

 $script:C.GatewayStop.Add_Click({Start-GatewayRequest 'StopConsole'})

 $script:C.GatewayRefresh.Add_Click({[void](Gateway-Refresh)})

 $script:C.GatewayImportProfile.Add_Click({

  if($script:Task -or $script:GatewayTask){return}

  $d=[Microsoft.Win32.OpenFileDialog]::new();$d.Filter='WireGuard config (*.conf)|*.conf|All files (*.*)|*.*'

  if(!$d.ShowDialog($script:Window)){return}

  $country=[string]$script:C.Country.SelectedItem.Content;$out=Join-Path $script:Root 'gateway\runtime\console.profile.json'

  $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$script:Deps.pythonw;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true

  foreach($a in @((Join-Path $script:Root 'gateway\import_wireguard.py'),$d.FileName,'--name',('Console-'+$country),'--country',$country,'--output',$out)){[void]$psi.ArgumentList.Add($a)}

  try{$p=[Diagnostics.Process]::Start($psi);if(!$p.WaitForExit(15000)){try{$p.Kill($true)}catch{};throw 'PROFILE_IMPORT_TIMEOUT'};if($p.ExitCode -ne 0){throw 'PROFILE_IMPORT_FAILED'};$script:C.GatewayState.Text='پروفایل کنسول وارد شد';$script:C.GatewayDetail.Text='کلید فقط در runtime محلی ذخیره شد. هنگام Start Console، TCP/UDP و کشور '+$country+' دوباره آزمون می‌شوند.'}catch{$script:C.GatewayState.Text='وارد کردن پروفایل ناموفق';$script:C.GatewayDetail.Text=$_.Exception.Message}

 })

 function Scope-IsFullSystem{return [bool]$script:C.FullSystem.IsChecked}

$script:C.FullSystem.Add_Click({
 $on=Scope-IsFullSystem
 if($on){
  $script:C.ScopeText.Text='روشن · اتصال بعدی WARP کل سیستم'
  $m=Selected
  if($m -notin @('AUTO','WARP')){$script:C.StatusTitle.Text='تونل کل سیستم فقط با WARP';$script:C.StatusDetail.Text='WARP یا AUTO را انتخاب کن؛ سایر providerها فقط مرورگر هستند.'}
 }else{
  if($script:FullSystemActive){
   if([Windows.MessageBox]::Show('تونل کل سیستم اکنون فعال است. خاموش و rollback شود؟','FreeNet Hub · Full System','YesNo','Question') -eq 'Yes'){Start-GatewayRequest 'Stop'}else{$script:C.FullSystem.IsChecked=$true;$script:C.ScopeText.Text='روشن · WARP کل سیستم فعال';return}
  }else{$script:C.ScopeText.Text='خاموش · فقط مرورگر (پیش‌فرض)'}
 }
})

$script:C.QuickConnect.Add_Click({
 if(Scope-IsFullSystem){$script:DesiredMode='WARP';Start-GatewayRequest 'StartPc'}
 else{$script:DesiredMode='AUTO';Start-Work 'Connect' 'AUTO'}
})

 $script:C.Connect.Add_Click({$m=Selected;if(Scope-IsFullSystem){if($m -notin @('AUTO','WARP')){$script:C.StatusTitle.Text='تونل کل سیستم فقط با WARP';$script:C.StatusDetail.Text='سوییچ را خاموش کن یا WARP/AUTO را انتخاب کن.';return};$script:DesiredMode='WARP';$script:Repairs=0;Start-GatewayRequest 'StartPc';return};if($m -eq 'DIRECT' -and [Windows.MessageBox]::Show('این حالت IP اصلی را به سایت‌ها نشان می‌دهد و تونل نیست. ادامه؟','FreeNet Hub','YesNo','Warning') -ne 'Yes'){return};$script:DesiredMode=$m;$script:Repairs=0;Start-Work 'Connect' $m})

 $script:C.Verify.Add_Click({$m=Selected;if($m -eq 'AUTO'){$m=if($script:CurrentMode){$script:CurrentMode}else{$script:DesiredMode}};if(!$m -or $m -eq 'AUTO'){$script:C.StatusTitle.Text='مسیر فعالی برای بررسی نیست';$script:C.StatusDetail.Text='ابتدا «شروع اتصال» را بزنید یا یک مسیر مشخص انتخاب کنید.';return};Start-Work 'Verify' $m})

 $script:C.EmergencyChatGPT.Add_Click({$script:DesiredMode='CHATGPT';$script:Repairs=0;Start-Work 'ChatGPT' 'AUTO'})

 $script:C.Browser.Add_Click({if($script:FullSystemActive){Start-Work 'Browser' 'DIRECT';return};if(!$script:CurrentMode){$script:C.StatusTitle.Text='مرورگر باز نشد';$script:C.StatusDetail.Text=Friendly-Error 'CONNECT_FIRST';return};Start-Work 'Browser' $script:CurrentMode})

 $script:C.QuickStop.Add_Click({if($script:FullSystemActive){if([Windows.MessageBox]::Show('تونل کل سیستم متعلق به FreeNetHub خاموش و rollback شود؟','توقف محدود','YesNo','Question') -eq 'Yes'){Start-GatewayRequest 'Stop'};return};if([Windows.MessageBox]::Show('فقط مسیرهای مرورگر متعلق به FreeNet Hub متوقف شوند؟ سایر VPNها و Chrome شخصی تغییر نمی‌کنند.','توقف محدود','YesNo','Question') -eq 'Yes'){Start-Work 'Stop'}})

 $script:C.Cancel.Add_Click({Cancel-Work})

 $script:C.Scan.Add_Click({Start-Work 'Scan'})

 $script:C.Inventory.Add_Click({Start-Work 'Inventory'})

 $script:C.Doctor.Add_Click({Start-Work 'Doctor'})

 $script:C.Speed.Add_Click({if(!$script:CurrentMode){$script:C.StatusTitle.Text='آزمون سرعت اجرا نشد';$script:C.StatusDetail.Text=Friendly-Error 'CONNECT_FIRST';return};Start-Work 'Speed' $script:CurrentMode})

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

 $script:Window.Add_Closing({param($s,$e)if($script:GatewayTask){$e.Cancel=$true;$script:C.GatewayDetail.Text='عملیات Gateway هنوز در حال اجراست؛ پس از پایان دوباره ببندید.';return};if($script:Task){$e.Cancel=$true;Cancel-Work;return};if(!$Smoke -and !$script:AllowClose -and ($script:CurrentMode -or $script:FullSystemActive)){$a=[Windows.MessageBox]::Show('بستن پنل، تونل را قطع نمی‌کند و پایش متوقف می‌شود. پنل بسته شود؟ برای حفظ پایش، Cancel و سپس Minimize را بزنید.','FreeNet Hub','OKCancel','Information');if($a -ne 'OK'){$e.Cancel=$true}}})

 $script:Timer=[Windows.Threading.DispatcherTimer]::new();$script:Timer.Interval=[TimeSpan]::FromMilliseconds(400);$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45)

 $script:Timer.Add_Tick({

  try{

   $script:Tick++

   if($script:GatewayTask -and $script:GatewayTask.HasExited){

    $ec=$script:GatewayTask.ExitCode;$script:GatewayTask.Dispose();$script:GatewayTask=$null;$r=Read-Json (Join-Path $script:Root ('jobs\gateway-'+$script:GatewayJob+'.json'))

    if(!$r){$r=@{exit=20;result=@{error='GATEWAY_RESULT_MISSING'};action=$script:GatewayAction}}

    $script:Last=$r;$script:C.Details.Text=(Sanitize $r)|ConvertTo-Json -Depth 16

    if($r.exit -eq 0){$script:C.GatewayState.Text='عملیات Gateway موفق بود';$script:C.GatewayDetail.Text=$script:GatewayAction+' با کنترل rollback کامل شد.';$script:C.SidebarState.Text='Gateway آماده'}else{$code=if($r.result.ContainsKey('error')){[string]$r.result.error}else{'GATEWAY_FAILED'};$script:C.GatewayState.Text='عملیات Gateway کامل نشد';$script:C.GatewayDetail.Text=Friendly-Error $code $r.result;$script:C.SidebarState.Text='Gateway نیاز به بررسی'}

    [void](Gateway-Refresh);Set-Busy

   }

   if($script:Task){

    $script:C.Elapsed.Text=('زمان سپری‌شده: {0:0} ثانیه' -f ([DateTime]::UtcNow-$script:Started).TotalSeconds)

    $p=Join-Path $script:Root ('jobs\'+$script:Job+'.progress.json');$s=Read-Json $p

    if($s -and $s.job -eq $script:Job -and !$script:Cancelled){$script:C.StatusDetail.Text=$s.message}

    if($script:Task.HasExited){

     $ec=$script:Task.ExitCode;$script:Task.Dispose();$script:Task=$null;$r=Read-Json (Join-Path $script:Root ('jobs\'+$script:Job+'.json'))

     if(!$r -or $r.job -ne $script:Job -or $r.action -ne $script:Action -or $r.exit -ne $ec){$r=@{exit=1;result=@{error='RESULT_PROTOCOL_MISMATCH'};action=$script:Action}}

     $script:Last=$r;$script:C.Details.Text=(Sanitize $r)|ConvertTo-Json -Depth 16

     if($r.result.ContainsKey('healthy') -and $r.result.ContainsKey('mode')){

      $script:Health=$r.result

      if($r.result.healthy){$script:CurrentMode=[string]$r.result.mode;$script:DesiredMode=$script:CurrentMode;$script:Failures=0}

      else{

       $conn=$(if($r.result.ContainsKey('connected')){[bool]$r.result.connected}else{$true})

       if(!$conn -and $script:CurrentMode -eq [string]$r.result.mode){$script:CurrentMode=''}

       if($script:Action -eq 'Verify'){$script:Failures++}

      }

      Paint-Health

     }

     elseif($r.exit -ne 0){$script:C.StatusTitle.Text=if($r.exit -eq 20){'عملیات لغو شد'}elseif($r.exit -eq 124){'مهلت زمانی تمام شد'}else{'عملیات انجام نشد'};$script:C.StatusDetail.Text=Friendly-Error $(if($r.result.ContainsKey('error')){[string]$r.result.error}else{''}) $r.result;$script:C.SidebarState.Text='نیاز به بررسی'}

     else{

      $script:C.StatusTitle.Text='عملیات انجام شد';$script:C.StatusDetail.Text='تغییر فقط در محدودهٔ اعلام‌شده انجام شد؛ برای نتیجهٔ شبکه از دکمه بررسی استفاده کنید.'

      if($r.action -eq 'Stop'){$script:CurrentMode='';$script:DesiredMode='';$script:Health=$null;$script:C.SidebarState.Text='بدون اتصال'}

      if($r.action -eq 'Scan'){$script:C.ScanSummary.Text='ترتیب پیشنهادی فعلی: '+($r.result.rank -join ' ← ')}

      if($r.action -eq 'Inventory'){

       $script:C.BridgeStatus.Text=($r.result.providers|Where-Object{$_.mode -in @('WEBTUNNEL','OBFS4')}|ForEach-Object{$_.mode+': '+$_.state}) -join [Environment]::NewLine

       $running=@($r.result.providers|Where-Object{$_.state -in @('CONNECTED_NOT_VERIFIED','STARTING_OR_UNREADY')})

       if($running.Count -eq 1){$script:CurrentMode=[string]$running[0].mode;$script:DesiredMode=$script:CurrentMode;$script:C.StatusTitle.Text='مسیر فعال شناسایی شد';$script:C.StatusDetail.Text=$script:CurrentMode+' فعال است؛ برای شاهد HTTPS تازه «بررسی مسیر انتخاب‌شده» را بزنید.';$script:C.SidebarState.Text='فعال / تأیید نشده'}

       elseif($running.Count -gt 1){$script:CurrentMode='';$script:C.StatusTitle.Text='چند مسیر فعال شناسایی شد';$script:C.StatusDetail.Text='برای جلوگیری از ابهام، مسیر موردنظر را انتخاب و وضعیت را بررسی کنید.';$script:C.SidebarState.Text='نیاز به بررسی'}

       elseif(!$script:Health){$script:CurrentMode='';$script:C.StatusTitle.Text='آماده برای اتصال';$script:C.StatusDetail.Text='هیچ مسیر مدیریت‌شده‌ای فعال نیست. مسیر را انتخاب و «شروع اتصال» را بزنید.';$script:C.SidebarState.Text='بدون اتصال'}

      }

     }

     Set-Busy;$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45);$script:C.Elapsed.Text='عملیات پایان یافت؛ اتصال کل سیستم تغییر نکرد.'

    }

   }else{

    if($script:Tick % 25 -eq 0){Paint-Health}

    if(!$Smoke -and $script:C.Monitor.IsChecked -and $script:DesiredMode -and [DateTime]::UtcNow -ge $script:NextCheck){

     $script:NextCheck=[DateTime]::UtcNow.AddSeconds(90)

     if(!$script:CurrentMode){

      if($script:C.AutoRepair.IsChecked -and $script:Repairs -lt 2){$script:Repairs++;$script:Failures=0;Start-Work 'Connect' $script:DesiredMode}

      else{$script:C.SidebarState.Text='قطع / بازیابی خاموش';$script:C.StatusDetail.Text='مسیر فعال نیست و بازیابی خودکار خاموش است.'}

     }

     elseif($script:C.AutoRepair.IsChecked -and $script:Failures -ge 3 -and $script:Repairs -lt 2){$script:Repairs++;$script:Failures=0;Start-Work 'Connect' $script:DesiredMode}

     else{Start-Work 'Verify' $script:CurrentMode}

    }

   }

   if($Smoke -and $script:Tick -ge 6 -and !$script:Task){

    $script:Window.UpdateLayout();$b=[Windows.Media.Imaging.RenderTargetBitmap]::new([int]$script:Window.ActualWidth,[int]$script:Window.ActualHeight,96,96,[Windows.Media.PixelFormats]::Pbgra32);$b.Render($script:Window)

    $encoder=[Windows.Media.Imaging.PngBitmapEncoder]::new();$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($b));$f=[IO.File]::Create((Join-Path $script:Root 'evidence\UI.png'));try{$encoder.Save($f)}finally{$f.Dispose()}

    Write-Json (Join-Path $script:Root 'evidence\gui.json') @{utc=[DateTime]::UtcNow.ToString('o');visible=$script:Window.IsVisible;controls=$script:C.Count;width=$script:Window.ActualWidth;height=$script:Window.ActualHeight;ticks=$script:Tick;topmost=$script:Window.Topmost;networkRequested=$false;theme=$script:Settings.theme;workerAction=$(if($script:Last){$script:Last.action}else{''});workerExit=$(if($script:Last){$script:Last.exit}else{-1});currentMode=$script:CurrentMode;desiredMode=$script:DesiredMode;statusTitle=$script:C.StatusTitle.Text;statusDetail=$script:C.StatusDetail.Text;latency=$script:C.LatencyValue.Text;country=$script:C.CountryValue.Text;sidebarState=$script:C.SidebarState.Text;gatewayState=$script:C.GatewayState.Text;consoleLink=$script:C.ConsoleLinkState.Text;fullSystem=$script:FullSystemActive;scopeSelection=$(if($script:C.FullSystem.IsChecked){'SYSTEM'}else{'BROWSER'})};$script:AllowClose=$true;$script:Window.Close()

   }

  }catch{$script:C.StatusTitle.Text='خطای نمایش نتیجه';$script:C.Details.Text=$_.Exception.ToString()}

 })

 $script:Window.Add_ContentRendered({[void]$script:Window.Activate();[void](Gateway-Refresh);[void]$script:C.Connect.Focus();if($script:SmokeVerifyMode){Start-Work 'Verify' $script:SmokeVerifyMode}else{Start-Work 'Inventory'}})

 Set-Busy;$script:Timer.Start();[void]$script:Window.ShowDialog()

}catch{

 $msg=$_.Exception.ToString();[IO.File]::WriteAllText((Join-Path $script:Root 'logs\ui-error.txt'),$msg,[Text.UTF8Encoding]::new($false));try{Add-Type -AssemblyName PresentationFramework;[Windows.MessageBox]::Show($msg,'FreeNet Hub — startup error')|Out-Null}catch{};exit 1

}finally{if($script:Timer){$script:Timer.Stop()};if($script:Tray){$script:Tray.Visible=$false;$script:Tray.Dispose()};if($script:AppIcon){$script:AppIcon.Dispose()};if($script:Lease){$script:Lease.Dispose()}}

