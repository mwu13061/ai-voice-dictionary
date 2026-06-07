# src/ui/magic_toast.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
import pyperclip
import keyboard
import time

class MagicToast(QWidget):
    """
    [A201] Minimalist Confirm Toast.
    - Only "Undo" button.
    - Click anywhere else = Confirm (default behavior as it closes).
    """
    def __init__(self, original_text, new_text, parent=None):
        super().__init__(parent)
        self.original_text = original_text
        self.new_text = new_text
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget { background-color: #8e44ad; border: 2px solid #9b59b6; border-radius: 20px; }
            QLabel { color: white; font-weight: bold; font-family: 'Microsoft JhengHei'; }
        """)
        c_layout = QHBoxLayout(container)
        
        c_layout.addWidget(QLabel("✨ AI 優化已套用"))
        
        undo_btn = QPushButton("↺ 撤銷並還原原文")
        undo_btn.setStyleSheet("""
            QPushButton { background: #e74c3c; color: white; border-radius: 12px; padding: 6px 15px; font-weight: bold; }
            QPushButton:hover { background: #ff4757; }
        """)
        undo_btn.clicked.connect(self.on_undo)
        c_layout.addWidget(undo_btn)
        
        layout.addWidget(container)
        # Stay a bit longer so user can read
        QTimer.singleShot(8000, self.close)

    def on_undo(self):
        try:
            pyperclip.copy(self.original_text)
            keyboard.press_and_release('ctrl+v')
        except: pass
        self.close()

    def show_at_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 150
        self.move(x, y)
        self.show()
