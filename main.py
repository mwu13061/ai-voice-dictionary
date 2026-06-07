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
