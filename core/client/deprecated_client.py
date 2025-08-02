#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
レガシークライアント（非推奨）

⚠️ DEPRECATED: このファイルは非推奨です。
新しいモジュール構成を使用してください:

推奨:
    from core.client import BlueskyClient

レガシー（非推奨）:
    from core.client import BlueskyClient as DeprecatedBlueskyClient

新しい構成では以下のようにコンポーネントが分離されています:
- core.client.facade.BlueskyClient (メインファサード)
- core.client.api_client.BlueskyApiClient (API操作)
- core.client.auth_manager.BlueskyAuthManager (認証管理)
- core.client.session_manager.BlueskySessionManager (セッション管理)
- core.client.user_manager.BlueskyUserManager (ユーザー管理)
- core.client.error_handler.BlueskyErrorHandler (エラーハンドリング)

移行ガイド:
1. 既存のコードは変更不要（ファサードが互換性を保持）
2. 新しい機能にはファサード経由でアクセス
3. 特定のコンポーネントのみ必要な場合は個別にインポート可能

"""

import warnings
from core.client.facade import BlueskyClient as _RefactoredBlueskyClient

# 非推奨警告を発行
warnings.warn(
    "core.client.deprecated_client is deprecated. "
    "Use 'from core.client import BlueskyClient' instead.",
    DeprecationWarning,
    stacklevel=2
)

# 後方互換性のためのエイリアス
BlueskyClient = _RefactoredBlueskyClient

# 非推奨の例外クラス（移行のため）
class AuthenticationError(Exception):
    """認証エラーを表す例外クラス（非推奨）
    
    新しい実装では core.exceptions.AuthenticationError を使用してください。
    """
    pass