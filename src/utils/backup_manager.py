import os
import shutil
import time
from datetime import datetime
from loguru import logger

class BackupManager:
    """
    [A406] Automated Backup & Restore System.
    Ensures zero-loss development by creating snapshots before edits.
    """
    def __init__(self, root_dir=r"D:\AI VOICE", backup_dir=r"D:\AI VOICE\backups"):
        self.root_dir = root_dir
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_snapshot(self, label="Surgical_Fix"):
        """ Creates a full source backup (excluding venv and models) """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"Build_{label}_{timestamp}"
        target_path = os.path.join(self.backup_dir, folder_name)
        
        logger.info(f"💾 Creating system snapshot: {folder_name}...")
        
        # Define folders to include (Source only to keep it small/fast)
        to_backup = ['src', 'main.py', '啟動語音助手.bat', 'GEMINI.md']
        
        os.makedirs(target_path, exist_ok=True)
        for item in to_backup:
            src = os.path.join(self.root_dir, item)
            dst = os.path.join(target_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.exists(src):
                shutil.copy2(src, dst)
        
        logger.success(f"✅ Snapshot secured at: {target_path}")
        return target_path

    def restore_snapshot(self, folder_name):
        """ Restores a specific snapshot to the root directory """
        src_path = os.path.join(self.backup_dir, folder_name)
        if not os.path.exists(src_path):
            logger.error(f"❌ Restore failed: Snapshot {folder_name} not found.")
            return False
            
        logger.warning(f"⚠️ RESTORING SYSTEM TO: {folder_name}...")
        # Simple overwrite of source files
        for item in os.listdir(src_path):
            src = os.path.join(src_path, item)
            dst = os.path.join(self.root_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst): shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        logger.success("✅ System restoration complete.")
        return True

if __name__ == "__main__":
    # Create initial safety backup
    manager = BackupManager()
    manager.create_snapshot("A406_Stability_Base")
