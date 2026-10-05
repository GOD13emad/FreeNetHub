param([switch]$Smoke,[ValidateRange(0,4)][int]$SmokeTab=0,[switch]$SmokePreconnect,[string]$SmokeEvidencePath='')

# FreeNet Hub 4.2. One UI; browser routes plus explicit elevated PC/console gateway. No network change on launch.

Set-StrictMode -Version Latest

$ErrorActionPreference='Stop'

$script:Root=Split-Path $PSScriptRoot -Parent
New-Item -ItemType Directory -Path (Join-Path $script:Root 'logs'),(Join-Path $script:Root 'jobs'),(Join-Path $script:Root 'evidence') -Force|Out-Null

$script:Task=$null;$script:GatewayTask=$null;$script:GatewayJob='';$script:GatewayAction='';$script:Lease=$null;$script:Timer=$null;$script:Tray=$null;$script:AppIcon=$null;$script:CurrentMode='';$script:DesiredMode='';$script:ConnectionScope='BROWSER';$script:FullSystemActive=$false;$script:Health=$null;$script:Last=$null;$script:C=@{};$script:Tick=0;$script:Failures=0;$script:Repairs=0;$script:NodeConnectAfterSelect=$false;$script:NodeRows=@();$script:NodeSelected='';$script:NodeGridSortKey='';$script:NodeGridSortDescending=$false;$script:AllowClose=$false;$script:ShellHosted=($env:FREENETHUB_SHELL_HOST -eq '1');$script:SmokeVerifyMode=$(if($Smoke){[string]$env:FREENETHUB_SMOKE_VERIFY_MODE}else{''});$script:StartupUpdateChecked=$false;$script:StartupUpdateDue=[DateTime]::UtcNow.AddSeconds(12)

function Read-Json([string]$p){if(!(Test-Path -LiteralPath $p)){return $null};if((Get-Item $p).Length -gt 4194304){throw 'RESULT_TOO_LARGE'};Get-Content -LiteralPath $p -Raw -Encoding utf8|ConvertFrom-Json -AsHashtable}

