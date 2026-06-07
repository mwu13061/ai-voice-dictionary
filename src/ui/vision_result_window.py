# src/ui/vision_result_window.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, 
    QPushButton, QHBoxLayout, QApplication, QWidget, QStatusBar, QCheckBox, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QGuiApplication
import pyperclip
from loguru import logger
import os

class AutoExpandingTextEdit(QTextEdit):
    """ [A340] Compact TextEdit that adjusts to content but allows scrolling. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setMinimumHeight(60) # Approx 2 lines
        self.document().contentsChanged.connect(self.update_height)
        self.setStyleSheet("background-color: #2c3e50; border: 1px solid #34495e; color: white; padding: 2px;")

    def update_height(self):
        # Dynamically adjust height up to a reasonable limit, then enable scroll
        doc_height = self.document().size().height()
        new_height = int(doc_height + 10)
        self.setFixedHeight(max(60, min(300, new_height)))

class VisionResultWindow(QDialog):
    """
    [A470] Ultra-Compact & Resizable Vision Tool.
    - Robust content parsing for immediate translation.
    - Cleaned up language list.
    """
    recapture_requested = Signal()
    target_lang_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📸 AI 截圖翻譯助手")
        self.resize(550, 400)
        self.keep_image = False; self.save_dir = ""; self._is_loading_config = False
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #1a252f; color: #ecf0f1; font-family: 'Microsoft JhengHei', 'Segoe UI'; font-size: 9pt; }
            QLabel { font-weight: bold; color: #3498db; }
            QComboBox { background: #2c3e50; color: #f1c40f; border: 1px solid #3498db; padding: 2px; font-weight: bold; }
            QPushButton#action_btn { background-color: #27ae60; color: white; border-radius: 3px; padding: 4px 10px; font-weight: bold; }
            QPushButton#copy_small { background-color: #34495e; color: #bdc3c7; border: 1px solid #3498db; padding: 1px 6px; font-size: 8pt; border-radius: 2px; }
            QStatusBar { color: #f1c40f; font-weight: bold; background: #16212d; font-size: 8pt; min-height: 22px; }
        """)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10, 10, 10, 5); self.main_layout.setSpacing(6)
        
        h_top = QHBoxLayout(); self.btn_recapture = QPushButton("📸 立即擷取螢幕並翻譯"); self.btn_recapture.setObjectName("action_btn"); self.btn_recapture.clicked.connect(self.recapture_requested.emit); h_top.addWidget(self.btn_recapture)
        self.chk_keep = QCheckBox("💾 保留截圖"); self.chk_keep.toggled.connect(self._toggle_keep_image); h_top.addStretch(); h_top.addWidget(self.chk_keep); self.main_layout.addLayout(h_top)
            
        h_u = QHBoxLayout(); h_u.addWidget(QLabel("📄 原始內容：")); h_u.addStretch(); btn_c1 = QPushButton("📋 複製"); btn_c1.setObjectName("copy_small"); btn_c1.clicked.connect(lambda: self._copy(self.orig_text.toPlainText())); h_u.addWidget(btn_c1); self.main_layout.addLayout(h_u)
        self.orig_text = AutoExpandingTextEdit(); self.main_layout.addWidget(self.orig_text)
        
        h_d = QHBoxLayout(); h_d.addWidget(QLabel("🌐 翻譯目標：")); self.lang_cb = QComboBox(); self.lang_cb.addItems(["繁體中文", "简体中文", "English", "日本語", "한국어", "Français", "Deutsch", "Español"]); self.lang_cb.currentTextChanged.connect(self._on_lang_changed); h_d.addWidget(self.lang_cb)
        h_d.addStretch(); btn_c2 = QPushButton("📋 複製翻譯"); btn_c2.setObjectName("copy_small"); btn_c2.clicked.connect(lambda: self._copy(self.res_text.toPlainText())); h_d.addWidget(btn_c2); self.main_layout.addLayout(h_d)
        
        self.res_text = AutoExpandingTextEdit(); self.res_text.setPlaceholderText("等待分析結果..."); self.res_text.setStyleSheet("background-color: #16212d; color: #f1c40f; border: 1px solid #f39c12; padding: 2px;"); self.main_layout.addWidget(self.res_text)
        
        self.status_bar = QStatusBar(); self.status_bar.setFixedHeight(22); self.status_bar.showMessage("就緒"); self.main_layout.addWidget(self.status_bar)

    def _on_lang_changed(self, lang):
        if not self._is_loading_config:
            self.target_lang_changed.emit(lang)
            if self.orig_text.toPlainText().strip(): self.status_bar.showMessage(f"⏳ 正在重新翻譯至 {lang}...", 3000)

    def set_target_lang(self, lang):
        self._is_loading_config = True; self.lang_cb.setCurrentText(lang); self._is_loading_config = False

    def clear_content(self):
        self.orig_text.clear(); self.res_text.clear(); self.status_bar.showMessage("已清空舊內容，就緒")

    def _toggle_keep_image(self, checked):
        if checked:
            d = QFileDialog.getExistingDirectory(self, "選擇截圖儲存位置")
            if d: self.save_dir = d; self.keep_image = True
            else: self.chk_keep.setChecked(False); self.keep_image = False
        else: self.keep_image = False; self.save_dir = ""

    def update_content(self, raw_text):
        """ [A470] Robust parsing for Original/Translated blocks """
        if not raw_text: return
        if "[ORIGINAL]" in raw_text and "[TRANSLATED]" in raw_text:
            parts = raw_text.split("[TRANSLATED]")
            o = parts[0].replace("[ORIGINAL]", "").strip(); t = parts[1].strip()
            self.orig_text.setPlainText(o); self.res_text.setPlainText(t)
        elif "[TRANSLATED]" in raw_text:
            parts = raw_text.split("[TRANSLATED]")
            self.orig_text.setPlainText(parts[0].strip()); self.res_text.setPlainText(parts[1].strip())
        else:
            self.orig_text.setPlainText("AI 未能標註原文，顯示原始回傳："); self.res_text.setPlainText(raw_text)
        self.status_bar.showMessage("✅ 翻譯已就緒", 3000)
        QTimer.singleShot(50, self.adjust_to_content)

    def adjust_to_content(self):
        hint_h = self.sizeHint().height(); self.resize(self.width(), hint_h)

    def _copy(self, text):
        if text:
            pyperclip.copy(text)
            self.status_bar.showMessage("📋 已成功複製到剪貼簿", 2000)
            
            # [A571] Button feedback
            btn = self.sender()
            if isinstance(btn, QPushButton):
                old_text = btn.text()
                btn.setText("✅ 已複製")
                btn.setEnabled(False)
                QTimer.singleShot(1000, lambda: (btn.setText(old_text), btn.setEnabled(True)))

    def show_at_center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                if not self.isVisible(): self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)
            self.show(); self.raise_(); self.activateWindow()
        except: self.show()
