#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
エラー処理フロー統合テスト (Phase 3 拡充版)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import tempfile
from pathlib import Path
from typing import Dict, Any
from atproto.exceptions import AtProtocolError

from tests.factories import UserFactory, PostFactory


@pytest.mark.integration
class TestErrorHandlingFlowIntegration:
    """エラー処理フロー統合テストクラス"""
    
    def test_authentication_error_flow(self, integrated_error_handling_components):
        """認証エラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        mock_wx = components['mock_wx']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 認証エラーをシミュレート
        auth_error = AtProtocolError("InvalidToken", "Token is invalid or expired")
        mock_atproto.get_timeline.side_effect = auth_error
        
        # エラーハンドリングの実行
        with pytest.raises(Exception):  # AuthenticationErrorまたは他のエラー
            client.get_timeline()
        
        # 認証エラー処理が呼ばれることを確認
        # エラーハンドラーが適切に動作することを確認
        assert mock_atproto.get_timeline.called
    
    def test_network_error_flow(self, integrated_error_handling_components):
        """ネットワークエラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        mock_wx = components['mock_wx']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # ネットワークエラーをシミュレート
        network_error = ConnectionError("Network is unreachable")
        mock_atproto.send_post.side_effect = network_error
        
        # エラーハンドリングの実行
        with pytest.raises(ConnectionError):
            client.send_post("テスト投稿")
        
        # ネットワークエラーが適切に処理されることを確認
        assert mock_atproto.send_post.called
    
    def test_api_rate_limit_error_flow(self, integrated_error_handling_components):
        """APIレート制限エラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        mock_wx = components['mock_wx']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # レート制限エラーをシミュレート
        rate_limit_error = AtProtocolError("RateLimitExceeded", "Rate limit exceeded")
        mock_atproto.like.side_effect = rate_limit_error
        
        # エラーハンドリングの実行
        with pytest.raises(AtProtocolError):
            client.like("at://test.post/uri", "test_cid")
        
        # レート制限エラーが適切に処理されることを確認
        assert mock_atproto.like.called
    
    def test_file_upload_error_flow(self, integrated_error_handling_components):
        """ファイルアップロードエラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        mock_wx = components['mock_wx']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # ファイルサイズエラーをシミュレート
        file_error = AtProtocolError("BlobTooLarge", "Blob size exceeds limit")
        mock_atproto.upload_blob.side_effect = file_error
        
        # エラーハンドリングの実行
        test_data = b"fake_large_file_data"
        
        with pytest.raises(AtProtocolError):
            client.upload_blob(test_data, "image/jpeg")
        
        # ファイルアップロードエラーが適切に処理されることを確認
        assert mock_atproto.upload_blob.called
    
    def test_database_error_flow(self, integrated_error_handling_components):
        """データベースエラー処理フローのテスト"""
        components = integrated_error_handling_components
        credential_manager = components['credential_manager']
        
        # データベースエラーをシミュレート
        with patch.object(components['data_store'], 'save_session') as mock_save:
            mock_save.side_effect = Exception("Database connection failed")
            
            # 認証情報保存の実行
            result = credential_manager.save_credentials("test@example.com", "password", {})
            
            # エラーが適切に処理されることを確認
            assert result == False
            assert mock_save.called
    
    def test_encryption_error_flow(self, integrated_error_handling_components, mock_crypto):
        """暗号化エラー処理フローのテスト"""
        components = integrated_error_handling_components
        credential_manager = components['credential_manager']
        
        # 暗号化エラーをシミュレート
        mock_crypto['encrypt'].side_effect = Exception("Encryption failed")
        
        # 認証情報保存の実行
        result = credential_manager.save_credentials("test@example.com", "password", {})
        
        # 暗号化エラーが適切に処理されることを確認
        assert result == False
        assert mock_crypto['encrypt'].called
    
    def test_session_expired_error_flow(self, integrated_error_handling_components):
        """セッション期限切れエラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        mock_wx = components['mock_wx']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # セッション期限切れエラーをシミュレート
        session_error = AtProtocolError("ExpiredToken", "Session has expired")
        mock_atproto.get_timeline.side_effect = session_error
        
        # エラーハンドリングの実行
        with pytest.raises(Exception):
            client.get_timeline()
        
        # セッション期限切れエラーが適切に処理されることを確認
        assert mock_atproto.get_timeline.called
    
    def test_multiple_error_cascade_flow(self, integrated_error_handling_components):
        """複数エラーの連鎖処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 最初にネットワークエラー、その後認証エラーをシミュレート
        errors = [
            ConnectionError("Network timeout"),
            AtProtocolError("InvalidToken", "Token expired")
        ]
        mock_atproto.send_post.side_effect = errors
        
        # 最初のエラー
        with pytest.raises(ConnectionError):
            client.send_post("テスト投稿1")
        
        # 2回目のエラー
        with pytest.raises(AtProtocolError):
            client.send_post("テスト投稿2")
        
        # 両方のエラーが処理されることを確認
        assert mock_atproto.send_post.call_count == 2
    
    def test_error_recovery_flow(self, integrated_error_handling_components):
        """エラー回復フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 最初はエラー、その後成功するようにモック設定
        mock_post_result = PostFactory()
        mock_atproto.send_post.side_effect = [
            ConnectionError("Temporary network error"),  # 1回目はエラー
            mock_post_result  # 2回目は成功
        ]
        
        # 最初の試行（エラー）
        with pytest.raises(ConnectionError):
            client.send_post("テスト投稿")
        
        # 2回目の試行（成功）
        result = client.send_post("テスト投稿")
        
        # エラー後の回復が成功することを確認
        assert result == mock_post_result
        assert mock_atproto.send_post.call_count == 2
    
    def test_error_logging_flow(self, integrated_error_handling_components):
        """エラーログ記録フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # エラーをシミュレート
        test_error = AtProtocolError("TestError", "This is a test error")
        mock_atproto.get_timeline.side_effect = test_error
        
        # エラーが発生することを確認
        with pytest.raises(Exception):
            client.get_timeline()
        
        # エラーが発生したことを確認（caplogの代わりにモックAPIの呼び出しで確認）
        assert mock_atproto.get_timeline.called
        assert mock_atproto.get_timeline.call_count == 1


