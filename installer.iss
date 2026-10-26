; Inno Setup script: turns dist\PWCScan into a one-file installer.
; Build with build_windows.bat, or open this file in Inno Setup 6 and press Compile.

#define AppName "PWC Scan"
#define AppVersion "1.2.0"
#define AppPublisher "Rowland Restorations"
#define AppExe "PWCScan.exe"

[Setup]
; Never change the AppId: it's what makes a new version upgrade the installed one.
AppId={{6CE4B958-3306-438D-95FD-9C41288C079B}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Per-user install: no admin prompt, installs to %LOCALAPPDATA%\Programs
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=PWCScan-Setup-{#AppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\PWCScan\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
