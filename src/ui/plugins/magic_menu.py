# src/ui/plugins/magic_menu.py
import sys, os, time, threading, pyperclip, keyboard, pyautogui, ctypes
from PySide6.QtWidgets import QMenu, QFileIconProvider, QApplication
from PySide6.QtGui import QCursor, QAction
from PySide6.QtCore import Qt, QTimer, QPoint, QFileInfo
from loguru import logger

class MagicMenu(QMenu):
    """
    Build [A627] SYNCED CAPTURE UI.
    - Receives pre-captured text from SmartTrigger.
    - Zero delay popup.
    """
    def __init__(self, controller, parent=None):
        super().__init__(parent); self.controller = controller 
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.setStyleSheet("QMenu { background-color: #1c2833; color: white; border: 2px solid #3498db; border-radius: 8px; padding: 5px; qproperty-iconSize: 24px 24px; } QMenu::item { padding: 10px 30px 10px 15px; border-radius: 4px; background-color: transparent; } QMenu::item:selected { background-color: #3498db; }")
        self._setup_actions(); self.selected_text = ""

    def _setup_actions(self):
        self.clear(); config_items = self.controller.settings.raw_config.get("magic_items", [])
        provider = QFileIconProvider()
        for item in config_items:
            if not item.get("visible", True): continue
            mid = item["id"]; name = item["name"]; act = QAction(name, self)
            if item.get("type") == "app":
                import shutil; resolved = shutil.which(item.get("val", "").strip().strip("'\"")) or item.get("val", "")
                if os.path.exists(resolved):
                    icon = provider.icon(QFileInfo(resolved))
                    if not icon.isNull(): act.setIcon(icon)
            act.triggered.connect(lambda checked, m=mid: self._process_request(m)); self.addAction(act)
            if mid == "LEARN": self.addSeparator()

    def popup_at_cursor(self, pre_captured_text=""):
        """ [A627] Receives pre-captured text from background thread """
        self.selected_text = pre_captured_text
        self._setup_actions()
        self.adjustSize()
        
        pos = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()
        
        menu_w = self.sizeHint().width()
        menu_h = self.sizeHint().height()
        
        x = pos.x() + 10
        y = pos.y() + 10
        
        if x + menu_w > screen.right():
            x = pos.x() - menu_w - 10
        if y + menu_h > screen.bottom():
            y = pos.y() - menu_h - 10
            
        x = max(screen.left(), x)
        y = max(screen.top(), y)
        
        self._show_time = time.time()
        self.exec(QPoint(x, y))

    def focusOutEvent(self, event): super().focusOutEvent(event); self.close()
    def _process_request(self, mode):
        if hasattr(self, '_show_time') and (time.time() - self._show_time < 0.15): return
        self.hide(); self.close(); time.sleep(0.02) 
        self.controller.magic_request_triggered.emit(mode, self.selected_text)
