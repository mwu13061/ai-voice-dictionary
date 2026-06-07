# src/audio/engines/engine_v2_stable.py
import os, sys, re, time
from loguru import logger
import numpy as np
from src.utils.path_helper import get_resource_path, get_external_resource

# [A613/A633] SPEED CRITICAL: Pre-import heavy libs at module level
import torch

class EngineV2Stable:
    """
    [V2 Stable] Build [A633] PERFORMANCE LOCKED.
    [REPRODUCTION_GUARD] No imports inside process() method.
    """
    def __init__(self, models_dir="models", device="cpu"):
        self.device = "cpu"
        self.cc_literal = None
        self.use_punc = True 
        self.asr_path = get_external_resource(os.path.join("models", "SenseVoiceSmall"))
        self.asr_model = None

    def load(self):
        try:
            from funasr import AutoModel as FunAutoModel
            from opencc import OpenCC
            
            # [A24] Optimize CPU threads for inference (2 threads is verified fastest for hybrid CPU)
            import os
            cores = os.cpu_count() or 4
            threads = min(2, cores)
            torch.set_num_threads(threads)
            try: torch.set_num_interop_threads(1)
            except: pass
            torch.set_grad_enabled(False)
            logger.info(f"⚙️ [ENGINE_V2] PyTorch CPU threads optimized: set to {threads}")
            
            # CUDA / GPU Acceleration detection with detailed logging
            cuda_available = torch.cuda.is_available()
            self.device = "cuda" if cuda_available else "cpu"
            
            logger.info("========================================")
            logger.info(f"⚙️ [ENGINE_V2] CUDA Acceleration Available: {cuda_available}")
            if cuda_available:
                logger.info(f"⚙️ [ENGINE_V2] GPU Name: {torch.cuda.get_device_name(0)}")
                logger.info(f"⚙️ [ENGINE_V2] CUDA Device Count: {torch.cuda.device_count()}")
            else:
                logger.warning(f"⚠️ [ENGINE_V2] CUDA not available. Running on CPU (Threads: default optimized).")
                logger.warning("⚠️ [ENGINE_V2] For 10x faster speech recognition, please install PyTorch with CUDA support.")
            logger.info("========================================")
            
            try: self.cc_literal = OpenCC('s2t')
            except: logger.warning("⚠️ OpenCC Load Failed.")

            if not os.path.exists(self.asr_path):
                logger.error(f"❌ Model Not Found: {self.asr_path}"); return False
            
            logger.info(f"⌛ [A633] Engine JIT Init (Device: {self.device})")
            self.asr_model = FunAutoModel(model=self.asr_path, device=self.device, disable_update=True, hub="ms")
            
            if self.asr_model is None: return False
            logger.success(f"✅ SenseVoice ASR Ready.")
            return True
        except Exception as e:
            import traceback; logger.error(f"❌ ASR Load Error:\n{traceback.format_exc()} viewer"); return False

    def update_config(self, config: dict):
        self.use_punc = bool(config.get("use_punc", True))

    def process(self, audio_data: np.ndarray) -> str:
        """ [A613/A633] SPEED LOCKED - NO IMPORTS OR IO IN THIS BLOCK """
        try:
            if not self.asr_model: return ""
            
            # [A633] Force inference mode for zero-overhead performance
            with torch.inference_mode():
                res = self.asr_model.generate(
                    input=audio_data, 
                    cache={},
                    language="zh", 
                    use_itn=self.use_punc
                )
                
            raw_asr = re.sub(r'<\|.*?\|>', '', res[0].get('text', '')).strip()
            if not raw_asr: return ""
            
            # [A402] Fast Traditional conversion
            return self.cc_literal.convert(raw_asr) if self.cc_literal else raw_asr
        except Exception as e:
            logger.error(f"ASR Process Error: {e}"); return ""

    def process_text(self, prompt: str) -> str: return ""