function Write-Json([string]$p,$v){$t=$p+'.'+[guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllText($t,($v|ConvertTo-Json -Depth 18),[Text.UTF8Encoding]::new($false));[IO.File]::Move($t,$p,$true)}

function Sanitize($v){if($v -is [Collections.IDictionary]){$r=@{};foreach($k in $v.Keys){$r[$k]=if($k -in @('private_key','token','password','secret','home','localProxy')){'[redacted]'}elseif($k -in @('ip','endpoint') -and !$script:C.ShowIp.IsChecked){'[hidden]'}else{Sanitize $v[$k]}};return $r};if($v -is [array]){return ,@(foreach($x in $v){Sanitize $x})};if($v -is [string]){return $v.Replace($env:USERPROFILE,'[USER]')};return $v}

try{

 $script:Deps=Read-Json (Join-Path $PSScriptRoot 'dependencies.json')
 $script:Pythonw=''
 if($script:Deps -and $script:Deps.ContainsKey('pythonw') -and (Test-Path -LiteralPath ([string]$script:Deps.pythonw))){
  $script:Pythonw=[string]$script:Deps.pythonw
 }else{
  $pcmd=Get-Command pythonw.exe -ErrorAction SilentlyContinue
  if(!$pcmd){$pcmd=Get-Command python.exe -ErrorAction SilentlyContinue}
  if(!$pcmd){$pcmd=Get-Command python -ErrorAction SilentlyContinue}
  if($pcmd){$script:Pythonw=[string]$pcmd.Source}
 }

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

 foreach($e in $x.SelectNodes('//*[@Name]')){$n=$e.GetAttribute('Name');$script:C[$n]=$script:Window.FindName($n)};if($Smoke){$script:C.Tabs.SelectedIndex=$SmokeTab}

 $work=[Windows.SystemParameters]::WorkArea;$script:Window.MinWidth=[Math]::Min(1180,$work.Width);$script:Window.MinHeight=[Math]::Min(760,$work.Height);$script:Window.Width=[Math]::Min(1440,$work.Width);$script:Window.Height=[Math]::Min(1020,$work.Height)

 $script:Settings=@{theme='dark';country='AUTO';home='https://www.youtube.com/';monitor=$false;autoRepair=$false;showIp=$false;minimizeToTray=$true;order=@('NODE','WARP','TOR','GOOL','CFON');localProxy='socks5h://127.0.0.1:9909';includeDirect=$false;testPathMode='BASE';pingTimeoutSec=10;downloadTimeoutSec=30;uploadTimeoutSec=30}

 $stored=Read-Json (Join-Path $script:Root 'settings.json');if($stored){foreach($k in @($script:Settings.Keys)){if($stored.ContainsKey($k)){$script:Settings[$k]=$stored[$k]}}}

 function Set-ComboContent($ctrl,[string]$value){
  if(!$ctrl){return}
  foreach($i in $ctrl.Items){if([string]$i.Content -eq $value){$ctrl.SelectedItem=$i;return}}
 }
 function Paint-TestSettings{
  if(!$script:C.ContainsKey('ToolsTestBasePath')){return}
  $soft=$script:Window.Resources['Soft'];$selected=$script:Window.Resources['SelectedFill'];$line=$script:Window.Resources['Line'];$accent=$script:Window.Resources['Accent']
  foreach($n in @('ToolsTestBasePath','ToolsTestSelectedPath')){$script:C[$n].Background=$soft;$script:C[$n].BorderBrush=$line}
  $n=$(if([string]$script:Settings.testPathMode -eq 'SELECTED'){'ToolsTestSelectedPath'}else{'ToolsTestBasePath'})
  $script:C[$n].Background=$selected;$script:C[$n].BorderBrush=$accent
 }
 Set-ComboContent $script:C.PingTimeoutBox ([string]$script:Settings.pingTimeoutSec)
 Set-ComboContent $script:C.DownloadTimeoutBox ([string]$script:Settings.downloadTimeoutSec)
 Set-ComboContent $script:C.UploadTimeoutBox ([string]$script:Settings.uploadTimeoutSec)
 Paint-TestSettings

 $script:C.Home.Text=$script:Settings.home;$script:C.CustomProxy.Text=$script:Settings.localProxy;$script:C.ShowIp.IsChecked=$script:Settings.showIp;if($script:C.ContainsKey('ShowIpDashboard')){$script:C.ShowIpDashboard.IsChecked=$script:Settings.showIp;}$script:C.FullSystem.IsChecked=$false;$script:C.ScopeText.Text='مرورگر · پیش‌فرض امن';$script:C.ConnectionScopeText.Text='حالت: مرورگر';$script:C.TrayOption.IsChecked=$(if($script:ShellHosted){$true}else{$script:Settings.minimizeToTray});if($script:ShellHosted){$script:C.TrayOption.IsEnabled=$false;$script:C.TrayOption.ToolTip='Tray is managed by FreeNetHub.exe'};$script:C.Monitor.IsChecked=$script:Settings.monitor;$script:C.AutoRepair.IsChecked=$script:Settings.autoRepair;if($script:C.ContainsKey('UpdateInstallMain')){$script:C.UpdateInstallMain.IsEnabled=$false}

 foreach($i in $script:C.Country.Items){if($i.Content -eq $script:Settings.country){$script:C.Country.SelectedItem=$i}}

 function Theme-Apply([string]$name){
 $script:Settings.theme=$name
 $colors=if($name -eq 'light'){
  @{Bg='#F3F6FA';Panel='#FFFFFF';Ink='#173047';Muted='#4A6177';Line='#CFDAE5';Accent='#12776C';Soft='#E8F0F7';SelectedFill='#D7F1ED';PillFill='#DDE8F2';TableHeader='#D8E4EF';UpdatePanel='#E2F4F1'}
 }else{
  @{Bg='#061426';Panel='#081D33';Ink='#F5FAFF';Muted='#A6BBD0';Line='#164A68';Accent='#18E0C4';Soft='#0D2A43';SelectedFill='#0A4F5B';PillFill='#0B3654';TableHeader='#07182A';UpdatePanel='#08273E'}
 }
 foreach($k in $colors.Keys){$script:Window.Resources[$k]=[Windows.Media.BrushConverter]::new().ConvertFromString($colors[$k])}
}

 Theme-Apply $script:Settings.theme

 $script:Research=Read-Json (Join-Path $script:Root 'docs\research.json')

 function Research-Show{$q=$script:C.Search.Text;$rows=@($script:Research.products|Where-Object{!$q -or (($_|ConvertTo-Json -Compress) -match [regex]::Escape($q))});$script:C.ResearchText.Text=($rows|ForEach-Object{$_.name+"`r`n"+$_.features+"`r`n"+'نیاز / محدودیت: '+$_.requirements+"`r`n"+'تصمیم برای این محصول: '+$_.decision+"`r`n"+$_.source+"`r`n"}) -join "`r`n---------------------------`r`n"}

 Research-Show

 function Console-Capability{
  $runtime=Join-Path $script:Root 'gateway\runtime'
  $gateway=Test-Path -LiteralPath (Join-Path $runtime 'local_gateway.json')
  $provider=Test-Path -LiteralPath (Join-Path $runtime 'local_provider.json')
  $profile=Test-Path -LiteralPath (Join-Path $runtime 'console.profile.json')
  return [ordered]@{prerequisites=$gateway;localProvider=$provider;profile=$profile;canConnect=($provider -or $profile);canPreflight=$provider}
 }

 function Paint-ConsoleCapability{
  if(!$script:C.ContainsKey('ConsoleCapability')){return}
  $c=Console-Capability
  if($c.localProvider){
   $script:C.ConsoleCapability.Text='مسیر خروجی محلی کنسول آماده است؛ تست قبل از اتصال و اتصال کنسول قابل اجرا هستند.'
  }elseif($c.profile){
   $script:C.ConsoleCapability.Text='WireGuard profile کنسول آماده است؛ اتصال قابل اجراست. تست سرعت مستقل این profile هنوز نیاز به preflight اختصاصی دارد.'
  }elseif($c.prerequisites){
   $script:C.ConsoleCapability.Text='پیش‌نیازهای کنسول آماده‌اند، اما مسیر خروجی تنظیم نشده است. یک WireGuard profile معتبر وارد کنید.'
  }else{
   $script:C.ConsoleCapability.Text='ابتدا «راه‌اندازی پیش‌نیازهای کنسول» را اجرا کنید، سپس یک مسیر خروجی معتبر وارد کنید.'
  }
  return $c
 }

 function Set-Busy{

  $busy=($null -ne $script:Task -or $null -ne $script:GatewayTask)

  foreach($n in @('Connect','QuickConnect','QuickStop','EmergencyChatGPT','Browser','Verify','Scan','Inventory','Doctor','Speed','Updates','Export','ImportWeb','ImportObfs','ImportWebClipboard','ImportObfsClipboard','Save','Mode','Country','FullSystem','GatewayConsoleStart','GatewayStop','GatewayRefresh','GatewaySetupConsole','GatewayImportProfile','NodeRefreshList','NodeTestAll','NodeImportClipboard','NodeImportFile','NodeImportUrl','NodeRefreshPublic','NodeSelect','NodeFavorite','NodePin','NodeTest','NodeConnect','NodeStop','NodeSaveMeta','NodeHistory','NodeCopyLink','NodeExportRaw','NodeExportBase64','NodeFilter','NodeSort','BrowserConnectCard','FullSystemConnectCard','ConsoleConnectCard','CurrentPathSpeed','ConnectSmart','TestSmart','ConnectNode','TestNodePath','ConnectWarp','TestWarpPath','ConnectCfon','TestCfonPath','ConnectTor','TestTorPath','ConnectCustom','TestCustomPath','ConnectGool','TestGoolPath','ConnectDirect','TestDirectPath','NodeBenchmarkBatch','NodeSpeed','BridgeWebTest','BridgeWebConnect','BridgeObfsTest','BridgeObfsConnect','ConsoleSpeed','UpdateCheckMain','UpdateInstallMain','MainTest','MainConnect','AdvancedMethodsOpen','ToolsNodeRefresh','MainMethodSmart','MainMethodNode','MainMethodWarp','MainMethodCfon','MainMethodTor','MainMethodCustom','MainMethodDirect')){if($script:C.ContainsKey($n)){$script:C[$n].IsEnabled=!$busy}}

  $script:C.Cancel.IsEnabled=($null -ne $script:Task);$script:C.Progress.IsIndeterminate=$busy
  $cap=Paint-ConsoleCapability
  if($script:C.ContainsKey('GatewayConsoleStart')){$script:C.GatewayConsoleStart.IsEnabled=(-not $busy -and [bool]$cap.canConnect)}
  if($script:C.ContainsKey('ConsoleSpeed')){$script:C.ConsoleSpeed.IsEnabled=(-not $busy -and [bool]$cap.canPreflight)}
  if($script:ConnectionScope -eq 'CONSOLE'){
   $script:C.MainConnect.IsEnabled=(-not $busy -and [bool]$cap.canConnect)
   $script:C.MainTest.IsEnabled=(-not $busy -and [bool]$cap.canPreflight)
  }
  if(Get-Command Paint-ConnectionSelection -ErrorAction SilentlyContinue){Paint-ConnectionSelection}

 }

 function Friendly-Error([string]$code,$h=$null){

  switch($code){

   'NOT_CONNECTED'{return 'مسیر انتخاب‌شده متصل نیست. ابتدا «شروع اتصال» را بزنید، سپس دوباره بررسی کنید.'}

   'PATH_NOT_READY'{return 'پردازش مسیر شروع شده اما پروکسی محلی هنوز آماده نیست. چند ثانیه صبر کنید یا اتصال را دوباره برقرار کنید.'}

   'LOCAL_PROXY_UNREACHABLE'{return 'پروکسی محلی این مسیر در دسترس نیست؛ وضعیت اتصال با اجرای واقعی مسیر هم‌خوان نیست.'}

   'PORT_OWNED_BY_ANOTHER_PROCESS'{return 'پورت محلی این مسیر توسط پردازشی خارج از مالکیت تأییدشدهٔ FreeNet Hub اشغال شده است.'}

   'COUNTRY_MISMATCH_OR_UNKNOWN'{return 'HTTPS برقرار است، اما کشور خروجی با سیاست انتخاب‌شده تطابق ندارد یا قابل تأیید نیست.'}

   'COUNTRY_MODE_UNSUPPORTED'{return 'کشور هدف فعال است. برای اتصال به همان کشور، AUTO، Node Hub، CFON یا پروکسی شخصیِ قابل‌تأیید را انتخاب کنید؛ WARP/Tor کشور مشخصی را تضمین نمی‌کنند.'}
   'NODE_POOL_EMPTY'{return 'هیچ نودی وارد نشده است. از فایل، کلیپ‌بورد، Subscription HTTPS یا منبع عمومی نود اضافه کنید.'}
   'NODE_NOT_FOUND'{return 'نود انتخاب‌شده دیگر در فهرست موجود نیست؛ لیست را تازه‌سازی کنید.'}
   'NODE_NOT_SELECTED'{return 'ابتدا یک نود را از فهرست انتخاب کنید.'}
   'NODE_ACTIVE_STOP_FIRST'{return 'یک Node دیگر اکنون فعال است. ابتدا Node فعال را قطع کنید، سپس انتخاب را عوض کنید.'}
   'DEPENDENCY_NOT_CONFIGURED_SINGBOX'{return 'هستهٔ sing-box پین‌شده آماده نیست. Setup وابستگی‌های FreeNet Hub را اجرا کنید.'}
   'NODE_SUBSCRIPTION_HTTPS_REQUIRED'{return 'آدرس Subscription باید HTTPS معتبر و بدون نام‌کاربری/رمز در خود URL باشد.'}
   'NODE_SUBSCRIPTION_FETCH_FAILED'{return 'دریافت Subscription کامل نشد؛ URL یا دسترسی شبکه را بررسی کنید.'}
   'PUBLIC_NODE_SOURCE_UNREACHABLE'{return 'منبع عمومی نودها در این لحظه در دسترس نبود.'}
   'NODE_COUNTRY_NOT_FOUND'{return 'هیچ نود آزموده‌شده‌ای با کشور هدف تطابق نداشت؛ اتصال به کشور دیگری موفق اعلام نشد.'}
   'NODE_POOL_NO_HEALTHY_NODE'{return 'در نودهای بررسی‌شده مسیر سالمی پیدا نشد.'}

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

   'UPDATE_NOT_NEWER_THAN_CURRENT'{return 'نسخهٔ GitHub از این Preview جدیدتر نیست؛ downgrade انجام نمی‌شود.'}
   'UPDATE_SHA256_METADATA_MISSING'{return 'Release GitHub فاقد SHA-256 قابل‌تأیید برای installer است؛ دانلود برای نصب پذیرفته نشد.'}
   'UPDATE_INSTALLER_ASSET_MISSING'{return 'در Release رسمی GitHub installer سازگار پیدا نشد.'}
   'CONSOLE_CONNECT_FIRST'{return 'ابتدا Console Gateway را روشن کنید، سپس تست Ping/Download/Upload را اجرا کنید.'}
   'CONSOLE_SPEED_PROFILE_PATH_UNAVAILABLE'{return 'برای این WireGuard profile هنوز endpoint تست مستقل تعریف نشده؛ به‌جای عدد میزبان N/A نمایش داده می‌شود.'}
   'CONSOLE_PREFLIGHT_PROVIDER_START_FAILED'{return 'provider کنسول برای تست قبل از اتصال آماده نشد؛ تنظیمات Console Provider را بررسی کنید.'}
   'CONSOLE_PREFLIGHT_VERIFICATION_FAILED'{return 'مسیر موقت کنسول نتوانست HTTPS را قبل از اتصال تأیید کند.'}
   'CONSOLE_PREFLIGHT_COUNTRY_MISMATCH'{return 'مسیر موقت کنسول برقرار شد اما کشور خروجی مورد انتظار تأیید نشد.'}
   'CONSOLE_ROUTE_NOT_CONFIGURED'{return 'برای کنسول هنوز مسیر خروجی تعریف نشده است. در تب کنسول یک WireGuard profile معتبر وارد کنید.'}
   'CONSOLE_PROFILE_PREFLIGHT_UNAVAILABLE'{return 'WireGuard profile موجود است، اما تست سرعت مستقل قبل از اتصال برای این profile هنوز آماده نشده است.'}
   'SYSTEM_TUNNEL_NOT_ACTIVE'{return 'برای تست Full System باید WARP واقعی روی مسیر سیستم تأیید شود.'}
   'PATH_SPEED_VERIFICATION_FAILED'{return 'مسیر برای تست Performance تأیید نشد؛ عدد سرعت نامعتبر نمایش داده نمی‌شود.'}
   default{return $(if($code){'خطا: '+$code}else{'عملیات کامل نشد. جزئیات فنی را بررسی کنید.'})}

  }

 }

 function Paint-Health{

  $h=$script:Health;if(!$h -or !$h.ContainsKey('mode') -or !$h.ContainsKey('checked')){return}

  $state=$(if($h.ContainsKey('state')){[string]$h.state}else{''});$connected=$(if($h.ContainsKey('connected')){[bool]$h.connected}else{$true})

  $fresh=$false;try{$age=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($h.checked)).TotalSeconds;$fresh=$age -ge 0 -and $age -lt 65}catch{}

  $script:C.RouteValue.Text=[string]$h.mode
  $uiCountry=$(if($script:C.Country.SelectedItem){[string]$script:C.Country.SelectedItem.Content}else{'AUTO'})
  $countryMismatch=[bool]($connected -and $uiCountry -ne 'AUTO' -and [string]$h.country -ne $uiCountry)
  if($countryMismatch){
   $script:C.CountryValue.Text=$(if($h.country){[string]$h.country}else{'نامشخص'})
   $script:C.LatencyValue.Text='—';$script:C.IpValue.Text='—'
   $script:C.StatusTitle.Text='کشور خروجی با انتخاب شما یکی نیست'
   $script:C.StatusDetail.Text='هدف: '+$uiCountry+' · خروجی فعلی: '+$(if($h.country){[string]$h.country}else{'نامشخص'})+' · این اتصال برای کشور هدف سالم اعلام نمی‌شود؛ دوباره متصل شوید.'
   $script:C.SidebarState.Text='نیاز به اتصال مجدد';$script:C.SidebarDetail.Text='کشور انتخاب‌شده باید با exit واقعی تطابق داشته باشد.'
   return
  }

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

  $script:C.StatusDetail.Text=if(!$h.healthy){Friendly-Error ([string]$h.error) $h}elseif($h.mode -in @('CFON','NODE')){'کشور خروجی با exit واقعی بررسی شده است؛ این شاهد مربوط به HTTPS است.'}else{'این نتیجهٔ آزمون وب است؛ ورود به حساب، رسانه و همهٔ انواع نشت آزمون جدا دارند.'}

  $script:C.SidebarState.Text=if($h.healthy -and $fresh){'بررسی موفق'}elseif($h.healthy){'متصل / شاهد قدیمی'}else{'متصل / نیاز به بررسی'}

  $script:C.SidebarDetail.Text='آخرین شاهد: '+$h.checked

 }

 function Node-StateText($n){
  $lt=$(if($n.ContainsKey('last_test')){$n.last_test}else{$null});$ep=$(if($n.ContainsKey('endpoint_test')){$n.endpoint_test}else{$null})
  return $(if($lt -and $lt.healthy){'✓ '+[string]$lt.country+' '+$(if($null -ne $lt.seconds){([math]::Round([double]$lt.seconds*1000)).ToString()+'ms'}else{''})}elseif($lt){'× proxy'}elseif($ep -and $ep.reachable){'TCP '+[string]$ep.latency_ms+'ms'}elseif($ep){'× TCP'}else{'?'})
 }

 function Format-Metric([object]$v,[string]$unit){
  if($null -eq $v -or [string]::IsNullOrWhiteSpace([string]$v)){return '—'}
  try{return ([math]::Round([double]$v,1)).ToString()+' '+$unit}catch{return '—'}
 }

 function Get-MethodMetricControl([string]$mode){
  return $(switch($mode){'NODE'{'NodeMetric'};'WARP'{'WarpMetric'};'CFON'{'CfonMetric'};'GOOL'{'GoolMetric'};'TOR'{'TorMetric'};'WEBTUNNEL'{'WebTunnelMetric'};'OBFS4'{'Obfs4Metric'};'CUSTOM'{'CustomMetric'};'DIRECT'{'DirectMetric'};default{''}})
 }

 function Get-DashPrefix([string]$mode){
  return $(switch($mode){'NODE'{'DashNode'};'WARP'{'DashWarp'};'CFON'{'DashCfon'};'GOOL'{'DashGool'};'TOR'{'DashTor'};'WEBTUNNEL'{'DashWebTunnel'};'OBFS4'{'DashObfs4'};'CUSTOM'{'DashCustom'};'DIRECT'{'DashDirect'};default{''}})
 }

 function Paint-TestState([string]$mode,[string]$state,[string]$detail='',[bool]$Primary=$true){
  $dashPrefix=Get-DashPrefix $mode
  if($dashPrefix){
   foreach($k in @('Ping','Down','Up')){$n=$dashPrefix+$k;if($script:C.ContainsKey($n)){$script:C[$n].Text=$(if($state -eq 'RUNNING'){'...'}else{'N/A'})}}
   $n=$dashPrefix+'State';if($script:C.ContainsKey($n)){$script:C[$n].Text=$(if($state -eq 'RUNNING'){'در حال تست...'}elseif($state -eq 'TIMEOUT'){'TIMEOUT'}elseif($state -eq 'SKIP'){'N/A'}else{'FAIL'})}
  }
  $metric=Get-MethodMetricControl $mode
  if($metric -and $script:C.ContainsKey($metric)){$script:C[$metric].Text=$(if($state -eq 'RUNNING'){'در حال تست...'}else{'N/A'+$(if($detail){' • '+$detail}else{''})})}
  if(!$Primary){return}
  if($state -eq 'RUNNING'){
   if($script:C.ContainsKey('TestStateValue')){$script:C.TestStateValue.Text='در حال تست...'}
  }else{
   $script:C.MetricPing.Text='N/A';$script:C.MetricDownload.Text='N/A';$script:C.MetricUpload.Text='N/A';$script:C.MetricCountry.Text='?'
   $script:C.MetricFreshness.Text='آخرین تست ناموفق: '+[DateTimeOffset]::UtcNow.ToString('o')
   if($script:C.ContainsKey('TestStateValue')){$script:C.TestStateValue.Text=$state+' • '+$detail}
  }
 }

 function Paint-Performance($p,[string]$mode='',[bool]$Primary=$true){
  if(!$p){return}
  $ping=Format-Metric $p.pingMs 'ms';$down=Format-Metric $p.downloadMbps 'Mbps';$up=Format-Metric $p.uploadMbps 'Mbps'
  $country=$(if($p.country){[string]$p.country}else{'?'})
  $line='Ping '+$ping+' • Down '+$down+' • Up '+$up
  switch($mode){
   'NODE'{$script:C.NodeMetric.Text=$line;if($script:C.ContainsKey('CompareNode')){$script:C.CompareNode.Text=$line+' • '+$country}}
   'WARP'{$script:C.WarpMetric.Text=$line;if($script:C.ContainsKey('CompareWarp')){$script:C.CompareWarp.Text=$line+' • '+$country}}
   'CFON'{$script:C.CfonMetric.Text=$line}
   'GOOL'{if($script:C.ContainsKey('GoolMetric')){$script:C.GoolMetric.Text=$line}}
   'TOR'{$script:C.TorMetric.Text=$line}
   'WEBTUNNEL'{if($script:C.ContainsKey('WebTunnelMetric')){$script:C.WebTunnelMetric.Text=$line}}
   'OBFS4'{if($script:C.ContainsKey('Obfs4Metric')){$script:C.Obfs4Metric.Text=$line}}
   'CUSTOM'{$script:C.CustomMetric.Text=$line}
   'DIRECT'{if($script:C.ContainsKey('DirectMetric')){$script:C.DirectMetric.Text=$line};if($script:C.ContainsKey('CompareDirect')){$script:C.CompareDirect.Text=$line+' • '+$country}}
  }
  $dashPrefix=Get-DashPrefix $mode
  if($dashPrefix){
   foreach($pair in @(@('Ping',$ping),@('Down',$down),@('Up',$up),@('State',$(if($p.ok){'PASS'}else{'FAIL / N/A'})))){
    $n=$dashPrefix+$pair[0];if($script:C.ContainsKey($n)){$script:C[$n].Text=[string]$pair[1]}
   }
  }
  if(!$Primary){return}
  $script:C.MetricPing.Text=$ping;$script:C.MetricDownload.Text=$down;$script:C.MetricUpload.Text=$up;$script:C.MetricCountry.Text=$country
  $script:C.MetricFreshness.Text='آخرین تست: '+$(if($p.ContainsKey('checked') -and $p.checked){[string]$p.checked}else{[DateTimeOffset]::UtcNow.ToString('o')})
  $script:C.StatusTitle.Text=$(if($p.ok){'تست مسیر موفق بود'}else{'تست مسیر کامل نبود'})
  if($script:C.ContainsKey('TestStateValue')){$script:C.TestStateValue.Text=$(if($p.ok){'PASS • مسیر واقعی بررسی شد'}else{'FAIL / N/A'})}
  $script:C.StatusDetail.Text=$mode+' • '+$line+' • Country '+$country
 }

 function Select-ModeTag([string]$tag){
  foreach($i in $script:C.Mode.Items){if([string]$i.Tag -eq $tag){$script:C.Mode.SelectedItem=$i;return}}
 }

 function Resolve-SystemProvider([string]$tag=''){
  if(!$tag){$tag=if($script:C.Mode.SelectedItem){[string]$script:C.Mode.SelectedItem.Tag}else{'AUTO'}}
  if($tag -eq 'NODE'){return 'NODE'}
  if($tag -eq 'WARP'){return 'WARP'}
  if($tag -eq 'AUTO'){
   $country=if($script:C.Country.SelectedItem){[string]$script:C.Country.SelectedItem.Content}else{'AUTO'}
   if($country -and $country -ne 'AUTO'){return 'NODE'}
   return 'WARP'
  }
  return ''
 }

 function Paint-ConnectionSelection{
  $scope=if($script:ConnectionScope -eq 'SYSTEM'){'کل سیستم'}elseif($script:ConnectionScope -eq 'CONSOLE'){'کنسول'}else{'مرورگر'}
  $tag=if($script:C.Mode.SelectedItem){[string]$script:C.Mode.SelectedItem.Tag}else{'AUTO'}
  $method=if($script:C.Mode.SelectedItem){[string]$script:C.Mode.SelectedItem.Content}else{'—'}
  $country=if($script:C.Country.SelectedItem){[string]$script:C.Country.SelectedItem.Content}else{'AUTO'}
  $accent=$script:Window.Resources['Accent'];$soft=$script:Window.Resources['Soft'];$selected=$script:Window.Resources['SelectedFill'];$line=$script:Window.Resources['Line']

  foreach($n in @('BrowserConnectCard','FullSystemConnectCard','ConsoleConnectCard')){
   $script:C[$n].Background=$soft;$script:C[$n].BorderBrush=$line
  }
  $scopeButton=if($script:ConnectionScope -eq 'SYSTEM'){'FullSystemConnectCard'}elseif($script:ConnectionScope -eq 'CONSOLE'){'ConsoleConnectCard'}else{'BrowserConnectCard'}
  $script:C[$scopeButton].Background=$selected
  $script:C[$scopeButton].BorderBrush=$accent

  foreach($n in @('MethodsScopeBrowser','MethodsScopeSystem','MethodsScopeConsole')){
   if($script:C.ContainsKey($n)){$script:C[$n].Background=$soft;$script:C[$n].BorderBrush=$line}
  }
  $ms=if($script:ConnectionScope -eq 'SYSTEM'){'MethodsScopeSystem'}elseif($script:ConnectionScope -eq 'CONSOLE'){'MethodsScopeConsole'}else{'MethodsScopeBrowser'}
  if($script:C.ContainsKey($ms)){$script:C[$ms].Background=$selected;$script:C[$ms].BorderBrush=$accent}
  $methodButtons=[ordered]@{
   AUTO='MainMethodSmart';NODE='MainMethodNode';WARP='MainMethodWarp';CFON='MainMethodCfon';
   TOR='MainMethodTor';CUSTOM='MainMethodCustom';DIRECT='MainMethodDirect'
  }
  $busy=($null -ne $script:Task -or $null -ne $script:GatewayTask)
  $allowed=$(if($script:ConnectionScope -eq 'SYSTEM'){@('AUTO','NODE','WARP')}elseif($script:ConnectionScope -eq 'CONSOLE'){@()}else{@('AUTO','NODE','WARP','CFON','TOR','CUSTOM','DIRECT')})
  foreach($k in $methodButtons.Keys){
   $b=$script:C[$methodButtons[$k]];$b.Background=$soft;$b.BorderBrush=$line;$b.IsEnabled=(($allowed -contains $k) -and -not $busy)
  }
  if($methodButtons.Contains($tag)){
   $sel=$script:C[$methodButtons[$tag]]
   if($sel.IsEnabled){$sel.Background=$selected;$sel.BorderBrush=$accent}
  }

  $countryCapable=(($script:ConnectionScope -eq 'BROWSER' -and $tag -in @('AUTO','NODE','CFON','CUSTOM')) -or ($script:ConnectionScope -eq 'SYSTEM' -and $tag -in @('AUTO','NODE')))
  $script:C.Country.IsEnabled=($countryCapable -and -not $busy)
  $shownCountry=$(if($countryCapable){$country}else{'—'})
  if($script:ConnectionScope -eq 'CONSOLE'){
   $method='Console Gateway';$script:C.MainConnect.Content='اتصال کنسول';$script:C.MainTest.Content='تست کنسول قبل از اتصال';$script:C.Browser.IsEnabled=$false
   $cap=Paint-ConsoleCapability
   $script:C.MainConnect.IsEnabled=(-not $busy -and [bool]$cap.canConnect)
   $script:C.MainTest.IsEnabled=(-not $busy -and [bool]$cap.canPreflight)
   if(-not $cap.canConnect){$script:C.StatusTitle.Text='کنسول نیاز به مسیر خروجی دارد';$script:C.StatusDetail.Text='پیش‌نیازها و سپس WireGuard profile معتبر را از تب «کنسول» آماده کنید.'}
  }elseif($script:ConnectionScope -eq 'SYSTEM'){
   $resolved=Resolve-SystemProvider $tag
   $method=$(if($tag -eq 'AUTO'){'Smart System → '+$resolved}else{$method})
   $script:C.MainConnect.Content='اتصال کل سیستم با روش انتخاب‌شده';$script:C.MainTest.Content='تست مسیر نهایی کل سیستم';$script:C.Browser.IsEnabled=$false
  }else{
   $script:C.MainConnect.Content='اتصال با روش انتخاب‌شده';$script:C.MainTest.Content='تست Ping + Download + Upload';$script:C.Browser.IsEnabled=$true
  }
  $script:C.ConnectionScopeText.Text='حالت: '+$scope
  $script:C.MainSelectionSummary.Text=$scope+' · '+$method+' · '+$shownCountry
  $script:C.SidebarScope.Text=$scope;$script:C.SidebarMethod.Text=$method;$script:C.SidebarTargetCountry.Text=$shownCountry
  $script:C.TestMethodValue.Text=$method
 }

 function Select-ConnectionScope([string]$scope){
  switch($scope){
   'SYSTEM'{
    $script:ConnectionScope='SYSTEM';$script:C.FullSystem.IsChecked=$true;$script:C.Mode.IsEnabled=$true
    $currentTag=if($script:C.Mode.SelectedItem){[string]$script:C.Mode.SelectedItem.Tag}else{'AUTO'};if($currentTag -notin @('AUTO','NODE','WARP')){Select-ModeTag 'AUTO'}
    $script:C.ScopeText.Text='کل سیستم · روش‌های پشتیبانی‌شده اعمال می‌شوند'
    $script:C.StatusTitle.Text='حالت کل سیستم انتخاب شد'
    $script:C.StatusDetail.Text='قبل از اتصال همان مسیر نهایی تست می‌شود. WARP و Node Pool برای کل سیستم پشتیبانی می‌شوند؛ AUTO با کشور مشخص به Node و بدون کشور به WARP می‌رود.'
   }
   'CONSOLE'{
    $script:ConnectionScope='CONSOLE';$script:C.FullSystem.IsChecked=$false;$script:C.Mode.IsEnabled=$false
    $script:C.ScopeText.Text='کنسول · مسیر مستقل Console Gateway'
    $script:C.StatusTitle.Text='حالت کنسول انتخاب شد'
    $script:C.StatusDetail.Text='تست و اتصال کنسول مستقل از مرورگر و کل سیستم انجام می‌شود.'
   }
   default{
    $script:ConnectionScope='BROWSER';$script:C.FullSystem.IsChecked=$false;$script:C.Mode.IsEnabled=$true
    $script:C.ScopeText.Text='مرورگر · پیش‌فرض امن'
    $script:C.StatusTitle.Text='حالت مرورگر انتخاب شد'
    $script:C.StatusDetail.Text='روش اتصال را انتخاب کن، تست بگیر و سپس وصل شو.'
   }
  }
  Paint-ConnectionSelection
 }

 Paint-ConnectionSelection

 function Start-ProviderConnect([string]$mode){
  Select-ModeTag $mode
  if(Scope-IsFullSystem){
   $provider=Resolve-SystemProvider $mode
   if(!$provider){$script:C.StatusTitle.Text='این روش Browser Only است';$script:C.StatusDetail.Text='برای Full System فقط WARP یا Node Pool قابل استفاده است.';return}
   $policy=$(if($provider -eq 'NODE' -and $mode -eq 'AUTO'){'AUTO'}else{'SELECTED'})
   if($provider -eq 'NODE' -and $policy -eq 'SELECTED' -and !(Persistent-SelectedNodeId)){$script:C.StatusTitle.Text='برای Full System یک Node انتخاب کنید';$script:C.StatusDetail.Text='از «سرورها / نودها» یک Node را انتخاب و قبل از اتصال تست کنید.';$script:C.Tabs.SelectedIndex=2;return}
   $script:DesiredMode=$provider;Start-GatewayRequest 'StartPc' $provider $policy;return
  }
  if($mode -eq 'DIRECT' -and [Windows.MessageBox]::Show('Direct تونل نیست و IP اصلی را به مقصد نشان می‌دهد. ادامه؟','FreeNet Hub · Direct','YesNo','Warning') -ne 'Yes'){return}
  $script:DesiredMode=$mode;$script:Repairs=0;Start-Work 'Connect' $mode
 }

 function Connect-MethodCard([string]$mode){
  Select-ModeTag $mode;Paint-ConnectionSelection
  if($script:ConnectionScope -eq 'CONSOLE'){Start-GatewayRequest 'StartConsole';return}
  Start-ProviderConnect $mode
 }

 function Start-ProviderPing([string]$mode){
  Select-ModeTag $mode
  if($script:ConnectionScope -eq 'CONSOLE'){Start-Work 'ConsolePreflight' 'CONSOLE';return}
  if($script:ConnectionScope -eq 'SYSTEM'){Start-ProviderBenchmark $mode;return}
   Paint-TestState $mode 'RUNNING'
  Start-Work 'ProviderPing' $mode
 }

 function Start-ConfiguredTest([bool]$PingOnly=$false){
  if($script:ConnectionScope -eq 'CONSOLE'){Start-Work 'ConsolePreflight' 'CONSOLE';return}
  $mode=Selected
  # BASE means the selected method is exercised over the host/base transport.
  # It must never silently replace Smart/Node/WARP/etc. with Direct.
  if($PingOnly){Start-ProviderPing $mode}else{Start-ProviderBenchmark $mode}
 }

 function Start-ProviderBenchmark([string]$mode){
  Select-ModeTag $mode
  if($script:ConnectionScope -eq 'CONSOLE'){Start-Work 'ConsolePreflight' 'CONSOLE';return}
  if($script:ConnectionScope -eq 'SYSTEM'){
   Paint-TestState $mode 'RUNNING'
   $provider=Resolve-SystemProvider $mode
   if(!$provider){$script:C.StatusTitle.Text='این روش برای Full System پشتیبانی نمی‌شود';return}
   if($script:FullSystemActive){$active=$(if($script:DesiredMode -in @('NODE','WARP')){$script:DesiredMode}else{$provider});Start-Work 'SystemSpeed' $active;return}
   if($provider -eq 'NODE'){
    if($mode -eq 'AUTO'){Start-Work 'NodeSystemPreflightAuto' 'NODE';return}
    if(!(Persistent-SelectedNodeId)){$script:C.StatusTitle.Text='برای Node یک نود انتخاب کنید';$script:C.StatusDetail.Text='برای Full System در حالت Node باید نود انتخاب‌شده داشته باشید.';$script:C.Tabs.SelectedIndex=2;return}
    Start-Work 'NodeSystemPreflight' 'NODE';return
   }
   Start-Work 'ProviderBenchmark' $provider
   return
  }
  if($mode -eq 'AUTO'){
   foreach($m in @('NODE','WARP','CFON','GOOL','TOR','CUSTOM','DIRECT')){Paint-TestState $m 'RUNNING' '' $false}
   foreach($m in @('WEBTUNNEL','OBFS4')){Paint-TestState $m 'SKIP' 'NOT_CONFIGURED_OR_NOT_TESTED' $false}
   if($script:C.ContainsKey('SmartMetric')){$script:C.SmartMetric.Text='در حال تست همه روش‌ها...'}
   if($script:C.ContainsKey('CompareSmart')){$script:C.CompareSmart.Text='Smart فقط انتخاب‌گر است؛ نتایج روی روش‌های واقعی ثبت می‌شوند.'}
   if($script:C.ContainsKey('TestStateValue')){$script:C.TestStateValue.Text='Smart: در حال تست همه روش‌های واقعی...'}
  }else{Paint-TestState $mode 'RUNNING'}
  Start-Work 'ProviderBenchmark' $mode
 }

 function Install-VerifiedUpdate([string]$path){
  if(!$path -or !(Test-Path -LiteralPath $path)){$script:C.UpdateStatus.Text='فایل آپدیت معتبر پیدا نشد.';return}
  $directDpi=Get-DirectDpiStatus
  $gateway=Gateway-Refresh
  if(!$gateway){$script:C.UpdateStatus.Text='وضعیت Gateway قابل راستی‌آزمایی نیست؛ برای جلوگیری از قطع ناقص، نصب آپدیت شروع نشد.';return}
  if($script:CurrentMode -or $script:FullSystemActive -or [bool]$gateway.running -or $directDpi.active -or $directDpi.stale){
   $script:C.UpdateStatus.Text='قبل از نصب آپدیت، اتصال‌های متعلق به FreeNet Hub را Stop/rollback کنید. برنامه باز می‌ماند.'
   return
  }
  if([Windows.MessageBox]::Show('Installer از GitHub دانلود و SHA-256 آن تأیید شده است. برنامه بسته و نصب بدون reboot شروع شود؟','FreeNet Hub Update','YesNo','Question') -ne 'Yes'){return}
  try{
   $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$path;$psi.UseShellExecute=$false
   foreach($a in @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS')){[void]$psi.ArgumentList.Add($a)}
   [void][Diagnostics.Process]::Start($psi);$script:AllowClose=$true;$script:Window.Close()
  }catch{$script:C.UpdateStatus.Text='شروع installer ناموفق: '+$_.Exception.Message}
 }

 function Get-NodeRowValue($row,[string]$property){
  $p=$row.PSObject.Properties[$property];if(!$p){return $null};return $p.Value
 }

 function Sort-NodeRowsNumeric($rows,[string]$property,[bool]$descending=$false){
  $present=@($rows|Where-Object{$null -ne (Get-NodeRowValue $_ $property)})
  $missing=@($rows|Where-Object{$null -eq (Get-NodeRowValue $_ $property)}|Sort-Object NameSort)
  if($descending){$present=@($present|Sort-Object @{Expression={[double](Get-NodeRowValue $_ $property)};Descending=$true},NameSort)}
  else{$present=@($present|Sort-Object @{Expression={[double](Get-NodeRowValue $_ $property)}},NameSort)}
  return @($present)+@($missing)
 }

 function Sort-NodeRowsText($rows,[string]$property,[bool]$descending=$false){
  $present=@();$missing=@()
  foreach($row in @($rows)){
   $v=[string](Get-NodeRowValue $row $property)
   if([string]::IsNullOrWhiteSpace($v) -or $v -in @('?','N/A','—')){$missing+=,$row}else{$present+=,$row}
  }
  if($descending){$present=@($present|Sort-Object @{Expression={([string](Get-NodeRowValue $_ $property)).ToLowerInvariant()};Descending=$true},NameSort)}
  else{$present=@($present|Sort-Object @{Expression={([string](Get-NodeRowValue $_ $property)).ToLowerInvariant()}},NameSort)}
  return @($present)+@($missing|Sort-Object NameSort)
 }

 function Apply-NodeFilter{
  if(!$script:C.ContainsKey('NodeList')){return}
  $keep=Selected-NodeId;$script:C.NodeList.Items.Clear()
  $q=$(if($script:C.NodeFilter){$script:C.NodeFilter.Text.Trim().ToLowerInvariant()}else{''})
  $rows=@($script:NodeRows)
  if($q){
   $rows=@($rows|Where-Object{
    $n=$_.Node;$blob=([string]$n.name+' '+[string]$n.protocol+' '+[string]$n.server+' '+([string]::Join(' ',@($n.tags)))+' '+[string]$n.note+' '+$(if($n.last_test){[string]$n.last_test.country}else{''})).ToLowerInvariant()
    $blob.Contains($q)
   })
  }
  if($script:NodeGridSortKey){
   switch($script:NodeGridSortKey){
    'PingValue'{$rows=Sort-NodeRowsNumeric $rows 'PingValue' $script:NodeGridSortDescending}
    'DownloadValue'{$rows=Sort-NodeRowsNumeric $rows 'DownloadValue' $script:NodeGridSortDescending}
    'UploadValue'{$rows=Sort-NodeRowsNumeric $rows 'UploadValue' $script:NodeGridSortDescending}
    default{$rows=Sort-NodeRowsText $rows $script:NodeGridSortKey $script:NodeGridSortDescending}
   }
  }else{
   $sort=$(if($script:C.NodeSort.SelectedItem){[string]$script:C.NodeSort.SelectedItem.Tag}else{'SMART'})
   switch($sort){
    'LATENCY'{$rows=Sort-NodeRowsNumeric $rows 'PingValue' $false}
    'SPEED'{$rows=Sort-NodeRowsNumeric $rows 'DownloadValue' $false}
    'UPLOAD'{$rows=Sort-NodeRowsNumeric $rows 'UploadValue' $false}
    'NAME'{$rows=Sort-NodeRowsText $rows 'NameSort' $false}
    'COUNTRY'{$rows=Sort-NodeRowsText $rows 'CountrySort' $false}
    'PROTOCOL'{$rows=Sort-NodeRowsText $rows 'ProtocolSort' $false}
   }
  }
  foreach($o in @($rows)){[void]$script:C.NodeList.Items.Add($o);if($keep -and [string]$o.Id -eq $keep){$script:C.NodeList.SelectedItem=$o}}
 }

 function Paint-Nodes($h){
  if(!$h){return}
  if($h.ContainsKey('nodes')){
   $selected=$(if($h.ContainsKey('selected')){[string]$h.selected}else{''});$script:NodeSelected=$selected;$script:NodeRows=@()
   foreach($n in @($h.nodes)){
    $state=Node-StateText $n
    $marks=$(if($n.pinned){'📌 '}else{''})+$(if($n.favorite){'★ '}else{''})
    $rating=$(if([int]$n.rating -gt 0){' '+('★'*[int]$n.rating)}else{''})
    $display=$marks+$state+'  ['+[string]$n.protocol+'] '+[string]$n.name+$rating+'  ·  '+[string]$n.server+':'+[string]$n.port
    $perf=$(if($n.performance_test){$n.performance_test}else{$null});$lt=$(if($n.last_test){$n.last_test}else{$null})
    $pingValue=$null
    if($perf -and $null -ne $perf.pingMs){$pingValue=[double]$perf.pingMs}
    elseif($lt -and $null -ne $lt.seconds){$pingValue=[double]$lt.seconds*1000}
    elseif($n.endpoint_test -and $n.endpoint_test.reachable -and $null -ne $n.endpoint_test.latency_ms){$pingValue=[double]$n.endpoint_test.latency_ms}
    $downloadValue=$(if($perf -and $perf.ok -and $null -ne $perf.downloadMbps){[double]$perf.downloadMbps}else{$null})
    $uploadValue=$(if($perf -and $perf.ok -and $null -ne $perf.uploadMbps){[double]$perf.uploadMbps}else{$null})
    $ping=$(if($null -ne $pingValue){Format-Metric $pingValue 'ms'}else{'?'})
    $down=$(if($null -ne $downloadValue){Format-Metric $downloadValue 'Mbps'}elseif($perf){'N/A'}else{'?'})
    $up=$(if($null -ne $uploadValue){Format-Metric $uploadValue 'Mbps'}elseif($perf){'N/A'}else{'?'})
    $country=$(if($perf -and $perf.country){[string]$perf.country}elseif($lt -and $lt.country){[string]$lt.country}else{'?'})
    $last=$(if($perf -and $perf.checked){[string]$perf.checked}elseif($lt -and $lt.checked){[string]$lt.checked}else{'?'})
    $status=$(if($perf -and $perf.ok){'PASS'}elseif($perf){'FAIL'}elseif($lt -and $lt.healthy){'HTTPS'}elseif($n.endpoint_test -and $n.endpoint_test.reachable){'TCP'}else{'—'})
    $nameText=($marks+[string]$n.name+$rating);$protocolText=[string]$n.protocol;$sourceText=[string]$n.source
    $script:NodeRows+=,[pscustomobject]@{Id=[string]$n.id;Display=$display;Status=$status;StatusSort=$status;Name=$nameText;NameSort=([string]$n.name).ToLowerInvariant();Country=$country;CountrySort=$country.ToLowerInvariant();Protocol=$protocolText;ProtocolSort=$protocolText.ToLowerInvariant();Ping=$ping;PingValue=$pingValue;Download=$down;DownloadValue=$downloadValue;Upload=$up;UploadValue=$uploadValue;Source=$sourceText;SourceSort=$sourceText.ToLowerInvariant();LastTest=$last;LastTestSort=$last.ToLowerInvariant();Node=$n}
   }
   Apply-NodeFilter
   $script:C.NodeSummary.Text='نودها: '+[string]$h.total+$(if($h.ContainsKey('reachable')){' · TCP قابل‌دسترسی: '+[string]$h.reachable}else{''})+' · انتخاب‌شده: '+$(if($selected){$selected}else{'ندارد'})
  }
  if($h.ContainsKey('node')){$n=$h.node;$script:C.NodeDetail.Text='انتخاب: ['+[string]$n.protocol+'] '+[string]$n.name+' · '+[string]$n.server+':'+[string]$n.port}
  if($h.ContainsKey('test')){
   $q=$h.test;$ms=$(if($null -ne $q.seconds){([math]::Round([double]$q.seconds*1000)).ToString()+' ms'}else{'—'})
   $script:C.NodeDetail.Text=$(if($q.healthy){'تست واقعی PASS · کشور خروجی: '+[string]$q.country+' · HTTPS: '+$ms}else{'تست واقعی FAIL · '+(Friendly-Error ([string]$q.error) $q)})
  }
  if($h.ContainsKey('performance')){$p=$h.performance;Paint-Performance $p 'NODE';$script:C.NodeDetail.Text='Node performance · Ping '+(Format-Metric $p.pingMs 'ms')+' · Download '+(Format-Metric $p.downloadMbps 'Mbps')+' · Upload '+(Format-Metric $p.uploadMbps 'Mbps')}
  if($h.ContainsKey('warning')){$script:C.NodeDetail.Text=[string]$h.warning}
 }

 function Selected-NodeObject{if($script:C.NodeList.SelectedItem){return $script:C.NodeList.SelectedItem.Node};return $null}

 function Fill-NodeEditor{
  $n=Selected-NodeObject;if(!$n){return}
  $script:C.NodeNameEdit.Text=[string]$n.name;$script:C.NodeTags.Text=([string]::Join(', ',@($n.tags)));$script:C.NodeNote.Text=[string]$n.note
  $rating=[Math]::Max(0,[Math]::Min(5,[int]$n.rating));$script:C.NodeRating.SelectedIndex=$rating
 }

 function Get-RawNodeById([string]$id){
  if(!$id){return $null};$store=Read-Json (Join-Path $script:Root 'data\nodes.json');if(!$store){return $null}
  foreach($n in @($store.nodes)){if([string]$n.id -eq $id){return $n}}
  return $null
 }

 function Export-NodeLinks([bool]$base64){
  $store=Read-Json (Join-Path $script:Root 'data\nodes.json');if(!$store -or !@($store.nodes).Count){$script:C.NodeDetail.Text='نودی برای خروجی وجود ندارد.';return}
  $rows=@($store.nodes|Where-Object{![string]::IsNullOrWhiteSpace([string]$_.raw)}|ForEach-Object{[string]$_.raw})
  $d=[Microsoft.Win32.SaveFileDialog]::new();$d.Filter='Text (*.txt)|*.txt';$d.FileName=$(if($base64){'freenethub-nodes-base64.txt'}else{'freenethub-nodes.txt'})
  if(!$d.ShowDialog($script:Window)){return}
  $text=$rows -join "`n";if($base64){$text=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text))}
  [IO.File]::WriteAllText($d.FileName,$text,[Text.UTF8Encoding]::new($false));$script:C.NodeDetail.Text='خروجی محلی ذخیره شد: '+[IO.Path]::GetFileName($d.FileName)+' · شامل credential نود است؛ محرمانه نگه دارید.'
 }

 function Selected-NodeId{if($script:C.NodeList.SelectedItem){return [string]$script:C.NodeList.SelectedItem.Id};return ''}

 function Start-Work([string]$action,[string]$mode='AUTO',[string]$payload=''){

  if($script:Task -or $script:GatewayTask){return}

  $script:Job=[guid]::NewGuid().ToString('N');$script:Action=$action;$script:Started=[DateTime]::UtcNow;$script:Cancelled=$false

  if(!$script:Pythonw){throw 'PYTHON_RUNTIME_NOT_AVAILABLE'};$p=[Diagnostics.ProcessStartInfo]::new();$p.FileName=$script:Pythonw;$p.UseShellExecute=$false;$p.CreateNoWindow=$true;$p.WorkingDirectory=$script:Root

  $budget=$(if($action -eq 'ProviderBenchmark' -and $mode -eq 'AUTO'){'600'}elseif($action -in @('Scan','NodeBenchmarkBatch','UpdateDownload')){'600'}elseif($action -in @('ProviderBenchmark','PathSpeed','SystemSpeed','ConsoleSpeed','NodeSpeed','NodeSystemPreflight')){'360'}else{'240'})
  foreach($a in @((Join-Path $PSScriptRoot 'engine.py'),'--action',$action,'--mode',$mode,'--job',$script:Job,'--budget',$budget)){[void]$p.ArgumentList.Add($a)}

  if($payload){[void]$p.ArgumentList.Add('--payload');[void]$p.ArgumentList.Add($payload)}

  try{$script:Task=[Diagnostics.Process]::Start($p);$script:C.StatusTitle.Text='در حال انجام درخواست';$script:C.SidebarState.Text='در حال بررسی';$script:C.StatusDetail.Text='پنجره پاسخ‌گو می‌ماند؛ لغو عملیات در دسترس است.';$script:C.Details.Text='Job: '+$script:Job+"`r`nAction: "+$action;Set-Busy}

  catch{$script:Task=$null;$script:C.StatusTitle.Text='شروع عملیات ناموفق';$script:C.StatusDetail.Text=$_.Exception.Message;Set-Busy}

 }

 function Selected{return [string]$script:C.Mode.SelectedItem.Tag}
