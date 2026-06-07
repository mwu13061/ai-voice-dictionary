# AI Voice Assistant - 專案全局視圖 (Global View)
自動生成時間: 2026-06-07 11:58:47
> ⚠️ **注意**: 本檔案為腳本自動生成，用於提供 AI 開發者全局上下文。請勿直接手動修改此檔案，而是修改原始程式碼後重新執行 `python sync_global_view.py`。

## 🗂️ 檔案索引 (File Index)
- `GEMINI.md`
- `main.py`
- `src/__init__.py`
- `src/audio/__init__.py`
- `src/audio/audio_recorder.py`
- `src/audio/engines/__init__.py`
- `src/audio/engines/engine_v1_legacy.py`
- `src/audio/engines/engine_v2_stable.py`
- `src/audio/minimind_engine.py`
- `src/audio/whisper_engine.py`
- `src/llm/__init__.py`
- `src/llm/gemini_engine.py`
- `src/ui/__init__.py`
- `src/ui/app_controller.py`
- `src/ui/handlers/__init__.py`
- `src/ui/handlers/dict_handler.py`
- `src/ui/handlers/macro_handler.py`
- `src/ui/handlers/profile_handler.py`
- `src/ui/handlers/vision_handler.py`
- `src/ui/handlers/voice_handler.py`
- `src/ui/learning_toast.py`
- `src/ui/magic_toast.py`
- `src/ui/plugins/magic_menu.py`
- `src/ui/plugins/magic_menu_v1.py`
- `src/ui/recording_widget.py`
- `src/ui/repeat_learn_dialog.py`
- `src/ui/settings_window.py`
- `src/ui/settings_window_decompiled.py`
- `src/ui/snip_overlay.py`
- `src/ui/vision_result_window.py`
- `src/utils/__init__.py`
- `src/utils/backup_manager.py`
- `src/utils/cloud_engine.py`
- `src/utils/hotkey_manager.py`
- `src/utils/input_mode_manager.py`
- `src/utils/learning_engine.py`
- `src/utils/module_loader.py`
- `src/utils/output_plugins/__init__.py`
- `src/utils/output_plugins/plugin_v1_instant.py`
- `src/utils/output_plugins/plugin_v2_typing.py`
- `src/utils/path_helper.py`
- `src/utils/screenshot_tool.py`
- `src/utils/smart_trigger.py`
- `src/utils/text_output.py`

---

## 💻 核心程式碼內容 (Source Code)

### 📄 `GEMINI.md`
```markdown
無法讀取檔案內容: 'utf-8' codec can't decode byte 0x95 in position 6941: invalid start byte

```

### 📄 `main.py`
```python
# main.py
import sys
import os

# [A4] ULTRA-FAST OFFLINE INITIALIZATION: DISABLE HF/MODELSCOPE CONNECTION WAITS
os.environ["MODELSCOPE_DISABLE_UPDATE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# [A215] ULTRA ENCODING SHIELD: FORCE UTF-8 AT ALL LEVELS
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "UTF-8"

# [A1000] DPI & ENVIRONMENT RESILIENCE
if sys.platform == "win32":
    # Prevent Qt from conflicting with manual DPI settings
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTOSCALE_DOS"] = "1" 

    try:
        import io
        if sys.stdout is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except: pass

from PySide6.QtWidgets import QApplication
from src.ui.app_controller import AppController
from src.utils.path_helper import initialize_universal_environment, get_writable_path # [A1000]
from loguru import logger

def main():
    # [A402] Diagnostic Restoration: Keep console log in source mode
    logger.remove()
    
    # 1. Always log to file (Async)
    log_file = get_writable_path("app_runtime.log")
    logger.add(log_file, rotation="1 MB", encoding="utf-8", level="DEBUG", enqueue=True)
    
    # 2. Log to console ALWAYS (if available) [A568/A569]
    import sys as sys_module
    if sys_module.stderr is not None:
        logger.add(sys_module.stderr, level="INFO")
    
    if hasattr(sys, '_MEIPASS'):
        logger.info("🚀 [PROD MODE] Console Diagnostics Active.")
    else:
        logger.info("🛠️ [DEV MODE] Console Logging Active.")
    
    logger.info(f"--- SYSTEM STARTING (A1000 UNIVERSAL RELEASE) ---")
    
    # [A1000] Lock in embedded binaries before anything else loads
    initialize_universal_environment()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    try:
        controller = AppController()
        controller.run()
        logger.success("✅ Application Awakened. Zero-Dependency Mode Locked.")
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("CRITICAL STARTUP ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()

```

### 📄 `src/__init__.py`
```python

```

### 📄 `src/audio/__init__.py`
```python

```

### 📄 `src/audio/audio_recorder.py`
```python
# src/audio/audio_recorder.py
import sounddevice as sd
import numpy as np
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger

class AudioRecorder(QObject):
    """
    Refactored AudioRecorder: 
    1. Removed Auto-Silence to prevent loops.
    2. Added robust state management.
    3. Standardized output to float32 16kHz.
    """
    recording_finished = Signal(np.ndarray)
    chunk_ready = Signal(np.ndarray)
    volume_signal = Signal(float) # [A112]
    vad_silent = Signal()

    def __init__(self, sample_rate=16000):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_buffer = []
        self.stream = None
        self._chunk_count = 0
        
        # VAD Parameters
        self.vad_threshold = 0.015 
        self.silence_count = 0
        self.is_streaming_mode = False

    def start_recording(self, streaming=False):
        if self.is_recording:
            logger.warning("AudioRecorder: Attempted to start while already recording.")
            return
        
        self.is_streaming_mode = streaming
        logger.info(f"--- AUDIO RECORDING STARTED ---")
        self.audio_buffer = []
        self._chunk_count = 0
        self.is_recording = True
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=self._audio_callback,
                blocksize=1600 # 0.1s chunks for smooth volume detection
            )
            self.stream.start()
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            self.is_recording = False

    def stop_recording(self, emit=True):
        if not self.is_recording:
            return

        self.is_recording = False

        # [A475] SPEED STANDARD: DO NOT MODIFY (Turbo Data Handoff BEFORE closing stream)
        if emit:
            if self.audio_buffer:
                full_audio = np.concatenate(self.audio_buffer).flatten()
                logger.debug(f"⚡ [TURBO] Emitting {len(full_audio)} samples instantly.")
                self.recording_finished.emit(full_audio)
            else:
                logger.warning("AudioRecorder: Stopped with empty audio buffer. Emitting empty array.")
                self.recording_finished.emit(np.array([], dtype=np.float32))

        logger.info(f"--- AUDIO RECORDING STOPPED (Chunks captured: {self._chunk_count}) ---")
        
        # [A563] ULTRA-TURBO: Move stream cleanup to background to avoid blocking emitter thread
        def _cleanup(s):
            try:
                s.stop()
                s.close()
            except: pass
            
        if self.stream:
            import threading
            threading.Thread(target=_cleanup, args=(self.stream,), daemon=True).start()
            self.stream = None

    def flush_buffer(self):
        if not self.is_recording:
            return np.array([], dtype=np.float32)
        buf = self.audio_buffer
        self.audio_buffer = []
        if buf:
            try:
                return np.concatenate(buf).flatten()
            except Exception as e:
                logger.error(f"Error concatenating buffer: {e}")
        return np.array([], dtype=np.float32)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        if self.is_recording:
            self._chunk_count += 1
            chunk = indata.copy()
            self.audio_buffer.append(chunk)
            
            # Calculate Volume (RMS)
            energy = np.sqrt(np.mean(chunk**2))
            self.volume_signal.emit(float(energy))
            
            if self.is_streaming_mode:
                self.chunk_ready.emit(chunk.flatten())

```

### 📄 `src/audio/engines/__init__.py`
```python
# package

```

### 📄 `src/audio/engines/engine_v1_legacy.py`
```python
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

```

### 📄 `src/audio/engines/engine_v2_stable.py`
```python
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
            
            # [A24] Let PyTorch optimize threading using logical/physical core default allocation
            torch.set_grad_enabled(False)
            
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

```

### 📄 `src/audio/minimind_engine.py`
```python
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

```

### 📄 `src/audio/whisper_engine.py`
```python
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

```

### 📄 `src/llm/__init__.py`
```python

```

### 📄 `src/llm/gemini_engine.py`
```python
# src/llm/gemini_engine.py
import os
from google import genai
from google.genai import types
from loguru import logger
import time

class GeminiEngine:
    """
    Handles connection to Google Gemini for text correction and optimization.
    """
    def __init__(self, api_key=None, model_id="gemini-2.0-flash"):
        # Prioritize provided api_key, then check environment variable GH088768
        self.api_key = api_key or os.environ.get("GH088768", "")
        self.model_id = model_id
        self.client = None
        
        if self.api_key:
            logger.info("Gemini API Key loaded from environment variable GH088768.")
        else:
            logger.warning("Gemini API Key not found in environment variable GH088768.")
        
        self.system_prompt = (
            "你是一個專業的語音輸入糾錯助手。你的任務是將輸入的「初步語音辨識文字」轉換為「正確、流暢、無錯別字的繁體中文」。\n"
            "規則：\n"
            "1. 修正同音異義字 (例如：'送齣' -> '送出')。\n"
            "2. 修正語法錯誤，但保持說話者的原始語氣。\n"
            "3. 保持簡潔，不要添加額外的解釋或問候語。\n"
            "4. 如果輸入已經很完美，則原樣返回。\n"
            "5. 直接輸出修正後的文字內容。"
        )

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self.client = None # Reset client to pick up new key

    def _get_client(self):
        if self.client is None:
            if not self.api_key:
                logger.error("Gemini API Key is not set!")
                raise ValueError("API Key missing")
            self.client = genai.Client(api_key=self.api_key)
        return self.client

    def correct_text(self, text: str) -> str:
        """
        Send text to Gemini for semantic correction.
        """
        if not text.strip():
            return ""
            
        try:
            client = self._get_client()
            logger.debug(f"Sending text to Gemini: {text}")
            
            response = client.models.generate_content(
                model=self.model_id,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.1, # Low temperature for consistency
                )
            )
            
            corrected_text = response.text.strip()
            logger.info(f"Gemini correction: {corrected_text}")
            return corrected_text
            
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            # Fallback: return original text if AI fails
            return text

```

### 📄 `src/ui/__init__.py`
```python

```

### 📄 `src/ui/app_controller.py`
```python
# src/ui/app_controller.py
import sys, os, threading, time, io, numpy as np, string, re, keyboard, pyautogui, pyperclip, queue
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from loguru import logger

from src.ui.recording_widget import RecordingWidget
from src.ui.settings_window import SettingsWindow, RefinementDialog, QuickAddDialog
from src.audio.audio_recorder import AudioRecorder
from src.utils.hotkey_manager import HotkeyManager
from src.utils.module_loader import ModuleLoader
from src.utils.learning_engine import LearningEngine
from src.ui.plugins.magic_menu import MagicMenu
from src.utils.smart_trigger import SmartTrigger 
from src.utils.cloud_engine import GeminiCloudEngine
from src.utils.screenshot_tool import ScreenshotTool
from src.utils.path_helper import get_resource_path 

from src.ui.handlers.macro_handler import MacroHandler
from src.ui.handlers.dict_handler import DictionaryHandler
from src.ui.handlers.voice_handler import VoiceHandler
from src.ui.handlers.vision_handler import VisionHandler
from src.ui.handlers.profile_handler import ProfileHandler

class ToastNotification(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 37, 47, 230);
                border: 1.5px solid #3498db;
                border-radius: 6px;
            }
            QLabel {
                color: #f1c40f;
                font-family: 'Microsoft JhengHei';
                font-size: 10pt;
                font-weight: bold;
                padding: 6px 12px;
            }
        """)
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        l.addWidget(lbl)
        
        # Position at the center-bottom of the screen
        screen = QGuiApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.8) # 80% down
        self.move(x, y)
        
        # Auto-destruct after 3 seconds
        QTimer.singleShot(3000, self.close_toast)
        
    def close_toast(self):
        self.close()
        self.deleteLater()

class AppController(QObject):
    magic_request_triggered = Signal(str, str)
    magic_learn_triggered = Signal(str)
    ready_signal = Signal(str)
    asr_result_signal = Signal(str)
    vision_result_signal = Signal(str)
    launch_refinement_signal = Signal(str)
    refinement_result_signal = Signal(str)
    query_done_signal = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_engine_ready = False
        self._first_load_done = False
        self._lock = threading.Lock()
        self._physical_release_time = 0
        self._speech_detected = False
        self._is_continuous_restart = False
        
        self._asr_queue = queue.Queue()
        self._asr_worker_thread = threading.Thread(target=self._asr_worker, daemon=True)
        self._asr_worker_thread.start()
        
        self.settings = SettingsWindow()
        self.recorder = AudioRecorder()
        self.hotkey_manager = HotkeyManager()
        self.learning_engine = LearningEngine()
        self.smart_trigger = SmartTrigger()
        
        self.smart_trigger.controller = self
        self.hotkey_manager.controller = self
        self.cloud_engine = GeminiCloudEngine()
        self.engine = None
        self.output_plugin = None
        
        self.macro_handler = MacroHandler(self)
        self.dict_handler = DictionaryHandler(self)
        self.voice_handler = VoiceHandler(self)
        self.vision_handler = VisionHandler(self)
        self.profile_handler = ProfileHandler(self)
        
        self.ui = RecordingWidget()
        self.magic_menu = MagicMenu(self)
        self.tray = QSystemTrayIcon(self)
        
        self._setup_tray()
        self._connect_signals()
        
        self._vad_timer = QTimer()
        self._vad_timer.setSingleShot(True)
        self._vad_timer.timeout.connect(self.stop_session)
    
    def _setup_tray(self):
        icon_path = get_resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(QIcon.fromTheme("audio-input-microphone"))
            
        tm = QMenu()
        show_act = QAction("⚙️ 設定", self)
        show_act.triggered.connect(self._show_settings)
        exit_act = QAction("❌ 退出", self)
        exit_act.triggered.connect(self._safe_exit)
        tm.addAction(show_act)
        tm.addAction(exit_act)
        self.tray.setContextMenu(tm)
        self.tray.show()
    
    def _safe_exit(self):
        try:
            self.tray.hide()
            import os
            os._exit(0)
        except:
            sys.exit(0)
 
    def _connect_signals(self):
        # Hotkeys
        self.hotkey_manager.start_recording_signal.connect(self.request_start, Qt.QueuedConnection)
        self.hotkey_manager.stop_recording_signal.connect(self.request_stop, Qt.QueuedConnection)
        self.hotkey_manager.magic_menu_signal.connect(lambda: self._handle_smart_magic_trigger(""), Qt.QueuedConnection)
        
        # Smart Trigger
        self.smart_trigger.voice_start_signal.connect(self.request_start, Qt.QueuedConnection)
        self.smart_trigger.voice_stop_signal.connect(self.request_stop, Qt.QueuedConnection)
        self.smart_trigger.magic_signal.connect(self._handle_smart_magic_trigger, Qt.QueuedConnection)
        self.smart_trigger.click_signal.connect(self._handle_global_click, Qt.QueuedConnection)
        
        # Audio
        self.recorder.recording_finished.connect(self.on_audio_ready)
        self.recorder.volume_signal.connect(self._on_volume_update)
        self.asr_result_signal.connect(self._handle_asr_output)
        
        # Handlers
        self.magic_learn_triggered.connect(self.dict_handler.handle_magic_learn, Qt.QueuedConnection)
        self.settings.add_dict_requested.connect(self.dict_handler.add_item)
        self.settings.del_dict_requested.connect(self.dict_handler.del_item)
        self.settings.clear_dict_requested.connect(self.dict_handler.clear_all)
        self.settings.import_dict_requested.connect(self.dict_handler.import_items)
        
        self.launch_refinement_signal.connect(self.profile_handler.launch_refinement, Qt.QueuedConnection)
        self.refinement_result_signal.connect(self.profile_handler.deliver_result, Qt.QueuedConnection)
        self.vision_result_signal.connect(self.vision_handler.show_result_window, Qt.QueuedConnection)
        
        # UI & System
        self.ready_signal.connect(self._handle_ready_msg)
        self.query_done_signal.connect(self._on_query_done)
        self.settings.start_pairing_requested.connect(lambda: self.hotkey_manager.set_learning_mode(True))
        self.settings.stop_pairing_requested.connect(lambda: self.hotkey_manager.set_learning_mode(False))
        self.hotkey_manager.input_captured_signal.connect(self.settings.handle_captured_input)
        self.settings.settings_changed.connect(self.on_settings_updated)
        self.settings.preview_sound_requested.connect(lambda i: threading.Thread(target=self._play_selected_chime, args=("START", i), daemon=True).start())
        self.settings.launch_vision_requested.connect(self.vision_handler.start_snip)
        self.settings.preview_ui_requested.connect(self._preview_ui_position)
        self.ui.position_changed.connect(self.settings.update_ui_coords)
        self.magic_request_triggered.connect(self._handle_magic_action, Qt.QueuedConnection)
 
    def _handle_global_click(self, x, y):
        if self.magic_menu and self.magic_menu.isVisible() and not self.magic_menu.underMouse():
            self.magic_menu.close()
 
    def _handle_magic_action(self, mode, captured_text):
        if mode == "SETTINGS":
            self._show_settings()
        elif mode == "VISION":
            self.vision_handler.start_snip()
        elif mode == "LEARN":
            self.magic_learn_triggered.emit(captured_text)
        elif mode == "FIX":
            self.launch_refinement_signal.emit(captured_text)
        else:
            self.macro_handler.execute_macro(mode)
 
    def request_start(self):
        with self._lock:
            if self.is_recording: return
            self.is_recording = True
            
            ui_idx = self.settings.raw_config.get("recording_style", 1)
            m = {0: 2, 1: 0, 2: 1}
            self.ui.set_style(m.get(ui_idx, 0))
            
            if not self.is_engine_ready:
                self.ui.set_loading_state()
            else:
                self.ui.show_recording()
                
            # [A20] Run VAD safety timeout only in Toggle Mode (1, 2)
            if self.settings.raw_config.get("recording_mode", 0) in [1, 2]:
                self._speech_detected = False
                self._is_continuous_restart = False
                timeout_val = float(self.settings.raw_config.get("silence_timeout", 5.0))
                init_timeout = max(5.0, timeout_val)
                self._vad_timer.start(int(init_timeout * 1000))
                
            if self.settings.raw_config.get("audio_cue", True):
                self._play_selected_chime("START")
                time.sleep(0.1)
                
            self.recorder.start_recording(streaming=False)
 
    def request_stop(self):
        with self._lock:
            if not self.is_recording: return
            self._physical_release_time = time.time()
            self.is_recording = False
            self._vad_timer.stop()
            self.ui.hide()
            self.recorder.stop_recording(emit=True)
            if self.settings.raw_config.get("audio_cue", True):
                threading.Thread(target=self._play_selected_chime, args=("STOP",), daemon=True).start()
 
    def _asr_worker(self):
        while True:
            try:
                item = self._asr_queue.get()
                if item is None:
                    break
                audio_data, is_restart = item
                try:
                    if self.engine and self.is_engine_ready:
                        raw_text = self.engine.process(audio_data)
                        self.voice_handler.process_asr_result(raw_text)
                except Exception as e:
                    logger.error(f"ASR worker inference error: {e}")
                finally:
                    if not is_restart:
                        QTimer.singleShot(0, self.ui.hide)
                    self._asr_queue.task_done()
            except Exception as e:
                logger.error(f"ASR worker loop error: {e}")
                time.sleep(0.05)

    def on_audio_ready(self, audio_data: np.ndarray):
        is_restart = getattr(self, "_is_continuous_restart", False)
        self._is_continuous_restart = False
        if not self.voice_handler.check_audio_gate(audio_data):
            if not is_restart:
                QTimer.singleShot(0, self.ui.hide)
            return
        self._asr_queue.put((audio_data, is_restart))
 
    def _handle_asr_output_background(self, text):
        if self.output_plugin:
            self.output_plugin.output(text, mode=self.settings.raw_config.get("output_mode", 0))
 
    def _handle_asr_output(self, text):
        self._handle_asr_output_background(text)
 
    def _async_engine_load(self, ev, config=None):
        try:
            self.engine = ModuleLoader.load_engine(ev)
            if self.engine: 
                self.engine.load()
                if hasattr(self.engine, "update_config") and config:
                    self.engine.update_config(config)
                self.is_engine_ready = True
                self.ready_signal.emit("✅ 語音引擎就緒")
                if not self._first_load_done:
                    self._first_load_done = True
                    threading.Thread(target=self._play_selected_chime, args=("START", 9), daemon=True).start()
        except Exception as e:
            logger.error(f"Load Error: {e}")
 
    def on_settings_updated(self, config):
        try:
            import ctypes
            hWnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hWnd:
                ctypes.windll.user32.ShowWindow(hWnd, 5 if config.get("show_console", True) else 0)
        except: pass
        
        self.hotkey_manager.update_hotkey(config.get("hotkey", "ctrl+shift+win"))
        self.hotkey_manager.update_magic_hotkey(config.get("magic_hotkey", "alt+win"))
        self.hotkey_manager.update_config(
            hold_duration_s=config.get("smart_hold_duration", 0.5),
            mode=config.get("recording_mode", 0)
        )
        
        self.smart_trigger.set_enabled(
            left=config.get("smart_left", True), 
            right=config.get("smart_right", True), 
            hold_duration_s=config.get("smart_hold_duration", 0.5),
            mode=config.get("recording_mode", 0)
        )
        
        self.cloud_engine.configure(config.get("gemini_api_key", ""), config.get("opt_model", ""))
        self.output_plugin = ModuleLoader.load_output_plugin(config.get("output_version", "v1_instant"))
        
        ev = config.get("engine_version", "v2_stable")
        current_ev = getattr(self, "_current_engine_ver", None)
        
        if not self.engine or ev != current_ev:
            self._current_engine_ver = ev
            self.is_engine_ready = False
            threading.Thread(target=self._async_engine_load, args=(ev, config), daemon=True).start()
        elif hasattr(self.engine, "update_config"):
            self.engine.update_config(config)

    def _show_settings(self):
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def _handle_ready_msg(self, m): 
        logger.info(f"📢 [NOTIFICATION] {m}")
        toast = ToastNotification(m)
        toast.show()
        self._active_toast = toast

    def _on_query_done(self, ok, msg):
        pass

    def _handle_smart_magic_trigger(self, text=""):
        # Dismiss any editor context menu first by simulating Esc
        try: keyboard.press_and_release('esc')
        except: pass
        # [A636] Use QTimer to ensure the popup happens on main thread but after event loop
        QTimer.singleShot(50, lambda: self.magic_menu.popup_at_cursor(text))

    def _preview_ui_position(self):
        self.ui.enter_positioning_mode("📍 請拖曳。點擊畫面任一處結束...")

    def _play_selected_chime(self, mode="START", style=None):
        if style is None: style = self.settings.raw_config.get("sound_style_idx", 9)
        if style == 0: return
        try:
            import winsound
            s = [(1000,50),(800,50),(1000,50),(400,50),(1200,50),(1500,50),(600,50),(900,50),(1100,50),(1300,50),(1000,50),(1200,50),(2000,50),(500,50),(1800,50)]
            f, d = s[style] if style < len(s) else (1000, 50)
            if mode == "STOP":
                f = int(f * 0.8) # 20% lower pitch for Stop confirmation
            winsound.Beep(f, d)
        except: pass
 
    def _on_volume_update(self, e):
        s = self.settings.raw_config.get("vad_sensitivity", 50)
        th = 0.1 * (1.02 ** (50 - s))
        if self.is_recording and self.settings.raw_config.get("recording_mode", 0) in [1, 2]:
            if e > th:
                self._speech_detected = True
                self._vad_timer.start(1000)

    def run(self):
        self.settings.load_settings()
        self.settings.update_dict_list(self.learning_engine.list_all())
        self.on_settings_updated(self.settings.raw_config)
        self.ui.set_initial_position(self.settings.raw_config.get("ui_x", 800), self.settings.raw_config.get("ui_y", 100))
        self.hotkey_manager.initialize(
            self.settings.raw_config.get("hotkey"), 
            self.settings.raw_config.get("magic_hotkey"), 
            smart_trigger=self.smart_trigger
        )

    def stop_session(self):
        mode = self.settings.raw_config.get("recording_mode", 0)
        if mode not in [1, 2]:
            # PTT mode should not have VAD timeout logic at all
            logger.warning(f"📡 [VAD] stop_session called in non-toggle mode {mode}. Ignoring.")
            return

        if self._speech_detected:
            # [A16] Silence detected after speech (1s): transcribe what was said, but continue recording
            logger.info("📡 [VAD] Speech pause detected (1s). Flushing buffer and continuing recording...")
            self._is_continuous_restart = True
            
            # Flush buffer and run inference
            audio_data = self.recorder.flush_buffer()
            if len(audio_data) > 0:
                self.on_audio_ready(audio_data)
                
            self._speech_detected = False
            self._vad_timer.start(5000) # Reset to 5s initial timeout
        else:
            if mode == 2:
                # In Toggle Mode B (2), we NEVER stop on idle silence, just reset VAD countdown
                logger.info(f"📡 [VAD] Idle silence timeout in mode {mode}. Keeping recording session active.")
                self._speech_detected = False
                self._vad_timer.start(5000)
            else:
                logger.info("📡 [VAD] Stopping recording session completely.")
                self.request_stop()

```

