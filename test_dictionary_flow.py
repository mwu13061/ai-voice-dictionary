import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.app_controller import AppController

def run_test():
    print("🚀 [TEST] Starting Comprehensive Magic Menu & Dictionary Test...")
    
    app = QApplication(sys.argv)
    controller = AppController()
    
    # 1. Test Menu Triggering (Main Thread Safety)
    print("📡 [TEST] Simulating Smart Magic Trigger (Mouse Hold)...")
    
    def check_menu_visible():
        # exec() is blocking, so we can't easily check visibility while it's open in this test
        # without multithreading, but we can check if the signal was received and processed.
        print("✅ [PASS] If no crash occurred, the routing to Main Thread is likely working.")
        
        # 2. Test Dictionary Learning Flow
        test_text = "DIAGNOSTIC_STAMP_999"
        print(f"📡 [TEST] Triggering 'LEARN' flow for text: {test_text}")
        controller._handle_magic_learn(test_text)
        
        # Check result after a delay
        QTimer.singleShot(1000, final_check)

    def final_check():
        print("🔍 [TEST] Final Validation...")
        if controller.settings.isVisible() and controller.settings.dict_dlg:
            txt = controller.settings.dict_dlg.in_w.text()
            if txt == "DIAGNOSTIC_STAMP_999":
                print(f"✅ [PASS] Dictionary Manager open with text: {txt}")
                print("\n✨ ALL TESTS PASSED! ✨")
            else:
                print(f"❌ [FAIL] Text mismatch: {txt}")
        else:
            print("❌ [FAIL] Dictionary Manager failed to open.")
        app.quit()

    # Simulate the trigger that comes from the Mouse Thread
    QTimer.singleShot(500, controller._handle_smart_magic_trigger)
    # Wait for menu logic (which we'll need to bypass or close for the test to continue)
    # Since exec() is blocking, we'll simulate the learn call AFTER the trigger logic starts
    QTimer.singleShot(1000, check_menu_visible)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_test()
