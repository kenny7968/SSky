#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
統一エラーハンドラーのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import wx
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.error_handler import UnifiedErrorHandler as ErrorHandler, ErrorLevel
from core.exceptions import SSkyError, AuthenticationError, ValidationError, BlueskyAPIError

class TestErrorHandler(unittest.TestCase):
    """統一エラーハンドラーのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.mock_parent = MagicMock()
        self.mock_status_bar = MagicMock()
        self.mock_status_bar.SetStatusText = MagicMock()
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_error_with_exception(self, mock_logger, mock_msgbox):
        """例外を使ったエラー処理のテスト"""
        error = ValueError("テストエラー")
        
        ErrorHandler.handle_error(
            error,
            "テスト操作",
            self.mock_parent,
            show_dialog=True,
            level=ErrorLevel.ERROR,
            log_traceback=True
        )
        
        # ログが記録されることを確認
        mock_logger.error.assert_called_once_with(
            "テスト操作エラー: テストエラー",
            exc_info=True
        )
        
        # ダイアログが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "テスト操作に失敗しました: テストエラー",
            "エラー",
            wx.OK | wx.ICON_ERROR,
            self.mock_parent
        )
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_error_with_string(self, mock_logger, mock_msgbox):
        """文字列を使ったエラー処理のテスト"""
        error_msg = "テストエラーメッセージ"
        
        ErrorHandler.handle_error(
            error_msg,
            "テスト操作",
            self.mock_parent,
            show_dialog=True,
            level=ErrorLevel.WARNING,
            log_traceback=False
        )
        
        # ログが記録されることを確認
        mock_logger.warning.assert_called_once_with("テスト操作エラー: テストエラーメッセージ")
        
        # ダイアログが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "テスト操作に失敗しました: テストエラーメッセージ",
            "警告",
            wx.OK | wx.ICON_WARNING,
            self.mock_parent
        )
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_error_no_dialog(self, mock_logger, mock_msgbox):
        """ダイアログ非表示のテスト"""
        error = Exception("テストエラー")
        
        ErrorHandler.handle_error(
            error,
            "テスト操作",
            self.mock_parent,
            show_dialog=False,
            level=ErrorLevel.ERROR
        )
        
        # ログが記録されることを確認
        mock_logger.error.assert_called_once()
        
        # ダイアログが表示されないことを確認
        mock_msgbox.assert_not_called()
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_api_error_atprotocol(self, mock_logger, mock_msgbox):
        """AT Protocol APIエラーのテスト"""
        # AtProtocolErrorの模擬クラス
        class MockAtProtocolError(Exception):
            pass
        
        error = MockAtProtocolError("API Error")
        error.__class__.__name__ = "AtProtocolError"
        
        ErrorHandler.handle_api_error(
            error,
            "API操作",
            self.mock_parent
        )
        
        # エラーが正しく処理されることを確認
        mock_logger.error.assert_called_once()
        mock_msgbox.assert_called_once()
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_api_error_network(self, mock_logger, mock_msgbox):
        """ネットワークエラーのテスト"""
        class MockConnectionError(Exception):
            pass
        
        error = MockConnectionError("Connection failed")
        error.__class__.__name__ = "ConnectionError"
        
        ErrorHandler.handle_api_error(
            error,
            "ネットワーク操作",
            self.mock_parent
        )
        
        # 警告ログが記録されることを確認
        mock_logger.warning.assert_called_once()
        
        # 適切なメッセージが表示されることを確認
        args, kwargs = mock_msgbox.call_args
        self.assertIn("ネットワーク接続に問題があります", args[0])
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_validation_error(self, mock_logger, mock_msgbox):
        """バリデーションエラーのテスト"""
        ErrorHandler.handle_validation_error(
            "入力値が無効です",
            "バリデーション",
            self.mock_parent
        )
        
        # 警告ログが記録されることを確認
        mock_logger.warning.assert_called_once_with("バリデーションエラー: 入力値が無効です")
        
        # 警告ダイアログが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "バリデーションに失敗しました: 入力値が無効です",
            "警告",
            wx.OK | wx.ICON_WARNING,
            self.mock_parent
        )
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_success_with_dialog(self, mock_logger, mock_msgbox):
        """成功メッセージ（ダイアログ表示）のテスト"""
        ErrorHandler.handle_success(
            "操作が成功しました",
            "成功",
            self.mock_parent,
            show_dialog=True
        )
        
        # 情報ログが記録されることを確認
        mock_logger.info.assert_called_once_with("操作が成功しました")
        
        # 成功ダイアログが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "操作が成功しました",
            "成功",
            wx.OK | wx.ICON_INFORMATION
        )
    
    @patch('utils.error_handler.wx.MessageBox')
    @patch('utils.error_handler.logger')
    def test_handle_success_with_status_bar(self, mock_logger, mock_msgbox):
        """成功メッセージ（ステータスバー更新）のテスト"""
        ErrorHandler.handle_success(
            "操作が成功しました",
            "成功",
            self.mock_parent,
            show_dialog=False,
            status_bar=self.mock_status_bar
        )
        
        # 情報ログが記録されることを確認
        mock_logger.info.assert_called_once_with("操作が成功しました")
        
        # ダイアログが表示されないことを確認
        mock_msgbox.assert_not_called()
        
        # ステータスバーが更新されることを確認
        self.mock_status_bar.SetStatusText.assert_called_once_with("操作が成功しました")
    
    @patch('utils.error_handler.logger')
    def test_update_status_bar_success(self, mock_logger):
        """ステータスバー更新（成功）のテスト"""
        ErrorHandler.update_status_bar(
            self.mock_status_bar,
            "操作が完了しました",
            success=True
        )
        
        # ステータスバーが更新されることを確認
        self.mock_status_bar.SetStatusText.assert_called_once_with("操作が完了しました")
        
        # デバッグログが記録されることを確認
        mock_logger.debug.assert_called_once_with("ステータスバー更新: 操作が完了しました")
    
    @patch('utils.error_handler.logger')
    def test_update_status_bar_error(self, mock_logger):
        """ステータスバー更新（エラー）のテスト"""
        ErrorHandler.update_status_bar(
            self.mock_status_bar,
            "操作に失敗しました",
            success=False
        )
        
        # ステータスバーが更新されることを確認
        self.mock_status_bar.SetStatusText.assert_called_once_with("操作に失敗しました")
        
        # 警告ログが記録されることを確認
        mock_logger.warning.assert_called_once_with("ステータスバー更新（エラー）: 操作に失敗しました")
    
    def test_update_status_bar_no_status_bar(self):
        """ステータスバーがない場合のテスト"""
        # ステータスバーがNoneの場合
        ErrorHandler.update_status_bar(None, "テストメッセージ")
        
        # ステータスバーがSetStatusTextメソッドを持たない場合
        invalid_status_bar = MagicMock()
        del invalid_status_bar.SetStatusText
        ErrorHandler.update_status_bar(invalid_status_bar, "テストメッセージ")
        
        # 例外が発生しないことを確認（このテストが通れば正常）
        self.assertTrue(True)
    
    @patch('utils.error_handler.wx.MessageBox')
    def test_show_error_dialog_different_levels(self, mock_msgbox):
        """異なるエラーレベルでのダイアログ表示テスト"""
        # 情報レベル
        ErrorHandler._show_error_dialog("情報メッセージ", ErrorLevel.INFO.value, self.mock_parent)
        mock_msgbox.assert_called_with("情報メッセージ", "情報", wx.OK | wx.ICON_INFORMATION, self.mock_parent)
        
        # 警告レベル
        ErrorHandler._show_error_dialog("警告メッセージ", ErrorLevel.WARNING.value, self.mock_parent)
        mock_msgbox.assert_called_with("警告メッセージ", "警告", wx.OK | wx.ICON_WARNING, self.mock_parent)
        
        # エラーレベル
        ErrorHandler._show_error_dialog("エラーメッセージ", ErrorLevel.ERROR.value, self.mock_parent)
        mock_msgbox.assert_called_with("エラーメッセージ", "エラー", wx.OK | wx.ICON_ERROR, self.mock_parent)

if __name__ == '__main__':
    unittest.main()