### 📄 `src/ui/handlers/__init__.py`
```python
# handler package

```

### 📄 `src/ui/handlers/dict_handler.py`
```python
# src/ui/handlers/dict_handler.py
import threading
import time
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QGuiApplication
from src.ui.settings_window import QuickAddDialog

class DictionaryHandler:
    """
    [A632] Isolated Dictionary Logic.
    [REPRODUCTION_GUARD] Ensures captured text reaches the input field.
    """
    def __init__(self, controller):
        self.controller = controller
        self.quick_dlg = None

    def handle_magic_learn(self, text):
        """ [A632] Data Pipe Restoration """
        logger.info(f"📔 [DICT_HANDLER] Quick-Add request for: '{text[:20]}'")
        
        # 1. Cleanup old
        if self.quick_dlg:
            try: self.quick_dlg.close(); self.quick_dlg.deleteLater()
            except: pass
            
        # 2. Open new MINI dialog
        # Ensure text is passed correctly to initial_text
        self.quick_dlg = QuickAddDialog(text)
        self.quick_dlg.add_req.connect(self.add_item)
        
        # 3. Position near cursor
        pos = QCursor.pos()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = max(screen.left(), min(pos.x() + 10, screen.right() - 250))
        y = max(screen.top(), min(pos.y() + 10, screen.bottom() - 150))
        self.quick_dlg.move(x, y)
        
        self.quick_dlg.show()
        self.quick_dlg.raise_()
        self.quick_dlg.activateWindow()

    def add_item(self, orig, corr):
        if self.controller.learning_engine.add_habit_manual(orig, corr):
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
            self.controller.ready_signal.emit(f"✅ 已加入詞庫: {orig} ➔ {corr}")

    def import_items(self, items_json):
        try:
            import json
            items = json.loads(items_json)
            count = 0
            for orig, corr in items:
                if self.controller.learning_engine.add_habit_manual(orig, corr): count += 1
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())
            logger.success(f"📔 [DICT_HANDLER] Merged {count} items.")
        except Exception as e:
            logger.error(f"❌ [DICT_HANDLER] Import failed: {e}")

    def del_item(self, orig):
        if self.controller.learning_engine.delete_habit(orig):
            self.controller.settings.update_dict_list(self.controller.learning_engine.list_all())

    def clear_all(self):
        if self.controller.learning_engine.clear_dictionary():
            self.controller.settings.update_dict_list([])
            self.controller.ready_signal.emit("🧹 詞庫已清空")

```

### 📄 `src/ui/handlers/macro_handler.py`
```python
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

```

### 📄 `src/ui/handlers/profile_handler.py`
```python
# src/ui/handlers/profile_handler.py
import threading
import time
import pyautogui
import keyboard
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from src.ui.settings_window import RefinementDialog

class ProfileHandler:
    """
    [A542] Isolated AI Refinement Logic.
    Manages:
    - AI text optimization (FIX mode).
    - RefinementDialog interaction.
    - Result delivery to target application.
    """
    def __init__(self, controller):
        self.controller = controller

    def launch_refinement(self, text):
        """ [A583/A586] Entry point for FIX mode with empty check and dynamic profiles """
        if not text or not text.strip():
            logger.warning("⚠️ [FIX] No text captured. Aborting.")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未偵測到選取文字。\\n請先用滑鼠選取一段文字後再執行此功能。")
            return

        ready, err = self.controller.cloud_engine.is_ready()
        if not ready:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "AI 未就緒", err)
            return
        
        # [A586] Pass profiles to dialog
        p = self.controller.settings.raw_config.get("opt_profiles", [])
        i = self.controller.settings.raw_config.get("active_profile_idx", 0)
        profile_names = [x["name"] for x in p]
        
        self.refine_dlg = RefinementDialog(text, profile_names, i)
        self.refine_dlg.restore_requested.connect(self.handle_restore)
        self.refine_dlg.retry_requested.connect(lambda req: threading.Thread(
            target=self._run_inference, args=(text, req), daemon=True).start())
        self.refine_dlg.profile_changed.connect(self.handle_profile_change)
        self.refine_dlg.show()
        
        threading.Thread(target=self._run_inference, args=(text,), daemon=True).start()

    def handle_profile_change(self, idx):
        """ [A586] Update active profile and re-run immediately """
        logger.info(f"🔄 [PROFILE_HANDLER] Profile switched to index {idx}")
        self.controller.settings.raw_config["active_profile_idx"] = idx
        self.controller.settings._widget_changed() # Trigger save
        
        # Reset dialog status
        if self.refine_dlg:
            self.refine_dlg.status.setText("⏳ AI 處理中...")
            self.refine_dlg.status.setStyleSheet("color:#f39c12;")
            self.refine_dlg.btn_restore.setEnabled(False)
            self.refine_dlg.btn_retry.setEnabled(False)
        
        threading.Thread(target=self._run_inference, args=(self.refine_dlg.original_text, ""), daemon=True).start()

    def _run_inference(self, text, extra_req=""):
        try:
            m = self.controller.settings.raw_config.get("opt_model", "")
            p = self.controller.settings.raw_config.get("opt_profiles", [])
            i = self.controller.settings.raw_config.get("active_profile_idx", 0)
            u = p[i]['prompt'] if 0 <= i < len(p) else "請優化:"
            
            s = f"你是一個專業的文字修飾助手。只能輸出最終結果。不要對話。方向：{u}"
            if extra_req:
                s += f" 追加要求：{extra_req}"
                
            res = self.controller.cloud_engine.process_text(user_text=text, system_prompt=s, model_override=m)
            self.controller.refinement_result_signal.emit(res)
        except Exception as e:
            logger.error(f"❌ [PROFILE_HANDLER] Inference Failed: {e}")

    def deliver_result(self, res):
        """ connected to refinement_result_signal """
        if hasattr(self, 'refine_dlg') and self.refine_dlg:
            if not res.startswith("❌"):
                # [A545] Explicit Hardened Sequence instead of pyautogui
                keyboard.press('ctrl')
                time.sleep(0.1)
                keyboard.press('a')
                time.sleep(0.1)
                keyboard.release('a')
                keyboard.release('ctrl')
                
                time.sleep(0.1)
                self.controller.output_plugin.output(res)
            self.refine_dlg.show_ready()

    def handle_restore(self, original_text):
        # [A545] Explicit Hardened Sequence
        keyboard.press('ctrl')
        time.sleep(0.1)
        keyboard.press('a')
        time.sleep(0.1)
        keyboard.release('a')
        keyboard.release('ctrl')
        
        time.sleep(0.1)
        self.controller.output_plugin.output(original_text)

```

### 📄 `src/ui/handlers/vision_handler.py`
```python
# src/ui/handlers/vision_handler.py
import threading
from loguru import logger
from PySide6.QtWidgets import QMessageBox
from src.utils.screenshot_tool import ScreenshotTool

class VisionHandler:
    """
    [A542] Isolated Vision Logic.
    Manages:
    - Screen snipping.
    - Screenshot processing.
    - Displaying vision results.
    """
    def __init__(self, controller):
        self.controller = controller
        self._snip_overlay = None # [A549] Keep reference to prevent GC

    def start_snip(self):
        """ Entry point for VISION mode """
        logger.info("🎯 [VISION_HANDLER] Starting Snip Flow...")
        ready, err = self.controller.cloud_engine.is_ready()
        if not ready:
            logger.error(f"❌ [VISION_HANDLER] Cloud Engine not ready: {err}")
            QMessageBox.warning(None, "設定不完整", err)
            return
        
        try:
            from src.ui.snip_overlay import SnipOverlay
            self._snip_overlay = SnipOverlay()
            self._snip_overlay.snip_captured.connect(self._handle_snip_captured)
            self._snip_overlay.show()
            logger.success("📸 [VISION_HANDLER] Snip Overlay Visible.")
        except Exception as e:
            logger.error(f"❌ [VISION_HANDLER] Failed to show SnipOverlay: {e}")

    def _handle_snip_captured(self, rect):
        logger.info(f"📸 [VISION_HANDLER] Area captured: {rect}")
        path = ScreenshotTool.capture_area(rect)
        if path:
            logger.info(f"💾 [VISION_HANDLER] Screenshot saved: {path}")
            threading.Thread(target=self._async_process_vision, args=(path,), daemon=True).start()
        else:
            logger.error("❌ [VISION_HANDLER] Screenshot capture returned no path.")

    def _async_process_vision(self, path):
        try:
            m = self.controller.settings.raw_config.get("vision_model", "")
            res = self.controller.cloud_engine.process_vision(path, model_override=m)
            if res:
                self.controller.vision_result_signal.emit(res)
        except Exception as e:
            logger.error(f"❌ [VISION_HANDLER] Process Failed: {e}")

    def show_result_window(self, content=""):
        """ connected to vision_result_signal """
        from src.ui.vision_result_window import VisionResultWindow
        if not hasattr(self.controller, 'vision_win') or self.controller.vision_win is None:
            self.controller.vision_win = VisionResultWindow()
        if content:
            self.controller.vision_win.update_content(content)
        self.controller.vision_win.show_at_center()

```

### 📄 `src/ui/handlers/voice_handler.py`
```python
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

```

### 📄 `src/ui/learning_toast.py`
```python
# src/ui/learning_toast.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QColor, QScreen

class LearningToast(QWidget):
    """
    Interactive Learning Toast [A103]:
    - Precise feedback: [Old] -> [New]
    - Confirm/Undo actions.
    - Premium minimalist UI.
    """
    confirmed = Signal(str, str)
    cancelled = Signal()

    def __init__(self, original, corrected, is_full=False, parent=None):
        super().__init__(parent)
        self.original = original
        self.corrected = corrected
        self.is_full = is_full
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        container = QWidget()
        # Premium dark slate theme
        container.setStyleSheet("""
            QWidget {
                background-color: #1e272e;
                border: 1px solid #3498db;
                border-radius: 20px;
            }
        """)
        c_layout = QHBoxLayout(container)
        
        # Icon
        icon_label = QLabel("✨")
        icon_label.setStyleSheet("border: none; font-size: 16px;")
        c_layout.addWidget(icon_label)
        
        # Message
        msg = f"學習：{self.original} ➔ {self.corrected}"
        if self.is_full:
            msg = f"❗ 詞庫已滿(5/5)，請升級 Pro 以儲存：{self.original} ➔ {self.corrected}"
            
        msg_label = QLabel(msg)
        msg_label.setStyleSheet("color: white; font-family: 'Microsoft JhengHei'; font-size: 13px; border: none;")
        c_layout.addWidget(msg_label)
        
        if not self.is_full:
            # Confirm Button
            confirm_btn = QPushButton("✓ 確認")
            confirm_btn.setStyleSheet("""
                QPushButton { background: #2ecc71; color: white; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #27ae60; }
            """)
            confirm_btn.clicked.connect(self.on_confirm)
            c_layout.addWidget(confirm_btn)
            
            # Undo Button
            undo_btn = QPushButton("↺ 撤銷")
            undo_btn.setStyleSheet("""
                QPushButton { background: #e74c3c; color: white; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #c0392b; }
            """)
            undo_btn.clicked.connect(self.on_cancel)
            c_layout.addWidget(undo_btn)
        else:
            # Upgrade Suggestion Button
            upgrade_btn = QPushButton("💎 升級 Pro")
            upgrade_btn.setStyleSheet("""
                QPushButton { background: #f1c40f; color: black; border-radius: 12px; padding: 4px 10px; font-weight: bold; }
                QPushButton:hover { background: #f39c12; }
            """)
            c_layout.addWidget(upgrade_btn)
            
        layout.addWidget(container)
        
        # Auto hide after 8 seconds if no action
        QTimer.singleShot(8000, self.close)

    def on_confirm(self):
        self.confirmed.emit(self.original, self.corrected)
        self.close()
        
    def on_cancel(self):
        self.cancelled.emit()
        self.close()

    def show_at_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        # Bottom right
        self.adjustSize()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60
        self.move(x, y)
        self.show()
        # Premium Sound logic would go here

```

### 📄 `src/ui/magic_toast.py`
```python
# src/ui/magic_toast.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
import pyperclip
import keyboard
import time

class MagicToast(QWidget):
    """
    [A201] Minimalist Confirm Toast.
    - Only "Undo" button.
    - Click anywhere else = Confirm (default behavior as it closes).
    """
    def __init__(self, original_text, new_text, parent=None):
        super().__init__(parent)
        self.original_text = original_text
        self.new_text = new_text
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget { background-color: #8e44ad; border: 2px solid #9b59b6; border-radius: 20px; }
            QLabel { color: white; font-weight: bold; font-family: 'Microsoft JhengHei'; }
        """)
        c_layout = QHBoxLayout(container)
        
        c_layout.addWidget(QLabel("✨ AI 優化已套用"))
        
        undo_btn = QPushButton("↺ 撤銷並還原原文")
        undo_btn.setStyleSheet("""
            QPushButton { background: #e74c3c; color: white; border-radius: 12px; padding: 6px 15px; font-weight: bold; }
            QPushButton:hover { background: #ff4757; }
        """)
        undo_btn.clicked.connect(self.on_undo)
        c_layout.addWidget(undo_btn)
        
        layout.addWidget(container)
        # Stay a bit longer so user can read
        QTimer.singleShot(8000, self.close)

    def on_undo(self):
        try:
            pyperclip.copy(self.original_text)
            keyboard.press_and_release('ctrl+v')
        except: pass
        self.close()

    def show_at_corner(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 150
        self.move(x, y)
        self.show()

```

