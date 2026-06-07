# src/ui/plugins/magic_menu_v1.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QApplication
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QIcon

class MagicMenuV1(QWidget):
    """
    Context Magic Menu [A97]:
    - Floating AI action menu.
    - Modern minimalist design.
    """
    action_triggered = Signal(str) # Emits the action type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        # Style based on A81 Capsule aesthetics
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 1px solid #3498db;
                border-radius: 8px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 8px 15px;
                text-align: left;
                font-family: "Microsoft JhengHei";
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-radius: 4px;
            }
        """)

        actions = [
            ("✨ AI 潤飾 (正式)", "rewrite_formal"),
            ("📝 AI 縮寫 (簡潔)", "rewrite_concise"),
            ("🌐 翻譯成英文", "translate_en"),
            ("↩️ 復原原始文字", "undo")
        ]

        for label, act_id in actions:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=act_id: self.on_action(a))
            self.layout.addWidget(btn)

    def on_action(self, action_id):
        self.action_triggered.emit(action_id)
        self.hide()

    def popup(self):
        # Position at current mouse cursor
        pos = QCursor.pos()
        self.move(pos.x() + 5, pos.y() + 5)
        self.show()
        self.raise_()
        self.activateWindow()
