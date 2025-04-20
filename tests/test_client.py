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
        
    @patch('core.client.AtprotoClient')
    def test_login_success(self, mock_atproto):
        """ログイン成功のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client.login.return_value = MagicMock(display_name="Test User")
        mock_atproto.return_value = mock_client
        
        # テスト実行
        client = BlueskyClient()
        result = client.login("test_user", "test_password")
        
        # 検証
        mock_client.login.assert_called_once_with("test_user", "test_password")
        self.assertTrue(client.is_logged_in)
        self.assertEqual(result.display_name, "Test User")
        
    @patch('core.client.AtprotoClient')
    def test_login_failure(self, mock_atproto):
        """ログイン失敗のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client.login.side_effect = AtProtocolError("Login failed")
        mock_atproto.return_value = mock_client
        
        # テスト実行
        client = BlueskyClient()
        with self.assertRaises(AtProtocolError):
            client.login("test_user", "test_password")
        
        # 検証
        self.assertFalse(client.is_logged_in)
        
    def test_logout(self):
        """ログアウトのテスト"""
        # テスト実行
        result = self.client.logout()
        
        # 検証
        self.assertTrue(result)
        self.assertFalse(self.client.is_logged_in)
        self.assertIsNone(self.client.profile)
        
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
        self.client.reply_to_post("Test reply", reply_to)
        
        # 検証
        self.client.client.send_post.assert_called_once()
        args, kwargs = self.client.client.send_post.call_args
        self.assertEqual(kwargs['text'], "Test reply")
        self.assertEqual(kwargs['reply_to']['parent']['uri'], 'test_uri')
        self.assertEqual(kwargs['reply_to']['parent']['cid'], 'test_cid')
        self.assertEqual(kwargs['reply_to']['root']['uri'], 'root_uri')
        self.assertEqual(kwargs['reply_to']['root']['cid'], 'root_cid')
        
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
        self.client.reply_to_post("Test reply", reply_to)
        
        # 検証
        self.client.client.send_post.assert_called_once()
        args, kwargs = self.client.client.send_post.call_args
        self.assertEqual(kwargs['text'], "Test reply")
        self.assertEqual(kwargs['reply_to']['parent']['uri'], 'test_uri')
        self.assertEqual(kwargs['reply_to']['parent']['cid'], 'test_cid')
        self.assertEqual(kwargs['reply_to']['root']['uri'], 'parent_uri')
        self.assertEqual(kwargs['reply_to']['root']['cid'], 'parent_cid')
        
    def test_reply_to_post_no_parent_or_root(self):
        """返信（親投稿もルート投稿もなし）のテスト"""
        # テストデータ
        reply_to = {
            'uri': 'test_uri',
            'cid': 'test_cid'
        }
        
        # テスト実行
        self.client.reply_to_post("Test reply", reply_to)
        
        # 検証
        self.client.client.send_post.assert_called_once()
        args, kwargs = self.client.client.send_post.call_args
        self.assertEqual(kwargs['text'], "Test reply")
        self.assertEqual(kwargs['reply_to']['parent']['uri'], 'test_uri')
        self.assertEqual(kwargs['reply_to']['parent']['cid'], 'test_cid')
        self.assertEqual(kwargs['reply_to']['root']['uri'], 'test_uri')
        self.assertEqual(kwargs['reply_to']['root']['cid'], 'test_cid')
        
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
        self.client.quote_post("Test quote", quote_of)
        
        # 検証
        self.client.client.send_post.assert_called_once()
        args, kwargs = self.client.client.send_post.call_args
        self.assertEqual(kwargs['text'], "Test quote")
        self.assertEqual(kwargs['quote']['uri'], 'test_uri')
        self.assertEqual(kwargs['quote']['cid'], 'test_cid')
        
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
        self.client.repost(repost_of)
        
        # 検証
        self.client.client.repost.assert_called_once_with('test_uri', 'test_cid')
        
    def test_repost_not_logged_in(self):
        """未ログイン状態でのリポストテスト"""
        # ログイン状態を変更
        self.client.is_logged_in = False
        
        # テスト実行
        with self.assertRaises(Exception) as context:
            self.client.repost({'uri': 'test_uri', 'cid': 'test_cid'})
        
        # 検証
        self.assertEqual(str(context.exception), "リポストにはログインが必要です")

if __name__ == '__main__':
    unittest.main()
