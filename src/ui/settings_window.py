# src/ui/settings_window.py
import os, json, sqlite3, shutil, sys, threading, time
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QGroupBox, QDialog, QTabWidget, 
                             QCheckBox, QGridLayout, QListWidget, QFileDialog, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QTextEdit, QListWidgetItem, QFrame, 
                             QSlider, QAbstractItemView, QMenu, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPoint
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QAction
from loguru import logger
from src.utils.path_helper import get_writable_path

CONFIG_PATH = get_writable_path(os.path.join("user_data", "gemini_tool_config.json"))
HW_CHINESE = {"mouse_back": "滑鼠側後退鍵", "mouse_forward": "滑鼠側前進鍵", "mouse_middle": "滑鼠中鍵", 
              "ctrl": "Ctrl", "shift": "Shift", "alt": "Alt", "win": "Win鍵", "enter": "Enter", 
              "space": "空白鍵", "tab": "Tab", "f10": "F10", "f12": "F12"}
MODIFIERS = ["ctrl", "shift", "alt", "win"]

def to_chinese_hk(hk): 
    if not hk: return "未設定"
    return "+".join([HW_CHINESE.get(p, p.upper()) for p in hk.lower().split('+')])

class UnifiedKeyDialog(QDialog):
    """ [A636] RESTORED: Missing Hotkey Configuration Dialog """
    def __init__(self, current_hk, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ 設定組合按鍵")
        self.setFixedSize(550, 650)
        self.selected_mods = []
        self.selected_key = ""
        self.btn_map = {}
        self._parse_hk(current_hk)
        self.setup_ui()
        
    def _parse_hk(self, hk_str):
        if not hk_str: return
        parts = hk_str.lower().split('+')
        for p in parts:
            if p in MODIFIERS: self.selected_mods.append(p)
            else: self.selected_key = p
            
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; color: #ecf0f1; } 
            QGroupBox { border: 1px solid #34495e; color: #3498db; } 
            QPushButton[selected='true'] { background: #f39c12; }
            QPushButton { background: #34495e; border: 1px solid #3498db; color: white; padding: 5px; }
        """)
        layout = QVBoxLayout(self)
        gp = QGroupBox("🤝 直接錄製"); lp = QVBoxLayout(gp)
        self.btn_rec = QPushButton("🔴 開始錄製")
        self.btn_rec.clicked.connect(lambda: self.parent().start_pairing_requested.emit())
        lp.addWidget(self.btn_rec)
        layout.addWidget(gp)
        
        gm = QGroupBox("🎹 手動組合"); lm = QVBoxLayout(gm)
        self.tabs = QTabWidget()
        kg = {
            "控制": ["ctrl", "shift", "alt", "win", "mouse_back", "mouse_forward", "mouse_middle"], 
            "功能": ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"], 
            "字母": [chr(i) for i in range(ord('a'), ord('z')+1)]
        }
        for g, keys in kg.items():
            tab = QWidget(); grid = QGridLayout(tab)
            for i, k in enumerate(keys):
                btn = QPushButton(HW_CHINESE.get(k, k.upper()))
                btn.clicked.connect(lambda checked, v=k: self._toggle(v))
                grid.addWidget(btn, i//4, i%4)
                self.btn_map[k] = btn
            self.tabs.addTab(tab, g)
        lm.addWidget(self.tabs)
        layout.addWidget(gm)
        
        self.lbl_cur = QLabel()
        layout.addWidget(self.lbl_cur)
        
        br = QHBoxLayout()
        bok = QPushButton("✅ 確定"); bok.clicked.connect(self.accept); br.addWidget(bok)
        bcl = QPushButton("掃描清空"); bcl.clicked.connect(self._clear); br.addWidget(bcl)
        layout.addLayout(br)
        self._update()
        
    def _toggle(self, v):
        if v in MODIFIERS:
            if v in self.selected_mods: self.selected_mods.remove(v)
            else: self.selected_mods.append(v)
        else: self.selected_key = v
        self._update()
        
    def _clear(self): 
        self.selected_mods = []
        self.selected_key = ""
        self._update()
        
    def _update(self):
        s = self.result_hk
        self.lbl_cur.setText(f"目前：{to_chinese_hk(s)}")
        for k, b in self.btn_map.items(): 
            b.setProperty("selected", "true" if k in s.split('+') else "false")
            b.style().unpolish(b)
            b.style().polish(b)
            
    def update_captured(self, k): 
        self.selected_mods = []
        self.selected_key = ""
        self._parse_hk(k)
        self._update()
        
    @property
    def result_hk(self):
        p = sorted(list(set(self.selected_mods))) 
        if self.selected_key: p.append(self.selected_key)
        return "+".join(p)

class QuickAddDialog(QDialog):
    add_req = Signal(str, str)
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("📔 快速加入")
        self.setFixedSize(220, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self.setup_ui(initial_text)
        
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def setup_ui(self, initial_text):
        f = QFrame(self); f.setObjectName("MainFrame")
        f.setStyleSheet("""
            QFrame#MainFrame { background: #1a252f; border: 2px solid #3498db; border-radius: 8px; }
            QLabel { color: #f39c12; font-weight: bold; font-size: 8pt; }
            QLineEdit { background: white; color: black; border-radius: 2px; padding: 1px 3px; border: 1px solid #3498db; font-size: 9pt; }
            QPushButton { background: #2ecc71; color: white; font-weight: bold; border-radius: 3px; padding: 3px; font-size: 8pt; }
        """)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(f)
        vl = QVBoxLayout(f); vl.setContentsMargins(5, 5, 5, 5); vl.setSpacing(3)
        
        h_top = QHBoxLayout(); h_top.addWidget(QLabel("✨ 快速新增")); h_top.addStretch()
        b_cls = QPushButton("✕"); b_cls.setFixedSize(16, 16); b_cls.setStyleSheet("background: #e74c3c; border: none;"); b_cls.clicked.connect(self.reject)
        h_top.addWidget(b_cls); vl.addLayout(h_top)
        
        gl = QGridLayout(); gl.setSpacing(3)
        gl.addWidget(QLabel("❌:"), 0, 0); self.in_err = QLineEdit(initial_text); self.in_err.setFixedHeight(20); gl.addWidget(self.in_err, 0, 1)
        gl.addWidget(QLabel("✅:"), 1, 0); self.in_corr = QLineEdit(); self.in_corr.setFixedHeight(20); gl.addWidget(self.in_corr, 1, 1)
        vl.addLayout(gl)
        
        self.btn_add = QPushButton("新增 (Enter)"); self.btn_add.clicked.connect(self._handle_add); vl.addWidget(self.btn_add)
        self.in_corr.setFocus()
        self.in_corr.returnPressed.connect(self._handle_add)
        self.in_err.returnPressed.connect(self._handle_add)

    def _handle_add(self):
        err = self.in_err.text().strip(); corr = self.in_corr.text().strip()
        if err and corr:
            self.add_req.emit(err, corr)
            self.in_err.clear()
            self.in_err.setFocus()

class RefinementDialog(QDialog):
    restore_requested = Signal(str); retry_requested = Signal(str); profile_changed = Signal(int)
    def __init__(self, text, profiles=None, active_idx=0, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.original_text = text; self._drag_pos = None; self.profiles = profiles or []; self.active_idx = active_idx; self.setup_ui()
        p = QCursor.pos(); s = QGuiApplication.primaryScreen().availableGeometry(); self.move(max(s.left(), min(p.x()+15, s.right()-210)), max(s.top(), min(p.y()+15, s.bottom()-150)))
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos: self.move(e.globalPosition().toPoint() - self._drag_pos)
    def setup_ui(self):
        f = QFrame(self); f.setObjectName("MainFrame"); f.setStyleSheet("QFrame#MainFrame{background:#1a252f;border:1px solid #3498db;border-radius:6px;} QPushButton{background:#2c3e50;padding:6px;border-radius:3px;color:white;border:1px solid #3498db;} QLabel{color:#f39c12;font-weight:bold;font-size:9pt;}")
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(f); vl = QVBoxLayout(f)
        h = QHBoxLayout(); self.status = QLabel("⏳ AI 處理中..."); h.addWidget(self.status); h.addStretch()
        b_cls = QPushButton("✕"); b_cls.setFixedWidth(25); b_cls.clicked.connect(self.reject); h.addWidget(b_cls); vl.addLayout(h)
        if self.profiles:
            self.btn_prof = QPushButton(f"📑 方案: {self.profiles[self.active_idx]}"); self.btn_prof.clicked.connect(self._cycle_profile); vl.addWidget(self.btn_prof)
        br = QHBoxLayout(); self.btn_restore = QPushButton("🔙 還原"); self.btn_restore.clicked.connect(lambda: self.restore_requested.emit(self.original_text) or self.accept()); br.addWidget(self.btn_restore); vl.addLayout(br)
    def _cycle_profile(self):
        self.active_idx = (self.active_idx + 1) % len(self.profiles); self.btn_prof.setText(f"📑 方案: {self.profiles[self.active_idx]}"); self.profile_changed.emit(self.active_idx)

class DictionaryManager(QDialog):
    add_req = Signal(str, str); del_req = Signal(str); closed_signal = Signal()
    def __init__(self, i, parent=None, initial_text=""): 
        super().__init__(parent); self.setWindowTitle("📔 個人詞庫管理"); self.setFixedSize(600, 650); self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint); self.all_items = i; self.setup_ui(initial_text)
    def setup_ui(self, initial_text):
        self.setStyleSheet("""QDialog { background: #1a252f; color: #ecf0f1; } QPushButton { background: #2c3e50; border: 1px solid #3498db; color: white; padding: 8px; } QLineEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 3px; padding: 5px; } QListWidget { background: #0d1117; color: #f1c40f; border: 1px solid #3498db; font-size: 10pt; } QListWidget::item { border-bottom: 1px solid #2c3e50; height: 50px; } QListWidget::item:selected { background: #3498db; color: white; }""")
        l = QVBoxLayout(self); l.addWidget(QLabel("📖 詞庫列表 (錯誤音 ➔ 正確字):"))
        self.lw = QListWidget(); self.lw.setViewMode(QListWidget.IconMode); self.lw.setFlow(QListWidget.TopToBottom); self.lw.setWrapping(True); self.lw.setResizeMode(QListWidget.Adjust); self.lw.setMovement(QListWidget.Static); self.lw.setSpacing(2); self.lw.setGridSize(QSize(180, 60)); self.lw.setSelectionMode(QAbstractItemView.SingleSelection); self.lw.itemClicked.connect(self._on_item_clicked); self.upd(self.all_items); l.addWidget(self.lw)
        gh = QHBoxLayout(); self.iw = QLineEdit(); self.iw.setPlaceholderText("❌ 錯誤音"); self.ir = QLineEdit(); self.ir.setPlaceholderText("✅ 正確字"); gh.addWidget(self.iw); gh.addWidget(self.ir); l.addLayout(gh)
        bh = QHBoxLayout(); b_a = QPushButton("➕ 新增詞條"); b_a.clicked.connect(self._add); bh.addWidget(b_a, 2); b_d = QPushButton("🗑️ 刪除選取"); b_d.clicked.connect(self._del_active); bh.addWidget(b_d, 1); l.addLayout(bh)
        b_cl = QPushButton("💾 儲存並關閉"); b_cl.setMinimumHeight(40); b_cl.setStyleSheet("background: #27ae60; font-weight: bold;"); b_cl.clicked.connect(self.close)
        l.addWidget(b_cl)
        
        # [A30] Checkbox to agree sharing wrong word pairs for feedback
        self.chk_share = QCheckBox("🤝 同意匿名回饋我的錯誤字對照，共同提升全球辨識準確度")
        self.chk_share.setChecked(self.parent().raw_config.get("share_dict_feedback", True))
        self.chk_share.toggled.connect(self._toggle_share)
        l.addWidget(self.chk_share)

        if initial_text: self.iw.setText(initial_text); self.ir.setFocus()
    def upd(self, i):
        self.all_items = i
        self.lw.clear(); groups = {}
        for o, c in i: groups.setdefault(c, []).append(o)
        for k in sorted(groups.keys()):
            vars = groups[k]; text = f"{k} ({len(vars)})" if len(vars) > 1 else f"{vars[0]} ➔ {k}"; item = QListWidgetItem(text); item.setData(Qt.UserRole, (k, vars)); item.setTextAlignment(Qt.AlignCenter); self.lw.addItem(item)
    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data and len(data[1]) > 1:
            m = QMenu(self); m.setStyleSheet("background: #2c3e50; color: white;")
            for v in data[1]:
                a = QAction(f"❌ 刪除: {v} ➔ {data[0]}", self); a.triggered.connect(lambda chk=False, ov=v: self._del_specific(ov)); m.addAction(a)
            m.exec(QCursor.pos())
    def _add(self):
        o, c = self.iw.text().strip(), self.ir.text().strip()
        if o and c: self.add_req.emit(o, c); self.iw.clear(); self.ir.clear()
    def _del_active(self):
        if self.lw.currentItem():
            d = self.lw.currentItem().data(Qt.UserRole)
            if d: self._del_specific(d[1][0]) if len(d[1]) == 1 else self._on_item_clicked(self.lw.currentItem())
    def _del_specific(self, o): self.del_req.emit(o)
    def _toggle_share(self, checked):
        self.parent().raw_config["share_dict_feedback"] = checked
        self.parent()._widget_changed()
    def closeEvent(self, e): self.closed_signal.emit(); super().closeEvent(e)

class AppPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 選擇已安裝程式")
        self.setFixedSize(500, 550)
        self.selected_path = ""
        self.all_apps = []
        
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; color: #ecf0f1; }
            QLineEdit { background: white; color: black; border-radius: 4px; padding: 6px; }
            QListWidget { background: #1a252f; color: white; border: 1px solid #3498db; border-radius: 4px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #2c3e50; }
            QListWidget::item:selected { background: #3498db; }
            QPushButton { background: #34495e; border: 1px solid #3498db; color: white; padding: 8px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🔍 輸入關鍵字搜尋已安裝軟體:"))
        self.search_in = QLineEdit()
        self.search_in.textChanged.connect(self._filter)
        layout.addWidget(self.search_in)
        
        self.lw = QListWidget()
        self.lw.setIconSize(QSize(32, 32))
        layout.addWidget(self.lw)
        
        self.status_lbl = QLabel("⏳ 正在掃描系統應用程式...")
        layout.addWidget(self.status_lbl)
        
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 選擇並套用"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ 取消"); btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok); btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)
        
        self.lw.itemDoubleClicked.connect(lambda: self.accept())
        
        threading.Thread(target=self._load_apps, daemon=True).start()

    def _load_apps(self):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        provider = QFileIconProvider()
        paths = []
        
        # 公用開始選單
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        
        # 個人開始選單
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        
                        # 取得系統圖示
                        icon = provider.icon(QFileInfo(full_path))
                        apps_found.append((name, full_path, icon))
        
        apps_found.sort(key=lambda x: x[0].lower())
        
        common_apps = [
            ("📸 截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 剪貼簿歷史記錄 (Win+V)", "system://clipboard")
        ]
        
        final_apps = []
        for name, path in common_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path == "system://clipboard" else path
            icon = provider.icon(QFileInfo(icon_path))
            final_apps.append((name, path, icon))
            
        final_apps.extend(apps_found)
        self.all_apps = final_apps
        
        QTimer.singleShot(0, self._populate_ui)

    def _populate_ui(self):
        self.lw.clear()
        for name, path, icon in self.all_apps:
            item = QListWidgetItem(name)
            item.setIcon(icon)
            item.setData(Qt.UserRole, path)
            self.lw.addItem(item)
        self.status_lbl.setText(f"✅ 掃描完成。共找到 {len(self.all_apps)} 個應用程式。")

    def _filter(self, text):
        text = text.lower().strip()
        self.lw.clear()
        for name, path, icon in self.all_apps:
            if not text or text in name.lower():
                item = QListWidgetItem(name)
                item.setIcon(icon)
                item.setData(Qt.UserRole, path)
                self.lw.addItem(item)

    def accept(self):
        item = self.lw.currentItem()
        if item:
            self.selected_path = item.data(Qt.UserRole)
            super().accept()
        else:
            QMessageBox.warning(self, "提示", "請先選擇一個應用程式。")

class GlobalDictionaryViewer(QDialog):
    """ [A43] Viewer and manager for the synchronized global dictionary """
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 全球共享詞庫管理與編輯")
        self.setFixedSize(550, 600)
        self.setStyleSheet("""
            QDialog { background: #1a252f; color: #ecf0f1; }
            QLabel { color: #f1c40f; font-weight: bold; font-size: 10pt; }
            QListWidget { background: #0d1117; color: #3498db; border: 1px solid #3498db; font-size: 10pt; padding: 5px; }
            QPushButton { background: #2c3e50; border: 1px solid #3498db; color: white; padding: 8px; font-weight: bold; min-height: 30px; border-radius: 4px; }
            QPushButton:hover { background: #34495e; border-color: #2980b9; }
        """)
        
        from src.utils.learning_engine import LearningEngine
        self.engine = LearningEngine()
        
        l = QVBoxLayout(self)
        l.addWidget(QLabel("🌐 全球共享詞庫對照表 (下載自雲端 / 本地暫存)："))
        
        self.lw = QListWidget()
        l.addWidget(self.lw)
        
        # Populate list widget
        self.items_list = list(items)  # list of (orig, corr)
        self.populate_list()
        
        # Buttons layout
        h_ops = QHBoxLayout()
        self.btn_add = QPushButton("➕ 新增詞條")
        self.btn_add.clicked.connect(self.add_new_item)
        h_ops.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("✏️ 編輯選取")
        self.btn_edit.clicked.connect(self.edit_selected)
        h_ops.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("❌ 刪除選取")
        self.btn_delete.clicked.connect(self.delete_selected)
        h_ops.addWidget(self.btn_delete)
        
        l.addLayout(h_ops)
        
        b_close = QPushButton("關閉")
        b_close.clicked.connect(self.accept)
        l.addWidget(b_close)

    def populate_list(self):
        self.lw.clear()
        if not self.items_list:
            item = QListWidgetItem("⚠️ 目前全球共享詞庫為空，或尚未成功從雲端同步。")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled) # Make it unselectable
            self.lw.addItem(item)
        else:
            for orig, corr in sorted(self.items_list, key=lambda x: x[0]):
                item = QListWidgetItem(f"✅ {orig} ➔ {corr}")
                item.setData(Qt.UserRole, (orig, corr))
                self.lw.addItem(item)

    def add_new_item(self):
        dlg = EditPairDialog("", "", self)
        if dlg.exec() == QDialog.Accepted:
            orig = dlg.orig_in.text().strip()
            corr = dlg.corr_in.text().strip()
            if not orig or not corr:
                return
            
            # Check if orig already exists
            for i, (o, c) in enumerate(self.items_list):
                if o == orig:
                    reply = QMessageBox.question(
                        self, "詞條已存在", f"「{orig}」已存在於詞庫中（對應到「{c}」）。是否要將其覆蓋？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.items_list[i] = (orig, corr)
                        self.save_and_refresh()
                    return
            
            self.items_list.append((orig, corr))
            self.save_and_refresh()

    def edit_selected(self):
        selected = self.lw.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇要編輯的項目。")
            return
        item = selected[0]
        data = item.data(Qt.UserRole)
        if not data:
            return
        orig, corr = data
        dlg = EditPairDialog(orig, corr, self)
        if dlg.exec() == QDialog.Accepted:
            new_orig = dlg.orig_in.text().strip()
            new_corr = dlg.corr_in.text().strip()
            if not new_orig or not new_corr:
                return
            
            # Remove old one
            self.items_list = [x for x in self.items_list if x[0] != orig]
            
            # Add new one
            self.items_list.append((new_orig, new_corr))
            self.save_and_refresh()

    def delete_selected(self):
        selected = self.lw.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇要刪除的項目。")
            return
        
        reply = QMessageBox.question(
            self, "確認刪除", "確定要刪除選取的詞條嗎？這將會立即儲存到本地全球詞庫檔案中。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        for item in selected:
            data = item.data(Qt.UserRole)
            if data:
                orig, corr = data
                self.items_list = [x for x in self.items_list if x[0] != orig]
                
        self.save_and_refresh()

    def save_and_refresh(self):
        from src.utils.learning_engine import get_locked_db_path
        import csv
        db_dir = os.path.dirname(get_locked_db_path())
        global_csv_path = os.path.join(db_dir, "global_learning.csv")
        try:
            os.makedirs(os.path.dirname(global_csv_path), exist_ok=True)
            with open(global_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Original', 'Correction'])
                for orig, corr in sorted(self.items_list):
                    writer.writerow([orig, corr])
            self.engine.refresh_cache()
            self.populate_list()
        except Exception as ex:
            QMessageBox.critical(self, "儲存失敗", f"無法儲存至本地 global_learning.csv: {ex}")

class EditPairDialog(QDialog):
    def __init__(self, orig="", corr="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ 編輯語音詞條")
        self.setFixedSize(350, 160)
        self.setStyleSheet("""
            QDialog { background: #2c3e50; color: #ecf0f1; }
            QLabel { color: #f1c40f; font-weight: bold; font-size: 10pt; }
            QLineEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 4px; padding: 5px; font-size: 10pt; }
            QPushButton { background: #34495e; border: 1px solid #3498db; color: white; padding: 8px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #2980b9; }
        """)
        from PySide6.QtWidgets import QFormLayout
        l = QFormLayout(self)
        l.setSpacing(10)
        
        self.orig_in = QLineEdit(orig)
        self.orig_in.setPlaceholderText("例如：在線")
        self.corr_in = QLineEdit(corr)
        self.corr_in.setPlaceholderText("例如：再線")
        
        l.addRow(QLabel("原語音文字 (錯字):"), self.orig_in)
        l.addRow(QLabel("修正後文字 (正字):"), self.corr_in)
        
        btns = QHBoxLayout()
        b_ok = QPushButton("確定")
        b_ok.clicked.connect(self.accept)
        b_cl = QPushButton("取消")
        b_cl.clicked.connect(self.reject)
        btns.addWidget(b_ok)
        btns.addWidget(b_cl)
        l.addRow(btns)

class GlobalDictModeratorDialog(QDialog):
    """ [A46] Global Dictionary Moderation GUI with Rule Check and AI Risk Check """
    log_signal = Signal(str)
    
    def __init__(self, api_key="", model_id="gemini-2.0-flash", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛡️ 全球共享詞庫審核與管理工具")
        self.setMinimumSize(950, 700)
        self.api_key = api_key
        self.model_id = model_id
        
        from src.utils.learning_engine import LearningEngine
        self.engine = LearningEngine()
        self.current_csv_path = ""
        
        self.setStyleSheet("""
            QDialog { background: #1a252f; color: #ecf0f1; }
            QLabel { color: #f1c40f; font-weight: bold; font-size: 10pt; }
            QListWidget { background: #0d1117; color: #3498db; border: 1px solid #3498db; font-size: 10pt; padding: 5px; }
            QPushButton { background: #2c3e50; border: 1px solid #3498db; color: white; padding: 8px; font-weight: bold; min-height: 30px; border-radius: 4px; }
            QPushButton:hover { background: #34495e; border-color: #2980b9; }
            QPushButton:disabled { background: #555; border-color: #777; color: #aaa; }
            QTextEdit { background: #0d1117; color: #2ecc71; border: 1px solid #27ae60; font-family: 'Consolas', monospace; font-size: 9pt; }
        """)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header Section
        lbl_title = QLabel("🛡️ 全球共享詞庫上傳審核面板")
        lbl_title.setStyleSheet("font-size: 14pt; color: #f1c40f; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(
            "提示：此工具為管理員進行全球共享詞庫上傳前的人工審查。\n"
            "本機規則會自動將「單個字」及「非同音字組合」歸類為高風險；您亦可啟動 AI 智慧分類進一步識別惡意或敏感字詞。\n"
            "最後，點擊「儲存並上傳至 GitHub」以正式發佈至全球庫。"
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #bdc3c7; font-size: 9.5pt; line-height: 1.4;")
        layout.addWidget(lbl_desc)
        
        # Path Selector bar
        h_path = QHBoxLayout()
        self.lbl_path = QLabel("待審核檔：未載入 (預設將載入 collected_feedback.csv)")
        self.lbl_path.setStyleSheet("color: #ecf0f1; font-weight: normal;")
        h_path.addWidget(self.lbl_path)
        
        self.btn_load_csv = QPushButton("📥 載入待審核 CSV")
        self.btn_load_csv.clicked.connect(lambda: self.load_csv_file())
        h_path.addWidget(self.btn_load_csv)
        layout.addLayout(h_path)
        
        # Splitter for Low / High Risk lists
        from PySide6.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel (Safe Candidates / Low Risk)
        left_widget = QWidget()
        left_lay = QVBoxLayout(left_widget)
        left_lay.setContentsMargins(0, 0, 0, 0)
        lbl_low_title = QLabel("✅ 安全候選 (低風險 / 將發佈至全球庫)")
        lbl_low_title.setStyleSheet("color: #2ecc71; font-weight: bold;")
        left_lay.addWidget(lbl_low_title)
        
        self.lw_low = QListWidget()
        self.lw_low.setSelectionMode(QAbstractItemView.ExtendedSelection)
        left_lay.addWidget(self.lw_low)
        
        self.btn_to_high = QPushButton("移至高風險 ➡️")
        self.btn_to_high.setStyleSheet("background: #d35400; border-color: #e67e22;")
        self.btn_to_high.clicked.connect(self.move_to_high)
        left_lay.addWidget(self.btn_to_high)
        
        # Right Panel (High Risk / To be reviewed)
        right_widget = QWidget()
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(0, 0, 0, 0)
        lbl_high_title = QLabel("⚠️ 待審查項目 (高風險 / 單字或異音詞)")
        lbl_high_title.setStyleSheet("color: #e74c3c; font-weight: bold;")
        right_lay.addWidget(lbl_high_title)
        
        self.lw_high = QListWidget()
        self.lw_high.setSelectionMode(QAbstractItemView.ExtendedSelection)
        right_lay.addWidget(self.lw_high)
        
        self.btn_to_low = QPushButton("⬅️ 移至低風險")
        self.btn_to_low.setStyleSheet("background: #27ae60; border-color: #2ecc71;")
        self.btn_to_low.clicked.connect(self.move_to_low)
        right_lay.addWidget(self.btn_to_low)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)
        
        # Item operation buttons
        h_ops = QHBoxLayout()
        self.btn_add = QPushButton("➕ 新增詞條")
        self.btn_add.clicked.connect(self.add_new_item)
        h_ops.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("✏️ 編輯選取")
        self.btn_edit.clicked.connect(self.edit_selected)
        h_ops.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("❌ 刪除選取")
        self.btn_delete.clicked.connect(self.delete_selected)
        h_ops.addWidget(self.btn_delete)
        
        self.btn_ai = QPushButton("🤖 啟動 AI 智慧分類")
        self.btn_ai.setStyleSheet("background: #8e44ad; border-color: #9b59b6;")
        self.btn_ai.clicked.connect(self.run_ai_check)
        h_ops.addWidget(self.btn_ai)
        layout.addLayout(h_ops)
        
        # Progress Bar
        from PySide6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #3498db; border-radius: 4px; text-align: center; color: white; background: #0d1117; }
            QProgressBar::chunk { background-color: #3498db; }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status / Log window
        layout.addWidget(QLabel("📋 執行日誌與狀態偵測："))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(120)
        layout.addWidget(self.log_console)
        self.log_signal.connect(self.log_console.append)
        
        # Footer
        h_foot = QHBoxLayout()
        self.btn_export = QPushButton("💾 導出已核准之 CSV")
        self.btn_export.clicked.connect(self.export_approved_csv)
        h_foot.addWidget(self.btn_export)
        
        self.btn_upload = QPushButton("📤 儲存並上傳至 GitHub")
        self.btn_upload.setStyleSheet("background: #27ae60; border-color: #2ecc71; font-size: 11pt; min-height: 35px;")
        self.btn_upload.clicked.connect(self.save_and_upload)
        h_foot.addWidget(self.btn_upload)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.reject)
        h_foot.addWidget(btn_close)
        layout.addLayout(h_foot)
        
        # Auto-load feedback path
        from src.utils.learning_engine import get_locked_db_path
        db_dir = os.path.dirname(get_locked_db_path())
        feedback_path = os.path.join(db_dir, "collected_feedback.csv")
        if os.path.exists(feedback_path):
            self.load_csv_file(feedback_path)
        else:
            self.log("ℹ️ 提示：未偵測到預設 user_data/collected_feedback.csv。請手動載入 CSV。")
            
    def log(self, text):
        # Thread-safe log append via Qt Signal
        self.log_signal.emit(text)
        
    def add_item_to_list(self, list_widget, orig, corr, reason):
        display_text = f"{orig} ➔ {corr}"
        if reason:
            display_text += f" ({reason})"
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, (orig, corr, reason))
        list_widget.addItem(item)
        
    def load_csv_file(self, file_path=None):
        from src.utils.learning_engine import get_locked_db_path
        db_dir = os.path.dirname(get_locked_db_path())
        
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "載入待審查 CSV", db_dir, "CSV 檔案 (*.csv)"
            )
            if not file_path:
                return
                
        self.current_csv_path = file_path
        self.lbl_path.setText(f"待審核檔：{os.path.basename(file_path)}")
        self.log(f"📥 正在載入檔案：{file_path}")
        
        try:
            import csv
            items = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                is_header = False
                if header:
                    h0 = header[0].lower()
                    if any(x in h0 for x in ["orig", "corr", "word", "phrase", "original", "correction"]):
                        is_header = True
                
                if not is_header and header:
                    if len(header) >= 2:
                        orig, corr = header[0].strip(), header[1].strip()
                        if orig and corr:
                            items.append((orig, corr))
                            
                for row in reader:
                    if len(row) >= 2:
                        orig, corr = row[0].strip(), row[1].strip()
                        if orig and corr:
                            items.append((orig, corr))
                            
            # Load existing global dictionary to filter out already-uploaded entries
            existing_global = set()
            global_csv_path = os.path.join(db_dir, "global_learning.csv")
            if os.path.exists(global_csv_path):
                try:
                    with open(global_csv_path, 'r', encoding='utf-8-sig') as gf:
                        g_reader = csv.reader(gf)
                        next(g_reader, None) # Skip header
                        for g_row in g_reader:
                            if len(g_row) >= 2:
                                existing_global.add((g_row[0].strip(), g_row[1].strip()))
                except Exception as ge:
                    logger.warning(f"Failed to read existing global dictionary for filtering: {ge}")

            # Classify
            self.lw_low.clear()
            self.lw_high.clear()
            
            skipped_count = 0
            for orig, corr in items:
                if (orig, corr) in existing_global:
                    skipped_count += 1
                    continue
                    
                is_high_risk = False
                reason = ""
                if len(orig) == 1 or len(corr) == 1:
                    is_high_risk = True
                    reason = "單個字"
                elif not self.engine.is_phonetic_typo(orig, corr):
                    is_high_risk = True
                    reason = "非同音字組合"
                    
                if is_high_risk:
                    self.add_item_to_list(self.lw_high, orig, corr, reason)
                else:
                    self.add_item_to_list(self.lw_low, orig, corr, "")
                    
            log_msg = f"✅ 成功載入 {len(items) - skipped_count} 筆項目！"
            if skipped_count > 0:
                log_msg += f"（自動過濾了 {skipped_count} 筆全球庫已存在之項目）"
            log_msg += f"本機規則篩選結果：安全 {self.lw_low.count()} 筆，高風險 {self.lw_high.count()} 筆。"
            self.log(log_msg)
            
        except Exception as ex:
            self.log(f"❌ 載入檔案失敗: {ex}")
            QMessageBox.critical(self, "錯誤", f"無法讀取 CSV 檔案：{ex}")
            
    def move_to_high(self):
        selected_items = self.lw_low.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            orig, corr, _ = item.data(Qt.UserRole)
            self.lw_low.takeItem(self.lw_low.row(item))
            self.add_item_to_list(self.lw_high, orig, corr, "手動調整")
            
    def move_to_low(self):
        selected_items = self.lw_high.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            orig, corr, _ = item.data(Qt.UserRole)
            self.lw_high.takeItem(self.lw_high.row(item))
            self.add_item_to_list(self.lw_low, orig, corr, "")
            
    def add_new_item(self):
        dlg = EditPairDialog("", "", self)
        if dlg.exec() == QDialog.Accepted:
            orig = dlg.orig_in.text().strip()
            corr = dlg.corr_in.text().strip()
            if not orig or not corr:
                return
            is_high_risk = False
            reason = ""
            if len(orig) == 1 or len(corr) == 1:
                is_high_risk = True
                reason = "單個字"
            elif not self.engine.is_phonetic_typo(orig, corr):
                is_high_risk = True
                reason = "非同音字組合"
                
            if is_high_risk:
                self.add_item_to_list(self.lw_high, orig, corr, reason)
            else:
                self.add_item_to_list(self.lw_low, orig, corr, "")
            self.log(f"➕ 新增詞條：{orig} ➔ {corr}")
            
    def edit_selected(self):
        low_sel = self.lw_low.selectedItems()
        high_sel = self.lw_high.selectedItems()
        if not low_sel and not high_sel:
            QMessageBox.warning(self, "提示", "請先選擇要編輯的項目。")
            return
        target_item = low_sel[0] if low_sel else high_sel[0]
        is_low = bool(low_sel)
        orig, corr, _ = target_item.data(Qt.UserRole)
        
        dlg = EditPairDialog(orig, corr, self)
        if dlg.exec() == QDialog.Accepted:
            new_orig = dlg.orig_in.text().strip()
            new_corr = dlg.corr_in.text().strip()
            if not new_orig or not new_corr:
                return
            is_high_risk = False
            new_reason = ""
            if len(new_orig) == 1 or len(new_corr) == 1:
                is_high_risk = True
                new_reason = "單個字"
            elif not self.engine.is_phonetic_typo(new_orig, new_corr):
                is_high_risk = True
                new_reason = "非同音字組合"
                
            if is_low:
                self.lw_low.takeItem(self.lw_low.row(target_item))
            else:
                self.lw_high.takeItem(self.lw_high.row(target_item))
                
            if is_high_risk:
                self.add_item_to_list(self.lw_high, new_orig, new_corr, new_reason)
            else:
                self.add_item_to_list(self.lw_low, new_orig, new_corr, "")
            self.log(f"✏️ 修改詞條：{orig}➔{corr} 變更為 {new_orig}➔{new_corr}")
            
    def delete_selected(self):
        low_sel = self.lw_low.selectedItems()
        high_sel = self.lw_high.selectedItems()
        if not low_sel and not high_sel:
            QMessageBox.warning(self, "提示", "請先選擇要刪除的項目。")
            return
        for item in low_sel:
            self.lw_low.takeItem(self.lw_low.row(item))
        for item in high_sel:
            self.lw_high.takeItem(self.lw_high.row(item))
        self.log("❌ 已刪除選取的項目。")
        
    def run_ai_check(self):
        if not self.api_key:
            QMessageBox.warning(self, "缺乏 API 金鑰", "⚠️ 請先在設定中輸入有效的 Gemini API Key 才能執行 AI 審查。")
            return
            
        items_to_check = []
        for i in range(self.lw_low.count()):
            item = self.lw_low.item(i)
            orig, corr, _ = item.data(Qt.UserRole)
            items_to_check.append((orig, corr))
        for i in range(self.lw_high.count()):
            item = self.lw_high.item(i)
            orig, corr, _ = item.data(Qt.UserRole)
            items_to_check.append((orig, corr))
            
        if not items_to_check:
            QMessageBox.information(self, "提示", "無任何詞條需要審核。")
            return
            
        self.btn_ai.setEnabled(False)
        self.log("🤖 啟動 AI 智慧分類...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        def worker():
            try:
                from google import genai
                from google.genai import types
                import json
                
                client = genai.Client(api_key=self.api_key)
                batch_size = 50
                results = []
                total_items = len(items_to_check)
                
                for idx in range(0, total_items, batch_size):
                    batch = items_to_check[idx:idx+batch_size]
                    self.log(f"⏳ 正在傳送第 {idx+1} ~ {min(idx+batch_size, total_items)} 筆資料至 Gemini...")
                    
                    system_instruction = (
                        "你是一個語音輸入糾錯詞庫的審核專家。使用者會提供一個以 JSON 格式表示的 (original, correction) 對照表列表。\n"
                        "你的任務是識別是否有「高風險 (High Risk)」的詞條，並將它們分類為 'High' 或 'Low'，且說明高風險的原因。\n"
                        "「高風險」定義如下：\n"
                        "1. 品牌污染或惡意競爭對手注入：包含競爭產品名稱、惡意廣告、推廣網址或品牌污染文字。\n"
                        "2. 敏感、政治、暴力、色情或辱罵性詞彙。\n"
                        "3. 系統命令或快捷鍵巨集（例如 Windows 快速鍵、程式碼、控制指令如 'rm -rf', 'Ctrl+Alt+Del' 等非同音錯字對）。\n"
                        "4. 語意不通、非語音同音錯字的雜亂符號或隨意字元組合。\n"
                        "其餘一般的同音/近音字修正，均屬於「低風險 (Low)」安全候選。\n\n"
                        "請務必回傳一個符合 JSON 格式的陣列，不要有 markdown 區塊包裹（可以直接用 json 回覆），格式如下：\n"
                        "[\n"
                        "  {\"original\": \"原字\", \"correction\": \"修正字\", \"risk\": \"High\" 或 \"Low\", \"reason\": \"原因說明，如果 Low 則空白\"}\n"
                        "]"
                    )
                    
                    user_content = json.dumps([{"original": o, "correction": c} for o, c in batch], ensure_ascii=False)
                    
                    response = client.models.generate_content(
                        model=self.model_id,
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                            response_mime_type="application/json"
                        )
                    )
                    
                    resp_text = response.text.strip()
                    if resp_text.startswith("```json"):
                        resp_text = resp_text[7:]
                    if resp_text.endswith("```"):
                        resp_text = resp_text[:-3]
                    resp_text = resp_text.strip()
                    
                    try:
                        batch_results = json.loads(resp_text)
                        if not isinstance(batch_results, list):
                            batch_results = []
                    except Exception as parse_ex:
                        logger.warning(f"Failed to parse Gemini response: {resp_text}, error: {parse_ex}")
                        batch_results = [{"original": o, "correction": c, "risk": "Low", "reason": ""} for o, c in batch]
                        
                    results.extend(batch_results)
                    progress_val = int(((idx + len(batch)) / total_items) * 100)
                    QTimer.singleShot(0, lambda p=progress_val: self.progress_bar.setValue(p))
                    
                QTimer.singleShot(0, lambda r=results: self.on_ai_check_finished(r))
            except Exception as ex:
                logger.error(f"AI Check Error: {ex}")
                QTimer.singleShot(0, lambda e=str(ex): self.on_ai_check_error(e))
                
        threading.Thread(target=worker, daemon=True).start()
        
    def on_ai_check_finished(self, results):
        self.btn_ai.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log("✅ AI 智慧分類完成！")
        
        ai_map = {}
        for r in results:
            orig = r.get("original", "").strip()
            corr = r.get("correction", "").strip()
            risk = r.get("risk", "Low").strip()
            reason = r.get("reason", "").strip()
            ai_map[(orig, corr)] = (risk, reason)
            
        all_items = []
        for i in range(self.lw_low.count()):
            all_items.append(self.lw_low.item(i).data(Qt.UserRole))
        for i in range(self.lw_high.count()):
            all_items.append(self.lw_high.item(i).data(Qt.UserRole))
            
        self.lw_low.clear()
        self.lw_high.clear()
        
        for orig, corr, old_reason in all_items:
            is_high_risk = False
            reason = ""
            if len(orig) == 1 or len(corr) == 1:
                is_high_risk = True
                reason = "單個字"
            elif not self.engine.is_phonetic_typo(orig, corr):
                is_high_risk = True
                reason = "非同音字組合"
                
            if not is_high_risk:
                ai_risk, ai_reason = ai_map.get((orig, corr), ("Low", ""))
                if ai_risk.lower() == "high":
                    is_high_risk = True
                    reason = f"AI: {ai_reason}" if ai_reason else "AI 高風險"
                    
            if is_high_risk:
                self.add_item_to_list(self.lw_high, orig, corr, reason)
            else:
                self.add_item_to_list(self.lw_low, orig, corr, "")
                
        self.log(f"📊 分類結果：安全候選 {self.lw_low.count()} 筆，待審查項目 {self.lw_high.count()} 筆。")
        
    def on_ai_check_error(self, err):
        self.btn_ai.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log(f"❌ AI 智慧分類失敗: {err}")
        QMessageBox.critical(self, "錯誤", f"AI 檢查過程中發生錯誤：{err}")
        
    def export_approved_csv(self):
        approved_items = []
        for i in range(self.lw_low.count()):
            orig, corr, _ = self.lw_low.item(i).data(Qt.UserRole)
            approved_items.append((orig, corr))
        if not approved_items:
            QMessageBox.warning(self, "提示", "無任何安全候選項目可導出。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "導出已核准之 global_learning.csv", "", "CSV 檔案 (*.csv)"
        )
        if not file_path:
            return
        import csv
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Original', 'Correction'])
                for orig, corr in sorted(approved_items):
                    writer.writerow([orig, corr])
            self.log(f"✅ 已成功導出 {len(approved_items)} 筆項目至 {file_path}")
            QMessageBox.information(self, "導出成功", f"已成功導出至：\n{file_path}")
        except Exception as ex:
            QMessageBox.critical(self, "導出失敗", f"無法導出檔案：{ex}")
            
    def save_and_upload(self):
        approved_items = []
        for i in range(self.lw_low.count()):
            orig, corr, _ = self.lw_low.item(i).data(Qt.UserRole)
            approved_items.append((orig, corr))
        if not approved_items:
            reply = QMessageBox.question(
                self, "確認", "安全候選清單為空。這將會清空全球詞庫主檔。確定要繼續嗎？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        from src.utils.learning_engine import get_locked_db_path
        global_csv_path = os.path.join(os.path.dirname(get_locked_db_path()), "global_learning.csv")
        import csv
        try:
            os.makedirs(os.path.dirname(global_csv_path), exist_ok=True)
            with open(global_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Original', 'Correction'])
                for orig, corr in sorted(approved_items):
                    writer.writerow([orig, corr])
            self.log(f"💾 本地全球詞庫已更新：{global_csv_path} ({len(approved_items)} 筆)")
            self.engine.refresh_cache()
        except Exception as ex:
            QMessageBox.critical(self, "儲存失敗", f"無法儲存至本地 global_learning.csv: {ex}")
            return
            
        self.btn_upload.setEnabled(False)
        self.log("🚀 開始上傳至 GitHub...")
        
        def git_thread():
            try:
                import subprocess
                import os
                
                env = os.environ.copy()
                env["GIT_TERMINAL_PROMPT"] = "0"
                
                def run_git_cmd(args):
                    self.log(f"Executing: {' '.join(args)}")
                    res = subprocess.run(
                        args, cwd=os.getcwd(), capture_output=True, text=True, encoding='utf-8', errors='ignore', env=env
                    )
                    if res.returncode != 0:
                        self.log(f"❌ 命令失敗 (代碼 {res.returncode}):\n{res.stderr}")
                        return False, res.stderr
                    if res.stdout.strip():
                        self.log(res.stdout)
                    return True, res.stdout
                    
                if not os.path.exists(".git"):
                    self.log("⚠️ 當前目錄非 Git 倉庫，正在初始化 Git...")
                    success, _ = run_git_cmd(["git", "init"])
                    if not success:
                        raise Exception("Git 初始化失敗")
                        
                remote_url = "https://github.com/mwu13061/ai-voice-dictionary.git"
                check_remote = subprocess.run(
                    ["git", "remote", "get-url", "origin"], cwd=os.getcwd(), capture_output=True, text=True, env=env
                )
                if check_remote.returncode != 0:
                    self.log("配置 GitHub 遠端倉庫位址...")
                    run_git_cmd(["git", "remote", "add", "origin", remote_url])
                else:
                    current_url = check_remote.stdout.strip()
                    if current_url != remote_url:
                        self.log("更新 GitHub 遠端倉庫位址...")
                        run_git_cmd(["git", "remote", "set-url", "origin", remote_url])
                        
                run_git_cmd(["git", "add", "user_data/global_learning.csv"])
                status_res = subprocess.run(
                    ["git", "status", "--porcelain", "user_data/global_learning.csv"], cwd=os.getcwd(), capture_output=True, text=True
                )
                if status_res.stdout.strip():
                    run_git_cmd(["git", "commit", "-m", f"Update global dictionary: {len(approved_items)} items"])
                else:
                    self.log("ℹ️ 檔案內容無變更，無需 Commit。")
                    
                self.log("正在推送檔案至 GitHub (這可能需要幾秒鐘)...")
                success, err_msg = run_git_cmd(["git", "push", "origin", "main"])
                if not success:
                    self.log("嘗試推送至 master 分支...")
                    success, err_msg = run_git_cmd(["git", "push", "origin", "master"])
                    
                if success:
                    self.log("🎉 上傳成功！全球詞庫已成功推送至 GitHub 倉庫。")
                    QTimer.singleShot(0, lambda: QMessageBox.information(
                        self, "上傳成功", "🎉 全球共享詞庫已成功儲存並上傳至 GitHub 倉庫！"
                    ))
                else:
                    self.log("\n⚠️ 提示：自動推送失敗，這可能是因為您尚未在 Git 中配置憑證（GitHub 密碼/Token）。")
                    self.log("但本地已成功更新，您可以隨時在命令列中手動推送：")
                    self.log("  git push origin main\n")
                    QTimer.singleShot(0, lambda: QMessageBox.warning(
                        self, "推送失敗",
                        "本地 global_learning.csv 已更新並 Commit！\n\n"
                        "但推送至 GitHub 失敗。這通常是由於 GitHub 身份驗證限制所致。\n"
                        "您可以依照日誌區的提示，手動在終端機中執行 'git push' 進行驗證。"
                    ))
            except Exception as e:
                self.log(f"❌ 上傳過程中發生錯誤: {e}")
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "上傳錯誤", f"上傳過程中發生錯誤：{e}"))
            QTimer.singleShot(0, lambda: self.btn_upload.setEnabled(True))
            
        threading.Thread(target=git_thread, daemon=True).start()

class MacroEditorDialog(QDialog):
    def __init__(self, n="", t="text", v="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ 編輯自定義按鈕")
        self.setFixedSize(520, 600)
        self.setStyleSheet("""
            QDialog { background: #2c3e50; color: #ecf0f1; } 
            QLineEdit, QTextEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 4px; padding: 5px; } 
            QRadioButton { color: #ecf0f1; font-weight: bold; }
            QPushButton { background: #34495e; border: 2px solid #3498db; color: white; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background: #2980b9; }
        """)
        self.is_rec = False
        self._init_done = False
        self._populating = False
        l = QVBoxLayout(self)
        l.setSpacing(8)
        
        # 1. Name input
        l.addWidget(QLabel("📝 按鈕顯示名稱:"))
        self.name_in = QLineEdit(n)
        self.name_in.setPlaceholderText("例如：剪圖、小畫家、我的常用文字...")
        l.addWidget(self.name_in)
        
        l.addSpacing(5)
        
        # 2. Execution Type selection
        l.addWidget(QLabel("⚡ 選擇按鈕執行類型 (單選):"))
        
        # Group radio buttons inside a nice frame with borders or background
        type_frame = QFrame()
        type_frame.setStyleSheet("QFrame { background: #1a252f; border: 1px solid #34495e; border-radius: 6px; padding: 10px; } QLabel { border: none; background: transparent; } QRadioButton { border: none; background: transparent; }")
        tf_layout = QVBoxLayout(type_frame)
        tf_layout.setSpacing(6)
        tf_layout.setContentsMargins(10, 8, 10, 8)
        
        self.type_group = QButtonGroup(self)
        
        self.r_text = QRadioButton("💬 常用文字輸入 (自動打字貼上)")
        self.r_keys = QRadioButton("⌨️ 模擬鍵盤組合鍵 (快捷鍵)")
        self.r_sys = QRadioButton("💻 啟動系統內建工具 (截圖、小畫家...)")
        self.r_app = QRadioButton("🚀 啟動自定義軟體或檔案 (本機應用程式)")
        
        self.type_group.addButton(self.r_text, 0)
        self.type_group.addButton(self.r_keys, 1)
        self.type_group.addButton(self.r_sys, 2)
        self.type_group.addButton(self.r_app, 3)
        
        lbl_text_desc = QLabel("💡 說明：點擊按鈕時，直接在目前的游標焦點處輸入您設定的常用文字、句子或範本（免去重複打字）。")
        lbl_text_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_text_desc.setWordWrap(True)
        
        lbl_keys_desc = QLabel("💡 說明：點擊按鈕時，模擬按下一組鍵盤快捷鍵（例如複製 Ctrl+C、重做 Ctrl+Y 等）。")
        lbl_keys_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_keys_desc.setWordWrap(True)
        
        lbl_sys_desc = QLabel("💡 說明：點擊按鈕時，直接開啟 Windows 內建的工具，如系統截圖、小畫家、計算機、螢幕鍵盤等。")
        lbl_sys_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_sys_desc.setWordWrap(True)
        
        lbl_app_desc = QLabel("💡 說明：點擊按鈕時，開啟您自行設定的本機常用應用程式、檔案、路徑或網頁。")
        lbl_app_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_app_desc.setWordWrap(True)
        
        tf_layout.addWidget(self.r_text)
        tf_layout.addWidget(lbl_text_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_keys)
        tf_layout.addWidget(lbl_keys_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_sys)
        tf_layout.addWidget(lbl_sys_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_app)
        tf_layout.addWidget(lbl_app_desc)
        
        l.addWidget(type_frame)
        
        l.addSpacing(5)
        
        # 3. Value editor block
        self.t_lbl = QLabel("🔧 設定內容:")
        l.addWidget(self.t_lbl)
        
        self.val_text = QTextEdit(v if t == "text" else "")
        self.val_text.setPlaceholderText("請輸入您想要自動輸入 the 文字、範本或段落...")
        l.addWidget(self.val_text)
        
        kh = QHBoxLayout()
        self.val_keys = QLineEdit(v if t == "combo" else "")
        self.val_keys.setPlaceholderText("點擊右側按鈕開始錄製組合鍵...")
        self.btn_rec = QPushButton("🔴 錄製按鍵")
        self.btn_rec.clicked.connect(self._toggle_rec)
        kh.addWidget(self.val_keys)
        kh.addWidget(self.btn_rec)
        l.addLayout(kh)
        
        self.sys_combo = QComboBox()
        self.sys_combo.setIconSize(QSize(20, 20))
        self.sys_combo.setStyleSheet("QComboBox { background: white; color: black; padding: 5px; border-radius: 4px; }")
        l.addWidget(self.sys_combo)
        
        self.app_layout = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.setIconSize(QSize(20, 20))
        self.app_combo.setStyleSheet("QComboBox { background: white; color: black; padding: 5px; border-radius: 4px; }")
        self.btn_browse = QPushButton("📁 瀏覽檔案")
        self.btn_browse.clicked.connect(self._browse_app)
        self.app_layout.addWidget(self.app_combo, 1)
        self.app_layout.addWidget(self.btn_browse)
        l.addLayout(self.app_layout)
        
        # Populate sys_combo
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        provider = QFileIconProvider()
        sys_apps = [
            ("📸 系統截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 系統小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 系統計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 系統記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 系統螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 系統剪貼簿歷史記錄 (Win+V)", "system://clipboard"),
            ("📂 系統檔案總管 (explorer.exe)", "explorer.exe"),
            ("⚙️ 系統設定 (ms-settings:)", "ms-settings:")
        ]
        for name, path in sys_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path in ["system://clipboard", "ms-settings:"] else path
            icon = provider.icon(QFileInfo(icon_path))
            self.sys_combo.addItem(icon, name, path)
            
        # Connect radio buttons selection change
        self.r_text.toggled.connect(self._sync)
        self.r_keys.toggled.connect(self._sync)
        self.r_sys.toggled.connect(self._sync)
        self.r_app.toggled.connect(self._sync)
        
        # Auto-fill name signals
        self.sys_combo.currentIndexChanged.connect(lambda: self._auto_fill_name("sys"))
        self.app_combo.currentIndexChanged.connect(lambda: self._auto_fill_name("app"))
        self.r_sys.toggled.connect(lambda checked: checked and self._auto_fill_name("sys"))
        self.r_app.toggled.connect(lambda checked: checked and self._auto_fill_name("app"))
        
        # Initial selection mapping
        idx = 0
        sys_match_idx = -1
        if t == "combo":
            idx = 1
        elif t == "app":
            # Check if it matches any system app path
            for i in range(self.sys_combo.count()):
                if self.sys_combo.itemData(i) and v and self.sys_combo.itemData(i).lower() == v.lower():
                    sys_match_idx = i
                    break
            if sys_match_idx != -1:
                idx = 2
            else:
                idx = 3
                
        if idx == 0: self.r_text.setChecked(True)
        elif idx == 1: self.r_keys.setChecked(True)
        elif idx == 2:
            self.r_sys.setChecked(True)
            self.sys_combo.setCurrentIndex(sys_match_idx)
        elif idx == 3: self.r_app.setChecked(True)
        
        self._sync()
        
        l.addSpacing(10)
        b_ok = QPushButton("✅ 確定儲存")
        b_ok.clicked.connect(self.accept)
        l.addWidget(b_ok)
        
        # Initialize self._last_autofilled_name
        self._last_autofilled_name = ""
        if idx == 2 and sys_match_idx != -1:
            self._last_autofilled_name = self._clean_app_name(self.sys_combo.itemText(sys_match_idx))
        elif idx == 3 and v:
            self._last_autofilled_name = self._clean_app_name(os.path.basename(v))

        self._init_done = True
        
        # Check if parent has pre-scanned cached apps list
        apps = []
        if parent and hasattr(parent, 'cached_apps') and parent.cached_apps:
            apps = parent.cached_apps
            
        if apps:
            self._populate_combo(apps, v if (t == "app" and idx == 3) else "")
        else:
            self.app_combo.addItem("⏳ 正在掃描系統應用程式...", "")
            threading.Thread(target=self._scan_apps_for_combo, args=(v if (t == "app" and idx == 3) else "",), daemon=True).start()
            
    def _sync(self): 
        idx = self.type_group.checkedId()
        self.val_text.setVisible(idx == 0)
        self.val_keys.setVisible(idx == 1)
        self.btn_rec.setVisible(idx == 1)
        self.sys_combo.setVisible(idx == 2)
        self.app_combo.setVisible(idx == 3)
        self.btn_browse.setVisible(idx == 3)
        
    def _scan_apps_for_combo(self, initial_val=""):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        provider = QFileIconProvider()
        paths = []
        
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        icon = provider.icon(QFileInfo(full_path))
                        apps_found.append((name, full_path, icon))
                        
        apps_found.sort(key=lambda x: x[0].lower())
        
        common_apps = [
            ("📸 截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 剪貼簿歷史記錄 (Win+V)", "system://clipboard")
        ]
        
        final_apps = []
        for name, path in common_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path == "system://clipboard" else path
            icon = provider.icon(QFileInfo(icon_path))
            final_apps.append((name, path, icon))
            
        final_apps.extend(apps_found)
        
        if self.parent() and hasattr(self.parent(), "cached_apps"):
            self.parent().cached_apps = final_apps
            
        QTimer.singleShot(0, lambda: self._populate_combo(final_apps, initial_val))

    def _populate_combo(self, apps, initial_val=""):
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        self._populating = True
        try:
            self.app_combo.clear()
            self.app_combo.addItem("--- 請選擇本機軟體 ---", "")
            
            found_idx = 0
            for name, path, icon in apps:
                self.app_combo.addItem(icon, name, path)
                if initial_val and path.lower() == initial_val.lower():
                    found_idx = self.app_combo.count() - 1
                    
            if initial_val and found_idx == 0:
                provider = QFileIconProvider()
                icon = provider.icon(QFileInfo(initial_val))
                name = os.path.basename(initial_val)
                self.app_combo.addItem(icon, name, initial_val)
                found_idx = self.app_combo.count() - 1
                
            self.app_combo.setCurrentIndex(found_idx)
        finally:
            self._populating = False

    def _browse_app(self):
        p, _ = QFileDialog.getOpenFileName(self, "選擇要啟動的程式或檔案", "", "All Files (*.*)")
        if p:
            from PySide6.QtWidgets import QFileIconProvider
            from PySide6.QtCore import QFileInfo
            provider = QFileIconProvider()
            icon = provider.icon(QFileInfo(p))
            name = os.path.basename(p)
            
            for idx in range(self.app_combo.count()):
                if self.app_combo.itemData(idx) == p:
                    self.app_combo.setCurrentIndex(idx)
                    return
                    
            self.app_combo.addItem(icon, name, p)
            self.app_combo.setCurrentIndex(self.app_combo.count() - 1)
            
    def _toggle_rec(self):
        if not self.is_rec:
            self.is_rec = True
            self.btn_rec.setText("⏹️ 停止並追加")
            self.btn_rec.setStyleSheet("background: #e74c3c; border: 2px solid white;")
            if hasattr(self.parent(), 'start_pairing_requested'): 
                self.parent().start_pairing_requested.emit()
        else:
            self.is_rec = False
            self.btn_rec.setText("🔴 錄製按鍵")
            self.btn_rec.setStyleSheet("")
            if hasattr(self.parent(), 'stop_pairing_requested'):
                self.parent().stop_pairing_requested.emit()
                
    def update_captured(self, k): 
        cur = self.val_keys.text().strip()
        self.val_keys.setText(f"{cur}, {k}" if cur else k)
        self.val_keys.setStyleSheet("background: #2ecc71; color: white;")
        QTimer.singleShot(200, lambda: self.val_keys.setStyleSheet(""))
        
    def get_data(self): 
        idx = self.type_group.checkedId()
        t = "text"
        if idx == 1: t = "combo"
        elif idx in [2, 3]: t = "app"
        
        val = ""
        if idx == 0: val = self.val_text.toPlainText()
        elif idx == 1: val = self.val_keys.text()
        elif idx == 2: val = self.sys_combo.itemData(self.sys_combo.currentIndex()) or ""
        elif idx == 3: val = self.app_combo.itemData(self.app_combo.currentIndex()) or ""
        
        return self.name_in.text(), t, val

    def _clean_app_name(self, name: str) -> str:
        import re
        import os
        
        # 1. If it looks like a path, get the base name
        if "\\" in name or "/" in name:
            name = os.path.basename(name)
            
        # 2. Remove file extension first (case-insensitive)
        name = re.sub(r'\.(exe|lnk|app|bat|cmd|sh)$', '', name, flags=re.IGNORECASE)
        
        # 3. Remove parenthesized text (like "(calc.exe)")
        name = re.sub(r'[\(（].*?[\)）]', '', name)
        
        # 4. Remove emojis and symbols, keeping only letters, numbers, Chinese characters, spaces, dashes, underscores
        name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\-_]', '', name)
        name = name.strip()
        
        # 5. Remove common prefixes
        if name.startswith("系統"):
            name = name[2:]
        elif name.startswith("本機"):
            name = name[2:]
            
        return name.strip()

    def _auto_fill_name(self, source_type=None):
        if not getattr(self, "_init_done", False) or getattr(self, "_populating", False):
            return
            
        idx = self.type_group.checkedId()
        if source_type == "sys" and idx != 2:
            return
        if source_type == "app" and idx != 3:
            return
            
        text = ""
        if idx == 2:
            text = self.sys_combo.currentText()
        elif idx == 3:
            text = self.app_combo.currentText()
            if text == "--- 請選擇本機軟體 ---" or text == "⏳ 正在掃描系統應用程式...":
                text = ""
                
        if not text:
            return
            
        new_clean = self._clean_app_name(text)
        if not new_clean:
            return
            
        current_name = self.name_in.text().strip()
        last_auto = getattr(self, "_last_autofilled_name", "")
        
        if not current_name or current_name == last_auto:
            self.name_in.setText(new_clean)
            self._last_autofilled_name = new_clean

class MagicItemWidget(QWidget):
    del_req = Signal()
    edit_req = Signal()
    vis_changed = Signal(bool)
    def __init__(self, n, v, b, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 2, 5, 2)
        self.chk = QCheckBox()
        self.chk.setChecked(v)
        self.chk.toggled.connect(self.vis_changed.emit)
        l.addWidget(self.chk)
        self.lbl = QLabel(n)
        self.lbl.setStyleSheet("font-weight: bold;")
        l.addWidget(self.lbl)
        l.addStretch()
        if not b:
            b_ed = QPushButton("📝")
            b_ed.setFixedSize(35, 35)
            b_ed.setStyleSheet("border: 2px solid #3498db; background: #34495e;")
            b_ed.clicked.connect(self.edit_req.emit)
            l.addWidget(b_ed)
            b_de = QPushButton("✕")
            b_de.setFixedSize(35, 35)
            b_de.setStyleSheet("color: #e74c3c; border: 2px solid #e74c3c; background: #34495e;")
            b_de.clicked.connect(self.del_req.emit)
            l.addWidget(b_de)
        h = QLabel("≡")
        h.setStyleSheet("font-size: 18pt; color: #7f8c8d;")
        l.addWidget(h)

class ProfileManager(QDialog):
    def __init__(self, profiles, active_idx, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ AI 提示詞最佳化方案管理員")
        self.setFixedSize(700, 500)
        self.profiles = [p.copy() for p in profiles]
        self.active_idx = active_idx
        self._is_loading = False
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        layout = QVBoxLayout(self)
        main_h = QHBoxLayout()
        left_f = QVBoxLayout()
        left_f.addWidget(QLabel("方案清單 (請在主頁面切換):"))
        self.list_w = QListWidget()
        self.list_w.setStyleSheet("background: #34495e; color: white;")
        for p in self.profiles: 
            self.list_w.addItem(p["name"])
        left_f.addWidget(self.list_w)
        btn_add = QPushButton("➕ 新增方案")
        btn_add.clicked.connect(self._add)
        btn_del = QPushButton("🗑️ 刪除方案")
        btn_del.clicked.connect(self._del)
        left_f.addWidget(btn_add)
        left_f.addWidget(btn_del)
        main_h.addLayout(left_f, 1)
        
        right_f = QVBoxLayout()
        right_f.addWidget(QLabel("方案名稱:"))
        self.name_in = QLineEdit()
        self.name_in.textChanged.connect(self._auto_save_current)
        right_f.addWidget(self.name_in)
        right_f.addWidget(QLabel("AI 修飾規則指令:"))
        self.prompt_in = QTextEdit()
        self.prompt_in.textChanged.connect(self._auto_save_current)
        right_f.addWidget(self.prompt_in)
        main_h.addLayout(right_f, 2)
        
        layout.addLayout(main_h)
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 完成並套用")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
        
        self.list_w.currentRowChanged.connect(self._load_current)
        if self.profiles: 
            self.list_w.setCurrentRow(self.active_idx)

    def _load_current(self, idx):
        if 0 <= idx < len(self.profiles):
            self._is_loading = True
            self.name_in.setText(self.profiles[idx]["name"])
            self.prompt_in.setPlainText(self.profiles[idx]["prompt"])
            self._is_loading = False

    def _add(self):
        self.profiles.append({"name": "新方案", "prompt": "請修飾內容："})
        self.list_w.addItem("新方案")
        self.list_w.setCurrentRow(len(self.profiles) - 1)

    def _del(self):
        idx = self.list_w.currentRow()
        if idx >= 0 and len(self.profiles) > 1:
            self.profiles.pop(idx)
            self.list_w.takeItem(idx)
            self.list_w.setCurrentRow(0)

    def _auto_save_current(self):
        if self._is_loading: return
        idx = self.list_w.currentRow()
        if idx >= 0:
            self.profiles[idx]["name"] = self.name_in.text()
            self.profiles[idx]["prompt"] = self.prompt_in.toPlainText()
            self.list_w.item(idx).setText(self.name_in.text())

class SettingsWindow(QWidget):
    settings_changed = Signal(dict)
    preview_ui_requested = Signal()
    preview_sound_requested = Signal(int)
    clear_dict_requested = Signal()
    add_dict_requested = Signal(str, str)
    del_dict_requested = Signal(str)
    launch_vision_requested = Signal()
    ready_signal = Signal(str)
    models_scanned_signal = Signal(list)
    import_dict_requested = Signal(str)
    start_pairing_requested = Signal()
    stop_pairing_requested = Signal()
    
    def __init__(self):
        super().__init__(); self.dict_dlg = None; self.quick_add_dlg = None; self.raw_config = {}; self.dict_items = []
        self.cached_apps = []
        threading.Thread(target=self._pre_scan_apps, daemon=True).start()
        self.setWindowTitle("AI 助手系統設定 (Build [A1002])"); self.setFixedWidth(480); self.setStyleSheet("""QWidget { background: #1a252f; color: #ecf0f1; font-family: 'Microsoft JhengHei'; } QTabWidget::pane { border: 1px solid #34495e; background: #2c3e50; } QTabBar::tab { background: #34495e; color: #bdc3c7; padding: 8px 12px; } QTabBar::tab:selected { background: #3498db; color: white; } QGroupBox { border: 2px solid #34495e; margin-top: 8px; padding-top: 8px; color: #3498db; font-weight: bold; } QComboBox, QLineEdit, QTextEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 3px; padding: 4px; } QPushButton { background: #34495e; border: 2px solid #3498db; color: white; padding: 8px; font-weight: bold; } QCheckBox { font-weight: bold; }""")
        self._save_timer = QTimer(); self._save_timer.setSingleShot(True); self._save_timer.setInterval(500); self._save_timer.timeout.connect(self._do_save); self.models_scanned_signal.connect(self._on_models_discovered); self.setup_ui(); self.load_settings()

    def _pre_scan_apps(self):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        provider = QFileIconProvider()
        paths = []
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        try:
                            icon = provider.icon(QFileInfo(full_path))
                            apps_found.append((name, full_path, icon))
                        except: pass
        apps_found.sort(key=lambda x: x[0].lower())
        self.cached_apps = apps_found

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self); self.tabs = QTabWidget(); self.main_layout.addWidget(self.tabs)
        
        # Tab 1: 設定
        t1 = QWidget(); l1 = QVBoxLayout(t1)
        l1.setContentsMargins(12, 10, 12, 10)
        l1.setSpacing(8)
        
        # 1. 啟動與核心設定
        gs = QGroupBox("🧠 啟動與核心設定"); ls = QVBoxLayout(gs)
        ls.setContentsMargins(12, 10, 12, 10); ls.setSpacing(8)
        self.chk_auto_start = QCheckBox("隨電腦開機自動啟動助手")
        self.chk_smart_left = QCheckBox("🖱️ 啟用左鍵長按啟動語音輸入")
        self.chk_smart_right = QCheckBox("🔮 啟用右鍵長按顯示魔法選單")
        self.chk_use_punc = QCheckBox("啟用自動輸入標點")
        ls.addWidget(self.chk_auto_start)
        ls.addWidget(self.chk_smart_left)
        ls.addWidget(self.chk_smart_right)
        ls.addWidget(self.chk_use_punc)
        l1.addWidget(gs)
        
        # Row layout for side-by-side GroupBoxes
        row_modes = QHBoxLayout()
        row_modes.setSpacing(8)
        
        # 2. 語音輸入設定
        go = QGroupBox("語音輸入設定"); lo = QVBoxLayout(go)
        lo.setContentsMargins(10, 8, 10, 8); lo.setSpacing(12)
        
        self.smart_hold_combo = QComboBox()
        self.smart_hold_combo.addItems(["啟動久按時間 0.3s", "啟動久按時間 0.5s", "啟動久按時間 0.8s", "啟動久按時間 1.0s", "啟動久按時間 1.5s"])
        lo.addWidget(self.smart_hold_combo)
        
        self.rec_mode_cb = QComboBox()
        self.rec_mode_cb.addItems(["📞 對講機模式", "🔘 開關模式 (久按開/停止發話關)", "🔘 開關模式 (久按開/久按關)"])
        lo.addWidget(self.rec_mode_cb)
        
        self.output_mode_cb = QComboBox()
        self.output_mode_cb.addItems(["🚀 極速貼上", "🎹 打字機模式"])
        lo.addWidget(self.output_mode_cb)
        row_modes.addWidget(go)
        
        # 3. 快速鍵語音輸入設定
        ghk = QGroupBox("快速鍵語音輸入設定"); lh = QVBoxLayout(ghk)
        lh.setContentsMargins(10, 8, 10, 8); lh.setSpacing(6)
        self.hk_disp = QLabel("啟動語音輸入：")
        self.btn_hk = QPushButton("🔧 修改按鍵組合")
        self.btn_hk.clicked.connect(lambda: self.open_key_dialog("hotkey"))
        self.m_hk_disp = QLabel("啟動魔法選單：")
        self.btn_mhk = QPushButton("🔧 修改按鍵組合")
        self.btn_mhk.clicked.connect(lambda: self.open_key_dialog("magic_hotkey"))
        lh.addWidget(self.hk_disp)
        lh.addWidget(self.btn_hk)
        lh.addWidget(self.m_hk_disp)
        lh.addWidget(self.btn_mhk)
        row_modes.addWidget(ghk)
        
        l1.addLayout(row_modes)
        
        # 4. 啟動語音輸入風格
        ga = QGroupBox("啟動語音輸入風格"); la = QVBoxLayout(ga)
        la.setContentsMargins(12, 10, 12, 10); la.setSpacing(6)
        la.addWidget(QLabel("音效提醒風格："))
        self.sound_sel = QComboBox()
        self.sound_sel.addItems(["🫥 無提醒", "現代電子", "經典鈴聲", "沉穩鼓點", "科技掃描", "清脆警告", "柔和水滴", "數位通訊", "機械卡鎖", "未來科幻", "極簡提示"])
        la.addWidget(self.sound_sel)
        
        la.addWidget(QLabel("圖像提醒風格："))
        self.vis_style_cb = QComboBox()
        self.vis_style_cb.addItems(["🫥 無提醒", "💬 固定位置氣泡提醒", "✨ 跟隨遊標位置氣泡提醒"])
        la.addWidget(self.vis_style_cb)
        
        b_pos = QPushButton("📍 調整氣泡球固定位置")
        b_pos.clicked.connect(self.preview_ui_requested.emit)
        la.addWidget(b_pos)
        l1.addWidget(ga)
        
        # [A5] Compatibility variables for configuration sync without cluttering UI
        self.chk_audio_cue = QCheckBox()
        self.sound_sel.currentIndexChanged.connect(lambda idx: self.chk_audio_cue.setChecked(idx != 0))
        
        l1.addStretch()
        self.tabs.addTab(t1, "⚡ 設定")
        
        # Tab 2: 🪄 魔法選單
        tm = QWidget(); lm = QVBoxLayout(tm); lm.setContentsMargins(10,10,10,10)
        self.lw_mag = QListWidget()
        self.lw_mag.setDragDropMode(QListWidget.InternalMove)
        self.lw_mag.model().rowsMoved.connect(self._reorder)
        lm.addWidget(QLabel("選單管理 (≡ 拖拽排序 / 勾選隱藏):"))
        lm.addWidget(self.lw_mag)
        b_add_m = QPushButton("➕ 新增自定義按鈕")
        b_add_m.clicked.connect(self._add_macro)
        lm.addWidget(b_add_m)
        self.tabs.addTab(tm, "🪄 魔法選單")
        
        # Tab 3: Pro
        tp = QWidget(); lp = QVBoxLayout(tp)
        self.api_in = QLineEdit(); self.api_in.setEchoMode(QLineEdit.Password)
        lp.addWidget(QLabel("Gemini API Key:")); lp.addWidget(self.api_in)
        self.opt_m = QComboBox(); self.opt_m.setEditable(True)
        self.vis_m = QComboBox(); self.vis_m.setEditable(True)
        self.fix_m = QComboBox(); self.fix_m.setEditable(True)
        lp.addWidget(QLabel("✨ 1. 提示詞優化模型:"))
        lp.addWidget(self.opt_m)
        lp.addWidget(QLabel("📸 2. 截圖翻譯模型:"))
        lp.addWidget(self.vis_m)
        lp.addWidget(QLabel("🧠 3. 語音聽寫糾正模型:"))
        lp.addWidget(self.fix_m)
        b_chk = QPushButton("🔍 查詢模型清單"); b_chk.clicked.connect(self._check_models); lp.addWidget(b_chk)
        self.prof_cb = QComboBox()
        lp.addWidget(QLabel("AI 修改方案:"))
        lp.addWidget(self.prof_cb)
        b_p = QPushButton("⚙️ AI 提示詞管理"); b_p.clicked.connect(self.open_profile_manager); lp.addWidget(b_p)
        b_d = QPushButton("📔 個人詞庫管理"); b_d.clicked.connect(self.open_dict_manager); lp.addWidget(b_d)
        b_v = QPushButton("📸 截圖翻譯助手"); b_v.clicked.connect(self.launch_vision_requested.emit); lp.addWidget(b_v)
        lp.addStretch()
        
        # [A31] Symmetrical Export & Import buttons on the same row, half size, at the very bottom
        h_io = QHBoxLayout()
        b_exp = QPushButton("📤 匯出自定義")
        b_exp.setStyleSheet("font-size: 9pt; padding: 6px;")
        b_exp.clicked.connect(self.export_user_data)
        b_imp = QPushButton("📥 匯入自定義")
        b_imp.setStyleSheet("font-size: 9pt; padding: 6px;")
        b_imp.clicked.connect(self.import_user_data)
        h_io.addWidget(b_exp)
        h_io.addWidget(b_imp)
        lp.addLayout(h_io)
        
        self.tabs.addTab(tp, "💎 Pro")
        
        # Tab 4: 工程
        te = QWidget(); le = QVBoxLayout(te)
        self.eng_cb = QComboBox(); self.eng_cb.addItems(["SenseVoice (極速版)", "V1 傳統版 (含本地 LLM)"])
        le.addWidget(QLabel("辨識引擎:")); le.addWidget(self.eng_cb)
        
        # Sensitivity Section
        h_sens = QHBoxLayout()
        h_sens.addWidget(QLabel("語音啟動靈敏度:"))
        self.vad_val_lbl = QLabel("50")
        self.vad_val_lbl.setStyleSheet("font-weight: bold; color: #3498db;")
        h_sens.addStretch()
        h_sens.addWidget(self.vad_val_lbl)
        le.addLayout(h_sens)
        
        self.vad_sl = QSlider(Qt.Horizontal); self.vad_sl.setRange(1, 100)
        self.vad_sl.valueChanged.connect(lambda v: self.vad_val_lbl.setText(str(v)))
        le.addWidget(self.vad_sl)
        
        lbl_sens_desc = QLabel("💡 說明：調大(更靈敏)更容易偵測微弱說話聲，但也更易錄入背景雜音；調小則只偵測大聲發話，適合吵雜環境。")
        lbl_sens_desc.setWordWrap(True)
        lbl_sens_desc.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        le.addWidget(lbl_sens_desc)
        
        le.addSpacing(10)
        
        # Silence Timeout Section
        h_sil = QHBoxLayout()
        h_sil.addWidget(QLabel("未發話安全超時防呆 (秒):"))
        self.sil_val_lbl = QLabel("5.0 秒")
        self.sil_val_lbl.setStyleSheet("font-weight: bold; color: #3498db;")
        h_sil.addStretch()
        h_sil.addWidget(self.sil_val_lbl)
        le.addLayout(h_sil)
        
        self.sil_sp = QSlider(Qt.Horizontal); self.sil_sp.setRange(1, 10)
        self.sil_sp.valueChanged.connect(lambda v: self.sil_val_lbl.setText(f"{float(v):.1f} 秒"))
        le.addWidget(self.sil_sp)
        
        lbl_sil_desc = QLabel("💡 說明：【僅開關模式有效】此設定僅在「開關模式」生效，用於防止忘記關閉錄音或人離開時產生無限錄製（防呆安全機制）。「對講機模式」下完全停用此機制，不受此設定影響，以避免影響正常的按鍵長按錄音。")
        lbl_sil_desc.setWordWrap(True)
        lbl_sil_desc.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        le.addWidget(lbl_sil_desc)
        
        le.addSpacing(10)
        self.chk_af = QCheckBox("啟用 AI 背景自動糾錯 (需 API)"); le.addWidget(self.chk_af)
        self.chk_con = QCheckBox("顯示監控視窗"); le.addWidget(self.chk_con)
        
        # [A43] View Global Dictionary button
        self.btn_view_global = QPushButton("📖 檢視全球詞庫內容")
        self.btn_view_global.clicked.connect(self.open_global_dict_viewer)
        le.addWidget(self.btn_view_global)
        
        # [A46] Moderate Global Dictionary button
        self.btn_moderate_global = QPushButton("🛡️ 全球共享詞庫管理與審核")
        self.btn_moderate_global.clicked.connect(self.open_global_dict_moderator)
        le.addWidget(self.btn_moderate_global)
        
        le.addStretch(); self.tabs.addTab(te, "🔧 工程")
        
        # Signals
        ws = [
            (self.chk_auto_start, "toggled"), (self.chk_smart_left, "toggled"), (self.chk_smart_right, "toggled"),
            (self.smart_hold_combo, "currentIndexChanged"), (self.rec_mode_cb, "currentIndexChanged"),
            (self.output_mode_cb, "currentIndexChanged"), (self.vis_style_cb, "currentIndexChanged"),
            (self.api_in, "textChanged"), (self.opt_m, "currentTextChanged"), (self.vis_m, "currentTextChanged"),
            (self.fix_m, "currentTextChanged"), (self.prof_cb, "currentIndexChanged"), (self.chk_con, "toggled"),
            (self.chk_af, "toggled"), (self.chk_use_punc, "toggled"), (self.eng_cb, "currentIndexChanged"),
            (self.sil_sp, "valueChanged"), (self.vad_sl, "valueChanged"), (self.chk_audio_cue, "toggled"),
            (self.sound_sel, "currentIndexChanged")
        ]
        for w, s in ws: getattr(w, s).connect(self._widget_changed)
        self.sound_sel.currentIndexChanged.connect(lambda i: self.preview_sound_requested.emit(i))

    def load_settings(self):
        defaults = {
            "hotkey": "ctrl+shift+win", "magic_hotkey": "alt+win", 
            "smart_left": True, "smart_right": True, "smart_hold_duration": 0.5, 
            "use_punc": True, "recording_mode": 0, "recording_style": 1, "sound_style_idx": 9,
            "opt_profiles": [
                {
                    "name": "日常文字潤飾與錯字修正",
                    "prompt": "你是一個專業的文字編輯。請修正以下文字中的錯別字與標點符號，使語句通順。不要改變原本的語氣與意思，不要加任何開場白或解釋，直接輸出修改後的文字。"
                },
                {
                    "name": "指派任務型 (產生結構化指令)",
                    "prompt": "你是一個專業的提示詞工程師。請務必使用 Markdown 格式，將使用者的模糊想法結構化為具備執行力的 AI 指令。請明確劃分以下模塊：\n## 1. 任務角色 (Role)\n## 2. 背景與上下文 (Context)\n## 3. 具體要求與限制 (Constraints)\n## 4. 預期輸出格式 (Output Format)\n請直接輸出結構化後的結果，不要任何開場白與廢話。"
                }
            ], "show_console": True,
            "audio_cue": True, "vad_sensitivity": 50, "silence_timeout": 5.0, "auto_fix": False,
            "engine_version": "v2_stable",
            "magic_items": [
                {"id": "LEARN", "name": "📓 加入個人詞庫", "visible": True},
                {"id": "FIX", "name": "🪄 AI 個人化提示詞最佳化", "visible": True},
                {"id": "VISION", "name": "📸 擷取畫面並翻譯對照", "visible": True}
            ]
        }
        self.raw_config = defaults.copy()
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.raw_config.update(json.load(f))
            except: pass
        
        # Ensure default magic items exist
        its = self.raw_config.get("magic_items", [])
        bt = {"LEARN": "📓 加入個人詞庫", "FIX": "🪄 AI 個人化提示詞最佳化", "VISION": "📸 擷取畫面並翻譯對照"}
        for k, v in bt.items():
            if not any(x["id"] == k for x in its):
                its.insert(0, {"id": k, "name": v, "visible": True, "type": "internal", "val": ""})
        self.raw_config["magic_items"] = its
        
        # 載入後，如果發現 opt_profiles 是空的，或是只有預設的舊 "通用" 方案，則強制使用預設的這兩個方案
        profiles = self.raw_config.get("opt_profiles", [])
        if not profiles or (len(profiles) == 1 and profiles[0].get("name") in ["通用", ""]):
            self.raw_config["opt_profiles"] = [
                {
                    "name": "日常文字潤飾與錯字修正",
                    "prompt": "你是一個專業的文字編輯。請修正以下文字中的錯別字與標點符號，使語句通順。不要改變原本的語氣與意思，不要加任何開場白或解釋，直接輸出修改後的文字。"
                },
                {
                    "name": "指派任務型 (產生結構化指令)",
                    "prompt": "力量與方向。請務必使用 Markdown 格式，將使用者的模糊想法結構化為具備執行力的 AI 指令。請明確劃分以下模塊：\n## 1. 任務角色 (Role)\n## 2. 背景與上下文 (Context)\n## 3. 具體要求與限制 (Constraints)\n## 4. 預期輸出格式 (Output Format)\n請直接輸出結構化後的結果，不要任何開場白與廢話。"
                }
            ]
            # Replace placeholder text with the actual user prompt (fix '力量與方向')
            self.raw_config["opt_profiles"][1]["prompt"] = "你是一個專業的提示詞工程師。請務必使用 Markdown 格式，將使用者的模糊想法結構化為具備執行力的 AI 指令。請明確劃分以下模塊：\n## 1. 任務角色 (Role)\n## 2. 背景與上下文 (Context)\n## 3. 具體要求與限制 (Constraints)\n## 4. 預期輸出格式 (Output Format)\n請直接輸出結構化後的結果，不要任何開場白與廢話。"
        
        self._apply_ui()

    def _apply_ui(self):
        self._loading = True
        c = self.raw_config
        self.btn_hk.setText(to_chinese_hk(c.get("hotkey", "ctrl+shift+win")))
        self.btn_mhk.setText(to_chinese_hk(c.get("magic_hotkey", "alt+win")))
        self.chk_auto_start.setChecked(c.get("auto_start", False))
        self.chk_smart_left.setChecked(c.get("smart_left", True))
        self.chk_smart_right.setChecked(c.get("smart_right", True))
        self.chk_use_punc.setChecked(c.get("use_punc", True))
        self.chk_con.setChecked(c.get("show_console", True))
        self.chk_audio_cue.setChecked(c.get("audio_cue", True))
        self.api_in.setText(c.get("gemini_api_key", ""))
        self.sound_sel.setCurrentIndex(c.get("sound_style_idx", 9))
        self.vis_style_cb.setCurrentIndex(c.get("recording_style", 1))
        dur = c.get("smart_hold_duration", 0.5)
        self.smart_hold_combo.setCurrentIndex({0.3:0, 0.5:1, 0.8:2, 1.0:3, 1.5:4}.get(dur, 1))
        self.output_mode_cb.setCurrentIndex(c.get("output_mode", 0))
        self.rec_mode_cb.setCurrentIndex(c.get("recording_mode", 0))
        
        # Engineering parameters
        ev = c.get("engine_version", "v2_stable")
        idx = 0
        if ev == "v1_legacy": idx = 1
        self.eng_cb.setCurrentIndex(idx)
        
        self.vad_sl.setValue(c.get("vad_sensitivity", 50))
        self.sil_sp.setValue(int(float(c.get("silence_timeout", 5.0))))
        self.chk_af.setChecked(c.get("auto_fix", False))
        
        # Load and populate model comboboxes from cache
        cache = c.get("model_cache", [])
        if cache:
            self.opt_m.clear()
            self.vis_m.clear()
            self.fix_m.clear()
            for x in cache:
                m_id = x.get("id") or f"models/{x['display']}"
                display = x["display"]
                self.opt_m.addItem(display, m_id)
                self.fix_m.addItem(display, m_id)
                if x.get("can_vision", True):
                    self.vis_m.addItem(display, m_id)
                    
        # Apply current model text
        self.opt_m.setCurrentText(c.get("opt_model", ""))
        self.vis_m.setCurrentText(c.get("vision_model", ""))
        self.fix_m.setCurrentText(c.get("fix_model", ""))
        
        self._upd_prof()
        self._upd_mag_ui()
        self._loading = False

    def _upd_prof(self):
        self.prof_cb.clear()
        for x in self.raw_config.get("opt_profiles", []):
            self.prof_cb.addItem(x["name"])
        self.prof_cb.setCurrentIndex(self.raw_config.get("active_profile_idx", 0))

    def _upd_mag_ui(self):
        self.lw_mag.clear()
        for i in self.raw_config.get("magic_items", []):
            mid = i["id"]
            is_sys = mid in ["LEARN", "FIX", "VISION"]
            li = QListWidgetItem()
            li.setData(Qt.UserRole, mid)
            self.lw_mag.addItem(li)
            w = MagicItemWidget(i["name"], i.get("visible", True), is_sys, self)
            li.setSizeHint(w.sizeHint())
            self.lw_mag.setItemWidget(li, w)
            w.vis_changed.connect(lambda v, m=mid: self._mag_vis(m, v))
            if not is_sys:
                w.del_req.connect(lambda m=mid: self._del_macro(m))
                w.edit_req.connect(lambda m=mid: self._ed_macro(m))

    def _mag_vis(self, m, v):
        for x in self.raw_config.get("magic_items", []):
            if x["id"] == m:
                x["visible"] = v
        self._widget_changed()

    def _add_macro(self): 
        d = MacroEditorDialog(parent=self)
        self.active_dialog = d
        if d.exec() == QDialog.Accepted:
            n, t, v = d.get_data()
            self.raw_config.setdefault("magic_items", []).append({
                "id": f"macro_{int(time.time())}", 
                "name": n, 
                "visible": True, 
                "type": t, 
                "val": v
            })
            self._upd_mag_ui()
            self._widget_changed()
        self.active_dialog = None

    def _ed_macro(self, m): 
        it = next(x for x in self.raw_config.get("magic_items", []) if x["id"] == m)
        d = MacroEditorDialog(it["name"], it.get("type", "text"), it.get("val", ""), self)
        self.active_dialog = d
        if d.exec() == QDialog.Accepted:
            n, t, v = d.get_data()
            it.update({"name": n, "type": t, "val": v})
            self._upd_mag_ui()
            self._widget_changed()
        self.active_dialog = None

    def _del_macro(self, m): 
        if QMessageBox.question(self, "確認", "確定要刪除此自定義按鈕嗎？") == QMessageBox.Yes:
            self.raw_config["magic_items"] = [x for x in self.raw_config.get("magic_items", []) if x["id"] != m]
            self._upd_mag_ui()
            self._widget_changed()

    def _reorder(self, *args): 
        if not self._loading:
            reordered = []
            for i in range(self.lw_mag.count()):
                mid = self.lw_mag.item(i).data(Qt.UserRole)
                item = next(x for x in self.raw_config.get("magic_items", []) if x["id"] == mid)
                reordered.append(item)
            self.raw_config["magic_items"] = reordered
            self._widget_changed()

    def set_auto_start(self, enabled: bool):
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "AI_Voice_Assistant"
            app_path = f'"{sys.executable}"' if hasattr(sys, '_MEIPASS') else f'"{os.path.join(os.getcwd(), "啟動語音助手.bat")}"'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled: 
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
        except: pass

    def handle_captured_input(self, k):
        if self.active_dialog and self.active_dialog.isVisible():
            if hasattr(self.active_dialog, 'update_captured'): 
                self.active_dialog.update_captured(k)
            if not isinstance(self.active_dialog, MacroEditorDialog): 
                self.stop_pairing_requested.emit()

    def _widget_changed(self, *args):
        if not self._loading:
            self.set_auto_start(self.chk_auto_start.isChecked())
            self._save_timer.start()

    def _do_save(self):
        try:
            ev_list = ["v2_stable", "v1_legacy"]
            upd = {
                "hotkey": self.raw_config.get("hotkey", "ctrl+shift+win"),
                "magic_hotkey": self.raw_config.get("magic_hotkey", "alt+win"),
                "gemini_api_key": self.api_in.text(),
                "opt_model": self.opt_m.currentText(),
                "vision_model": self.vis_m.currentText(),
                "fix_model": self.fix_m.currentText(),
                "smart_left": self.chk_smart_left.isChecked(),
                "smart_right": self.chk_smart_right.isChecked(),
                "smart_hold_duration": [0.3, 0.5, 0.8, 1.0, 1.5][self.smart_hold_combo.currentIndex()],
                "output_mode": self.output_mode_cb.currentIndex(),
                "recording_mode": self.rec_mode_cb.currentIndex(),
                "recording_style": self.vis_style_cb.currentIndex(),
                "sound_style_idx": self.sound_sel.currentIndex(),
                "use_punc": self.chk_use_punc.isChecked(),
                "show_console": self.chk_con.isChecked(),
                "audio_cue": self.chk_audio_cue.isChecked(),
                "active_profile_idx": self.prof_cb.currentIndex(),
                "engine_version": ev_list[self.eng_cb.currentIndex()] if self.eng_cb.currentIndex() < len(ev_list) else "v2_stable",
                "vad_sensitivity": self.vad_sl.value(),
                "silence_timeout": float(self.sil_sp.value()),
                "vad_buffer": float(self.sil_sp.value()),
                "auto_fix": self.chk_af.isChecked(),
                "auto_start": self.chk_auto_start.isChecked()
            }
            self.raw_config.update(upd)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.raw_config, f, indent=4)
            self.settings_changed.emit(self.raw_config)
        except Exception as e:
            logger.error(f"Save Error: {e}")

    def open_key_dialog(self, target):
        d = UnifiedKeyDialog(self.raw_config.get(target, ""), self)
        if d.exec() == QDialog.Accepted:
            self.raw_config[target] = d.result_hk
            self._apply_ui()
            self._widget_changed()

    def open_profile_manager(self):
        p = self.raw_config.get("opt_profiles", [])
        idx = self.raw_config.get("active_profile_idx", 0)
        d = ProfileManager(p, idx, self)
        if d.exec() == QDialog.Accepted:
            self.raw_config["opt_profiles"] = d.profiles
            self._upd_prof()
            self._widget_changed()

    def open_quick_add(self, text=""):
        if self.quick_add_dlg: self.quick_add_dlg.close(); self.quick_add_dlg.deleteLater()
        self.quick_add_dlg = QuickAddDialog(text, self)
        self.quick_add_dlg.add_req.connect(self.add_dict_requested.emit)
        self.quick_add_dlg.show()

    def open_dict_manager(self, initial_text=""):
        if self.dict_dlg: self.dict_dlg.close(); self.dict_dlg.deleteLater()
        self.dict_dlg = DictionaryManager(self.dict_items, self, initial_text)
        self.dict_dlg.add_req.connect(self.add_dict_requested.emit)
        self.dict_dlg.del_req.connect(self.del_dict_requested.emit)
        self.dict_dlg.closed_signal.connect(self._sync_dict_on_close)
        self.dict_dlg.show()

    def _sync_dict_on_close(self):
        self.dict_items = self.dict_dlg.all_items
        self.dict_items.sort(key=lambda x: x[1])

    def export_user_data(self):
        """ [A30] Export settings and dictionary as two separate files in chosen folder """
        folder = QFileDialog.getExistingDirectory(self, "選擇匯出資料夾")
        if not folder: return
        
        try:
            # 1. Export settings
            settings_path = os.path.join(folder, "ai_settings_backup.json")
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(self.raw_config, f, indent=4, ensure_ascii=False)
                
            # 2. Export dictionary
            dict_path = os.path.join(folder, "user_dictionary_feedback.csv")
            import csv
            with open(dict_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Original", "Correction"])
                for orig, corr in self.dict_items:
                    writer.writerow([orig, corr])
                    
            QMessageBox.information(
                self, "匯出成功",
                f"✅ 匯出成功！\n\n已儲存至：\n1. 設定檔：{settings_path}\n2. 詞庫檔：{dict_path}\n\n💡 提示：您可以將「詞庫檔」提供給開發團隊，用於全球詞庫更新，以持續提升辨識準確度！"
            )
        except Exception as e:
            QMessageBox.critical(self, "匯出失敗", f"❌ 匯出失敗：{e}")

    def import_user_data(self):
        """ [A31] Import settings and dictionary additively from chosen folder """
        folder = QFileDialog.getExistingDirectory(self, "選擇匯入資料夾")
        if not folder: return
        
        settings_path = os.path.join(folder, "ai_settings_backup.json")
        dict_path = os.path.join(folder, "user_dictionary_feedback.csv")
        
        has_settings = os.path.exists(settings_path)
        has_dict = os.path.exists(dict_path)
        
        if not has_settings and not has_dict:
            QMessageBox.warning(self, "匯入失敗", f"❌ 在該資料夾中找不到備份檔案。\n\n需要：\n1. 設定檔：ai_settings_backup.json\n或\n2. 詞庫檔：user_dictionary_feedback.csv")
            return
            
        imported_msg = []
        try:
            # 1. Import settings
            if has_settings:
                with open(settings_path, "r", encoding="utf-8") as f:
                    imported_config = json.load(f)
                self.raw_config.update(imported_config)
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.raw_config, f, indent=4, ensure_ascii=False)
                self._apply_ui()
                self.settings_changed.emit(self.raw_config)
                imported_msg.append("✅ 系統設定已成功恢復")
                
            # 2. Import dictionary (Additive)
            if has_dict:
                import csv
                imported_items = []
                with open(dict_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader, None) # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            orig, corr = row[0].strip(), row[1].strip()
                            if orig and corr:
                                imported_items.append((orig, corr))
                                
                if imported_items:
                    self.import_dict_requested.emit(json.dumps(imported_items))
                    imported_msg.append(f"✅ 已增量合併 {len(imported_items)} 筆個人詞庫（保留原有內容）")
                    
            QMessageBox.information(
                self, "匯入成功",
                "\n".join(imported_msg)
            )
        except Exception as e:
            QMessageBox.critical(self, "匯入失敗", f"❌ 匯入失敗：{e}")

    def update_dict_list(self, i):
        self.dict_items = i
        if self.dict_dlg and self.dict_dlg.isVisible():
            self.dict_dlg.upd(i)

    def _check_models(self):
        self.btn_chk_models.setText("⏳ 查詢中...")
        self.btn_chk_models.setEnabled(False)
        threading.Thread(target=self._async_chk, daemon=True).start()

    def _async_chk(self):
        try:
            from src.utils.cloud_engine import GeminiCloudEngine
            e = GeminiCloudEngine(); e.configure(self.api_in.text().strip())
            m = e.get_available_models_with_capabilities()
            if m: 
                self.raw_config.update({"model_cache": m})
                self.models_scanned_signal.emit(m)
        except Exception as e:
            logger.error(f"Model Check Error: {e}")
        QTimer.singleShot(0, lambda: self.btn_chk_models.setText("🔍 查詢模型清單"))
        QTimer.singleShot(0, lambda: self.btn_chk_models.setEnabled(True))

    def _on_models_discovered(self, m_list):
        self.opt_m.clear()
        self.vis_m.clear()
        self.fix_m.clear()
        for x in m_list:
            m_id = x.get("id") or f"models/{x['display']}"
            display = x["display"]
            self.opt_m.addItem(display, m_id)
            self.fix_m.addItem(display, m_id)
            if x.get("can_vision", True):
                self.vis_m.addItem(display, m_id)
        self._widget_changed()

    def update_ui_coords(self, x, y):
        self.raw_config.update({"ui_x": x, "ui_y": y})
        self._widget_changed()

    def open_global_dict_viewer(self):
        """ [A43] Loads the global dictionary list and shows the viewer dialog """
        try:
            from src.utils.learning_engine import LearningEngine
            engine = LearningEngine()
            items = engine.list_global_dictionary()
        except Exception as e:
            items = []
            logger.error(f"Error listing global dictionary: {e}")
            
        dlg = GlobalDictionaryViewer(items, self)
        dlg.exec()

    def open_global_dict_moderator(self):
        """ [A46] Opens the global dictionary moderation tool """
        api_key = self.api_in.text().strip()
        # Find model ID from opt_m QComboBox
        model_id = self.opt_m.currentData() or "gemini-2.0-flash"
        dlg = GlobalDictModeratorDialog(api_key, model_id, self)
        dlg.exec()
 
