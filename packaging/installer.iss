; Inno Setup 6 Script for Devoice Workstation
; Generates Devoice-Setup.exe (Standalone Windows Installer)

#define MyAppName "Devoice"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Devoice Audio"
#define MyAppURL "https://github.com/Req1quor/Devoice"
#define MyAppExeName "Devoice.exe"

[Setup]
AppId={{5E97D4B2-3A79-4B5C-9A8E-1C9D4F281E93}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Devoice-Setup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "flstudio"; Description: "Intégrer Devoice au menu Outils de FL Studio (Tools -> Devoice)"; GroupDescription: "Intégrations DAW :"; Check: IsFLStudioInstalled

[Dirs]
Name: "{app}\runtime"; Permissions: users-full
Name: "{app}\models"; Permissions: users-full

[Files]
Source: "..\dist\Devoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function IsFLStudioInstalled: Boolean;
begin
  Result := RegKeyExists(HKCU, 'Software\Image-Line\Shared\FL Studio tools') or 
            RegKeyExists(HKCU, 'Software\Image-Line\FL Studio 21') or 
            RegKeyExists(HKCU, 'Software\Image-Line\FL Studio 20');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  I: Integer;
  SubKey: String;
  ToolName: String;
  EmptySlot: Integer;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('flstudio') then
  begin
    EmptySlot := -1;
    for I := 0 to 7 do
    begin
      SubKey := 'Software\Image-Line\Shared\FL Studio tools\' + IntToStr(I);
      if RegQueryStringValue(HKCU, SubKey, 'Name', ToolName) then
      begin
        if (ToolName = '') or (ToolName = 'Devoice') then
        begin
          EmptySlot := I;
          Break;
        end;
      end
      else
      begin
        EmptySlot := I;
        Break;
      end;
    end;

    if EmptySlot >= 0 then
    begin
      SubKey := 'Software\Image-Line\Shared\FL Studio tools\' + IntToStr(EmptySlot);
      RegWriteStringValue(HKCU, SubKey, 'Name', 'Devoice');
      RegWriteStringValue(HKCU, SubKey, 'FileName', ExpandConstant('{app}\{#MyAppExeName}'));
      RegWriteStringValue(HKCU, SubKey, 'Params', '');
    end;
  end;
end;