### 📄 `src/ui/plugins/magic_menu.py`
```python
# src/ui/plugins/magic_menu.py
import sys, os, time, threading, pyperclip, keyboard, pyautogui, ctypes
from PySide6.QtWidgets import QMenu, QFileIconProvider, QApplication
from PySide6.QtGui import QCursor, QAction
from PySide6.QtCore import Qt, QTimer, QPoint, QFileInfo
from loguru import logger

class MagicMenu(QMenu):
    """
    Build [A627] SYNCED CAPTURE UI.
    - Receives pre-captured text from SmartTrigger.
    - Zero delay popup.
    """
    def __init__(self, controller, parent=None):
        super().__init__(parent); self.controller = controller 
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_InputMethodEnabled, False)
        self.setStyleSheet("QMenu { background-color: #1c2833; color: white; border: 2px solid #3498db; border-radius: 8px; padding: 5px; qproperty-iconSize: 24px 24px; } QMenu::item { padding: 10px 30px 10px 15px; border-radius: 4px; background-color: transparent; } QMenu::item:selected { background-color: #3498db; }")
        self._setup_actions(); self.selected_text = ""

    def _setup_actions(self):
        self.clear(); config_items = self.controller.settings.raw_config.get("magic_items", [])
        provider = QFileIconProvider()
        for item in config_items:
            if not item.get("visible", True): continue
            mid = item["id"]; name = item["name"]; act = QAction(name, self)
            if item.get("type") == "app":
                import shutil; resolved = shutil.which(item.get("val", "").strip().strip("'\"")) or item.get("val", "")
                if os.path.exists(resolved):
                    icon = provider.icon(QFileInfo(resolved))
                    if not icon.isNull(): act.setIcon(icon)
            act.triggered.connect(lambda checked, m=mid: self._process_request(m)); self.addAction(act)
            if mid == "LEARN": self.addSeparator()

    def popup_at_cursor(self, pre_captured_text=""):
        """ [A627] Receives pre-captured text from background thread """
        self.selected_text = pre_captured_text
        self._setup_actions()
        self.adjustSize()
        
        pos = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()
        
        menu_w = self.sizeHint().width()
        menu_h = self.sizeHint().height()
        
        x = pos.x() + 10
        y = pos.y() + 10
        
        if x + menu_w > screen.right():
            x = pos.x() - menu_w - 10
        if y + menu_h > screen.bottom():
            y = pos.y() - menu_h - 10
            
        x = max(screen.left(), x)
        y = max(screen.top(), y)
        
        self._show_time = time.time()
        self.exec(QPoint(x, y))

    def focusOutEvent(self, event): super().focusOutEvent(event); self.close()
    def _process_request(self, mode):
        if hasattr(self, '_show_time') and (time.time() - self._show_time < 0.15): return
        self.hide(); self.close(); time.sleep(0.02) 
        self.controller.magic_request_triggered.emit(mode, self.selected_text)

```

### 📄 `src/ui/plugins/magic_menu_v1.py`
```python
# src/ui/plugins/magic_menu_v1.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QApplication
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QIcon

class MagicMenuV1(QWidget):
    """
    Context Magic Menu [A97]:
    - Floating AI action menu.
    - Modern minimalist design.
    """
    action_triggered = Signal(str) # Emits the action type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        # Style based on A81 Capsule aesthetics
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 1px solid #3498db;
                border-radius: 8px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 8px 15px;
                text-align: left;
                font-family: "Microsoft JhengHei";
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-radius: 4px;
            }
        """)

        actions = [
            ("✨ AI 潤飾 (正式)", "rewrite_formal"),
            ("📝 AI 縮寫 (簡潔)", "rewrite_concise"),
            ("🌐 翻譯成英文", "translate_en"),
            ("↩️ 復原原始文字", "undo")
        ]

        for label, act_id in actions:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=act_id: self.on_action(a))
            self.layout.addWidget(btn)

    def on_action(self, action_id):
        self.action_triggered.emit(action_id)
        self.hide()

    def popup(self):
        # Position at current mouse cursor
        pos = QCursor.pos()
        self.move(pos.x() + 5, pos.y() + 5)
        self.show()
        self.raise_()
        self.activateWindow()

```

### 📄 `src/ui/recording_widget.py`
```python
# src/ui/recording_widget.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QCursor
import math

class WaveAnimation(QWidget):
    def __init__(self, parent=None, is_mini=False):
        super().__init__(parent)
        # [A536] Centered Mini Wave
        size_w = 30 if is_mini else 40
        size_h = 12 if is_mini else 16
        self.setFixedSize(size_w, size_h)
        self.phase = 0
        self.is_mini = is_mini
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(50)

    def update_wave(self):
        self.phase += 0.2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        spacing = 5 if self.is_mini else 6
        bar_w = 2 if self.is_mini else 3
        max_h = 10 if self.is_mini else 14
        
        # [A536] Calculate centering offset for bars
        total_w = (4 * spacing) + bar_w
        offset_x = (self.width() - total_w) / 2
        
        # Draw 5 bars symmetrically
        for i in range(5):
            h = 3 + abs(math.sin(self.phase + i * 0.8)) * max_h
            painter.setBrush(QColor(255, 255, 255, 220))
            painter.setPen(Qt.NoPen)
            x = offset_x + (i * spacing)
            y = (self.height() - h) / 2
            painter.drawRoundedRect(x, y, bar_w, h, 1, 1)

class RecordingWidget(QWidget):
    position_changed = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self.display_style = 0 # 0: Bubble, 1: Cursor Wave, 2: Hidden
        self.is_positioning_mode = False # [A554] Persistent positioning
        self._follow_timer = QTimer(self); self._follow_timer.timeout.connect(self._follow_cursor)
        self.setup_ui()
    
    def enter_positioning_mode(self, text="請拖曳調整位置..."):
        """ [A554] Enter persistent positioning mode """
        self.is_positioning_mode = True
        self.set_style(0) # Force bubble
        if hasattr(self, 'label'):
            self.label.setText(text)
        self.show_recording()
        # [A554] In positioning mode, we WANT focus for the click-to-close
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, False)
        self.show()

    def exit_positioning_mode(self):
        """ [A554] Exit and restore flags """
        self.is_positioning_mode = False
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)
        self.hide()
        
    def setup_ui(self):
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget(): child.widget().deleteLater()
        else:
            self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.display_style == 2: # Hidden
            self.setFixedSize(1, 1); return

        if self.display_style == 1: # [A536] Compact Centered Cursor Wave
            self.setFixedSize(48, 24) 
            self.container = QFrame(); self.container.setFixedSize(48, 24)
            self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid rgba(255,255,255,60);")
            cl = QHBoxLayout(self.container); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0); cl.setAlignment(Qt.AlignCenter)
            
            self.wave = WaveAnimation(is_mini=True)
            self.loading_label = QLabel("未啟動")
            self.loading_label.setStyleSheet("color: #f39c12; font-size: 10px; font-weight: bold; font-family: 'Microsoft JhengHei';")
            self.loading_label.hide()
            
            cl.addWidget(self.wave)
            cl.addWidget(self.loading_label)
            
            self.main_layout.addWidget(self.container)
            self._follow_timer.start(10)
        else: # Traditional Bubble
            self._follow_timer.stop()
            self.setFixedSize(160, 36)
            self.pill = QFrame(); self.pill.setObjectName("pill"); self.pill.setFixedSize(160, 36)
            self.pill.setAttribute(Qt.WA_TransparentForMouseEvents) # [A549]
            self.pill.setStyleSheet("QFrame#pill { background-color: rgba(30, 30, 30, 230); border-radius: 18px; border: 1px solid rgba(255, 255, 255, 60); }")
            pl = QHBoxLayout(self.pill); pl.setContentsMargins(10, 0, 10, 0); pl.setSpacing(6)
            self.dot = QLabel(); self.dot.setFixedSize(8, 8); self.dot.setStyleSheet("background-color: #ff4d4d; border-radius: 4px;")
            self.label = QLabel("正在聽..."); self.label.setStyleSheet("color: white; font-family: 'Microsoft JhengHei'; font-size: 13px; font-weight: bold;")
            self.wave = WaveAnimation()
            
            # [A550] Ensure all children are transparent for dragging
            for w in [self.dot, self.label, self.wave]: 
                w.setAttribute(Qt.WA_TransparentForMouseEvents)
                
            pl.addWidget(self.dot); pl.addWidget(self.label); pl.addWidget(self.wave)
            self.main_layout.addWidget(self.pill)

    def set_style(self, style_idx):
        self.display_style = style_idx
        self.setup_ui()

    def _follow_cursor(self):
        if self.isVisible() and self.display_style == 1:
            pos = QCursor.pos()
            # [A536] Center vertically, 20px to the right
            self.move(pos.x() + 20, pos.y() - 12)

    def set_initial_position(self, x=None, y=None):
        if self.display_style == 1: return
        screen = self.screen().geometry()
        if x is not None and y is not None: self.move(x, y)
        else: self.move((screen.width() - 160) // 2, 80)

    def show_recording(self):
        if self.display_style == 2: return
        # [A526/A536/A552] Reset to normal state ONLY if text is "正在啟動中..."
        if hasattr(self, 'label') and self.display_style == 0:
            if self.label.text() == "正在啟動中...":
                self.label.setText("正在聽...")
            self.dot.setStyleSheet("background-color: #ff4d4d; border-radius: 4px;")
        
        if hasattr(self, 'container') and self.display_style == 1:
            self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid rgba(255,255,255,60);")
            if hasattr(self, 'wave'): self.wave.show()
            if hasattr(self, 'loading_label'): self.loading_label.hide()
            
        self.show()
        self.setWindowOpacity(1.0) # Ensure visible
        if self.display_style == 0: self.raise_()

    def set_loading_state(self):
        """ [A536] Visual feedback when engine is still loading """
        if self.display_style == 2: return
        self.show()
        if self.display_style == 0:
            if hasattr(self, 'label'): 
                self.label.setText("正在啟動中...")
                self.dot.setStyleSheet("background-color: #f39c12; border-radius: 4px;") # Yellow for loading
            self.raise_()
        elif self.display_style == 1:
            if hasattr(self, 'container'):
                self.container.setStyleSheet("background: rgba(30, 30, 30, 200); border-radius: 12px; border: 1px solid #f39c12;")
                if hasattr(self, 'wave'): self.wave.hide()
                if hasattr(self, 'loading_label'): self.loading_label.show()

    def show_processing(self):
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_pos is not None:
            self._drag_pos = None
            pos = self.pos()
            self.position_changed.emit(pos.x(), pos.y())
            event.accept()

```

### 📄 `src/ui/repeat_learn_dialog.py`
```python
# src/ui/repeat_learn_dialog.py
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class RepeatLearnDialog(QDialog):
    """ [A185] Learning Dialog triggered by repeat voice input """
    def __init__(self, raw_text, candidates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📓 發現重複語音 - 是否加入個人詞庫？")
        self.setFixedSize(450, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.raw_text = raw_text
        self.selected_correct = ""
        self.setup_ui(candidates)

    def setup_ui(self, candidates):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"您剛才重複輸入了：\n「{self.raw_text}」", font="bold"))
        layout.addWidget(QLabel("\n這通常代表 AI 聽錯了。請選擇正確的內容："))
        
        self.group = QButtonGroup(self)
        for i, cand in enumerate(candidates):
            rb = QRadioButton(cand)
            self.group.addButton(rb, i)
            layout.addWidget(rb)
        
        # Manual Input
        layout.addWidget(QLabel("\n或是手動輸入正確文字："))
        self.manual_in = QLineEdit()
        layout.addWidget(self.manual_in)
        
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 加入詞庫並修正"); btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton("❌ 忽略"); btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok); btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _on_ok(self):
        # Priority: Manual > Selected
        self.selected_correct = self.manual_in.text().strip()
        if not self.selected_correct:
            btn = self.group.checkedButton()
            if btn: self.selected_correct = btn.text()
            
        if self.selected_correct:
            self.accept()
        else:
            self.reject()

```

