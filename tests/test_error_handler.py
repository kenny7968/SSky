#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
エラーハンドラーの単体テスト (Phase 1 リファクタリング版)
"""

import unittest
from unittest.mock import patch, MagicMock
import logging

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.error_handler import UnifiedErrorHandler, ErrorLevel
from core.exceptions import AuthenticationError
from atproto.exceptions import AtProtocolError


class TestErrorLevel(unittest.TestCase):
    """ErrorLevelの単体テストクラス"""
    
    def test_error_level_values(self):
        """ErrorLevelの値が正しいことを確認"""
        self.assertEqual(ErrorLevel.INFO.value, "情報")
        self.assertEqual(ErrorLevel.WARNING.value, "警告")
        self.assertEqual(ErrorLevel.ERROR.value, "エラー")
        self.assertEqual(ErrorLevel.CRITICAL.value, "重大なエラー")
    
    def test_error_level_enum_members(self):
        """ErrorLevelの全メンバーが存在することを確認"""
        expected_levels = {'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        actual_levels = {level.name for level in ErrorLevel}
        self.assertEqual(actual_levels, expected_levels)


class TestUnifiedErrorHandler(unittest.TestCase):
    """UnifiedErrorHandlerの単体テストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.error_handler = UnifiedErrorHandler()
        self.mock_auth_manager = MagicMock()
        self.error_handler_with_auth = UnifiedErrorHandler(self.mock_auth_manager)
    
    def test_initialization(self):
        """初期化のテスト"""
        # 認証マネージャーなしでの初期化
        handler = UnifiedErrorHandler()
        self.assertIsNone(handler.auth_manager)
        
        # 認証マネージャーありでの初期化
        auth_manager = MagicMock()
        handler_with_auth = UnifiedErrorHandler(auth_manager)
        self.assertEqual(handler_with_auth.auth_manager, auth_manager)
    
    @patch('core.error_handler.logger')
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_with_exception(self, mock_dialog, mock_logger):
        """例外オブジェクトでのエラー処理テスト"""
        test_exception = ValueError("テストエラー")
        operation = "テスト操作"
        
        UnifiedErrorHandler.handle_error(
            error=test_exception,
            operation=operation,
            show_dialog=True,
            level=ErrorLevel.ERROR
        )
        
        # ログが正しく呼ばれることを確認
        expected_log_msg = f"{operation}エラー: テストエラー"
        mock_logger.error.assert_called_once_with(expected_log_msg, exc_info=True)
        
        # ダイアログが正しく呼ばれることを確認
        expected_dialog_msg = f"{operation}に失敗しました: テストエラー"
        mock_dialog.assert_called_once_with(expected_dialog_msg, "エラー", None)
    
    @patch('core.error_handler.logger')
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_with_string(self, mock_dialog, mock_logger):
        """文字列でのエラー処理テスト"""
        error_msg = "テストエラーメッセージ"
        operation = "テスト操作"
        
        UnifiedErrorHandler.handle_error(
            error=error_msg,
            operation=operation,
            show_dialog=True,
            level=ErrorLevel.WARNING
        )
        
        # ログが正しく呼ばれることを確認
        expected_log_msg = f"{operation}エラー: {error_msg}"
        mock_logger.warning.assert_called_once_with(expected_log_msg)
        
        # ダイアログが正しく呼ばれることを確認
        expected_dialog_msg = f"{operation}に失敗しました: {error_msg}"
        mock_dialog.assert_called_once_with(expected_dialog_msg, "警告", None)
    
    @patch('core.error_handler.logger')
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_without_operation(self, mock_dialog, mock_logger):
        """操作名なしでのエラー処理テスト"""
        error_msg = "テストエラーメッセージ"
        
        UnifiedErrorHandler.handle_error(
            error=error_msg,
            operation="",
            show_dialog=True,
            level=ErrorLevel.ERROR
        )
        
        # ログが正しく呼ばれることを確認
        mock_logger.error.assert_called_once_with(error_msg)
        
        # ダイアログが正しく呼ばれることを確認
        mock_dialog.assert_called_once_with(error_msg, "エラー", None)
    
    @patch('core.error_handler.logger')
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_no_dialog(self, mock_dialog, mock_logger):
        """ダイアログなしでのエラー処理テスト"""
        error_msg = "テストエラーメッセージ"
        
        UnifiedErrorHandler.handle_error(
            error=error_msg,
            operation="テスト操作",
            show_dialog=False,
            level=ErrorLevel.ERROR
        )
        
        # ログは呼ばれるがダイアログは呼ばれないことを確認
        mock_logger.error.assert_called_once()
        mock_dialog.assert_not_called()
    
    @patch('core.error_handler.logger')
    def test_handle_error_different_levels(self, mock_logger):
        """異なるエラーレベルでのログ出力テスト"""
        error_msg = "テストエラー"
        
        # INFO レベル
        UnifiedErrorHandler.handle_error(error_msg, level=ErrorLevel.INFO, show_dialog=False)
        mock_logger.info.assert_called_with(error_msg)
        
        # WARNING レベル
        mock_logger.reset_mock()
        UnifiedErrorHandler.handle_error(error_msg, level=ErrorLevel.WARNING, show_dialog=False)
        mock_logger.warning.assert_called_with(error_msg)
        
        # ERROR レベル
        mock_logger.reset_mock()
        UnifiedErrorHandler.handle_error(error_msg, level=ErrorLevel.ERROR, show_dialog=False)
        mock_logger.error.assert_called_with(error_msg)
        
        # CRITICAL レベル
        mock_logger.reset_mock()
        UnifiedErrorHandler.handle_error(error_msg, level=ErrorLevel.CRITICAL, show_dialog=False)
        mock_logger.critical.assert_called_with(error_msg)
    
    @patch('core.error_handler.logger')
    def test_handle_error_no_traceback(self, mock_logger):
        """トレースバック無効でのエラー処理テスト"""
        test_exception = ValueError("テストエラー")
        
        UnifiedErrorHandler.handle_error(
            error=test_exception,
            operation="テスト操作",
            show_dialog=False,
            level=ErrorLevel.ERROR,
            log_traceback=False
        )
        
        # exc_infoが渡されていないことを確認
        expected_log_msg = "テスト操作エラー: テストエラー"
        mock_logger.error.assert_called_once_with(expected_log_msg)
    
    @patch('wx.MessageBox')
    def test_show_error_dialog(self, mock_msgbox):
        """エラーダイアログ表示のテスト"""
        # プライベートメソッドの直接テストは通常避けるべきだが、
        # UIコンポーネントのテストでは必要
        message = "テストエラーメッセージ"
        title = "エラー"
        parent = MagicMock()
        
        UnifiedErrorHandler._show_error_dialog(message, title, parent)
        
        # MessageBoxが正しいパラメータで呼ばれることを確認
        mock_msgbox.assert_called_once_with(
            message, 
            title, 
            516,  # wx.OK | wx.ICON_ERROR の実際の値
            parent
        )
    
    @patch('wx.MessageBox')
    def test_show_error_dialog_no_parent(self, mock_msgbox):
        """親ウィンドウなしでのエラーダイアログ表示テスト"""
        message = "テストエラーメッセージ"
        title = "エラー"
        
        UnifiedErrorHandler._show_error_dialog(message, title, None)
        
        # MessageBoxが正しいパラメータで呼ばれることを確認
        mock_msgbox.assert_called_once_with(
            message, 
            title, 
            516,  # wx.OK | wx.ICON_ERROR の実際の値
            None
        )
    
    def test_handle_api_error_method_exists(self):
        """handle_api_errorメソッドが存在することを確認"""
        # メソッドが存在することを確認
        self.assertTrue(hasattr(self.error_handler, 'handle_api_error'))
        self.assertTrue(callable(getattr(self.error_handler, 'handle_api_error')))
    
    def test_handle_validation_error_method_exists(self):
        """handle_validation_errorメソッドが存在することを確認"""
        # メソッドが存在することを確認
        self.assertTrue(hasattr(UnifiedErrorHandler, 'handle_validation_error'))
        self.assertTrue(callable(getattr(UnifiedErrorHandler, 'handle_validation_error')))


