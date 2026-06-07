# src/utils/text_output.py
import keyboard
import time
import pyperclip
import pyautogui
from loguru import logger

def output_text(text: str, mode: str = "paste"):
    """
    Handles outputting text to the active window.
    Modes:
    - 'paste': Instant via clipboard (Ctrl+V)
    - 'type': Fast typewriter effect via keyboard.write
    """
    if not text: return
    logger.info(f"Injecting text (Mode: {mode}): {text}")
    
    # 1. Clear any active modifiers
    modifiers = ['ctrl', 'shift', 'alt', 'win']
    for key in modifiers:
        try:
            if keyboard.is_pressed(key):
                pyautogui.keyUp(key)
        except: pass

    if mode == "paste":
        try:
            # 2a. Safely try to backup old clipboard (often locked by OS)
            old_clip = ""
            try:
                old_clip = pyperclip.paste()
            except Exception:
                pass # Ignore if we can't read it
                
            # 2b. Perform paste
            pyperclip.copy(text)
            keyboard.press_and_release('ctrl+v')
            time.sleep(0.02) # Give OS a moment to process the paste command
            
            # 2c. Safely restore
            if old_clip:
                try:
                    pyperclip.copy(old_clip)
                except Exception:
                    pass
            logger.success("Clipboard fast write executed.")
        except Exception as e:
            logger.error(f"Clipboard paste entirely failed: {e}")
            # Fallback to direct typing with ZERO delay for instant speed
            keyboard.write(text, delay=0)
            logger.info("Direct keyboard instant-fallback executed.")
    else:
        # Fast Typewriter Mode [A90]
        # Set a very small delay. Windows timer resolution might make this ~15ms per char.
        keyboard.write(text, delay=0.005)
        logger.success("Fast typewriter write executed.")

    time.sleep(0.05)
