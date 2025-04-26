#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証ハンドラのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.handlers.auth_handlers import AuthHandlers
from core.client import BlueskyClient
from core.auth.auth_manager import AuthManager

class TestAuthHandlers(unittest.TestCase):
    """AuthHandlersのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 親ウィンドウのモックを作成
        self.mock_parent = MagicMock()
        
        # クライアントのモックを作成
        self.mock_client = MagicMock(spec=BlueskyClient)
        
        # 認証マネージャーのモックを作成
        self.mock_auth_manager = MagicMock(spec=AuthManager)
        
        # AuthHandlersのインスタンスを作成
        self.auth_handlers = AuthHandlers(
            parent=self.mock_parent,
            client=self.mock_client,
            auth_manager=self.mock_auth_manager
        )
    
    def test_login_with_session_success(self):
        """セッション情報を使用したログイン成功のテスト"""
        # モックの設定
        self.mock_client.login_with_session.return_value = MagicMock(handle="test_handle")
        
        # テスト実行
        result = self.auth_handlers.login_with_session("test_session_string", "test_did")
        
        # 検証
        self.mock_client.login_with_session.assert_called_once_with("test_session_string")
        self.assertTrue(result)
    
    def test_login_with_session_failure(self):
        """セッション情報を使用したログイン失敗のテスト"""
        # モックの設定
        self.mock_client.login_with_session.side_effect = Exception("Login failed")
        
        # テスト実行
        result = self.auth_handlers.login_with_session("test_session_string", "test_did")
        
        # 検証
        self.mock_client.login_with_session.assert_called_once_with("test_session_string")
        self.assertFalse(result)
        self.mock_auth_manager.delete_session.assert_called_once_with("test_did")
    
    def test_load_session_success(self):
        """セッション情報の読み込み成功のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = ("test_session_string", "test_did")
        self.auth_handlers.login_with_session = MagicMock(return_value=True)
        
        # テスト実行
        result = self.auth_handlers.load_session()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        self.auth_handlers.login_with_session.assert_called_once_with("test_session_string", "test_did")
        self.assertTrue(result)
    
    def test_load_session_no_data(self):
        """セッション情報がない場合のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = (None, None)
        
        # テスト実行
        result = self.auth_handlers.load_session()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        self.assertFalse(result)
    
    def test_load_session_bytes_data(self):
        """バイト列のセッション情報の場合のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = (b"test_session_string", "test_did")
        self.auth_handlers.login_with_session = MagicMock(return_value=True)
        
        # テスト実行
        result = self.auth_handlers.load_session()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        # バイト列がLatin-1でデコードされていることを確認
        self.auth_handlers.login_with_session.assert_called_once_with("test_session_string", "test_did")
        self.assertTrue(result)
    
    def test_load_session_login_failure(self):
        """ログイン失敗時のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = ("test_session_string", "test_did")
        self.auth_handlers.login_with_session = MagicMock(return_value=False)
        
        # テスト実行
        result = self.auth_handlers.load_session()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        self.auth_handlers.login_with_session.assert_called_once_with("test_session_string", "test_did")
        self.assertFalse(result)
    
    @patch('wx.MessageBox')
    def test_logout_success(self, mock_message_box):
        """ログアウト成功のテスト"""
        # モックの設定
        self.mock_client.profile = MagicMock(handle="test_handle")
        self.mock_client.user_did = "test_did"
        self.mock_client.logout.return_value = True
        
        # テスト実行
        result = self.auth_handlers.on_logout(None)
        
        # 検証
        self.mock_auth_manager.delete_session.assert_called_once_with("test_did")
        self.mock_client.logout.assert_called_once()
        mock_message_box.assert_called_once()
        self.assertTrue(result)
    
    def test_logout_no_profile(self):
        """プロフィールがない場合のログアウトテスト"""
        # モックの設定
        self.mock_client.profile = None
        
        # テスト実行
        result = self.auth_handlers.on_logout(None)
        
        # 検証
        self.mock_auth_manager.delete_session.assert_not_called()
        self.mock_client.logout.assert_not_called()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
