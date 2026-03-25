; grabtl Inno Setup Script
; Generates a Windows installer for grabtl

[Setup]
AppName=grabtl
AppVersion=0.1.0
AppPublisher=grabtl
AppPublisherURL=https://github.com/naokami3/grabtl
DefaultDirName={userappdata}\grabtl
DefaultGroupName=grabtl
OutputDir=build\installer
OutputBaseFilename=grabtl-0.1.0-setup
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=assets\grabtl.ico
UninstallDisplayIcon={app}\grabtl.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成"; GroupDescription: "追加オプション:"

[Files]
Source: "build\release\build_entry.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\grabtl"; Filename: "{app}\grabtl.exe"
Name: "{group}\grabtl をアンインストール"; Filename: "{uninstallexe}"
Name: "{userdesktop}\grabtl"; Filename: "{app}\grabtl.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\grabtl.exe"; Description: "grabtl を起動"; Flags: nowait postinstall skipifsilent
