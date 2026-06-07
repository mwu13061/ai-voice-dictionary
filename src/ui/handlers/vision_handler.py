# src/ui/handlers/vision_handler.py
import threading
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from src.utils.screenshot_tool import ScreenshotTool

class VisionHandler:
    """
    [A542] Isolated Vision Logic.
    Manages:
    - Screen snipping.
    - Screenshot processing.
    - Displaying vision results.
    """
    def __init__(self, controller):
        self.controller = controller
        self._snip_overlay = None # [A549] Keep reference to prevent GC

    def start_snip(self):
        """ Entry point for VISION mode """
        logger.info("🎯 [VISION_HANDLER] Starting Snip Flow...")
        ready, err = self.controller.cloud_engine.is_ready()
        if not ready:
            logger.error(f"❌ [VISION_HANDLER] Cloud Engine not ready: {err}")
            QMessageBox.warning(None, "設定不完整", err)
            return
        
        try:
            from src.ui.snip_overlay import SnipOverlay
            self._snip_overlay = SnipOverlay()
            self._snip_overlay.snip_captured.connect(self._handle_snip_captured)
            self._snip_overlay.show()
            logger.success("📸 [VISION_HANDLER] Snip Overlay Visible.")
        except Exception as e:
            logger.error(f"❌ [VISION_HANDLER] Failed to show SnipOverlay: {e}")

    def _handle_snip_captured(self, rect):
        logger.info(f"📸 [VISION_HANDLER] Area captured: {rect}")
        path = ScreenshotTool.capture_area(rect)
        if path:
            logger.info(f"💾 [VISION_HANDLER] Screenshot saved: {path}")
            threading.Thread(target=self._async_process_vision, args=(path,), daemon=True).start()
        else:
            logger.error("❌ [VISION_HANDLER] Screenshot capture returned no path.")

    def _async_process_vision(self, path):
        try:
            m = self.controller.settings.raw_config.get("vision_model", "")
            res = self.controller.cloud_engine.process_vision(path, model_override=m)
            if res:
                self.controller.vision_result_signal.emit(res)
        except Exception as e:
            logger.error(f"❌ [VISION_HANDLER] Process Failed: {e}")

    def show_result_window(self, content=""):
        """ connected to vision_result_signal """
        from src.ui.vision_result_window import VisionResultWindow
        if not hasattr(self.controller, 'vision_win') or self.controller.vision_win is None:
            self.controller.vision_win = VisionResultWindow()
        if content:
            self.controller.vision_win.update_content(content)
        self.controller.vision_win.show_at_center()
