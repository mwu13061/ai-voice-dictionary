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
