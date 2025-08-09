#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
API クライアントの単体テスト (Phase 2 pytest版)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import logging

from core.client.api_client import BlueskyApiClient
from atproto.exceptions import AtProtocolError
from tests.factories import UserFactory, PostFactory


class TestBlueskyApiClient:
    """BlueskyApiClient の単体テストクラス"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """セッションマネージャーのモック"""
        return MagicMock()
    
    @pytest.fixture
    def api_client(self, mock_session_manager, mock_atproto_client):
        """APIクライアントのテスト用インスタンス"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            client = BlueskyApiClient(mock_session_manager)
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_initialization_with_session_manager(self, mock_session_manager):
        """セッションマネージャー付き初期化テスト"""
        with patch('core.client.api_client.AtprotoClient'):
            client = BlueskyApiClient(mock_session_manager)
            assert client.session_manager == mock_session_manager
            assert client.client is not None
    
    def test_initialization_without_session_manager(self):
        """セッションマネージャーなし初期化テスト"""
        with patch('core.client.api_client.AtprotoClient'):
            client = BlueskyApiClient()
            assert client.session_manager is None
            assert client.client is not None
    
    def test_get_timeline_success(self, api_client, mock_atproto_client, mock_logger):
        """タイムライン取得成功のテスト"""
        # モックデータの準備
        mock_timeline = MagicMock()
        mock_timeline.feed = ['post1', 'post2', 'post3']
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        with patch('core.client.api_client.logger', mock_logger):
            # メソッド実行
            result = api_client.get_timeline(limit=3)
        
        # 結果検証
        assert result == mock_timeline
        mock_atproto_client.get_timeline.assert_called_once_with(limit=3)
        
        # ログ検証
        assert mock_logger.info.called
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("タイムラインを取得しています" in msg for msg in log_calls)
        assert any("タイムラインを取得しました: 3件" in msg for msg in log_calls)
    
    def test_get_timeline_default_limit(self, api_client, mock_atproto_client):
        """タイムライン取得のデフォルト件数テスト"""
        mock_timeline = MagicMock()
        mock_timeline.feed = ['post'] * 50  # デフォルト50件
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        # デフォルト引数でメソッド実行
        result = api_client.get_timeline()
        
        # デフォルトlimit=50で呼ばれることを確認
        mock_atproto_client.get_timeline.assert_called_once_with(limit=50)
    
    def test_get_timeline_api_error(self, api_client, mock_atproto_client):
        """タイムライン取得時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        mock_atproto_client.get_timeline.side_effect = AtProtocolError("API Error")
        
        # エラーが適切にraise されることを確認
        with pytest.raises(AtProtocolError, match="API Error"):
            api_client.get_timeline()
        
        # APIが呼ばれたことを確認
        mock_atproto_client.get_timeline.assert_called_once()
    
    @pytest.mark.parametrize("limit,expected_limit", [
        (10, 10),
        (25, 25),
        (100, 100),
        (None, 50)  # デフォルト値
    ])
    def test_get_timeline_various_limits(self, api_client, mock_atproto_client, limit, expected_limit):
        """様々な件数でのタイムライン取得テスト"""
        mock_timeline = MagicMock()
        mock_timeline.feed = ['post'] * (expected_limit or 50)
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        # 実行
        if limit is None:
            api_client.get_timeline()
        else:
            api_client.get_timeline(limit=limit)
        
        # 期待される引数で呼ばれることを確認
        mock_atproto_client.get_timeline.assert_called_once_with(limit=expected_limit)
    
    def test_send_post_text_only(self, api_client, mock_atproto_client, mock_logger):
        """テキストのみ投稿のテスト"""
        mock_result = MagicMock()
        mock_atproto_client.send_post.return_value = mock_result
        
        with patch('core.client.api_client.logger', mock_logger):
            # テキストのみ投稿
            text = "テスト投稿です"
            result = api_client.send_post(text)
        
        # 結果検証
        assert result == mock_result
        mock_atproto_client.send_post.assert_called_once_with(text=text)
        
        # ログ検証
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("投稿を送信しています" in msg for msg in log_calls)
        assert any("投稿が完了しました" in msg for msg in log_calls)
    
    def test_send_post_with_images(self, api_client, mock_atproto_client, mock_logger):
        """画像付き投稿のテスト"""
        mock_result = MagicMock()
        mock_atproto_client.send_post.return_value = mock_result
        
        with patch('core.client.api_client.logger', mock_logger):
            # 画像付き投稿
            text = "画像付き投稿です"
            images = [MagicMock(), MagicMock()]  # モック画像ブロブ
            result = api_client.send_post(text, images)
        
        # 結果検証
        assert result == mock_result
        mock_atproto_client.send_post.assert_called_once_with(text=text, images=images)
        
        # ログが適切に出力されることを確認
        assert mock_logger.info.called
    
    def test_send_post_api_error(self, api_client, mock_atproto_client):
        """投稿時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        mock_atproto_client.send_post.side_effect = AtProtocolError("投稿エラー")
        
        # エラーが適切にraise されることを確認
        with pytest.raises(AtProtocolError, match="投稿エラー"):
            api_client.send_post("テスト投稿")
        
        # APIが呼ばれたことを確認
        mock_atproto_client.send_post.assert_called_once()
    
    def test_upload_blob_success(self, api_client, mock_atproto_client, mock_logger):
        """ファイルアップロード成功のテスト"""
        mock_blob = MagicMock()
        mock_atproto_client.upload_blob.return_value = mock_blob
        
        with patch('core.client.api_client.logger', mock_logger):
            # ファイルアップロード
            file_data = b"test file data"
            mime_type = "image/jpeg"
            result = api_client.upload_blob(file_data, mime_type)
        
        # 結果検証
        assert result == mock_blob
        mock_atproto_client.upload_blob.assert_called_once_with(file_data, mime_type)
        
        # ログ検証
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any(f"ファイルをアップロードしています: {mime_type}" in msg for msg in log_calls)
    
    def test_upload_blob_without_mime_type(self, api_client, mock_atproto_client):
        """MIMEタイプなしファイルアップロードのテスト"""
        mock_blob = MagicMock()
        mock_atproto_client.upload_blob.return_value = mock_blob
        
        # MIMEタイプなしでファイルアップロード
        file_data = b"test file data"
        result = api_client.upload_blob(file_data)
        
        # 結果検証
        assert result == mock_blob
        mock_atproto_client.upload_blob.assert_called_once_with(file_data, None)
    
    def test_upload_blob_api_error(self, api_client, mock_atproto_client):
        """ファイルアップロード時のAPIエラーテスト"""
        # AtProtocolError を発生させる
        mock_atproto_client.upload_blob.side_effect = AtProtocolError("アップロードエラー")
        
        # エラーが適切にraise されることを確認
        with pytest.raises(AtProtocolError, match="アップロードエラー"):
            api_client.upload_blob(b"test data", "image/jpeg")
        
        # APIが呼ばれたことを確認
        mock_atproto_client.upload_blob.assert_called_once()
    
    def test_client_instance_type(self):
        """クライアントインスタンスのタイプテスト"""
        # AtprotoClient がモックされていることを確認
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            client = BlueskyApiClient()
            mock_atproto.assert_called_once()
    
    def test_session_manager_integration(self, api_client, mock_session_manager):
        """セッションマネージャーとの統合テスト"""
        # セッションマネージャーが正しく保持されていることを確認
        assert api_client.session_manager == mock_session_manager