### 📄 `src/ui/settings_window.py`
```python
# src/ui/settings_window.py
import os, json, sqlite3, shutil, sys, threading, time
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QGroupBox, QDialog, QTabWidget, 
                             QCheckBox, QGridLayout, QListWidget, QFileDialog, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QTextEdit, QListWidgetItem, QFrame, 
                             QSlider, QAbstractItemView, QMenu, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPoint
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QAction
from loguru import logger
from src.utils.path_helper import get_writable_path

CONFIG_PATH = get_writable_path(os.path.join("user_data", "gemini_tool_config.json"))
HW_CHINESE = {"mouse_back": "滑鼠側後退鍵", "mouse_forward": "滑鼠側前進鍵", "mouse_middle": "滑鼠中鍵", 
              "ctrl": "Ctrl", "shift": "Shift", "alt": "Alt", "win": "Win鍵", "enter": "Enter", 
              "space": "空白鍵", "tab": "Tab", "f10": "F10", "f12": "F12"}
MODIFIERS = ["ctrl", "shift", "alt", "win"]

def to_chinese_hk(hk): 
    if not hk: return "未設定"
    return "+".join([HW_CHINESE.get(p, p.upper()) for p in hk.lower().split('+')])

class UnifiedKeyDialog(QDialog):
    """ [A636] RESTORED: Missing Hotkey Configuration Dialog """
    def __init__(self, current_hk, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ 設定組合按鍵")
        self.setFixedSize(550, 650)
        self.selected_mods = []
        self.selected_key = ""
        self.btn_map = {}
        self._parse_hk(current_hk)
        self.setup_ui()
        
    def _parse_hk(self, hk_str):
        if not hk_str: return
        parts = hk_str.lower().split('+')
        for p in parts:
            if p in MODIFIERS: self.selected_mods.append(p)
            else: self.selected_key = p
            
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; color: #ecf0f1; } 
            QGroupBox { border: 1px solid #34495e; color: #3498db; } 
            QPushButton[selected='true'] { background: #f39c12; }
            QPushButton { background: #34495e; border: 1px solid #3498db; color: white; padding: 5px; }
        """)
        layout = QVBoxLayout(self)
        gp = QGroupBox("🤝 直接錄製"); lp = QVBoxLayout(gp)
        self.btn_rec = QPushButton("🔴 開始錄製")
        self.btn_rec.clicked.connect(lambda: self.parent().start_pairing_requested.emit())
        lp.addWidget(self.btn_rec)
        layout.addWidget(gp)
        
        gm = QGroupBox("🎹 手動組合"); lm = QVBoxLayout(gm)
        self.tabs = QTabWidget()
        kg = {
            "控制": ["ctrl", "shift", "alt", "win", "mouse_back", "mouse_forward", "mouse_middle"], 
            "功能": ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"], 
            "字母": [chr(i) for i in range(ord('a'), ord('z')+1)]
        }
        for g, keys in kg.items():
            tab = QWidget(); grid = QGridLayout(tab)
            for i, k in enumerate(keys):
                btn = QPushButton(HW_CHINESE.get(k, k.upper()))
                btn.clicked.connect(lambda checked, v=k: self._toggle(v))
                grid.addWidget(btn, i//4, i%4)
                self.btn_map[k] = btn
            self.tabs.addTab(tab, g)
        lm.addWidget(self.tabs)
        layout.addWidget(gm)
        
        self.lbl_cur = QLabel()
        layout.addWidget(self.lbl_cur)
        
        br = QHBoxLayout()
        bok = QPushButton("✅ 確定"); bok.clicked.connect(self.accept); br.addWidget(bok)
        bcl = QPushButton("掃描清空"); bcl.clicked.connect(self._clear); br.addWidget(bcl)
        layout.addLayout(br)
        self._update()
        
    def _toggle(self, v):
        if v in MODIFIERS:
            if v in self.selected_mods: self.selected_mods.remove(v)
            else: self.selected_mods.append(v)
        else: self.selected_key = v
        self._update()
        
    def _clear(self): 
        self.selected_mods = []
        self.selected_key = ""
        self._update()
        
    def _update(self):
        s = self.result_hk
        self.lbl_cur.setText(f"目前：{to_chinese_hk(s)}")
        for k, b in self.btn_map.items(): 
            b.setProperty("selected", "true" if k in s.split('+') else "false")
            b.style().unpolish(b)
            b.style().polish(b)
            
    def update_captured(self, k): 
        self.selected_mods = []
        self.selected_key = ""
        self._parse_hk(k)
        self._update()
        
    @property
    def result_hk(self):
        p = sorted(list(set(self.selected_mods))) 
        if self.selected_key: p.append(self.selected_key)
        return "+".join(p)

class QuickAddDialog(QDialog):
    add_req = Signal(str, str)
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("📔 快速加入")
        self.setFixedSize(220, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self.setup_ui(initial_text)
        
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def setup_ui(self, initial_text):
        f = QFrame(self); f.setObjectName("MainFrame")
        f.setStyleSheet("""
            QFrame#MainFrame { background: #1a252f; border: 2px solid #3498db; border-radius: 8px; }
            QLabel { color: #f39c12; font-weight: bold; font-size: 8pt; }
            QLineEdit { background: white; color: black; border-radius: 2px; padding: 1px 3px; border: 1px solid #3498db; font-size: 9pt; }
            QPushButton { background: #2ecc71; color: white; font-weight: bold; border-radius: 3px; padding: 3px; font-size: 8pt; }
        """)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(f)
        vl = QVBoxLayout(f); vl.setContentsMargins(5, 5, 5, 5); vl.setSpacing(3)
        
        h_top = QHBoxLayout(); h_top.addWidget(QLabel("✨ 快速新增")); h_top.addStretch()
        b_cls = QPushButton("✕"); b_cls.setFixedSize(16, 16); b_cls.setStyleSheet("background: #e74c3c; border: none;"); b_cls.clicked.connect(self.reject)
        h_top.addWidget(b_cls); vl.addLayout(h_top)
        
        gl = QGridLayout(); gl.setSpacing(3)
        gl.addWidget(QLabel("❌:"), 0, 0); self.in_err = QLineEdit(initial_text); self.in_err.setFixedHeight(20); gl.addWidget(self.in_err, 0, 1)
        gl.addWidget(QLabel("✅:"), 1, 0); self.in_corr = QLineEdit(); self.in_corr.setFixedHeight(20); gl.addWidget(self.in_corr, 1, 1)
        vl.addLayout(gl)
        
        self.btn_add = QPushButton("新增 (Enter)"); self.btn_add.clicked.connect(self._handle_add); vl.addWidget(self.btn_add)
        self.in_corr.setFocus()
        self.in_corr.returnPressed.connect(self._handle_add)
        self.in_err.returnPressed.connect(self._handle_add)

    def _handle_add(self):
        err = self.in_err.text().strip(); corr = self.in_corr.text().strip()
        if err and corr: self.add_req.emit(err, corr); self.accept()

class RefinementDialog(QDialog):
    restore_requested = Signal(str); retry_requested = Signal(str); profile_changed = Signal(int)
    def __init__(self, text, profiles=None, active_idx=0, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.original_text = text; self._drag_pos = None; self.profiles = profiles or []; self.active_idx = active_idx; self.setup_ui()
        p = QCursor.pos(); s = QGuiApplication.primaryScreen().availableGeometry(); self.move(max(s.left(), min(p.x()+15, s.right()-210)), max(s.top(), min(p.y()+15, s.bottom()-150)))
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos: self.move(e.globalPosition().toPoint() - self._drag_pos)
    def setup_ui(self):
        f = QFrame(self); f.setObjectName("MainFrame"); f.setStyleSheet("QFrame#MainFrame{background:#1a252f;border:1px solid #3498db;border-radius:6px;} QPushButton{background:#2c3e50;padding:6px;border-radius:3px;color:white;border:1px solid #3498db;} QLabel{color:#f39c12;font-weight:bold;font-size:9pt;}")
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(f); vl = QVBoxLayout(f)
        h = QHBoxLayout(); self.status = QLabel("⏳ AI 處理中..."); h.addWidget(self.status); h.addStretch()
        b_cls = QPushButton("✕"); b_cls.setFixedWidth(25); b_cls.clicked.connect(self.reject); h.addWidget(b_cls); vl.addLayout(h)
        if self.profiles:
            self.btn_prof = QPushButton(f"📑 方案: {self.profiles[self.active_idx]}"); self.btn_prof.clicked.connect(self._cycle_profile); vl.addWidget(self.btn_prof)
        br = QHBoxLayout(); self.btn_restore = QPushButton("🔙 還原"); self.btn_restore.clicked.connect(lambda: self.restore_requested.emit(self.original_text) or self.accept()); br.addWidget(self.btn_restore); vl.addLayout(br)
    def _cycle_profile(self):
        self.active_idx = (self.active_idx + 1) % len(self.profiles); self.btn_prof.setText(f"📑 方案: {self.profiles[self.active_idx]}"); self.profile_changed.emit(self.active_idx)

class DictionaryManager(QDialog):
    add_req = Signal(str, str); del_req = Signal(str); closed_signal = Signal()
    def __init__(self, i, parent=None, initial_text=""): 
        super().__init__(parent); self.setWindowTitle("📔 個人詞庫管理"); self.setFixedSize(600, 650); self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint); self.all_items = i; self.setup_ui(initial_text)
    def setup_ui(self, initial_text):
        self.setStyleSheet("""QDialog { background: #1a252f; color: #ecf0f1; } QPushButton { background: #2c3e50; border: 1px solid #3498db; color: white; padding: 8px; } QLineEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 3px; padding: 5px; } QListWidget { background: #0d1117; color: #f1c40f; border: 1px solid #3498db; font-size: 10pt; } QListWidget::item { border-bottom: 1px solid #2c3e50; height: 50px; } QListWidget::item:selected { background: #3498db; color: white; }""")
        l = QVBoxLayout(self); l.addWidget(QLabel("📖 詞庫列表 (錯誤音 ➔ 正確字):"))
        self.lw = QListWidget(); self.lw.setViewMode(QListWidget.IconMode); self.lw.setFlow(QListWidget.TopToBottom); self.lw.setWrapping(True); self.lw.setResizeMode(QListWidget.Adjust); self.lw.setMovement(QListWidget.Static); self.lw.setSpacing(2); self.lw.setGridSize(QSize(180, 60)); self.lw.setSelectionMode(QAbstractItemView.SingleSelection); self.lw.itemClicked.connect(self._on_item_clicked); self.upd(self.all_items); l.addWidget(self.lw)
        gh = QHBoxLayout(); self.iw = QLineEdit(); self.iw.setPlaceholderText("❌ 錯誤音"); self.ir = QLineEdit(); self.ir.setPlaceholderText("✅ 正確字"); gh.addWidget(self.iw); gh.addWidget(self.ir); l.addLayout(gh)
        bh = QHBoxLayout(); b_a = QPushButton("➕ 新增詞條"); b_a.clicked.connect(self._add); bh.addWidget(b_a, 2); b_d = QPushButton("🗑️ 刪除選取"); b_d.clicked.connect(self._del_active); bh.addWidget(b_d, 1); l.addLayout(bh)
        b_cl = QPushButton("💾 儲存並關閉"); b_cl.setMinimumHeight(40); b_cl.setStyleSheet("background: #27ae60; font-weight: bold;"); b_cl.clicked.connect(self.close)
        l.addWidget(b_cl)
        if initial_text: self.iw.setText(initial_text); self.ir.setFocus()
    def upd(self, i):
        self.lw.clear(); groups = {}
        for o, c in i: groups.setdefault(c, []).append(o)
        for k in sorted(groups.keys()):
            vars = groups[k]; text = f"{k} ({len(vars)})" if len(vars) > 1 else f"{vars[0]} ➔ {k}"; item = QListWidgetItem(text); item.setData(Qt.UserRole, (k, vars)); item.setTextAlignment(Qt.AlignCenter); self.lw.addItem(item)
    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data and len(data[1]) > 1:
            m = QMenu(self); m.setStyleSheet("background: #2c3e50; color: white;")
            for v in data[1]:
                a = QAction(f"❌ 刪除: {v} ➔ {data[0]}", self); a.triggered.connect(lambda chk=False, ov=v: self._del_specific(ov)); m.addAction(a)
            m.exec(QCursor.pos())
    def _add(self):
        o, c = self.iw.text().strip(), self.ir.text().strip()
        if o and c: self.add_req.emit(o, c); self.all_items.append((o, c)); self.upd(self.all_items); self.iw.clear(); self.ir.clear()
    def _del_active(self):
        if self.lw.currentItem():
            d = self.lw.currentItem().data(Qt.UserRole)
            if d: self._del_specific(d[1][0]) if len(d[1]) == 1 else self._on_item_clicked(self.lw.currentItem())
    def _del_specific(self, o): self.del_req.emit(o); self.all_items = [x for x in self.all_items if x[0] != o]; self.upd(self.all_items)
    def closeEvent(self, e): self.closed_signal.emit(); super().closeEvent(e)

class AppPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 選擇已安裝程式")
        self.setFixedSize(500, 550)
        self.selected_path = ""
        self.all_apps = []
        
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; color: #ecf0f1; }
            QLineEdit { background: white; color: black; border-radius: 4px; padding: 6px; }
            QListWidget { background: #1a252f; color: white; border: 1px solid #3498db; border-radius: 4px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #2c3e50; }
            QListWidget::item:selected { background: #3498db; }
            QPushButton { background: #34495e; border: 1px solid #3498db; color: white; padding: 8px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🔍 輸入關鍵字搜尋已安裝軟體:"))
        self.search_in = QLineEdit()
        self.search_in.textChanged.connect(self._filter)
        layout.addWidget(self.search_in)
        
        self.lw = QListWidget()
        self.lw.setIconSize(QSize(32, 32))
        layout.addWidget(self.lw)
        
        self.status_lbl = QLabel("⏳ 正在掃描系統應用程式...")
        layout.addWidget(self.status_lbl)
        
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 選擇並套用"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ 取消"); btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok); btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)
        
        self.lw.itemDoubleClicked.connect(lambda: self.accept())
        
        threading.Thread(target=self._load_apps, daemon=True).start()

    def _load_apps(self):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        provider = QFileIconProvider()
        paths = []
        
        # 公用開始選單
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        
        # 個人開始選單
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        
                        # 取得系統圖示
                        icon = provider.icon(QFileInfo(full_path))
                        apps_found.append((name, full_path, icon))
        
        apps_found.sort(key=lambda x: x[0].lower())
        
        common_apps = [
            ("📸 截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 剪貼簿歷史記錄 (Win+V)", "system://clipboard")
        ]
        
        final_apps = []
        for name, path in common_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path == "system://clipboard" else path
            icon = provider.icon(QFileInfo(icon_path))
            final_apps.append((name, path, icon))
            
        final_apps.extend(apps_found)
        self.all_apps = final_apps
        
        QTimer.singleShot(0, self._populate_ui)

    def _populate_ui(self):
        self.lw.clear()
        for name, path, icon in self.all_apps:
            item = QListWidgetItem(name)
            item.setIcon(icon)
            item.setData(Qt.UserRole, path)
            self.lw.addItem(item)
        self.status_lbl.setText(f"✅ 掃描完成。共找到 {len(self.all_apps)} 個應用程式。")

    def _filter(self, text):
        text = text.lower().strip()
        self.lw.clear()
        for name, path, icon in self.all_apps:
            if not text or text in name.lower():
                item = QListWidgetItem(name)
                item.setIcon(icon)
                item.setData(Qt.UserRole, path)
                self.lw.addItem(item)

    def accept(self):
        item = self.lw.currentItem()
        if item:
            self.selected_path = item.data(Qt.UserRole)
            super().accept()
        else:
            QMessageBox.warning(self, "提示", "請先選擇一個應用程式。")

class MacroEditorDialog(QDialog):
    def __init__(self, n="", t="text", v="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ 編輯自定義按鈕")
        self.setFixedSize(520, 600)
        self.setStyleSheet("""
            QDialog { background: #2c3e50; color: #ecf0f1; } 
            QLineEdit, QTextEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 4px; padding: 5px; } 
            QRadioButton { color: #ecf0f1; font-weight: bold; }
            QPushButton { background: #34495e; border: 2px solid #3498db; color: white; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background: #2980b9; }
        """)
        self.is_rec = False
        l = QVBoxLayout(self)
        l.setSpacing(8)
        
        # 1. Name input
        l.addWidget(QLabel("📝 按鈕顯示名稱:"))
        self.name_in = QLineEdit(n)
        self.name_in.setPlaceholderText("例如：剪圖、小畫家、我的常用文字...")
        l.addWidget(self.name_in)
        
        l.addSpacing(5)
        
        # 2. Execution Type selection
        l.addWidget(QLabel("⚡ 選擇按鈕執行類型 (單選):"))
        
        # Group radio buttons inside a nice frame with borders or background
        type_frame = QFrame()
        type_frame.setStyleSheet("QFrame { background: #1a252f; border: 1px solid #34495e; border-radius: 6px; padding: 10px; } QLabel { border: none; background: transparent; } QRadioButton { border: none; background: transparent; }")
        tf_layout = QVBoxLayout(type_frame)
        tf_layout.setSpacing(6)
        tf_layout.setContentsMargins(10, 8, 10, 8)
        
        self.type_group = QButtonGroup(self)
        
        self.r_text = QRadioButton("💬 常用文字輸入 (自動打字貼上)")
        self.r_keys = QRadioButton("⌨️ 模擬鍵盤組合鍵 (快捷鍵)")
        self.r_sys = QRadioButton("💻 啟動系統內建工具 (截圖、小畫家...)")
        self.r_app = QRadioButton("🚀 啟動自定義軟體或檔案 (本機應用程式)")
        
        self.type_group.addButton(self.r_text, 0)
        self.type_group.addButton(self.r_keys, 1)
        self.type_group.addButton(self.r_sys, 2)
        self.type_group.addButton(self.r_app, 3)
        
        lbl_text_desc = QLabel("💡 說明：點擊按鈕時，直接在目前的游標焦點處輸入您設定的常用文字、句子或範本（免去重複打字）。")
        lbl_text_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_text_desc.setWordWrap(True)
        
        lbl_keys_desc = QLabel("💡 說明：點擊按鈕時，模擬按下一組鍵盤快捷鍵（例如複製 Ctrl+C、重做 Ctrl+Y 等）。")
        lbl_keys_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_keys_desc.setWordWrap(True)
        
        lbl_sys_desc = QLabel("💡 說明：點擊按鈕時，直接開啟 Windows 內建的工具，如系統截圖、小畫家、計算機、螢幕鍵盤等。")
        lbl_sys_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_sys_desc.setWordWrap(True)
        
        lbl_app_desc = QLabel("💡 說明：點擊按鈕時，開啟您自行設定的本機常用應用程式、檔案、路徑或網頁。")
        lbl_app_desc.setStyleSheet("color: #95a5a6; font-size: 11px;")
        lbl_app_desc.setWordWrap(True)
        
        tf_layout.addWidget(self.r_text)
        tf_layout.addWidget(lbl_text_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_keys)
        tf_layout.addWidget(lbl_keys_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_sys)
        tf_layout.addWidget(lbl_sys_desc)
        tf_layout.addSpacing(4)
        tf_layout.addWidget(self.r_app)
        tf_layout.addWidget(lbl_app_desc)
        
        l.addWidget(type_frame)
        
        l.addSpacing(5)
        
        # 3. Value editor block
        self.t_lbl = QLabel("🔧 設定內容:")
        l.addWidget(self.t_lbl)
        
        self.val_text = QTextEdit(v if t == "text" else "")
        self.val_text.setPlaceholderText("請輸入您想要自動輸入 the 文字、範本或段落...")
        l.addWidget(self.val_text)
        
        kh = QHBoxLayout()
        self.val_keys = QLineEdit(v if t == "combo" else "")
        self.val_keys.setPlaceholderText("點擊右側按鈕開始錄製組合鍵...")
        self.btn_rec = QPushButton("🔴 錄製按鍵")
        self.btn_rec.clicked.connect(self._toggle_rec)
        kh.addWidget(self.val_keys)
        kh.addWidget(self.btn_rec)
        l.addLayout(kh)
        
        self.sys_combo = QComboBox()
        self.sys_combo.setIconSize(QSize(20, 20))
        self.sys_combo.setStyleSheet("QComboBox { background: white; color: black; padding: 5px; border-radius: 4px; }")
        l.addWidget(self.sys_combo)
        
        self.app_layout = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.setIconSize(QSize(20, 20))
        self.app_combo.setStyleSheet("QComboBox { background: white; color: black; padding: 5px; border-radius: 4px; }")
        self.btn_browse = QPushButton("📁 瀏覽檔案")
        self.btn_browse.clicked.connect(self._browse_app)
        self.app_layout.addWidget(self.app_combo, 1)
        self.app_layout.addWidget(self.btn_browse)
        l.addLayout(self.app_layout)
        
        # Populate sys_combo
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        provider = QFileIconProvider()
        sys_apps = [
            ("📸 系統截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 系統小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 系統計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 系統記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 系統螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 系統剪貼簿歷史記錄 (Win+V)", "system://clipboard"),
            ("📂 系統檔案總管 (explorer.exe)", "explorer.exe"),
            ("⚙️ 系統設定 (ms-settings:)", "ms-settings:")
        ]
        for name, path in sys_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path in ["system://clipboard", "ms-settings:"] else path
            icon = provider.icon(QFileInfo(icon_path))
            self.sys_combo.addItem(icon, name, path)
            
        # Connect radio buttons selection change
        self.r_text.toggled.connect(self._sync)
        self.r_keys.toggled.connect(self._sync)
        self.r_sys.toggled.connect(self._sync)
        self.r_app.toggled.connect(self._sync)
        
        # Initial selection mapping
        idx = 0
        sys_match_idx = -1
        if t == "combo":
            idx = 1
        elif t == "app":
            # Check if it matches any system app path
            for i in range(self.sys_combo.count()):
                if self.sys_combo.itemData(i) and v and self.sys_combo.itemData(i).lower() == v.lower():
                    sys_match_idx = i
                    break
            if sys_match_idx != -1:
                idx = 2
            else:
                idx = 3
                
        if idx == 0: self.r_text.setChecked(True)
        elif idx == 1: self.r_keys.setChecked(True)
        elif idx == 2:
            self.r_sys.setChecked(True)
            self.sys_combo.setCurrentIndex(sys_match_idx)
        elif idx == 3: self.r_app.setChecked(True)
        
        self._sync()
        
        l.addSpacing(10)
        b_ok = QPushButton("✅ 確定儲存")
        b_ok.clicked.connect(self.accept)
        l.addWidget(b_ok)
        
        # Check if parent has pre-scanned cached apps list
        apps = []
        if parent and hasattr(parent, 'cached_apps') and parent.cached_apps:
            apps = parent.cached_apps
            
        if apps:
            self._populate_combo(apps, v if (t == "app" and idx == 3) else "")
        else:
            self.app_combo.addItem("⏳ 正在掃描系統應用程式...", "")
            threading.Thread(target=self._scan_apps_for_combo, args=(v if (t == "app" and idx == 3) else "",), daemon=True).start()
            
    def _sync(self): 
        idx = self.type_group.checkedId()
        self.val_text.setVisible(idx == 0)
        self.val_keys.setVisible(idx == 1)
        self.btn_rec.setVisible(idx == 1)
        self.sys_combo.setVisible(idx == 2)
        self.app_combo.setVisible(idx == 3)
        self.btn_browse.setVisible(idx == 3)
        
    def _scan_apps_for_combo(self, initial_val=""):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        provider = QFileIconProvider()
        paths = []
        
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        icon = provider.icon(QFileInfo(full_path))
                        apps_found.append((name, full_path, icon))
                        
        apps_found.sort(key=lambda x: x[0].lower())
        
        common_apps = [
            ("📸 截圖工具 (SnippingTool.exe)", "C:\\Windows\\System32\\SnippingTool.exe"),
            ("🎨 小畫家 (mspaint.exe)", "C:\\Windows\\System32\\mspaint.exe"),
            ("🧮 計算機 (calc.exe)", "C:\\Windows\\System32\\calc.exe"),
            ("📝 記事本 (notepad.exe)", "C:\\Windows\\System32\\notepad.exe"),
            ("⌨️ 螢幕小鍵盤 (osk.exe)", "C:\\Windows\\System32\\osk.exe"),
            ("📋 剪貼簿歷史記錄 (Win+V)", "system://clipboard")
        ]
        
        final_apps = []
        for name, path in common_apps:
            icon_path = "C:\\Windows\\System32\\shell32.dll" if path == "system://clipboard" else path
            icon = provider.icon(QFileInfo(icon_path))
            final_apps.append((name, path, icon))
            
        final_apps.extend(apps_found)
        
        if self.parent() and hasattr(self.parent(), "cached_apps"):
            self.parent().cached_apps = final_apps
            
        QTimer.singleShot(0, lambda: self._populate_combo(final_apps, initial_val))

    def _populate_combo(self, apps, initial_val=""):
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        
        self.app_combo.clear()
        self.app_combo.addItem("--- 請選擇本機軟體 ---", "")
        
        found_idx = 0
        for name, path, icon in apps:
            self.app_combo.addItem(icon, name, path)
            if initial_val and path.lower() == initial_val.lower():
                found_idx = self.app_combo.count() - 1
                
        if initial_val and found_idx == 0:
            provider = QFileIconProvider()
            icon = provider.icon(QFileInfo(initial_val))
            name = os.path.basename(initial_val)
            self.app_combo.addItem(icon, name, initial_val)
            found_idx = self.app_combo.count() - 1
            
        self.app_combo.setCurrentIndex(found_idx)

    def _browse_app(self):
        p, _ = QFileDialog.getOpenFileName(self, "選擇要啟動的程式或檔案", "", "All Files (*.*)")
        if p:
            from PySide6.QtWidgets import QFileIconProvider
            from PySide6.QtCore import QFileInfo
            provider = QFileIconProvider()
            icon = provider.icon(QFileInfo(p))
            name = os.path.basename(p)
            
            for idx in range(self.app_combo.count()):
                if self.app_combo.itemData(idx) == p:
                    self.app_combo.setCurrentIndex(idx)
                    return
                    
            self.app_combo.addItem(icon, name, p)
            self.app_combo.setCurrentIndex(self.app_combo.count() - 1)
            
    def _toggle_rec(self):
        if not self.is_rec:
            self.is_rec = True
            self.btn_rec.setText("⏹️ 停止並追加")
            self.btn_rec.setStyleSheet("background: #e74c3c; border: 2px solid white;")
            if hasattr(self.parent(), 'start_pairing_requested'): 
                self.parent().start_pairing_requested.emit()
        else:
            self.is_rec = False
            self.btn_rec.setText("🔴 錄製按鍵")
            self.btn_rec.setStyleSheet("")
            if hasattr(self.parent(), 'stop_pairing_requested'):
                self.parent().stop_pairing_requested.emit()
                
    def update_captured(self, k): 
        cur = self.val_keys.text().strip()
        self.val_keys.setText(f"{cur}, {k}" if cur else k)
        self.val_keys.setStyleSheet("background: #2ecc71; color: white;")
        QTimer.singleShot(200, lambda: self.val_keys.setStyleSheet(""))
        
    def get_data(self): 
        idx = self.type_group.checkedId()
        t = "text"
        if idx == 1: t = "combo"
        elif idx in [2, 3]: t = "app"
        
        val = ""
        if idx == 0: val = self.val_text.toPlainText()
        elif idx == 1: val = self.val_keys.text()
        elif idx == 2: val = self.sys_combo.itemData(self.sys_combo.currentIndex()) or ""
        elif idx == 3: val = self.app_combo.itemData(self.app_combo.currentIndex()) or ""
        
        return self.name_in.text(), t, val

class MagicItemWidget(QWidget):
    del_req = Signal()
    edit_req = Signal()
    vis_changed = Signal(bool)
    def __init__(self, n, v, b, parent=None):
        super().__init__(parent)
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 2, 5, 2)
        self.chk = QCheckBox()
        self.chk.setChecked(v)
        self.chk.toggled.connect(self.vis_changed.emit)
        l.addWidget(self.chk)
        self.lbl = QLabel(n)
        self.lbl.setStyleSheet("font-weight: bold;")
        l.addWidget(self.lbl)
        l.addStretch()
        if not b:
            b_ed = QPushButton("📝")
            b_ed.setFixedSize(35, 35)
            b_ed.setStyleSheet("border: 2px solid #3498db; background: #34495e;")
            b_ed.clicked.connect(self.edit_req.emit)
            l.addWidget(b_ed)
            b_de = QPushButton("✕")
            b_de.setFixedSize(35, 35)
            b_de.setStyleSheet("color: #e74c3c; border: 2px solid #e74c3c; background: #34495e;")
            b_de.clicked.connect(self.del_req.emit)
            l.addWidget(b_de)
        h = QLabel("≡")
        h.setStyleSheet("font-size: 18pt; color: #7f8c8d;")
        l.addWidget(h)

class ProfileManager(QDialog):
    def __init__(self, profiles, active_idx, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ AI 提示詞最佳化方案管理員")
        self.setFixedSize(700, 500)
        self.profiles = [p.copy() for p in profiles]
        self.active_idx = active_idx
        self._is_loading = False
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
        layout = QVBoxLayout(self)
        main_h = QHBoxLayout()
        left_f = QVBoxLayout()
        left_f.addWidget(QLabel("方案清單 (請在主頁面切換):"))
        self.list_w = QListWidget()
        self.list_w.setStyleSheet("background: #34495e; color: white;")
        for p in self.profiles: 
            self.list_w.addItem(p["name"])
        left_f.addWidget(self.list_w)
        btn_add = QPushButton("➕ 新增方案")
        btn_add.clicked.connect(self._add)
        btn_del = QPushButton("🗑️ 刪除方案")
        btn_del.clicked.connect(self._del)
        left_f.addWidget(btn_add)
        left_f.addWidget(btn_del)
        main_h.addLayout(left_f, 1)
        
        right_f = QVBoxLayout()
        right_f.addWidget(QLabel("方案名稱:"))
        self.name_in = QLineEdit()
        self.name_in.textChanged.connect(self._auto_save_current)
        right_f.addWidget(self.name_in)
        right_f.addWidget(QLabel("AI 修飾規則指令:"))
        self.prompt_in = QTextEdit()
        self.prompt_in.textChanged.connect(self._auto_save_current)
        right_f.addWidget(self.prompt_in)
        main_h.addLayout(right_f, 2)
        
        layout.addLayout(main_h)
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("✅ 完成並套用")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
        
        self.list_w.currentRowChanged.connect(self._load_current)
        if self.profiles: 
            self.list_w.setCurrentRow(self.active_idx)

    def _load_current(self, idx):
        if 0 <= idx < len(self.profiles):
            self._is_loading = True
            self.name_in.setText(self.profiles[idx]["name"])
            self.prompt_in.setPlainText(self.profiles[idx]["prompt"])
            self._is_loading = False

    def _add(self):
        self.profiles.append({"name": "新方案", "prompt": "請修飾內容："})
        self.list_w.addItem("新方案")
        self.list_w.setCurrentRow(len(self.profiles) - 1)

    def _del(self):
        idx = self.list_w.currentRow()
        if idx >= 0 and len(self.profiles) > 1:
            self.profiles.pop(idx)
            self.list_w.takeItem(idx)
            self.list_w.setCurrentRow(0)

    def _auto_save_current(self):
        if self._is_loading: return
        idx = self.list_w.currentRow()
        if idx >= 0:
            self.profiles[idx]["name"] = self.name_in.text()
            self.profiles[idx]["prompt"] = self.prompt_in.toPlainText()
            self.list_w.item(idx).setText(self.name_in.text())

class SettingsWindow(QWidget):
    settings_changed = Signal(dict)
    preview_ui_requested = Signal()
    preview_sound_requested = Signal(int)
    clear_dict_requested = Signal()
    add_dict_requested = Signal(str, str)
    del_dict_requested = Signal(str)
    launch_vision_requested = Signal()
    ready_signal = Signal(str)
    models_scanned_signal = Signal(list)
    import_dict_requested = Signal(str)
    start_pairing_requested = Signal()
    stop_pairing_requested = Signal()
    
    def __init__(self):
        super().__init__(); self.dict_dlg = None; self.quick_add_dlg = None; self.raw_config = {}; self.dict_items = []
        self.cached_apps = []
        threading.Thread(target=self._pre_scan_apps, daemon=True).start()
        self.setWindowTitle("AI 助手系統設定 (Build [A1002])"); self.setFixedWidth(480); self.setStyleSheet("""QWidget { background: #1a252f; color: #ecf0f1; font-family: 'Microsoft JhengHei'; } QTabWidget::pane { border: 1px solid #34495e; background: #2c3e50; } QTabBar::tab { background: #34495e; color: #bdc3c7; padding: 8px 12px; } QTabBar::tab:selected { background: #3498db; color: white; } QGroupBox { border: 2px solid #34495e; margin-top: 8px; padding-top: 8px; color: #3498db; font-weight: bold; } QComboBox, QLineEdit, QTextEdit { background: white; color: black; border: 2px solid #3498db; border-radius: 3px; padding: 4px; } QPushButton { background: #34495e; border: 2px solid #3498db; color: white; padding: 8px; font-weight: bold; } QCheckBox { font-weight: bold; }""")
        self._save_timer = QTimer(); self._save_timer.setSingleShot(True); self._save_timer.setInterval(500); self._save_timer.timeout.connect(self._do_save); self.models_scanned_signal.connect(self._on_models_discovered); self.setup_ui(); self.load_settings()

    def _pre_scan_apps(self):
        import os
        from PySide6.QtWidgets import QFileIconProvider
        from PySide6.QtCore import QFileInfo
        provider = QFileIconProvider()
        paths = []
        p1 = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
        if os.path.exists(p1): paths.append(p1)
        appdata = os.environ.get("APPDATA")
        if appdata:
            p2 = os.path.join(appdata, "Microsoft\\Windows\\Start Menu\\Programs")
            if os.path.exists(p2): paths.append(p2)
            
        seen_names = set()
        apps_found = []
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        if name.lower() in seen_names: continue
                        full_path = os.path.join(root, f)
                        seen_names.add(name.lower())
                        try:
                            icon = provider.icon(QFileInfo(full_path))
                            apps_found.append((name, full_path, icon))
                        except: pass
        apps_found.sort(key=lambda x: x[0].lower())
        self.cached_apps = apps_found

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self); self.tabs = QTabWidget(); self.main_layout.addWidget(self.tabs)
        
        # Tab 1: 設定
        t1 = QWidget(); l1 = QVBoxLayout(t1)
        l1.setContentsMargins(12, 10, 12, 10)
        l1.setSpacing(8)
        
        # 1. 啟動與核心設定
        gs = QGroupBox("🧠 啟動與核心設定"); ls = QVBoxLayout(gs)
        ls.setContentsMargins(12, 10, 12, 10); ls.setSpacing(8)
        self.chk_auto_start = QCheckBox("隨電腦開機自動啟動助手")
        self.chk_smart_left = QCheckBox("🖱️ 啟用左鍵長按啟動語音輸入")
        self.chk_smart_right = QCheckBox("🔮 啟用右鍵長按顯示魔法選單")
        self.chk_use_punc = QCheckBox("啟用自動輸入標點")
        ls.addWidget(self.chk_auto_start)
        ls.addWidget(self.chk_smart_left)
        ls.addWidget(self.chk_smart_right)
        ls.addWidget(self.chk_use_punc)
        l1.addWidget(gs)
        
        # Row layout for side-by-side GroupBoxes
        row_modes = QHBoxLayout()
        row_modes.setSpacing(8)
        
        # 2. 語音輸入設定
        go = QGroupBox("語音輸入設定"); lo = QVBoxLayout(go)
        lo.setContentsMargins(10, 8, 10, 8); lo.setSpacing(12)
        
        self.smart_hold_combo = QComboBox()
        self.smart_hold_combo.addItems(["啟動久按時間 0.3s", "啟動久按時間 0.5s", "啟動久按時間 0.8s", "啟動久按時間 1.0s", "啟動久按時間 1.5s"])
        lo.addWidget(self.smart_hold_combo)
        
        self.rec_mode_cb = QComboBox()
        self.rec_mode_cb.addItems(["📞 對講機模式", "🔘 開關模式 (久按開/停止發話關)", "🔘 開關模式 (久按開/久按關)"])
        lo.addWidget(self.rec_mode_cb)
        
        self.output_mode_cb = QComboBox()
        self.output_mode_cb.addItems(["🚀 極速貼上", "🎹 打字機模式"])
        lo.addWidget(self.output_mode_cb)
        row_modes.addWidget(go)
        
        # 3. 快速鍵語音輸入設定
        ghk = QGroupBox("快速鍵語音輸入設定"); lh = QVBoxLayout(ghk)
        lh.setContentsMargins(10, 8, 10, 8); lh.setSpacing(6)
        self.hk_disp = QLabel("啟動語音輸入：")
        self.btn_hk = QPushButton("🔧 修改按鍵組合")
        self.btn_hk.clicked.connect(lambda: self.open_key_dialog("hotkey"))
        self.m_hk_disp = QLabel("啟動魔法選單：")
        self.btn_mhk = QPushButton("🔧 修改按鍵組合")
        self.btn_mhk.clicked.connect(lambda: self.open_key_dialog("magic_hotkey"))
        lh.addWidget(self.hk_disp)
        lh.addWidget(self.btn_hk)
        lh.addWidget(self.m_hk_disp)
        lh.addWidget(self.btn_mhk)
        row_modes.addWidget(ghk)
        
        l1.addLayout(row_modes)
        
        # 4. 啟動語音輸入風格
        ga = QGroupBox("啟動語音輸入風格"); la = QVBoxLayout(ga)
        la.setContentsMargins(12, 10, 12, 10); la.setSpacing(6)
        la.addWidget(QLabel("音效提醒風格："))
        self.sound_sel = QComboBox()
        self.sound_sel.addItems(["🫥 無提醒", "現代電子", "經典鈴聲", "沉穩鼓點", "科技掃描", "清脆警告", "柔和水滴", "數位通訊", "機械卡鎖", "未來科幻", "極簡提示"])
        la.addWidget(self.sound_sel)
        
        la.addWidget(QLabel("圖像提醒風格："))
        self.vis_style_cb = QComboBox()
        self.vis_style_cb.addItems(["🫥 無提醒", "💬 固定位置氣泡提醒", "✨ 跟隨遊標位置氣泡提醒"])
        la.addWidget(self.vis_style_cb)
        
        b_pos = QPushButton("📍 調整氣泡球固定位置")
        b_pos.clicked.connect(self.preview_ui_requested.emit)
        la.addWidget(b_pos)
        l1.addWidget(ga)
        
        # [A5] Compatibility variables for configuration sync without cluttering UI
        self.chk_audio_cue = QCheckBox()
        self.sound_sel.currentIndexChanged.connect(lambda idx: self.chk_audio_cue.setChecked(idx != 0))
        
        l1.addStretch()
        self.tabs.addTab(t1, "⚡ 設定")
        
        # Tab 2: 🪄 魔法選單
        tm = QWidget(); lm = QVBoxLayout(tm); lm.setContentsMargins(10,10,10,10)
        self.lw_mag = QListWidget()
        self.lw_mag.setDragDropMode(QListWidget.InternalMove)
        self.lw_mag.model().rowsMoved.connect(self._reorder)
        lm.addWidget(QLabel("選單管理 (≡ 拖拽排序 / 勾選隱藏):"))
        lm.addWidget(self.lw_mag)
        b_add_m = QPushButton("➕ 新增自定義按鈕")
        b_add_m.clicked.connect(self._add_macro)
        lm.addWidget(b_add_m)
        self.tabs.addTab(tm, "🪄 魔法選單")
        
        # Tab 3: Pro
        tp = QWidget(); lp = QVBoxLayout(tp)
        self.api_in = QLineEdit(); self.api_in.setEchoMode(QLineEdit.Password)
        lp.addWidget(QLabel("Gemini API Key:")); lp.addWidget(self.api_in)
        self.opt_m = QComboBox(); self.opt_m.setEditable(True)
        self.vis_m = QComboBox(); self.vis_m.setEditable(True)
        self.fix_m = QComboBox(); self.fix_m.setEditable(True)
        lp.addWidget(QLabel("✨ 1. 提示詞優化模型:"))
        lp.addWidget(self.opt_m)
        lp.addWidget(QLabel("📸 2. 截圖翻譯模型:"))
        lp.addWidget(self.vis_m)
        lp.addWidget(QLabel("🧠 3. 語音聽寫糾正模型:"))
        lp.addWidget(self.fix_m)
        b_chk = QPushButton("🔍 查詢模型清單"); b_chk.clicked.connect(self._check_models); lp.addWidget(b_chk)
        self.prof_cb = QComboBox()
        lp.addWidget(QLabel("AI 修改方案:"))
        lp.addWidget(self.prof_cb)
        b_p = QPushButton("⚙️ AI 提示詞管理"); b_p.clicked.connect(self.open_profile_manager); lp.addWidget(b_p)
        b_d = QPushButton("📔 個人詞庫管理"); b_d.clicked.connect(self.open_dict_manager); lp.addWidget(b_d)
        b_v = QPushButton("📸 截圖翻譯助手"); b_v.clicked.connect(self.launch_vision_requested.emit); lp.addWidget(b_v)
        lp.addStretch(); self.tabs.addTab(tp, "💎 Pro")
        
        # Tab 4: 工程
        te = QWidget(); le = QVBoxLayout(te)
        self.eng_cb = QComboBox(); self.eng_cb.addItems(["SenseVoice (極速版)", "V1 傳統版 (含本地 LLM)"])
        le.addWidget(QLabel("辨識引擎:")); le.addWidget(self.eng_cb)
        
        # Sensitivity Section
        h_sens = QHBoxLayout()
        h_sens.addWidget(QLabel("語音啟動靈敏度:"))
        self.vad_val_lbl = QLabel("50")
        self.vad_val_lbl.setStyleSheet("font-weight: bold; color: #3498db;")
        h_sens.addStretch()
        h_sens.addWidget(self.vad_val_lbl)
        le.addLayout(h_sens)
        
        self.vad_sl = QSlider(Qt.Horizontal); self.vad_sl.setRange(1, 100)
        self.vad_sl.valueChanged.connect(lambda v: self.vad_val_lbl.setText(str(v)))
        le.addWidget(self.vad_sl)
        
        lbl_sens_desc = QLabel("💡 說明：調大(更靈敏)更容易偵測微弱說話聲，但也更易錄入背景雜音；調小則只偵測大聲發話，適合吵雜環境。")
        lbl_sens_desc.setWordWrap(True)
        lbl_sens_desc.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        le.addWidget(lbl_sens_desc)
        
        le.addSpacing(10)
        
        # Silence Timeout Section
        h_sil = QHBoxLayout()
        h_sil.addWidget(QLabel("未發話安全超時防呆 (秒):"))
        self.sil_val_lbl = QLabel("5.0 秒")
        self.sil_val_lbl.setStyleSheet("font-weight: bold; color: #3498db;")
        h_sil.addStretch()
        h_sil.addWidget(self.sil_val_lbl)
        le.addLayout(h_sil)
        
        self.sil_sp = QSlider(Qt.Horizontal); self.sil_sp.setRange(1, 10)
        self.sil_sp.valueChanged.connect(lambda v: self.sil_val_lbl.setText(f"{float(v):.1f} 秒"))
        le.addWidget(self.sil_sp)
        
        lbl_sil_desc = QLabel("💡 說明：【僅開關模式有效】此設定僅在「開關模式」生效，用於防止忘記關閉錄音或人離開時產生無限錄製（防呆安全機制）。「對講機模式」下完全停用此機制，不受此設定影響，以避免影響正常的按鍵長按錄音。")
        lbl_sil_desc.setWordWrap(True)
        lbl_sil_desc.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        le.addWidget(lbl_sil_desc)
        
        le.addSpacing(10)
        self.chk_af = QCheckBox("啟用 AI 背景自動糾錯 (需 API)"); le.addWidget(self.chk_af)
        self.chk_con = QCheckBox("顯示監控視窗"); le.addWidget(self.chk_con)
        le.addStretch(); self.tabs.addTab(te, "🔧 工程")
        
        # Signals
        ws = [
            (self.chk_auto_start, "toggled"), (self.chk_smart_left, "toggled"), (self.chk_smart_right, "toggled"),
            (self.smart_hold_combo, "currentIndexChanged"), (self.rec_mode_cb, "currentIndexChanged"),
            (self.output_mode_cb, "currentIndexChanged"), (self.vis_style_cb, "currentIndexChanged"),
            (self.api_in, "textChanged"), (self.opt_m, "currentTextChanged"), (self.vis_m, "currentTextChanged"),
            (self.fix_m, "currentTextChanged"), (self.prof_cb, "currentIndexChanged"), (self.chk_con, "toggled"),
            (self.chk_af, "toggled"), (self.chk_use_punc, "toggled"), (self.eng_cb, "currentIndexChanged"),
            (self.sil_sp, "valueChanged"), (self.vad_sl, "valueChanged"), (self.chk_audio_cue, "toggled"),
            (self.sound_sel, "currentIndexChanged")
        ]
        for w, s in ws: getattr(w, s).connect(self._widget_changed)
        self.sound_sel.currentIndexChanged.connect(lambda i: self.preview_sound_requested.emit(i))

    def load_settings(self):
        defaults = {
            "hotkey": "ctrl+shift+win", "magic_hotkey": "alt+win", 
            "smart_left": True, "smart_right": True, "smart_hold_duration": 0.5, 
            "use_punc": True, "recording_mode": 0, "recording_style": 1, "sound_style_idx": 9,
            "opt_profiles": [{"name": "通用", "prompt": "請優化:"}], "show_console": True,
            "audio_cue": True, "vad_sensitivity": 50, "silence_timeout": 5.0, "auto_fix": False,
            "engine_version": "v2_stable",
            "magic_items": [
                {"id": "LEARN", "name": "📓 加入個人詞庫", "visible": True},
                {"id": "FIX", "name": "🪄 AI 個人化提示詞最佳化", "visible": True},
                {"id": "VISION", "name": "📸 擷取畫面並翻譯對照", "visible": True}
            ]
        }
        self.raw_config = defaults.copy()
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.raw_config.update(json.load(f))
            except: pass
        
        # Ensure default magic items exist
        its = self.raw_config.get("magic_items", [])
        bt = {"LEARN": "📓 加入個人詞庫", "FIX": "🪄 AI 個人化提示詞最佳化", "VISION": "📸 擷取畫面並翻譯對照"}
        for k, v in bt.items():
            if not any(x["id"] == k for x in its):
                its.insert(0, {"id": k, "name": v, "visible": True, "type": "internal", "val": ""})
        self.raw_config["magic_items"] = its
        
        self._apply_ui()

    def _apply_ui(self):
        self._loading = True
        c = self.raw_config
        self.btn_hk.setText(to_chinese_hk(c.get("hotkey", "ctrl+shift+win")))
        self.btn_mhk.setText(to_chinese_hk(c.get("magic_hotkey", "alt+win")))
        self.chk_auto_start.setChecked(c.get("auto_start", False))
        self.chk_smart_left.setChecked(c.get("smart_left", True))
        self.chk_smart_right.setChecked(c.get("smart_right", True))
        self.chk_use_punc.setChecked(c.get("use_punc", True))
        self.chk_con.setChecked(c.get("show_console", True))
        self.chk_audio_cue.setChecked(c.get("audio_cue", True))
        self.api_in.setText(c.get("gemini_api_key", ""))
        self.sound_sel.setCurrentIndex(c.get("sound_style_idx", 9))
        self.vis_style_cb.setCurrentIndex(c.get("recording_style", 1))
        dur = c.get("smart_hold_duration", 0.5)
        self.smart_hold_combo.setCurrentIndex({0.3:0, 0.5:1, 0.8:2, 1.0:3, 1.5:4}.get(dur, 1))
        self.output_mode_cb.setCurrentIndex(c.get("output_mode", 0))
        self.rec_mode_cb.setCurrentIndex(c.get("recording_mode", 0))
        
        # Engineering parameters
        ev = c.get("engine_version", "v2_stable")
        idx = 0
        if ev == "v1_legacy": idx = 1
        self.eng_cb.setCurrentIndex(idx)
        
        self.vad_sl.setValue(c.get("vad_sensitivity", 50))
        self.sil_sp.setValue(int(float(c.get("silence_timeout", 5.0))))
        self.chk_af.setChecked(c.get("auto_fix", False))
        
        # Load and populate model comboboxes from cache
        cache = c.get("model_cache", [])
        if cache:
            self.opt_m.clear()
            self.vis_m.clear()
            self.fix_m.clear()
            for x in cache:
                m_id = x.get("id") or f"models/{x['display']}"
                display = x["display"]
                self.opt_m.addItem(display, m_id)
                self.fix_m.addItem(display, m_id)
                if x.get("can_vision", True):
                    self.vis_m.addItem(display, m_id)
                    
        # Apply current model text
        self.opt_m.setCurrentText(c.get("opt_model", ""))
        self.vis_m.setCurrentText(c.get("vision_model", ""))
        self.fix_m.setCurrentText(c.get("fix_model", ""))
        
        self._upd_prof()
        self._upd_mag_ui()
        self._loading = False

    def _upd_prof(self):
        self.prof_cb.clear()
        for x in self.raw_config.get("opt_profiles", []):
            self.prof_cb.addItem(x["name"])
        self.prof_cb.setCurrentIndex(self.raw_config.get("active_profile_idx", 0))

    def _upd_mag_ui(self):
        self.lw_mag.clear()
        for i in self.raw_config.get("magic_items", []):
            mid = i["id"]
            is_sys = mid in ["LEARN", "FIX", "VISION"]
            li = QListWidgetItem()
            li.setData(Qt.UserRole, mid)
            self.lw_mag.addItem(li)
            w = MagicItemWidget(i["name"], i.get("visible", True), is_sys, self)
            li.setSizeHint(w.sizeHint())
            self.lw_mag.setItemWidget(li, w)
            w.vis_changed.connect(lambda v, m=mid: self._mag_vis(m, v))
            if not is_sys:
                w.del_req.connect(lambda m=mid: self._del_macro(m))
                w.edit_req.connect(lambda m=mid: self._ed_macro(m))

    def _mag_vis(self, m, v):
        for x in self.raw_config.get("magic_items", []):
            if x["id"] == m:
                x["visible"] = v
        self._widget_changed()

    def _add_macro(self): 
        d = MacroEditorDialog(parent=self)
        self.active_dialog = d
        if d.exec() == QDialog.Accepted:
            n, t, v = d.get_data()
            self.raw_config.setdefault("magic_items", []).append({
                "id": f"macro_{int(time.time())}", 
                "name": n, 
                "visible": True, 
                "type": t, 
                "val": v
            })
            self._upd_mag_ui()
            self._widget_changed()
        self.active_dialog = None

    def _ed_macro(self, m): 
        it = next(x for x in self.raw_config.get("magic_items", []) if x["id"] == m)
        d = MacroEditorDialog(it["name"], it.get("type", "text"), it.get("val", ""), self)
        self.active_dialog = d
        if d.exec() == QDialog.Accepted:
            n, t, v = d.get_data()
            it.update({"name": n, "type": t, "val": v})
            self._upd_mag_ui()
            self._widget_changed()
        self.active_dialog = None

    def _del_macro(self, m): 
        if QMessageBox.question(self, "確認", "確定要刪除此自定義按鈕嗎？") == QMessageBox.Yes:
            self.raw_config["magic_items"] = [x for x in self.raw_config.get("magic_items", []) if x["id"] != m]
            self._upd_mag_ui()
            self._widget_changed()

    def _reorder(self, *args): 
        if not self._loading:
            reordered = []
            for i in range(self.lw_mag.count()):
                mid = self.lw_mag.item(i).data(Qt.UserRole)
                item = next(x for x in self.raw_config.get("magic_items", []) if x["id"] == mid)
                reordered.append(item)
            self.raw_config["magic_items"] = reordered
            self._widget_changed()

    def set_auto_start(self, enabled: bool):
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "AI_Voice_Assistant"
            app_path = f'"{sys.executable}"' if hasattr(sys, '_MEIPASS') else f'"{os.path.join(os.getcwd(), "啟動語音助手.bat")}"'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled: 
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
        except: pass

    def handle_captured_input(self, k):
        if self.active_dialog and self.active_dialog.isVisible():
            if hasattr(self.active_dialog, 'update_captured'): 
                self.active_dialog.update_captured(k)
            if not isinstance(self.active_dialog, MacroEditorDialog): 
                self.stop_pairing_requested.emit()

    def _widget_changed(self, *args):
        if not self._loading:
            self.set_auto_start(self.chk_auto_start.isChecked())
            self._save_timer.start()

    def _do_save(self):
        try:
            ev_list = ["v2_stable", "v1_legacy"]
            upd = {
                "hotkey": self.raw_config.get("hotkey", "ctrl+shift+win"),
                "magic_hotkey": self.raw_config.get("magic_hotkey", "alt+win"),
                "gemini_api_key": self.api_in.text(),
                "opt_model": self.opt_m.currentText(),
                "vision_model": self.vis_m.currentText(),
                "fix_model": self.fix_m.currentText(),
                "smart_left": self.chk_smart_left.isChecked(),
                "smart_right": self.chk_smart_right.isChecked(),
                "smart_hold_duration": [0.3, 0.5, 0.8, 1.0, 1.5][self.smart_hold_combo.currentIndex()],
                "output_mode": self.output_mode_cb.currentIndex(),
                "recording_mode": self.rec_mode_cb.currentIndex(),
                "recording_style": self.vis_style_cb.currentIndex(),
                "sound_style_idx": self.sound_sel.currentIndex(),
                "use_punc": self.chk_use_punc.isChecked(),
                "show_console": self.chk_con.isChecked(),
                "audio_cue": self.chk_audio_cue.isChecked(),
                "active_profile_idx": self.prof_cb.currentIndex(),
                "engine_version": ev_list[self.eng_cb.currentIndex()] if self.eng_cb.currentIndex() < len(ev_list) else "v2_stable",
                "vad_sensitivity": self.vad_sl.value(),
                "silence_timeout": float(self.sil_sp.value()),
                "vad_buffer": float(self.sil_sp.value()),
                "auto_fix": self.chk_af.isChecked(),
                "auto_start": self.chk_auto_start.isChecked()
            }
            self.raw_config.update(upd)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.raw_config, f, indent=4)
            self.settings_changed.emit(self.raw_config)
        except Exception as e:
            logger.error(f"Save Error: {e}")

    def open_key_dialog(self, target):
        d = UnifiedKeyDialog(self.raw_config.get(target, ""), self)
        if d.exec() == QDialog.Accepted:
            self.raw_config[target] = d.result_hk
            self._apply_ui()
            self._widget_changed()

    def open_profile_manager(self):
        p = self.raw_config.get("opt_profiles", [])
        idx = self.raw_config.get("active_profile_idx", 0)
        d = ProfileManager(p, idx, self)
        if d.exec() == QDialog.Accepted:
            self.raw_config["opt_profiles"] = d.profiles
            self._upd_prof()
            self._widget_changed()

    def open_quick_add(self, text=""):
        if self.quick_add_dlg: self.quick_add_dlg.close(); self.quick_add_dlg.deleteLater()
        self.quick_add_dlg = QuickAddDialog(text, self)
        self.quick_add_dlg.add_req.connect(self.add_dict_requested.emit)
        self.quick_add_dlg.show()

    def open_dict_manager(self, initial_text=""):
        if self.dict_dlg: self.dict_dlg.close(); self.dict_dlg.deleteLater()
        self.dict_dlg = DictionaryManager(self.dict_items, self, initial_text)
        self.dict_dlg.add_req.connect(self.add_dict_requested.emit)
        self.dict_dlg.del_req.connect(self.del_dict_requested.emit)
        self.dict_dlg.closed_signal.connect(self._sync_dict_on_close)
        self.dict_dlg.show()

    def _sync_dict_on_close(self):
        self.dict_items = self.dict_dlg.all_items
        self.dict_items.sort(key=lambda x: x[1])
        self.import_dict_requested.emit(json.dumps(self.dict_items))

    def update_dict_list(self, i):
        self.dict_items = i
        if self.dict_dlg and self.dict_dlg.isVisible():
            self.dict_dlg.upd(i)

    def _check_models(self):
        self.btn_chk_models.setText("⏳ 查詢中...")
        self.btn_chk_models.setEnabled(False)
        threading.Thread(target=self._async_chk, daemon=True).start()

    def _async_chk(self):
        try:
            from src.utils.cloud_engine import GeminiCloudEngine
            e = GeminiCloudEngine(); e.configure(self.api_in.text().strip())
            m = e.get_available_models_with_capabilities()
            if m: 
                self.raw_config.update({"model_cache": m})
                self.models_scanned_signal.emit(m)
        except Exception as e:
            logger.error(f"Model Check Error: {e}")
        QTimer.singleShot(0, lambda: self.btn_chk_models.setText("🔍 查詢模型清單"))
        QTimer.singleShot(0, lambda: self.btn_chk_models.setEnabled(True))

    def _on_models_discovered(self, m_list):
        self.opt_m.clear()
        self.vis_m.clear()
        self.fix_m.clear()
        for x in m_list:
            m_id = x.get("id") or f"models/{x['display']}"
            display = x["display"]
            self.opt_m.addItem(display, m_id)
            self.fix_m.addItem(display, m_id)
            if x.get("can_vision", True):
                self.vis_m.addItem(display, m_id)
        self._widget_changed()

    def update_ui_coords(self, x, y):
        self.raw_config.update({"ui_x": x, "ui_y": y})
        self._widget_changed()
 

```

