#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
クライアントモジュールのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client import BlueskyClient
from atproto.exceptions import AtProtocolError

class TestBlueskyClient(unittest.TestCase):
    """BlueskyClientのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.client = BlueskyClient()
        # ログイン状態をモック
        self.client.is_logged_in = True
        self.client.client = MagicMock()
        self.client.profile = MagicMock()
        
    def test_init(self):
        """初期化のテスト"""
        client = BlueskyClient()
        self.assertFalse(client.is_logged_in)
        self.assertIsNone(client.profile)
        
    def test_login_success(self):
        """ログイン成功のテスト"""
        # モックの設定
        client = BlueskyClient()
        mock_profile = MagicMock(display_name="Test User")
        
        with patch.object(client.auth_manager, 'login') as mock_login:
            mock_login.return_value = mock_profile
            
            # テスト実行
            result = client.login("test_user", "test_password")
            
            # 検証
            mock_login.assert_called_once_with("test_user", "test_password")
            self.assertEqual(result.display_name, "Test User")
        
    def test_login_failure(self):
        """ログイン失敗のテスト"""
        # モックの設定
        client = BlueskyClient()
        
        with patch.object(client.auth_manager, 'login') as mock_login:
            mock_login.side_effect = AtProtocolError("Login failed")
            
            # テスト実行
            with self.assertRaises(AtProtocolError):
                client.login("test_user", "test_password")
            
            # 検証
            self.assertFalse(client.is_logged_in)
        
    def test_logout(self):
        """ログアウトのテスト"""
        # テスト実行
        with patch.object(self.client.auth_manager, 'logout') as mock_logout:
            mock_logout.return_value = True
            result = self.client.logout()
            
            # 検証
            mock_logout.assert_called_once()
            self.assertTrue(result)
        
    def test_reply_to_post_with_root(self):
        """返信（ルート投稿あり）のテスト"""
        # テストデータ
        reply_to = {
            'uri': 'test_uri',
            'cid': 'test_cid',
            'reply_root': {
                'uri': 'root_uri',
                'cid': 'root_cid'
            }
        }
        
        # テスト実行
        with patch.object(self.client.api_client, 'reply_to_post') as mock_reply:
            self.client.reply_to_post("Test reply", reply_to)
            
            # 検証
            mock_reply.assert_called_once_with("Test reply", reply_to)
        
    def test_reply_to_post_with_parent(self):
        """返信（親投稿あり）のテスト"""
        # テストデータ
        reply_to = {
            'uri': 'test_uri',
            'cid': 'test_cid',
            'reply_parent': {
                'uri': 'parent_uri',
                'cid': 'parent_cid'
            }
        }
        
        # テスト実行
        with patch.object(self.client.api_client, 'reply_to_post') as mock_reply:
            self.client.reply_to_post("Test reply", reply_to)
            
            # 検証
            mock_reply.assert_called_once_with("Test reply", reply_to)
        
    def test_reply_to_post_no_parent_or_root(self):
        """返信（親投稿もルート投稿もなし）のテスト"""
        # テストデータ
        reply_to = {
            'uri': 'test_uri',
            'cid': 'test_cid'
        }
        
        # テスト実行
        with patch.object(self.client.api_client, 'reply_to_post') as mock_reply:
            self.client.reply_to_post("Test reply", reply_to)
            
            # 検証
            mock_reply.assert_called_once_with("Test reply", reply_to)
        
    def test_reply_to_post_not_logged_in(self):
        """未ログイン状態での返信テスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.reply_to_post("Test reply", {'uri': 'test_uri', 'cid': 'test_cid'})
        
        # 検証
        self.assertEqual(str(context.exception), "返信にはログインが必要です")
        
    def test_quote_post(self):
        """引用のテスト"""
        # テストデータ
        quote_of = {
            'uri': 'test_uri',
            'cid': 'test_cid'
        }
        
        # テスト実行
        with patch.object(self.client.api_client, 'quote_post') as mock_quote:
            self.client.quote_post("Test quote", quote_of)
            
            # 検証
            mock_quote.assert_called_once_with("Test quote", quote_of)
        
    def test_quote_post_not_logged_in(self):
        """未ログイン状態での引用テスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.quote_post("Test quote", {'uri': 'test_uri', 'cid': 'test_cid'})
        
        # 検証
        self.assertEqual(str(context.exception), "引用にはログインが必要です")
        
    def test_repost(self):
        """リポストのテスト"""
        # テストデータ
        repost_of = {
            'uri': 'test_uri',
            'cid': 'test_cid'
        }
        
        # テスト実行
        with patch.object(self.client.api_client, 'repost') as mock_repost:
            self.client.repost(repost_of)
            
            # 検証
            mock_repost.assert_called_once_with(repost_of)
        
    def test_repost_not_logged_in(self):
        """未ログイン状態でのリポストテスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.repost({'uri': 'test_uri', 'cid': 'test_cid'})
        
        # 検証
        self.assertEqual(str(context.exception), "リポストにはログインが必要です")
        
    def test_export_session_string_success(self):
        """セッション情報のエクスポート成功のテスト"""
        # テスト実行
        with patch.object(self.client.auth_manager, 'export_session_string') as mock_export:
            mock_export.return_value = "test_session_string"
            result = self.client.export_session_string()
            
            # 検証
            mock_export.assert_called_once()
            self.assertEqual(result, "test_session_string")
        
    def test_export_session_string_not_logged_in(self):
        """未ログイン状態でのセッション情報エクスポートテスト"""
        # テスト実行
        with patch.object(self.client.auth_manager, 'export_session_string') as mock_export:
            mock_export.return_value = None
            result = self.client.export_session_string()
            
            # 検証
            self.assertIsNone(result)
        
        
    def test_login_with_session_success(self):
        """セッション情報を使用したログイン成功のテスト"""
        # テスト実行
        mock_profile = MagicMock(handle="test_handle")
        with patch.object(self.client.auth_manager, 'login_with_session') as mock_login:
            mock_login.return_value = mock_profile
            
            result = self.client.login_with_session("test_session_string")
            
            # 検証
            mock_login.assert_called_once_with("test_session_string")
            self.assertEqual(result.handle, "test_handle")
        
    def test_login_with_session_failure(self):
        """セッション情報を使用したログイン失敗のテスト"""
        # テスト実行
        from core.exceptions import AuthenticationError
        with patch.object(self.client.auth_manager, 'login_with_session') as mock_login:
            mock_login.side_effect = AuthenticationError("セッションが無効になりました。再ログインが必要です。")
            
            with self.assertRaises(AuthenticationError) as context:
                self.client.login_with_session("test_session_string")
            
            # 検証
            self.assertEqual(str(context.exception), "セッションが無効になりました。再ログインが必要です。")
    
    def test_follow_success(self):
        """フォロー成功のテスト"""
        # テスト実行
        with patch.object(self.client.error_handler, 'safe_api_call') as mock_safe_call:
            mock_safe_call.return_value = MagicMock()
            result = self.client.follow("test_user")
            
            # 検証
            mock_safe_call.assert_called_once()
            self.assertIsNotNone(result)
    
    def test_follow_not_logged_in(self):
        """未ログイン状態でのフォローテスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.follow("test_user")
        
        # 検証
        self.assertEqual(str(context.exception), "フォローにはログインが必要です")
    
    def test_block_success(self):
        """ブロック成功のテスト"""
        # テスト実行
        with patch.object(self.client.error_handler, 'safe_api_call') as mock_safe_call:
            mock_safe_call.return_value = MagicMock()
            result = self.client.block("test_user")
            
            # 検証
            mock_safe_call.assert_called_once()
            self.assertIsNotNone(result)
    
    def test_block_not_logged_in(self):
        """未ログイン状態でのブロックテスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.block("test_user")
        
        # 検証
        self.assertEqual(str(context.exception), "ブロックにはログインが必要です")
    
    def test_get_following_success(self):
        """フォロー中ユーザー取得成功のテスト"""
        # テスト実行
        with patch.object(self.client.error_handler, 'handle_with_auth_check') as mock_handle:
            mock_result = MagicMock()
            mock_result.follows = [MagicMock(), MagicMock()]
            mock_handle.return_value = mock_result
            
            result = self.client.get_following("test_user", limit=50)
            
            # 検証
            mock_handle.assert_called_once()
            self.assertEqual(len(result.follows), 2)
    
    def test_get_followers_success(self):
        """フォロワー取得成功のテスト"""
        # テスト実行
        with patch.object(self.client.error_handler, 'handle_with_auth_check') as mock_handle:
            mock_result = MagicMock()
            mock_result.followers = [MagicMock(), MagicMock(), MagicMock()]
            mock_handle.return_value = mock_result
            
            result = self.client.get_followers("test_user", limit=30)
            
            # 検証
            mock_handle.assert_called_once()
            self.assertEqual(len(result.followers), 3)

if __name__ == '__main__':
    unittest.main()
