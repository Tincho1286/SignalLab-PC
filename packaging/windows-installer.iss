#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef PayloadDir
  #error PayloadDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef InstallerAppId
  #define InstallerAppId "{{91B68A45-9170-44B7-B40B-A171BDE5938D}"
#endif

[Setup]
AppId={#InstallerAppId}
AppName=SignalLab PC
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}.0
SetupMutex=Local\SignalLabPC.Setup.91B68A45917044B7B40BA171BDE5938D
AppPublisher=SignalLab PC
AppPublisherURL=https://github.com/Tincho1286/SignalLab-PC
AppUpdatesURL=https://github.com/Tincho1286/SignalLab-PC/releases
DefaultDirName={localappdata}\Programs\SignalLab PC
DefaultGroupName=SignalLab PC
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes
DisableDirPage=auto
UsePreviousAppDir=yes
UsePreviousTasks=yes
CloseApplications=yes
CloseApplicationsFilter=SignalLab-PC.exe
RestartApplications=no
UninstallDisplayIcon={app}\SignalLab-PC.exe
LicenseFile={#PayloadDir}\LICENSE
OutputDir={#OutputDir}
OutputBaseFilename=SignalLab-PC-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SignalLab PC"; Filename: "{app}\SignalLab-PC.exe"
Name: "{group}\Desinstalar SignalLab PC"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SignalLab PC"; Filename: "{app}\SignalLab-PC.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SignalLab-PC.exe"; Description: "Abrir SignalLab PC"; Flags: nowait postinstall; Check: LaunchAllowed

[Code]
function OpenProcess(Access: LongWord; Inherit: Integer; Pid: LongWord): THandle;
  external 'OpenProcess@kernel32.dll stdcall';
function WaitForSingleObject(Handle: THandle; Milliseconds: LongWord): LongWord;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Integer;
  external 'CloseHandle@kernel32.dll stdcall';

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Pid: Integer; Process: THandle; WaitResult: LongWord;
    OldMS, OldLS, NewMS, NewLS: Cardinal;
begin
  Result := '';
  Pid := StrToIntDef(ExpandConstant('{param:SIGNALLABPARENTPID|0}'), 0);
  if Pid > 1 then begin
    Process := OpenProcess($00100000, 0, Pid);
    if Process <> 0 then begin
      WaitResult := WaitForSingleObject(Process, 120000);
      CloseHandle(Process);
      if WaitResult <> 0 then
      begin
        Result := 'SignalLab sigue abierto. Cerralo antes de instalar la actualización.';
        Exit;
      end;
    end;
  end;
  if GetVersionNumbers(ExpandConstant('{app}\SignalLab-PC.exe'), OldMS, OldLS) and
     GetVersionNumbers(ExpandConstant('{srcexe}'), NewMS, NewLS) then
    if (OldMS > NewMS) or ((OldMS = NewMS) and (OldLS > NewLS)) then
      Result := 'Ya hay una versión más nueva instalada. Este instalador no la reemplazará.';
end;

function LaunchAllowed: Boolean;
var I: Integer;
begin
  Result := True;
  for I := 1 to ParamCount do
    if Lowercase(ParamStr(I)) = '/nolaunch' then
      Result := False;
end;
