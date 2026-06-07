# src/utils/hotkey_manager.py
from PySide6.QtCore import QObject, Signal
from pynput import keyboard, mouse
from loguru import logger
import threading
import time

class HotkeyManager(QObject):
    """
    Build [A446] Unified Input Sensor.
    - SOLE owner of the mouse listener to prevent hook conflicts.
    - Forwards events to SmartTrigger logic.
    """
    start_recording_signal = Signal()
    stop_recording_signal = Signal() # [A563] Added for keyboard PTT
    magic_menu_signal = Signal()
    input_captured_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._active_keys = set()
        self._target_keys = set()
        self._magic_keys = set()
        self._cooldown = 0.3
        self._last_trigger_time = 0
        self._is_pressed = False
        self._lock = threading.Lock()
        
        self.learning_mode = False
        self.mouse_listener = None
        self.kb_listener = None
        self.smart_trigger = None # [A446] Will be injected by controller
        self.controller = None
        
        self._recording_mode = 0
        self._hold_duration_ms = 500
        self._hotkey_timer_active = False
        self._hotkey_timer = None

    def initialize(self, hotkey_str, magic_hotkey_str, cooldown=0.3, smart_trigger=None):
        self._cooldown = cooldown
        self._target_keys = self._parse_keys(hotkey_str)
        self._magic_keys = self._parse_keys(magic_hotkey_str)
        self.smart_trigger = smart_trigger
        
        logger.warning(f"Engine A446: V:{hotkey_str} M:{magic_hotkey_str} CD:{cooldown}")
        self._start_listeners()
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _parse_keys(self, s):
        if not s: return set()
        return set(s.lower().split('+'))

    def _start_listeners(self):
        if self.kb_listener: self.kb_listener.stop()
        if self.mouse_listener: self.mouse_listener.stop()

        self.kb_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.kb_listener.start()
        
        # [A446] Single Mouse Listener for both Hotkeys and Smart Trigger
        self.mouse_listener = mouse.Listener(on_click=self._on_click, on_move=self._on_move)
        self.mouse_listener.start()

    def set_learning_mode(self, enabled: bool):
        self.learning_mode = enabled
        if enabled:
            logger.info("HotkeyManager: Raw VK Pairing ACTIVE.")
            self._active_keys.clear()

    def _watchdog(self):
        while True:
            time.sleep(2.0)
            if self._active_keys and (time.time() - self._last_trigger_time > 2.0):
                with self._lock:
                    self._active_keys.clear()
                    self._is_pressed = False

    def _on_move(self, x, y):
        if self.smart_trigger:
            self.smart_trigger.handle_move(x, y)

    def _on_click(self, x, y, button, pressed):
        # 1. Forward to SmartTrigger logic (handles holds)
        if self.smart_trigger:
            self.smart_trigger.handle_click(x, y, button, pressed)

        # 2. Handle simple side-button clicks
        if not pressed: return
        btn_name = str(button).lower()
        
        clean_name = btn_name
        if "button.x1" in btn_name: clean_name = "mouse_back"
        elif "button.x2" in btn_name: clean_name = "mouse_forward"
        elif "button.left" in btn_name: clean_name = "mouse_left"
        elif "button.right" in btn_name: clean_name = "mouse_right"
        elif "button.middle" in btn_name: clean_name = "mouse_middle"
        else:
            clean_name = btn_name.replace("button.", "mouse_")

        if self.learning_mode:
            if clean_name in ["mouse_left", "mouse_right"]: return
            logger.success(f"Captured Mouse Event: {clean_name}")
            self.input_captured_signal.emit(clean_name)
            return

        self._check_mouse_trigger(clean_name)

    def _check_mouse_trigger(self, trigger_name):
        now = time.time()
        if now - self._last_trigger_time < self._cooldown: return
        
        if trigger_name in self._target_keys and len(self._target_keys) == 1:
            self._last_trigger_time = now
            self._is_pressed = True
            self.start_recording_signal.emit()
            self._start_ptt_watchdog()
        elif trigger_name in self._magic_keys and len(self._magic_keys) == 1:
            self._last_trigger_time = now
            self.magic_menu_signal.emit()

    def _on_press(self, key):
        """ [A164/A168] Capture RAW VK and ASCII Control Chars """
        try:
            k = ""
            if hasattr(key, 'char') and key.char:
                if ord(key.char) < 32: k = chr(ord(key.char) + 96)
                else: k = key.char.lower()
            elif hasattr(key, 'name'): k = key.name.lower()
            if not k:
                if hasattr(key, 'vk'): k = f"vk:{key.vk}"
                else: k = str(key).lower().replace("key.", "").replace("<", "").replace(">", "")

            if not k or k == "none": return
            if k.startswith('ctrl'): k = 'ctrl'
            if k.startswith('shift'): k = 'shift'
            if k.startswith('alt'): k = 'alt'
            if k == 'cmd': k = 'win'
            if k in ['media_back', 'browser_back']: k = 'mouse_back'
            if k in ['media_forward', 'browser_forward']: k = 'mouse_forward'
            
            with self._lock:
                self._active_keys.add(k)
                if self.learning_mode:
                    # [A490] Don't emit yet, wait for release to get full combo
                    return
                self._check_triggers()
        except: pass

    def _on_release(self, key):
        try:
            k = ""
            if hasattr(key, 'char') and key.char:
                if ord(key.char) < 32: k = chr(ord(key.char) + 96)
                else: k = key.char.lower()
            elif hasattr(key, 'name'): k = key.name.lower()
            if not k and hasattr(key, 'vk'): k = f"vk:{key.vk}"
            if not k: return

            if k.startswith('ctrl'): k = 'ctrl'
            if k.startswith('shift'): k = 'shift'
            if k.startswith('alt'): k = 'alt'
            if k == 'cmd': k = 'win'
            if k in ['media_back', 'browser_back']: k = 'mouse_back'
            if k in ['media_forward', 'browser_forward']: k = 'mouse_forward'
            
            with self._lock:
                if self.learning_mode and self._active_keys:
                    # [A490] Capture full combo on release
                    combo = "+".join(sorted(list(self._active_keys)))
                    logger.success(f"Captured Combo: {combo}")
                    self.input_captured_signal.emit(combo)
                    self._active_keys.clear()
                    return

                if k in self._active_keys: self._active_keys.remove(k)
                
                # [A563] PTT Stop Detection / Toggle Cancel Detection
                if self._recording_mode == 0:
                    if self._is_pressed and not self._target_keys.issubset(self._active_keys):
                         logger.info("🎯 [INPUT] Hotkey Released -> Stop recording")
                         self._is_pressed = False
                         self.stop_recording_signal.emit()
                else:
                    if not self._target_keys.issubset(self._active_keys):
                        if self._hotkey_timer_active:
                            self._cancel_hotkey_timer()
                            self._hotkey_timer_active = False
        except: pass

    def _check_triggers(self):
        if self.learning_mode: return
        now = time.time()

        # [A559] Robust Subset Check: Ensure all target keys are in active set
        if self._target_keys and self._target_keys.issubset(self._active_keys):
            if self._recording_mode == 0:
                if now - self._last_trigger_time < self._cooldown: return
                if not self._is_pressed:
                    logger.info(f"🎯 [INPUT] Trigger Detected: {'+'.join(self._target_keys)}")
                    self._is_pressed = True
                    self._last_trigger_time = now
                    self.start_recording_signal.emit()
                    self._start_ptt_watchdog()
            else:
                if not self._hotkey_timer_active:
                    self._hotkey_timer_active = True
                    self._hotkey_timer = threading.Timer(self._hold_duration_ms / 1000.0, self._evaluate_hotkey_toggle)
                    self._hotkey_timer.daemon = True
                    self._hotkey_timer.start()
            return

        if self._magic_keys and self._magic_keys.issubset(self._active_keys):
            if now - self._last_trigger_time < self._cooldown: return
            if not self._is_pressed:
                logger.info(f"🎯 [INPUT] Magic Menu Triggered: {'+'.join(self._magic_keys)}")
                self._is_pressed = True
                self._last_trigger_time = now
                self.magic_menu_signal.emit()
            return

    def _start_ptt_watchdog(self):
        """ [PTT Watchdog] Poll physical states of keys to trigger instant stop on release """
        def _poll():
            import ctypes
            user32 = ctypes.windll.user32
            
            vk_map = {
                'ctrl': [0x11, 0xA2, 0xA3],
                'shift': [0x10, 0xA0, 0xA1],
                'alt': [0x12, 0xA4, 0xA5],
                'win': [0x5B, 0x5C],
            }
            named_keys = {
                'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'esc': 0x1B,
                'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
                'page_up': 0x21, 'page_down': 0x22, 'end': 0x23, 'home': 0x24,
                'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
                'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
                'f11': 0x7A, 'f12': 0x7B
            }
            mouse_vk_map = {
                'mouse_left': 0x01,
                'mouse_right': 0x02,
                'mouse_middle': 0x04,
                'mouse_back': 0x05,
                'mouse_forward': 0x06,
            }
            
            while True:
                time.sleep(0.02) # Poll every 20ms for instant real-time response
                with self._lock:
                    if not self._is_pressed or self._recording_mode != 0:
                        break
                    
                    is_held = True
                    if self._target_keys:
                        for tk in self._target_keys:
                            if tk in vk_map:
                                if not any((user32.GetAsyncKeyState(vk) & 0x8000) != 0 for vk in vk_map[tk]):
                                    is_held = False
                                    break
                            elif tk.startswith('mouse_') or 'button' in tk:
                                vk = None
                                if tk in mouse_vk_map:
                                    vk = mouse_vk_map[tk]
                                elif 'x1' in tk or 'back' in tk:
                                    vk = 0x05
                                elif 'x2' in tk or 'forward' in tk:
                                    vk = 0x06
                                elif 'left' in tk:
                                    vk = 0x01
                                elif 'right' in tk:
                                    vk = 0x02
                                elif 'middle' in tk:
                                    vk = 0x04
                                    
                                if vk and (user32.GetAsyncKeyState(vk) & 0x8000) == 0:
                                    is_held = False
                                    break
                            elif len(tk) == 1:
                                vk = user32.VkKeyScanW(ord(tk)) & 0xFF
                                if vk != 0xFF and (user32.GetAsyncKeyState(vk) & 0x8000) == 0:
                                    is_held = False
                                    break
                            else:
                                if tk in named_keys and (user32.GetAsyncKeyState(named_keys[tk]) & 0x8000) == 0:
                                    is_held = False
                                    break
                    
                    if not is_held:
                        logger.info("🎯 [INPUT] Physical Hotkey Release Detected via Watchdog -> Stop recording")
                        self._is_pressed = False
                        self._active_keys.clear()
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, self.stop_recording_signal.emit)
                        break

    def _evaluate_hotkey_toggle(self):
        with self._lock:
            if self._target_keys and self._target_keys.issubset(self._active_keys):
                is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_pressed
                if is_rec:
                    logger.info("🎯 [INPUT] Hotkey Long-Press -> Toggle Stop recording")
                    self._is_pressed = False
                    self.stop_recording_signal.emit()
                else:
                    logger.info("🎯 [INPUT] Hotkey Long-Press -> Toggle Start recording")
                    self._is_pressed = True
                    self.start_recording_signal.emit()

    def _cancel_hotkey_timer(self):
        if self._hotkey_timer:
            try: self._hotkey_timer.cancel()
            except: pass
            self._hotkey_timer = None

    def update_config(self, hold_duration_s: float, mode: int):
        with self._lock:
            self._hold_duration_ms = int(hold_duration_s * 1000)
            self._recording_mode = mode
            self._cancel_hotkey_timer()
            self._hotkey_timer_active = False
            logger.info(f"HotkeyManager Config: mode={mode}, duration={hold_duration_s}s")

    def update_hotkey(self, hotkey_str):
        self._target_keys = self._parse_keys(hotkey_str)
        
    def update_magic_hotkey(self, magic_hotkey_str):
        self._magic_keys = self._parse_keys(magic_hotkey_str)
