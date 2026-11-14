; ======================================================================
; ip+ - Inno Setup Windows Installer Script
; Produces: release/ip+_Setup_v1.0.0.exe
; ======================================================================

#define MyAppName "ip+"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Iqsan Azhar"
#define MyAppURL "https://github.com/iqsanazhr/ip_plus"
#define MyAppExeName "ip+.exe"

[Setup]
; Unique GUID for ip+ Windows Installer
AppId={{9E6E92B1-4A82-4144-8C37-975CD4981C8E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\ip+
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\release
OutputBaseFilename=ip+_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\ip_plus.ico
UninstallDisplayIcon={app}\assets\ip_plus.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "installappledriver"; Description: "Pasang otomatis Apple Mobile Device Support (Driver USB Apple resmi dari Apple Inc.)"; GroupDescription: "Layanan Perangkat Keras Apple:"; Flags: checkedonce; Check: not IsAppleDriverServiceRunning

[Files]
; Distribute all built application files from the standalone release (No Python required)
Source: "..\release\ip_plus-Win64-Standalone-EXE-v{#MyAppVersion}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\ip_plus.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\ip_plus.ico"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Start-Process winget -ArgumentList 'install --id Apple.AppleMobileDeviceSupport -e --silent --accept-package-agreements --accept-source-agreements' -Wait -WindowStyle Hidden -ErrorAction SilentlyContinue"""; StatusMsg: "Memeriksa dan memasang driver USB Apple resmi..."; Tasks: installappledriver; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.pane_webview_storage"
Type: files; Name: "{app}\user_settings.json"
Type: files; Name: "{app}\typed_history.json"
Type: files; Name: "{app}\debug_metrics.json"

[Code]
function IsAppleDriverServiceRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('sc.exe', 'query "Apple Mobile Device Service"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;
