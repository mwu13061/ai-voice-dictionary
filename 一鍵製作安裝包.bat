@echo off
chcp 65001 >nul
echo ===================================================
echo 🛠️  AI 語音助手：一鍵封裝與安裝包製作小工具 🛠️
echo ===================================================
echo.

:: 1. 啟用虛擬環境
echo [步驟 1/3] 啟用 Python 虛擬環境...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 錯誤：找不到 venv 虛擬環境！請確認程式目錄完整性。
    pause
    exit /b
)
call venv\Scripts\activate.bat

:: 2. 執行 PyInstaller 封裝
echo.
echo [步驟 2/3] 開始執行 PyInstaller 封裝程式 (這可能需要幾分鐘)...
python -m PyInstaller build_config.spec --clean
if %errorlevel% neq 0 (
    echo.
    echo ❌ 錯誤：PyInstaller 封裝失敗！請檢查錯誤日誌。
    pause
    exit /b
)
echo.
echo ✅ PyInstaller 封裝完成！檔案已輸出至 dist\AI語音助手_v1000

:: 3. 搜尋 Inno Setup 並自動編譯安裝包
echo.
echo [步驟 3/3] 正在尋找 Inno Setup 編譯器 (ISCC.exe)...

set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

if not defined ISCC_PATH (
    echo.
    echo ⚠️  提示：未在系統中檢測到 Inno Setup。
    echo 💡  請先下載並安裝免費的 Inno Setup 6：https://jrsoftware.org/isdl.php
    echo 💡  安裝完成後，您可以直接【雙擊】專案根目錄的 「installer_setup.iss」手動進行編譯。
    echo.
    echo 📦 綠色版資料夾（已打包完成）：D:\AI VOICE\dist\AI語音助手_v1000
    echo.
    pause
    exit /b
)

echo.
echo 🚀 找到 Inno Setup！正在編譯打包安裝檔...
"%ISCC_PATH%" installer_setup.iss
if %errorlevel% neq 0 (
    echo.
    echo ❌ 錯誤：Inno Setup 編譯安裝檔失敗！
    pause
    exit /b
)

echo.
echo ===================================================
echo 🎉🎉🎉 安裝包製作成功！ 🎉🎉🎉
echo ===================================================
echo.
echo 📁 安裝檔路徑：D:\AI VOICE\installer_output\AI_Voice_Assistant_Setup.exe
echo.
pause
