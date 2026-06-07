import sys
import os
import torch
from loguru import logger
from funasr import AutoModel

# [A401] Source Audit Script
print("--- SOURCE AUDIT STARTING ---")

model_path = r"D:\AI VOICE\models\SenseVoiceSmall"
print(f"Checking model at: {model_path}")
if not os.path.exists(model_path):
    print("❌ ERROR: Model directory missing!")
    sys.exit(1)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

try:
    print("Attempting to load AutoModel...")
    # Using the same parameters as in engine_v2_stable.py
    model = AutoModel(
        model=model_path,
        device=device,
        disable_update=True,
        hub="ms"
    )
    print("✅ SUCCESS: Model loaded successfully!")
except Exception as e:
    import traceback
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

print("--- AUDIT COMPLETE ---")
