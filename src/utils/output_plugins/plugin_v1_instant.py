# src/utils/output_plugins/plugin_v1_instant.py
import time, ctypes, pyperclip, keyboard
from ctypes import wintypes
from loguru import logger

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]
class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]
class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("iu", INPUT_UNION)]

class OutputPlugin:
    """
    [A634] ULTRA-SPEED OUTPUT.
    [REPRODUCTION_GUARD] Hand Release -> Instant Paste (0.015s target).
    """
    def __init__(self):
        self.SendInput = ctypes.windll.user32.SendInput
        self.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.SendInput.restype = wintypes.UINT

    def _is_physically_pressed(self, vk):
        return (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0

    def _robust_clipboard_copy(self, text, retries=10, delay=0.005):
        # Direct Win32 implementation with automatic retries for locked clipboard
        import ctypes
        from ctypes import wintypes
        
        OpenClipboard = ctypes.windll.user32.OpenClipboard
        EmptyClipboard = ctypes.windll.user32.EmptyClipboard
        SetClipboardData = ctypes.windll.user32.SetClipboardData
        CloseClipboard = ctypes.windll.user32.CloseClipboard
        GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
        GlobalLock = ctypes.windll.kernel32.GlobalLock
        GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
        
        OpenClipboard.argtypes = [wintypes.HWND]
        OpenClipboard.restype = wintypes.BOOL
        EmptyClipboard.argtypes = []
        EmptyClipboard.restype = wintypes.BOOL
        SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        SetClipboardData.restype = wintypes.HANDLE
        CloseClipboard.argtypes = []
        CloseClipboard.restype = wintypes.BOOL
        
        GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        GlobalAlloc.restype = wintypes.HANDLE
        GlobalLock.argtypes = [wintypes.HANDLE]
        GlobalLock.restype = ctypes.c_void_p
        GlobalUnlock.argtypes = [wintypes.HANDLE]
        GlobalUnlock.restype = wintypes.BOOL
        
        unicode_text = text.encode('utf-16le') + b'\x00\x00'
        
        opened = False
        for i in range(retries):
            if OpenClipboard(None):
                opened = True
                break
            time.sleep(delay)
            
        if not opened:
            raise RuntimeError("Clipboard locked and cannot be opened.")
            
        try:
            EmptyClipboard()
            h_mem = GlobalAlloc(0x0002, len(unicode_text)) # GMEM_MOVEABLE = 0x0002
            if not h_mem:
                raise RuntimeError("GlobalAlloc failed.")
            p_mem = GlobalLock(h_mem)
            if not p_mem:
                raise RuntimeError("GlobalLock failed.")
            ctypes.memmove(p_mem, unicode_text, len(unicode_text))
            GlobalUnlock(h_mem)
            if not SetClipboardData(13, h_mem): # CF_UNICODETEXT = 13
                raise RuntimeError("SetClipboardData failed.")
        finally:
            CloseClipboard()

    def _unicode_inject(self, text: str):
        inputs = []
        for char in text:
            cp = ord(char)
            # INPUT_KEYBOARD = 1, KEYEVENTF_UNICODE = 0x0004, KEYEVENTF_KEYUP = 0x0002
            inputs.append(INPUT(1, INPUT_UNION(ki=KEYBDINPUT(0, cp, 0x0004, 0, None))))
            inputs.append(INPUT(1, INPUT_UNION(ki=KEYBDINPUT(0, cp, 0x0004 | 0x0002, 0, None))))
        
        n = len(inputs)
        input_array = (INPUT * n)(*inputs)
        sent = self.SendInput(n, input_array, ctypes.sizeof(INPUT))
        if sent < n:
            logger.warning(f"⚠️ [OUTPUT] SendInput injected only {sent}/{n} events. This is typically blocked by Windows UIPI if the target window is running as Administrator (Elevated), or if the screen/workstation is locked.")
        else:
            logger.success(f"🚀 [PERF] Atomic Unicode Injection completed for {len(text)} chars.")

    def _log_foreground_window_diagnostics(self):
        try:
            import os
            # Define types and functions
            GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
            GetForegroundWindow.restype = wintypes.HWND

            GetWindowTextW = ctypes.windll.user32.GetWindowTextW
            GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            GetWindowTextW.restype = ctypes.c_int

            GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
            GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            GetWindowThreadProcessId.restype = wintypes.DWORD

            GetLastError = ctypes.windll.kernel32.GetLastError
            GetLastError.restype = wintypes.DWORD

            hwnd = GetForegroundWindow()
            if not hwnd:
                logger.info("ℹ️ [OUTPUT_DIAGNOSTICS] No active foreground window detected.")
                return

            # Get Title
            title_buf = ctypes.create_unicode_buffer(512)
            GetWindowTextW(hwnd, title_buf, 512)
            title = title_buf.value or "Untitled / Unknown"

            # Get PID
            pid = wintypes.DWORD(0)
            GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            target_pid = pid.value

            # Get Process Name
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            OpenProcess = ctypes.windll.kernel32.OpenProcess
            OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            OpenProcess.restype = wintypes.HANDLE
            
            CloseHandle = ctypes.windll.kernel32.CloseHandle
            CloseHandle.argtypes = [wintypes.HANDLE]
            CloseHandle.restype = wintypes.BOOL
            
            QueryFullProcessImageNameW = ctypes.windll.kernel32.QueryFullProcessImageNameW
            QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
            QueryFullProcessImageNameW.restype = wintypes.BOOL

            h_proc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, target_pid)
            proc_name = "Unknown"
            is_elevated_guess = False
            
            if h_proc:
                buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                    proc_name = os.path.basename(buf.value)
                CloseHandle(h_proc)
            else:
                err = GetLastError()
                if err == 5: # Access Denied
                    proc_name = "Access Denied (Target process likely runs as Administrator)"
                    is_elevated_guess = True
                else:
                    proc_name = f"OpenProcess failed (Code {err})"

            # Our app status
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            
            # Check if focus is our own app window
            my_pid = os.getpid()
            is_own_window = (target_pid == my_pid)

            # Check physically pressed modifiers
            pressed_modifiers = []
            for name, vk in [("Shift", 0x10), ("Ctrl", 0x11), ("Alt", 0x12), ("WinLeft", 0x5B), ("WinRight", 0x5C)]:
                if (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0:
                    pressed_modifiers.append(name)

            # Log summary
            diag_msg = (
                f"🖥️ [OUTPUT_DIAGNOSTICS] Active Window: [{title}] | Process: {proc_name} (PID: {target_pid}) | "
                f"App Admin: {is_admin} | Target Admin Guess: {is_elevated_guess} | Active Modifiers: {pressed_modifiers}"
            )
            logger.info(diag_msg)

            if is_own_window:
                logger.warning("⚠️ [OUTPUT_DIAGNOSTICS] WARNING: The foreground window belongs to the AI Assistant itself. The text cannot paste into another application unless you focus on that application first.")
            elif is_elevated_guess and not is_admin:
                logger.warning("⚠️ [OUTPUT_DIAGNOSTICS] PRIVILEGE MISMATCH WARNING: The target window runs as Administrator (Elevated), but this Assistant runs as a normal user. Windows UIPI will BLOCK all simulated inputs. Please run the AI Assistant as Administrator to output text to this window.")

        except Exception as e:
            logger.error(f"❌ [OUTPUT_DIAGNOSTICS] Failed to gather active window info: {e}")

    def output(self, text: str, mode: int = 0):
        """ [A634] ZERO-DELAY PIPE """
        if not text: return
        
        self._log_foreground_window_diagnostics()
        
        # Virtually release modifiers natively using keybd_event to avoid races or paste failures
        vks = [0x10, 0x11, 0x12, 0x5B, 0x5C] # shift, ctrl, alt, win
        vk_sc = {0x10: 0x2A, 0x11: 0x1D, 0x12: 0x38, 0x5B: 0x5B, 0x5C: 0x5C}
        user32 = ctypes.windll.user32
        released = []
        for vk in vks:
            if (user32.GetAsyncKeyState(vk) & 0x8000) != 0:
                sc = vk_sc.get(vk, 0)
                user32.keybd_event(vk, sc, 2, 0) # KEYEVENTF_KEYUP
                released.append(vk)
                
        try:
            if mode == 0:
                try:
                    self._robust_clipboard_copy(text)
                    
                    # [A63] Verify clipboard content was set correctly before sending Ctrl+V
                    verify_ok = False
                    for _ in range(8):
                        time.sleep(0.008)  # 8ms per check, up from 2ms total
                        try:
                            cb_content = pyperclip.paste()
                            if cb_content == text:
                                verify_ok = True
                                break
                        except:
                            pass
                    
                    if not verify_ok:
                        logger.warning(f"⚠️ [OUTPUT] Clipboard verify failed after 64ms, falling back to Unicode inject")
                        self._unicode_inject(text)
                    else:
                        logger.info(f"📋 [OUTPUT] Clipboard verified OK, sending Ctrl+V for {len(text)} chars")
                        user32.keybd_event(0x11, 0x1D, 0, 0) # Ctrl down
                        user32.keybd_event(0x56, 0x2F, 0, 0) # V down
                        time.sleep(0.015)  # 15ms (up from 10ms) for slow IME environments
                        user32.keybd_event(0x56, 0x2F, 2, 0) # V up
                        user32.keybd_event(0x11, 0x1D, 2, 0) # Ctrl up
                        logger.info(f"✅ [OUTPUT] Ctrl+V sent successfully")
                except Exception as clipboard_err:
                    logger.warning(f"⚠️ [OUTPUT] Clipboard paste failed: {clipboard_err}. Falling back to Atomic Unicode Injection.")
                    self._unicode_inject(text)
            else:
                self._unicode_inject(text)
        except Exception as e: 
            logger.error(f"❌ [OUTPUT] Fatal output error: {e}")
            self._unicode_inject(text)
        finally:
            # Restore modifier keys if they were physically held down
            for vk in released:
                sc = vk_sc.get(vk, 0)
                user32.keybd_event(vk, sc, 0, 0) # KEYEVENTF_KEYDOWN

