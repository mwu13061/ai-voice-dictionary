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

# [A36] Unified Phonetic homophone character groups for voice typing correction
CONFUSED_GROUPS = [
    "在再載災讚",
    "的得地底迪",
    "是事世市試示室四思石世適式設社射舌十食拾實時濕失",
    "川穿傳船專窗雙闖床創",
    "理力利立例歷離里",
    "建件健漸簡見尖",
    "風分份豐封鋒峰粉芬",
    "心新信欣星形行性型省",
    "我臥握喔",
    "嗯恩安昂",
    "和何河合核荷",
    "作做左昨",
    "經精驚靜境金近",
    "中重終眾種鐘",
    "加家佳夾甲架",
    "前錢簽乾淺千",
    "發法反方",
    "國果過郭鍋",
    "主注著助住竹",
    "人仁任忍認",
    "一伊依衣醫以意易藝",
    "有友又右幼誘油",
    "軟亂管暖",
    "體提替天",
    "定訂頂丁",
    "按案暗安",
    "鈕牛扭柳",
    "語雨與玉預",
    "音應英印因",
    "輸書舒樹署",
    "入路錄陸如",
    "用擁永優",
    "戶湖互護",
    "個各歌給",
    "詞磁此次刺",
    "庫苦哭褲",
    "全前錢圈",
    "球求秋區"
]

