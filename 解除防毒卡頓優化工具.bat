@echo off
CHCP 65001 > nul
echo ===================================================
echo [A386] 效能極速優化與防毒白名單登錄工具
echo ===================================================
echo.
echo 說明：
echo 封裝版的 AI 語音助手因為沒有微軟數位簽章，當它執行「全域熱鍵」與「自動打字」時，
echo Windows Defender (微軟防毒) 會將其視為可疑行為，並在【每一次按鍵】時進行記憶體掃描，
echo 這就是導致您感覺「反應變慢」、「極速打字卡頓」的真正元凶！(延遲約 0.3s - 1s)
echo.
echo 此工具將會把您的發布資料夾加入防毒軟體的「排除清單 (白名單)」，
echo 藉此解除防毒軟體的監視，瞬間恢復與 Python 源碼版一樣的極速體驗！
echo.
echo ⚠️ 注意：執行此操作需要系統管理員權限。
echo ---------------------------------------------------

:: Check for administrative permissions
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [狀態] 已取得管理員權限，準備登錄白名單...
) else (
    echo [錯誤] 權限不足！
    echo 請在【解除防毒卡頓優化工具.bat】上點擊右鍵，選擇「以系統管理員身分執行」。
    pause
    exit /b 1
)

:: Add current directory to Defender exclusion
set "TARGET_DIR=%~dp0dist\AI語音助手_v1000"

if not exist "%TARGET_DIR%" (
    echo [錯誤] 找不到發布資料夾。請先執行過封裝管理員。
    pause
    exit /b 1
)

echo 正在將以下路徑加入 Windows Defender 排除清單：
echo %TARGET_DIR%
echo.

powershell -Command "Add-MpPreference -ExclusionPath '%TARGET_DIR%'"

if %errorLevel% == 0 (
    echo ✅ 成功！已解除 Windows Defender 的監視。
    echo 🚀 請重新啟動您的 AI 語音助手.exe，享受極速打字體驗！
) else (
    echo ❌ 發生錯誤，可能您的電腦使用了其他的防毒軟體 (如卡巴斯基、Avast 等)。
    echo 麻煩請手動將該資料夾加入您防毒軟體的白名單中。
)

echo.
pause
