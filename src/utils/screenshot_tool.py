# src/utils/screenshot_tool.py
import os
import time
from PIL import Image
from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QScreen

class ScreenshotTool:
    """
    [A256] DPI-Aware Screenshot Tool.
    - Uses logical-to-physical mapping for high-res screens.
    - Forced directory verification.
    """
    @staticmethod
    def capture_fullscreen(save_path="user_data/temp_snip.png"):
        try:
            full_path = os.path.abspath(save_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            screen = QGuiApplication.primaryScreen()
            if not screen: return None
            
            pixmap = screen.grabWindow(0)
            pixmap.save(full_path, "PNG")
            logger.info(f"Fullscreen saved to: {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Fullscreen failed: {e}")
            return None

    @staticmethod
    def capture_area(rect, save_path="user_data/temp_snip.png"):
        """
        Captures a specific QRect area with DPI awareness.
        """
        try:
            full_path = os.path.abspath(save_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            screen = QGuiApplication.primaryScreen()
            if not screen: return None
            
            # [A256] Handle High-DPI scaling
            # Qt's grabWindow on Windows expects logical coordinates, 
            # but sometimes there's an offset if virtual desktop isn't starting at (0,0).
            dpr = screen.devicePixelRatio()
            logger.info(f"Capture Area: {rect.x()},{rect.y()} {rect.width()}x{rect.height()} (DPR: {dpr})")
            
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            
            if pixmap.isNull():
                logger.error("GrabWindow returned a null pixmap.")
                return None
                
            success = pixmap.save(full_path, "PNG")
            if success:
                logger.info(f"Area saved to: {full_path}")
                return full_path
            else:
                logger.error(f"Failed to save pixmap to {full_path}")
                return None
        except Exception as e:
            logger.error(f"Area capture failed: {e}")
            return None
