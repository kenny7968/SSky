#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
統合エラーハンドラー（リファクタリング版）
"""

import wx
import logging
import typing
from enum import Enum
from atproto.exceptions import AtProtocolError
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

class ErrorLevel(Enum):
    """エラーレベル定義"""
    INFO = "情報"
    WARNING = "警告"
    ERROR = "エラー"
    CRITICAL = "重大なエラー"

class UnifiedErrorHandler:
    """統合エラーハンドリングクラス（リファクタリング版）
    
    責任:
    - API関連エラーの統一処理
    - 認証エラーの判定と処理
    - UIエラーダイアログの表示
    - エラーログの統一出力
    - 再試行ロジックの提供
    """
    
    def __init__(self, auth_manager=None):
        """初期化
        
        Args:
            auth_manager (BlueskyAuthManager, optional): 認証管理インスタンス
        """
        self.auth_manager = auth_manager
    
    @staticmethod
    def handle_error(
        error: typing.Union[Exception, str],
        operation: str = "",
        parent: typing.Optional[wx.Window] = None,
        show_dialog: bool = True,
        level: ErrorLevel = ErrorLevel.ERROR,
        log_traceback: bool = True
    ) -> None:
        """統一エラー処理
        
        Args:
            error: エラー情報（Exception または文字列）
            operation: 実行していた操作名
            parent: 親ウィンドウ（MessageBox表示用）
            show_dialog: ダイアログを表示するかどうか
            level: エラーレベル
            log_traceback: トレースバックをログに記録するかどうか
        """
        # エラーメッセージの構築
        if isinstance(error, Exception):
            error_msg = str(error)
        else:
            error_msg = error
        
        # 操作名を含むメッセージの作成
        if operation:
            full_message = f"{operation}に失敗しました: {error_msg}"
            log_message = f"{operation}エラー: {error_msg}"
        else:
            full_message = error_msg
            log_message = error_msg
        
        # ログに記録
        if level == ErrorLevel.INFO:
            logger.info(log_message)
        elif level == ErrorLevel.WARNING:
            logger.warning(log_message)
        elif level == ErrorLevel.ERROR:
            if log_traceback and isinstance(error, Exception):
                logger.error(log_message, exc_info=True)
            else:
                logger.error(log_message)
        elif level == ErrorLevel.CRITICAL:
            if log_traceback and isinstance(error, Exception):
                logger.critical(log_message, exc_info=True)
            else:
                logger.critical(log_message)
        
        # ダイアログ表示
        if show_dialog:
            UnifiedErrorHandler._show_error_dialog(full_message, level.value, parent)
    
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
            if self.is_authentication_error(error):
                logger.error(f"{operation_name}中に認証エラーが発生しました: {str(error)}")
                
                # ログイン状態をリセット
                if self.auth_manager:
                    self.auth_manager.handle_authentication_error(error, operation_name)
                
                return True
        
        # その他のエラー
        logger.error(f"{operation_name}中にエラーが発生しました: {str(error)}")
        return False
    
    def is_authentication_error(self, error) -> bool:
        """エラーが認証関連かどうかを判定
        
        Args:
            error: 発生したエラー
            
        Returns:
            bool: 認証エラーの場合はTrue
        """
        if isinstance(error, AtProtocolError):
            error_str = str(error).lower()
            auth_keywords = [
                "auth", "authentication", "unauthorized", "invalid_token",
                "token_expired", "session_expired", "invalid_session",
                "access_denied", "forbidden"
            ]
            return any(keyword in error_str for keyword in auth_keywords)
        
        if isinstance(error, AuthenticationError):
            return True
            
        return False
    
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
        if require_login and self.auth_manager:
            if not self.auth_manager.is_logged_in:
                logger.error(f"{operation_name}に失敗しました: ログインしていません")
                raise Exception(f"{operation_name}にはログインが必要です")
        
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
    
    @staticmethod
    def handle_validation_error(
        message: str,
        operation: str = "",
        parent: typing.Optional[wx.Window] = None,
        show_dialog: bool = True
    ) -> None:
        """バリデーションエラーの処理
        
        Args:
            message: エラーメッセージ
            operation: 実行していた操作名
            parent: 親ウィンドウ
            show_dialog: ダイアログを表示するかどうか
        """
        UnifiedErrorHandler.handle_error(
            message,
            operation,
            parent,
            show_dialog,
            ErrorLevel.WARNING,
            False  # バリデーションエラーはトレースバック不要
        )
    
    @staticmethod
    def handle_success(
        message: str,
        title: str = "完了",
        parent: typing.Optional[wx.Window] = None,
        show_dialog: bool = True,
        status_bar: typing.Optional[typing.Any] = None
    ) -> None:
        """成功メッセージの処理
        
        Args:
            message: 成功メッセージ
            title: ダイアログタイトル
            parent: 親ウィンドウ
            show_dialog: ダイアログを表示するかどうか
            status_bar: ステータスバー（あれば更新）
        """
        logger.info(message)
        
        if show_dialog:
            wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)
        elif status_bar and hasattr(status_bar, 'SetStatusText'):
            status_bar.SetStatusText(message)
    
    @staticmethod
    def update_status_bar(
        status_bar: typing.Optional[typing.Any],
        message: str,
        success: bool = True
    ) -> None:
        """ステータスバーの更新
        
        Args:
            status_bar: ステータスバーオブジェクト
            message: 表示するメッセージ
            success: 成功かどうか
        """
        try:
            if status_bar and hasattr(status_bar, 'SetStatusText'):
                status_bar.SetStatusText(message)
                if success:
                    logger.debug(f"ステータスバー更新: {message}")
                else:
                    logger.warning(f"ステータスバー更新（エラー）: {message}")
            else:
                logger.debug(f"ステータスバーが利用できません（メッセージ: {message}）")
        except Exception as e:
            logger.warning(f"ステータスバーの更新に失敗しました: {str(e)}")
    
    @staticmethod
    def _show_error_dialog(
        message: str,
        title: str,
        parent: typing.Optional[wx.Window] = None
    ) -> None:
        """エラーダイアログの表示
        
        Args:
            message: エラーメッセージ
            title: ダイアログタイトル
            parent: 親ウィンドウ
        """
        # アイコンの選択
        if title == ErrorLevel.INFO.value:
            icon = wx.ICON_INFORMATION
        elif title == ErrorLevel.WARNING.value:
            icon = wx.ICON_WARNING
        else:  # ERROR または CRITICAL
            icon = wx.ICON_ERROR
        
        wx.MessageBox(message, title, wx.OK | icon, parent)
    
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

# 後方互換性のためのエイリアス
ErrorHandler = UnifiedErrorHandler
