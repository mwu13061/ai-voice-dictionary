# src/ui/handlers/dict_handler.py
import threading
import time
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QGuiApplication
from src.ui.settings_window import QuickAddDialog

class DictionaryHandler:
    """
    [A632] Isolated Dictionary Logic.
    [REPRODUCTION_GUARD] Ensures captured text reaches the input field.
    """
    def __init__(self, controller):
        self.controller = controller
        self.quick_dlg = None

    def handle_magic_learn(self, text):
        """ [A632] Data Pipe Restoration """
        logger.info(f"📔 [DICT_HANDLER] Quick-Add request for: '{text[:20]}'")
        
        # 1. Cleanup old
        if self.quick_dlg:
            try: self.quick_dlg.close(); self.quick_dlg.deleteLater()
            except: pass
            
        # 2. Open new MINI dialog
        # Ensure text is passed correctly to initial_text
        self.quick_dlg = QuickAddDialog(text)
        self.quick_dlg.add_req.connect(self.add_item)
        
        # 3. Position above cursor, centered horizontally, with flip and screen clamping
        pos = QCursor.pos()
        # [A60] Use the screen that CONTAINS the cursor (multi-monitor fix)
        cursor_screen = QGuiApplication.screenAt(pos)
        if cursor_screen is None:
            cursor_screen = QGuiApplication.primaryScreen()
        screen = cursor_screen.availableGeometry()
        
        dlg_w = 260
        dlg_h = 185
        
        # Place above the cursor
        x = pos.x() - dlg_w // 2
        y = pos.y() - dlg_h - 20
        
        # If it would go above the screen top, place it below the cursor instead
        if y < screen.top():
            y = pos.y() + 20
            
        # Clamp to screen boundaries
        x = max(screen.left(), min(x, screen.right() - dlg_w))
        y = max(screen.top(), min(y, screen.bottom() - dlg_h))
        
        self.quick_dlg.setGeometry(x, y, dlg_w, dlg_h)
        
        self.quick_dlg.show()
        self.quick_dlg.raise_()
        self.quick_dlg.activateWindow()

    def add_item(self, orig, corr):
        try:
            if self.controller.learning_engine.add_habit_manual(orig, corr):
                self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
                self.controller.ready_signal.emit(f"✅ 已加入詞庫: {orig} ➔ {corr}")
            else:
                self.controller.ready_signal.emit(f"❌ 加入詞庫失敗，請確認詞條格式是否正確")
        except Exception as e:
            logger.error(f"❌ [DICT_HANDLER] add_item error: {e}")
            self.controller.ready_signal.emit(f"❌ 加入詞庫時發生錯誤: {e}")

    def import_items(self, items_json):
        try:
            import json
            items = json.loads(items_json)
            count = 0
            for orig, corr in items:
                if self.controller.learning_engine.add_habit_manual(orig, corr):
                    count += 1
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
            logger.success(f"📔 [DICT_HANDLER] Merged {count} items.")
        except Exception as e:
            logger.error(f"❌ [DICT_HANDLER] Import failed: {e}")

    def del_item(self, orig):
        if self.controller.learning_engine.delete_habit(orig):
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())

    def clear_all(self):
        # [A65] Audit fix: add confirmation dialog before wiping entire dictionary
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None,
            "⚠️ 確認清空詞庫",
            "確定要清空全部個人詞庫嗎？\n\n此操作無法復原，建議先匯出備份。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        if self.controller.learning_engine.clear_dictionary():
            self.controller.settings.update_dict_list([])
            self.controller.ready_signal.emit("🧹 個人詞庫已清空")
