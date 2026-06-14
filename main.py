# main.py
import sys
import os

# [A4] ULTRA-FAST OFFLINE INITIALIZATION: DISABLE HF/MODELSCOPE CONNECTION WAITS
os.environ["MODELSCOPE_DISABLE_UPDATE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# [A215] ULTRA ENCODING SHIELD: FORCE UTF-8 AT ALL LEVELS
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "UTF-8"

# [A1000] DPI & ENVIRONMENT RESILIENCE
if sys.platform == "win32":
    # Prevent Qt from conflicting with manual DPI settings
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTOSCALE_DOS"] = "1" 

    try:
        import io
        if sys.stdout is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except: pass

from PySide6.QtWidgets import QApplication
from src.ui.app_controller import AppController
from src.utils.path_helper import initialize_universal_environment, get_writable_path # [A1000]
from loguru import logger


def kill_other_instances():
    import os
    import sys
    import time
    import socket
    import subprocess
    from loguru import logger
    
    my_pid = os.getpid()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', 29988))
        # Keep socket open to hold the lock
        globals()['_instance_lock_socket'] = s
    except socket.error:
        logger.info("⚠️ [SINGLETON] Another instance of AI Voice Assistant is running. Terminating it...")
        # PowerShell script to search for other python.exe/pythonw.exe processes running main.py and terminate them
        cmd = 'powershell -Command "Get-CimInstance Win32_Process -Filter \\"Name = \'python.exe\' or Name = \'pythonw.exe\'\\" | Where-Object { $_.CommandLine -like \'*main.py*\' -and $_.ProcessId -ne ' + str(my_pid) + ' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"'
        try:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as p_err:
            logger.warning(f"Failed to execute process termination command: {p_err}")
            
        time.sleep(0.8)
        try:
            s.bind(('127.0.0.1', 29988))
            globals()['_instance_lock_socket'] = s
            logger.success("✅ [SINGLETON] Old instance successfully terminated. New instance has taken control.")
        except socket.error:
            logger.error("❌ [SINGLETON] Could not bind port 29988 even after termination attempt. Another instance might be stuck. Exiting.")
            sys.exit(1)

def main():
    # [A402] Diagnostic Restoration: Keep console log in source mode
    logger.remove()
    
    # 1. Always log to file (Async)
    log_file = get_writable_path("app_runtime.log")
    logger.add(log_file, rotation="1 MB", encoding="utf-8", level="DEBUG", enqueue=True)
    
    # 2. Log to console ALWAYS (if available) [A568/A569]
    import sys as sys_module
    if sys_module.stderr is not None:
        logger.add(sys_module.stderr, level="INFO")
    
    if hasattr(sys, '_MEIPASS'):
        logger.info("🚀 [PROD MODE] Console Diagnostics Active.")
    else:
        logger.info("🛠️ [DEV MODE] Console Logging Active.")
    
    kill_other_instances()
    logger.info(f"--- SYSTEM STARTING (A1000 UNIVERSAL RELEASE) ---")
    
    # [A1000] Lock in embedded binaries before anything else loads
    initialize_universal_environment()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    try:
        controller = AppController()
        controller.run()
        logger.success("✅ Application Awakened. Zero-Dependency Mode Locked.")
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("CRITICAL STARTUP ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
