# src/utils/smart_trigger.py
import time, threading, ctypes, pyperclip, keyboard, pyautogui
from ctypes import wintypes
from pynput import mouse
from loguru import logger
from PySide6.QtCore import QObject, Signal

class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT)
    ]

user32 = ctypes.windll.user32
IDC_IBEAM = 32513

class SmartTrigger(QObject):
    """
    Build [A636] ROBUST CORE TRIGGER & CAPTURE.
    - [REPRODUCTION_GUARD] Mouse Move Threshold (5px) implemented.
    - Background capture with physical state verification.
    """
    voice_start_signal = Signal(); voice_stop_signal = Signal()
    magic_signal = Signal(str); click_signal = Signal(int, int)

    def __init__(self):
        super().__init__()
        self._left_enabled = True; self._right_enabled = True; self._recording_mode = 0
        self._button_held = None; self._is_recording_active = False
        self._start_pos = (0, 0); self._is_moving = False; self._pre_pressed_captured_text = ""
        self._hold_duration_ms = 500; self._timer = None; self._lock = threading.Lock()
        self._h_ibeam = user32.LoadCursorW(None, ctypes.c_wchar_p(IDC_IBEAM))

    def set_enabled(self, left: bool, right: bool, hold_duration_s: float = 0.5, mode: int = 0):
        with self._lock:
            self._hold_duration_ms = int(hold_duration_s * 1000)
            self._left_enabled = left; self._right_enabled = right; self._recording_mode = mode
            logger.info(f"Sensor A636 Active: L:{left} R:{right} D:{hold_duration_s}s")

    def _get_current_cursor(self):
        info = CURSORINFO()
        info.cbSize = ctypes.sizeof(CURSORINFO)
        if user32.GetCursorInfo(ctypes.byref(info)):
            return info.hCursor
        return None

    def handle_move(self, x, y):
        """ [A636] CRITICAL: Anti-Trigger Movement Guard """
        if self._button_held:
            dx = abs(x - self._start_pos[0]); dy = abs(y - self._start_pos[1])
            # Threshold: 5px movement cancels the long-press logic
            if dx > 5 or dy > 5:
                if not self._is_moving:
                    self._is_moving = True; self._cancel_timer()

    def handle_click(self, x, y, button, pressed):
        if pressed: self.click_signal.emit(int(x), int(y))
        with self._lock:
            if pressed:
                if self._button_held: return 
                if (button == mouse.Button.left and self._left_enabled) or (button == mouse.Button.right and self._right_enabled):
                    self._button_held = button; self._start_pos = (x, y); self._is_moving = False
                    self._start_timer()

            else:
                if self._button_held == button:
                    self._cancel_timer(); self._button_held = None
                    if self._recording_mode == 0 and button == mouse.Button.left:
                        is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_recording_active
                        if is_rec:
                            self.voice_stop_signal.emit(); self._is_recording_active = False

    def _start_timer(self):
        self._cancel_timer()
        self._timer = threading.Timer(self._hold_duration_ms / 1000.0, self._evaluate_trigger)
        self._timer.daemon = True; self._timer.start()

    def _cancel_timer(self):
        if self._timer: self._timer.cancel(); self._timer = None

    def _robust_capture(self):
        """ [A7] High-Resilience Selection Capture inside Timer Thread """
        logger.info("📋 [A636] Attempting robust text capture...")
        old_cb = pyperclip.paste()
        try: pyperclip.copy("")
        except: pass

        # 1. Programmatically release right mouse button
        # This resolves issues where target applications block keys due to active mouse drag/hold state
        user32.mouse_event(0x0010, 0, 0, 0, 0) # MOUSEEVENTF_RIGHTUP
        time.sleep(0.02) # Let OS process release event

        # 2. Release modifier keys to avoid keyboard state interference with ctrl+c
        modifiers = [0x10, 0x11, 0x12, 0x5B, 0x5C] # shift, ctrl, alt, win
        released = []
        for vk in modifiers:
            if user32.GetAsyncKeyState(vk) & 0x8000:
                user32.keybd_event(vk, 0, 2, 0) # KEYEVENTF_KEYUP
                released.append(vk)
                
        # 3. Send Ctrl+C natively with correct scan codes
        user32.keybd_event(0x11, 0x1D, 0, 0) # Ctrl down
        user32.keybd_event(0x43, 0x2E, 0, 0) # C down
        time.sleep(0.01)
        user32.keybd_event(0x43, 0x2E, 2, 0) # C up
        user32.keybd_event(0x11, 0x1D, 2, 0) # Ctrl up
        
        res = ""
        for i in range(15):
            time.sleep(0.01)
            try:
                res = pyperclip.paste().strip()
                if res: break
            except: pass
            
        # 4. If first try failed (likely because context menu popped up and took focus)
        if not res:
            logger.info("📋 [A636] Initial copy empty, sending Esc to dismiss context menu and retrying...")
            user32.keybd_event(0x1B, 0x01, 0, 0) # Esc down with scan code
            time.sleep(0.01)
            user32.keybd_event(0x1B, 0x01, 2, 0) # Esc up
            time.sleep(0.05) # Wait for focus to return
            
            # Send Ctrl+C again
            user32.keybd_event(0x11, 0x1D, 0, 0)
            user32.keybd_event(0x43, 0x2E, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(0x43, 0x2E, 2, 0)
            user32.keybd_event(0x11, 0x1D, 2, 0)
            
            for i in range(20):
                time.sleep(0.01)
                try:
                    res = pyperclip.paste().strip()
                    if res: break
                except: pass

        # Restore modifier keys if they were physically held
        for vk in released:
            user32.keybd_event(vk, 0, 0, 0) # KEYEVENTF_KEYDOWN
            
        if res:
            logger.success(f"📋 [A636] Robust capture SUCCESS: '{res}'")
        else:
            logger.warning("📋 [A636] Robust capture FAILED.")
            try: pyperclip.copy(old_cb)
            except: pass
        return res

    def _evaluate_trigger(self):
        """ [A636] Dispatch only if NOT moving and cursor is I-beam """
        with self._lock:
            if not self._button_held or self._is_moving: return
            
            # 檢查游標是否為直線游標 (I-beam)
            current_cursor = self._get_current_cursor()
            if current_cursor != self._h_ibeam:
                logger.info(f"📡 Cursor not I-Beam ({current_cursor} != {self._h_ibeam}). Bypassing trigger.")
                self._button_held = None
                return
                
            if self._button_held == mouse.Button.left:
                is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_recording_active
                if self._recording_mode in [1, 2]:
                    if is_rec:
                        logger.info("📡 [A636] Voice Stop (Toggle Mode via Mouse)")
                        self._is_recording_active = False; self.voice_stop_signal.emit()
                    else:
                        logger.info("📡 [A636] Voice Start (Toggle Mode via Mouse)")
                        self._is_recording_active = True; self.voice_start_signal.emit()
                    self._button_held = None
                else:
                    if not is_rec:
                        logger.info("📡 [A636] Voice Start (PTT Mode via Mouse)")
                        self._is_recording_active = True; self.voice_start_signal.emit()
            elif self._button_held == mouse.Button.right:
                logger.info("📡 [A636] Magic Capture Start")
                captured = self._robust_capture()
                self.magic_signal.emit(captured); self._button_held = None
