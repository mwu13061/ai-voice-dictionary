# src/audio/engines/engine_v1_legacy.py
import os
import sys
import torch
import re
from loguru import logger
import numpy as np
from funasr import AutoModel as FunAutoModel
from opencc import OpenCC
from transformers import AutoTokenizer

class EngineV1Legacy:
    """
    [V1 Legacy] Build A80 Base
    - Fast ASR + LLM Correction (MiniMindOmni).
    - Known issue: Tensor mismatch causing LLM bypass in some environments.
    """
    def __init__(self, models_dir="models", device="cpu"):
        self.device = device
        self.cc = OpenCC('s2twp')
        self.llm_path = os.path.abspath(os.path.join(models_dir, "minimind-3o-hf"))
        self.asr_path = os.path.abspath(os.path.join(models_dir, "SenseVoiceSmall"))
        self.asr_model = None
        self.llm_model = None
        self.tokenizer = None

    def load(self):
        try:
            # Add to path to find local model_omni.py
            if self.llm_path not in sys.path: sys.path.append(self.llm_path)
            
            # 1. Ear
            self.asr_model = FunAutoModel(model=self.asr_path, device=self.device, disable_update=True)
            # 2. Brain (Omni mode)
            self.tokenizer = AutoTokenizer.from_pretrained(self.llm_path, trust_remote_code=True)
            import model_omni
            self.llm_model = model_omni.MiniMindOmni.from_pretrained(
                self.llm_path, torch_dtype=torch.float32
            ).to(self.device).eval()
            return True
        except Exception as e:
            logger.error(f"EngineV1 Load Error: {e}")
            return False

    def process(self, audio_data: np.ndarray) -> str:
        try:
            res = self.asr_model.generate(input=audio_data, cache={}, language="zh", use_itn=True)
            raw_asr = re.sub(r'<\|.*?\|>', '', res[0].get('text', '')).strip()
            if not raw_asr: return ""
            
            prompt = f"修正同音錯字，僅輸出繁體：\n{raw_asr}"
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.llm_model.generate(**inputs, max_new_tokens=48, temperature=0.1)
            
            corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True).replace(prompt, "").strip()
            return self.cc.convert(corrected if corrected else raw_asr)
        except Exception as e:
            logger.warning(f"EngineV1 AI Fallback: {e}")
            return self.cc.convert(raw_asr) if 'raw_asr' in locals() else ""
