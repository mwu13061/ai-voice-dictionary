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
        
        # 3. Position near cursor
        pos = QCursor.pos()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = max(screen.left(), min(pos.x() + 10, screen.right() - 250))
        y = max(screen.top(), min(pos.y() + 10, screen.bottom() - 150))
        self.quick_dlg.move(x, y)
        
        self.quick_dlg.show()
        self.quick_dlg.raise_()
        self.quick_dlg.activateWindow()

    def add_item(self, orig, corr):
        if self.controller.learning_engine.add_habit_manual(orig, corr):
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
            self.controller.ready_signal.emit(f"✅ 已加入詞庫: {orig} ➔ {corr}")

    def import_items(self, items_json):
        try:
            import json
            items = json.loads(items_json)
            count = 0
            for orig, corr in items:
                if self.controller.learning_engine.add_habit_manual(orig, corr): count += 1
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
            logger.success(f"📔 [DICT_HANDLER] Merged {count} items.")
        except Exception as e:
            logger.error(f"❌ [DICT_HANDLER] Import failed: {e}")

    def del_item(self, orig):
        if self.controller.learning_engine.delete_habit(orig):
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())

    def clear_all(self):
        if self.controller.learning_engine.clear_dictionary():
            self.controller.settings.update_dict_list([])
            self.controller.ready_signal.emit("🧹 詞庫已清空")
