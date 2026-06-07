import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from src.ui.settings_window import RefinementDialog
from loguru import logger

def test_ui():
    app = QApplication(sys.argv)
    
    test_text = "這是一段測試文字，用來模擬從視窗中擷取到的原始內容。"
    logger.info("Starting RefinementDialog Test...")
    
    # Create the dialog
    dlg = RefinementDialog(test_text)
    
    # Simulate AI result after 2 seconds
    def simulate_ai():
        mock_result = "✨ 這是 AI 優化後的結果：\n\n" + ("這是一段很長很長的測試內容，用來確認文字框能否正確顯示大段文字。" * 10)
        logger.info(f"Simulating AI result delivery (Length: {len(mock_result)})")
        dlg.show_result(mock_result)
        
    QTimer.singleShot(2000, simulate_ai)
    
    # Show the dialog
    dlg.show()
    logger.info("Dialog show() called. Check if it appears near your cursor.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui()
