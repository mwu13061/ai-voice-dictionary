# src/utils/output_plugins/plugin_v2_typing.py
import keyboard
from loguru import logger

class PluginV2Typing:
    """[V2] High-Speed Typewriter Effect"""
    def output(self, text: str):
        if not text: return
        try:
            # Optimized for efficiency
            keyboard.write(text, delay=0.005)
            return True
        except Exception as e:
            logger.error(f"Typing Plugin Error: {e}")
            return False
