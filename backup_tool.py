# backup_tool.py
import os
import sys
import zipfile
import datetime

BACKUP_DIR = "backups"
FILES_TO_BACKUP = ["main.py"]
DIRS_TO_BACKUP = ["src"]

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(BACKUP_DIR, f"src_backup_{timestamp}.zip")
    
    try:
        with zipfile.ZipFile(backup_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup files
            for file in FILES_TO_BACKUP:
                if os.path.exists(file):
                    zipf.write(file)
            # Backup directories
            for directory in DIRS_TO_BACKUP:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            filepath = os.path.join(root, file)
                            zipf.write(filepath)
                            
        print(f"✅ 備份成功！備份存檔：{backup_filename}")
    except Exception as e:
        print(f"❌ 備份失敗：{e}")

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("src_backup_") and f.endswith(".zip")]
    return sorted(files, reverse=True)

def restore_backup():
    backups = list_backups()
    if not backups:
        print("❌ 找不到任何歷史備份檔案。")
        return
        
    print("\n--- 歷史備份清單 ---")
    for idx, f in enumerate(backups):
        print(f"[{idx + 1}] {f}")
        
    try:
        choice = input("\n請輸入要還原的備份編號 (或按 Enter 取消): ").strip()
        if not choice:
            print("已取消還原。")
            return
        idx = int(choice) - 1
        if idx < 0 or idx >= len(backups):
            print("❌ 輸入無效。")
            return
            
        selected_backup = os.path.join(BACKUP_DIR, backups[idx])
        confirm = input(f"⚠️ 警告：還原將覆蓋當前的 src 目錄與 main.py。確認還原 {backups[idx]}？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消還原。")
            return
            
        # Perform restore
        with zipfile.ZipFile(selected_backup, 'r') as zipf:
            zipf.extractall()
        print(f"✅ 還原成功！已回復至備份狀態：{backups[idx]}")
    except ValueError:
        print("❌ 請輸入有效的數字。")
    except Exception as e:
        print(f"❌ 還原失敗：{e}")

def main():
    print("==========================================")
    print("      語音助手 原始碼備份與還原工具")
    print("==========================================")
    print("1. 建立當前系統備份 (Backup)")
    print("2. 還原歷史備份 (Restore)")
    print("3. 退出")
    print("==========================================")
    
    choice = input("請選擇操作 (1-3): ").strip()
    if choice == '1':
        create_backup()
    elif choice == '2':
        restore_backup()
    else:
        print("退出工具。")

if __name__ == "__main__":
    main()