function Persistent-SelectedNodeId{
 $ui=Selected-NodeId;if($ui){return $ui}
 try{$p=Join-Path $script:Root 'data\nodes.json';if(Test-Path $p){$j=Get-Content $p -Raw -Encoding UTF8|ConvertFrom-Json;if([string]$j.selected){return [string]$j.selected}}}catch{}
 return ''
}

 function Sync-CountrySelection{
  if(!$script:C.Country.SelectedItem){return}
  $newCountry=[string]$script:C.Country.SelectedItem.Content
  if($newCountry -notin @('AT','DE','NL','US','CA','GB','FR','SG','JP','AUTO')){return}
  if([string]$script:Settings.country -eq $newCountry){return}
  $script:Settings.country=$newCountry
  Write-Json (Join-Path $script:Root 'settings.json') $script:Settings
  $script:C.StatusTitle.Text='کشور هدف تغییر کرد'
  $actual=$(if($script:Health -and $script:Health.ContainsKey('country')){[string]$script:Health.country}else{''})
  if($newCountry -eq 'AUTO'){
   $script:C.StatusDetail.Text='انتخاب خودکار فعال شد؛ اتصال بعدی بهترین مسیر سالم را انتخاب می‌کند.'
  }elseif($actual -and $actual -eq $newCountry){
   $script:C.StatusDetail.Text='خروجی فعلی با کشور انتخاب‌شده هم‌خوان است؛ در اتصال بعدی نیز دوباره راستی‌آزمایی می‌شود.'
  }else{
   $script:C.StatusDetail.Text='اتصال فعلی برای کشور '+$newCountry+' معتبر نیست؛ «شروع اتصال» را بزنید تا خروجی واقعی همان کشور پیدا و تأیید شود.'
  }
 }
 $script:C.Country.Add_SelectionChanged({Sync-CountrySelection;Paint-ConnectionSelection})
 $script:C.Mode.Add_SelectionChanged({if($script:C.ContainsKey('TestStateValue')){$script:C.TestStateValue.Text='هنوز تست نشده'};Paint-ConnectionSelection})
 $script:C.Tabs.Add_SelectionChanged({
  if($script:C.Tabs.SelectedIndex -eq 2 -and !$script:Task -and !$script:GatewayTask){
   Start-Work 'NodeList' 'NODE'
  }
 })

 function Cancel-Work{$script:BenchmarkAllActive=$false;if($script:Task){[IO.File]::WriteAllText((Join-Path $script:Root ('jobs\'+$script:Job+'.cancel')),'user cancel');$script:Cancelled=$true;$script:C.Cancel.IsEnabled=$false;$script:C.StatusDetail.Text='لغو درخواست شد؛ منتظر ثبت نتیجه و پاک‌سازی محدود هستیم.'}}

 function Open-Doc([string]$file){$p=Join-Path $script:Root ('docs\'+$file);$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='notepad.exe';$psi.UseShellExecute=$false;[void]$psi.ArgumentList.Add($p);[void][Diagnostics.Process]::Start($psi)}



 function Gateway-Refresh{

  try{

   $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true

   foreach($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $script:Root 'gateway\gateway_control.ps1'),'-Action','Status')){[void]$psi.ArgumentList.Add($a)}

   $p=[Diagnostics.Process]::Start($psi);if(!$p.WaitForExit(8000)){try{$p.Kill($true)}catch{};throw 'GATEWAY_STATUS_TIMEOUT'};$raw=$p.StandardOutput.ReadToEnd();if($p.ExitCode -ne 0){throw 'GATEWAY_STATUS_FAILED'}

   $j=$raw|ConvertFrom-Json -AsHashtable;$g=$j.result

   $script:FullSystemActive=[bool]($g.running -and [string]$g.mode -eq 'PC_TUNNEL');if($script:FullSystemActive){$ap=[string]$g.session.provider;if($ap -notin @('NODE','WARP')){$ap='WARP'};$script:DesiredMode=$ap;$script:ConnectionScope='SYSTEM';$script:C.FullSystem.IsChecked=$true;$script:C.ScopeText.Text='کل سیستم · '+$ap+' فعال';Select-ModeTag $ap};if($g.running -and [string]$g.mode -eq 'CONSOLE_ONLY'){$script:C.GatewayState.Text='اتصال کنسول فعال است';$script:C.GatewayDetail.Text='Mode: CONSOLE_ONLY · مسیر میزبان جداگانه راستی‌آزمایی شده است.'}elseif($script:FullSystemActive){$script:C.GatewayState.Text='اتصال کنسول خاموش است';$script:C.GatewayDetail.Text='تونل کل سیستم از صفحهٔ اتصال فعال است؛ این صفحه فقط کنسول را مدیریت می‌کند.'}else{$script:C.GatewayState.Text='اتصال کنسول خاموش است';$script:C.GatewayDetail.Text='هیچ اتصال کنسول متعلق به FreeNetHub فعال نیست.'}

   $cs=[string]$g.console.status;$an=$(if([string]$g.console.description){[string]$g.console.description}else{'آداپتور اختصاصی کنسول'});$script:C.ConsoleLinkState.Text=$an+': '+$(if($cs -eq 'Up'){'لینک برقرار'}elseif($cs -eq 'Disconnected'){'کابل متصل نیست'}elseif($cs -eq 'Missing'){'پیکربندی/سخت‌افزار پیدا نشد'}else{$cs})

   $m=$g.console.manual;$script:C.ConsoleInstructions.Text='IP: '+$m.ip+'   |   Mask: 255.255.255.0   |   Gateway: '+$m.gateway+'   |   DNS: '+$m.dns

   Paint-ConsoleCapability|Out-Null
   Set-Busy
   return $g

  }catch{$script:C.GatewayState.Text='وضعیت اتصال کنسول قابل خواندن نیست';$script:C.GatewayDetail.Text=$_.Exception.Message;return $null}

 }

 function Start-GatewayRequest([string]$action,[string]$provider='WARP',[string]$nodePolicy='SELECTED'){

  if($script:Task -or $script:GatewayTask){return}

  if($action -eq 'StartPc' -and [Windows.MessageBox]::Show(('تمام ترافیک این کامپیوتر از مسیر '+$provider+' وارد TUN می‌شود. TCP/UDP قبل و بعد از اعمال بررسی می‌شوند و شکست باعث rollback خودکار می‌شود. ادامه؟'),'FreeNet Hub · Full PC','YesNo','Warning') -ne 'Yes'){return}
  if($action -eq 'SetupConsole' -and [Windows.MessageBox]::Show('پیش‌نیازهای Gateway کنسول بررسی و در صورت نیاز نصب می‌شوند: usbipd و sing-box pinned و ابزارهای WSL. این عملیات هیچ تونلی را روشن نمی‌کند. ادامه؟','FreeNet Hub · Console Setup','YesNo','Question') -ne 'Yes'){return}

  if($action -eq 'StartConsole'){
   $cap=Console-Capability
   if(-not $cap.canConnect){$script:C.GatewayState.Text='مسیر خروجی کنسول تنظیم نشده';$script:C.GatewayDetail.Text='ابتدا پیش‌نیازها را آماده و یک WireGuard profile معتبر وارد کنید.';Set-Busy;return}

   $g=Gateway-Refresh;if($g -and [string]$g.console.status -ne 'Up'){$script:C.GatewayDetail.Text='Gateway کنسول آماده می‌شود؛ کابل را می‌توانید بعداً وصل کنید. تا برقراری لینک، مسیر در حالت انتظار می‌ماند.'}

  }

  if($action -eq 'Stop' -and [Windows.MessageBox]::Show('Gateway متعلق به FreeNetHub قطع و تنظیمات موقت آن rollback شود؟','FreeNet Hub · Stop Gateway','YesNo','Question') -ne 'Yes'){return}

  $script:GatewayJob=[guid]::NewGuid().ToString('N');$script:GatewayAction=$action;$script:GatewayStarted=[DateTime]::UtcNow

  $result=Join-Path $script:Root ('jobs\gateway-'+$script:GatewayJob+'.json');Remove-Item $result -Force -ErrorAction SilentlyContinue

  $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName='pwsh.exe';$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WorkingDirectory=$script:Root

  foreach($a in @('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',(Join-Path $script:Root 'gateway\gateway_request.ps1'),'-Action',$action,'-Job',$script:GatewayJob)){[void]$psi.ArgumentList.Add($a)}
  if($action -eq 'StartPc'){[void]$psi.ArgumentList.Add('-Provider');[void]$psi.ArgumentList.Add($provider);if($provider -eq 'NODE'){[void]$psi.ArgumentList.Add('-NodePolicy');[void]$psi.ArgumentList.Add($nodePolicy)}}

  try{$script:GatewayTask=[Diagnostics.Process]::Start($psi);$script:C.GatewayState.Text='در انتظار تأیید UAC / اجرای Gateway';$script:C.GatewayDetail.Text='Job: '+$script:GatewayJob+' · '+$action;$script:C.SidebarState.Text='عملیات شبکه در حال اجرا';Set-Busy}catch{$script:GatewayTask=$null;$script:C.GatewayState.Text='شروع Gateway ناموفق';$script:C.GatewayDetail.Text=$_.Exception.Message;Set-Busy}

 }



 $script:C.GatewayConsoleStart.Add_Click({Start-GatewayRequest 'StartConsole'})
 $script:C.GatewaySetupConsole.Add_Click({Start-GatewayRequest 'SetupConsole'})

 $script:C.GatewayStop.Add_Click({Start-GatewayRequest 'StopConsole'})

 $script:C.GatewayRefresh.Add_Click({[void](Gateway-Refresh)})

 $script:C.GatewayImportProfile.Add_Click({

  if($script:Task -or $script:GatewayTask){return}

  $d=[Microsoft.Win32.OpenFileDialog]::new();$d.Filter='WireGuard config (*.conf)|*.conf|All files (*.*)|*.*'

  if(!$d.ShowDialog($script:Window)){return}

  $country=[string]$script:C.Country.SelectedItem.Content;$out=Join-Path $script:Root 'gateway\runtime\console.profile.json'

  if(!$script:Pythonw){$script:C.GatewayState.Text='Python runtime آماده نیست';$script:C.GatewayDetail.Text='برای Import WireGuard باید Python runtime نصب یا dependency manifest معتبر باشد.';return};$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$script:Pythonw;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true

  foreach($a in @((Join-Path $script:Root 'gateway\import_wireguard.py'),$d.FileName,'--name',('Console-'+$country),'--country',$country,'--output',$out)){[void]$psi.ArgumentList.Add($a)}

  try{$p=[Diagnostics.Process]::Start($psi);if(!$p.WaitForExit(15000)){try{$p.Kill($true)}catch{};throw 'PROFILE_IMPORT_TIMEOUT'};if($p.ExitCode -ne 0){throw 'PROFILE_IMPORT_FAILED'};$script:C.GatewayState.Text='پروفایل کنسول وارد شد';$script:C.GatewayDetail.Text='کلید فقط در runtime محلی ذخیره شد. هنگام Start Console، TCP/UDP و کشور '+$country+' دوباره آزمون می‌شوند.';Paint-ConsoleCapability|Out-Null;Set-Busy}catch{$script:C.GatewayState.Text='وارد کردن پروفایل ناموفق';$script:C.GatewayDetail.Text=$_.Exception.Message;Paint-ConsoleCapability|Out-Null;Set-Busy}

 })

 function Scope-IsFullSystem{return [bool]$script:C.FullSystem.IsChecked}

$script:C.FullSystem.Add_Click({
 $on=Scope-IsFullSystem
 if($on){$script:ConnectionScope='SYSTEM';$script:C.ScopeText.Text='کل سیستم · WARP / Node Pool';$m=Selected;if($m -notin @('AUTO','NODE','WARP')){Select-ModeTag 'AUTO'}}
 else{if($script:FullSystemActive){if([Windows.MessageBox]::Show('تونل کل سیستم اکنون فعال است. خاموش و rollback شود؟','FreeNet Hub · Full System','YesNo','Question') -eq 'Yes'){Start-GatewayRequest 'Stop'}else{$script:C.FullSystem.IsChecked=$true;return}}else{$script:ConnectionScope='BROWSER';$script:C.ScopeText.Text='مرورگر · پیش‌فرض امن'}}
 Paint-ConnectionSelection
})

$script:C.QuickConnect.Add_Click({Select-ModeTag 'AUTO';Select-ConnectionScope 'BROWSER';$script:DesiredMode='AUTO';Start-Work 'Connect' 'AUTO'})

 $script:C.Connect.Add_Click({$m=Selected;if(Scope-IsFullSystem){$p=Resolve-SystemProvider $m;if(!$p){$script:C.StatusTitle.Text='روش Full System پشتیبانی نمی‌شود';return};$script:DesiredMode=$p;$script:Repairs=0;$np=$(if($p -eq 'NODE' -and $m -eq 'AUTO'){'AUTO'}else{'SELECTED'});Start-GatewayRequest 'StartPc' $p $np;return};if($m -eq 'DIRECT' -and [Windows.MessageBox]::Show('این حالت IP اصلی را به سایت‌ها نشان می‌دهد و تونل نیست. ادامه؟','FreeNet Hub','YesNo','Warning') -ne 'Yes'){return};$script:DesiredMode=$m;$script:Repairs=0;Start-Work 'Connect' $m})

 $script:C.Verify.Add_Click({$m=Selected;if($m -eq 'AUTO'){$m=if($script:CurrentMode){$script:CurrentMode}else{$script:DesiredMode}};if(!$m -or $m -eq 'AUTO'){$script:C.StatusTitle.Text='مسیر فعالی برای بررسی نیست';$script:C.StatusDetail.Text='ابتدا «شروع اتصال» را بزنید یا یک مسیر مشخص انتخاب کنید.';return};Start-Work 'Verify' $m})

 $script:C.EmergencyChatGPT.Add_Click({$script:DesiredMode='CHATGPT';$script:Repairs=0;Start-Work 'ChatGPT' 'AUTO'})

 $script:C.NodeRefreshList.Add_Click({Start-Work 'NodeRefreshSmart' 'NODE'})
 $script:C.NodeTestAll.Add_Click({Start-Work 'NodeTestAll' 'NODE'})
 $script:C.NodeImportClipboard.Add_Click({
  try{$txt=[Windows.Clipboard]::GetText()}catch{$txt=''}
  if([string]::IsNullOrWhiteSpace($txt)){$script:C.NodeDetail.Text='کلیپ‌بورد متن قابل وارد کردن ندارد.';return}
  $p=Join-Path $script:Root ('jobs\node-import-'+[guid]::NewGuid().ToString('N')+'.txt')
  [IO.File]::WriteAllText($p,$txt,[Text.UTF8Encoding]::new($false));Start-Work 'NodeImport' 'AUTO' $p
 })
 $script:C.NodeImportFile.Add_Click({
  $d=[Microsoft.Win32.OpenFileDialog]::new();$d.Filter='Node/subscription text (*.txt;*.conf)|*.txt;*.conf|All files (*.*)|*.*'
  if($d.ShowDialog($script:Window)){Start-Work 'NodeImport' 'AUTO' $d.FileName}
 })
 $script:C.NodeImportUrl.Add_Click({
  $url=$script:C.NodeSourceUrl.Text.Trim()
  if(!$url){$script:C.NodeDetail.Text='آدرس Subscription HTTPS را وارد کنید.';return}
  $p=Join-Path $script:Root ('jobs\node-sub-'+[guid]::NewGuid().ToString('N')+'.json');Write-Json $p @{url=$url};Start-Work 'NodeImportUrl' 'AUTO' $p
 })
 $script:C.NodeRefreshPublic.Add_Click({
  if([Windows.MessageBox]::Show('نودهای عمومی موقت و غیرقابل‌اعتمادند و فقط به‌عنوان کاندید وارد می‌شوند. ادامه؟','FreeNet Hub · Public Nodes','YesNo','Warning') -eq 'Yes'){Start-Work 'NodeRefreshPublic'}
 })
 $script:C.NodeSelect.Add_Click({$id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return};Start-Work 'NodeSelect' 'NODE' $id})
 $script:C.NodeFavorite.Add_Click({$id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return};Start-Work 'NodeFavorite' 'NODE' $id})
 $script:C.NodePin.Add_Click({$id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return};Start-Work 'NodePin' 'NODE' $id})
 $script:C.NodeList.Add_SelectionChanged({Fill-NodeEditor})
 $script:C.NodeList.Add_Sorting({
  param($sender,$e)
  $e.Handled=$true
  $key=[string]$e.Column.SortMemberPath
  if(!$key){return}
  $descending=($e.Column.SortDirection -eq [ComponentModel.ListSortDirection]::Ascending)
  foreach($col in $script:C.NodeList.Columns){$col.SortDirection=$null}
  $e.Column.SortDirection=$(if($descending){[ComponentModel.ListSortDirection]::Descending}else{[ComponentModel.ListSortDirection]::Ascending})
  $script:NodeGridSortKey=$key;$script:NodeGridSortDescending=$descending
  Apply-NodeFilter
 })
 $script:C.NodeFilter.Add_TextChanged({Apply-NodeFilter})
 $script:C.NodeSort.Add_SelectionChanged({$script:NodeGridSortKey='';$script:NodeGridSortDescending=$false;foreach($col in $script:C.NodeList.Columns){$col.SortDirection=$null};Apply-NodeFilter})
 $script:C.NodeSaveMeta.Add_Click({
  $id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return}
  $rating=$(if($script:C.NodeRating.SelectedItem){[int]$script:C.NodeRating.SelectedItem.Tag}else{0})
  $tags=@($script:C.NodeTags.Text.Split(',')|ForEach-Object{$_.Trim()}|Where-Object{$_})
  $p=Join-Path $script:Root ('jobs\node-meta-'+[guid]::NewGuid().ToString('N')+'.json')
  Write-Json $p @{id=$id;name=$script:C.NodeNameEdit.Text;note=$script:C.NodeNote.Text;tags=$tags;rating=$rating};Start-Work 'NodeMeta' 'NODE' $p
 })
 $script:C.NodeHistory.Add_Click({
  $n=Selected-NodeObject;if(!$n){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return}
  $hist=@($n.history);if(!$hist.Count){$script:C.NodeDetail.Text='برای این نود هنوز تاریخچهٔ تست واقعی وجود ندارد.';return}
  $script:C.NodeDetail.Text=(@($hist|Select-Object -Last 8|ForEach-Object{[string]$_.checked+' · '+$(if($_.healthy){'PASS '+[string]$_.country}else{'FAIL '+[string]$_.error})+' · '+$(if($null -ne $_.seconds){([math]::Round([double]$_.seconds*1000)).ToString()+'ms'}else{'—'})}) -join "`r`n")
 })
 $script:C.NodeCopyLink.Add_Click({$n=Get-RawNodeById (Selected-NodeId);if(!$n){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return};[Windows.Clipboard]::SetText([string]$n.raw);$script:C.NodeDetail.Text='لینک نود فقط در کلیپ‌بورد کپی شد؛ در گزارش FreeNet Hub ذخیره نشد.'})
 $script:C.NodeExportRaw.Add_Click({Export-NodeLinks $false})
 $script:C.NodeExportBase64.Add_Click({Export-NodeLinks $true})
 $script:C.NodeTest.Add_Click({$id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب و «انتخاب نود» را بزنید.';return};Start-Work 'NodeTest' 'NODE'})
 $script:C.NodeConnect.Add_Click({
  $id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب کنید.';return}
  $script:NodeConnectAfterSelect=$true;Start-Work 'NodeSelect' 'NODE' $id
 })
 $script:C.NodeStop.Add_Click({Start-Work 'StopOne' 'NODE'})
 $script:C.NodeSpeed.Add_Click({$id=Selected-NodeId;if(!$id){$script:C.NodeDetail.Text='ابتدا یک نود را انتخاب و «انتخاب» را بزنید.';return};Start-Work 'NodeSpeed' 'NODE'})
 $script:C.NodeBenchmarkBatch.Add_Click({
  if([Windows.MessageBox]::Show('تست Download/Upload همه نودهای قابل‌دسترسی به‌صورت batchهای کوچک انجام می‌شود و مصرف داده دارد. ادامه؟','FreeNet Hub · Benchmark All','YesNo','Question') -ne 'Yes'){return}
  $script:BenchmarkAllActive=$true;$script:NextNodeBenchmark=[DateTime]::UtcNow;Start-Work 'NodeBenchmarkBatch' 'NODE'
 })

 $script:DirectDpiStatePath=Join-Path $env:ProgramData 'FreeNetHub\directdpi\state.json'

 function Get-DirectDpiStatus{
  $state=$null
  try{$state=Read-Json $script:DirectDpiStatePath}catch{}
  if(!$state){return @{active=$false;phase='OFF';pid=0;stale=$false;dns=$false}}
  $pidValue=0
  try{$pidValue=[int]$state.pid}catch{}
  $winwsAlive=$false
  if($pidValue -gt 0){$winwsAlive=[bool](Get-Process -Id $pidValue -ErrorAction SilentlyContinue)}
  $dnsAlive=$false
  try{$dnsAlive=$false; if($state -and $state.ctrldPid){ $cp=Get-Process -Id ([int]$state.ctrldPid) -ErrorAction SilentlyContinue; $dnsAlive=[bool]($cp -and $cp.Path -and $cp.Path.StartsWith((Join-Path $PSScriptRoot 'directdns'),[StringComparison]::OrdinalIgnoreCase)) }}catch{}
  $active=($winwsAlive -and $dnsAlive -and [string]$state.phase -eq 'ACTIVE')
  return @{active=$active;phase=[string]$state.phase;pid=$pidValue;stale=(-not $active);dns=$dnsAlive}
 }

 function Paint-DirectDpiStatus{
  if(!$script:C.ContainsKey('DirectDpiStatus')){return}
  $s=Get-DirectDpiStatus
  if($s.active){
   $script:C.DirectDpiStatus.Text='Direct DPI: فعال — ULA + DoH + DPI، بدون VPN/Proxy'
   $script:C.DirectDpiStart.IsEnabled=$false
   $script:C.DirectDpiStop.IsEnabled=$true
  }elseif($s.stale){
   $script:C.DirectDpiStatus.Text='Direct DPI: state قدیمی — Start آن را rollback و بازسازی می‌کند'
   $script:C.DirectDpiStart.IsEnabled=$true
   $script:C.DirectDpiStop.IsEnabled=$true
  }else{
   $script:C.DirectDpiStatus.Text='Direct DPI: خاموش'
   $script:C.DirectDpiStart.IsEnabled=$true
   $script:C.DirectDpiStop.IsEnabled=$false
  }
 }

 function Invoke-DirectDpi([ValidateSet('Start','Stop')][string]$Action){
  $name=$(if($Action -eq 'Start'){'Start-DirectDpi.ps1'}else{'Stop-DirectDpi.ps1'})
  $file=Join-Path $PSScriptRoot ('directdpi\'+$name)
  if(!(Test-Path -LiteralPath $file)){
   $script:C.StatusTitle.Text='Direct DPI در این build موجود نیست'
   $script:C.StatusDetail.Text=$file
   return
  }
  try{
   $pwsh=(Get-Command pwsh.exe -ErrorAction Stop).Source
   $script:C.StatusTitle.Text=$(if($Action -eq 'Start'){'در حال فعال‌سازی Direct DPI…'}else{'در حال خاموش‌کردن Direct DPI…'})
   $script:C.StatusDetail.Text='Windows UAC فقط برای DNS/WinDivert همین قابلیت لازم است؛ VPN/Proxy یا route تونلی ساخته نمی‌شود.'
   $arg='-NoProfile -ExecutionPolicy Bypass -File "'+$file+'"'
   $p=Start-Process -FilePath $pwsh -Verb RunAs -ArgumentList $arg -Wait -PassThru
   Paint-DirectDpiStatus
   $s=Get-DirectDpiStatus
   if($Action -eq 'Start' -and $p.ExitCode -eq 0 -and $s.active){
    $script:C.StatusTitle.Text='Direct DPI فعال شد'
    $script:C.StatusDetail.Text='DNS امن و bypass محدود مقصدهای فیلترشده فعال است؛ مسیر پیش‌فرض سیستم تغییر نکرده.'
    $script:C.SidebarState.Text='Direct DPI / no VPN'
   }elseif($Action -eq 'Stop' -and $p.ExitCode -eq 0 -and -not $s.active){
    $script:C.StatusTitle.Text='Direct DPI خاموش شد'
    $script:C.StatusDetail.Text='DNS prestate و WinDivert متعلق به FreeNetHub rollback شدند.'
    $script:C.SidebarState.Text='Direct'
   }else{
    $script:C.StatusTitle.Text='Direct DPI به PASS نرسید'
    $script:C.StatusDetail.Text='Exit '+[string]$p.ExitCode+'؛ state/evidence برای علت دقیق حفظ شده است.'
   }
  }catch{
   Paint-DirectDpiStatus
   $script:C.StatusTitle.Text='Direct DPI اجرا نشد'
   $script:C.StatusDetail.Text=$_.Exception.Message
  }
 }

 $script:C.BrowserConnectCard.Add_Click({Select-ConnectionScope 'BROWSER'})
 $script:C.FullSystemConnectCard.Add_Click({Select-ConnectionScope 'SYSTEM'})
 $script:C.ConsoleConnectCard.Add_Click({Select-ConnectionScope 'CONSOLE'})
 if($script:C.ContainsKey('MethodsScopeBrowser')){$script:C.MethodsScopeBrowser.Add_Click({Select-ConnectionScope 'BROWSER'})}
 if($script:C.ContainsKey('MethodsScopeSystem')){$script:C.MethodsScopeSystem.Add_Click({Select-ConnectionScope 'SYSTEM'})}
 if($script:C.ContainsKey('MethodsScopeConsole')){$script:C.MethodsScopeConsole.Add_Click({Select-ConnectionScope 'CONSOLE'})}
 if($script:C.ContainsKey('MainPingTest')){$script:C.MainPingTest.Add_Click({Start-ConfiguredTest $true})}
 if($script:C.ContainsKey('ToolsApplyWarpSystem')){$script:C.ToolsApplyWarpSystem.Add_Click({Select-ConnectionScope 'SYSTEM';Connect-MethodCard 'WARP'})}
 if($script:C.ContainsKey('ToolsApplyNodeSystem')){$script:C.ToolsApplyNodeSystem.Add_Click({Select-ConnectionScope 'SYSTEM';Connect-MethodCard 'NODE'})}
 if($script:C.ContainsKey('ToolsUpdateRootPath')){$script:C.ToolsUpdateRootPath.IsChecked=$true;$script:C.ToolsUpdateRootPath.IsEnabled=$false;$script:C.ToolsUpdateRootPath.ToolTip='آپدیت و دریافت نودها همیشه از مسیر پایهٔ سیستم انجام می‌شود.'}
 if($script:C.ContainsKey('ShowIpDashboard')){$script:C.ShowIpDashboard.Add_Click({$script:C.ShowIp.IsChecked=$script:C.ShowIpDashboard.IsChecked;$script:Settings.showIp=[bool]$script:C.ShowIp.IsChecked;Paint-Health})}
 if($script:C.ContainsKey('MethodsRetestAll')){$script:C.MethodsRetestAll.Add_Click({
   if($script:Task -or $script:GatewayTask){return}
   $script:MethodBenchQueue=$(if($script:ConnectionScope -eq 'SYSTEM'){@('WARP','NODE')}elseif($script:ConnectionScope -eq 'CONSOLE'){@('CONSOLE')}else{@('AUTO','NODE','WARP','CFON','TOR','CUSTOM','GOOL','DIRECT')})
   $script:C.StatusTitle.Text='تست همه روش‌ها شروع شد'
   $next=$script:MethodBenchQueue[0];$script:MethodBenchQueue=@($script:MethodBenchQueue|Select-Object -Skip 1)
   if($next -eq 'CONSOLE'){Start-Work 'ConsolePreflight' 'CONSOLE'}else{Start-ProviderBenchmark $next}
 })}
 if($script:C.ContainsKey('ToolsTestBasePath')){$script:C.ToolsTestBasePath.Add_Click({$script:Settings.testPathMode='BASE';Paint-TestSettings;Write-Json (Join-Path $script:Root 'settings.json') $script:Settings})}
 if($script:C.ContainsKey('ToolsTestSelectedPath')){$script:C.ToolsTestSelectedPath.Add_Click({$script:Settings.testPathMode='SELECTED';Paint-TestSettings;Write-Json (Join-Path $script:Root 'settings.json') $script:Settings})}
 if($script:C.ContainsKey('PingTimeoutBox')){$script:C.PingTimeoutBox.Add_SelectionChanged({if($script:C.PingTimeoutBox.SelectedItem){$script:Settings.pingTimeoutSec=[int]$script:C.PingTimeoutBox.SelectedItem.Content;Write-Json (Join-Path $script:Root 'settings.json') $script:Settings}})}
 if($script:C.ContainsKey('DownloadTimeoutBox')){$script:C.DownloadTimeoutBox.Add_SelectionChanged({if($script:C.DownloadTimeoutBox.SelectedItem){$script:Settings.downloadTimeoutSec=[int]$script:C.DownloadTimeoutBox.SelectedItem.Content;Write-Json (Join-Path $script:Root 'settings.json') $script:Settings}})}
 if($script:C.ContainsKey('UploadTimeoutBox')){$script:C.UploadTimeoutBox.Add_SelectionChanged({if($script:C.UploadTimeoutBox.SelectedItem){$script:Settings.uploadTimeoutSec=[int]$script:C.UploadTimeoutBox.SelectedItem.Content;Write-Json (Join-Path $script:Root 'settings.json') $script:Settings}})}
 $script:C.ConsoleOpenCard.Add_Click({$script:C.Tabs.SelectedIndex=3})
 $script:C.ConsoleSpeed.Add_Click({Start-Work 'ConsoleSpeed' 'CONSOLE'})
 $script:C.CurrentPathSpeed.Add_Click({if($script:FullSystemActive){$p=$(if($script:DesiredMode -in @('NODE','WARP')){$script:DesiredMode}else{'WARP'});Start-Work 'SystemSpeed' $p}elseif($script:CurrentMode){Start-Work 'PathSpeed' $script:CurrentMode}else{Start-Work 'Speed' 'DIRECT'}})
 $script:C.MainMethodSmart.Add_Click({Select-ModeTag 'AUTO';Paint-ConnectionSelection})
 $script:C.MainMethodNode.Add_Click({Select-ModeTag 'NODE';Paint-ConnectionSelection})
 $script:C.MainMethodWarp.Add_Click({Select-ModeTag 'WARP';Paint-ConnectionSelection})
 $script:C.MainMethodCfon.Add_Click({Select-ModeTag 'CFON';Paint-ConnectionSelection})
 $script:C.MainMethodTor.Add_Click({Select-ModeTag 'TOR';Paint-ConnectionSelection})
 $script:C.MainMethodCustom.Add_Click({Select-ModeTag 'CUSTOM';Paint-ConnectionSelection})
 $script:C.MainMethodDirect.Add_Click({Select-ModeTag 'DIRECT';Paint-ConnectionSelection})
 $script:C.AdvancedMethodsOpen.Add_Click({$script:C.Tabs.SelectedIndex=1})
 $script:C.MainTest.Add_Click({Start-ConfiguredTest $false})
 $script:C.MainConnect.Add_Click({
  if($script:ConnectionScope -eq 'CONSOLE'){Start-GatewayRequest 'StartConsole';return}
  Start-ProviderConnect (Selected)
 })

 $script:C.ConnectSmart.Add_Click({Connect-MethodCard 'AUTO'});$script:C.TestSmart.Add_Click({Start-ProviderBenchmark 'AUTO'})
 $script:C.ConnectNode.Add_Click({Connect-MethodCard 'NODE'});$script:C.TestNodePath.Add_Click({Start-ProviderBenchmark 'NODE'})
 $script:C.ConnectWarp.Add_Click({Connect-MethodCard 'WARP'});$script:C.TestWarpPath.Add_Click({Start-ProviderBenchmark 'WARP'})
 $script:C.ConnectCfon.Add_Click({Connect-MethodCard 'CFON'});$script:C.TestCfonPath.Add_Click({Start-ProviderBenchmark 'CFON'})
 $script:C.ConnectTor.Add_Click({Connect-MethodCard 'TOR'});$script:C.TestTorPath.Add_Click({Start-ProviderBenchmark 'TOR'})
 $script:C.ConnectCustom.Add_Click({Connect-MethodCard 'CUSTOM'});$script:C.TestCustomPath.Add_Click({Start-ProviderBenchmark 'CUSTOM'})
 $script:C.ConnectGool.Add_Click({Connect-MethodCard 'GOOL'});$script:C.TestGoolPath.Add_Click({Start-ProviderBenchmark 'GOOL'})
 $script:C.ConnectDirect.Add_Click({Connect-MethodCard 'DIRECT'});$script:C.TestDirectPath.Add_Click({Start-ProviderBenchmark 'DIRECT'})
$script:C.BridgeWebTest.Add_Click({Start-ProviderBenchmark 'WEBTUNNEL'});$script:C.BridgeWebConnect.Add_Click({Start-ProviderConnect 'WEBTUNNEL'})
$script:C.BridgeObfsTest.Add_Click({Start-ProviderBenchmark 'OBFS4'});$script:C.BridgeObfsConnect.Add_Click({Start-ProviderConnect 'OBFS4'})
 $script:C.ToolsNodeRefresh.Add_Click({Start-Work 'NodeRefreshSmart' 'NODE'})

 $script:C.Browser.Add_Click({if($script:FullSystemActive){Start-Work 'Browser' 'DIRECT';return};if(!$script:CurrentMode){$script:C.StatusTitle.Text='مرورگر باز نشد';$script:C.StatusDetail.Text=Friendly-Error 'CONNECT_FIRST';return};Start-Work 'Browser' $script:CurrentMode})

 $script:C.QuickStop.Add_Click({if($script:FullSystemActive){if([Windows.MessageBox]::Show('تونل کل سیستم متعلق به FreeNetHub خاموش و rollback شود؟','توقف محدود','YesNo','Question') -eq 'Yes'){Start-GatewayRequest 'Stop'};return};if([Windows.MessageBox]::Show('فقط مسیرهای مرورگر متعلق به FreeNet Hub متوقف شوند؟ سایر VPNها و Chrome شخصی تغییر نمی‌کنند.','توقف محدود','YesNo','Question') -eq 'Yes'){Start-Work 'Stop'}})

 $script:C.Cancel.Add_Click({Cancel-Work})

 $script:C.Scan.Add_Click({Start-Work 'Scan'})

 $script:C.Inventory.Add_Click({Start-Work 'Inventory'})

 $script:C.Doctor.Add_Click({Start-Work 'Doctor'})
 $script:C.DirectNetworkAudit.Add_Click({Start-Work 'DirectNetworkAudit' 'DIRECT'})
 $script:C.DirectDpiStart.Add_Click({Invoke-DirectDpi 'Start'})
 $script:C.DirectDpiStop.Add_Click({Invoke-DirectDpi 'Stop'})
 Paint-DirectDpiStatus

 $script:C.Speed.Add_Click({Start-Work 'Speed' 'DIRECT'})

 $script:C.Updates.Add_Click({Start-Work 'UpdateCheck'})
 $script:C.UpdateCheckMain.Add_Click({Start-Work 'UpdateCheck'})
 $script:C.UpdateInstallMain.Add_Click({Start-Work 'UpdateDownload'})
 $script:C.UpdateDownload.Add_Click({Start-Work 'UpdateDownload'})

 $script:C.Export.Add_Click({Start-Work 'Export'})

 $script:C.ShowIp.Add_Click({Paint-Health;if($script:Last){$script:C.Details.Text=(Sanitize $script:Last)|ConvertTo-Json -Depth 15}})

 $script:C.Search.Add_TextChanged({Research-Show})

 $script:C.Theme.Add_Click({Theme-Apply $(if($script:Settings.theme -eq 'dark'){'light'}else{'dark'});Paint-ConnectionSelection})

 $script:C.Help.Add_Click({Open-Doc 'HELP_FA.txt'})

 $script:C.BridgeHelp.Add_Click({Open-Doc 'BRIDGES_FA.txt'})

 $script:C.AdvancedHelp.Add_Click({Open-Doc 'ADVANCED_FA.txt'})

 $script:C.Copy.Add_Click({[Windows.Clipboard]::SetText($script:C.Details.Text)})

 $script:C.Logs.Add_Click({$p=[Diagnostics.ProcessStartInfo]::new();$p.FileName='explorer.exe';$p.UseShellExecute=$false;[void]$p.ArgumentList.Add((Join-Path $script:Root 'evidence'));[void][Diagnostics.Process]::Start($p)})

 foreach($n in @('ImportWeb','ImportObfs')){$script:C[$n].Tag=if($n -eq 'ImportWeb'){'WEBTUNNEL'}else{'OBFS4'};$script:C[$n].Add_Click({param($sender,$event)$d=[Microsoft.Win32.OpenFileDialog]::new();$d.Filter='Text files (*.txt)|*.txt';if($d.ShowDialog($script:Window)){Start-Work 'Import' ([string]$sender.Tag) $d.FileName}})}
 foreach($n in @('ImportWebClipboard','ImportObfsClipboard')){
  $script:C[$n].Tag=if($n -eq 'ImportWebClipboard'){'WEBTUNNEL'}else{'OBFS4'}
  $script:C[$n].Add_Click({
   param($sender,$event)
   try{$txt=[Windows.Clipboard]::GetText()}catch{$txt=''}
   if([string]::IsNullOrWhiteSpace($txt)){$script:C.BridgeStatus.Text='Clipboard bridge text is empty.';return}
   $p=Join-Path $script:Root ('jobs\bridge-import-'+[guid]::NewGuid().ToString('N')+'.txt')
   [IO.File]::WriteAllText($p,$txt,[Text.UTF8Encoding]::new($false))
   Start-Work 'Import' ([string]$sender.Tag) $p
  })
 }

 $script:C.Save.Add_Click({$script:Settings.country=[string]$script:C.Country.SelectedItem.Content;$script:Settings.home=$script:C.Home.Text;$script:Settings.localProxy=$script:C.CustomProxy.Text;$script:Settings.monitor=[bool]$script:C.Monitor.IsChecked;$script:Settings.autoRepair=[bool]$script:C.AutoRepair.IsChecked;$script:Settings.showIp=[bool]$script:C.ShowIp.IsChecked;$script:Settings.minimizeToTray=[bool]$script:C.TrayOption.IsChecked;$p=Join-Path $script:Root 'jobs\settings-request.json';Write-Json $p $script:Settings;Start-Work 'Settings' 'AUTO' $p})

 if(!$script:ShellHosted){

  $script:Tray=[Windows.Forms.NotifyIcon]::new();if(Test-Path -LiteralPath $icoPath){$script:AppIcon=[Drawing.Icon]::new($icoPath);$script:Tray.Icon=$script:AppIcon}else{$script:Tray.Icon=[Drawing.SystemIcons]::Application};$script:Tray.Text='FreeNet Hub — browser routes';$script:Tray.Visible=$false

  $menu=[Windows.Forms.ContextMenuStrip]::new();$show=$menu.Items.Add('Open FreeNet Hub');$show.add_Click({$script:Window.Show();$script:Window.WindowState='Normal';[void]$script:Window.Activate();$script:Tray.Visible=$false})

  $exit=$menu.Items.Add('Close panel (leave tunnel unchanged)');$exit.add_Click({$script:AllowClose=$true;$script:Window.Close()});$script:Tray.ContextMenuStrip=$menu

  $script:Tray.Add_DoubleClick({$script:Window.Show();$script:Window.WindowState='Normal';[void]$script:Window.Activate();$script:Tray.Visible=$false})

  $script:Window.Add_StateChanged({if($script:Window.WindowState -eq 'Minimized' -and $script:C.TrayOption.IsChecked){$script:Tray.Visible=$true;$script:Window.Hide()}})

 }

 $script:Window.Add_Closing({param($s,$e)if(!$Smoke -and $script:ShellHosted -and !$script:AllowClose){$e.Cancel=$true;$script:Window.WindowState='Minimized';return};if($script:GatewayTask){$e.Cancel=$true;$script:C.GatewayDetail.Text='عملیات Gateway هنوز در حال اجراست؛ پس از پایان دوباره ببندید.';return};if($script:Task){$e.Cancel=$true;Cancel-Work;return};if(!$Smoke -and !$script:AllowClose -and ($script:CurrentMode -or $script:FullSystemActive)){$a=[Windows.MessageBox]::Show('بستن پنل، تونل را قطع نمی‌کند و پایش متوقف می‌شود. پنل بسته شود؟ برای حفظ پایش، Cancel و سپس Minimize را بزنید.','FreeNet Hub','OKCancel','Information');if($a -ne 'OK'){$e.Cancel=$true}}})

 $script:Timer=[Windows.Threading.DispatcherTimer]::new();$script:Timer.Interval=[TimeSpan]::FromMilliseconds(400);$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45);$script:NextNodeRefresh=[DateTime]::UtcNow;$script:NextNodeBenchmark=[DateTime]::UtcNow.AddMinutes(1);$script:BenchmarkAllActive=$false

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

     elseif($r.exit -ne 0){
      $err=$(if($r.result.ContainsKey('error')){[string]$r.result.error}else{'UNKNOWN_ERROR'})
      $script:C.StatusTitle.Text=if($r.exit -eq 20){'عملیات لغو شد'}elseif($r.exit -eq 124){'مهلت زمانی تمام شد'}else{'عملیات انجام نشد'}
      $script:C.StatusDetail.Text=Friendly-Error $err $r.result;$script:C.SidebarState.Text='نیاز به بررسی'
      $failMode=$(switch([string]$r.action){
       'Speed'{'DIRECT'};'ProviderBenchmark'{[string]$r.mode};'ProviderPing'{[string]$r.mode};'PathSpeed'{[string]$r.mode};'SystemSpeed'{[string]$r.mode};
       'NodeSpeed'{'NODE'};'NodeSystemPreflight'{'NODE'};'NodeSystemPreflightAuto'{'NODE'};default{''}
      })
      if($failMode){Paint-TestState $failMode $(if($r.exit -eq 124){'TIMEOUT'}else{'FAIL'}) $err}
     }

     else{

      $script:C.StatusTitle.Text='عملیات انجام شد';$script:C.StatusDetail.Text='تغییر فقط در محدودهٔ اعلام‌شده انجام شد؛ برای نتیجهٔ شبکه از دکمه بررسی استفاده کنید.'

      if($r.action -eq 'Stop'){$script:CurrentMode='';$script:DesiredMode='';$script:Health=$null;$script:C.SidebarState.Text='بدون اتصال'}
      if($r.action -eq 'StopOne' -and $script:CurrentMode -eq 'NODE'){$script:CurrentMode='';$script:DesiredMode='';$script:Health=$null;$script:C.SidebarState.Text='Node قطع شد'}
      if([string]$r.action -like 'Node*'){Paint-Nodes $r.result}
      if($r.action -eq 'NodeSelect' -and $script:NodeConnectAfterSelect){
       $script:NodeConnectAfterSelect=$false;Select-ModeTag 'NODE';Select-ConnectionScope 'BROWSER';$script:C.Tabs.SelectedIndex=0
       $script:C.StatusTitle.Text='Node انتخاب شد';$script:C.StatusDetail.Text='اکنون در صفحهٔ اتصال، ابتدا تست بگیر و سپس «اتصال با روش انتخاب‌شده» را بزن.'
      }

      if($r.action -eq 'ProviderBenchmark'){
       if($r.mode -eq 'AUTO'){
        foreach($row in @($r.result.results)){
         $m=[string]$row.provider
         if($row.performance){
          Paint-Performance $row.performance $m $false
          if($m -eq 'NODE' -and $row.node -and $script:C.ContainsKey('NodeMetric')){$script:C.NodeMetric.Text=$script:C.NodeMetric.Text+' • Best node: '+[string]$row.node.name}
         }else{Paint-TestState $m 'FAIL' ([string]$row.error) $false}
        }
        $best=[string]$r.result.provider
        if($best -and $r.result.performance){
         Paint-Performance $r.result.performance $best $true
         $script:C.SmartMetric.Text='Best → '+$best
         if($script:C.ContainsKey('CompareSmart')){$script:C.CompareSmart.Text='Selector only • Best → '+$best+' • '+[string]::Join(' → ',@($r.result.rank))}
         if($script:C.ContainsKey('TestMethodValue')){$script:C.TestMethodValue.Text='Smart → '+$best}
         $script:C.StatusTitle.Text='Smart بهترین روش را انتخاب کرد: '+$best
        }else{
         $script:C.SmartMetric.Text='هیچ روش موفقی پیدا نشد'
         if($script:C.ContainsKey('CompareSmart')){$script:C.CompareSmart.Text='Selector only • no successful provider'}
         Paint-TestState 'AUTO' 'FAIL' 'ALL_SMART_PATHS_FAILED'
        }
       }else{
        $pm=$(if($r.result.provider){[string]$r.result.provider}else{[string]$r.mode})
        Paint-Performance $r.result.performance $pm
        if($pm -eq 'NODE' -and $r.result.node -and $script:C.ContainsKey('NodeMetric')){$script:C.NodeMetric.Text=$script:C.NodeMetric.Text+' • Best node: '+[string]$r.result.node.name}
       }
      }
      if($r.action -eq 'ProviderPing'){
       if($r.mode -eq 'AUTO'){
        foreach($row in @($r.result.results)){
         $m=[string]$row.provider
         if($row.performance){
          $perf=$row.performance;$ping=Format-Metric $perf.pingMs 'ms';$dashPrefix=Get-DashPrefix $m
          if($dashPrefix){$n=$dashPrefix+'Ping';if($script:C.ContainsKey($n)){$script:C[$n].Text=$ping};$n=$dashPrefix+'State';if($script:C.ContainsKey($n)){$script:C[$n].Text=$(if($perf.ok){'PASS'}else{'FAIL'})}}
         }else{Paint-TestState $m 'FAIL' ([string]$row.error) $false}
        }
        $best=[string]$r.result.provider;$perf=$r.result.performance
        if($best -and $perf){
         $ping=Format-Metric $perf.pingMs 'ms';$country=$(if($perf.country){[string]$perf.country}else{'?'})
         $script:C.MetricPing.Text=$ping;$script:C.MetricCountry.Text=$country;$script:C.MetricFreshness.Text='آخرین Ping: '+[DateTimeOffset]::UtcNow.ToString('o')
         $script:C.SmartMetric.Text='Best Ping → '+$best+' • '+$ping
         $script:C.StatusTitle.Text='Smart کم‌تاخیرترین روش موفق را پیدا کرد: '+$best;$script:C.StatusDetail.Text='Ping '+$ping+' • Country '+$country
        }else{Paint-TestState 'AUTO' 'FAIL' 'ALL_SMART_PATHS_FAILED'}
       }else{
        $pm=$(if($r.result.provider){[string]$r.result.provider}else{[string]$r.mode})
        $perf=$r.result.performance;$ping=Format-Metric $perf.pingMs 'ms';$country=$(if($perf.country){[string]$perf.country}else{'?'})
        $script:C.MetricPing.Text=$ping;$script:C.MetricCountry.Text=$country;$script:C.MetricFreshness.Text='آخرین Ping: '+[DateTimeOffset]::UtcNow.ToString('o')
        $script:C.StatusTitle.Text=$(if($perf.ok){'Ping مسیر موفق بود'}else{'Ping مسیر ناموفق بود'})
        $script:C.StatusDetail.Text=$pm+' • Ping '+$ping+' • Country '+$country
        $dashPrefix=Get-DashPrefix $pm
        if($dashPrefix){$n=$dashPrefix+'Ping';if($script:C.ContainsKey($n)){$script:C[$n].Text=$ping}}
       }
      }
      if($r.action -eq 'PathSpeed'){
       Paint-Performance $r.result $(if($r.result.mode){[string]$r.result.mode}else{$script:CurrentMode})
      }
      if($r.action -eq 'SystemSpeed'){
       $sp=$(if($r.result.provider){[string]$r.result.provider}else{$r.mode});Paint-Performance $r.result $sp;$script:C.StatusDetail.Text='Full System · '+$sp+' · '+$script:C.StatusDetail.Text
      }
      if($r.action -eq 'NodeSystemPreflight'){
       Paint-Performance $r.result 'NODE'
       if($r.result.systemEligible){
        $script:C.StatusTitle.Text='Node برای Full System قابل استفاده است'
        $script:C.StatusDetail.Text='HTTPS و UDP با همان Node تأیید شدند · TCP '+[string]$r.result.country+' · UDP '+[string]$r.result.udpCountry+$(if($r.result.ok){' · تست سرعت کامل شد'}else{' · نمونهٔ سرعت ناقص؛ Down/Up = N/A'})
       }
      }
      if($r.action -eq 'ConsoleSpeed'){
       Paint-Performance $r.result 'CONSOLE';$script:C.StatusDetail.Text='Console Provider · '+$script:C.StatusDetail.Text
      }
      if($r.action -eq 'ConsolePreflight'){
       Paint-Performance $r.result 'CONSOLE';$script:C.StatusDetail.Text='تست قبل از اتصال کنسول · '+$script:C.StatusDetail.Text
      }
      if($r.action -eq 'NodeSpeed'){
       Paint-Nodes $r.result
       Start-Work 'NodeList' 'NODE'
      }
      if($r.action -eq 'NodeBenchmarkBatch'){
       Paint-Nodes $r.result;$remaining=[int]$r.result.remainingUnbenchmarked
       if($script:BenchmarkAllActive -and $remaining -gt 0){
        $script:C.StatusTitle.Text='Benchmark همه نودها در حال ادامه است'
        $script:C.StatusDetail.Text=[string]$r.result.benchmarked+' نود این batch تست شدند · PASS '+[string]$r.result.passed+' · N/A '+[string]$r.result.failed+' · '+[string]$remaining+' نود eligible باقی مانده.'
        $script:NextNodeBenchmark=[DateTime]::UtcNow.AddSeconds(2)
       }else{
        $script:BenchmarkAllActive=$false;$script:C.StatusTitle.Text='Benchmark نودها کامل شد'
        $best=$r.result.best
        $bestText=$(if($best -and $best.performance){' · بهترین: '+[string]$best.node.name+' · '+(Format-Metric $best.performance.pingMs 'ms')+' · ↓ '+(Format-Metric $best.performance.downloadMbps 'Mbps')+' · ↑ '+(Format-Metric $best.performance.uploadMbps 'Mbps')}else{' · بهترین full-health: پیدا نشد'})
        $script:C.StatusDetail.Text=[string]$r.result.benchmarked+' نود این batch به‌روزرسانی شدند · PASS '+[string]$r.result.passed+' · N/A '+[string]$r.result.failed+' · باقی‌مانده: '+[string]$remaining+$bestText
        $script:NextNodeBenchmark=[DateTime]::UtcNow.AddMinutes(10)
       }
      }
      if($r.action -eq 'NodeRefreshPublic'){
       $script:NextNodeRefresh=[DateTime]::UtcNow.AddMinutes(30);$script:NextNodeBenchmark=[DateTime]::UtcNow.AddSeconds(3)
      }
      if($r.action -eq 'UpdateCheck'){
       $a=$r.result.asset
       if($a){
        $script:C.UpdateStatus.Text='GitHub: '+[string]$r.result.tag+' · '+[string]$a.name+' · '+$(if($r.result.updateAvailable){'نسخه جدیدتر موجود است'}else{'نسخه جدیدتر نیست'})
        $script:C.UpdateDownload.Visibility=$(if($r.result.updateAvailable){'Visible'}else{'Collapsed'})
        $script:C.UpdateInstallMain.IsEnabled=[bool]$r.result.updateAvailable
       }else{$script:C.UpdateStatus.Text='Release پیدا شد ولی installer asset موجود نیست.';$script:C.UpdateInstallMain.IsEnabled=$false}
      }
      if($r.action -eq 'UpdateDownload'){
       $script:C.UpdateStatus.Text='دانلود و SHA-256 تأیید شد: '+[string]$r.result.sha256
       Install-VerifiedUpdate ([string]$r.result.installer)
      }

      if($r.action -eq 'DirectNetworkAudit'){
       $nat=[string]$r.result.nat.natClassification
       $udp=$(if($r.result.nat.udpTraversalCandidate){'UDP traversal candidate: PASS'}else{'UDP traversal candidate: UNPROVEN'})
       $v6=$(if($null -ne $r.result.adapter.ipv6BindingEnabled -and -not [bool]$r.result.adapter.ipv6BindingEnabled){'IPv6: locally disabled'}elseif([int]$r.result.adapter.ipv6DefaultRoutes -gt 0){'IPv6: available'}else{'IPv6: no upstream route'})
       $script:C.StatusTitle.Text=$(if($r.result.nat.cgnatConfirmed){'CGNAT تأیید شد؛ مسیر مستقیم تحلیل شد'}else{'ممیزی مسیر مستقیم انجام شد'})
       $script:C.StatusDetail.Text=$nat+' · '+$udp+' · '+$v6+' · هیچ VPN/Proxy یا تغییر شبکه‌ای اعمال نشد.'
       $script:C.SidebarState.Text='Direct / CGNAT audit'
      }

      if($r.action -eq 'Speed'){
       Paint-Performance $r.result 'DIRECT'
       if($SmokePreconnect){
        $smokeOut=$(if($SmokeEvidencePath){$SmokeEvidencePath}else{Join-Path $script:Root 'evidence\r46_preconnect_ui.json'})
        Write-Json $smokeOut @{schema=1;utc=[DateTime]::UtcNow.ToString('o');action='Speed';exit=[int]$r.exit;rendered=@{ping=[string]$script:C.MetricPing.Text;download=[string]$script:C.MetricDownload.Text;upload=[string]$script:C.MetricUpload.Text;freshness=[string]$script:C.MetricFreshness.Text};backend=@{pingMs=$r.result.pingMs;downloadMbps=$r.result.downloadMbps;uploadMbps=$r.result.uploadMbps;routeProof=[string]$r.result.defaultRoute.routeProof};networkMutation=$false}
       }
       $script:C.StatusTitle.Text=$(if($r.result.ok){'تست سرعت مستقیم کامل شد'}else{'تست سرعت مستقیم ناقص بود'})
       $script:C.StatusDetail.Text='اینترنت مستقیم · دانلود '+[string]$r.result.downloadMbps+' Mbps · آپلود '+[string]$r.result.uploadMbps+' Mbps · Ping '+$(if($null -ne $r.result.pingMs){[string]$r.result.pingMs+' ms'}else{'نامشخص'})+' · مسیر '+[string]$r.result.defaultRoute.adapterName
       $script:C.SidebarState.Text='Speed · DIRECT'
      }

      if($r.action -eq 'Scan'){$script:C.ScanSummary.Text='ترتیب پیشنهادی فعلی: '+($r.result.rank -join ' ← ')}

      if($r.action -eq 'Inventory'){

       $script:C.BridgeStatus.Text=($r.result.providers|Where-Object{$_.mode -in @('WEBTUNNEL','OBFS4')}|ForEach-Object{$_.mode+': '+$_.state}) -join [Environment]::NewLine

       $running=@($r.result.providers|Where-Object{$_.state -in @('CONNECTED_NOT_VERIFIED','STARTING_OR_UNREADY')})

       if($running.Count -eq 1){$script:CurrentMode=[string]$running[0].mode;$script:DesiredMode=$script:CurrentMode;$script:C.StatusTitle.Text='مسیر فعال شناسایی شد';$script:C.StatusDetail.Text=$script:CurrentMode+' فعال است؛ برای شاهد HTTPS تازه «بررسی مسیر انتخاب‌شده» را بزنید.';$script:C.SidebarState.Text='فعال / تأیید نشده'}

       elseif($running.Count -gt 1){$script:CurrentMode='';$script:C.StatusTitle.Text='چند مسیر فعال شناسایی شد';$script:C.StatusDetail.Text='برای جلوگیری از ابهام، مسیر موردنظر را انتخاب و وضعیت را بررسی کنید.';$script:C.SidebarState.Text='نیاز به بررسی'}

       elseif(!$script:Health){$script:CurrentMode='';$script:C.StatusTitle.Text='آماده برای اتصال';$script:C.StatusDetail.Text='هیچ مسیر مدیریت‌شده‌ای فعال نیست. مسیر را انتخاب و «شروع اتصال» را بزنید.';$script:C.SidebarState.Text='بدون اتصال'}

      }
      if($r.action -eq 'Inventory' -and !$Smoke){Start-Work 'NodeRefreshSmart' 'NODE'}

     }

     if($r.action -eq 'ProviderBenchmark' -and $script:MethodBenchQueue -and @($script:MethodBenchQueue).Count -gt 0){
      $next=$script:MethodBenchQueue[0];$script:MethodBenchQueue=@($script:MethodBenchQueue|Select-Object -Skip 1)
      if($next -eq 'CONSOLE'){Start-Work 'ConsolePreflight' 'CONSOLE'}else{Start-ProviderBenchmark $next}
     }
     Set-Busy;$script:NextCheck=[DateTime]::UtcNow.AddSeconds(45);$script:C.Elapsed.Text='عملیات پایان یافت؛ اتصال کل سیستم تغییر نکرد.'

    }

   }else{

    if($script:Tick % 25 -eq 0){Paint-Health}

    if(!$Smoke -and !$script:Task -and !$script:GatewayTask -and !$script:StartupUpdateChecked -and [DateTime]::UtcNow -ge $script:StartupUpdateDue){
     $script:StartupUpdateChecked=$true
     Start-Work 'UpdateCheck'
    }
    elseif(!$Smoke -and !$script:Task -and !$script:GatewayTask -and $script:C.Tabs.SelectedIndex -eq 2){
     if([DateTime]::UtcNow -ge $script:NextNodeRefresh){Start-Work 'NodeRefreshPublic' 'NODE'}
     elseif([DateTime]::UtcNow -ge $script:NextNodeBenchmark){Start-Work 'NodeBenchmarkBatch' 'NODE'}
    }

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

 $script:Window.Add_ContentRendered({
  [void]$script:Window.Activate()
  if($Smoke){
   if($SmokePreconnect){$script:Settings.testPathMode='BASE';Select-ModeTag 'DIRECT';Paint-TestState 'DIRECT' 'RUNNING';Start-Work 'Speed' 'DIRECT'}
   elseif($script:SmokeVerifyMode){Start-Work 'Verify' $script:SmokeVerifyMode}
  }else{
   [void](Gateway-Refresh);Start-Work 'Inventory'
  }
 })

 Set-Busy;$script:Timer.Start();[void]$script:Window.ShowDialog()

}catch{

 $msg=$_.Exception.ToString();[IO.File]::WriteAllText((Join-Path $script:Root 'logs\ui-error.txt'),$msg,[Text.UTF8Encoding]::new($false));try{Add-Type -AssemblyName PresentationFramework;[Windows.MessageBox]::Show($msg,'FreeNet Hub — startup error')|Out-Null}catch{};exit 1

}finally{if($script:Timer){$script:Timer.Stop()};if($script:Tray){$script:Tray.Visible=$false;$script:Tray.Dispose()};if($script:AppIcon){$script:AppIcon.Dispose()};if($script:Lease){$script:Lease.Dispose()}}

