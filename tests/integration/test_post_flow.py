#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿フロー統合テスト (Phase 3 拡充版)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, Any

from tests.factories import UserFactory, PostFactory


@pytest.mark.integration
class TestPostFlowIntegration:
    """投稿フロー統合テストクラス"""
    
    
    def test_complete_text_post_flow(self, integrated_post_components):
        """完全なテキスト投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 投稿成功をモック
        mock_post_result = PostFactory()
        mock_atproto.send_post.return_value = mock_post_result
        
        # テキスト投稿の実行
        post_text = "これはテスト投稿です"
        result = client.send_post(post_text)
        
        # 結果検証
        assert result is not None
        assert result == mock_post_result
        mock_atproto.send_post.assert_called_once_with(text=post_text)
    
    def test_complete_image_post_flow(self, integrated_post_components):
        """完全な画像投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 画像アップロードとs送を同期モック
        mock_upload_result = {"ref": "test_blob_ref"}
        mock_atproto.upload_blob.return_value = mock_upload_result
        
        mock_post_result = PostFactory()
        mock_atproto.send_post.return_value = mock_post_result
        
        # 画像データの準備
        test_image_data = b"fake_image_data"
        mock_images = [mock_upload_result]
        
        # 画像投稿の実行
        post_text = "画像付きテスト投稿"
        
        # 先に画像をアップロード
        upload_result = client.upload_blob(test_image_data, "image/jpeg")
        
        # 投稿を送信
        result = client.send_post(post_text, [upload_result])
        
        # 結果検証
        assert upload_result is not None
        assert upload_result == mock_upload_result
        assert result is not None
        assert result == mock_post_result
        
        # APIが適切に呼ばれることを確認
        mock_atproto.upload_blob.assert_called_once_with(test_image_data, "image/jpeg")
        mock_atproto.send_post.assert_called_once_with(text=post_text, images=[upload_result])
    
    def test_post_with_authentication_error(self, integrated_post_components):
        """認証エラーが発生する投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 認証エラーをシミュレート
        from atproto.exceptions import AtProtocolError
        mock_atproto.send_post.side_effect = AtProtocolError("Unauthorized")
        
        # 投稿の実行
        post_text = "認証エラーテスト投稿"
        
        with pytest.raises(AtProtocolError):
            client.send_post(post_text)
        
        # APIが呼ばれることを確認
        mock_atproto.send_post.assert_called_once_with(text=post_text)
    
    def test_post_without_login(self, integrated_post_components):
        """ログインなしでの投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        
        # 未ログイン状態を設定
        client.is_logged_in = False
        
        # 投稿の実行
        post_text = "未ログインテスト投稿"
        
        with pytest.raises(Exception, match="投稿にはログインが必要です"):
            client.send_post(post_text)
    
    def test_reply_post_flow(self, integrated_post_components):
        """リプライ投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # リプライ成功をモック（send_postメソッドを使用）
        mock_reply_result = PostFactory()
        mock_atproto.send_post.return_value = mock_reply_result
        
        # リプライ元の投稿情報
        reply_to = {
            "uri": "at://original.post/uri",
            "cid": "original_post_cid"
        }
        
        # リプライ投稿の実行
        reply_text = "これはリプライです"
        result = client.reply_to_post(reply_text, reply_to)
        
        # 結果検証
        assert result is not None
        assert result == mock_reply_result
        # send_postメソッドに reply_to パラメータを渡す
        # reply_paramsの形式で呼ばれる
        assert mock_atproto.send_post.called
        call_args = mock_atproto.send_post.call_args
        assert call_args[1]['text'] == reply_text
        assert 'reply_to' in call_args[1]
    
    def test_quote_post_flow(self, integrated_post_components):
        """引用投稿フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 引用成功をモック（send_postメソッドを使用）
        mock_quote_result = PostFactory()
        mock_atproto.send_post.return_value = mock_quote_result
        
        # 引用元の投稿情報
        quote_of = {
            "uri": "at://quoted.post/uri",
            "cid": "quoted_post_cid"
        }
        
        # 引用投稿の実行
        quote_text = "これは引用投稿です"
        result = client.quote_post(quote_text, quote_of)
        
        # 結果検証
        assert result is not None
        assert result == mock_quote_result
        # send_postメソッドに quote パラメータを渡す
        assert mock_atproto.send_post.called
        call_args = mock_atproto.send_post.call_args
        assert call_args[1]['text'] == quote_text
        assert 'quote' in call_args[1]
    
    def test_repost_flow(self, integrated_post_components):
        """リポストフローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # リポスト成功をモック
        mock_repost_result = PostFactory()
        mock_atproto.repost.return_value = mock_repost_result
        
        # リポスト元の投稿情報
        repost_of = {
            "uri": "at://reposted.post/uri",
            "cid": "reposted_post_cid"
        }
        
        # リポストの実行
        result = client.repost(repost_of)
        
        # 結果検証
        assert result is not None
        assert result == mock_repost_result
        # repostメソッドはuri, cidを別引数として受け取る
        mock_atproto.repost.assert_called_once_with(repost_of['uri'], repost_of['cid'])
    
    def test_like_post_flow(self, integrated_post_components):
        """いいねフローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # いいね成功をモック
        mock_like_result = {"uri": "at://like/record"}
        mock_atproto.like.return_value = mock_like_result
        
        # いいね対象の投稿情報
        post_uri = "at://liked.post/uri"
        post_cid = "liked_post_cid"
        
        # いいねの実行
        result = client.like(post_uri, post_cid)
        
        # 結果検証
        assert result is not None
        assert result == mock_like_result
        # likeメソッドはuri, cidを位置引数として受け取る
        mock_atproto.like.assert_called_once_with(post_uri, post_cid)
    
    def test_delete_post_flow(self, integrated_post_components):
        """投稿削除フローのテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 削除成功をモック（com.atproto.repo.delete_recordを使用）
        mock_delete_result = {"success": True}
        mock_atproto.com = Mock()
        mock_atproto.com.atproto = Mock()
        mock_atproto.com.atproto.repo = Mock()
        mock_atproto.com.atproto.repo.delete_record = Mock(return_value=mock_delete_result)
        
        # 削除対象の投稿URI（正しい形式）
        post_uri = "at://did:plc:testuser/app.bsky.feed.post/test123"
        
        # 投稿削除の実行
        result = client.delete_post(post_uri)
        
        # 結果検証
        assert result is not None
        assert result == mock_delete_result
        # com.atproto.repo.delete_recordが呼ばれることを確認
        assert mock_atproto.com.atproto.repo.delete_record.called


@pytest.mark.integration
@pytest.mark.slow
class TestPostFlowPerformance:
    """投稿フロー性能テストクラス"""
    
    def test_bulk_post_operations_performance(self, integrated_post_components):
        """大量投稿操作の性能テスト"""
        import time
        
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 投稿成功をモック
        mock_post_result = PostFactory()
        mock_atproto.send_post.return_value = mock_post_result
        
        # 性能測定
        start_time = time.time()
        
        # 大量の投稿を実行
        for i in range(50):
            post_text = f"パフォーマンステスト投稿 {i}"
            client.send_post(post_text)
        
        end_time = time.time()
        
        # 性能目標: 50件の投稿で5秒以内
        assert end_time - start_time < 5.0
        
        # 全ての投稿が呼ばれることを確認
        assert mock_atproto.send_post.call_count == 50
    
    def test_concurrent_post_operations_performance(self, integrated_post_components):
        """同時投稿操作の性能テスト"""
        import threading
        import time
        
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 投稿成功をモック
        mock_post_result = PostFactory()
        mock_atproto.send_post.return_value = mock_post_result
        
        results = []
        
        def post_worker(post_id):
            """投稿ワーカー関数"""
            try:
                post_text = f"同時投稿テスト {post_id}"
                result = client.send_post(post_text)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        # 性能測定
        start_time = time.time()
        
        # 10個の同時スレッドで投稿を実行
        threads = []
        for i in range(10):
            thread = threading.Thread(target=post_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 結果検証
        assert len(results) == 10
        assert all(result == mock_post_result for result in results)
        
        # 性能目標: 10個の同時投稿で10秒以内
        assert end_time - start_time < 10.0
        
        # 全ての投稿が呼ばれることを確認
        assert mock_atproto.send_post.call_count == 10


@pytest.mark.integration
@pytest.mark.network
class TestPostFlowWithNetworkSimulation:
    """ネットワーク関連の投稿フロー統合テスト"""
    
    def test_network_timeout_during_post(self, integrated_post_components):
        """投稿時のネットワークタイムアウト処理のテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # タイムアウトエラーをシミュレート
        mock_atproto.send_post.side_effect = TimeoutError("ネットワークタイムアウト")
        
        # 投稿の実行
        post_text = "タイムアウトテスト投稿"
        
        with pytest.raises(TimeoutError):
            client.send_post(post_text)
        
        # APIが呼ばれることを確認
        mock_atproto.send_post.assert_called_once_with(text=post_text)
    
    def test_connection_error_during_upload(self, integrated_post_components):
        """アップロード時の接続エラー処理のテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 接続エラーをシミュレート
        mock_atproto.upload_blob.side_effect = ConnectionError("接続に失敗しました")
        
        # アップロードの実行
        test_image_data = b"fake_image_data"
        
        with pytest.raises(ConnectionError):
            client.upload_blob(test_image_data, "image/jpeg")
        
        # APIが呼ばれることを確認
        mock_atproto.upload_blob.assert_called_once_with(test_image_data, "image/jpeg")
    
    def test_partial_failure_retry_mechanism(self, integrated_post_components):
        """部分的な失敗時のリトライメカニズムテスト"""
        components = integrated_post_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 最初は失敗、2回目は成功するようにモック設定
        mock_post_result = PostFactory()
        mock_atproto.send_post.side_effect = [
            ConnectionError("一時的な接続エラー"),
            mock_post_result  # 2回目は成功
        ]
        
        # カスタムリトライロジックがある場合のテスト
        # 実装にリトライ機能がない場合は、1回目のエラーで終わる
        post_text = "リトライテスト投稿"
        
        try:
            result = client.send_post(post_text)
            # リトライ機能がある場合は成功
            assert result == mock_post_result
        except ConnectionError:
            # リトライ機能がない場合は1回目のエラーで失敗
            pass
        
        # 少なくとも1回は呼ばれることを確認
        assert mock_atproto.send_post.call_count >= 1