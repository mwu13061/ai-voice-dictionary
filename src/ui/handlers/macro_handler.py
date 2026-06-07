# src/ui/handlers/macro_handler.py
import time
import threading
import keyboard
import pyperclip
from loguru import logger

class MacroHandler:
    """
    [A542/A558/A560] FINAL HARDENED Macro & Capture Handler.
    Physically isolated to prevent any regression.
    Fixes interference between text capture and custom macros.
    """
    def __init__(self, controller):
        self.controller = controller

    def trigger_action(self, mode):
        """ [A560] Entry point for Magic Menu actions """
        # [A558] Handle modes that don't need text capture
        if mode in ["VISION", "SETTINGS"]:
            self.controller.magic_request_triggered_dispatch(mode, "")
            return
            
        # [A560] Custom macros should NOT trigger bulletproof_capture
        # Capture is ONLY for AI refinement (FIX) and Dictionary (LEARN)
        if mode in ["FIX", "LEARN"]:
            threading.Thread(target=self.bulletproof_capture, args=(mode,), daemon=True).start()
        elif mode.startswith("macro_"):
            # Execute immediately to avoid 1.5s delay and Ctrl+C interference
            self.controller.magic_request_triggered_dispatch(mode, "")

    def bulletproof_capture(self, mode):
        """ [A542] Ultra-Harden Capture: Explicit Key Sequences """
        try:
            time.sleep(0.5) # Initial calm-down
            pyperclip.copy("")
            
            # Step 1: Explicit Copy
            logger.debug("⌨️ [MACRO] Attempting explicit Ctrl+C sequence...")
            keyboard.press('ctrl')
            time.sleep(0.1)
            keyboard.press('c')
            time.sleep(0.2)
            keyboard.release('c')
            keyboard.release('ctrl')
            
            time.sleep(0.5) # Wait for OS clipboard
            captured = pyperclip.paste().strip()
            
            if not captured:
                logger.warning("⚠️ [MACRO] Capture empty, trying Select All + Copy...")
                # Step 2: Explicit Select All
                keyboard.press('ctrl')
                time.sleep(0.1)
                keyboard.press('a')
                time.sleep(0.2)
                keyboard.release('a')
                keyboard.release('ctrl')
                
                time.sleep(0.3)
                
                # Step 3: Explicit Copy Again
                keyboard.press('ctrl')
                time.sleep(0.1)
                keyboard.press('c')
                time.sleep(0.2)
                keyboard.release('c')
                keyboard.release('ctrl')
                
                time.sleep(0.5)
                captured = pyperclip.paste().strip()
            
            # Dispatch result back to main controller signals
            self.controller.magic_request_triggered_dispatch(mode, captured)
        except Exception as e:
            logger.error(f"❌ [MACRO_HANDLER] Capture Error: {e}")

    def execute_macro(self, macro_id):
        """ [A542/A560/A586/A588] Execute Macros & External Apps """
        items = self.controller.settings.raw_config.get("magic_items", [])
        macro = next((x for x in items if x["id"] == macro_id), None)
        if not macro or not macro.get("val"): return
        
        try:
            logger.info(f"🚀 [MACRO_HANDLER] Executing: {macro['name']} (Type: {macro.get('type', 'combo')})")
            
            # [A23] Custom Text Input Execution
            if macro.get("type") == "text":
                val = macro["val"]
                logger.info(f"📝 [MACRO_HANDLER] Outputting text macro: '{val}'")
                self.controller._handle_asr_output_background(val)
                return
            
            # [A586/A588/A589] External Application Execution
            if macro.get("type") == "app":
                app_path = macro["val"].strip().strip('"\'')
                import os
                import sys
                import subprocess
                import ctypes
                
                try:
                    if app_path == "system://clipboard":
                        logger.info("📋 [MACRO_HANDLER] Simulating Win+V to show Clipboard History...")
                        keyboard.press_and_release('win+v')
                    elif app_path.lower().endswith(".py"):
                        # Execute python script explicitly
                        subprocess.Popen([sys.executable, app_path], shell=True)
                    else:
                        # [A589] Use native Windows ShellExecute (os.startfile)
                        class Wow64DisableRedirection:
                            def __enter__(self):
                                self.old_value = ctypes.c_void_p()
                                try:
                                    ctypes.windll.kernel32.Wow64DisableWow64FsRedirection(ctypes.byref(self.old_value))
                                except: pass
                            def __exit__(self, exc_type, exc_val, exc_tb):
                                try:
                                    ctypes.windll.kernel32.Wow64RevertWow64FsRedirection(self.old_value)
                                except: pass
                                
                        with Wow64DisableRedirection():
                            os.startfile(app_path)
                    logger.success(f"✅ [MACRO_HANDLER] Launched App: {app_path}")
                except Exception as e:
                    logger.error(f"❌ [MACRO_HANDLER] Failed to launch {app_path}: {e}")
                return

            # Default Keyboard Combo Execution
            steps = [s.strip().lower() for s in macro["val"].split(',')]
            
            for step in steps:
                if '+' in step:
                    # [A542] Explicit MODIFIER handling
                    parts = [p.strip() for p in step.split('+')]
                    mods = [p for p in parts if p in ['ctrl', 'shift', 'alt', 'win']]
                    keys = [p for p in parts if p not in mods]
                    
                    # Press mods
                    for m in mods: keyboard.press(m); time.sleep(0.05)
                    # Press keys
                    for k in keys: keyboard.press(k); time.sleep(0.05)
                    
                    time.sleep(0.2) # Hold duration
                    
                    # Release reverse
                    for k in reversed(keys): keyboard.release(k)
                    for m in reversed(mods): keyboard.release(m)
                else:
                    keyboard.press_and_release(step)
                
                time.sleep(0.3) # Heavy delay between steps for stability
        except Exception as e:
            logger.error(f"❌ [MACRO_HANDLER] Macro Error: {e}")