### 📄 `src/ui/settings_window_decompiled.py`
```python
# Source Generated with Decompyle++

# File: src.ui.settings_window_with_header.pyc (Python 3.11)



import os

import json

import sqlite3

import shutil

import sys

import threading

import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox, QDialog, QTabWidget, QCheckBox, QGridLayout, QListWidget, QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidgetItem, QFrame, QSlider, QAbstractItemView, QMenu

from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPoint

from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QAction

from loguru import logger

from src.utils.path_helper import get_writable_path

CONFIG_PATH = get_writable_path(os.path.join('user_data', 'gemini_tool_config.json'))

HW_CHINESE = {

    'mouse_back': '滑鼠側後退鍵',

    'mouse_forward': '滑鼠側前進鍵',

    'mouse_middle': '滑鼠中鍵',

    'ctrl': 'Ctrl',

    'shift': 'Shift',

    'alt': 'Alt',

    'win': 'Win鍵',

    'enter': 'Enter',

    'space': '空白鍵',

    'tab': 'Tab',

    'f10': 'F10',

    'f12': 'F12' }

MODIFIERS = [

    'ctrl',

    'shift',

    'alt',

    'win']



def to_chinese_hk(hk):

    if not hk:

        return '未設定'

    return (lambda .0: [ HW_CHINESE.get(p, p.upper()) for p in .0 ])(hk.lower().split('+')())





class UnifiedKeyDialog(QDialog):

    pass

# WARNING: Decompyle incomplete





class QuickAddDialog(QDialog):

    pass

# WARNING: Decompyle incomplete





class RefinementDialog(QDialog):

    pass

# WARNING: Decompyle incomplete





class DictionaryManager(QDialog):

    pass

# WARNING: Decompyle incomplete





class AppPickerDialog(QDialog):

    pass

# WARNING: Decompyle incomplete





class MacroEditorDialog(QDialog):

    pass

# WARNING: Decompyle incomplete





class MagicItemWidget(QWidget):

    pass

# WARNING: Decompyle incomplete





class ProfileManager(QDialog):

    pass

# WARNING: Decompyle incomplete





class SettingsWindow(QWidget):

    pass

# WARNING: Decompyle incomplete




```

