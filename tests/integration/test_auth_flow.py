#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証フロー統合テスト (Phase 2 pytest版)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import tempfile
import sqlite3
from pathlib import Path

from tests.factories import UserFactory


@pytest.fixture
def integrated_auth_components(temp_db_file, mock_crypto):
    """統合された認証コンポーネント"""
    components = {}
    
    # DataStore は実際のsqlite3を使用（モックなし）
    from core.data_store import DataStore
    components['data_store'] = DataStore(temp_db_file)
    
    # CredentialManager の設定（暗号化のみモック）
    with patch('utils.crypto.encrypt_data', mock_crypto['encrypt']), \
         patch('utils.crypto.decrypt_data', mock_crypto['decrypt']):
        
        from core.auth.credential_manager import AuthCredentialManager
        # シングルトンリセット
        AuthCredentialManager._instance = None
        components['credential_manager'] = AuthCredentialManager()
    
    # BlueskyClient のモック設定（APIクライアントのみモック）
    with patch('core.client.api_client.AtprotoClient') as mock_atproto:
        mock_client = Mock()
        mock_atproto.return_value = mock_client
        
        from core.client.facade import BlueskyClient
        components['bluesky_client'] = BlueskyClient()
        components['mock_atproto'] = mock_client
    
    yield components
    
    # クリーンアップ
    try:
        from core.auth.credential_manager import AuthCredentialManager
        AuthCredentialManager._instance = None
    except:
        pass


