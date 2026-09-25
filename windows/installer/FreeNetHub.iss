#define MyAppName "FreeNet Hub"
#define MyAppVersion "4.2.0"
#define MyAppPublisher "FreeNet Hub"
#define MyAppExeName "FreeNetHub.exe"

[Setup]
AppId={{BCE83A4E-8897-4D52-A650-BB67A2BB8142}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\FreeNetHub
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\delivery\github_v4.2.0
OutputBaseFilename=FreeNetHub_4.2.0_R16_Clean_Setup
SetupIconFile=..\standalone\FreeNetHub.ico
UninstallDisplayIcon={app}\FreeNetHub.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ChangesAssociations=no
ChangesEnvironment=no
VersionInfoVersion=4.2.0.0
VersionInfoProductName=FreeNet Hub
VersionInfoDescription=FreeNet Hub 4.2 installer
MinVersion=10.0.19041
AppMutex=Local\FreeNetHub.Desktop.SingleInstance.v41

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Dirs]
Name: "{app}\data"
Name: "{app}\jobs"
Name: "{app}\evidence"
Name: "{app}\gateway\runtime"

[InstallDelete]
Type: filesandordirs; Name: "{app}\\runtime"

[Files]
Source: "..\standalone\FreeNetHub.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\standalone\FreeNetHub.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\app\engine.py"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\..\app\FreeNetHub.ps1"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\..\app\View.xaml"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\..\app\manifest.json"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\..\app\dependencies.example.json"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\..\app\assets\FreeNetHub.ico"; DestDir: "{app}\app\assets"; Flags: ignoreversion
Source: "..\..\app\assets\FreeNetHub_256.png"; DestDir: "{app}\app\assets"; Flags: ignoreversion
Source: "..\runtime\WarpPlusFast\*"; DestDir: "{app}\runtime\WarpPlusFast"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\runtime\TorSnowflake\bundle\*"; DestDir: "{app}\runtime\TorSnowflake\bundle"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\gateway\gateway_control.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\gateway_request.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\Setup-GatewayCore.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\Setup-ConsoleGateway.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\gateway_defaults.json"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\runtime_config.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\preflight.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\generate_config.py"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\apply_elevated.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\stop_elevated.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\console_provider.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\wsl_console.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\build_isolated_mihomo.py"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\import_wireguard.py"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\validate_console_profile.ps1"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\socks_udp_probe.py"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\manifest.json"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\README_FA.md"; DestDir: "{app}\gateway"; Flags: ignoreversion
Source: "..\..\gateway\tests\direct_stun.py"; DestDir: "{app}\gateway\tests"; Flags: ignoreversion
Source: "..\..\Setup-WindowsDependencies.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\Uninstall-FreeNetHub.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\docs\HELP_FA.txt"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\docs\ADVANCED_FA.txt"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\docs\BRIDGES_FA.txt"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\docs\RELEASE_NOTES_FA.txt"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\docs\research.json"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FreeNet Hub"; Filename: "{app}\FreeNetHub.exe"; Parameters: """{app}\app\FreeNetHub.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\FreeNetHub.exe"
Name: "{autodesktop}\FreeNet Hub"; Filename: "{app}\FreeNetHub.exe"; Parameters: """{app}\app\FreeNetHub.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\FreeNetHub.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FreeNetHub.exe"; Parameters: """{app}\app\FreeNetHub.ps1"""; Description: "Launch FreeNet Hub"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\INSTALL_RUNTIME_STATUS.json"
Type: files; Name: "{app}\PWSH_PATH.txt"
Type: files; Name: "{app}\UNINSTALL_CLEANUP_STATUS.json"
Type: files; Name: "{app}\settings.json"
Type: files; Name: "{app}\app\dependencies.json"
Type: filesandordirs; Name: "{app}\jobs"
Type: filesandordirs; Name: "{app}\evidence"
Type: filesandordirs; Name: "{app}\gateway\runtime"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\runtime"

[Code]
function FindPwsh: String;
var
  P: String;
begin
  Result := '';
  P := AddBackslash(GetEnv('ProgramFiles')) + 'PowerShell\7\pwsh.exe';
  if FileExists(P) then begin Result := P; exit; end;
  P := AddBackslash(GetEnv('ProgramFiles')) + 'PowerShell\7-preview\pwsh.exe';
  if FileExists(P) then begin Result := P; exit; end;
  P := AddBackslash(ExpandConstant('{localappdata}')) + 'Programs\PowerShell\7\pwsh.exe';
  if FileExists(P) then begin Result := P; exit; end;
  P := FileSearch('pwsh.exe', GetEnv('PATH'));
  if P <> '' then Result := P;
end;

function PwshPath(Param: String): String;
begin
  Result := FindPwsh;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  P, Winget: String;
  ResultCode: Integer;
begin
  NeedsRestart := False;
  Result := '';
  P := FindPwsh;
  if P <> '' then exit;

  Winget := FileSearch('winget.exe', GetEnv('PATH'));
  if Winget = '' then
    Winget := ExpandConstant('{localappdata}\Microsoft\WindowsApps\winget.exe');
  if not FileExists(Winget) then begin
    Result := 'PowerShell 7 is required and Windows Package Manager (winget) was not found. Install PowerShell 7, then run Setup again.';
    exit;
  end;

  if (not Exec(Winget, 'install --id Microsoft.PowerShell --exact --source winget --accept-source-agreements --accept-package-agreements --silent --disable-interactivity',
      '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode)) or (ResultCode <> 0) then begin
    Result := 'PowerShell 7 prerequisite installation failed. No FreeNet Hub network changes were made.';
    exit;
  end;

  P := FindPwsh;
  if P = '' then begin
    P := AddBackslash(GetEnv('ProgramFiles')) + 'PowerShell\7\pwsh.exe';
    if not FileExists(P) then begin
      Result := 'PowerShell 7 was installed but pwsh.exe could not be resolved. Sign out/in or install PowerShell 7 and rerun Setup.';
      exit;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  P, Params: String;
  ResultCode: Integer;
  PwshLines: TArrayOfString;
begin
  if CurStep = ssPostInstall then begin
    P := FindPwsh;
    if P = '' then
      RaiseException('PowerShell 7 runtime is unavailable after prerequisite setup.');

    SetArrayLength(PwshLines, 1);
    PwshLines[0] := P;
    if not SaveStringsToUTF8FileWithoutBOM(ExpandConstant('{app}\PWSH_PATH.txt'), PwshLines, False) then
      RaiseException('FreeNet Hub could not persist the PowerShell 7 runtime path.');

    Params := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
      ExpandConstant('{app}\Setup-WindowsDependencies.ps1') +
      '" -InstallMissingRuntime -ResultPath "' +
      ExpandConstant('{app}\INSTALL_RUNTIME_STATUS.json') + '"';

    if (not Exec(P, Params, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode)) or (ResultCode <> 0) then
      RaiseException('FreeNet Hub runtime bootstrap failed. Setup did not promote this installation.');

    if not FileExists(ExpandConstant('{app}\app\dependencies.json')) then
      RaiseException('FreeNet Hub dependency manifest was not created.');
    if not FileExists(ExpandConstant('{app}\INSTALL_RUNTIME_STATUS.json')) then
      RaiseException('FreeNet Hub runtime acceptance record was not created.');
  end;
end;

function InitializeUninstall: Boolean;
var
  P, ScriptPath, Params, PwshFile: String;
  ResultCode: Integer;
  PwshLines: TArrayOfString;
begin
  Result := True;
  ScriptPath := ExpandConstant('{app}\Uninstall-FreeNetHub.ps1');
  if not FileExists(ScriptPath) then exit;

  P := '';
  PwshFile := ExpandConstant('{app}\PWSH_PATH.txt');
  if FileExists(PwshFile) and LoadStringsFromFile(PwshFile, PwshLines) and (GetArrayLength(PwshLines) > 0) then
    P := Trim(PwshLines[0]);
  if (P = '') or (not FileExists(P)) then
    P := FindPwsh;
  if P = '' then begin
    MsgBox('PowerShell 7 is required to safely stop FreeNet Hub network state before uninstall.', mbError, MB_OK);
    Result := False;
    exit;
  end;

  Params := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ScriptPath + '" -ResultPath "' +
    ExpandConstant('{app}\UNINSTALL_CLEANUP_STATUS.json') + '"';

  if (not Exec(P, Params, ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode)) or (ResultCode <> 0) then begin
    MsgBox('FreeNet Hub could not verify safe network cleanup. Uninstall was cancelled so an active tunnel is not orphaned.', mbError, MB_OK);
    Result := False;
  end;
end;
