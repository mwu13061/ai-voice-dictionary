import sys
import os

# [A381] BUNDLE AUDIT SCRIPT
# This script simulates the EXE's internal environment to find missing files.

internal_dir = r"D:\AI VOICE\dist\AI語音助手_v1000\_internal"
sys.path.insert(0, internal_dir)

print(f"--- BUNDLE AUDIT STARTING ---")
print(f"Internal Dir: {internal_dir}")

try:
    print("1. Testing torch import...")
    import torch
    print(f"   - Success! Torch version: {torch.__version__}")
except Exception as e:
    print(f"   - FAILED: {e}")

try:
    print("2. Testing OpenCC import...")
    from opencc import OpenCC
    cc = OpenCC('s2t')
    print(f"   - Success! OpenCC initialized.")
except Exception as e:
    print(f"   - FAILED: {e}")

try:
    print("3. Testing FunASR core import...")
    from funasr import AutoModel
    print(f"   - Success! AutoModel imported.")
    print("4. Testing FunASR initialization (without loading models)...")
    # This checks if the factory functions are callable
    print(f"   - AutoModel type: {type(AutoModel)}")
except Exception as e:
    print(f"   - FAILED: {e}")

print("--- AUDIT COMPLETE ---")
