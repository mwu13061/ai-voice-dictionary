import sys
import os
import time
import numpy as np
from loguru import logger

# Set standard output to UTF-8 to prevent encoding errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# [A404] End-to-End Diagnostic Self-Test
# This script bypasses the microphone and simulates a real voice input event.

print("\n--- STARTING AUTOMATED PIPELINE TEST ---")

# 1. Force add project src to path
sys.path.insert(0, os.getcwd())

try:
    from src.audio.engines.engine_v2_stable import EngineV2Stable
    from src.utils.learning_engine import LearningEngine
    from src.utils.output_plugins.plugin_v1_instant import OutputPlugin
    
    print("✅ All modules imported successfully.")

    # 2. Initialize components
    print("⌛ Initializing Engine (this may take a few seconds)...")
    engine = EngineV2Stable()
    engine.load()
    
    learner = LearningEngine()
    output = OutputPlugin()
    
    print("✅ Components ready.")

    # 3. Create synthetic audio (1 second of white noise to trigger engine)
    # SenseVoice needs actual content, let's hope it detects something from noise
    # or just use a very low amplitude sine wave.
    fs = 16000
    duration = 1.0
    audio = np.random.uniform(-0.1, 0.1, int(fs * duration)).astype(np.float32)
    
    print(f"📡 Simulating Audio Ready (Len={len(audio)} samples)...")
    
    # 4. Run Inference
    t0 = time.time()
    raw_text = engine.process(audio)
    t1 = time.time()
    
    infer_time = t1 - t0
    print(f"🤖 Engine Processed in {infer_time:.4f}s")
    assert infer_time < 0.6, f"❌ [PERF REGRESSION] Inference is too slow ({infer_time:.4f}s > 0.6s). Check PyTorch thread/CPU optimizations!"
    print("✅ Performance Assertion: Inference speed OK.")
    print(f"🤖 Raw Text: '{raw_text}'")

    if not raw_text:
        # If synthetic noise didn't work, we've at least proven the pipeline exists.
        # Let's force a text to test the output plugin.
        raw_text = "自動化自我測試成功"
        print("⚠️ Engine returned empty (normal for noise), forcing test text.")

    # 5. Run Correction
    final_text = learner.apply_habits(raw_text)
    print(f"📝 Final Corrected Text: '{final_text}'")

    # 6. Test Output (This will try to press Ctrl+V)
    print("⌨️ Attempting Injection Test (you should see text in 2 seconds if you focus a text area)...")
    time.sleep(2.0)
    
    t_out_start = time.time()
    output.output(final_text)
    t_out_end = time.time()
    
    out_time = t_out_end - t_out_start
    print(f"⌨️ Keystroke Injection completed in {out_time:.4f}s")
    assert out_time < 0.05, f"❌ [PERF REGRESSION] Keystroke injection is too slow ({out_time:.4f}s > 0.05s)!"
    print("✅ Performance Assertion: Keystroke injection speed OK.")
    
    print("\n✅ --- PIPELINE TEST COMPLETE (ALL PERFORMANCE GUARDS PASSED) ---")
    print("If you didn't see the text above typed out, the issue is at the Win32 Keyboard level.")

except Exception as e:
    import traceback
    print(f"❌ TEST FAILED: {e}")
    traceback.print_exc()

input("\nPress Enter to exit...")
