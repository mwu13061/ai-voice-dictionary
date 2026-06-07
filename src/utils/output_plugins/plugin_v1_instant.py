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
        self.SendInput(n, input_array, ctypes.sizeof(INPUT))
        logger.success(f"🚀 [PERF] Atomic Unicode Injection completed for {len(text)} chars.")

    def output(self, text: str, mode: int = 0):
        """ [A634] ZERO-DELAY PIPE """
        if not text: return
        
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
                    time.sleep(0.002) # Very minimal sleep to let clipboard sync
                    user32.keybd_event(0x11, 0x1D, 0, 0) # Ctrl down
                    user32.keybd_event(0x56, 0x2F, 0, 0) # V down
                    time.sleep(0.01)
                    user32.keybd_event(0x56, 0x2F, 2, 0) # V up
                    user32.keybd_event(0x11, 0x1D, 2, 0) # Ctrl up
                except Exception as clipboard_err:
                    logger.warning(f"⚠️ Clipboard paste failed: {clipboard_err}. Falling back to Atomic Unicode Injection.")
                    self._unicode_inject(text)
            else:
                self._unicode_inject(text)
        except Exception as e: 
            logger.error(f"Output error: {e}")
            self._unicode_inject(text)
        finally:
            # Restore modifier keys if they were physically held down
            for vk in released:
                sc = vk_sc.get(vk, 0)
                user32.keybd_event(vk, sc, 0, 0) # KEYEVENTF_KEYDOWN
