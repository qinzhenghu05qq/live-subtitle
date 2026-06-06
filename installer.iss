; Inno Setup 6 installer for LiveSubtitle (Windows)
; 生成 dist\LiveSubtitleSetup.exe

#define AppName "LiveSubtitle"
#define AppVersion "1.0.0"
#define AppPublisher "Local Build"

[Setup]
AppId={{B5C0E3A2-8F4A-4C9B-9A41-3E1F5C2D7B91}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=LiveSubtitleSetup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
UninstallDisplayIcon={app}\LiveSubtitle.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\LiveSubtitle\LiveSubtitle.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\LiveSubtitle\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\LiveSubtitle.exe"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\LiveSubtitle.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LiveSubtitle.exe"; Description: "立即启动 {#AppName}"; Flags: nowait postinstall skipifsilent
