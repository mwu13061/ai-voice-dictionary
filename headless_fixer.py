import sys
import os
import json
import threading
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.utils.cloud_engine import GeminiCloudEngine
from loguru import logger

def run_headless_diagnostic():
    logger.info("🧪 [HEADLESS] Starting Deep Diagnostic...")
    
    # 1. Load Real Config
    config_path = "user_data/gemini_tool_config.json"
    if not os.path.exists(config_path):
        logger.error(f"❌ Config not found at {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    api_key = config.get("gemini_api_key", "")
    model = config.get("opt_model", "")
    
    if not api_key:
        logger.error("❌ API Key is empty in config!")
        return
        
    logger.info(f"🔑 Using API Key: {api_key[:10]}...")
    logger.info(f"🤖 Target Model: {model}")

    # 2. Test Cloud Engine Directly
    engine = GeminiCloudEngine()
    engine.configure(api_key, model)
    
    ready, msg = engine.is_ready()
    if not ready:
        logger.error(f"❌ Engine reported NOT READY: {msg}")
        return
    
    logger.success("✅ Engine Ready. Testing simple inference...")
    
    # 3. Perform Mock Inference
    test_text = "測試文字：今天天氣很好。"
    system_prompt = "請幫我潤飾這段文字："
    
    try:
        t_start = time.time()
        result = engine.process_text(test_text, system_prompt, model_override=model)
        duration = time.time() - t_start
        
        if result and not "❌" in result:
            logger.success(f"✅ Inference Success! Length: {len(result)} (Time: {duration:.2f}s)")
            logger.info(f"📝 Result Preview: {result[:50]}...")
        else:
            logger.error(f"❌ Inference failed or returned error: {result}")
            
    except Exception as e:
        logger.error(f"❌ Critical Inference Crash: {e}")

if __name__ == "__main__":
    run_headless_diagnostic()
