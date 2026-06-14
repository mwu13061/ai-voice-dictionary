# src/utils/localization.py
import json
import os
from loguru import logger
from src.utils.path_helper import get_writable_path

CONFIG_PATH = get_writable_path(os.path.join("user_data", "gemini_tool_config.json"))

TRANSLATIONS = {
    "zh-TW": {
        "title": "AI 語音助手設定 (Build [A1002])",
        "tab_settings": "⚡ 設定",
        "tab_magic": "🪄 魔法選單",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 工程",
        "save": "💾 儲存設定",
        "close": "❌ 關閉",
        "save_success": "✅ 設定已儲存",
        "save_restart_msg": "語言設定將於下次啟動時生效。",
        "settings_tray": "⚙️ 設定",
        "exit_tray": "❌ 退出",
        
        # Settings Tab
        "core_settings": "🧠 啟動與核心設定",
        "auto_start": "隨電腦開機自動啟動助手",
        "smart_left": "🖱️ 啟用左鍵長按啟動語音輸入",
        "smart_right": "🔮 啟用右鍵長按顯示魔法選單",
        "use_punc": "啟用自動輸入標點",
        
        "trigger_modes": "📡 語音輸入觸發模式",
        "recording_mode": "錄音觸發方式：",
        "smart_hold_time": "啟動久按時間",
        "mode_ptt": "📞 對講機模式",
        "mode_toggle_1": "🔘 開關模式 (久按開/停止發話關)",
        "mode_toggle_2": "🔘 開關模式 (久按開/久按關)",
        "output_instant": "🚀 極速貼上",
        "output_typewriter": "🎹 打字機模式",
        "mic_lbl": "🎙️ 麥克風:",
        "mic_tooltip": "選擇語音輸入的麥克風裝置",
        "refresh_tooltip": "重新整理麥克風清單",
        
        "hotkey_settings": "快速鍵語音輸入設定",
        "start_voice": "啟動語音輸入：",
        "start_magic": "啟動魔法選單：",
        "modify_keys": "🔧 修改按鍵組合",
        
        "style_settings": "啟動語音輸入風格",
        "sound_cue": "音效提醒風格：",
        "ui_cue": "圖像提醒風格：",
        "bubble_pos": "📍 調整氣泡球固定位置",
        "vis_style_none": "🫥 無提醒",
        "vis_style_fixed": "💬 固定位置氣泡提醒",
        "vis_style_follow": "✨ 跟隨遊標位置氣泡提醒",
        
        "lang_settings": "🌐 語言與介面設定",
        "asr_lang": "語音辨識語言：",
        "ui_lang": "介面顯示語言：",
        "restart_hint": "* (變更語言需重啟軟體生效)",
        
        # Magic Menu Tab
        "menu_mgmt": "選單管理 (≡ 拖拽排序 / 勾選隱藏):",
        "add_custom": "➕ 新增自定義按鈕",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. 提示詞優化模型:",
        "vis_model": "📸 2. 截圖翻譯模型:",
        "fix_model": "🧠 3. 語音聽寫糾正模型:",
        "query_models": "🔍 查詢模型清單",
        "ai_option": "AI 修改方案:",
        "add_scheme": "➕ 新增方案",
        "del_scheme": "➖ 刪除方案",
        "edit_prompt": "編輯提示詞內容:",
        "export_all": "📤 匯出全部設定 (備份)",
        "import_all": "📥 匯入全部設定 (還原)",
        
        # Engineering Tab
        "auto_fix": "啟用 AI 背景自動糾錯 (需 API)",
        "show_monitor": "顯示監控視窗",
        "auto_gen_variants": "手動新增個人詞庫時，自動新增同音字變體 (工程)",
    },
    "zh-CN": {
        "title": "AI 语音助手设置 (Build [A1002])",
        "tab_settings": "⚡ 设置",
        "tab_magic": "🪄 魔法菜单",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 工程",
        "save": "💾 保存设置",
        "close": "❌ 关闭",
        "save_success": "✅ 设置已保存",
        "save_restart_msg": "语言设置将于下次启动时生效。",
        "settings_tray": "⚙️ 设置",
        "exit_tray": "❌ 退出",
        
        # Settings Tab
        "core_settings": "🧠 启动与核心设置",
        "auto_start": "随电脑开机自动启动助手",
        "smart_left": "🖱️ 启用左键长按启动语音输入",
        "smart_right": "🔮 启用右键长按显示魔法菜单",
        "use_punc": "启用自动输入标点",
        
        "trigger_modes": "📡 语音输入触发模式",
        "recording_mode": "录音触发方式：",
        "smart_hold_time": "启动久按时间",
        "mode_ptt": "📞 对讲机模式",
        "mode_toggle_1": "🔘 开关模式 (久按开/停止发话关)",
        "mode_toggle_2": "🔘 开关模式 (久按开/久按关)",
        "output_instant": "🚀 极速贴上",
        "output_typewriter": "🎹 打字机模式",
        "mic_lbl": "🎙️ 麦克风:",
        "mic_tooltip": "选择语音输入的麦克风设备",
        "refresh_tooltip": "重新整理麦克风清单",
        
        "hotkey_settings": "快捷键语音输入设置",
        "start_voice": "启动语音输入：",
        "start_magic": "启动魔法菜单：",
        "modify_keys": "🔧 修改按键组合",
        
        "style_settings": "启动语音输入风格",
        "sound_cue": "音效提醒风格：",
        "ui_cue": "图像提醒风格：",
        "bubble_pos": "📍 调整气泡球固定位置",
        "vis_style_none": "🫥 无提醒",
        "vis_style_fixed": "💬 固定位置气泡提醒",
        "vis_style_follow": "✨ 跟随光标位置气泡提醒",
        
        "lang_settings": "🌐 语言与界面设置",
        "asr_lang": "语音识别语言：",
        "ui_lang": "界面显示语言：",
        "restart_hint": "* (变更语言需重启软件生效)",
        
        # Magic Menu Tab
        "menu_mgmt": "菜单管理 (≡ 拖拽排序 / 勾选隐藏):",
        "add_custom": "➕ 新增自定义按钮",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. 提示词优化模型:",
        "vis_model": "📸 2. 截图翻译模型:",
        "fix_model": "🧠 3. 语音听写纠正模型:",
        "query_models": "🔍 查询模型清单",
        "ai_option": "AI 修改方案:",
        "add_scheme": "➕ 新增方案",
        "del_scheme": "➖ 删除方案",
        "edit_prompt": "编辑提示词内容:",
        "export_all": "📤 导出全部设置 (备份)",
        "import_all": "📥 导入全部设置 (还原)",
        
        # Engineering Tab
        "auto_fix": "启用 AI 背景自动纠错 (需 API)",
        "show_monitor": "显示监控窗口",
        "auto_gen_variants": "手动新增个人词库时，自动新增同音字变体 (工程)",
    },
    "en-US": {
        "title": "AI Voice Assistant Settings (Build [A1002])",
        "tab_settings": "⚡ Settings",
        "tab_magic": "🪄 Magic Menu",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 Dev",
        "save": "💾 Save Settings",
        "close": "❌ Close",
        "save_success": "✅ Settings Saved",
        "save_restart_msg": "Language settings will take effect upon next startup.",
        "settings_tray": "⚙️ Settings",
        "exit_tray": "❌ Exit",
        
        # Settings Tab
        "core_settings": "🧠 Startup & Core Settings",
        "auto_start": "Start Assistant automatically with Windows",
        "smart_left": "🖱️ Enable left long-press for dictation",
        "smart_right": "🔮 Enable right long-press for Magic Menu",
        "use_punc": "Enable automatic punctuation",
        
        "trigger_modes": "📡 Voice Input Trigger Mode",
        "recording_mode": "Recording trigger method:",
        "smart_hold_time": "Hold Threshold",
        "mode_ptt": "📞 Push-to-Talk Mode",
        "mode_toggle_1": "🔘 Toggle (Hold/Release to Stop)",
        "mode_toggle_2": "🔘 Toggle (Hold/Hold again to Stop)",
        "output_instant": "🚀 Instant Paste",
        "output_typewriter": "🎹 Typewriter Mode",
        "mic_lbl": "🎙️ Mic:",
        "mic_tooltip": "Choose microphone device for dictation",
        "refresh_tooltip": "Refresh microphone device list",
        
        "hotkey_settings": "Hotkey Settings",
        "start_voice": "Start Voice Dictation:",
        "start_magic": "Start Magic Menu:",
        "modify_keys": "🔧 Modify Key Combo",
        
        "style_settings": "UI & Sound Styles",
        "sound_cue": "Chime Style:",
        "ui_cue": "Visual Hint Style:",
        "bubble_pos": "📍 Adjust Bubble Fixed Position",
        "vis_style_none": "🫥 No Reminder",
        "vis_style_fixed": "💬 Fixed Bubble Reminder",
        "vis_style_follow": "✨ Follow Cursor Bubble Reminder",
        
        "lang_settings": "🌐 Language Settings",
        "asr_lang": "ASR Language:",
        "ui_lang": "UI Language:",
        "restart_hint": "* (Restart required for UI language change)",
        
        # Magic Menu Tab
        "menu_mgmt": "Menu Management (≡ Drag to sort / Check to hide):",
        "add_custom": "➕ Add Custom Button",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. Prompt Opt Model:",
        "vis_model": "📸 2. Vision Model:",
        "fix_model": "🧠 3. ASR Fix Model:",
        "query_models": "🔍 Query Models",
        "ai_option": "AI Modification Profile:",
        "add_scheme": "➕ Add Profile",
        "del_scheme": "➖ Delete Profile",
        "edit_prompt": "Edit Prompt Content:",
        "export_all": "📤 Export Settings (Backup)",
        "import_all": "📥 Import Settings (Restore)",
        
        # Engineering Tab
        "auto_fix": "Enable AI Auto-Fix (API Required)",
        "show_monitor": "Show Monitor Window",
        "auto_gen_variants": "Auto-generate homophone variants (Dev)",
    },
    "ja-JP": {
        "title": "AI 音声アシスタント設定 (Build [A1002])",
        "tab_settings": "⚡ 設定",
        "tab_magic": "🪄 マジックメニュー",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 開発",
        "save": "💾 設定を保存",
        "close": "❌ 閉じる",
        "save_success": "✅ 設定を保存しました",
        "save_restart_msg": "言語設定は次回の起動時に有効になります。",
        "settings_tray": "⚙️ 設定",
        "exit_tray": "❌ 終了",
        
        # Settings Tab
        "core_settings": "🧠 起動とコア設定",
        "auto_start": "Windows 起動時に自動でアシスタントを開始",
        "smart_left": "🖱️ 左クリック長押しで音声入力を開始",
        "smart_right": "🔮 右クリック長押しでマジックメニューを表示",
        "use_punc": "句読点の自動入力を有効化",
        
        "trigger_modes": "📡 音声入力トリガーモード",
        "recording_mode": "録음トリガー方法：",
        "smart_hold_time": "長押し判定時間",
        "mode_ptt": "📞 トランシーバーモード",
        "mode_toggle_1": "🔘 トグル（長押しで開始 / 離して停止）",
        "mode_toggle_2": "🔘 トグル（長押しで開始 / 再度長押しで停止）",
        "output_instant": "🚀 高速貼り付け",
        "output_typewriter": "🎹 タイプライターモード",
        "mic_lbl": "🎙️ マイク:",
        "mic_tooltip": "音声入力用のマイクデバイスを選択",
        "refresh_tooltip": "マイクデバイスリストを更新",
        
        "hotkey_settings": "ホットキー設定",
        "start_voice": "音声入力を開始：",
        "start_magic": "マジックメニューを開始：",
        "modify_keys": "🔧 キーの組み合わせを変更",
        
        "style_settings": "UI & 効果音スタイル",
        "sound_cue": "チャイムスタイル：",
        "ui_cue": "ビジュアルヒントスタイル：",
        "bubble_pos": "📍 バブルの固定位置を調整",
        "vis_style_none": "🫥 通知なし",
        "vis_style_fixed": "💬 固定位置のバブル通知",
        "vis_style_follow": "✨ カーソル追従のバブル通知",
        
        "lang_settings": "🌐 言語設定",
        "asr_lang": "音声認識言語：",
        "ui_lang": "表示言語：",
        "restart_hint": "* (言語変更の適用には再起動が必要です)",
        
        # Magic Menu Tab
        "menu_mgmt": "メニュー管理 (≡ ドラッグして並べ替え / チェックして非表示):",
        "add_custom": "➕ カスタムボタンを追加",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. プロンプト最適化モデル:",
        "vis_model": "📸 2. ビジョンモデル:",
        "fix_model": "🧠 3. 音声修正モデル:",
        "query_models": "🔍 モデル一覧を照会",
        "ai_option": "AI 修正プロファイル:",
        "add_scheme": "➕ プロファイルを追加",
        "del_scheme": "➖ プロファイルを削除",
        "edit_prompt": "プロンプト内容を編集:",
        "export_all": "📤 設定をエクスポート (バックアップ)",
        "import_all": "📥 設定をインポート (復元)",
        
        # Engineering Tab
        "auto_fix": "AI バックグラウンド自動修正を有効化 (API必要)",
        "show_monitor": "モニターウィンドウを表示",
        "auto_gen_variants": "同音異義語の自動生成 (開発)",
    },
    "ko-KR": {
        "title": "AI 음성 비서 설정 (Build [A1002])",
        "tab_settings": "⚡ 설정",
        "tab_magic": "🪄 매직 메뉴",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 개발",
        "save": "💾 설정 저장",
        "close": "❌ 닫기",
        "save_success": "✅ 설정이 저장되었습니다",
        "save_restart_msg": "언어 설정은 다음 시작 시 적용됩니다.",
        "settings_tray": "⚙️ 설정",
        "exit_tray": "❌ 종료",
        
        # Settings Tab
        "core_settings": "🧠 시작 및 코어 설정",
        "auto_start": "Windows 시작 시 비서 자동 실행",
        "smart_left": "🖱️ 마우스 왼쪽 버튼 길게 눌러 음성 입력 시작",
        "smart_right": "🔮 마우스 오른쪽 버튼 길게 눌러 매직 메뉴 표시",
        "use_punc": "문장 부호 자동 입력 활성화",
        
        "trigger_modes": "📡 음성 입력 트리거 모드",
        "recording_mode": "녹음 트리거 방식:",
        "smart_hold_time": "길게 누르기 임계값",
        "mode_ptt": "📞 무전기 모드",
        "mode_toggle_1": "🔘 토글 (길게 눌러 시작 / 떼서 중지)",
        "mode_toggle_2": "🔘 토글 (길게 눌러 시작 / 다시 길게 눌러 중지)",
        "output_instant": "🚀 즉시 붙여넣기",
        "output_typewriter": "🎹 타자기 모드",
        "mic_lbl": "🎙️ 마이크:",
        "mic_tooltip": "음성 입력용 마이크 장치 선택",
        "refresh_tooltip": "마이크 장치 목록 새로고침",
        
        "hotkey_settings": "단축키 설정",
        "start_voice": "음성 입력 시작:",
        "start_magic": "매직 메뉴 시작:",
        "modify_keys": "🔧 단축키 조합 변경",
        
        "style_settings": "UI 및 효과음 스타일",
        "sound_cue": "차임벨 스타일:",
        "ui_cue": "시각적 힌트 스타일:",
        "bubble_pos": "📍 버블 고정 위치 조정",
        "vis_style_none": "🫥 알림 없음",
        "vis_style_fixed": "💬 고정 위치 버블 알림",
        "vis_style_follow": "✨ 커서 따라가기 버블 알림",
        
        "lang_settings": "🌐 언어 설정",
        "asr_lang": "음성 인식 언어:",
        "ui_lang": "표시 언어:",
        "restart_hint": "* (표시 언어 변경은 재시작 시 적용됩니다)",
        
        # Magic Menu Tab
        "menu_mgmt": "메뉴 관리 (≡ 드래그하여 정렬 / 체크하여 숨기기):",
        "add_custom": "➕ 사용자 정의 버튼 추가",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. 프롬프트 최적화 모델:",
        "vis_model": "📸 2. 비전 모델:",
        "fix_model": "🧠 3. 음성 보정 모델:",
        "query_models": "🔍 모델 목록 조회",
        "ai_option": "AI 보정 프로필:",
        "add_scheme": "➕ 프로필 추가",
        "del_scheme": "➖ 프로필 삭제",
        "edit_prompt": "프롬프트 내용 편집:",
        "export_all": "📤 설정 내보내기 (백업)",
        "import_all": "📥 설정 가져오기 (복원)",
        
        # Engineering Tab
        "auto_fix": "AI 백그라운드 자동 보정 활성화 (API 필요)",
        "show_monitor": "모니터 창 표시",
        "auto_gen_variants": "동음이의어 자동 생성 (개발)",
    },
    "zh-HK": {
        "title": "AI 語音助手設定 (Build [A1002])",
        "tab_settings": "⚡ 設定",
        "tab_magic": "🪄 魔法選單",
        "tab_pro": "💎 Pro",
        "tab_engineering": "🔧 工程",
        "save": "💾 儲存設定",
        "close": "❌ 關閉",
        "save_success": "✅ 設定已儲存",
        "save_restart_msg": "語言設定將於下次啟動時生效。",
        "settings_tray": "⚙️ 設定",
        "exit_tray": "❌ 退出",
        
        # Settings Tab
        "core_settings": "🧠 啟動與核心設定",
        "auto_start": "隨電腦開機自動啟動助手",
        "smart_left": "🖱️ 啟用左鍵長按啟動語音輸入",
        "smart_right": "🔮 啟用右鍵長按顯示魔法選單",
        "use_punc": "啟用自動輸入標點",
        
        "trigger_modes": "📡 語音輸入觸發模式",
        "recording_mode": "錄音觸發方式：",
        "smart_hold_time": "啟動久按時間",
        "mode_ptt": "📞 對講機模式",
        "mode_toggle_1": "🔘 開關模式 (久按開/停止發話關)",
        "mode_toggle_2": "🔘 開關模式 (久按開/久按關)",
        "output_instant": "🚀 極速貼上",
        "output_typewriter": "🎹 打字機模式",
        "mic_lbl": "🎙️ 麥克風:",
        "mic_tooltip": "選擇語音輸入的麥克風裝置",
        "refresh_tooltip": "重新整理麥克風清單",
        
        "hotkey_settings": "快速鍵語音輸入設定",
        "start_voice": "啟動語音輸入：",
        "start_magic": "啟動魔法選單：",
        "modify_keys": "🔧 修改按鍵組合",
        
        "style_settings": "啟動語音輸入風格",
        "sound_cue": "音效提醒風格：",
        "ui_cue": "圖像提醒風格：",
        "bubble_pos": "📍 調整氣泡球固定位置",
        "vis_style_none": "🫥 無提醒",
        "vis_style_fixed": "💬 固定位置氣泡提醒",
        "vis_style_follow": "✨ 跟隨遊標位置氣泡提醒",
        
        "lang_settings": "🌐 語言與介面設定",
        "asr_lang": "語音辨識語言：",
        "ui_lang": "介面顯示語言：",
        "restart_hint": "* (變更語言需重啟軟體生效)",
        
        # Magic Menu Tab
        "menu_mgmt": "選單管理 (≡ 拖拽排序 / 勾選隱藏):",
        "add_custom": "➕ 新增自定義按鈕",
        
        # Pro Tab
        "api_key": "Gemini API Key:",
        "opt_model": "✨ 1. 提示詞優化模型:",
        "vis_model": "📸 2. 截圖翻譯模型:",
        "fix_model": "🧠 3. 語音聽寫糾正模型:",
        "query_models": "🔍 查詢模型清單",
        "ai_option": "AI 修改方案:",
        "add_scheme": "➕ 新增方案",
        "del_scheme": "➖ 刪除方案",
        "edit_prompt": "編輯提示詞內容:",
        "export_all": "📤 匯出全部設定 (備份)",
        "import_all": "📥 匯入全部設定 (還原)",
        
        # Engineering Tab
        "auto_fix": "啟用 AI 背景自動糾錯 (需 API)",
        "show_monitor": "顯示監控視窗",
        "auto_gen_variants": "手動新增個人詞庫時，自動新增同音字變體 (工程)",
    }
}

class Localizer:
    _instance = None
    
    @staticmethod
    def get_instance():
        if Localizer._instance is None:
            Localizer._instance = Localizer()
        return Localizer._instance
        
    def __init__(self):
        self.language = "zh-TW"
        self.load_lang_from_config()
        
    def load_lang_from_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.language = config.get("ui_language", "zh-TW")
            except Exception as e:
                logger.warning(f"Failed to load language config: {e}")
                self.language = "zh-TW"
        if self.language not in TRANSLATIONS:
            self.language = "zh-TW"
            
    def t(self, key, default=""):
        lang_dict = TRANSLATIONS.get(self.language, TRANSLATIONS["zh-TW"])
        return lang_dict.get(key, default)