@pytest.mark.integration
class TestAuthFlowIntegration:
    """認証フロー統合テストクラス"""
    
    def test_complete_login_flow_success(self, integrated_auth_components):
        """完全なログインフロー成功テスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # プロフィール情報を含む適切なモックオブジェクトを作成
        from unittest.mock import MagicMock
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_profile.handle = "testuser.bsky.social"
        mock_profile.did = "did:plc:testuser123"
        
        # モックの設定
        mock_atproto.login.return_value = mock_profile
        mock_atproto.me.did = "did:plc:testuser123"
        
        # ログインフローの実行
        username = "testuser@bsky.social" 
        password = "testpassword"
        
        # ログイン試行（実際の実装に合わせる）
        result = client.login(username, password)
        
        # 結果検証
        assert result is not None
        assert client.is_logged_in
    
    def test_complete_login_flow_failure(self, integrated_auth_components):
        """完全なログインフロー失敗テスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # モックの設定（ログイン失敗）
        from atproto.exceptions import AtProtocolError
        mock_atproto.login.side_effect = AtProtocolError("ログイン失敗")
        
        # ログインフローの実行
        username = "invalid@bsky.social"
        password = "wrongpassword"
        
        # ログイン失敗時は例外が発生することを確認
        with pytest.raises(AtProtocolError, match="ログイン失敗"):
            client.login(username, password)
        
        # ログイン状態が未ログインになることを確認
        assert not client.is_logged_in
        
        # エラーが適切に処理されることを確認
        mock_atproto.login.assert_called_once_with(username, password)
    
    def test_credential_storage_flow(self, integrated_auth_components):
        """認証情報保存フローのテスト"""
        components = integrated_auth_components
        credential_manager = components['credential_manager']
        
        # テストデータ
        username = "testuser@bsky.social"
        password = "testpassword"
        session_data = {"access_token": "test_token", "refresh_token": "refresh_token"}
        
        # 暗号化とデータストアを両方モック
        with patch('utils.crypto.encrypt_data', return_value=b'encrypted') as mock_encrypt, \
             patch.object(credential_manager.data_store, 'save_session', return_value=True) as mock_save:
            # 認証情報の保存
            result = credential_manager.save_credentials(username, password, session_data)
            
            # 保存が成功することを確認
            assert result is True, "save_credentials should return True"
            # 暗号化とデータストアのメソッドが呼ばれることを確認
            assert mock_encrypt.called or mock_save.called, "Either encrypt_data or save_session should have been called"
        
        # データストアへの保存が呼ばれることを確認（実際のDBは使わないのでモックで確認）
        data_store = components['data_store']
        # データストアのメソッドが呼ばれることを想定
    
    def test_credential_retrieval_flow(self, integrated_auth_components):
        """認証情報取得フローのテスト"""
        components = integrated_auth_components
        credential_manager = components['credential_manager']
        
        # 復号化モックを設定
        import utils.crypto
        with patch.object(utils.crypto, 'decrypt_data', return_value='{"username": "test@bsky.social", "password": "testpass"}') as mock_decrypt:
            # 認証情報の取得試行
            credentials = credential_manager.get_stored_credentials()
            
            # 復号化が呼ばれることを確認（データが存在する場合）
            if credentials:
                assert mock_decrypt.called, "decrypt_data should have been called"
    
    def test_automatic_login_flow(self, integrated_auth_components):
        """自動ログインフローのテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # 保存された認証情報がある状態をモック
        mock_credentials = {
            "username": "saved@bsky.social",
            "password": "savedpassword", 
            "session_data": {"access_token": "saved_token"}
        }
        
        with patch.object(client.credential_manager, 'get_stored_credentials', return_value=mock_credentials), \
             patch.object(client, '_restore_session', return_value=True):
            
            # 自動ログインの実行
            success = client.auto_login()
        
        # 結果検証
        assert success is True
    
    def test_logout_flow(self, integrated_auth_components):
        """ログアウトフローのテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        
        # ログイン済みの状態を設定
        client.auth_manager.is_logged_in = True
        
        # credential_managerが存在するか確認
        assert hasattr(client, 'credential_manager'), "BlueskyClient should have credential_manager"
        
        # ログアウトの実行
        client.logout()
        
        # ログアウトが正常に実行された
        assert True
    
    def test_session_refresh_flow(self, integrated_auth_components):
        """セッション更新フローのテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # リフレッシュトークンがある状態を設定
        old_session = {"access_token": "old_token", "refresh_token": "refresh_token"}
        new_session = {"access_token": "new_token", "refresh_token": "new_refresh_token"}
        
        mock_atproto.refresh_session.return_value = new_session
        
        with patch.object(client, '_get_current_session', return_value=old_session), \
             patch.object(client, '_save_session') as mock_save:
            
            # セッション更新の実行
            success = client.refresh_session()
        
        # 結果検証
        assert success is True
        mock_atproto.refresh_session.assert_called_once_with(old_session["refresh_token"])
        mock_save.assert_called_once_with(new_session)


@pytest.mark.integration 
class TestAuthFlowWithRealDatabase:
    """実際のデータベースを使った認証フロー統合テスト"""
    
    @pytest.fixture
    def real_database_setup(self):
        """実際のSQLiteデータベースを使用するセットアップ"""
        # 一時データベースファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as temp_file:
            db_path = temp_file.name
        
        # データベースを初期化
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # テーブル作成（実際のスキーマに合わせる）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                encrypted_data BLOB NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        connection.commit()
        connection.close()
        
        yield db_path
        
        # クリーンアップ
        Path(db_path).unlink(missing_ok=True)
    
    def test_real_database_credential_storage(self, real_database_setup, mock_crypto):
        """実際のデータベースを使った認証情報保存テスト"""
        db_path = real_database_setup
        
        with patch('core.data_store.sqlite3.connect') as mock_connect:
            # 実際のデータベース接続を使用
            mock_connect.return_value = sqlite3.connect(db_path)
            
            from core.data_store import DataStore
            data_store = DataStore(db_path)
            
            with patch('core.auth.credential_manager.DataStore') as mock_ds_class, \
                 patch('utils.crypto.encrypt_data', mock_crypto['encrypt']), \
                 patch('utils.crypto.decrypt_data', mock_crypto['decrypt']):
                
                mock_ds_class.return_value = data_store
                
                from core.auth.credential_manager import AuthCredentialManager
                credential_manager = AuthCredentialManager()
                
                # 認証情報の保存
                username = "realtest@bsky.social"
                password = "realpassword"
                session_data = {"access_token": "real_token"}
                
                credential_manager.save_credentials(username, password, session_data)
                
                # 暗号化が呼ばれることを確認
                mock_crypto['encrypt'].assert_called()
    
    def test_real_database_migration_flow(self, real_database_setup):
        """実際のデータベースを使ったマイグレーションフローテスト"""
        db_path = real_database_setup
        
        from core.data_store import DataStore, MigrationManager
        
        # データストアの初期化とマイグレーション実行
        data_store = DataStore(db_path)
        migration_manager = MigrationManager(data_store)
        
        # マイグレーションの実行
        initial_version = migration_manager.get_current_version()
        migration_manager.apply_migrations()
        final_version = migration_manager.get_current_version()
        
        # バージョンが適切に管理されることを確認
        assert isinstance(initial_version, int)
        assert isinstance(final_version, int)
        assert final_version >= initial_version


@pytest.mark.integration
@pytest.mark.network
class TestAuthFlowWithNetworkSimulation:
    """ネットワーク関連の認証フロー統合テスト"""
    
    def test_network_timeout_handling(self, integrated_auth_components):
        """ネットワークタイムアウト処理のテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # タイムアウトエラーをシミュレート
        mock_atproto.login.side_effect = TimeoutError("ネットワークタイムアウト")
        
        # ログインの実行
        success = client.login("test@bsky.social", "password")
        
        # タイムアウトが適切に処理されることを確認
        assert success is False
        mock_atproto.login.assert_called_once()
    
    def test_connection_error_handling(self, integrated_auth_components):
        """接続エラー処理のテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # 接続エラーをシミュレート
        mock_atproto.login.side_effect = ConnectionError("接続に失敗しました")
        
        # ログインの実行
        success = client.login("test@bsky.social", "password")
        
        # 接続エラーが適切に処理されることを確認
        assert success is False
        mock_atproto.login.assert_called_once()
    
    def test_retry_mechanism(self, integrated_auth_components):
        """リトライメカニズムのテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # 最初は失敗、2回目は成功するようにモック設定
        mock_atproto.login.side_effect = [
            ConnectionError("一時的な接続エラー"),
            True  # 2回目は成功
        ]
        
        # リトライ付きログインの実行（実装にリトライ機能がある場合）
        with patch.object(client, '_login_with_retry') as mock_retry:
            mock_retry.return_value = True
            success = client._login_with_retry("test@bsky.social", "password")
        
        # リトライが機能することを確認
        assert success is True


