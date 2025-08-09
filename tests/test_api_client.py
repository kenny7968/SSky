#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
API クライアントの単体テスト (Phase 1 リファクタリング版)
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import logging

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client.api_client import BlueskyApiClient
from atproto.exceptions import AtProtocolError


class TestBlueskyApiClient(unittest.TestCase):
    """BlueskyApiClient の単体テストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.mock_session_manager = MagicMock()
        
        # AtprotoClient をモック
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            self.api_client = BlueskyApiClient(self.mock_session_manager)
            self.mock_atproto_instance = mock_atproto.return_value
            self.api_client.client = self.mock_atproto_instance
    
    def test_initialization_with_session_manager(self):
        """セッションマネージャー付き初期化テスト"""
        session_manager = MagicMock()
        
        with patch('core.client.api_client.AtprotoClient'):
            client = BlueskyApiClient(session_manager)
            self.assertEqual(client.session_manager, session_manager)
            self.assertIsNotNone(client.client)
    
    def test_initialization_without_session_manager(self):
        """セッションマネージャーなし初期化テスト"""
        with patch('core.client.api_client.AtprotoClient'):
            client = BlueskyApiClient()
            self.assertIsNone(client.session_manager)
            self.assertIsNotNone(client.client)
    
    @patch('core.client.api_client.logger')
    def test_get_timeline_success(self, mock_logger):
        """タイムライン取得成功のテスト"""
        # モックデータの準備
        mock_timeline = MagicMock()
        mock_timeline.feed = ['post1', 'post2', 'post3']
        self.mock_atproto_instance.get_timeline.return_value = mock_timeline
        
        # メソッド実行
        result = self.api_client.get_timeline(limit=3)
        
        # 結果検証
        self.assertEqual(result, mock_timeline)
        self.mock_atproto_instance.get_timeline.assert_called_once_with(limit=3)
        
        # ログ検証
        self.assertTrue(mock_logger.info.called)
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("タイムラインを取得しています" in msg for msg in log_calls))
        self.assertTrue(any("タイムラインを取得しました: 3件" in msg for msg in log_calls))
    
    @patch('core.client.api_client.logger')
    def test_get_timeline_default_limit(self, mock_logger):
        """タイムライン取得のデフォルト件数テスト"""
        mock_timeline = MagicMock()
        mock_timeline.feed = ['post'] * 50  # デフォルト50件
        self.mock_atproto_instance.get_timeline.return_value = mock_timeline
        
        # デフォルト引数でメソッド実行
        result = self.api_client.get_timeline()
        
        # デフォルトlimit=50で呼ばれることを確認
        self.mock_atproto_instance.get_timeline.assert_called_once_with(limit=50)
    
    def test_get_timeline_api_error(self):
        """タイムライン取得時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        self.mock_atproto_instance.get_timeline.side_effect = AtProtocolError("API Error")
        
        # エラーが適切にraise されることを確認
        with self.assertRaises(AtProtocolError):
            self.api_client.get_timeline()
        
        # APIが呼ばれたことを確認
        self.mock_atproto_instance.get_timeline.assert_called_once()
    
    @patch('core.client.api_client.logger')
    def test_send_post_text_only(self, mock_logger):
        """テキストのみ投稿のテスト"""
        mock_result = MagicMock()
        self.mock_atproto_instance.send_post.return_value = mock_result
        
        # テキストのみ投稿
        text = "テスト投稿です"
        result = self.api_client.send_post(text)
        
        # 結果検証
        self.assertEqual(result, mock_result)
        self.mock_atproto_instance.send_post.assert_called_once_with(text=text)
        
        # ログ検証
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("投稿を送信しています" in msg for msg in log_calls))
        self.assertTrue(any("投稿が完了しました" in msg for msg in log_calls))
    
    @patch('core.client.api_client.logger')
    def test_send_post_with_images(self, mock_logger):
        """画像付き投稿のテスト"""
        mock_result = MagicMock()
        self.mock_atproto_instance.send_post.return_value = mock_result
        
        # 画像付き投稿
        text = "画像付き投稿です"
        images = [MagicMock(), MagicMock()]  # モック画像ブロブ
        result = self.api_client.send_post(text, images)
        
        # 結果検証
        self.assertEqual(result, mock_result)
        self.mock_atproto_instance.send_post.assert_called_once_with(text=text, images=images)
        
        # ログが適切に出力されることを確認
        self.assertTrue(mock_logger.info.called)
    
    def test_send_post_api_error(self):
        """投稿時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        self.mock_atproto_instance.send_post.side_effect = AtProtocolError("投稿エラー")
        
        # エラーが適切にraise されることを確認
        with self.assertRaises(AtProtocolError):
            self.api_client.send_post("テスト投稿")
        
        # APIが呼ばれたことを確認
        self.mock_atproto_instance.send_post.assert_called_once()
    
    @patch('core.client.api_client.logger')
    def test_upload_blob_success(self, mock_logger):
        """ファイルアップロード成功のテスト"""
        mock_blob = MagicMock()
        self.mock_atproto_instance.upload_blob.return_value = mock_blob
        
        # ファイルアップロード
        file_data = b"test file data"
        mime_type = "image/jpeg"
        result = self.api_client.upload_blob(file_data, mime_type)
        
        # 結果検証
        self.assertEqual(result, mock_blob)
        self.mock_atproto_instance.upload_blob.assert_called_once_with(file_data, mime_type)
        
        # ログ検証
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any(f"ファイルをアップロードしています: {mime_type}" in msg for msg in log_calls))
    
    @patch('core.client.api_client.logger')
    def test_upload_blob_without_mime_type(self, mock_logger):
        """MIMEタイプなしファイルアップロードのテスト"""
        mock_blob = MagicMock()
        self.mock_atproto_instance.upload_blob.return_value = mock_blob
        
        # MIMEタイプなしでファイルアップロード
        file_data = b"test file data"
        result = self.api_client.upload_blob(file_data)
        
        # 結果検証
        self.assertEqual(result, mock_blob)
        self.mock_atproto_instance.upload_blob.assert_called_once_with(file_data, None)
    
    def test_upload_blob_api_error(self):
        """ファイルアップロード時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        self.mock_atproto_instance.upload_blob.side_effect = AtProtocolError("アップロードエラー")
        
        # エラーが適切にraise されることを確認
        with self.assertRaises(AtProtocolError):
            self.api_client.upload_blob(b"test data", "image/jpeg")
        
        # APIが呼ばれたことを確認
        self.mock_atproto_instance.upload_blob.assert_called_once()
    
    def test_client_instance_type(self):
        """クライアントインスタンスのタイプテスト"""
        # AtprotoClient がモックされていることを確認
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            client = BlueskyApiClient()
            mock_atproto.assert_called_once()
    
    def test_session_manager_integration(self):
        """セッションマネージャーとの統合テスト"""
        # セッションマネージャーが正しく保持されていることを確認
        self.assertEqual(self.api_client.session_manager, self.mock_session_manager)
    
    @patch('core.client.api_client.logger')
    def test_logging_integration(self, mock_logger):
        """ログ統合テスト"""
        # ログレベルが適切に設定されていることを確認
        # (実際のアプリケーションではlogger設定を確認)
        
        mock_timeline = MagicMock()
        mock_timeline.feed = []
        self.mock_atproto_instance.get_timeline.return_value = mock_timeline
        
        self.api_client.get_timeline()
        
        # info レベルでログが出力されることを確認
        self.assertTrue(mock_logger.info.called)
        self.assertGreaterEqual(mock_logger.info.call_count, 2)


