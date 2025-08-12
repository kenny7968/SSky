#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
E2E（エンドツーエンド）テストパッケージ

このパッケージには、SSkyアプリケーションの完全なエンドツーエンドテストが含まれています。
"""

__version__ = "1.0.0"
__author__ = "SSky Development Team"

# E2Eテスト用の共通定数
E2E_TEST_TIMEOUT = {
    'short': 5,      # 5秒 - 基本操作
    'medium': 15,    # 15秒 - API呼び出し
    'long': 30,      # 30秒 - 複雑なシナリオ
    'very_long': 60  # 60秒 - 全体テスト
}

# E2Eテスト用のマーカー定義
E2E_MARKERS = [
    "e2e_smoke",  # スモークテスト
    "e2e_full",   # フルテスト
    "e2e_gui",    # GUI関連テスト
    "e2e_api",    # API関連テスト
]