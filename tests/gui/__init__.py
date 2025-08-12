#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
GUIテストパッケージ

このパッケージには、SSkyアプリケーションのGUI関連テストが含まれています。
wxPythonベースのユーザーインターフェースのテスト、アクセシビリティテスト、
画面読み上げソフト対応のテストなどが含まれます。
"""

__version__ = "1.0.0"
__author__ = "SSky Development Team"

# GUIテスト用の共通定数
GUI_TEST_TIMEOUT = {
    'ui_response': 1,    # 1秒 - UI応答
    'dialog_show': 2,    # 2秒 - ダイアログ表示
    'accessibility': 5,  # 5秒 - アクセシビリティ機能
    'rendering': 3       # 3秒 - レンダリング
}

# GUIテスト用のマーカー定義
GUI_MARKERS = [
    "gui_smoke",         # GUIスモークテスト
    "gui_integration",   # GUI統合テスト
    "gui_accessibility", # アクセシビリティテスト
    "gui_dialog",        # ダイアログテスト
    "gui_timeline",      # タイムラインテスト
]

# アクセシビリティテスト用設定
ACCESSIBILITY_CONFIG = {
    "screen_reader_support": True,
    "keyboard_navigation": True,
    "high_contrast": True,
    "font_scaling": True,
    "focus_management": True
}

# wxPython モック設定
WX_MOCK_CONFIG = {
    "simulate_events": True,
    "mock_dialogs": True,
    "mock_controls": True,
    "accessibility_hooks": True
}