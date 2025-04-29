#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証サービスのテスト
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.handlers.auth_service import AuthService
from core.client import BlueskyClient
from core.auth.auth_manager import AuthManager
from atproto_client import Session, SessionEvent
from core import events

class TestAuthService(unittest.TestCase):
    """AuthServiceのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # クライアントのモックを作成
        self.mock_client = MagicMock(spec=BlueskyClient)
        
        # 認証マネージャーのモックを作成
        self.mock_auth_manager = MagicMock(spec=AuthManager)
        
        # pubsubのモックを作成
        self.mock_pub = MagicMock()
        
        # AuthServiceのインスタンスを作成
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            self.auth_service = AuthService(
                client=self.mock_client,
                auth_manager=self.mock_auth_manager
            )
    
    def test_handle_session_change_create(self):
        """セッション作成イベント処理のテスト"""
        # モックの設定
        mock_session = MagicMock(spec=Session)
        mock_session.did = "test_did"
        self.mock_client.export_session_string.return_value = "test_session_string"
        self.mock_auth_manager.save_session.return_value = True
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            self.auth_service._handle_session_change(SessionEvent.CREATE, mock_session)
        
        # 検証
        self.mock_client.export_session_string.assert_called_once()
        self.mock_auth_manager.save_session.assert_called_once_with("test_did", "test_session_string")
        self.mock_pub.sendMessage.assert_called_once_with(events.AUTH_SESSION_SAVED, did="test_did")
    
    def test_handle_session_change_refresh(self):
        """セッション更新イベント処理のテスト"""
        # モックの設定
        mock_session = MagicMock(spec=Session)
        mock_session.did = "test_did"
        self.mock_client.export_session_string.return_value = "test_session_string"
        self.mock_auth_manager.save_session.return_value = True
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            self.auth_service._handle_session_change(SessionEvent.REFRESH, mock_session)
        
        # 検証
        self.mock_client.export_session_string.assert_called_once()
        self.mock_auth_manager.save_session.assert_called_once_with("test_did", "test_session_string")
        self.mock_pub.sendMessage.assert_called_once_with(events.AUTH_SESSION_SAVED, did="test_did")
    
    def test_handle_session_change_import(self):
        """セッションインポートイベント処理のテスト（現在は何もしない）"""
        # モックの設定
        mock_session = MagicMock(spec=Session)
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            self.auth_service._handle_session_change(SessionEvent.IMPORT, mock_session)
        
        # 検証（何も呼ばれないはず）
        self.mock_client.export_session_string.assert_not_called()
        self.mock_auth_manager.save_session.assert_not_called()
        self.mock_pub.sendMessage.assert_not_called()
    
    def test_login_with_session_success(self):
        """セッション情報を使用したログイン成功のテスト"""
        # モックの設定
        mock_profile = MagicMock(handle="test_handle")
        self.mock_client.login_with_session.return_value = mock_profile
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.login_with_session("test_session_string", "test_did")
        
        # 検証
        self.mock_client.login_with_session.assert_called_once_with("test_session_string")
        # イベント発行の検証（順序も重要）
        expected_calls = [
            call(events.AUTH_SESSION_LOAD_ATTEMPT, did="test_did"),
            call(events.AUTH_SESSION_LOAD_SUCCESS, profile=mock_profile)
        ]
        self.mock_pub.sendMessage.assert_has_calls(expected_calls, any_order=False)
        self.assertTrue(result)
    
    def test_login_with_session_failure(self):
        """セッション情報を使用したログイン失敗のテスト"""
        # モックの設定
        self.mock_client.login_with_session.side_effect = Exception("Login failed")
        self.mock_auth_manager.delete_session.return_value = True
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.login_with_session("test_session_string", "test_did")
        
        # 検証
        self.mock_client.login_with_session.assert_called_once_with("test_session_string")
        self.assertFalse(result)
        self.mock_auth_manager.delete_session.assert_called_once_with("test_did")
        
        # イベント発行の検証（順序も重要）
        expected_calls = [
            call(events.AUTH_SESSION_LOAD_ATTEMPT, did="test_did"),
            call(events.AUTH_SESSION_INVALID, error=self.mock_client.login_with_session.side_effect, did="test_did"),
            call(events.AUTH_SESSION_DELETED, did="test_did"),
            call(events.AUTH_SESSION_LOAD_FAILURE, error=self.mock_client.login_with_session.side_effect, needs_relogin=True)
        ]
        self.mock_pub.sendMessage.assert_has_calls(expected_calls, any_order=False)
    
    def test_load_and_login_success(self):
        """セッション情報の読み込み成功のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = ("test_session_string", "test_did")
        
        # login_with_sessionをモック
        self.auth_service.login_with_session = MagicMock(return_value=True)
        
        # テスト実行
        result = self.auth_service.load_and_login()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        self.auth_service.login_with_session.assert_called_once_with("test_session_string", "test_did")
        self.assertTrue(result)
    
    def test_load_and_login_no_data(self):
        """セッション情報がない場合のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = (None, None)
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.load_and_login()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        self.mock_pub.sendMessage.assert_called_once_with(events.AUTH_SESSION_LOAD_FAILURE, error=None, needs_relogin=False)
        self.assertFalse(result)
    
    def test_load_and_login_bytes_data(self):
        """バイト列のセッション情報の場合のテスト"""
        # モックの設定
        self.mock_auth_manager.load_session.return_value = (b"test_session_string", "test_did")
        
        # login_with_sessionをモック
        self.auth_service.login_with_session = MagicMock(return_value=True)
        
        # テスト実行
        result = self.auth_service.load_and_login()
        
        # 検証
        self.mock_auth_manager.load_session.assert_called_once()
        # バイト列がデコードされていることを確認
        self.auth_service.login_with_session.assert_called_once_with("test_session_string", "test_did")
        self.assertTrue(result)
    
    def test_perform_login_success(self):
        """ログイン成功のテスト"""
        # モックの設定
        mock_profile = MagicMock(handle="test_handle")
        self.mock_client.login.return_value = mock_profile
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.perform_login("test_username", "test_password")
        
        # 検証
        self.mock_client.login.assert_called_once()
        self.mock_pub.sendMessage.assert_has_calls([
            call(events.AUTH_LOGIN_ATTEMPT),
            call(events.AUTH_LOGIN_SUCCESS, profile=mock_profile)
        ], any_order=False)
        self.assertTrue(result)
    
    def test_perform_login_failure(self):
        """ログイン失敗のテスト"""
        # モックの設定
        self.mock_client.login.side_effect = Exception("Login failed")
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.perform_login("test_username", "test_password")
        
        # 検証
        self.mock_client.login.assert_called_once()
        self.mock_pub.sendMessage.assert_has_calls([
            call(events.AUTH_LOGIN_ATTEMPT),
            call(events.AUTH_LOGIN_FAILURE, error=self.mock_client.login.side_effect)
        ], any_order=False)
        self.assertFalse(result)
    
    def test_perform_logout_success(self):
        """ログアウト成功のテスト"""
        # モックの設定
        mock_profile = MagicMock()
        mock_profile.did = "test_did"
        mock_profile.handle = "test_handle"
        self.mock_client.profile = mock_profile
        self.mock_auth_manager.delete_session.return_value = True
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.perform_logout()
        
        # 検証
        self.mock_auth_manager.delete_session.assert_called_once_with("test_did")
        self.mock_pub.sendMessage.assert_has_calls([
            call(events.AUTH_SESSION_DELETED, did="test_did"),
            call(events.AUTH_LOGOUT_SUCCESS)
        ], any_order=False)
        self.assertTrue(result)
    
    def test_perform_logout_no_profile(self):
        """プロフィールがない場合のログアウトテスト"""
        # モックの設定
        self.mock_client.profile = None
        
        # テスト実行
        with patch('gui.handlers.auth_service.pub', self.mock_pub):
            result = self.auth_service.perform_logout()
        
        # 検証
        self.mock_auth_manager.delete_session.assert_not_called()
        self.mock_pub.sendMessage.assert_called_once_with(events.AUTH_LOGOUT_SUCCESS)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
