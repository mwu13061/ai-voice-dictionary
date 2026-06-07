# src/audio/whisper_engine.py
import os
from faster_whisper import WhisperModel
from loguru import logger
import numpy as np

class WhisperEngine:
    """
    Wrapper for faster-whisper to provide fast local transcription.
    """
    def __init__(self, model_size="base", device="cpu", compute_type="auto"):
        """
        model_size: 'tiny', 'base', 'small', 'medium', 'large-v3'
        device: 'cpu' or 'cuda' (for NVIDIA GPU)
        compute_type: 'auto', 'int8', 'float16'
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def load_model(self):
        """ [A576/A577] Optimized Whisper Loading: Local-First with Watchdog """
        if self.model is None:
            logger.info(f"⌛ [ASR] Initializing Faster-Whisper ({self.model_size}) on {self.device}...")
            
            # [A577] Dynamically choose compute type if auto
            ct = self.compute_type
            if ct == "auto":
                ct = "float16" if self.device == "cuda" else "int8"
            
            # [A576] Watchdog
            def _watchdog():
                if self.model is None:
                    logger.warning(f"⏳ [ASR] Whisper load is taking a while... (下載中). Please wait.")
            
            import threading
            watchdog_timer = threading.Timer(10.0, _watchdog)
            watchdog_timer.start()

            try:
                from src.utils.path_helper import get_root_ascii_bridge
                download_root = os.path.join(os.getcwd(), "models", "whisper_cache")
                os.makedirs(download_root, exist_ok=True)
                safe_download_path = get_root_ascii_bridge(download_root)
                
                try:
                    self.model = WhisperModel(
                        self.model_size, 
                        device=self.device, 
                        compute_type=ct,
                        download_root=safe_download_path,
                        local_files_only=True,
                        cpu_threads=4
                    )
                    logger.success(f"✅ [ASR] Whisper ({self.model_size}) loaded from local cache.")
                except Exception:
                    logger.info(f"🌐 [ASR] Model '{self.model_size}' not found. Downloading (~480MB if small, ~145MB if base)...")
                    self.model = WhisperModel(
                        self.model_size, 
                        device=self.device, 
                        compute_type=ct,
                        download_root=safe_download_path,
                        local_files_only=False,
                        cpu_threads=4
                    )
                    logger.success(f"✅ [ASR] Whisper ({self.model_size}) ready.")
                    
            except Exception as e:
                logger.error(f"❌ [ASR] Whisper Load Fatal: {e}")
                raise
            finally:
                watchdog_timer.cancel()

    def transcribe(self, audio_data: np.ndarray) -> str:
        """ [A577] Transcription with Prompting """
        if self.model is None:
            self.load_model()
            
        logger.debug(f"Starting Whisper-{self.model_size} inference...")
        # [A577] initial_prompt helps guide the model to Traditional Chinese and correct context
        segments, info = self.model.transcribe(
            audio_data, 
            beam_size=5, 
            language="zh", 
            initial_prompt="以下是繁體中文的內容。" 
        )
        
        text = "".join([segment.text for segment in segments])
        logger.info(f"Whisper-{self.model_size} Result: {text}")
        return text.strip()
