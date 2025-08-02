#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
エラーハンドリングを担当するクラス
"""

import logging
import typing
from atproto.exceptions import AtProtocolError
from core.exceptions import AuthenticationError

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyErrorHandler:
    """エラー処理を統一的に担当するクラス
    
    API呼び出し時のエラー処理、認証エラーの判定、
    再試行ロジックなどを統合的に管理します。
    """
    
    def __init__(self, auth_manager=None):
        """初期化
        
        Args:
            auth_manager (BlueskyAuthManager, optional): 認証管理インスタンス
        """
        self.auth_manager = auth_manager
        
    def handle_api_error(self, error, operation_name="API操作"):
        """API呼び出し時のエラーを処理
        
        Args:
            error: 発生したエラー
            operation_name: 操作の名前（エラーメッセージ用）
            
        Returns:
            bool: 再ログインが必要な場合はTrue
        """
        if isinstance(error, AtProtocolError):
            # 認証エラーかどうかを確認
            if self._is_authentication_error(error):
                logger.error(f"{operation_name}中に認証エラーが発生しました: {str(error)}")
                
                # ログイン状態をリセット
                if self.auth_manager:
                    self.auth_manager.is_logged_in = False
                    self.auth_manager.profile = None
                
                # 再ログインが必要
                return True
        
        # その他のエラー
        logger.error(f"{operation_name}中にエラーが発生しました: {str(error)}")
        return False
    
    def _is_authentication_error(self, error):
        """認証エラーかどうかを判定
        
        Args:
            error: エラーオブジェクト
            
        Returns:
            bool: 認証エラーの場合はTrue
        """
        error_str = str(error).lower()
        auth_keywords = [
            "auth", "authentication", "unauthorized", "invalid_token",
            "token_expired", "session_expired", "invalid_session",
            "access_denied", "forbidden"
        ]
        
        return any(keyword in error_str for keyword in auth_keywords)
    
    def handle_with_auth_check(self, func, *args, operation_name=None, **kwargs):
        """認証チェック付きでAPI関数を実行
        
        Args:
            func: 実行する関数
            *args: 関数の位置引数
            operation_name: 操作名（エラーメッセージ用）
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
            
        Raises:
            AuthenticationError: 認証エラーの場合
            AtProtocolError: その他のAPIエラー
            Exception: その他のエラー
        """
        if not operation_name:
            operation_name = getattr(func, '__name__', 'API操作')
            
        try:
            return func(*args, **kwargs)
            
        except AtProtocolError as e:
            # 認証エラーかどうかを確認
            if self.handle_api_error(e, operation_name):
                # 認証エラーの場合は特別なエラーを発生させる
                raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
            # その他のAPIエラーはそのまま再発生
            raise
            
        except Exception as e:
            logger.error(f"{operation_name}中に例外が発生しました: {str(e)}", exc_info=True)
            raise
    
    def handle_login_required(self, auth_manager, operation_name="操作"):
        """ログイン必須操作のチェック
        
        Args:
            auth_manager: 認証管理インスタンス
            operation_name: 操作名
            
        Raises:
            Exception: ログインしていない場合
        """
        if not auth_manager or not auth_manager.is_logged_in:
            logger.error(f"{operation_name}に失敗しました: ログインしていません")
            raise Exception(f"{operation_name}にはログインが必要です")
    
    def safe_api_call(self, func, *args, operation_name=None, require_login=True, **kwargs):
        """安全なAPI呼び出しラッパー
        
        ログインチェック、エラーハンドリング、ログ出力を統合したラッパー関数
        
        Args:
            func: 実行する関数
            *args: 関数の位置引数
            operation_name: 操作名（エラーメッセージ用）
            require_login: ログインが必要かどうか
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
            
        Raises:
            Exception: ログインが必要なのにログインしていない場合
            AuthenticationError: 認証エラーの場合
            AtProtocolError: その他のAPIエラー
            Exception: その他のエラー
        """
        if not operation_name:
            operation_name = getattr(func, '__name__', 'API操作')
        
        # ログインチェック
        if require_login:
            self.handle_login_required(self.auth_manager, operation_name)
        
        # 操作開始ログ
        logger.info(f"{operation_name}を実行しています...")
        
        try:
            # API呼び出し実行
            result = self.handle_with_auth_check(func, *args, operation_name=operation_name, **kwargs)
            
            # 成功ログ
            logger.info(f"{operation_name}が完了しました")
            return result
            
        except Exception as e:
            # エラーログは handle_with_auth_check で出力済み
            raise
    
    def retry_on_auth_error(self, func, max_retries=1, *args, **kwargs):
        """認証エラー時の再試行処理
        
        Args:
            func: 実行する関数
            max_retries: 最大再試行回数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
            
        Raises:
            AuthenticationError: 再試行後も認証エラーが続く場合
            Exception: その他のエラー
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except AuthenticationError as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"認証エラーが発生しました。再試行します ({attempt + 1}/{max_retries + 1})")
                    # ここで再認証のロジックを追加することも可能
                    continue
                else:
                    logger.error(f"最大再試行回数 ({max_retries + 1}) に達しました")
                    raise
                    
            except Exception as e:
                # 認証エラー以外は再試行しない
                raise
        
        # このコードには到達しないはずだが、安全のため
        if last_exception:
            raise last_exception
    
    def create_error_context(self, operation_name, **context):
        """エラーコンテキスト情報を作成
        
        Args:
            operation_name: 操作名
            **context: コンテキスト情報
            
        Returns:
            dict: エラーコンテキスト情報
        """
        return {
            'operation': operation_name,
            'timestamp': logging.Formatter().formatTime(logging.makeLogRecord({})),
            'context': context
        }
    
    def log_error_with_context(self, error, operation_name, **context):
        """コンテキスト情報付きでエラーをログ出力
        
        Args:
            error: エラーオブジェクト
            operation_name: 操作名
            **context: コンテキスト情報
        """
        error_context = self.create_error_context(operation_name, **context)
        logger.error(
            f"エラーが発生しました: {str(error)}\n"
            f"操作: {error_context['operation']}\n"
            f"時刻: {error_context['timestamp']}\n"
            f"コンテキスト: {error_context['context']}",
            exc_info=True
        )