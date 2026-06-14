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
        """ [A61] Fast Model Listing - heuristic capability detection, no per-model API calls """
        if not self._api_key: return []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}&pageSize=100"
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                logger.error(f"❌ [Cloud] Model list API returned {response.status_code}: {response.text[:200]}")
                err_msg = self.explain_http_error(response.status_code)
                raise Exception(err_msg)
            
            data = response.json()
            raw_list = data.get('models', [])
            logger.info(f"🔍 [Cloud] Raw model count from API: {len(raw_list)}")
            
            # Filter and classify using heuristics (no per-model verification calls)
            results = []
            SKIP_KEYWORDS = ["embedding", "aqa", "classifier", "ranker", "bison", "gecko", "palm"]
            VISION_KEYWORDS = ["flash", "pro", "ultra", "vision", "multimodal", "2.0", "1.5"]
            
            for m in raw_list:
                m_name = m.get('name', "")
                m_id = m_name.replace("models/", "")
                display = m_id
                
                # Skip non-generation models
                if any(kw in m_id.lower() for kw in SKIP_KEYWORDS):
                    continue
                if "generateContent" not in m.get('supportedGenerationMethods', []):
                    continue
                    
                # Heuristic vision capability
                can_vision = any(kw in m_id.lower() for kw in VISION_KEYWORDS)
                
                results.append({
                    "id": f"models/{m_id}",
                    "display": display,
                    "can_vision": can_vision
                })
            
            # Sort: gemini models first, then alphabetically
            results.sort(key=lambda x: (
                0 if "gemini" in x['display'].lower() else 1,
                x['display']
            ))
            
            logger.success(f"✅ [Cloud] Discovered {len(results)} usable models (fast heuristic mode)")
            return results
        except Exception as e:
            logger.error(f"❌ [Cloud] Model discovery failed: {e}")
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
            return self.explain_http_error(response.status_code)
        except Exception as e: return f"❌ 視覺系統異常: {str(e)}"

    def explain_http_error(self, status_code: int) -> str:
        if status_code == 400:
            return "❌ 請求無效 (400)：請確認選擇的模型或輸入資料格式是否正確。"
        elif status_code == 401:
            return "❌ 驗證失敗 (401)：請檢查您的 Gemini API Key 是否輸入正確或已過期。"
        elif status_code == 403:
            return (
                "❌ 存取被拒 (403)：\n"
                "這通常代表您的 API Key 無法存取該模型或服務。原因包含：\n"
                "1. 您的 IP 地區不受 Google Gemini API 支援（例如在不支援的國家/地區使用 VPN）。\n"
                "2. 您輸入的 API Key 限制了該模型的存取權限。\n"
                "3. 該 API Key 所屬的 Google Cloud 專案未啟用 Generative Language API 服務。\n"
                "4. 帳戶存在欠費、限制或未完成帳單設定。"
            )
        elif status_code == 404:
            return "❌ 找不到資源 (404)：請確認設定中選擇的 AI 模型是否正確，或該模型已被移除。"
        elif status_code == 429:
            return "❌ API 配額超限 (429)：請求次數過多，或免費配額（RPM/TPM）已達上限，請稍後重試。"
        elif status_code >= 500:
            return f"❌ 伺服器錯誤 ({status_code})：Google 伺服器暫時繁忙或發生異常，請稍後重試。"
        else:
            return f"❌ 雲端 API 錯誤 ({status_code})：請檢查網路連線或 API 金鑰狀態。"

    def translate_text(self, text: str, target_lang: str = "繁體中文") -> str:
        if not self._initialized: return "❌ 引擎未就緒"
        try:
            prompt = f"Please translate the following text into {target_lang}. Strictly return ONLY the translated text."
            res = self.process_text(user_text=text, system_prompt=prompt)
            if res.startswith("❌"): return res
            return f"[ORIGINAL]\n{text}\n[TRANSLATED]\n{res}"
        except Exception as e: return f"❌ 翻譯失敗: {e}"