class LearningEngine:
    """ [A670/A555] Production Ready Database Engine with Hardened Migration """
    def __init__(self, update_callback=None):
        self._lock = threading.Lock()
        self._cache = []
        self._update_callback = update_callback
        self._initialize_db()
        self.refresh_cache()
        # [A43] Fetch latest global dictionary from GitHub on startup
        self.download_global_dictionary()

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
            temp_cache = {}
            # 1. Load global dictionary first (lower priority)
            global_path = os.path.join(os.path.dirname(DB_PATH), "global_learning.csv")
            if os.path.exists(global_path):
                try:
                    import csv
                    with open(global_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        next(reader, None) # Skip header
                        for row in reader:
                            if len(row) >= 2:
                                orig, corr = row[0].strip(), row[1].strip()
                                if orig and corr:
                                    temp_cache[orig] = corr
                except Exception as ge:
                    logger.warning(f"Failed to load global dictionary: {ge}")
            
            # 2. Load personal habits (higher priority, overrides global)
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT original, corrected FROM habits")
                rows = cursor.fetchall()
                conn.close()
                for orig, corr in rows:
                    temp_cache[orig] = corr
                    
            # 3. Convert to list format
            self._cache = list(temp_cache.items())
            
            # [A32] Auto collect feedback on startup and update
            self.auto_collect_feedback()
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")

    def auto_collect_feedback(self):
        """ [A32] Automatically collect new dictionary additions to user_data/collected_feedback.csv """
        try:
            # 1. Fetch current database items
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT original, corrected FROM habits")
                db_items = cursor.fetchall()
                conn.close()
                
            if not db_items:
                return
                
            # Load existing global dictionary to skip collecting already shared ones
            existing_global = set()
            global_path = os.path.join(os.path.dirname(DB_PATH), "global_learning.csv")
            if os.path.exists(global_path):
                try:
                    import csv
                    with open(global_path, 'r', encoding='utf-8-sig') as gf:
                        g_reader = csv.reader(gf)
                        next(g_reader, None) # Skip header
                        for g_row in g_reader:
                            if len(g_row) >= 2:
                                existing_global.add((g_row[0].strip(), g_row[1].strip()))
                except Exception as ge:
                    logger.warning(f"Failed to read global dictionary for auto-collect check: {ge}")

            # [A36] Only collect phonetic typos (homophones), ignoring custom shortcuts/abbreviations
            db_dict = {}
            for orig, corr in db_items:
                if self.is_phonetic_typo(orig, corr):
                    if (orig, corr) not in existing_global:
                        db_dict[orig] = corr
                    
            if not db_dict:
                return
            
            # 2. Read existing collected feedback
            feedback_path = os.path.join(os.path.dirname(DB_PATH), "collected_feedback.csv")
            existing_feedback = {}
            if os.path.exists(feedback_path):
                try:
                    import csv
                    with open(feedback_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        next(reader, None) # Skip header
                        for row in reader:
                            if len(row) >= 2:
                                existing_feedback[row[0].strip()] = row[1].strip()
                except Exception as re:
                    logger.warning(f"Error reading existing feedback CSV: {re}")
                    
            # 3. Check for new additions or updates
            needs_update = False
            for orig, corr in db_dict.items():
                if orig not in existing_feedback or existing_feedback[orig] != corr:
                    needs_update = True
                    break
                    
            if needs_update or not os.path.exists(feedback_path):
                merged = existing_feedback.copy()
                merged.update(db_dict)
                
                import csv
                os.makedirs(os.path.dirname(feedback_path), exist_ok=True)
                with open(feedback_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Original', 'Correction'])
                    for orig, corr in sorted(merged.items()):
                        writer.writerow([orig, corr])
                logger.info(f"🔄 [A32] Auto-collected new dictionary items to {feedback_path}")
        except Exception as e:
            logger.error(f"Failed to auto-collect feedback: {e}")

    def apply_habits(self, text):
        if not text: return text
        final_text = text
        # Fast memory-based correction
        for orig, corr in self._cache:
            if orig in final_text:
                final_text = final_text.replace(orig, corr)
        return final_text

    def generate_error_variants(self, orig: str, corr: str = None) -> list:
        if len(orig) <= 1:
            return []
            
        # [A36] Dynamically build confused map for characters in orig using CONFUSED_GROUPS
        confused_map = {}
        for char in orig:
            alts = []
            for group in CONFUSED_GROUPS:
                if char in group:
                    for c in group:
                        if c != char:
                            alts.append(c)
            if alts:
                confused_map[char] = alts
                
        variants = set()
        
        # Generate variations by substituting characters that are in the map
        for i, char in enumerate(orig):
            if char in confused_map:
                for alt in confused_map[char]:
                    variant = orig[:i] + alt + orig[i+1:]
                    if variant != orig and (corr is None or variant != corr):
                        variants.add(variant)
                        if len(variants) >= 5:
                            break
            if len(variants) >= 5:
                break
                
        # Fallback generator: if we still have < 3 variants, generate simple variations like omitting characters
        if len(variants) < 3 and len(orig) > 2:
            for i in range(len(orig)):
                variant = orig[:i] + orig[i+1:]
                if variant and (corr is None or variant != corr):
                    variants.add(variant)
                if len(variants) >= 5:
                    break
                    
        return list(variants)[:5]

    def is_phonetic_typo(self, orig: str, corr: str) -> bool:
        """ [A36] Checks if orig and corr represent a phonetic typo (homophones) """
        if not orig or not corr:
            return False
        # Typos from voice typing are almost always homophones with the same length
        if len(orig) != len(corr):
            return False
            
        for o_char, c_char in zip(orig, corr):
            if o_char == c_char:
                continue
            # Check if they share the same phonetic group in CONFUSED_GROUPS
            found_group = False
            for group in CONFUSED_GROUPS:
                if o_char in group and c_char in group:
                    found_group = True
                    break
            if not found_group:
                return False
        return True

    def add_habit_manual(self, orig, corr):
        if not orig or not corr: return False
        try:
            with self._lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO habits (original, corrected) VALUES (?, ?)", (orig, corr))
                
                # [A30] Auto-generate 3-5 wrong word combinations if correction target and original are > 1 character
                if len(corr) > 1 and len(orig) > 1:
                    variants = self.generate_error_variants(orig, corr)
                    for var in variants:
                        cursor.execute("INSERT OR REPLACE INTO habits (original, corrected) VALUES (?, ?)", (var, corr))
                
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

    def download_global_dictionary(self):
        """ [A43] Fetch latest global dictionary from GitHub in the background """
        def _download():
            # Check if we are on a developer computer (contains .git repository)
            # If so, skip auto background download to prevent overwriting local overrides
            is_dev = os.path.exists(".git") or os.path.exists(os.path.join(os.path.dirname(DB_PATH), "..", ".git"))
            if is_dev:
                logger.info("🌐 [A43] Developer machine detected (.git exists). Skipping background global dictionary download to protect local overrides.")
                self.refresh_cache()
                return

            url = "https://raw.githubusercontent.com/mwu13061/ai-voice-dictionary/main/user_data/global_learning.csv"
            global_path = os.path.join(os.path.dirname(DB_PATH), "global_learning.csv")
            try:
                import requests
                logger.info(f"🌐 [A43] Checking for global dictionary updates from {url}...")
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    os.makedirs(os.path.dirname(global_path), exist_ok=True)
                    with open(global_path, "wb") as f:
                        f.write(res.content)
                    logger.success("🌐 [A43] Global dictionary successfully synchronized from cloud!")
                    self.refresh_cache()
                else:
                    logger.warning(f"🌐 [A43] Cloud dictionary status: {res.status_code}")
            except Exception as e:
                logger.warning(f"🌐 [A43] Failed to download global dictionary: {e}")
                
        import threading
        threading.Thread(target=_download, daemon=True).start()

    def list_global_dictionary(self):
        """ [A43] List all entries in global_learning.csv """
        global_path = os.path.join(os.path.dirname(DB_PATH), "global_learning.csv")
        items = []
        if os.path.exists(global_path):
            try:
                import csv
                with open(global_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader, None) # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            orig, corr = row[0].strip(), row[1].strip()
                            if orig and corr:
                                items.append((orig, corr))
            except Exception as e:
                logger.warning(f"Error reading global dictionary file: {e}")
        return items
