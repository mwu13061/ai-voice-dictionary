; D:\AI VOICE\installer_setup.iss
; Inno Setup Compiler Script
; 透過免費的 Inno Setup 工具開啟此檔案並按下 [Compile]，即可生成銷售給一般使用者的單一安裝檔 (Setup.exe)

[Setup]
; 軟體基本資訊
AppName=AI 語音助手
AppVersion=1.0.0
AppPublisher=AI Voice Dictionary Team
DefaultDirName={localappdata}\Programs\AIVoiceAssistant
DisableDirPage=no
DefaultGroupName=AI 語音助手
DisableProgramGroupPage=yes

; 輸出路徑與安裝檔名稱
OutputDir=D:\AI VOICE\installer_output
OutputBaseFilename=AI_Voice_Assistant_Setup
SetupIconFile=D:\AI VOICE\assets\icon.png
Compression=lzma2/max
SolidCompression=yes

; 權限要求：不需要管理員權限即可安裝在使用者個人的 AppData 中，避開權限阻擋問題
PrivilegesRequired=lowest
ChangesEnvironment=yes

[Languages]
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 拷貝 PyInstaller 產出的綠色版資料夾 dist\AI語音助手_v1000 內的所有檔案與資料夾
Source: "D:\AI VOICE\dist\AI語音助手_v1000\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 建立開始功能表捷徑
Name: "{group}\AI 語音助手"; Filename: "{app}\AI語音助手.exe"; IconFilename: "{app}\assets\icon.png"
; 建立桌面捷徑
Name: "{autodesktop}\AI 語音助手"; Filename: "{app}\AI語音助手.exe"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.png"

[Run]
; 安裝完成後引導啟動軟體
Filename: "{app}\AI語音助手.exe"; Description: "啟動 AI 語音助手"; Flags: nowait postinstall skipifsilent
