#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ユーザーマネージャーモジュールのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client.user_manager import BlueskyUserManager
from atproto.exceptions import AtProtocolError

class TestBlueskyUserManager(unittest.TestCase):
    """BlueskyUserManagerのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.api_client = MagicMock()
        self.auth_manager = MagicMock()
        self.auth_manager.user_did = "did:plc:test123"
        self.user_manager = BlueskyUserManager(self.api_client, self.auth_manager)
        
    def test_init(self):
        """初期化のテスト"""
        user_manager = BlueskyUserManager()
        self.assertIsNone(user_manager.api_client)
        self.assertIsNone(user_manager.auth_manager)
        
    def test_follow_success(self):
        """フォロー成功のテスト"""
        # モックの設定
        self.api_client.client.follow.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.follow("test_user")
        
        # 検証
        self.api_client.client.follow.assert_called_once_with("test_user")
        self.assertIsNotNone(result)
        
    def test_unfollow_with_uri(self):
        """URI使用でのフォロー解除テスト"""
        # モックの設定
        mock_profile = MagicMock()
        mock_profile.viewer.following = "at://did:plc:test123/app.bsky.graph.follow/rkey123"
        self.api_client.client.get_profile.return_value = mock_profile
        self.api_client.client.com.atproto.repo.delete_record.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.unfollow("test_user")
        
        # 検証
        self.api_client.client.get_profile.assert_called_once_with(actor="test_user")
        self.api_client.client.com.atproto.repo.delete_record.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_block_success(self):
        """ブロック成功のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.did = "did:plc:target123"
        self.api_client.client.resolve_handle.return_value = mock_response
        self.api_client.client.app.bsky.graph.block.create.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.block("test_user")
        
        # 検証
        self.api_client.client.resolve_handle.assert_called_once_with(handle="test_user")
        self.api_client.client.app.bsky.graph.block.create.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_block_fallback_to_low_level_api(self):
        """ブロック時の低レベルAPI fallbackテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.did = "did:plc:target123"
        self.api_client.client.resolve_handle.return_value = mock_response
        self.api_client.client.app.bsky.graph.block.create.side_effect = AttributeError("Not available")
        self.api_client.client.com.atproto.repo.create_record.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.block("test_user")
        
        # 検証
        self.api_client.client.com.atproto.repo.create_record.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_unblock_with_uri(self):
        """URI使用でのブロック解除テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.did = "did:plc:target123"
        self.api_client.client.resolve_handle.return_value = mock_response
        
        mock_profile = MagicMock()
        mock_profile.viewer.blocking = "at://did:plc:test123/app.bsky.graph.block/rkey123"
        self.api_client.client.get_profile.return_value = mock_profile
        self.api_client.client.app.bsky.graph.block.delete.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.unblock("test_user")
        
        # 検証
        self.api_client.client.get_profile.assert_called_once_with(actor="test_user")
        self.api_client.client.app.bsky.graph.block.delete.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_mute_success(self):
        """ミュート成功のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.did = "did:plc:target123"
        self.api_client.client.resolve_handle.return_value = mock_response
        self.api_client.client.app.bsky.graph.mute_actor.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.mute("test_user")
        
        # 検証
        self.api_client.client.resolve_handle.assert_called_once_with(handle="test_user")
        self.api_client.client.app.bsky.graph.mute_actor.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_unmute_success(self):
        """ミュート解除成功のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.did = "did:plc:target123"
        self.api_client.client.resolve_handle.return_value = mock_response
        self.api_client.client.app.bsky.graph.unmute_actor.return_value = MagicMock()
        
        # テスト実行
        result = self.user_manager.unmute("test_user")
        
        # 検証
        self.api_client.client.resolve_handle.assert_called_once_with(handle="test_user")
        self.api_client.client.app.bsky.graph.unmute_actor.assert_called_once()
        self.assertIsNotNone(result)
        
    def test_get_following_success(self):
        """フォロー中ユーザー取得成功のテスト"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.follows = [MagicMock(), MagicMock()]
        self.api_client.client.app.bsky.graph.get_follows.return_value = mock_result
        
        # テスト実行
        result = self.user_manager.get_following("test_user", limit=50)
        
        # 検証
        self.api_client.client.app.bsky.graph.get_follows.assert_called_once_with({
            'actor': 'test_user',
            'limit': 50,
            'cursor': None
        })
        self.assertEqual(len(result.follows), 2)
        
    def test_get_followers_success(self):
        """フォロワー取得成功のテスト"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.followers = [MagicMock(), MagicMock(), MagicMock()]
        self.api_client.client.app.bsky.graph.get_followers.return_value = mock_result
        
        # テスト実行
        result = self.user_manager.get_followers("test_user", limit=30)
        
        # 検証
        self.api_client.client.app.bsky.graph.get_followers.assert_called_once_with({
            'actor': 'test_user',
            'limit': 30,
            'cursor': None
        })
        self.assertEqual(len(result.followers), 3)
        
    def test_get_blocked_users_success(self):
        """ブロックユーザー取得成功のテスト"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.blocks = [MagicMock()]
        self.api_client.client.app.bsky.graph.get_blocks.return_value = mock_result
        
        # テスト実行
        result = self.user_manager.get_blocked_users(limit=20)
        
        # 検証
        self.api_client.client.app.bsky.graph.get_blocks.assert_called_once_with(params={
            'limit': 20,
            'cursor': None
        })
        self.assertEqual(len(result.blocks), 1)
        
    def test_get_muted_users_success(self):
        """ミュートユーザー取得成功のテスト"""
        # モックの設定
        mock_result = MagicMock()
        mock_result.mutes = [MagicMock(), MagicMock()]
        self.api_client.client.app.bsky.graph.get_mutes.return_value = mock_result
        
        # テスト実行
        result = self.user_manager.get_muted_users(limit=10)
        
        # 検証
        self.api_client.client.app.bsky.graph.get_mutes.assert_called_once_with(params={
            'limit': 10,
            'cursor': None
        })
        self.assertEqual(len(result.mutes), 2)

if __name__ == '__main__':
    unittest.main()