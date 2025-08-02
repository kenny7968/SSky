#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
カスタム例外クラス定義
"""

class SSkyError(Exception):
    """SSkyアプリケーションの基底例外クラス"""
    pass

class AuthenticationError(SSkyError):
    """認証関連エラー"""
    pass

class ValidationError(SSkyError):
    """バリデーションエラー"""
    pass

class NetworkError(SSkyError):
    """ネットワーク関連エラー"""
    pass

class BlueskyAPIError(SSkyError):
    """Bluesky API関連エラー"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        """初期化
        
        Args:
            message: エラーメッセージ
            status_code: HTTPステータスコード
            response_data: APIレスポンスデータ
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class SessionError(AuthenticationError):
    """セッション関連エラー"""
    pass

class PostError(SSkyError):
    """投稿関連エラー"""
    pass

class DataStoreError(SSkyError):
    """データストア関連エラー"""
    pass

class ConfigurationError(SSkyError):
    """設定関連エラー"""
    pass