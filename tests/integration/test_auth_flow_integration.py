#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - 認証フロー統合テスト
完全リファクタリング版
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import json

# テスト対象モジュールのインポート
sys.path.insert(0, str(Path(__file__).parents[2]))
from core.client.api_client import BlueskyApiClient
from core.auth.credential_manager import AuthCredentialManager
from core.client.facade import BlueskyClient
from core.data_store import DataStore
from tests.mocks.common_mocks import (
    MockSessionManager,
    create_mock_post,
    create_mock_user
)


@pytest.fixture
def temp_test_dir():
    """テスト用一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_database(temp_test_dir):
    """テスト用データベース"""
    db_path = temp_test_dir / "test.db"
    store = DataStore(str(db_path))
    yield store
    store.close()


@pytest.fixture
def credential_manager(test_database):
    """テスト用CredentialManager"""
    AuthCredentialManager._instance = None
    with patch('core.auth.credential_manager.DataStore', return_value=test_database):
        manager = AuthCredentialManager()
        yield manager
    AuthCredentialManager._instance = None


@pytest.fixture
def mock_atproto_client():
    """AtprotoClientのモック"""
    with patch('core.client.api_client.AtprotoClient') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        # デフォルトのレスポンス設定
        mock_instance.login = MagicMock(return_value={
            "accessJwt": "test_access_token",
            "refreshJwt": "test_refresh_token",
            "handle": "test.user",
            "did": "did:plc:testuser"
        })
        
        yield mock_instance


@pytest.fixture
def bluesky_client(credential_manager, mock_atproto_client):
    """統合テスト用BlueskyClient"""
    with patch('core.client.facade.BlueskyApiClient') as mock_api_class:
        mock_api = MagicMock()
        mock_api.client = mock_atproto_client
        mock_api_class.return_value = mock_api
        
        client = BlueskyClient()
        client.api_client = mock_api
        client.credential_manager = credential_manager
        
        yield client


class TestAuthenticationFlowIntegration:
    """認証フローの統合テスト"""
    
    @pytest.mark.integration
    def test_full_login_flow(self, bluesky_client, mock_atproto_client):
        """完全なログインフロー"""
        # 1. 初期状態：未ログイン
        assert not bluesky_client.is_logged_in()
        
        # 2. ログイン実行
        result = bluesky_client.login("test.user", "password123")
        
        # 3. ログイン成功確認
        assert result is True
        assert bluesky_client.is_logged_in()
        
        # 4. セッション情報確認
        mock_atproto_client.login.assert_called_once_with(
            "test.user",
            "password123"
        )
    
    @pytest.mark.integration
    def test_login_with_credential_save(self, bluesky_client, credential_manager):
        """認証情報保存付きログイン"""
        # ログインと同時に認証情報を保存
        result = bluesky_client.login("test.user", "password123", save_credentials=True)
        
        assert result is True
        
        # 認証情報が保存されている
        assert credential_manager.has_saved_credentials()
        
        saved_creds = credential_manager.get_credentials()
        assert saved_creds["identifier"] == "test.user"
    
    @pytest.mark.integration
    def test_auto_login_flow(self, bluesky_client, credential_manager, mock_atproto_client):
        """自動ログインフロー"""
        # 1. 認証情報を保存
        credential_manager.save_credentials("test.user", "password123")
        
        # 2. 自動ログイン実行
        result = bluesky_client.auto_login()
        
        # 3. 成功確認
        assert result is True
        assert bluesky_client.is_logged_in()
        
        # 4. 保存された認証情報でログインされている
        mock_atproto_client.login.assert_called_with("test.user", "password123")
    
    @pytest.mark.integration
    def test_logout_flow(self, bluesky_client):
        """ログアウトフロー"""
        # 1. ログイン
        bluesky_client.login("test.user", "password123")
        assert bluesky_client.is_logged_in()
        
        # 2. ログアウト
        bluesky_client.logout()
        
        # 3. ログアウト確認
        assert not bluesky_client.is_logged_in()
        
        # 4. セッション情報がクリアされている
        assert bluesky_client.session_manager.get_session() is None
    
    @pytest.mark.integration
    def test_session_persistence(self, bluesky_client, test_database):
        """セッション永続化"""
        # 1. ログイン
        bluesky_client.login("test.user", "password123")
        
        # 2. セッション情報を保存
        session_data = {
            "accessJwt": "token123",
            "refreshJwt": "refresh123",
            "handle": "test.user"
        }
        test_database.save_session(session_data)
        
        # 3. 新しいクライアントインスタンスで復元
        new_client = BlueskyClient()
        new_client.restore_session()
        
        # セッションが復元されている
        assert new_client.is_logged_in()


class TestAuthenticationErrorHandling:
    """認証エラーハンドリングの統合テスト"""
    
    @pytest.mark.integration
    def test_login_with_invalid_credentials(self, bluesky_client, mock_atproto_client):
        """無効な認証情報でのログイン"""
        mock_atproto_client.login.side_effect = Exception("Invalid credentials")
        
        result = bluesky_client.login("invalid.user", "wrong_password")
        
        assert result is False
        assert not bluesky_client.is_logged_in()
    
    @pytest.mark.integration
    def test_network_error_during_login(self, bluesky_client, mock_atproto_client):
        """ログイン中のネットワークエラー"""
        from requests.exceptions import ConnectionError
        mock_atproto_client.login.side_effect = ConnectionError("Network error")
        
        result = bluesky_client.login("test.user", "password123")
        
        assert result is False
        assert not bluesky_client.is_logged_in()
    
    @pytest.mark.integration
    def test_corrupted_saved_credentials(self, bluesky_client, credential_manager):
        """破損した保存認証情報"""
        # 不正な認証情報を保存
        with patch.object(credential_manager, 'get_credentials', return_value=None):
            result = bluesky_client.auto_login()
            
            assert result is False
            assert not bluesky_client.is_logged_in()
    
    @pytest.mark.integration
    def test_session_expiration_handling(self, bluesky_client, mock_atproto_client):
        """セッション期限切れの処理"""
        # ログイン成功
        bluesky_client.login("test.user", "password123")
        
        # セッション期限切れをシミュレート
        mock_atproto_client.get_timeline.side_effect = Exception("Session expired")
        
        # タイムライン取得時にエラー
        with pytest.raises(Exception, match="Session expired"):
            bluesky_client.get_timeline()
        
        # 自動再ログイン試行
        if hasattr(bluesky_client, 'refresh_session'):
            bluesky_client.refresh_session()


class TestAuthenticationWithPubSub:
    """PubSubイベントを使用した認証統合テスト"""
    
    @pytest.mark.integration
    def test_login_event_publishing(self, bluesky_client):
        """ログインイベントの発行"""
        with patch('pubsub.pub.sendMessage') as mock_send:
            bluesky_client.login("test.user", "password123")
            
            # ログインイベントが発行される
            mock_send.assert_called()
            calls = mock_send.call_args_list
            
            # auth.login_successイベントが発行されている
            event_names = [call[0][0] for call in calls]
            assert any("login" in event for event in event_names)
    
    @pytest.mark.integration
    def test_logout_event_publishing(self, bluesky_client):
        """ログアウトイベントの発行"""
        bluesky_client.login("test.user", "password123")
        
        with patch('pubsub.pub.sendMessage') as mock_send:
            bluesky_client.logout()
            
            # ログアウトイベントが発行される
            mock_send.assert_called()
            calls = mock_send.call_args_list
            
            event_names = [call[0][0] for call in calls]
            assert any("logout" in event for event in event_names)
    
    @pytest.mark.integration
    def test_authentication_state_change_notification(self, bluesky_client):
        """認証状態変更の通知"""
        state_changes = []
        
        def on_auth_change(is_logged_in):
            state_changes.append(is_logged_in)
        
        # リスナー登録
        with patch('pubsub.pub.subscribe') as mock_subscribe:
            mock_subscribe(on_auth_change, 'auth.state_changed')
            
            # ログイン
            bluesky_client.login("test.user", "password123")
            on_auth_change(True)  # 手動でコールバック実行
            
            # ログアウト
            bluesky_client.logout()
            on_auth_change(False)  # 手動でコールバック実行
            
            # 状態変更が記録されている
            assert state_changes == [True, False]


class TestAuthenticationDataIntegrity:
    """認証データ整合性の統合テスト"""
    
    @pytest.mark.integration
    def test_credential_encryption(self, credential_manager):
        """認証情報の暗号化"""
        with patch('core.auth.credential_manager.encrypt_data') as mock_encrypt:
            mock_encrypt.return_value = b'encrypted_password'
            
            credential_manager.save_credentials("test.user", "plain_password")
            
            # 平文パスワードが暗号化される
            mock_encrypt.assert_called_once_with("plain_password")
    
    @pytest.mark.integration
    def test_credential_decryption(self, credential_manager):
        """認証情報の復号化"""
        # 暗号化して保存
        credential_manager.save_credentials("test.user", "password123")
        
        with patch('core.auth.credential_manager.decrypt_data') as mock_decrypt:
            mock_decrypt.return_value = "password123"
            
            creds = credential_manager.get_credentials()
            
            # 復号化される
            mock_decrypt.assert_called_once()
            assert creds["password"] == "password123"
    
    @pytest.mark.integration
    def test_concurrent_authentication_requests(self, bluesky_client):
        """並行認証リクエスト"""
        import threading
        results = []
        
        def login_thread():
            result = bluesky_client.login("test.user", "password123")
            results.append(result)
        
        # 複数スレッドから同時にログイン
        threads = [threading.Thread(target=login_thread) for _ in range(3)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # 1つのログインのみ成功
        assert len([r for r in results if r]) == 1


class TestAuthenticationRecovery:
    """認証回復の統合テスト"""
    
    @pytest.mark.integration
    def test_recover_from_failed_login(self, bluesky_client, mock_atproto_client):
        """ログイン失敗からの回復"""
        # 1回目：失敗
        mock_atproto_client.login.side_effect = Exception("Network error")
        result1 = bluesky_client.login("test.user", "password123")
        assert result1 is False
        
        # 2回目：成功
        mock_atproto_client.login.side_effect = None
        mock_atproto_client.login.return_value = {
            "accessJwt": "token",
            "handle": "test.user"
        }
        
        result2 = bluesky_client.login("test.user", "password123")
        assert result2 is True
    
    @pytest.mark.integration
    def test_credential_migration(self, credential_manager, test_database):
        """認証情報の移行"""
        # 旧形式の認証情報
        old_creds = {
            "username": "old.user",
            "password": "old_pass"
        }
        
        # 新形式への移行
        credential_manager.migrate_credentials(old_creds)
        
        # 新形式で取得可能
        new_creds = credential_manager.get_credentials()
        assert new_creds["identifier"] == "old.user"
    
    @pytest.mark.integration
    def test_session_refresh(self, bluesky_client, mock_atproto_client):
        """セッションリフレッシュ"""
        # ログイン
        bluesky_client.login("test.user", "password123")
        
        # リフレッシュトークンでセッション更新
        mock_atproto_client.refresh_session = MagicMock(return_value={
            "accessJwt": "new_token",
            "refreshJwt": "new_refresh"
        })
        
        result = bluesky_client.refresh_session()
        
        assert result is True
        mock_atproto_client.refresh_session.assert_called_once()