# src/ui/handlers/voice_handler.py
import re
import numpy as np
from loguru import logger

class VoiceHandler:
    """
    [A636] PERFORMANCE & MONITORING LOCKED.
    - [REPRODUCTION_GUARD] Hand Release -> Instant Paste.
    - [REPRODUCTION_GUARD] Console Content Monitoring.
    """
    def __init__(self, controller):
        self.controller = controller

    def process_asr_result(self, text):
        """ [A636] Direct Output + Console Logging """
        if not text or not text.strip(): return
        
        # 1. Trimming (No aggressive stripping)
        clean_text = text.strip()
        if not clean_text: return
        
        # [A2] CRITICAL: If the text contains no actual words (Chinese, English, or digits), ignore it to prevent outputting noise
        if not re.search(r'[\u4e00-\u9fffa-zA-Z0-9]', clean_text):
            logger.info(f"🎙️ [INPUT] Bypassed non-speech/noise ASR result: '{clean_text}'")
            return
        
        # 2. Learning Engine Sync
        learned = self.controller.learning_engine.apply_habits(clean_text)
        
        # [A11] Convert periods in the middle of the text to commas while keeping trailing punctuation
        if learned:
            trailing_punc = ""
            while learned and learned[-1] in "。！？?!.":
                trailing_punc = learned[-1] + trailing_punc
                learned = learned[:-1]
            learned = learned.replace("。", "，").replace(".", "，")
            learned = learned + trailing_punc
            
        # [A2] CRITICAL: If output is 3 characters or less, remove all punctuation
        punc_pattern = r'[，。！？：；「」『』、（）—－\s,\.!\?()\[\]\{\}:;\-_“”]'
        effective_text = re.sub(punc_pattern, '', learned)
        if len(effective_text) <= 3:
            learned = effective_text
            
        if not learned: return
        
        # [A18] Block single character if it is "我" or "嗯"
        if learned in ["我", "嗯"]:
            logger.info(f"🎙️ [INPUT] Bypassed single word noise: '{learned}'")
            return
        
        # 3. DIRECT OUTPUT (Zero-Latency Pipe)
        self.controller._handle_asr_output_background(learned)
        
        # 4. [A636] CONSOLE MONITORING: Log text to console for user to see
        logger.info(f"🎙️ [INPUT] {learned}")

    def check_audio_gate(self, audio_data):
        if audio_data is None or len(audio_data) == 0: return False
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 0.0001: return False
        if len(audio_data) < 3200: return False
        return True
