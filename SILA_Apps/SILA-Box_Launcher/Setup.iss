; Script Inno Setup
#define MyAppName "SILA Box"
#define MyAppVersion "1.1"
#define MyAppExeName "SILA_Box.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILABox_Installer
OutputBaseFilename=Setup_{#MyAppName}
SetupIconFile=C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILABox.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
DiskSpanning=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILA_Box.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILABox.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\ExtenSILA.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\EQ-SILAv1.1.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILA.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILAJackBay.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILAKeyMap.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SILAVSTBackup.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\negro\Desktop\SILA_SUELTO\SILABox\SoundWIDIbySILA.exe"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SILABox.ico"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Tasks]
Name: "desktopicon"; Description: "Crear un ícono en el escritorio"; GroupDescription: "Íconos adicionales"; Flags: checkedonce

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall runascurrentuser

[Code]
procedure InitializeWizard;
begin
  // Mostrar mensaje de advertencia si no se ejecuta como administrador
  if not IsAdminLoggedOn then
  begin
    MsgBox('Es necesario ejecutar el instalador como administrador.', mbError, MB_OK);
    WizardForm.Close;
  end;
end;
