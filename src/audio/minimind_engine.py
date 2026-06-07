import os
import sys
import torch
import re
import time
from loguru import logger
import numpy as np
from funasr import AutoModel as FunAutoModel
from opencc import OpenCC
from transformers import AutoTokenizer, SiglipImageProcessor
from PIL import Image
import io

# Path management
MODEL_HF_PATH = os.path.join(os.getcwd(), "models", "minimind-3o-hf")
if MODEL_HF_PATH not in sys.path: sys.path.append(MODEL_HF_PATH)

try:
    from model_omni import MiniMindOmni, OmniConfig
except ImportError:
    MiniMindOmni = None

class MiniMindEngine:
    """
    Build A129: THE TRUTH ABOUT LOCAL VISION.
    Uses polling-safe loading and direct device placement.
    """
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.asr_model = None
        self.llm_model = None 
        self.tokenizer = None
        self.cc = OpenCC('s2twp')
        
        self.llm_path = os.path.abspath(os.path.join(models_dir, "minimind-3o-hf"))
        self.asr_path = os.path.abspath(os.path.join(models_dir, "SenseVoiceSmall"))
        self.siglip_path = os.path.abspath(os.path.join(models_dir, "siglip2"))

    def load_engine(self):
        logger.info(f"Loading AI Brains on {self.device}...")
        try:
            # 1. Ear
            if self.asr_model is None:
                self.asr_model = FunAutoModel(model=self.asr_path, device=self.device, disable_update=True)
            # 2. Tokenizer
            if self.tokenizer is None:
                self.tokenizer = AutoTokenizer.from_pretrained(self.llm_path, trust_remote_code=True)
            
            # 3. REAL LOCAL VISION LOAD [A129]
            if MiniMindOmni and self.llm_model is None:
                logger.info("Step 3: Initializing MiniMind-Omni (Safe Load)...")
                
                # Prevent Meta Tensor issues
                with torch.device("cpu"):
                    config = OmniConfig.from_pretrained(self.llm_path)
                    self.llm_model = MiniMindOmni(
                        config, 
                        audio_encoder_path=self.asr_path,
                        vision_model_path=self.siglip_path
                    )
                
                weights_path = os.path.join(self.llm_path, "pytorch_model.bin")
                if os.path.exists(weights_path):
                    logger.info("Loading weights into CPU memory...")
                    state_dict = torch.load(weights_path, map_location="cpu")
                    self.llm_model.load_state_dict(state_dict, strict=False)
                    self.llm_model.to(self.device).eval()
                    logger.success("✅ LOCAL VISION ENGINE LOADED SUCCESSFULLY")
                else:
                    logger.error("pytorch_model.bin missing.")
            
            logger.success(f"AI Brains LOADED")
        except Exception as e:
            logger.error(f"AI Load Error: {e}")

    def process_image(self, pil_image: Image.Image, prompt="OCR並翻譯成繁體中文") -> str:
        """ [A129] REAL Local Vision Inference """
        if self.llm_model is None: self.load_engine()
        try:
            # Ensure model is ready
            if hasattr(self.llm_model, 'vision_encoder') and self.llm_model.vision_encoder:
                # Build Prompt
                img_prompt = f"<|image_pad|>\n{prompt}"
                inputs = self.tokenizer(img_prompt, return_tensors="pt").to(self.device)
                
                with torch.inference_mode():
                    outputs = self.llm_model.generate(
                        inputs["input_ids"],
                        images=[pil_image],
                        max_new_tokens=256,
                        temperature=0.1,
                        do_sample=False
                    )
                    res = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
                    return self.cc.convert(res)
            return "[本地辨識失敗] 視覺權重未成功載入。"
        except Exception as e:
            logger.error(f"Vision Inference Error: {e}")
            return f"[本地辨識失敗] 錯誤原因: {e}"

    def _remove_stutters(self, text: str) -> str:
        if not text: return ""
        for length in range(1, 5):
            pattern = re.compile(r"(.{"+str(length)+r"})\1+")
            text = pattern.sub(r"\1", text)
        return text

    def process_voice_to_text(self, audio_data: np.ndarray, mode="standard") -> str:
        if self.asr_model is None: self.load_engine()
        try:
            res = self.asr_model.generate(input=audio_data, cache={}, language="zh", use_itn=True)
            if not res: return ""
            raw_asr = re.sub(r'<\|.*?\|>', '', res[0].get('text', '')).strip()
            cleaned = self._remove_stutters(raw_asr)
            final_text = cleaned
            if len(cleaned) > 1:
                p = f"為此句加上結尾標點：{cleaned}\n標點："
                inputs = self.tokenizer(p, return_tensors="pt").to(self.device)
                outputs = self.llm_model.generate(inputs["input_ids"], max_new_tokens=2, temperature=0.1)
                mark = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
                if mark in "，。！？,.!?": final_text += mark
            return self.cc.convert(final_text)
        except: return ""

    def cleanup(self):
        if self.asr_model: del self.asr_model
        if self.llm_model: del self.llm_model