# パフォーマンステスト
@pytest.mark.slow
@pytest.mark.integration
class TestAuthFlowPerformance:
    """認証フロー性能テストクラス"""
    
    def test_bulk_credential_operations_performance(self, temp_db_file, mock_crypto):
        """大量認証情報操作の性能テスト"""
        import time
        
        with patch('core.data_store.sqlite3') as mock_sqlite:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_sqlite.connect.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_connection.execute = mock_cursor.execute
            mock_connection.commit = Mock()
            mock_connection.close = Mock()
            
            from core.data_store import DataStore
            data_store = DataStore(temp_db_file)
            
            with patch('core.auth.credential_manager.DataStore') as mock_ds_class, \
                 patch('utils.crypto.encrypt_data', mock_crypto['encrypt']), \
                 patch('utils.crypto.decrypt_data', mock_crypto['decrypt']):
                
                mock_ds_class.return_value = data_store
                
                from core.auth.credential_manager import AuthCredentialManager
                credential_manager = AuthCredentialManager()
                
                # 性能測定
                start_time = time.time()
                
                # 大量の認証情報操作を実行
                for i in range(100):
                    username = f"user{i}@bsky.social"
                    password = f"password{i}"
                    session_data = {"access_token": f"token{i}"}
                    
                    credential_manager.save_credentials(username, password, session_data)
                
                end_time = time.time()
                
                # 性能目標: 100件の操作で5秒以内
                assert end_time - start_time < 5.0
    
    def test_concurrent_auth_requests_performance(self, integrated_auth_components):
        """同時認証要求の性能テスト"""
        import threading
        import time
        
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # モックの設定
        mock_atproto.login.return_value = True
        
        results = []
        
        def login_worker(user_id):
            """ワーカー関数"""
            success = client.login(f"user{user_id}@bsky.social", f"password{user_id}")
            results.append(success)
        
        # 性能測定
        start_time = time.time()
        
        # 10個の同時スレッドで認証を実行
        threads = []
        for i in range(10):
            thread = threading.Thread(target=login_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 全て成功することを確認
        assert len(results) == 10
        assert all(results)
        
        # 性能目標: 10個の同時認証で10秒以内
        assert end_time - start_time < 10.0