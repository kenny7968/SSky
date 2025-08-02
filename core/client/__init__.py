#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
クライアントパッケージ初期化
"""

from core.client.facade import BlueskyClient
from core.client.api_client import BlueskyApiClient
from core.client.auth_manager import BlueskyAuthManager
from core.client.session_manager import BlueskySessionManager
from core.client.user_manager import BlueskyUserManager
from core.error_handler import UnifiedErrorHandler as BlueskyErrorHandler

# バージョン情報
__version__ = '0.2.0'

# エクスポートするクラス
__all__ = [
    'BlueskyClient',           # メインファサード（推奨）
    'BlueskyApiClient',        # API操作
    'BlueskyAuthManager',      # 認証管理
    'BlueskySessionManager',   # セッション管理
    'BlueskyUserManager',      # ユーザー管理
    'BlueskyErrorHandler',     # エラーハンドリング
]