### 📄 `src/ui/snip_overlay.py`
```python
# src/ui/snip_overlay.py
import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QGuiApplication

class SnipOverlay(QWidget):
    """
    [A232] Snip Overlay for Area Selection.
    - Darkens the screen.
    - Allows dragging a selection rectangle.
    - Emits the selected geometry.
    """
    snip_captured = Signal(QRect)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus # [A600] Do not steal focus to prevent OS "beep" sounds
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # [A600] Robust geometry for all screens
        geo = QRect()
        for screen in QGuiApplication.screens():
            geo = geo.united(screen.geometry())
        self.setGeometry(geo)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        
        # [A600] Ensure we have mouse tracking and are on top
        self.setMouseTracking(True)
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 1. Background darkness (semi-transparent black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        
        if self.is_selecting:
            # 2. Selection rectangle
            rect = QRect(self.begin, self.end).normalized()
            
            # 3. Clear the selection area (make it "see-through")
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # 4. Draw border around the clear area
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            rect = QRect(self.begin, self.end).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.snip_captured.emit(rect)
            self.close()
            self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            self.deleteLater()

def start_snipping():
    """ Helper to start the snipping process """
    overlay = SnipOverlay()
    overlay.show()
    return overlay

```

### 📄 `src/ui/vision_result_window.py`
```python
# src/ui/vision_result_window.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, 
    QPushButton, QHBoxLayout, QApplication, QWidget, QStatusBar, QCheckBox, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QGuiApplication
import pyperclip
from loguru import logger
import os

class AutoExpandingTextEdit(QTextEdit):
    """ [A340] Compact TextEdit that adjusts to content but allows scrolling. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setMinimumHeight(60) # Approx 2 lines
        self.document().contentsChanged.connect(self.update_height)
        self.setStyleSheet("background-color: #2c3e50; border: 1px solid #34495e; color: white; padding: 2px;")

    def update_height(self):
        # Dynamically adjust height up to a reasonable limit, then enable scroll
        doc_height = self.document().size().height()
        new_height = int(doc_height + 10)
        self.setFixedHeight(max(60, min(300, new_height)))

class VisionResultWindow(QDialog):
    """
    [A470] Ultra-Compact & Resizable Vision Tool.
    - Robust content parsing for immediate translation.
    - Cleaned up language list.
    """
    recapture_requested = Signal()
    target_lang_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📸 AI 截圖翻譯助手")
        self.resize(550, 400)
        self.keep_image = False; self.save_dir = ""; self._is_loading_config = False
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #1a252f; color: #ecf0f1; font-family: 'Microsoft JhengHei', 'Segoe UI'; font-size: 9pt; }
            QLabel { font-weight: bold; color: #3498db; }
            QComboBox { background: #2c3e50; color: #f1c40f; border: 1px solid #3498db; padding: 2px; font-weight: bold; }
            QPushButton#action_btn { background-color: #27ae60; color: white; border-radius: 3px; padding: 4px 10px; font-weight: bold; }
            QPushButton#copy_small { background-color: #34495e; color: #bdc3c7; border: 1px solid #3498db; padding: 1px 6px; font-size: 8pt; border-radius: 2px; }
            QStatusBar { color: #f1c40f; font-weight: bold; background: #16212d; font-size: 8pt; min-height: 22px; }
        """)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10, 10, 10, 5); self.main_layout.setSpacing(6)
        
        h_top = QHBoxLayout(); self.btn_recapture = QPushButton("📸 立即擷取螢幕並翻譯"); self.btn_recapture.setObjectName("action_btn"); self.btn_recapture.clicked.connect(self.recapture_requested.emit); h_top.addWidget(self.btn_recapture)
        self.chk_keep = QCheckBox("💾 保留截圖"); self.chk_keep.toggled.connect(self._toggle_keep_image); h_top.addStretch(); h_top.addWidget(self.chk_keep); self.main_layout.addLayout(h_top)
            
        h_u = QHBoxLayout(); h_u.addWidget(QLabel("📄 原始內容：")); h_u.addStretch(); btn_c1 = QPushButton("📋 複製"); btn_c1.setObjectName("copy_small"); btn_c1.clicked.connect(lambda: self._copy(self.orig_text.toPlainText())); h_u.addWidget(btn_c1); self.main_layout.addLayout(h_u)
        self.orig_text = AutoExpandingTextEdit(); self.main_layout.addWidget(self.orig_text)
        
        h_d = QHBoxLayout(); h_d.addWidget(QLabel("🌐 翻譯目標：")); self.lang_cb = QComboBox(); self.lang_cb.addItems(["繁體中文", "简体中文", "English", "日本語", "한국어", "Français", "Deutsch", "Español"]); self.lang_cb.currentTextChanged.connect(self._on_lang_changed); h_d.addWidget(self.lang_cb)
        h_d.addStretch(); btn_c2 = QPushButton("📋 複製翻譯"); btn_c2.setObjectName("copy_small"); btn_c2.clicked.connect(lambda: self._copy(self.res_text.toPlainText())); h_d.addWidget(btn_c2); self.main_layout.addLayout(h_d)
        
        self.res_text = AutoExpandingTextEdit(); self.res_text.setPlaceholderText("等待分析結果..."); self.res_text.setStyleSheet("background-color: #16212d; color: #f1c40f; border: 1px solid #f39c12; padding: 2px;"); self.main_layout.addWidget(self.res_text)
        
        self.status_bar = QStatusBar(); self.status_bar.setFixedHeight(22); self.status_bar.showMessage("就緒"); self.main_layout.addWidget(self.status_bar)

    def _on_lang_changed(self, lang):
        if not self._is_loading_config:
            self.target_lang_changed.emit(lang)
            if self.orig_text.toPlainText().strip(): self.status_bar.showMessage(f"⏳ 正在重新翻譯至 {lang}...", 3000)

    def set_target_lang(self, lang):
        self._is_loading_config = True; self.lang_cb.setCurrentText(lang); self._is_loading_config = False

    def clear_content(self):
        self.orig_text.clear(); self.res_text.clear(); self.status_bar.showMessage("已清空舊內容，就緒")

    def _toggle_keep_image(self, checked):
        if checked:
            d = QFileDialog.getExistingDirectory(self, "選擇截圖儲存位置")
            if d: self.save_dir = d; self.keep_image = True
            else: self.chk_keep.setChecked(False); self.keep_image = False
        else: self.keep_image = False; self.save_dir = ""

    def update_content(self, raw_text):
        """ [A470] Robust parsing for Original/Translated blocks """
        if not raw_text: return
        if "[ORIGINAL]" in raw_text and "[TRANSLATED]" in raw_text:
            parts = raw_text.split("[TRANSLATED]")
            o = parts[0].replace("[ORIGINAL]", "").strip(); t = parts[1].strip()
            self.orig_text.setPlainText(o); self.res_text.setPlainText(t)
        elif "[TRANSLATED]" in raw_text:
            parts = raw_text.split("[TRANSLATED]")
            self.orig_text.setPlainText(parts[0].strip()); self.res_text.setPlainText(parts[1].strip())
        else:
            self.orig_text.setPlainText("AI 未能標註原文，顯示原始回傳："); self.res_text.setPlainText(raw_text)
        self.status_bar.showMessage("✅ 翻譯已就緒", 3000)
        QTimer.singleShot(50, self.adjust_to_content)

    def adjust_to_content(self):
        hint_h = self.sizeHint().height(); self.resize(self.width(), hint_h)

    def _copy(self, text):
        if text:
            pyperclip.copy(text)
            self.status_bar.showMessage("📋 已成功複製到剪貼簿", 2000)
            
            # [A571] Button feedback
            btn = self.sender()
            if isinstance(btn, QPushButton):
                old_text = btn.text()
                btn.setText("✅ 已複製")
                btn.setEnabled(False)
                QTimer.singleShot(1000, lambda: (btn.setText(old_text), btn.setEnabled(True)))

    def show_at_center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                if not self.isVisible(): self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)
            self.show(); self.raise_(); self.activateWindow()
        except: self.show()

```

### 📄 `src/utils/__init__.py`
```python

```

### 📄 `src/utils/backup_manager.py`
```python
import os
import shutil
import time
from datetime import datetime
from loguru import logger

class BackupManager:
    """
    [A406] Automated Backup & Restore System.
    Ensures zero-loss development by creating snapshots before edits.
    """
    def __init__(self, root_dir=r"D:\AI VOICE", backup_dir=r"D:\AI VOICE\backups"):
        self.root_dir = root_dir
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_snapshot(self, label="Surgical_Fix"):
        """ Creates a full source backup (excluding venv and models) """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"Build_{label}_{timestamp}"
        target_path = os.path.join(self.backup_dir, folder_name)
        
        logger.info(f"💾 Creating system snapshot: {folder_name}...")
        
        # Define folders to include (Source only to keep it small/fast)
        to_backup = ['src', 'main.py', '啟動語音助手.bat', 'GEMINI.md']
        
        os.makedirs(target_path, exist_ok=True)
        for item in to_backup:
            src = os.path.join(self.root_dir, item)
            dst = os.path.join(target_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.exists(src):
                shutil.copy2(src, dst)
        
        logger.success(f"✅ Snapshot secured at: {target_path}")
        return target_path

    def restore_snapshot(self, folder_name):
        """ Restores a specific snapshot to the root directory """
        src_path = os.path.join(self.backup_dir, folder_name)
        if not os.path.exists(src_path):
            logger.error(f"❌ Restore failed: Snapshot {folder_name} not found.")
            return False
            
        logger.warning(f"⚠️ RESTORING SYSTEM TO: {folder_name}...")
        # Simple overwrite of source files
        for item in os.listdir(src_path):
            src = os.path.join(src_path, item)
            dst = os.path.join(self.root_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst): shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        logger.success("✅ System restoration complete.")
        return True

if __name__ == "__main__":
    # Create initial safety backup
    manager = BackupManager()
    manager.create_snapshot("A406_Stability_Base")

```

