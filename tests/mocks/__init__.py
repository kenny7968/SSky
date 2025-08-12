#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
共通モックパッケージ

このパッケージには、テスト全体で使用される共通のモッククラス、
モックデータ、モック設定が含まれています。
"""

__version__ = "1.0.0"
__author__ = "SSky Development Team"

# 共通モック設定
MOCK_CONFIG = {
    "api_client": {
        "enable_network_simulation": True,
        "default_timeout": 5.0,
        "rate_limit_simulation": True
    },
    "database": {
        "use_memory_db": True,
        "enable_transaction_rollback": True,
        "simulate_connection_errors": False
    },
    "wxpython": {
        "enable_event_simulation": True,
        "mock_system_dialogs": True,
        "accessibility_hooks": True
    },
    "file_system": {
        "use_temp_files": True,
        "simulate_permissions": True,
        "cleanup_after_test": True
    }
}

# モックデータ設定
MOCK_DATA_CONFIG = {
    "user_profiles": {
        "test_users": 10,
        "include_japanese_names": True,
        "include_edge_cases": True
    },
    "posts": {
        "sample_count": 50,
        "include_media": True,
        "include_replies": True,
        "include_reposts": True
    },
    "api_responses": {
        "include_errors": True,
        "include_rate_limits": True,
        "include_timeouts": True
    }
}