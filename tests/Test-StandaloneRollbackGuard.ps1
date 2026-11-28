[CmdletBinding()]
param()
$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest
$script=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\windows\standalone\Rollback-FreeNetHubShell.ps1')).Path
$text=Get-Content -LiteralPath $script -Raw
if($text -match '(?i)\bStop-Process\b'){ throw 'Rollback must never terminate processes by name or force.' }
if($text -notmatch '\bGet-CimInstance\b'){throw 'Expected exact target process guard.'}
$csc=@("$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe","$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe")|Where-Object{Test-Path -LiteralPath $_}|Select-Object -First 1
if(-not $csc){throw '.NET Framework CSC is required on Windows.'}
$workspace=Join-Path ([IO.Path]::GetTempPath()) ('fnh-rollback-test-'+[Guid]::NewGuid().ToString('N'))
$root=Join-Path $workspace 'target'
$foreign=Join-Path $workspace 'unrelated'
$bak=Join-Path $root 'backup\shell-v42-20261128-010203'
$outside=Join-Path $workspace 'external-backup'
$appdata=Join-Path $workspace 'appdata'
$oldAppdata=$env:APPDATA
$own=$null;$other=$null
$checks=0
function Assert([bool]$condition,[string]$message){
 if(-not $condition){throw ('GUARD_TEST_FAIL '+$message)}
 $script:checks++
}
try{
 foreach($p in @($root,$foreign,$bak,$outside,(Join-Path $appdata 'Microsoft\Windows\Start Menu\Programs'))){
   New-Item -ItemType Directory -Path $p -Force|Out-Null
 }
 $env:APPDATA=$appdata
 $code='using System; using System.Threading; class Probe { static void Main() { Thread.Sleep(30000); } }'
 $cs=Join-Path $workspace 'Probe.cs'
 Set-Content -LiteralPath $cs -Value $code -Encoding UTF8
 $targetExe=Join-Path $root 'FreeNetHub.exe'
 & $csc /nologo /target:exe ("/out:$targetExe") $cs
 if($LASTEXITCODE -ne 0){throw 'Probe compilation failed.'}
 $foreignExe=Join-Path $foreign 'FreeNetHub.exe'
 Copy-Item -LiteralPath $targetExe -Destination $foreignExe
 'backup-exe'|Set-Content -LiteralPath (Join-Path $bak 'FreeNetHub.exe') -Encoding UTF8
 'backup-icon'|Set-Content -LiteralPath (Join-Path $bak 'FreeNetHub.ico') -Encoding UTF8
 '{"restored":true}'|Set-Content -LiteralPath (Join-Path $bak 'SHELL_HOST_STATUS.json') -Encoding UTF8
 'old-link'|Set-Content -LiteralPath (Join-Path $bak 'FreeNet Hub.lnk') -Encoding UTF8
 'active-icon'|Set-Content -LiteralPath (Join-Path $root 'FreeNetHub.ico') -Encoding UTF8
 $oldHash=(Get-FileHash -LiteralPath $targetExe -Algorithm SHA256).Hash
 $rejected=$false
 try { & $script -Root $root -Backup $outside|Out-Null }catch{ $rejected=([string]$_ -match 'backup is not') }
 Assert $rejected 'external backup path rejected'
 Assert ((Get-FileHash -LiteralPath $targetExe -Algorithm SHA256).Hash -eq $oldHash) 'external backup does not modify file'
 $own=Start-Process -FilePath $targetExe -PassThru -WindowStyle Hidden
 $other=Start-Process -FilePath $foreignExe -PassThru -WindowStyle Hidden
 Start-Sleep -Milliseconds 350
 Assert (-not $own.HasExited -and -not $other.HasExited) 'both controlled probe processes alive'
 $blocked=$false
 try { & $script -Root $root -Backup $bak|Out-Null }catch{ $blocked=([string]$_ -match 'close the FreeNetHub executable') }
 Assert $blocked 'target process blocks rollback'
 $own.Refresh();$other.Refresh()
 Assert (-not $own.HasExited -and -not $other.HasExited) 'rollback did not terminate either process'
 Assert ((Get-FileHash -LiteralPath $targetExe -Algorithm SHA256).Hash -eq $oldHash) 'blocked rollback leaves executable untouched'
 $own.Kill();[void]$own.WaitForExit(2500);$own.Refresh()
 Assert $own.HasExited 'only owned target probe was stopped by test'
 & $script -Root $root -Backup $bak|Out-Null
 $other.Refresh()
 Assert (-not $other.HasExited) 'unrelated same-name process is not touched'
 $restored=Get-Content -LiteralPath $targetExe -Raw
 Assert ($restored -match 'backup-exe') 'expected executable restored'
 Assert ((Get-Content -LiteralPath (Join-Path $root 'FreeNetHub.ico') -Raw) -match 'backup-icon') 'expected icon restored'
 Assert ((Get-Content -LiteralPath (Join-Path $root 'SHELL_HOST_STATUS.json') -Raw) -match '"restored":true') 'status restored'
 Assert ((Get-Content -LiteralPath (Join-Path $appdata 'Microsoft\Windows\Start Menu\Programs\FreeNet Hub.lnk') -Raw) -match 'old-link') 'shortcut restored only inside sandbox'
 Write-Output ("ROLLBACK_ROOT_GUARD_PASS {0}/12; two isolated same-name probes; foreign process preserved" -f $checks)
}finally{
 if($own){try{$own.Refresh();if(-not $own.HasExited){$own.Kill();[void]$own.WaitForExit(2500)}}catch{}}
 if($other){try{$other.Refresh();if(-not $other.HasExited){$other.Kill();[void]$other.WaitForExit(2500)}}catch{}}
 $env:APPDATA=$oldAppdata
 if(Test-Path -LiteralPath $workspace){Remove-Item -LiteralPath $workspace -Recurse -Force -ErrorAction SilentlyContinue}
}
