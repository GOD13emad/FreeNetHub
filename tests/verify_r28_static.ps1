$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
function Run-Checked([string]$Exe,[string[]]$ArgumentList){
 & $Exe @ArgumentList
 $ec=$LASTEXITCODE
 if($ec -ne 0){throw ("FAILED "+$Exe+" "+($ArgumentList -join " ")+" exit="+$ec)}
}
# PowerShell AST parse
$tokens=$null;$errs=$null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root 'app\FreeNetHub.ps1'),[ref]$tokens,[ref]$errs)|Out-Null
if($errs.Count){throw ('POWERSHELL_PARSE: '+($errs|ForEach-Object{$_.Message}-join ' | '))}
# Uninstaller PowerShell AST parse
$ut=$null;$ue=$null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root 'Uninstall-FreeNetHub.ps1'),[ref]$ut,[ref]$ue)|Out-Null
if($ue.Count){throw ('UNINSTALL_POWERSHELL_PARSE: '+($ue|ForEach-Object{$_.Message}-join ' | '))}
$uninstall=Get-Content -LiteralPath (Join-Path $Root 'Uninstall-FreeNetHub.ps1') -Raw -Encoding UTF8
foreach($k in @('Get-OwnedEngineJobs','uninstall cancel','ENGINE_JOB_DRAIN_TIMEOUT','Permission denied|BUSY_ANOTHER_JOB')){if(!$uninstall.Contains($k)){throw ('R28_UNINSTALL_RACE_GUARD_'+$k)}}
# XML + WPF parse
[xml]$x=Get-Content -LiteralPath (Join-Path $Root 'app\View.xaml') -Raw -Encoding UTF8
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase
$w=[Windows.Markup.XamlReader]::Parse([IO.File]::ReadAllText((Join-Path $Root 'app\View.xaml')))
if(!$w){throw 'WPF_XAML_PARSE_EMPTY'}
# controller-referenced controls must exist
$ps=Get-Content -LiteralPath (Join-Path $Root 'app\FreeNetHub.ps1') -Raw -Encoding UTF8
$refs=@([regex]::Matches($ps,'\$script:C\.([A-Za-z0-9_]+)')|ForEach-Object{$_.Groups[1].Value}|Sort-Object -Unique|Where-Object{$_ -notin @('ContainsKey','Count')})
$names=@($x.SelectNodes('//*[@Name]')|ForEach-Object{$_.GetAttribute('Name')})
$missing=@($refs|Where-Object{$_ -notin $names})
if($missing.Count){throw ('MISSING_XAML_CONTROLS: '+($missing -join ','))}
Run-Checked 'python' @('-m','py_compile','app\engine.py','app\nodehub.py')
Run-Checked 'pwsh.exe' @('-NoProfile','-File','.\tests\verify_r24_strict.ps1')
$shell=Get-Content -LiteralPath windows\standalone\FreeNetHubShell.cs -Raw -Encoding UTF8
foreach($k in @('psi.UseShellExecute=false','psi.CreateNoWindow=true','psi.WindowStyle=ProcessWindowStyle.Hidden')){if(!$shell.Contains($k)){throw ('R28_WINDOWLESS_SHELL_CONTRACT_'+$k)}}
$engine=Get-Content -LiteralPath app\engine.py -Raw -Encoding UTF8
foreach($k in @('ProviderBenchmark','PathSpeed','SystemSpeed','ConsoleSpeed','UpdateCheck','UpdateDownload','NodeSpeed','NodeBenchmarkBatch','GOD13emad/FreeNetHub')){if(!$engine.Contains($k)){throw ('R28_ENGINE_CONTRACT_'+$k)}}
$view=Get-Content -LiteralPath app\View.xaml -Raw -Encoding UTF8
foreach($k in @('BrowserConnectCard','FullSystemConnectCard','ConsoleConnectCard','MetricPing','MetricDownload','MetricUpload','NodeBenchmarkBatch','NodeSpeed','UpdateCheckMain','UpdateInstallMain','ConsoleSpeed')){if(!$view.Contains('Name="'+$k+'"')){throw ('R28_UI_CONTRACT_'+$k)}}
foreach($h in @('Ping','Download','Upload','Country','Protocol','Source','Last Test')){if(!$view.Contains('Header="'+$h+'"') -and !$view.Contains('Header="کشور"')){if($h -ne 'Country'){throw ('R28_NODE_COLUMN_'+$h)}}}
Write-Output ('R28_STATIC=PASS controls='+$names.Count+' controllerRefs='+$refs.Count)
