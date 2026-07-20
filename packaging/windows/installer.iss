#define AppName "MTGA Deck Downloader"
#define AppExeName "mtga-deck-downloader.exe"
#define AppVersion GetEnv("APP_VERSION")
#define PayloadDir GetEnv("PAYLOAD_DIR")
#define OutputDir GetEnv("OUTPUT_DIR")
#define IconPath GetEnv("ICON_PATH")

[Setup]
AppId={{D4355F58-216F-45ED-A210-BA67E0CB87F4}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=pattont
AppPublisherURL=https://github.com/pattont/MTGA-DeckDownloader
AppSupportURL=https://github.com/pattont/MTGA-DeckDownloader/issues
AppUpdatesURL=https://github.com/pattont/MTGA-DeckDownloader/releases
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=MTGA-Deck-Downloader-{#AppVersion}-windows-x64-setup
SetupIconFile={#IconPath}
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName} Installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent unchecked