class TestBlueskyApiClientWithFactories:
    """ファクトリパターンを使用したテストクラス"""
    
    @pytest.fixture
    def api_client_with_data(self, mock_atproto_client):
        """テストデータ付きAPIクライアント"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_get_timeline_with_factory_data(self, api_client_with_data, mock_atproto_client):
        """ファクトリで生成したデータを使ったタイムライン取得テスト"""
        # ファクトリでテストデータを生成
        posts = [PostFactory() for _ in range(5)]
        
        mock_timeline = MagicMock()
        mock_timeline.feed = posts
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        # テスト実行
        result = api_client_with_data.get_timeline(limit=5)
        
        # 結果検証
        assert result == mock_timeline
        assert len(result.feed) == 5
        
        # 各投稿が適切な構造を持っていることを確認
        for post in result.feed:
            assert 'uri' in post
            assert 'cid' in post
            assert 'author' in post
            assert 'record' in post
    
    def test_send_post_with_factory_user(self, api_client_with_data, mock_atproto_client):
        """ファクトリユーザーデータを使った投稿テスト"""
        # ファクトリでユーザーデータを生成
        user = UserFactory()
        
        mock_result = MagicMock()
        mock_result.uri = f"at://{user['handle']}/app.bsky.feed.post/test123"
        mock_atproto_client.send_post.return_value = mock_result
        
        # テスト実行
        text = f"Hello from {user['displayName']}"
        result = api_client_with_data.send_post(text)
        
        # 結果検証
        assert result == mock_result
        mock_atproto_client.send_post.assert_called_once_with(text=text)
    
    @pytest.mark.parametrize("file_size,mime_type", [
        (1024, "image/jpeg"),
        (2048, "image/png"),
        (4096, "image/gif"),
        (10240, "video/mp4")
    ])
    def test_upload_various_file_types(self, api_client_with_data, mock_atproto_client, file_size, mime_type):
        """様々なファイルタイプのアップロードテスト"""
        # テストファイルデータを生成
        file_data = b"x" * file_size
        
        mock_blob = MagicMock()
        mock_blob.ref = f"test_blob_{file_size}_{mime_type.replace('/', '_')}"
        mock_atproto_client.upload_blob.return_value = mock_blob
        
        # テスト実行
        result = api_client_with_data.upload_blob(file_data, mime_type)
        
        # 結果検証
        assert result == mock_blob
        mock_atproto_client.upload_blob.assert_called_once_with(file_data, mime_type)


class TestBlueskyApiClientErrorHandling:
    """BlueskyApiClient のエラーハンドリングテストクラス"""
    
    @pytest.fixture
    def api_client_for_errors(self, mock_atproto_client):
        """エラーテスト用のAPIクライアント"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_network_error_propagation(self, api_client_for_errors, mock_atproto_client):
        """ネットワークエラーの伝播テスト"""
        # 一般的な例外を発生させる
        mock_atproto_client.get_timeline.side_effect = ConnectionError("ネットワークエラー")
        
        # エラーが適切に伝播されることを確認
        with pytest.raises(ConnectionError, match="ネットワークエラー"):
            api_client_for_errors.get_timeline()
    
    def test_atprotocol_error_propagation(self, api_client_for_errors, mock_atproto_client):
        """AtProtocolErrorの伝播テスト"""
        # 認証エラーをシミュレート
        auth_error = AtProtocolError("認証が必要です")
        mock_atproto_client.send_post.side_effect = auth_error
        
        # エラーが適切に伝播されることを確認
        with pytest.raises(AtProtocolError, match="認証が必要です"):
            api_client_for_errors.send_post("テスト投稿")
    
    def test_unexpected_error_propagation(self, api_client_for_errors, mock_atproto_client):
        """予期しないエラーの伝播テスト"""
        # 予期しない例外を発生させる
        mock_atproto_client.upload_blob.side_effect = RuntimeError("予期しないエラー")
        
        # エラーが適切に伝播されることを確認
        with pytest.raises(RuntimeError, match="予期しないエラー"):
            api_client_for_errors.upload_blob(b"test data")
    
    @pytest.mark.parametrize("error_type,error_message", [
        (ConnectionError, "接続エラー"),
        (TimeoutError, "タイムアウトエラー"),
        (AtProtocolError, "プロトコルエラー"),
        (ValueError, "値エラー"),
        (RuntimeError, "実行時エラー")
    ])
    def test_various_error_propagation(self, api_client_for_errors, mock_atproto_client, error_type, error_message):
        """様々なエラータイプの伝播テスト"""
        mock_atproto_client.get_timeline.side_effect = error_type(error_message)
        
        with pytest.raises(error_type, match=error_message):
            api_client_for_errors.get_timeline()


