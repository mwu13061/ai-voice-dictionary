@echo off
CHCP 65001 > nul
echo ===================================================
echo [A1000] 商業化發布封裝管理員
echo ===================================================
echo.
echo 正在清理舊的建置緩存...
taskkill /f /im AI語音助手.exe 2>nul
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo 正在執行專業封裝 (PyInstaller)...
echo 這可能需要幾分鐘，請稍候...
.\venv\Scripts\python.exe -m PyInstaller build_config.spec --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 封裝失敗！請檢查錯誤訊息。
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ---------------------------------------------------
echo ✅ 封裝核心完成！
echo ---------------------------------------------------
echo.
echo [最後步驟：準備分發包]
echo 1. 正在將 models 目錄複製到輸出資料夾...
xcopy /e /i /y "models" "dist\AI語音助手_v1000\models"

echo.
echo 2. 封裝成功！您的可分發程式位於：
echo    D:\AI VOICE\dist\AI語音助手_v1000
echo.
echo [分發確認]
if exist "dist\AI語音助手_v1000\models" (
    echo ✅ 0.1B 模型已自動包含在資料夾中，可直接拷貝使用。
) else (
    echo ⚠️ 警告：找不到 models 資料夾，請手動確認。
)
echo.
echo 🔔 封裝已全部結束！
powershell -c "[console]::beep(1000, 500); [console]::beep(1200, 500)"
echo.
echo [如何部署到其他電腦]
echo - 將 "AI語音助手_v1000" 整份資料夾拷貝到隨身碟。
echo - 在目標電腦上，直接執行資料夾內的 "AI語音助手.exe"。
echo - 提示：目標電腦若報 DLL 缺失，請安裝資料夾內(若有)或網路上的 VC++ Redist 2015-2022。
echo.
pause