### 📄 `src/utils/cloud_engine.py`
```python
# src/utils/cloud_engine.py
import os
import time
import traceback
import requests
import json
import base64
from loguru import logger

os.environ["PYTHONIOENCODING"] = "utf-8"

class GeminiCloudEngine:
    """ [A575] Optimized Lazy-Import Engine """
    def __init__(self):
        self._api_key = ""
        self._model_name = "" 
        self._client = None
        self._initialized = False

    def _get_client(self):
        """ [A575] JIT Import of SDK """
        if self._client: return self._client
        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except Exception as e:
            logger.error(f"❌ [Cloud] SDK Import Failed: {e}")
            return None

    def configure(self, api_key: str, model_name: str = ""):
        if not api_key or len(api_key.strip()) < 5:
            self._initialized = False; self._api_key = ""
            return
        
        try:
            clean_key = "".join(api_key.split())
            self._api_key = "".join(c for c in clean_key if 32 < ord(c) < 127)
            
            if model_name:
                self._model_name = model_name.replace("models/", "")
            
            # [A575] Verify client availability
            if self._get_client():
                self._initialized = True
                logger.success(f"CloudEngine [A515/A575] JIT Ready: {self._model_name}")
            else:
                self._initialized = False
        except Exception as e:
            self._initialized = False
            logger.error(f"CloudEngine Initialization Error: {e}")

    def verify_model(self, model_id: str) -> tuple[bool, bool]:
        """ [A525] Verify if model is usable and if it supports vision """
        client = self._get_client()
        if not client: return False, False
        try:
            from google.genai import types
            # Quick check: Send a minimal prompt
            is_gemini = "gemini" in model_id.lower()
            
            # 1. Usability Check (Text)
            try:
                config = types.GenerateContentConfig(max_output_tokens=1, temperature=0.0)
                res = client.models.generate_content(model=model_id, contents="ping", config=config)
                if not res or not hasattr(res, 'text'): return False, False
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower(): return False, False
                return False, False

            can_vision = is_gemini and any(kw in model_id.lower() for kw in ["flash", "pro", "ultra", "vision", "multimodal"])
            return True, can_vision
        except:
            return False, False

    def get_available_models_with_capabilities(self) -> list[dict]:
        """ [A525] Parallel Verification - No Hardcoded Names """
        if not self._api_key: return []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200: return []
            
            data = response.json()
            raw_list = data.get('models', [])
            
            # Step 1: Filter potential candidates
            candidates = []
            for m in raw_list:
                m_name = m.get('name', "")
                m_id = m_name.replace("models/", "")
                if any(kw in m_id.lower() for kw in ["embedding", "aqa", "classifier", "ranker"]): continue
                if "generateContent" in m.get('supportedGenerationMethods', []):
                    candidates.append(m_id)
            
            # Step 2: Parallel Verification
            from concurrent.futures import ThreadPoolExecutor
            verified_results = []
            
            def check(mid):
                ok, vision = self.verify_model(mid)
                if ok:
                    return {"id": f"models/{mid}", "display": mid, "can_vision": vision}
                return None

            logger.info(f"🚀 [A525] Verifying {len(candidates)} models in parallel...")
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(check, candidates))
            
            verified_results = [r for r in results if r]
            verified_results.sort(key=lambda x: (not x['display'].startswith('gemini'), x['display']))
            
            return verified_results
        except Exception as e:
            logger.error(f"❌ [A525] Discovery Fatal: {e}")
            return []

    def is_ready(self) -> tuple[bool, str]:
        if not self._api_key: return False, "尚未設定 API Key"
        if not self._initialized: return False, "引擎初始化失敗"
        return True, ""

    def process_text(self, user_text: str, system_prompt: str = "", model_override: str = None) -> str:
        if not self._initialized: return "❌ 尚未設定 API Key。"
        # [A515] Remove 'models/' prefix for SDK compatibility to avoid 404
        target_model = model_override if model_override else self._model_name
        if not target_model: return "❌ 錯誤：尚未選擇模型！"
        
        model_id = target_model.replace("models/", "")
        
        client = self._get_client()
        if not client: return "❌ 引擎初始化失敗。"

        try:
            from google.genai import types
            safe_text = str(user_text).encode('utf-8', 'ignore').decode('utf-8')
            safe_system = str(system_prompt).encode('utf-8', 'ignore').decode('utf-8')
            config = types.GenerateContentConfig(system_instruction=safe_system, temperature=0.3, top_p=0.95)
            
            for attempt in range(3):
                try:
                    response = client.models.generate_content(model=model_id, contents=safe_text, config=config)
                    if response and response.text: return response.text
                    return "❌ AI 未能生成內容。"
                except Exception as e:
                    last_err = str(e)
                    if any(x in last_err for x in ["503", "500", "overloaded"]):
                        time.sleep(2 * (attempt + 1)); continue
                    logger.error(f"❌ [A515] Text AI Error: {e}")
                    return f"❌ 系統錯誤: {last_err}"
        except Exception as e:
            return f"❌ 系統異常: {e}"
        return "❌ 系統錯誤 (重試失敗)"

    def process_vision(self, image_path: str, target_lang: str = "繁體中文", model_override: str = None) -> str:
        if not self._initialized or not self._api_key: return f"❌ 尚未設定 API Key。"
        if not os.path.exists(image_path): return f"❌ 找不到截圖檔案。"
        try:
            target_model = model_override if model_override else self._model_name
            if not target_model.startswith("models/"): target_model = f"models/{target_model}"
            
            with open(image_path, "rb") as f: img_data = f.read()
            encoded_image = base64.b64encode(img_data).decode('utf-8')
            url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={self._api_key}"
            
            # [A460] Highly explicit prompt for immediate extraction and translation
            prompt = (
                f"1. Extract all text from the image.\n"
                f"2. Translate the extracted text into {target_lang}.\n"
                f"Format your response EXACTLY like this:\n"
                f"[ORIGINAL]\n(Text here)\n"
                f"[TRANSLATED]\n(Translated text here)"
            )
            
            payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": encoded_image}}]}], "generationConfig": {"temperature": 0.1}}
            response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=45)
            if response.status_code == 200:
                res_data = response.json()
                return res_data['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                return f"❌ API 配額超限 (429): 免費流量已用完。目標語言: {target_lang}"
            return f"❌ 雲端 API 錯誤 ({response.status_code})"
        except Exception as e: return f"❌ 視覺系統異常: {str(e)}"

    def translate_text(self, text: str, target_lang: str = "繁體中文") -> str:
        if not self._initialized: return "❌ 引擎未就緒"
        try:
            prompt = f"Please translate the following text into {target_lang}. Strictly return ONLY the translated text."
            res = self.process_text(user_text=text, system_prompt=prompt)
            if res.startswith("❌"): return res
            return f"[ORIGINAL]\n{text}\n[TRANSLATED]\n{res}"
        except Exception as e: return f"❌ 翻譯失敗: {e}"

```

### 📄 `src/utils/hotkey_manager.py`
```python
# src/utils/hotkey_manager.py
from PySide6.QtCore import QObject, Signal
from pynput import keyboard, mouse
from loguru import logger
import threading
import time

class HotkeyManager(QObject):
    """
    Build [A446] Unified Input Sensor.
    - SOLE owner of the mouse listener to prevent hook conflicts.
    - Forwards events to SmartTrigger logic.
    """
    start_recording_signal = Signal()
    stop_recording_signal = Signal() # [A563] Added for keyboard PTT
    magic_menu_signal = Signal()
    input_captured_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._active_keys = set()
        self._target_keys = set()
        self._magic_keys = set()
        self._cooldown = 0.3
        self._last_trigger_time = 0
        self._is_pressed = False
        self._lock = threading.Lock()
        
        self.learning_mode = False
        self.mouse_listener = None
        self.kb_listener = None
        self.smart_trigger = None # [A446] Will be injected by controller
        self.controller = None
        
        self._recording_mode = 0
        self._hold_duration_ms = 500
        self._hotkey_timer_active = False
        self._hotkey_timer = None

    def initialize(self, hotkey_str, magic_hotkey_str, cooldown=0.3, smart_trigger=None):
        self._cooldown = cooldown
        self._target_keys = self._parse_keys(hotkey_str)
        self._magic_keys = self._parse_keys(magic_hotkey_str)
        self.smart_trigger = smart_trigger
        
        logger.warning(f"Engine A446: V:{hotkey_str} M:{magic_hotkey_str} CD:{cooldown}")
        self._start_listeners()
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _parse_keys(self, s):
        if not s: return set()
        return set(s.lower().split('+'))

    def _start_listeners(self):
        if self.kb_listener: self.kb_listener.stop()
        if self.mouse_listener: self.mouse_listener.stop()

        self.kb_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.kb_listener.start()
        
        # [A446] Single Mouse Listener for both Hotkeys and Smart Trigger
        self.mouse_listener = mouse.Listener(on_click=self._on_click, on_move=self._on_move)
        self.mouse_listener.start()

    def set_learning_mode(self, enabled: bool):
        self.learning_mode = enabled
        if enabled:
            logger.info("HotkeyManager: Raw VK Pairing ACTIVE.")
            self._active_keys.clear()

    def _watchdog(self):
        while True:
            time.sleep(2.0)
            if self._active_keys and (time.time() - self._last_trigger_time > 2.0):
                with self._lock:
                    self._active_keys.clear()
                    self._is_pressed = False

    def _on_move(self, x, y):
        if self.smart_trigger:
            self.smart_trigger.handle_move(x, y)

    def _on_click(self, x, y, button, pressed):
        # 1. Forward to SmartTrigger logic (handles holds)
        if self.smart_trigger:
            self.smart_trigger.handle_click(x, y, button, pressed)

        # 2. Handle simple side-button clicks
        if not pressed: return
        btn_name = str(button).lower()
        
        clean_name = btn_name
        if "button.x1" in btn_name: clean_name = "mouse_back"
        elif "button.x2" in btn_name: clean_name = "mouse_forward"
        elif "button.left" in btn_name: clean_name = "mouse_left"
        elif "button.right" in btn_name: clean_name = "mouse_right"
        elif "button.middle" in btn_name: clean_name = "mouse_middle"
        else:
            clean_name = btn_name.replace("button.", "mouse_")

        if self.learning_mode:
            if clean_name in ["mouse_left", "mouse_right"]: return
            logger.success(f"Captured Mouse Event: {clean_name}")
            self.input_captured_signal.emit(clean_name)
            return

        self._check_mouse_trigger(clean_name)

    def _check_mouse_trigger(self, trigger_name):
        now = time.time()
        if now - self._last_trigger_time < self._cooldown: return
        
        if trigger_name in self._target_keys and len(self._target_keys) == 1:
            self._last_trigger_time = now
            self.start_recording_signal.emit()
        elif trigger_name in self._magic_keys and len(self._magic_keys) == 1:
            self._last_trigger_time = now
            self.magic_menu_signal.emit()

    def _on_press(self, key):
        """ [A164/A168] Capture RAW VK and ASCII Control Chars """
        try:
            k = ""
            if hasattr(key, 'char') and key.char:
                if ord(key.char) < 32: k = chr(ord(key.char) + 96)
                else: k = key.char.lower()
            elif hasattr(key, 'name'): k = key.name.lower()
            if not k:
                if hasattr(key, 'vk'): k = f"vk:{key.vk}"
                else: k = str(key).lower().replace("key.", "").replace("<", "").replace(">", "")

            if not k or k == "none": return
            if k.startswith('ctrl'): k = 'ctrl'
            if k.startswith('shift'): k = 'shift'
            if k.startswith('alt'): k = 'alt'
            if k == 'cmd': k = 'win'
            if k in ['media_back', 'browser_back']: k = 'mouse_back'
            if k in ['media_forward', 'browser_forward']: k = 'mouse_forward'
            
            with self._lock:
                self._active_keys.add(k)
                if self.learning_mode:
                    # [A490] Don't emit yet, wait for release to get full combo
                    return
                self._check_triggers()
        except: pass

    def _on_release(self, key):
        try:
            k = ""
            if hasattr(key, 'char') and key.char:
                if ord(key.char) < 32: k = chr(ord(key.char) + 96)
                else: k = key.char.lower()
            elif hasattr(key, 'name'): k = key.name.lower()
            if not k and hasattr(key, 'vk'): k = f"vk:{key.vk}"
            if not k: return

            if k.startswith('ctrl'): k = 'ctrl'
            if k.startswith('shift'): k = 'shift'
            if k.startswith('alt'): k = 'alt'
            if k == 'cmd': k = 'win'
            if k in ['media_back', 'browser_back']: k = 'mouse_back'
            if k in ['media_forward', 'browser_forward']: k = 'mouse_forward'
            
            with self._lock:
                if self.learning_mode and self._active_keys:
                    # [A490] Capture full combo on release
                    combo = "+".join(sorted(list(self._active_keys)))
                    logger.success(f"Captured Combo: {combo}")
                    self.input_captured_signal.emit(combo)
                    self._active_keys.clear()
                    return

                if k in self._active_keys: self._active_keys.remove(k)
                
                # [A563] PTT Stop Detection / Toggle Cancel Detection
                if self._recording_mode == 0:
                    if self._is_pressed and not self._target_keys.issubset(self._active_keys):
                         logger.info("🎯 [INPUT] Hotkey Released -> Stop recording")
                         self._is_pressed = False
                         self.stop_recording_signal.emit()
                else:
                    if not self._target_keys.issubset(self._active_keys):
                        if self._hotkey_timer_active:
                            self._cancel_hotkey_timer()
                            self._hotkey_timer_active = False
        except: pass

    def _check_triggers(self):
        if self.learning_mode: return
        now = time.time()

        # [A559] Robust Subset Check: Ensure all target keys are in active set
        if self._target_keys and self._target_keys.issubset(self._active_keys):
            if self._recording_mode == 0:
                if now - self._last_trigger_time < self._cooldown: return
                if not self._is_pressed:
                    logger.info(f"🎯 [INPUT] Trigger Detected: {'+'.join(self._target_keys)}")
                    self._is_pressed = True
                    self._last_trigger_time = now
                    self.start_recording_signal.emit()
            else:
                if not self._hotkey_timer_active:
                    self._hotkey_timer_active = True
                    self._hotkey_timer = threading.Timer(self._hold_duration_ms / 1000.0, self._evaluate_hotkey_toggle)
                    self._hotkey_timer.daemon = True
                    self._hotkey_timer.start()
            return

        if self._magic_keys and self._magic_keys.issubset(self._active_keys):
            if now - self._last_trigger_time < self._cooldown: return
            if not self._is_pressed:
                logger.info(f"🎯 [INPUT] Magic Menu Triggered: {'+'.join(self._magic_keys)}")
                self._is_pressed = True
                self._last_trigger_time = now
                self.magic_menu_signal.emit()
            return

    def _evaluate_hotkey_toggle(self):
        with self._lock:
            if self._target_keys and self._target_keys.issubset(self._active_keys):
                is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_pressed
                if is_rec:
                    logger.info("🎯 [INPUT] Hotkey Long-Press -> Toggle Stop recording")
                    self._is_pressed = False
                    self.stop_recording_signal.emit()
                else:
                    logger.info("🎯 [INPUT] Hotkey Long-Press -> Toggle Start recording")
                    self._is_pressed = True
                    self.start_recording_signal.emit()

    def _cancel_hotkey_timer(self):
        if self._hotkey_timer:
            try: self._hotkey_timer.cancel()
            except: pass
            self._hotkey_timer = None

    def update_config(self, hold_duration_s: float, mode: int):
        with self._lock:
            self._hold_duration_ms = int(hold_duration_s * 1000)
            self._recording_mode = mode
            self._cancel_hotkey_timer()
            self._hotkey_timer_active = False
            logger.info(f"HotkeyManager Config: mode={mode}, duration={hold_duration_s}s")

    def update_hotkey(self, hotkey_str):
        self._target_keys = self._parse_keys(hotkey_str)
        
    def update_magic_hotkey(self, magic_hotkey_str):
        self._magic_keys = self._parse_keys(magic_hotkey_str)

```

### 📄 `src/utils/input_mode_manager.py`
```python
# src/utils/input_mode_manager.py
from enum import Enum
from loguru import logger

class InputMode(Enum):
    STANDARD = "standard"  # Hold/Press to record, release to output
    STREAMING = "streaming"  # VAD + Real-time output

class InputModeManager:
    """
    Manages the current input mode and associated settings.
    Build [A84]: Support for modular Free/Pro tiering.
    """
    def __init__(self, config=None):
        self.config = config or {}
        # Default to STANDARD for stability
        mode_str = self.config.get("input_mode", "standard")
        self.current_mode = InputMode(mode_str)
        
        # Streaming/VAD parameters
        self.vad_threshold = self.config.get("vad_threshold", 0.5)
        self.vad_silence_ms = self.config.get("vad_silence_ms", 1000) # User requested 1s
        self.streaming_interval_s = self.config.get("streaming_interval_s", 1.0) # 1s chunk as requested

    def set_mode(self, mode: InputMode):
        logger.info(f"Switching input mode to: {mode.value}")
        self.current_mode = mode
        self.config["input_mode"] = mode.value

    def is_streaming(self):
        return self.current_mode == InputMode.STREAMING

    def get_config(self):
        return self.config

```

### 📄 `src/utils/learning_engine.py`
```python
import sqlite3
import os
import sys
import threading
import time
from loguru import logger
from src.utils.path_helper import get_writable_path # [A670]

# [A670/A555] DEFINITIVE Locked Path for Database
def get_locked_db_path():
    try:
        import __main__
        if hasattr(sys, '_MEIPASS'): base = os.path.dirname(sys.executable)
        elif hasattr(__main__, "__file__"): base = os.path.dirname(os.path.abspath(__main__.__file__))
        else: base = os.getcwd()
        target = os.path.join(base, "user_data", "user_learning.db")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        return target
    except: return os.path.join(os.getcwd(), "user_data", "user_learning.db")

DB_PATH = get_locked_db_path()

class LearningEngine:
    """ [A670/A555] Production Ready Database Engine with Hardened Migration """
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = []
        self._initialize_db()
        self.refresh_cache()

    def _initialize_db(self):
        """ [A555] Final Scavenger Migration Logic """
        try:
            # 1. Candidate old paths
            root = os.path.dirname(os.path.dirname(DB_PATH))
            candidates = [
                os.path.join(root, "user_learning.db"), # Old root
                os.path.join(os.getcwd(), "user_learning.db"), # Possible CWD root
                os.path.join(os.path.dirname(DB_PATH), "user_learning.db") # Current data folder
            ]
            
            # 2. Perform Migration if needed
            if not os.path.exists(DB_PATH):
                import shutil
                for old in candidates:
                    if os.path.exists(old) and old != DB_PATH:
                        try:
                            shutil.copy(old, DB_PATH)
                            logger.success(f"📦 [A555] DATA RECOVERED: Migrated legacy dictionary from {old}")
                            # Rename old one to prevent repeat
                            os.rename(old, old + ".migrated")
                            break
                        except Exception as e:
                            logger.warning(f"⚠️ [A555] Migration failed for {old}: {e}")
            
            # 3. Standard Init
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS habits (
                        original TEXT PRIMARY KEY,
                        corrected TEXT,
                        hit_count INTEGER DEFAULT 1
                    )
                ''')
                conn.commit()
                conn.close()
            logger.info(f"Production Audit: Database secured at {DB_PATH}")
        except Exception as e:
            logger.error(f"DB Init Error: {e}")

    def refresh_cache(self):
        try:
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT original, corrected FROM habits")
                self._cache = cursor.fetchall()
                conn.close()
        except: pass

    def apply_habits(self, text):
        if not text: return text
        final_text = text
        # Fast memory-based correction
        for orig, corr in self._cache:
            if orig in final_text:
                final_text = final_text.replace(orig, corr)
        return final_text

    def add_habit_manual(self, orig, corr):
        if not orig or not corr: return False
        try:
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO habits (original, corrected) VALUES (?, ?)", (orig, corr))
                conn.commit()
                conn.close()
            self.refresh_cache()
            return True
        except Exception as e:
            logger.error(f"Add Habit Error: {e}")
            return False

    def delete_habit(self, orig):
        try:
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM habits WHERE original = ?", (orig,))
                conn.commit()
                conn.close()
            self.refresh_cache()
            return True
        except: return False

    def list_all(self):
        return self._cache

    def clear_dictionary(self):
        try:
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM habits")
                conn.commit()
                conn.close()
            self._cache = []
            return True
        except: return False

    def export_to_csv(self, file_path):
        """ [A474] Export dictionary to CSV for backup """
        try:
            import csv
            items = self.list_all()
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Original', 'Correction'])
                for orig, corr in items:
                    writer.writerow([orig, corr])
            return True
        except Exception as e:
            logger.error(f"Export Error: {e}")
            return False

    def import_from_csv(self, file_path):
        """ [A474] Import dictionary from CSV """
        try:
            import csv
            count = 0
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    orig = row.get('Original', '').strip()
                    corr = row.get('Correction', '').strip()
                    if orig and corr:
                        self.add_habit_manual(orig, corr)
                        count += 1
            return True, count
        except Exception as e:
            logger.error(f"Import Error: {e}")
            return False, 0

```