class TestErrorHandlerIntegration(unittest.TestCase):
    """エラーハンドラーの統合テストクラス"""
    
    @patch('core.error_handler.logger')
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_authentication_error_handling(self, mock_dialog, mock_logger):
        """認証エラー処理の統合テスト"""
        auth_error = AuthenticationError("認証に失敗しました")
        
        UnifiedErrorHandler.handle_error(
            error=auth_error,
            operation="ログイン",
            level=ErrorLevel.ERROR
        )
        
        # 認証エラーが適切に処理されることを確認
        mock_logger.error.assert_called_once_with(
            "ログインエラー: 認証に失敗しました", 
            exc_info=True
        )
        mock_dialog.assert_called_once_with(
            "ログインに失敗しました: 認証に失敗しました", 
            "エラー", 
            None
        )
    
    @patch('core.error_handler.logger')  
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_atprotocol_error_handling(self, mock_dialog, mock_logger):
        """AtProtocolエラー処理の統合テスト"""
        api_error = AtProtocolError("API呼び出しエラー")
        
        UnifiedErrorHandler.handle_error(
            error=api_error,
            operation="API操作",
            level=ErrorLevel.ERROR
        )
        
        # AtProtocolエラーが適切に処理されることを確認
        mock_logger.error.assert_called_once_with(
            "API操作エラー: API呼び出しエラー", 
            exc_info=True
        )
        mock_dialog.assert_called_once_with(
            "API操作に失敗しました: API呼び出しエラー", 
            "エラー", 
            None
        )
    
    @patch('core.error_handler.logger')
    def test_error_handler_with_none_error(self, mock_logger):
        """Noneエラーでの処理テスト"""
        # None エラーは通常発生しないが、防御的プログラミングのためのテスト
        # 実装では None も文字列として扱われるため、エラーにならない
        with patch('wx.MessageBox'):
            result = UnifiedErrorHandler.handle_error(
                error=None,
                operation="テスト操作",
                show_dialog=False
            )
            # エラーハンドリングされることを確認
            self.assertIsNone(result)  # handle_error は None を返す


if __name__ == '__main__':
    unittest.main(verbosity=2)