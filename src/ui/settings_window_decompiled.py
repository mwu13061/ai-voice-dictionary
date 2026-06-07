# Source Generated with Decompyle++
# File: src.ui.settings_window_with_header.pyc (Python 3.11)

import os
import json
import sqlite3
import shutil
import sys
import threading
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox, QDialog, QTabWidget, QCheckBox, QGridLayout, QListWidget, QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidgetItem, QFrame, QSlider, QAbstractItemView, QMenu
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPoint
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QAction
from loguru import logger
from src.utils.path_helper import get_writable_path
CONFIG_PATH = get_writable_path(os.path.join('user_data', 'gemini_tool_config.json'))
HW_CHINESE = {
    'mouse_back': '滑鼠側後退鍵',
    'mouse_forward': '滑鼠側前進鍵',
    'mouse_middle': '滑鼠中鍵',
    'ctrl': 'Ctrl',
    'shift': 'Shift',
    'alt': 'Alt',
    'win': 'Win鍵',
    'enter': 'Enter',
    'space': '空白鍵',
    'tab': 'Tab',
    'f10': 'F10',
    'f12': 'F12' }
MODIFIERS = [
    'ctrl',
    'shift',
    'alt',
    'win']

def to_chinese_hk(hk):
    if not hk:
        return '未設定'
    return (lambda .0: [ HW_CHINESE.get(p, p.upper()) for p in .0 ])(hk.lower().split('+')())


class UnifiedKeyDialog(QDialog):
    pass
# WARNING: Decompyle incomplete


class QuickAddDialog(QDialog):
    pass
# WARNING: Decompyle incomplete


class RefinementDialog(QDialog):
    pass
# WARNING: Decompyle incomplete


class DictionaryManager(QDialog):
    pass
# WARNING: Decompyle incomplete


class AppPickerDialog(QDialog):
    pass
# WARNING: Decompyle incomplete


class MacroEditorDialog(QDialog):
    pass
# WARNING: Decompyle incomplete


class MagicItemWidget(QWidget):
    pass
# WARNING: Decompyle incomplete


class ProfileManager(QDialog):
    pass
# WARNING: Decompyle incomplete


class SettingsWindow(QWidget):
    pass
# WARNING: Decompyle incomplete

