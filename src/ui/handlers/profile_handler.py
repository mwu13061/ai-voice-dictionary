# src/ui/handlers/profile_handler.py
import threading
import time
import pyautogui
import keyboard
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from src.ui.settings_window import RefinementDialog

class ProfileHandler:
    """
    [A542] Isolated AI Refinement Logic.
    Manages:
    - AI text optimization (FIX mode).
    - RefinementDialog interaction.
    - Result delivery to target application.
    """
    def __init__(self, controller):
        self.controller = controller

    def launch_refinement(self, text):
        """ [A583/A586] Entry point for FIX mode with empty check and dynamic profiles """
        if not text or not text.strip():
            logger.warning("⚠️ [FIX] No text captured. Aborting.")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未偵測到選取文字。\\n請先用滑鼠選取一段文字後再執行此功能。")
            return

        ready, err = self.controller.cloud_engine.is_ready()
        if not ready:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "AI 未就緒", err)
            return
        
        # [A586] Pass profiles to dialog
        p = self.controller.settings.raw_config.get("opt_profiles", [])
        i = self.controller.settings.raw_config.get("active_profile_idx", 0)
        profile_names = [x["name"] for x in p]
        
        self.refine_dlg = RefinementDialog(text, profile_names, i)
        self.refine_dlg.restore_requested.connect(self.handle_restore)
        self.refine_dlg.retry_requested.connect(lambda req: threading.Thread(
            target=self._run_inference, args=(text, req), daemon=True).start())
        self.refine_dlg.profile_changed.connect(self.handle_profile_change)
        self.refine_dlg.show()
        
        threading.Thread(target=self._run_inference, args=(text,), daemon=True).start()

    def handle_profile_change(self, idx):
        """ [A586] Update active profile and re-run immediately """
        logger.info(f"🔄 [PROFILE_HANDLER] Profile switched to index {idx}")
        self.controller.settings.raw_config["active_profile_idx"] = idx
        self.controller.settings._widget_changed() # Trigger save
        
        # Reset dialog status
        if self.refine_dlg:
            self.refine_dlg.status.setText("⏳ AI 處理中...")
            self.refine_dlg.status.setStyleSheet("color:#f39c12;")
            self.refine_dlg.btn_restore.setEnabled(False)
            self.refine_dlg.btn_retry.setEnabled(False)
        
        threading.Thread(target=self._run_inference, args=(self.refine_dlg.original_text, ""), daemon=True).start()

    def _run_inference(self, text, extra_req=""):
        try:
            m = self.controller.settings.raw_config.get("opt_model", "")
            p = self.controller.settings.raw_config.get("opt_profiles", [])
            i = self.controller.settings.raw_config.get("active_profile_idx", 0)
            u = p[i]['prompt'] if 0 <= i < len(p) else "請優化:"
            
            s = f"你是一個專業的文字修飾助手。只能輸出最終結果。不要對話。方向：{u}"
            if extra_req:
                s += f" 追加要求：{extra_req}"
                
            res = self.controller.cloud_engine.process_text(user_text=text, system_prompt=s, model_override=m)
            self.controller.refinement_result_signal.emit(res)
        except Exception as e:
            logger.error(f"❌ [PROFILE_HANDLER] Inference Failed: {e}")

    def deliver_result(self, res):
        """ connected to refinement_result_signal """
        if hasattr(self, 'refine_dlg') and self.refine_dlg:
            if not res.startswith("❌"):
                # [A545] Explicit Hardened Sequence instead of pyautogui
                keyboard.press('ctrl')
                time.sleep(0.1)
                keyboard.press('a')
                time.sleep(0.1)
                keyboard.release('a')
                keyboard.release('ctrl')
                
                time.sleep(0.1)
                self.controller.output_plugin.output(res)
            self.refine_dlg.show_ready()

    def handle_restore(self, original_text):
        # [A545] Explicit Hardened Sequence
        keyboard.press('ctrl')
        time.sleep(0.1)
        keyboard.press('a')
        time.sleep(0.1)
        keyboard.release('a')
        keyboard.release('ctrl')
        
        time.sleep(0.1)
        self.controller.output_plugin.output(original_text)
