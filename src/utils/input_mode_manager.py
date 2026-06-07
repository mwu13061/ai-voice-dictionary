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
