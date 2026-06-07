# src/ui/learning_toast.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QColor, QScreen

class LearningToast(QWidget):
    """
    Interactive Learning Toast [A103]:
    - Precise feedback: [Old] -> [New]
    - Confirm/Undo actions.
    - Premium minimalist UI.
    """
    confirmed = Signal(str, str)
    cancelled = Signal()

    def __init__(self, original, corrected, is_full=False, parent=None):
        super().__init__(parent)
        self.original = original
        self.corrected = corrected
        self.is_full = is_full
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        container = QWidget()
        # Premium dark slate theme
        container.setStyleSheet("""
            QWidget {
                background-color: #1e272e;
                border: 1px solid #3498db;
                border-radius: 20px;
            }
        """)
        c_layout = QHBoxLayout(container)
        
        # Icon
        icon_label = QLabel("✨")
        icon_label.setStyleSheet("border: none; font-size: 16px;")
        c_layout.addWidget(icon_label)
        
        # Message
        msg = f"學習：{self.original} ➔ {self.corrected}"
        if self.is_full:
            msg = f"❗ 詞庫已滿(5/5)，請升級 Pro 以儲存：{self.original} ➔ {self.corrected}"
            
        msg_label = QLabel(msg)
        msg_label.setStyleSheet("color: white; font-family: 'Microsoft JhengHei'; font-size: 13px; border: none;")
        c_layout.addWidget(msg_label)
        
        if not self.is_full:
            # Confirm Button
            confirm_btn = QPushButton("✓ 確認")
            confirm_btn.setStyleSheet("""
                QPushButton { background: #2ecc71; color: white; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #27ae60; }
            """)
            confirm_btn.clicked.connect(self.on_confirm)
            c_layout.addWidget(confirm_btn)
            
            # Undo Button
            undo_btn = QPushButton("↺ 撤銷")
            undo_btn.setStyleSheet("""
                QPushButton { background: #e74c3c; color: white; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #c0392b; }
            """)
            undo_btn.clicked.connect(self.on_cancel)
            c_layout.addWidget(undo_btn)
        else:
            # Upgrade Suggestion Button
            upgrade_btn = QPushButton("💎 升級 Pro")
            upgrade_btn.setStyleSheet("""
                QPushButton { background: #f1c40f; color: black; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #f39c12; }
            """)
            c_layout.addWidget(upgrade_btn)
            
        layout.addWidget(container)
        
        # Auto hide after 8 seconds if no action
        QTimer.singleShot(8000, self.close)

    def on_confirm(self):
        self.confirmed.emit(self.original, self.corrected)
        self.close()
        
    def on_cancel(self):
        self.cancelled.emit()
        self.close()

    def show_at_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        # Bottom right
        self.adjustSize()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60
        self.move(x, y)
        self.show()
        # Premium Sound logic would go here
