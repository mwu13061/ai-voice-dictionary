# src/ui/repeat_learn_dialog.py
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class RepeatLearnDialog(QDialog):
    """ [A185] Learning Dialog triggered by repeat voice input """
    def __init__(self, raw_text, candidates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📓 發現重複語音 - 是否加入個人詞庫？")
        self.setFixedSize(450, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.raw_text = raw_text
        self.selected_correct = ""
        self.setup_ui(candidates)

    def setup_ui(self, candidates):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"您剛才重複輸入了：\n「{self.raw_text}」", font="bold"))
        layout.addWidget(QLabel("\n這通常代表 AI 聽錯了。請選擇正確的內容："))
        
        self.group = QButtonGroup(self)
        for i, cand in enumerate(candidates):
            rb = QRadioButton(cand)
            self.group.addButton(rb, i)
            layout.addWidget(rb)
        
        # Manual Input
        layout.addWidget(QLabel("\n或是手動輸入正確文字："))
        self.manual_in = QLineEdit()
        layout.addWidget(self.manual_in)
        
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 加入詞庫並修正"); btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton("❌ 忽略"); btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok); btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _on_ok(self):
        # Priority: Manual > Selected
        self.selected_correct = self.manual_in.text().strip()
        if not self.selected_correct:
            btn = self.group.checkedButton()
            if btn: self.selected_correct = btn.text()
            
        if self.selected_correct:
            self.accept()
        else:
            self.reject()