class TestBlueskyApiClientLogging:
    """ロギング機能のテストクラス"""
    
    @pytest.fixture
    def api_client_with_logging(self, mock_atproto_client):
        """ログ付きAPIクライアント"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_logging_integration(self, api_client_with_logging, mock_atproto_client, mock_logger):
        """ログ統合テスト"""
        mock_timeline = MagicMock()
        mock_timeline.feed = []
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        with patch('core.client.api_client.logger', mock_logger):
            api_client_with_logging.get_timeline()
        
        # info レベルでログが出力されることを確認
        assert mock_logger.info.called
        assert mock_logger.info.call_count >= 2
    
    def test_error_logging(self, api_client_with_logging, mock_atproto_client, mock_logger):
        """エラーログのテスト"""
        mock_atproto_client.get_timeline.side_effect = AtProtocolError("テストエラー")
        
        with patch('core.client.api_client.logger', mock_logger):
            with pytest.raises(AtProtocolError):
                api_client_with_logging.get_timeline()


# パフォーマンステスト
@pytest.mark.slow
class TestBlueskyApiClientPerformance:
    """APIクライアント性能テストクラス"""
    
    def test_bulk_timeline_requests_performance(self, mock_atproto_client):
        """大量タイムライン要求の性能テスト"""
        import time
        
        # モックの設定
        mock_timeline = MagicMock()
        mock_timeline.feed = [PostFactory() for _ in range(50)]
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            
            # 性能測定
            start_time = time.time()
            
            results = [client.get_timeline(limit=10) for _ in range(100)]
            
            end_time = time.time()
        
        # 全て正常に処理されることを確認
        assert len(results) == 100
        assert all(result == mock_timeline for result in results)
        
        # 性能目標: 100回の要求で5秒以内
        assert end_time - start_time < 5.0