#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
契約テストパッケージ

このパッケージには、SSkyアプリケーションの各コンポーネント間の
契約テスト（Contract Tests）が含まれています。

契約テストは、以下の項目を検証します：
- APIインターフェースの準拠性
- データ形式の整合性
- 依存関係の契約遵守
- プロトコル仕様の遵守
"""

__version__ = "1.0.0"
__author__ = "SSky Development Team"

# 契約テスト用の共通定数
CONTRACT_TEST_CONFIG = {
    "api_contracts": {
        "bluesky_api": True,
        "atproto_protocol": True,
        "internal_api": True
    },
    "data_contracts": {
        "database_schema": True,
        "json_formats": True,
        "configuration_schema": True
    },
    "interface_contracts": {
        "gui_backend": True,
        "component_interfaces": True,
        "event_contracts": True
    }
}

# 契約テスト用のマーカー定義
CONTRACT_MARKERS = [
    "contract_api",        # API契約テスト
    "contract_data",       # データ契約テスト
    "contract_interface",  # インターフェース契約テスト
    "contract_protocol",   # プロトコル契約テスト
    "contract_schema"      # スキーマ契約テスト
]

# 契約検証レベル
CONTRACT_VERIFICATION_LEVELS = {
    "strict": "厳密な契約検証",
    "standard": "標準的な契約検証", 
    "lenient": "寛容な契約検証"
}