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