### 📄 `src/utils/module_loader.py`
```python
# src/utils/module_loader.py
import os
import sys
import importlib.util
from loguru import logger
from src.utils.path_helper import get_resource_path # [A670]

class ModuleLoader:
    """ [A670] Dynamic Component Loader with EXE support """
    
    @staticmethod
    def _probe_path(relative_path):
        """ [A1000] Resilient path probing for frozen environments """
        candidates = []
        meipass = getattr(sys, '_MEIPASS', 'NOT_SET')
        exe_dir = os.path.dirname(sys.executable)
        cwd = os.getcwd()
        
        logger.debug(f"🔍 Probing for: {relative_path}")
        logger.debug(f"🔍 System Context: MEIPASS={meipass}, EXE_DIR={exe_dir}, CWD={cwd}")
        logger.debug(f"🔍 sys.path[0-2]: {sys.path[:3]}")

        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, relative_path))
            candidates.append(os.path.join(sys._MEIPASS, "_internal", relative_path))
            candidates.append(os.path.join(exe_dir, relative_path))
            candidates.append(os.path.join(exe_dir, "_internal", relative_path))
        else:
            candidates.append(os.path.join(cwd, relative_path))
            
        for p in candidates:
            exists = os.path.exists(p)
            logger.debug(f"   - Checking: {p} [{'FOUND' if exists else 'MISSING'}]")
            if exists:
                return p
        return None

    @staticmethod
    def load_engine(engine_version: str):
        try:
            import traceback
            logger.info(f"Loader Audit: Requesting engine version '{engine_version}'")
            if not engine_version:
                logger.error("Loader Error: engine_version is empty!")
                return None
                
            rel_path = os.path.join("src", "audio", "engines", f"engine_{engine_version}.py")
            file_path = ModuleLoader._probe_path(rel_path)
            
            if not file_path:
                logger.error(f"Loader Error: Engine file not found after probing: {rel_path}")
                return None
                
            logger.info(f"Loader Audit: Loading engine from {file_path}")
            spec = importlib.util.spec_from_file_location(f"engine_{engine_version}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Map version string to class name
            class_map = {
                "v2_stable": "EngineV2Stable",
                "v1_legacy": "EngineV1Legacy"
            }
            class_name = class_map.get(engine_version, "EngineV2Stable")
            
            # [A379] VERBOSE LOAD TRACEBACK
            try:
                instance = getattr(module, class_name)()
                return instance
            except Exception as e:
                logger.critical(f"CRITICAL: Engine Instance Creation Failed!\n{traceback.format_exc()}")
                return None
                
        except Exception as e:
            import traceback
            logger.error(f"Engine Load Failed Traceback:\n{traceback.format_exc()}")
            return None

    @staticmethod
    def load_output_plugin(plugin_version: str):
        try:
            rel_path = os.path.join("src", "utils", "output_plugins", f"plugin_{plugin_version}.py")
            file_path = ModuleLoader._probe_path(rel_path)
            
            if not file_path: return None
                
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_version}", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            class_name = "OutputPlugin"
            return getattr(module, class_name)()
        except Exception as e:
            logger.error(f"Plugin Load Failed: {e}")
            return None

```

### 📄 `src/utils/output_plugins/__init__.py`
```python
# package

```

### 📄 `src/utils/output_plugins/plugin_v1_instant.py`
```python
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
                pyperclip.copy(text)
                time.sleep(0.002) # Very minimal sleep to let clipboard sync
                user32.keybd_event(0x11, 0x1D, 0, 0) # Ctrl down
                user32.keybd_event(0x56, 0x2F, 0, 0) # V down
                time.sleep(0.01)
                user32.keybd_event(0x56, 0x2F, 2, 0) # V up
                user32.keybd_event(0x11, 0x1D, 2, 0) # Ctrl up
            else:
                keyboard.write(text, delay=0.0)
        except Exception as e: 
            logger.error(f"Output error: {e}")
            keyboard.write(text, delay=0.0)
        finally:
            # Restore modifier keys if they were physically held down
            for vk in released:
                sc = vk_sc.get(vk, 0)
                user32.keybd_event(vk, sc, 0, 0) # KEYEVENTF_KEYDOWN

```

### 📄 `src/utils/output_plugins/plugin_v2_typing.py`
```python
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

```

### 📄 `src/utils/path_helper.py`
```python
# src/utils/path_helper.py
import os
import sys
from loguru import logger

def get_resource_path(relative_path):
    """
    [A1000] Universal Resource Resolver.
    For internal files bundled INSIDE the EXE.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()
    
    return os.path.join(base_path, relative_path)

def get_external_resource(relative_path):
    """
    [A1000/A567] External Resource Resolver with ASCII Root Bridge.
    Sentencepiece/C++ legacy libs fail with non-ASCII paths (Error #42).
    This creates a root-level ASCII junction to bypass encoding issues.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.getcwd()
        
    long_path = os.path.abspath(os.path.join(base_path, relative_path))
    
    # If path is already pure ASCII, return as is
    if all(ord(c) < 128 for c in long_path):
        return long_path

    # [A567] ROOT BRIDGE: Gold standard for non-ASCII path survival
    if sys.platform == 'win32':
        return get_root_ascii_bridge(long_path)
    
    return long_path

def get_root_ascii_bridge(long_path):
    """
    [A567/A568/A570] Creates a junction at the root of a drive (e.g. C:\.aiv_bridge)
    Junctions are ASCII-safe and bypass Chinese characters in the middle of paths.
    """
    import subprocess
    import shutil
    import hashlib
    
    # [A570] Detect if drive is C: or other
    drive = os.path.splitdrive(long_path)[0] or "C:"
    
    # List of potential bridge roots to try
    # C:\ is best, but if drive D: is where the app is, D:\.aiv_bridge is also ASCII-safe!
    roots_to_try = ["C:\\.aiv_bridge", os.path.join(drive, "\\.aiv_bridge")]
    
    path_hash = hashlib.md5(long_path.encode('utf-8')).hexdigest()[:8]
    safe_name = f"link_{path_hash}"

    for bridge_root in roots_to_try:
        try:
            if not os.path.exists(bridge_root):
                os.makedirs(bridge_root, exist_ok=True)
            
            bridge_path = os.path.join(bridge_root, safe_name)
            
            # [A570] Use lexists to detect even broken junctions/links
            if os.path.lexists(bridge_path):
                # If it's a junction/directory, we assume it's valid for this hash
                # (since hash is unique to the long_path)
                return bridge_path
            
            # Attempt to create junction
            cmd = f'cmd /c mklink /J "{bridge_path}" "{long_path}"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if res.returncode == 0:
                logger.success(f"🌉 [A570] Bridge Success: {bridge_path} -> {long_path}")
                return bridge_path
            elif "當檔案已存在時" in res.stderr or "already exists" in res.stderr.lower():
                # [A570] If mklink complains it exists but lexists missed it (rare),
                # try one aggressive wipe and re-link.
                subprocess.run(f'cmd /c rmdir "{bridge_path}"', shell=True)
                res2 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res2.returncode == 0:
                    return bridge_path
                    
        except Exception as e:
            logger.warning(f"🌉 [A570] Bridge Root {bridge_root} failed: {e}")
            continue

    # Final fallback to 8.3 short path if all bridges fail
    logger.error("🌉 [A570] All Root Bridges failed. Falling back to 8.3 short path.")
    return get_win32_short_path(long_path)

def get_win32_short_path(long_path):
    """
    [A566] Uses Win32 API to get the 8.3 short path name.
    This is the gold standard for bypassing non-ASCII path issues in legacy C++ libs.
    """
    import ctypes
    from ctypes import wintypes
    
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    
    # First call to get required buffer size
    output_buf_size = 0
    output_buf_size = _GetShortPathNameW(long_path, None, 0)
    if output_buf_size == 0:
        logger.error(f"❌ [A566] Failed to get short path for: {long_path}")
        return long_path
        
    output_buf = ctypes.create_unicode_buffer(output_buf_size)
    _GetShortPathNameW(long_path, output_buf, output_buf_size)
    short_path = output_buf.value
    logger.info(f"🌉 [A566] Path Bridge (8.3): {long_path} -> {short_path}")
    return short_path

def get_ascii_bridge_path(long_path):
    # Deprecated in favor of get_win32_short_path [A566]
    return get_win32_short_path(long_path)

def get_writable_path(relative_path):
    """
    [A670/A554] Persistent Data Resolver.
    Ensures user data lives next to the EXE or main script, not in CWD.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(sys.executable)
    else:
        # [A554] Get the directory of the main entry point to be absolute
        import __main__
        if hasattr(__main__, "__file__"):
            base_path = os.path.dirname(os.path.abspath(__main__.__file__))
        else:
            base_path = os.getcwd()
        
    target = os.path.join(base_path, relative_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return target

def initialize_universal_environment():
    """
    [A1000] Global environment setup to be called at main start.
    """
    try:
        # Register embedded bin folder to system PATH immediately
        if hasattr(sys, '_MEIPASS'):
            bin_dir = os.path.join(sys._MEIPASS, "bin")
            if os.path.exists(bin_dir):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
                logger.success(f"🛡️ [A1000] Iron-Clad Binaries Locked: {bin_dir}")
                
        # Silence FFmpeg warnings by explicitly setting paths for pydub
        from pydub import AudioSegment
        ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        
        # Check dev vs prod path
        dev_ffmpeg = os.path.join(os.getcwd(), "bin", ffmpeg_name)
        prod_ffmpeg = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "bin", ffmpeg_name)
        
        if os.path.exists(prod_ffmpeg):
            AudioSegment.converter = prod_ffmpeg
        elif os.path.exists(dev_ffmpeg):
            AudioSegment.converter = dev_ffmpeg
            
    except Exception as e:
        logger.warning(f"Environment initialization warning: {e}")

```

### 📄 `src/utils/screenshot_tool.py`
```python
# src/utils/screenshot_tool.py
import os
import time
from PIL import Image
from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QScreen

class ScreenshotTool:
    """
    [A256] DPI-Aware Screenshot Tool.
    - Uses logical-to-physical mapping for high-res screens.
    - Forced directory verification.
    """
    @staticmethod
    def capture_fullscreen(save_path="user_data/temp_snip.png"):
        try:
            full_path = os.path.abspath(save_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            screen = QGuiApplication.primaryScreen()
            if not screen: return None
            
            pixmap = screen.grabWindow(0)
            pixmap.save(full_path, "PNG")
            logger.info(f"Fullscreen saved to: {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Fullscreen failed: {e}")
            return None

    @staticmethod
    def capture_area(rect, save_path="user_data/temp_snip.png"):
        """
        Captures a specific QRect area with DPI awareness.
        """
        try:
            full_path = os.path.abspath(save_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            screen = QGuiApplication.primaryScreen()
            if not screen: return None
            
            # [A256] Handle High-DPI scaling
            # Qt's grabWindow on Windows expects logical coordinates, 
            # but sometimes there's an offset if virtual desktop isn't starting at (0,0).
            dpr = screen.devicePixelRatio()
            logger.info(f"Capture Area: {rect.x()},{rect.y()} {rect.width()}x{rect.height()} (DPR: {dpr})")
            
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            
            if pixmap.isNull():
                logger.error("GrabWindow returned a null pixmap.")
                return None
                
            success = pixmap.save(full_path, "PNG")
            if success:
                logger.info(f"Area saved to: {full_path}")
                return full_path
            else:
                logger.error(f"Failed to save pixmap to {full_path}")
                return None
        except Exception as e:
            logger.error(f"Area capture failed: {e}")
            return None

```

### 📄 `src/utils/smart_trigger.py`
```python
# src/utils/smart_trigger.py
import time, threading, ctypes, pyperclip, keyboard, pyautogui
from ctypes import wintypes
from pynput import mouse
from loguru import logger
from PySide6.QtCore import QObject, Signal

class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT)
    ]

user32 = ctypes.windll.user32
IDC_IBEAM = 32513

class SmartTrigger(QObject):
    """
    Build [A636] ROBUST CORE TRIGGER & CAPTURE.
    - [REPRODUCTION_GUARD] Mouse Move Threshold (5px) implemented.
    - Background capture with physical state verification.
    """
    voice_start_signal = Signal(); voice_stop_signal = Signal()
    magic_signal = Signal(str); click_signal = Signal(int, int)

    def __init__(self):
        super().__init__()
        self._left_enabled = True; self._right_enabled = True; self._recording_mode = 0
        self._button_held = None; self._is_recording_active = False
        self._start_pos = (0, 0); self._is_moving = False; self._pre_pressed_captured_text = ""
        self._hold_duration_ms = 500; self._timer = None; self._lock = threading.Lock()
        self._h_ibeam = user32.LoadCursorW(None, ctypes.c_wchar_p(IDC_IBEAM))

    def set_enabled(self, left: bool, right: bool, hold_duration_s: float = 0.5, mode: int = 0):
        with self._lock:
            self._hold_duration_ms = int(hold_duration_s * 1000)
            self._left_enabled = left; self._right_enabled = right; self._recording_mode = mode
            logger.info(f"Sensor A636 Active: L:{left} R:{right} D:{hold_duration_s}s")

    def _get_current_cursor(self):
        info = CURSORINFO()
        info.cbSize = ctypes.sizeof(CURSORINFO)
        if user32.GetCursorInfo(ctypes.byref(info)):
            return info.hCursor
        return None

    def handle_move(self, x, y):
        """ [A636] CRITICAL: Anti-Trigger Movement Guard """
        if self._button_held:
            dx = abs(x - self._start_pos[0]); dy = abs(y - self._start_pos[1])
            # Threshold: 5px movement cancels the long-press logic
            if dx > 5 or dy > 5:
                if not self._is_moving:
                    self._is_moving = True; self._cancel_timer()

    def handle_click(self, x, y, button, pressed):
        if pressed: self.click_signal.emit(int(x), int(y))
        with self._lock:
            if pressed:
                if self._button_held: return 
                if (button == mouse.Button.left and self._left_enabled) or (button == mouse.Button.right and self._right_enabled):
                    self._button_held = button; self._start_pos = (x, y); self._is_moving = False; self._start_timer()
            else:
                if self._button_held == button:
                    self._cancel_timer(); self._button_held = None
                    if self._recording_mode == 0 and button == mouse.Button.left:
                        is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_recording_active
                        if is_rec:
                            self.voice_stop_signal.emit(); self._is_recording_active = False

    def _start_timer(self):
        self._cancel_timer()
        self._timer = threading.Timer(self._hold_duration_ms / 1000.0, self._evaluate_trigger)
        self._timer.daemon = True; self._timer.start()

    def _cancel_timer(self):
        if self._timer: self._timer.cancel(); self._timer = None

    def _robust_capture(self):
        """ [A7] High-Resilience Selection Capture inside Timer Thread """
        logger.info("📋 [A636] Attempting robust text capture...")
        old_cb = pyperclip.paste()
        try: pyperclip.copy("")
        except: pass

        # 1. Programmatically release right mouse button
        # This resolves issues where target applications block keys due to active mouse drag/hold state
        user32.mouse_event(0x0010, 0, 0, 0, 0) # MOUSEEVENTF_RIGHTUP
        time.sleep(0.02) # Let OS process release event

        # 2. Release modifier keys to avoid keyboard state interference with ctrl+c
        modifiers = [0x10, 0x11, 0x12, 0x5B, 0x5C] # shift, ctrl, alt, win
        released = []
        for vk in modifiers:
            if user32.GetAsyncKeyState(vk) & 0x8000:
                user32.keybd_event(vk, 0, 2, 0) # KEYEVENTF_KEYUP
                released.append(vk)
                
        # 3. Send Ctrl+C natively with correct scan codes
        user32.keybd_event(0x11, 0x1D, 0, 0) # Ctrl down
        user32.keybd_event(0x43, 0x2E, 0, 0) # C down
        time.sleep(0.01)
        user32.keybd_event(0x43, 0x2E, 2, 0) # C up
        user32.keybd_event(0x11, 0x1D, 2, 0) # Ctrl up
        
        res = ""
        for i in range(15):
            time.sleep(0.01)
            try:
                res = pyperclip.paste().strip()
                if res: break
            except: pass
            
        # 4. If first try failed (likely because context menu popped up and took focus)
        if not res:
            logger.info("📋 [A636] Initial copy empty, sending Esc to dismiss context menu and retrying...")
            user32.keybd_event(0x1B, 0x01, 0, 0) # Esc down with scan code
            time.sleep(0.01)
            user32.keybd_event(0x1B, 0x01, 2, 0) # Esc up
            time.sleep(0.05) # Wait for focus to return
            
            # Send Ctrl+C again
            user32.keybd_event(0x11, 0x1D, 0, 0)
            user32.keybd_event(0x43, 0x2E, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(0x43, 0x2E, 2, 0)
            user32.keybd_event(0x11, 0x1D, 2, 0)
            
            for i in range(20):
                time.sleep(0.01)
                try:
                    res = pyperclip.paste().strip()
                    if res: break
                except: pass

        # Restore modifier keys if they were physically held
        for vk in released:
            user32.keybd_event(vk, 0, 0, 0) # KEYEVENTF_KEYDOWN
            
        if res:
            logger.success(f"📋 [A636] Robust capture SUCCESS: '{res}'")
        else:
            logger.warning("📋 [A636] Robust capture FAILED.")
            try: pyperclip.copy(old_cb)
            except: pass
        return res

    def _evaluate_trigger(self):
        """ [A636] Dispatch only if NOT moving and cursor is I-beam """
        with self._lock:
            if not self._button_held or self._is_moving: return
            
            # 檢查游標是否為直線游標 (I-beam)
            current_cursor = self._get_current_cursor()
            if current_cursor != self._h_ibeam:
                logger.info(f"📡 Cursor not I-Beam ({current_cursor} != {self._h_ibeam}). Bypassing trigger.")
                self._button_held = None
                return
                
            if self._button_held == mouse.Button.left:
                is_rec = self.controller.is_recording if (hasattr(self, "controller") and self.controller) else self._is_recording_active
                if self._recording_mode in [1, 2]:
                    if is_rec:
                        logger.info("📡 [A636] Voice Stop (Toggle Mode via Mouse)")
                        self._is_recording_active = False; self.voice_stop_signal.emit()
                    else:
                        logger.info("📡 [A636] Voice Start (Toggle Mode via Mouse)")
                        self._is_recording_active = True; self.voice_start_signal.emit()
                    self._button_held = None
                else:
                    if not is_rec:
                        logger.info("📡 [A636] Voice Start (PTT Mode via Mouse)")
                        self._is_recording_active = True; self.voice_start_signal.emit()
            elif self._button_held == mouse.Button.right:
                logger.info("📡 [A636] Magic Capture Start")
                captured = self._robust_capture()
                self.magic_signal.emit(captured); self._button_held = None

```

### 📄 `src/utils/text_output.py`
```python
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

```

