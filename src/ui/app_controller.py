# src/ui/app_controller.py
import sys, os, threading, time, io, numpy as np, string, re, keyboard, pyautogui, pyperclip, queue
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from loguru import logger

from src.ui.recording_widget import RecordingWidget
from src.ui.settings_window import SettingsWindow, RefinementDialog, QuickAddDialog
from src.audio.audio_recorder import AudioRecorder
from src.utils.hotkey_manager import HotkeyManager
from src.utils.module_loader import ModuleLoader
from src.utils.learning_engine import LearningEngine
from src.ui.plugins.magic_menu import MagicMenu
from src.utils.smart_trigger import SmartTrigger 
from src.utils.cloud_engine import GeminiCloudEngine
from src.utils.screenshot_tool import ScreenshotTool
from src.utils.path_helper import get_resource_path 

from src.ui.handlers.macro_handler import MacroHandler
from src.ui.handlers.dict_handler import DictionaryHandler
from src.ui.handlers.voice_handler import VoiceHandler
from src.ui.handlers.vision_handler import VisionHandler
from src.ui.handlers.profile_handler import ProfileHandler

class ToastNotification(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 37, 47, 230);
                border: 1.5px solid #3498db;
                border-radius: 6px;
            }
            QLabel {
                color: #f1c40f;
                font-family: 'Microsoft JhengHei';
                font-size: 10pt;
                font-weight: bold;
                padding: 6px 12px;
            }
        """)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        l.addWidget(lbl)
        
        # Position at the center-bottom of the screen
        screen = QGuiApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.8) # 80% down
        self.move(x, y)
        
        # Auto-destruct after 3 seconds
        QTimer.singleShot(3000, self.close_toast)
        
    def close_toast(self):
        self.close()
        self.deleteLater()

class AppController(QObject):
    magic_request_triggered = Signal(str, str)
    magic_learn_triggered = Signal(str)
    ready_signal = Signal(str)
    asr_result_signal = Signal(str)
    vision_result_signal = Signal(str)
    launch_refinement_signal = Signal(str)
    refinement_result_signal = Signal(str)
    query_done_signal = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self._target_hwnd = None
        self._last_valid_target_hwnd = None
        self.is_recording = False
        self.is_engine_ready = False
        self._first_load_done = False
        self._lock = threading.Lock()
        self._physical_release_time = 0
        self._speech_detected = False
        self._is_continuous_restart = False
        
        self._asr_queue = queue.Queue()
        self._asr_worker_thread = threading.Thread(target=self._asr_worker, daemon=True)
        self._asr_worker_thread.start()
        
        self.settings = SettingsWindow()
        self.recorder = AudioRecorder()
        self.hotkey_manager = HotkeyManager()
        self.learning_engine = LearningEngine()
        self.smart_trigger = SmartTrigger()
        
        self.smart_trigger.controller = self
        self.hotkey_manager.controller = self
        self.cloud_engine = GeminiCloudEngine()
        self.engine = None
        self.output_plugin = None
        
        self.macro_handler = MacroHandler(self)
        self.dict_handler = DictionaryHandler(self)
        self.voice_handler = VoiceHandler(self)
        self.vision_handler = VisionHandler(self)
        self.profile_handler = ProfileHandler(self)
        
        self.ui = RecordingWidget()
        self.magic_menu = MagicMenu(self)
        self.tray = QSystemTrayIcon(self)
        
        self._setup_tray()
        self._connect_signals()
        
        self._vad_timer = QTimer()
        self._vad_timer.setSingleShot(True)
        self._vad_timer.timeout.connect(self.stop_session)
    
    def _setup_tray(self):
        icon_path = get_resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(QIcon.fromTheme("audio-input-microphone"))
            
        tm = QMenu()
        show_act = QAction("⚙️ 設定", self)
        show_act.triggered.connect(self._show_settings)
        exit_act = QAction("❌ 退出", self)
        exit_act.triggered.connect(self._safe_exit)
        tm.addAction(show_act)
        tm.addAction(exit_act)
        self.tray.setContextMenu(tm)
        self.tray.show()
    
    def _safe_exit(self):
        try:
            self.tray.hide()
            import os
            os._exit(0)
        except:
            sys.exit(0)
 
    def _connect_signals(self):
        # Hotkeys
        self.hotkey_manager.start_recording_signal.connect(self.request_start, Qt.QueuedConnection)
        self.hotkey_manager.stop_recording_signal.connect(self.request_stop, Qt.QueuedConnection)
        self.hotkey_manager.magic_menu_signal.connect(lambda: self._handle_smart_magic_trigger(""), Qt.QueuedConnection)
        
        # Smart Trigger
        self.smart_trigger.voice_start_signal.connect(self.request_start, Qt.QueuedConnection)
        self.smart_trigger.voice_stop_signal.connect(self.request_stop, Qt.QueuedConnection)
        self.smart_trigger.magic_signal.connect(self._handle_smart_magic_trigger, Qt.QueuedConnection)
        self.smart_trigger.click_signal.connect(self._handle_global_click, Qt.QueuedConnection)
        
        # Audio
        self.recorder.recording_finished.connect(self.on_audio_ready)
        self.recorder.volume_signal.connect(self._on_volume_update)
        self.asr_result_signal.connect(self._handle_asr_output)
        
        # Handlers
        self.magic_learn_triggered.connect(self.dict_handler.handle_magic_learn, Qt.QueuedConnection)
        self.settings.add_dict_requested.connect(self.dict_handler.add_item)
        self.settings.del_dict_requested.connect(self.dict_handler.del_item)
        self.settings.clear_dict_requested.connect(self.dict_handler.clear_all)
        self.settings.import_dict_requested.connect(self.dict_handler.import_items)
        
        self.launch_refinement_signal.connect(self.profile_handler.launch_refinement, Qt.QueuedConnection)
        self.refinement_result_signal.connect(self.profile_handler.deliver_result, Qt.QueuedConnection)
        self.vision_result_signal.connect(self.vision_handler.show_result_window, Qt.QueuedConnection)
        
        # UI & System
        self.ready_signal.connect(self._handle_ready_msg)
        self.query_done_signal.connect(self._on_query_done)
        self.settings.start_pairing_requested.connect(lambda: self.hotkey_manager.set_learning_mode(True))
        self.settings.stop_pairing_requested.connect(lambda: self.hotkey_manager.set_learning_mode(False))
        self.hotkey_manager.input_captured_signal.connect(self.settings.handle_captured_input)
        self.settings.settings_changed.connect(self.on_settings_updated)
        self.settings.preview_sound_requested.connect(lambda i: threading.Thread(target=self._play_selected_chime, args=("START", i), daemon=True).start())
        self.settings.launch_vision_requested.connect(self.vision_handler.start_snip)
        self.settings.preview_ui_requested.connect(self._preview_ui_position)
        self.ui.position_changed.connect(self.settings.update_ui_coords)
        self.magic_request_triggered.connect(self._handle_magic_action, Qt.QueuedConnection)
 
    def _handle_global_click(self, x, y):
        if self.magic_menu and self.magic_menu.isVisible() and not self.magic_menu.underMouse():
            self.magic_menu.close()
 
    def _handle_magic_action(self, mode, captured_text):
        if mode == "SETTINGS":
            self._show_settings()
        elif mode == "VISION":
            self.vision_handler.start_snip()
        elif mode == "LEARN":
            self.magic_learn_triggered.emit(captured_text)
        elif mode == "FIX":
            self.launch_refinement_signal.emit(captured_text)
        else:
            self.macro_handler.execute_macro(mode)
 
    def _is_valid_external_hwnd(self, hwnd):
        if not hwnd:
            return False
        try:
            import ctypes
            import os
            from ctypes import wintypes
            
            # 1. Check if PID matches current process
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                # Allow voice input inside our own QuickAddDialog and DictionaryManager
                try:
                    if hasattr(self, 'dict_handler') and self.dict_handler and self.dict_handler.quick_dlg:
                        quick_dlg_hwnd = int(self.dict_handler.quick_dlg.winId())
                        root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) # GA_ROOT = 2
                        if root_hwnd == quick_dlg_hwnd:
                            return True
                    if hasattr(self, 'settings') and self.settings and hasattr(self.settings, 'dict_dlg') and self.settings.dict_dlg:
                        dict_dlg_hwnd = int(self.settings.dict_dlg.winId())
                        root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) # GA_ROOT = 2
                        if root_hwnd == dict_dlg_hwnd:
                            return True
                except Exception as e:
                    import logging
                    logging.warning(f"Error matching own window hwnd: {e}")
                return False
                
            # 2. Check window title for Antigravity/assistant elements
            buf_title = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf_title, 512)
            title = buf_title.value.lower() if buf_title.value else ""
            
            invalid_keywords = [
                "antigravity", "總司令指揮所", "ai語音助手", "助理設定", 
                "voice assistant", "pythonw", "python"
            ]
            for kw in invalid_keywords:
                if kw in title:
                    return False
                    
            # 3. Check process name of the HWND
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_proc = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            proc_name = ""
            if h_proc:
                buf_path = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_proc, 0, buf_path, ctypes.byref(size)):
                    proc_name = os.path.basename(buf_path.value).lower()
                ctypes.windll.kernel32.CloseHandle(h_proc)
                
            if "python" in proc_name or "cmd.exe" in proc_name:
                # Exclude terminal/CLI windows running our app
                if any(x in title for x in ["main.py", "啟動語音助手", "run", "terminal", "powershell"]):
                    return False
                    
            return True
        except Exception as ex:
            logger.warning(f"Error checking HWND validity: {ex}")
            return False

    def _capture_focused_hwnd(self):
        try:
            import ctypes
            from ctypes import wintypes
            
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("hwndActive", wintypes.HWND),
                    ("hwndFocus", wintypes.HWND),
                    ("hwndCapture", wintypes.HWND),
                    ("hwndMenuOwner", wintypes.HWND),
                    ("hwndMoveSize", wintypes.HWND),
                    ("hwndCaret", wintypes.HWND),
                    ("rcCaret", wintypes.RECT)
                ]
                
            gui = GUITHREADINFO()
            gui.cbSize = ctypes.sizeof(GUITHREADINFO)
            
            if ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(gui)):
                # If hwndFocus is valid, it's the exact focused typing control (like Edit in Notepad or active caret input)
                # If not, fallback to hwndActive (the active foreground window)
                hwnd = gui.hwndFocus or gui.hwndActive
                if hwnd:
                    return hwnd
            
            return ctypes.windll.user32.GetForegroundWindow()
        except Exception as ex:
            logger.warning(f"Error in GetGUIThreadInfo: {ex}")
            try:
                import ctypes
                return ctypes.windll.user32.GetForegroundWindow()
            except:
                return None

    def request_start(self):
        with self._lock:
            if self.is_recording: return
            self.is_recording = True
            
            # Capture target window HWND when recording starts using high-precision caret focus
            try:
                hwnd = self._capture_focused_hwnd()
                if hwnd and self._is_valid_external_hwnd(hwnd):
                    self._target_hwnd = hwnd
                    self._last_valid_target_hwnd = hwnd
                    logger.debug(f"🎯 [OUTPUT] Target HWND captured: {self._target_hwnd}")
                else:
                    # Fallback to last valid HWND if current is invalid (self app/terminal)
                    if self._last_valid_target_hwnd and self._is_valid_external_hwnd(self._last_valid_target_hwnd):
                        self._target_hwnd = self._last_valid_target_hwnd
                    else:
                        self._target_hwnd = None
                    logger.debug(f"🎯 [OUTPUT] Current foreground is invalid. Fallback HWND: {self._target_hwnd}")
            except Exception as e:
                logger.warning(f"Failed to capture target HWND: {e}")
                self._target_hwnd = self._last_valid_target_hwnd if self._last_valid_target_hwnd else None
            
            ui_idx = self.settings.raw_config.get("recording_style", 1)
            m = {0: 2, 1: 0, 2: 1}
            self.ui.set_style(m.get(ui_idx, 0))
            
            if not self.is_engine_ready:
                self.ui.set_loading_state()
            else:
                self.ui.show_recording()
                
            # [A20] Run VAD safety timeout only in Toggle Mode (1, 2)
            if self.settings.raw_config.get("recording_mode", 0) in [1, 2]:
                self._speech_detected = False
                self._is_continuous_restart = False
                timeout_val = float(self.settings.raw_config.get("silence_timeout", 5.0))
                init_timeout = max(5.0, timeout_val)
                self._vad_timer.start(int(init_timeout * 1000))
                
            if self.settings.raw_config.get("audio_cue", True):
                self._play_selected_chime("START")
                time.sleep(0.1)
                
            self.recorder.start_recording(streaming=False)
 
    def request_stop(self):
        with self._lock:
            if not self.is_recording: return
            self._physical_release_time = time.time()
            self.is_recording = False
            self._vad_timer.stop()
            self.ui.hide()
            self.recorder.stop_recording(emit=True)
            if self.settings.raw_config.get("audio_cue", True):
                threading.Thread(target=self._play_selected_chime, args=("STOP",), daemon=True).start()
 
    def _asr_worker(self):
        while True:
            try:
                item = self._asr_queue.get()
                if item is None:
                    break
                audio_data, is_restart = item
                try:
                    if self.engine and self.is_engine_ready:
                        raw_text = self.engine.process(audio_data)
                        self.voice_handler.process_asr_result(raw_text)
                except Exception as e:
                    logger.error(f"ASR worker inference error: {e}")
                finally:
                    if not is_restart:
                        QTimer.singleShot(0, self.ui.hide)
                    self._asr_queue.task_done()
            except Exception as e:
                logger.error(f"ASR worker loop error: {e}")
                time.sleep(0.05)

    def on_audio_ready(self, audio_data: np.ndarray):
        is_restart = getattr(self, "_is_continuous_restart", False)
        self._is_continuous_restart = False
        if not self.voice_handler.check_audio_gate(audio_data):
            if not is_restart:
                QTimer.singleShot(0, self.ui.hide)
            return
        self._asr_queue.put((audio_data, is_restart))
 
    def _force_foreground_window(self, hwnd):
        try:
            import ctypes
            from ctypes import wintypes
            import time
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            if user32.GetForegroundWindow() == hwnd:
                return True
                
            user32.BringWindowToTop(hwnd)
            if user32.SetForegroundWindow(hwnd):
                return True
                
            current_tid = kernel32.GetCurrentThreadId()
            foreground_tid = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
            
            attached = False
            if current_tid != foreground_tid and foreground_tid != 0:
                attached = user32.AttachThreadInput(current_tid, foreground_tid, True)
                
            try:
                user32.BringWindowToTop(hwnd)
                user32.ShowWindow(hwnd, 5) # SW_SHOW
                for _ in range(3):
                    if user32.SetForegroundWindow(hwnd):
                        return True
                    time.sleep(0.01)
                return False
            finally:
                if attached:
                    user32.AttachThreadInput(current_tid, foreground_tid, False)
        except Exception as e:
            logger.error(f"❌ [OUTPUT] _force_foreground_window error: {e}")
            return False

    def _handle_asr_output_background(self, text):
        if self.output_plugin:
            target = self._target_hwnd
            focus_ok = False
            if target:
                focus_ok = self._force_foreground_window(target)
                if not focus_ok:
                    try:
                        import ctypes
                        curr = ctypes.windll.user32.GetForegroundWindow()
                        buf = ctypes.create_unicode_buffer(256)
                        ctypes.windll.user32.GetWindowTextW(curr, buf, 256)
                        logger.warning(f"⚠️ [OUTPUT] Cannot restore focus. Current window: '{buf.value}'. Output may land in wrong app!")
                    except:
                        pass
            logger.info(f"📤 [OUTPUT] Sending to plugin: '{text}' (focus_restored={focus_ok})")
            self.output_plugin.output(text, mode=self.settings.raw_config.get("output_mode", 0))
 
    def _handle_asr_output(self, text):
        self._handle_asr_output_background(text)
 
    def _async_engine_load(self, ev, config=None):
        try:
            self.engine = ModuleLoader.load_engine(ev)
            if self.engine: 
                self.engine.load()
                if hasattr(self.engine, "update_config") and config:
                    self.engine.update_config(config)
                self.is_engine_ready = True
                self.ready_signal.emit("✅ 語音引擎就緒")
                if not self._first_load_done:
                    self._first_load_done = True
                    threading.Thread(target=self._play_selected_chime, args=("START", 9), daemon=True).start()
        except Exception as e:
            logger.error(f"Load Error: {e}")
 
    def on_settings_updated(self, config):
        try:
            import ctypes
            hWnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hWnd:
                ctypes.windll.user32.ShowWindow(hWnd, 5 if config.get("show_console", True) else 0)
        except: pass
        
        self.hotkey_manager.update_hotkey(config.get("hotkey", "ctrl+shift+win"))
        self.hotkey_manager.update_magic_hotkey(config.get("magic_hotkey", "alt+win"))
        self.hotkey_manager.update_config(
            hold_duration_s=config.get("smart_hold_duration", 0.5),
            mode=config.get("recording_mode", 0)
        )
        
        self.smart_trigger.set_enabled(
            left=config.get("smart_left", True), 
            right=config.get("smart_right", True), 
            hold_duration_s=config.get("smart_hold_duration", 0.5),
            mode=config.get("recording_mode", 0)
        )
        
        self.cloud_engine.configure(config.get("gemini_api_key", ""), config.get("opt_model", ""))
        self.output_plugin = ModuleLoader.load_output_plugin(config.get("output_version", "v1_instant"))
        
        ev = config.get("engine_version", "v2_stable")
        current_ev = getattr(self, "_current_engine_ver", None)
        
        if not self.engine or ev != current_ev:
            self._current_engine_ver = ev
            self.is_engine_ready = False
            threading.Thread(target=self._async_engine_load, args=(ev, config), daemon=True).start()
        elif hasattr(self.engine, "update_config"):
            self.engine.update_config(config)

    def _show_settings(self):
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def _handle_ready_msg(self, m): 
        logger.info(f"📢 [NOTIFICATION] {m}")
        toast = ToastNotification(m)
        toast.show()
        self._active_toast = toast

    def _on_query_done(self, ok, msg):
        pass

    def _handle_smart_magic_trigger(self, text=""):
        # Dismiss any editor context menu first by simulating Esc
        try: keyboard.press_and_release('esc')
        except: pass
        # [A636] Use QTimer to ensure the popup happens on main thread but after event loop
        QTimer.singleShot(50, lambda: self.magic_menu.popup_at_cursor(text))

    def _preview_ui_position(self):
        self.ui.enter_positioning_mode("📍 請拖曳。點擊畫面任一處結束...")

    def _play_selected_chime(self, mode="START", style=None):
        if style is None: style = self.settings.raw_config.get("sound_style_idx", 9)
        if style == 0: return
        try:
            import winsound
            s = [(1000,50),(800,50),(1000,50),(400,50),(1200,50),(1500,50),(600,50),(900,50),(1100,50),(1300,50),(1000,50),(1200,50),(2000,50),(500,50),(1800,50)]
            f, d = s[style] if style < len(s) else (1000, 50)
            if mode == "STOP":
                f = int(f * 0.8) # 20% lower pitch for Stop confirmation
            winsound.Beep(f, d)
        except: pass
 
    def _on_volume_update(self, e):
        s = self.settings.raw_config.get("vad_sensitivity", 50)
        th = 0.1 * (1.02 ** (50 - s))
        if self.is_recording and self.settings.raw_config.get("recording_mode", 0) in [1, 2]:
            if e > th:
                self._speech_detected = True
                self._vad_timer.start(1000)

    def run(self):
        self.settings.load_settings()
        self.settings.update_dict_list(self.learning_engine.list_all())
        self.on_settings_updated(self.settings.raw_config)
        self.ui.set_initial_position(self.settings.raw_config.get("ui_x", 800), self.settings.raw_config.get("ui_y", 100))
        self.hotkey_manager.initialize(
            self.settings.raw_config.get("hotkey"), 
            self.settings.raw_config.get("magic_hotkey"), 
            smart_trigger=self.smart_trigger
        )

    def stop_session(self):
        mode = self.settings.raw_config.get("recording_mode", 0)
        if mode not in [1, 2]:
            # PTT mode should not have VAD timeout logic at all
            logger.warning(f"📡 [VAD] stop_session called in non-toggle mode {mode}. Ignoring.")
            return

        if self._speech_detected:
            # [A16] Silence detected after speech (1s): transcribe what was said, but continue recording
            logger.info("📡 [VAD] Speech pause detected (1s). Flushing buffer and continuing recording...")
            self._is_continuous_restart = True
            
            # Flush buffer and run inference
            audio_data = self.recorder.flush_buffer()
            if len(audio_data) > 0:
                self.on_audio_ready(audio_data)
                
            self._speech_detected = False
            self._vad_timer.start(5000) # Reset to 5s initial timeout
        else:
            if mode == 2:
                # In Toggle Mode B (2), we NEVER stop on idle silence, just reset VAD countdown
                logger.info(f"📡 [VAD] Idle silence timeout in mode {mode}. Keeping recording session active.")
                self._speech_detected = False
                self._vad_timer.start(5000)
            else:
                logger.info("📡 [VAD] Stopping recording session completely.")
                self.request_stop()
