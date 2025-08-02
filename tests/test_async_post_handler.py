#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
非同期投稿処理ハンドラのテスト
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import threading
import time

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.handlers.async_post_handler import AsyncPostHandler
from core import events

class TestAsyncPostHandler(unittest.TestCase):
    """AsyncPostHandlerのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # クライアントのモックを作成
        self.mock_client = MagicMock()
        self.mock_client.send_post.return_value = {'uri': 'test_uri', 'cid': 'test_cid'}
        self.mock_client.upload_blob.return_value = {'ref': 'test_blob_ref'}
        self.mock_client.like.return_value = {'uri': 'test_like_uri'}
        self.mock_client.repost.return_value = {'uri': 'test_repost_uri'}
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_submit_post_text_only(self, mock_call_after, mock_send_message):
        """テキストのみの投稿テスト"""
        # テスト実行
        AsyncPostHandler.submit_post(self.mock_client, "テスト投稿")
        
        # 開始イベントが発行されることを確認
        mock_call_after.assert_called()
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # クライアントのメソッドが呼ばれることを確認
        self.mock_client.send_post.assert_called_once_with(text="テスト投稿")
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    @patch('gui.handlers.async_post_handler.read_binary_file')
    @patch('gui.handlers.async_post_handler.get_mime_type')
    def test_submit_post_with_images(self, mock_get_mime, mock_read_file, mock_call_after, mock_send_message):
        """画像付き投稿のテスト"""
        # モックの設定
        mock_read_file.return_value = b'fake_image_data'
        mock_get_mime.return_value = 'image/jpeg'
        
        # テスト実行
        images = ['/path/to/image1.jpg', '/path/to/image2.jpg']
        AsyncPostHandler.submit_post(self.mock_client, "画像付き投稿", images)
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # ファイル読み込みが呼ばれることを確認
        self.assertEqual(mock_read_file.call_count, 2)
        mock_read_file.assert_has_calls([
            call('/path/to/image1.jpg'),
            call('/path/to/image2.jpg')
        ])
        
        # MIMEタイプ取得が呼ばれることを確認
        self.assertEqual(mock_get_mime.call_count, 2)
        
        # 画像アップロードが呼ばれることを確認
        self.assertEqual(self.mock_client.upload_blob.call_count, 2)
        
        # 投稿が呼ばれることを確認
        self.mock_client.send_post.assert_called_once()
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    @patch('gui.handlers.async_post_handler.read_binary_file')
    def test_submit_post_file_read_error(self, mock_read_file, mock_call_after, mock_send_message):
        """ファイル読み込みエラーのテスト"""
        # モックの設定（ファイル読み込み失敗）
        mock_read_file.return_value = None
        
        # テスト実行
        images = ['/invalid/path/image.jpg']
        AsyncPostHandler.submit_post(self.mock_client, "投稿", images)
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # 投稿が呼ばれないことを確認
        self.mock_client.send_post.assert_not_called()
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_submit_post_client_error(self, mock_call_after, mock_send_message):
        """投稿時のクライアントエラーのテスト"""
        # モックの設定（投稿失敗）
        self.mock_client.send_post.side_effect = Exception("投稿エラー")
        
        # テスト実行
        AsyncPostHandler.submit_post(self.mock_client, "エラーテスト")
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # エラーイベントが発行されることを確認
        # wx.CallAfterの呼び出し回数を確認（開始イベント + エラーイベント）
        self.assertGreaterEqual(mock_call_after.call_count, 2)
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_like_post(self, mock_call_after, mock_send_message):
        """いいね処理のテスト"""
        # テスト実行
        AsyncPostHandler.like_post(self.mock_client, "test_uri", "test_cid")
        
        # 開始イベントが発行されることを確認
        mock_call_after.assert_called()
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # クライアントのメソッドが呼ばれることを確認
        self.mock_client.like.assert_called_once_with("test_uri", "test_cid")
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_like_post_error(self, mock_call_after, mock_send_message):
        """いいね処理エラーのテスト"""
        # モックの設定（いいね失敗）
        self.mock_client.like.side_effect = Exception("いいねエラー")
        
        # テスト実行
        AsyncPostHandler.like_post(self.mock_client, "test_uri", "test_cid")
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # エラーイベントが発行されることを確認
        # wx.CallAfterの呼び出し回数を確認（開始イベント + エラーイベント）
        self.assertGreaterEqual(mock_call_after.call_count, 2)
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_repost(self, mock_call_after, mock_send_message):
        """リポスト処理のテスト"""
        # テスト実行
        repost_of = {'uri': 'test_uri', 'cid': 'test_cid'}
        AsyncPostHandler.repost(self.mock_client, repost_of)
        
        # 開始イベントが発行されることを確認
        mock_call_after.assert_called()
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # クライアントのメソッドが呼ばれることを確認
        self.mock_client.repost.assert_called_once_with(repost_of)
    
    @patch('gui.handlers.async_post_handler.pub.sendMessage')
    @patch('gui.handlers.async_post_handler.wx.CallAfter')
    def test_repost_error(self, mock_call_after, mock_send_message):
        """リポスト処理エラーのテスト"""
        # モックの設定（リポスト失敗）
        self.mock_client.repost.side_effect = Exception("リポストエラー")
        
        # テスト実行
        repost_of = {'uri': 'test_uri', 'cid': 'test_cid'}
        AsyncPostHandler.repost(self.mock_client, repost_of)
        
        # スレッドの完了を待つ
        time.sleep(0.1)
        
        # エラーイベントが発行されることを確認
        # wx.CallAfterの呼び出し回数を確認（開始イベント + エラーイベント）
        self.assertGreaterEqual(mock_call_after.call_count, 2)
    
    def test_thread_completion(self):
        """スレッドが正常に終了することをテスト"""
        # アクティブなスレッド数を記録
        initial_thread_count = threading.active_count()
        
        # 複数の非同期処理を実行
        AsyncPostHandler.submit_post(self.mock_client, "テスト1")
        AsyncPostHandler.like_post(self.mock_client, "uri1", "cid1")
        AsyncPostHandler.repost(self.mock_client, {'uri': 'uri2', 'cid': 'cid2'})
        
        # スレッドの完了を待つ
        time.sleep(0.2)
        
        # スレッドがリークしていないことを確認
        final_thread_count = threading.active_count()
        self.assertEqual(initial_thread_count, final_thread_count)
    
    @patch('gui.handlers.async_post_handler.threading.Thread')
    def test_daemon_thread_creation(self, mock_thread):
        """デーモンスレッドが作成されることをテスト"""
        # モックスレッドを作成
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # テスト実行
        AsyncPostHandler.submit_post(self.mock_client, "テスト")
        
        # スレッドが作成され、デーモンフラグが設定されることを確認
        mock_thread.assert_called_once()
        self.assertTrue(mock_thread_instance.daemon)
        mock_thread_instance.start.assert_called_once()

if __name__ == '__main__':
    unittest.main()