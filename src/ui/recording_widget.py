# src/ui/recording_widget.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QCursor
import math

class WaveAnimation(QWidget):
    def __init__(self, parent=None, is_mini=False):
        super().__init__(parent)
        # [A536] Centered Mini Wave
        size_w = 30 if is_mini else 40
        size_h = 12 if is_mini else 16
        self.setFixedSize(size_w, size_h)
        self.phase = 0
        self.is_mini = is_mini
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(50)

    def update_wave(self):
        self.phase += 0.2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        spacing = 5 if self.is_mini else 6
        bar_w = 2 if self.is_mini else 3
        max_h = 10 if self.is_mini else 14
        
        # [A536] Calculate centering offset for bars
        total_w = (4 * spacing) + bar_w
        offset_x = (self.width() - total_w) / 2
        
        # Draw 5 bars symmetrically
        for i in range(5):
            h = 3 + abs(math.sin(self.phase + i * 0.8)) * max_h
            painter.setBrush(QColor(255, 255, 255, 220))
            painter.setPen(Qt.NoPen)
            x = offset_x + (i * spacing)
            y = (self.height() - h) / 2
            painter.drawRoundedRect(x, y, bar_w, h, 1, 1)

class RecordingWidget(QWidget):
    position_changed = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self.display_style = 0 # 0: Bubble, 1: Cursor Wave, 2: Hidden
        self.is_positioning_mode = False # [A554] Persistent positioning
        self._follow_timer = QTimer(self); self._follow_timer.timeout.connect(self._follow_cursor)
        self.setup_ui()
    
    def enter_positioning_mode(self, text="請拖曳調整位置..."):
        """ [A554] Enter persistent positioning mode """
        self.is_positioning_mode = True
        self.set_style(0) # Force bubble
        if hasattr(self, 'label'):
            self.label.setText(text)
        self.show_recording()
        # [A554] In positioning mode, we WANT focus for the click-to-close
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, False)
        self.show()

    def exit_positioning_mode(self):
        """ [A554] Exit and restore flags """
        self.is_positioning_mode = False
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)
        self.hide()
        
    def setup_ui(self):
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget(): child.widget().deleteLater()
        else:
            self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.display_style == 2: # Hidden
            self.setFixedSize(1, 1); return

        if self.display_style == 1: # [A536] Compact Centered Cursor Wave
            self.setFixedSize(48, 24) 
            self.container = QFrame(); self.container.setFixedSize(48, 24)
            self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid rgba(255,255,255,60);")
            cl = QHBoxLayout(self.container); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0); cl.setAlignment(Qt.AlignCenter)
            
            self.wave = WaveAnimation(is_mini=True)
            self.loading_label = QLabel("未啟動")
            self.loading_label.setStyleSheet("color: #f39c12; font-size: 10px; font-weight: bold; font-family: 'Microsoft JhengHei';")
            self.loading_label.hide()
            
            cl.addWidget(self.wave)
            cl.addWidget(self.loading_label)
            
            self.main_layout.addWidget(self.container)
            self._follow_timer.start(10)
        else: # Traditional Bubble
            self._follow_timer.stop()
            self.setFixedSize(160, 36)
            self.pill = QFrame(); self.pill.setObjectName("pill"); self.pill.setFixedSize(160, 36)
            self.pill.setAttribute(Qt.WA_TransparentForMouseEvents) # [A549]
            self.pill.setStyleSheet("QFrame#pill { background-color: rgba(30, 30, 30, 230); border-radius: 18px; border: 1px solid rgba(255, 255, 255, 60); }")
            pl = QHBoxLayout(self.pill); pl.setContentsMargins(10, 0, 10, 0); pl.setSpacing(6)
            self.dot = QLabel(); self.dot.setFixedSize(8, 8); self.dot.setStyleSheet("background-color: #ff4d4d; border-radius: 4px;")
            self.label = QLabel("正在聽..."); self.label.setStyleSheet("color: white; font-family: 'Microsoft JhengHei'; font-size: 13px; font-weight: bold;")
            self.wave = WaveAnimation()
            
            # [A550] Ensure all children are transparent for dragging
            for w in [self.dot, self.label, self.wave]: 
                w.setAttribute(Qt.WA_TransparentForMouseEvents)
                
            pl.addWidget(self.dot); pl.addWidget(self.label); pl.addWidget(self.wave)
            self.main_layout.addWidget(self.pill)

    def set_style(self, style_idx):
        self.display_style = style_idx
        self.setup_ui()

    def _follow_cursor(self):
        if self.isVisible() and self.display_style == 1:
            pos = QCursor.pos()
            # [A536] Center vertically, 20px to the right
            self.move(pos.x() + 20, pos.y() - 12)

    def set_initial_position(self, x=None, y=None):
        if self.display_style == 1: return
        screen = self.screen().geometry()
        if x is not None and y is not None: self.move(x, y)
        else: self.move((screen.width() - 160) // 2, 80)

    def show_recording(self):
        if self.display_style == 2: return
        # [A526/A536/A552] Reset to normal state ONLY if text is "正在啟動中..."
        if hasattr(self, 'label') and self.display_style == 0:
            if self.label.text() == "正在啟動中...":
                self.label.setText("正在聽...")
            self.dot.setStyleSheet("background-color: #ff4d4d; border-radius: 4px;")
        
        if hasattr(self, 'container') and self.display_style == 1:
            self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid rgba(255,255,255,60);")
            if hasattr(self, 'wave'): self.wave.show()
            if hasattr(self, 'loading_label'): self.loading_label.hide()
            
        self.show()
        self.setWindowOpacity(1.0) # Ensure visible
        if self.display_style == 0: self.raise_()

    def set_loading_state(self):
        """ [A536] Visual feedback when engine is still loading """
        if self.display_style == 2: return
        self.show()
        if self.display_style == 0:
            if hasattr(self, 'label'): 
                self.label.setText("正在啟動中...")
                self.dot.setStyleSheet("background-color: #f39c12; border-radius: 4px;") # Yellow for loading
            self.raise_()
        elif self.display_style == 1:
            if hasattr(self, 'container'):
                self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid #f39c12;")
                if hasattr(self, 'wave'): self.wave.hide()
                if hasattr(self, 'loading_label'): self.loading_label.show()

    def show_processing(self):
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_pos is not None:
            self._drag_pos = None
            pos = self.pos()
            self.position_changed.emit(pos.x(), pos.y())
            event.accept()