class TestBlueskyApiClientErrorHandling(unittest.TestCase):
    """BlueskyApiClient のエラーハンドリングテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            self.api_client = BlueskyApiClient()
            self.mock_atproto_instance = mock_atproto.return_value
            self.api_client.client = self.mock_atproto_instance
    
    def test_network_error_propagation(self):
        """ネットワークエラーの伝播テスト"""
        # 一般的な例外を発生させる
        self.mock_atproto_instance.get_timeline.side_effect = ConnectionError("ネットワークエラー")
        
        # エラーが適切に伝播されることを確認
        with self.assertRaises(ConnectionError):
            self.api_client.get_timeline()
    
    def test_atprotocol_error_propagation(self):
        """AtProtocolErrorの伝播テスト"""
        # 認証エラーをシミュレート
        auth_error = AtProtocolError("認証が必要です")
        self.mock_atproto_instance.send_post.side_effect = auth_error
        
        # エラーが適切に伝播されることを確認
        with self.assertRaises(AtProtocolError) as context:
            self.api_client.send_post("テスト投稿")
        
        self.assertEqual(str(context.exception), "認証が必要です")
    
    def test_unexpected_error_propagation(self):
        """予期しないエラーの伝播テスト"""
        # 予期しない例外を発生させる
        self.mock_atproto_instance.upload_blob.side_effect = RuntimeError("予期しないエラー")
        
        # エラーが適切に伝播されることを確認
        with self.assertRaises(RuntimeError):
            self.api_client.upload_blob(b"test data")


if __name__ == '__main__':
    unittest.main(verbosity=2)