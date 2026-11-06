; ============================================================================
; SNIPLY — Inno Setup Windows Installer Script
; Builds a signed-ready Windows 10/11 Setup Wizard (SNIPLY_Setup_v1.0.0.exe)
; Preserves user clipboard history during uninstallation unless explicitly confirmed.
; ============================================================================

#define MyAppName "SNIPLY"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SNIPLY Contributors"
#define MyAppURL "https://github.com/kemorovv/SNIPLY"
#define MyAppExeName "SNIPLY.exe"

[Setup]
AppId={{8E74A29F-53A1-4F2C-9D81-7B2C38E9011A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=SNIPLY_Setup_v{#MyAppVersion}
SetupIconFile=..\resources\logo\sniply.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\SNIPLY\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\SNIPLY\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\logo\sniply.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\resources\logo\sniply.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataPath := ExpandConstant('{localappdata}\SNIPLY');
    if DirExists(DataPath) then
    begin
      if MsgBox('Would you also like to permanently delete your local SNIPLY clipboard history, images, and settings stored in ' + DataPath + '?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(DataPath, True, True, True);
      end;
    end;
  end;
end;
