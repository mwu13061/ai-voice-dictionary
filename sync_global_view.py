import os
import datetime

# --- 配置設定 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = "GLOBAL_VIEW.md"

# 想要包含的目錄與單一檔案
INCLUDE_DIRS = ["src"]
INCLUDE_FILES = ["main.py", "GEMINI.md"]

# 排除的目錄與副檔名 (避免寫入不相關或過大的二進制檔案)
EXCLUDE_DIRS = ["__pycache__", "venv", ".git", "backups", "models", "build", "dist", "assets"]
EXCLUDE_EXTS = [".pyc", ".spec", ".log", ".db", ".png", ".pkg", ".zip", ".toc", ".exe", ".bat"]

def should_include(file_path):
    # 檢查是否在排除目錄中
    path_parts = file_path.replace("\\", "/").split("/")
    if any(ex_dir in path_parts for ex_dir in EXCLUDE_DIRS):
        return False
    # 檢查副檔名
    if any(file_path.endswith(ext) for ext in EXCLUDE_EXTS):
        return False
    return True

def gather_files():
    target_files = []
    
    # 加入指定的單一檔案
    for f in INCLUDE_FILES:
        path = os.path.join(PROJECT_ROOT, f)
        if os.path.exists(path) and should_include(path):
            target_files.append(path)
            
    # 遍歷指定的目錄
    for d in INCLUDE_DIRS:
        dir_path = os.path.join(PROJECT_ROOT, d)
        if os.path.exists(dir_path):
            for root, _, files in os.walk(dir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if should_include(full_path):
                        target_files.append(full_path)
                        
    return sorted(target_files)

def generate_global_view():
    files = gather_files()
    output_path = os.path.join(PROJECT_ROOT, OUTPUT_FILE)
    
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"# AI Voice Assistant - 專案全局視圖 (Global View)\n")
        out.write(f"自動生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write("> ⚠️ **注意**: 本檔案為腳本自動生成，用於提供 AI 開發者全局上下文。請勿直接手動修改此檔案，而是修改原始程式碼後重新執行 `python sync_global_view.py`。\n\n")
        
        # 建立檔案索引目錄
        out.write("## 🗂️ 檔案索引 (File Index)\n")
        for f in files:
            rel_path = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            out.write(f"- `{rel_path}`\n")
        out.write("\n---\n\n")
        
        # 寫入檔案內容
        out.write("## 💻 核心程式碼內容 (Source Code)\n\n")
        for f in files:
            rel_path = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            out.write(f"### 📄 `{rel_path}`\n")
            
            # 判斷 Markdown 的程式碼高亮類型
            lang = "python" if f.endswith(".py") else ("markdown" if f.endswith(".md") else "text")
            out.write(f"```{lang}\n")
            
            try:
                with open(f, "r", encoding="utf-8") as infile:
                    out.write(infile.read())
            except Exception as e:
                out.write(f"無法讀取檔案內容: {e}\n")
            out.write("\n```\n\n")
            
    print(f"✅ 成功生成全局視圖！共整合了 {len(files)} 個檔案至 {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_global_view()