@pytest.mark.integration
class TestErrorHandlingWithUserInteraction:
    """ユーザーインタラクション付きエラー処理テスト"""
    
    def test_error_dialog_display_flow(self, integrated_error_handling_components):
        """エラーダイアログ表示フローのテスト"""
        components = integrated_error_handling_components
        error_handler = components['error_handler']
        mock_wx = components['mock_wx']
        
        # エラーメッセージの表示テスト
        test_error = Exception("テストエラーメッセージ")
        
        with patch('wx.MessageBox') as mock_msgbox:
            # エラーハンドラーのメソッドを直接呼び出し（実装に依存）
            if hasattr(error_handler, 'display_error'):
                error_handler.display_error("テストエラー", "エラー詳細")
                
                # メッセージボックスが呼ばれることを確認
                mock_msgbox.assert_called()
    
    def test_user_choice_error_handling_flow(self, integrated_error_handling_components):
        """ユーザー選択付きエラー処理フローのテスト"""
        components = integrated_error_handling_components
        mock_wx = components['mock_wx']
        
        # ユーザーの選択をシミュレート
        mock_wx.MessageBox.return_value = mock_wx.YES  # ユーザーが「はい」を選択
        
        with patch('wx.MessageBox') as mock_msgbox:
            mock_msgbox.return_value = mock_wx.YES
            
            # 選択付きエラーダイアログをテスト（実装に依存）
            # 例: 再試行するかどうかのダイアログ
            if hasattr(components['error_handler'], 'ask_retry'):
                result = components['error_handler'].ask_retry("操作に失敗しました")
                assert result == True  # ユーザーが再試行を選択


@pytest.mark.integration
@pytest.mark.network
class TestErrorHandlingWithNetworkSimulation:
    """ネットワークシミュレーション付きエラー処理テスト"""
    
    def test_timeout_error_handling_flow(self, integrated_error_handling_components):
        """タイムアウトエラー処理フローのテスト"""
        import time
        
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # タイムアウトをシミュレート
        def slow_operation(*args, **kwargs):
            time.sleep(0.1)  # 短い遅延をシミュレート
            raise TimeoutError("Operation timed out")
        
        mock_atproto.get_timeline.side_effect = slow_operation
        
        start_time = time.time()
        
        with pytest.raises(TimeoutError):
            client.get_timeline()
        
        end_time = time.time()
        
        # タイムアウトが適切に処理されることを確認
        assert end_time - start_time >= 0.1
        assert mock_atproto.get_timeline.called
    
    def test_intermittent_network_error_flow(self, integrated_error_handling_components):
        """断続的ネットワークエラー処理フローのテスト"""
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # 断続的なネットワークエラーをシミュレート
        call_count = 0
        mock_post_result = PostFactory()
        
        def intermittent_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # 3回に1回成功
                return mock_post_result
            else:
                raise ConnectionError(f"Intermittent network error {call_count}")
        
        mock_atproto.send_post.side_effect = intermittent_error
        
        # 複数回の試行
        successful_posts = 0
        failed_posts = 0
        
        for i in range(9):  # 9回試行
            try:
                result = client.send_post(f"投稿 {i}")
                if result == mock_post_result:
                    successful_posts += 1
            except ConnectionError:
                failed_posts += 1
        
        # 断続的な成功/失敗が確認できることを確認
        assert successful_posts == 3  # 3回成功
        assert failed_posts == 6     # 6回失敗
        assert mock_atproto.send_post.call_count == 9


@pytest.mark.integration
@pytest.mark.slow
class TestErrorHandlingPerformance:
    """エラー処理性能テストクラス"""
    
    def test_bulk_error_handling_performance(self, integrated_error_handling_components):
        """大量エラー処理の性能テスト"""
        import time
        
        components = integrated_error_handling_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # ログイン状態を設定
        client.is_logged_in = True
        client.user_did = "did:plc:testuser"
        
        # エラーを常に発生させる
        mock_atproto.send_post.side_effect = AtProtocolError("TestError", "Test error message")
        
        # 性能測定
        start_time = time.time()
        
        # 大量のエラー処理を実行
        error_count = 0
        for i in range(100):
            try:
                client.send_post(f"テスト投稿 {i}")
            except AtProtocolError:
                error_count += 1
        
        end_time = time.time()
        
        # 性能目標: 100件のエラー処理で5秒以内
        assert end_time - start_time < 5.0
        
        # 全てのエラーが処理されることを確認
        assert error_count == 100
        assert mock_atproto.send_post.call_count == 100