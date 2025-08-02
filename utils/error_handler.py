#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
統一エラーハンドラー
"""

import wx
import logging
from typing import Optional, Union, Any
from enum import Enum

# ロガーの設定
logger = logging.getLogger(__name__)

class ErrorLevel(Enum):
    """エラーレベル定義"""
    INFO = "情報"
    WARNING = "警告"
    ERROR = "エラー"
    CRITICAL = "重大なエラー"

class ErrorHandler:
    """統一エラーハンドリングクラス"""
    
    @staticmethod
    def handle_error(
        error: Union[Exception, str],
        operation: str = "",
        parent: Optional[wx.Window] = None,
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
            ErrorHandler._show_error_dialog(full_message, level.value, parent)
    
    @staticmethod
    def handle_api_error(
        error: Exception,
        operation: str = "",
        parent: Optional[wx.Window] = None,
        show_dialog: bool = True
    ) -> None:
        """API関連エラーの処理
        
        Args:
            error: API例外
            operation: 実行していた操作名
            parent: 親ウィンドウ
            show_dialog: ダイアログを表示するかどうか
        """
        # API例外の種類を判定
        error_type = type(error).__name__
        
        if "AtProtocolError" in error_type:
            # AT Protocol APIエラー
            ErrorHandler.handle_error(
                error, 
                operation or "API操作", 
                parent, 
                show_dialog, 
                ErrorLevel.ERROR, 
                True
            )
        elif "ConnectionError" in error_type or "NetworkError" in error_type:
            # ネットワークエラー
            ErrorHandler.handle_error(
                "ネットワーク接続に問題があります。インターネット接続を確認してください。",
                operation or "ネットワーク操作",
                parent,
                show_dialog,
                ErrorLevel.WARNING,
                True
            )
        elif "AuthenticationError" in error_type or "Unauthorized" in str(error):
            # 認証エラー
            ErrorHandler.handle_error(
                "認証に失敗しました。再ログインが必要な可能性があります。",
                operation or "認証操作",
                parent,
                show_dialog,
                ErrorLevel.ERROR,
                True
            )
        else:
            # その他のエラー
            ErrorHandler.handle_error(
                error,
                operation or "操作",
                parent,
                show_dialog,
                ErrorLevel.ERROR,
                True
            )
    
    @staticmethod
    def handle_validation_error(
        message: str,
        operation: str = "",
        parent: Optional[wx.Window] = None,
        show_dialog: bool = True
    ) -> None:
        """バリデーションエラーの処理
        
        Args:
            message: エラーメッセージ
            operation: 実行していた操作名
            parent: 親ウィンドウ
            show_dialog: ダイアログを表示するかどうか
        """
        ErrorHandler.handle_error(
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
        parent: Optional[wx.Window] = None,
        show_dialog: bool = True,
        status_bar: Optional[Any] = None
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
    def _show_error_dialog(
        message: str,
        title: str,
        parent: Optional[wx.Window] = None
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
    
    @staticmethod
    def update_status_bar(
        status_bar: Any,
        message: str,
        success: bool = True
    ) -> None:
        """ステータスバーの更新
        
        Args:
            status_bar: ステータスバーオブジェクト
            message: メッセージ
            success: 成功かどうか
        """
        if status_bar and hasattr(status_bar, 'SetStatusText'):
            status_bar.SetStatusText(message)
            if success:
                logger.debug(f"ステータスバー更新: {message}")
            else:
                logger.warning(f"ステータスバー更新（エラー）: {message}")