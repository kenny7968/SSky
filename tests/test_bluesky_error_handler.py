#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
BlueskyErrorHandlerモジュールのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client.error_handler import BlueskyErrorHandler
from core.exceptions import AuthenticationError
from atproto.exceptions import AtProtocolError

class TestBlueskyErrorHandler(unittest.TestCase):
    """BlueskyErrorHandlerのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = MagicMock()
        self.auth_manager.is_logged_in = True
        self.auth_manager.profile = MagicMock()
        self.error_handler = BlueskyErrorHandler(self.auth_manager)
        
    def test_init(self):
        """初期化のテスト"""
        error_handler = BlueskyErrorHandler()
        self.assertIsNone(error_handler.auth_manager)
        
    def test_handle_api_error_auth_error(self):
        """認証エラーの処理テスト"""
        # テストデータ
        auth_error = AtProtocolError("Authentication failed")
        
        # テスト実行
        result = self.error_handler.handle_api_error(auth_error, "テスト操作")
        
        # 検証
        self.assertTrue(result)  # 再ログインが必要
        self.assertFalse(self.auth_manager.is_logged_in)
        self.assertIsNone(self.auth_manager.profile)
        
    def test_handle_api_error_non_auth_error(self):
        """非認証エラーの処理テスト"""
        # テストデータ
        non_auth_error = AtProtocolError("Network error")
        
        # テスト実行
        result = self.error_handler.handle_api_error(non_auth_error, "テスト操作")
        
        # 検証
        self.assertFalse(result)  # 再ログインは不要
        
    def test_handle_api_error_non_atprotocol_error(self):
        """AtProtocolError以外のエラー処理テスト"""
        # テストデータ
        other_error = ValueError("Some other error")
        
        # テスト実行
        result = self.error_handler.handle_api_error(other_error, "テスト操作")
        
        # 検証
        self.assertFalse(result)  # 再ログインは不要
        
    def test_is_authentication_error_auth_keywords(self):
        """認証エラー判定テスト（認証キーワード）"""
        auth_errors = [
            AtProtocolError("auth failed"),
            AtProtocolError("Authentication required"),
            AtProtocolError("Unauthorized access"),
            AtProtocolError("invalid_token"),
            AtProtocolError("Token_expired"),
            AtProtocolError("Session_expired"),
            AtProtocolError("Invalid_session"),
            AtProtocolError("Access_denied"),
            AtProtocolError("Forbidden")
        ]
        
        for error in auth_errors:
            with self.subTest(error=str(error)):
                result = self.error_handler._is_authentication_error(error)
                self.assertTrue(result)
                
    def test_is_authentication_error_non_auth_keywords(self):
        """認証エラー判定テスト（非認証キーワード）"""
        non_auth_errors = [
            AtProtocolError("Network error"),
            AtProtocolError("Server timeout"),
            AtProtocolError("Invalid request"),
            AtProtocolError("Rate limit exceeded")
        ]
        
        for error in non_auth_errors:
            with self.subTest(error=str(error)):
                result = self.error_handler._is_authentication_error(error)
                self.assertFalse(result)
                
    def test_handle_with_auth_check_success(self):
        """認証チェック付き実行成功のテスト"""
        # モック関数
        mock_func = MagicMock(return_value="success")
        
        # テスト実行
        result = self.error_handler.handle_with_auth_check(
            mock_func, "arg1", "arg2", operation_name="テスト操作", kwarg1="value1"
        )
        
        # 検証
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1")
        self.assertEqual(result, "success")
        
    def test_handle_with_auth_check_auth_error(self):
        """認証チェック付き実行認証エラーのテスト"""
        # モック関数（認証エラーを発生）
        mock_func = MagicMock(side_effect=AtProtocolError("auth failed"))
        
        # テスト実行
        with self.assertRaises(AuthenticationError) as context:
            self.error_handler.handle_with_auth_check(mock_func, operation_name="テスト操作")
        
        # 検証
        self.assertEqual(str(context.exception), "セッションが無効になりました。再ログインが必要です。")
        
    def test_handle_with_auth_check_other_atprotocol_error(self):
        """認証チェック付き実行その他AtProtocolErrorのテスト"""
        # モック関数（非認証エラーを発生）
        mock_func = MagicMock(side_effect=AtProtocolError("network error"))
        
        # テスト実行
        with self.assertRaises(AtProtocolError):
            self.error_handler.handle_with_auth_check(mock_func, operation_name="テスト操作")
        
    def test_handle_login_required_logged_in(self):
        """ログイン必須チェック（ログイン済み）のテスト"""
        # テスト実行（例外が発生しないことを確認）
        try:
            self.error_handler.handle_login_required(self.auth_manager, "テスト操作")
        except Exception:
            self.fail("handle_login_required raised an exception unexpectedly")
            
    def test_handle_login_required_not_logged_in(self):
        """ログイン必須チェック（未ログイン）のテスト"""
        # ログイン状態を変更
        self.auth_manager.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.error_handler.handle_login_required(self.auth_manager, "テスト操作")
        
        # 検証
        self.assertEqual(str(context.exception), "テスト操作にはログインが必要です")
        
    def test_handle_login_required_no_auth_manager(self):
        """ログイン必須チェック（認証マネージャーなし）のテスト"""
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.error_handler.handle_login_required(None, "テスト操作")
        
        # 検証
        self.assertEqual(str(context.exception), "テスト操作にはログインが必要です")
        
    def test_safe_api_call_success(self):
        """安全なAPI呼び出し成功のテスト"""
        # モック関数
        mock_func = MagicMock(return_value="success")
        
        # テスト実行
        result = self.error_handler.safe_api_call(
            mock_func, "arg1", operation_name="テスト操作", require_login=True
        )
        
        # 検証
        mock_func.assert_called_once_with("arg1")
        self.assertEqual(result, "success")
        
    def test_safe_api_call_no_login_required(self):
        """安全なAPI呼び出し（ログイン不要）のテスト"""
        # ログイン状態を変更
        self.auth_manager.is_logged_in = False
        
        # モック関数
        mock_func = MagicMock(return_value="success")
        
        # テスト実行
        result = self.error_handler.safe_api_call(
            mock_func, "arg1", operation_name="テスト操作", require_login=False
        )
        
        # 検証
        mock_func.assert_called_once_with("arg1")
        self.assertEqual(result, "success")
        
    def test_safe_api_call_login_required_not_logged_in(self):
        """安全なAPI呼び出し（ログイン必須、未ログイン）のテスト"""
        # ログイン状態を変更
        self.auth_manager.is_logged_in = False
        
        # モック関数
        mock_func = MagicMock()
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.error_handler.safe_api_call(
                mock_func, operation_name="テスト操作", require_login=True
            )
        
        # 検証
        self.assertEqual(str(context.exception), "テスト操作にはログインが必要です")
        mock_func.assert_not_called()
        
    def test_retry_on_auth_error_success_first_try(self):
        """認証エラー再試行（初回成功）のテスト"""
        # モック関数
        mock_func = MagicMock(return_value="success")
        
        # テスト実行
        result = self.error_handler.retry_on_auth_error(mock_func, 2, "arg1")
        
        # 検証
        mock_func.assert_called_once_with("arg1")
        self.assertEqual(result, "success")
        
    def test_retry_on_auth_error_success_second_try(self):
        """認証エラー再試行（2回目成功）のテスト"""
        # モック関数（1回目は認証エラー、2回目は成功）
        mock_func = MagicMock(side_effect=[AuthenticationError("auth failed"), "success"])
        
        # テスト実行
        result = self.error_handler.retry_on_auth_error(mock_func, 2, "arg1")
        
        # 検証
        self.assertEqual(mock_func.call_count, 2)
        self.assertEqual(result, "success")
        
    def test_retry_on_auth_error_max_retries_exceeded(self):
        """認証エラー再試行（最大再試行回数超過）のテスト"""
        # モック関数（常に認証エラー）
        mock_func = MagicMock(side_effect=AuthenticationError("auth failed"))
        
        # テスト実行
        with self.assertRaises(AuthenticationError):
            self.error_handler.retry_on_auth_error(mock_func, 1, "arg1")
        
        # 検証
        self.assertEqual(mock_func.call_count, 2)  # 初回 + 1回の再試行
        
    def test_retry_on_auth_error_non_auth_error(self):
        """認証エラー再試行（非認証エラー）のテスト"""
        # モック関数（非認証エラー）
        mock_func = MagicMock(side_effect=ValueError("other error"))
        
        # テスト実行
        with self.assertRaises(ValueError):
            self.error_handler.retry_on_auth_error(mock_func, 2, "arg1")
        
        # 検証
        mock_func.assert_called_once_with("arg1")  # 再試行なし
        
    def test_create_error_context(self):
        """エラーコンテキスト作成のテスト"""
        # テスト実行
        context = self.error_handler.create_error_context(
            "テスト操作", user="test_user", action="test_action"
        )
        
        # 検証
        self.assertEqual(context['operation'], "テスト操作")
        self.assertIn('timestamp', context)
        self.assertEqual(context['context']['user'], "test_user")
        self.assertEqual(context['context']['action'], "test_action")

if __name__ == '__main__':
    unittest.main()