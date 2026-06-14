# src/ui/snip_overlay.py
import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QGuiApplication

class SnipOverlay(QWidget):
    """
    [A232] Snip Overlay for Area Selection.
    - Darkens the screen.
    - Allows dragging a selection rectangle.
    - Emits the selected geometry.
    """
    snip_captured = Signal(QRect)
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # [A600] Robust geometry for all screens
        geo = QRect()
        for screen in QGuiApplication.screens():
            geo = geo.united(screen.geometry())
        self.setGeometry(geo)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        
        # [A600] Ensure we have mouse tracking and are on top
        self.setMouseTracking(True)
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 1. Background darkness (semi-transparent black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        
        if self.is_selecting:
            # 2. Selection rectangle
            rect = QRect(self.begin, self.end).normalized()
            
            # 3. Clear the selection area (make it "see-through")
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # 4. Draw border around the clear area
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            self.is_selecting = True
            self.update()
        elif event.button() == Qt.RightButton:
            self.close()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            rect = QRect(self.begin, self.end).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.snip_captured.emit(rect)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.closed.emit()
        self.deleteLater()
        super().closeEvent(event)

def start_snipping():
    """ Helper to start the snipping process """
    overlay = SnipOverlay()
    overlay.show()
    return overlay
