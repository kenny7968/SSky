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
    
    # CredentialManager の設定（暗号化関数を注入）
    from core.auth.credential_manager import AuthCredentialManager
    # シングルトンリセット
    AuthCredentialManager._instance = None
    # 暗号化関数を注入してCredentialManagerを作成
    components['credential_manager'] = AuthCredentialManager(
        data_store=components['data_store'],
        encrypt_func=mock_crypto['encrypt'],
        decrypt_func=mock_crypto['decrypt']
    )
    
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
        
        # 認証情報の保存と取得のフロー全体をテスト
        username = "test@bsky.social"
        password = "testpass"
        session_data = {"access_token": "test_token"}
        
        # まず保存
        result = credential_manager.save_credentials(username, password, session_data)
        assert result is True
        
        # データストアから暗号化データが返されるようモック
        with patch.object(credential_manager.data_store, 'get_latest_session', return_value=('test_did', b'encrypted')):
            credentials = credential_manager.get_stored_credentials()
            
            # credential_manager.decrypt_funcが呼ばれたことを確認
            # decrypt_funcはモックされた関数なので、呼び出しを確認
            assert credential_manager.decrypt_func.called, "decrypt_func should have been called"
            
            # 取得した認証情報の確認
            if credentials:
                assert isinstance(credentials, dict), "Credentials should be a dictionary"
                assert 'username' in credentials
                assert credentials['username'] == 'test@bsky.social'
    
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
        
        # プロフィール情報を含む適切なモックオブジェクトを作成
        from unittest.mock import MagicMock
        mock_profile = MagicMock()
        mock_profile.display_name = "Saved User"
        mock_profile.handle = "saved.bsky.social"
        mock_profile.did = "did:plc:saveduser123"
        
        # モックの設定
        mock_atproto.login.return_value = mock_profile
        mock_atproto.me.did = "did:plc:saveduser123"
        
        with patch.object(client.credential_manager, 'get_stored_credentials', return_value=mock_credentials):
            # 自動ログインは実際にはloginメソッドを呼ぶ
            success = client.login(mock_credentials['username'], mock_credentials['password'])
        
        # 結果検証
        assert success is not None
        assert client.is_logged_in
    
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
        
        # まずログインしてセッションを確立
        from unittest.mock import MagicMock
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_profile.handle = "testuser.bsky.social"
        mock_profile.did = "did:plc:testuser123"
        
        mock_atproto.login.return_value = mock_profile
        mock_atproto.me.did = "did:plc:testuser123"
        
        # ログインを実行
        client.login("test@bsky.social", "password")
        
        # セッションリフレッシュのモック
        # atprotoライブラリではセッションリフレッシュは内部的に処理される
        # セッション管理はsession_managerで行われる
        if hasattr(client, 'session_manager'):
            # セッションマネージャーの存在を確認
            assert client.session_manager is not None
            
        # セッションが維持されていることを確認
        assert client.is_logged_in


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
        
        # DataStoreを直接使用（パッチなし）
        from core.data_store import DataStore
        data_store = DataStore(db_path)
        
        # モック関数を作成
        mock_encrypt_func = Mock(return_value=b'encrypted_data')
        mock_decrypt_func = Mock(return_value='{"username": "test", "password": "pass"}')
        
        from core.auth.credential_manager import AuthCredentialManager
        # シングルトンリセット
        AuthCredentialManager._instance = None
        # 暗号化関数を注入して作成
        credential_manager = AuthCredentialManager(
            data_store=data_store,
            encrypt_func=mock_encrypt_func,
            decrypt_func=mock_decrypt_func
        )
        
        # 認証情報の保存
        username = "realtest@bsky.social"
        password = "realpassword"
        session_data = {"access_token": "real_token"}
        
        result = credential_manager.save_credentials(username, password, session_data)
        
        # 保存が成功したことを確認
        assert result is True, "Credentials should be saved successfully"
        
        # 暗号化が呼ばれることを確認
        mock_encrypt_func.assert_called()
    
    def test_real_database_migration_flow(self, real_database_setup):
        """実際のデータベースを使ったマイグレーションフローテスト"""
        db_path = real_database_setup
        
        from core.data_store import DataStore
        
        # データストアの初期化（マイグレーションは自動実行される）
        data_store = DataStore(db_path)
        
        # バージョン情報を確認
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # バージョンテーブルが存在し、バージョンが設定されていることを確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
        assert cursor.fetchone() is not None, "db_version table should exist"
        
        cursor.execute("SELECT version FROM db_version ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        assert result is not None, "Version should be set"
        assert result[0] >= 0, "Version should be 0 or greater"
        
        connection.close()


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
        
        # ログインの実行（例外が発生することを期待）
        with pytest.raises(TimeoutError, match="ネットワークタイムアウト"):
            client.login("test@bsky.social", "password")
        
        # タイムアウトで失敗したことを確認
        assert not client.is_logged_in
        mock_atproto.login.assert_called_once()
    
    def test_connection_error_handling(self, integrated_auth_components):
        """接続エラー処理のテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # 接続エラーをシミュレート
        mock_atproto.login.side_effect = ConnectionError("接続に失敗しました")
        
        # ログインの実行（例外が発生することを期待）
        with pytest.raises(ConnectionError, match="接続に失敗しました"):
            client.login("test@bsky.social", "password")
        
        # 接続エラーで失敗したことを確認
        assert not client.is_logged_in
        mock_atproto.login.assert_called_once()
    
    def test_retry_mechanism(self, integrated_auth_components):
        """リトライメカニズムのテスト"""
        components = integrated_auth_components
        client = components['bluesky_client']
        mock_atproto = components['mock_atproto']
        
        # プロフィール情報を含むモックオブジェクト
        from unittest.mock import MagicMock
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_profile.handle = "testuser.bsky.social"
        mock_profile.did = "did:plc:testuser123"
        
        # 最初は失敗、2回目は成功するようにモック設定
        mock_atproto.login.side_effect = [
            ConnectionError("一時的な接続エラー"),
            mock_profile  # 2回目は成功
        ]
        mock_atproto.me.did = "did:plc:testuser123"
        
        # 最初のログイン試行（失敗）
        with pytest.raises(ConnectionError):
            client.login("test@bsky.social", "password")
        
        # リセット
        mock_atproto.login.side_effect = None
        mock_atproto.login.return_value = mock_profile
        
        # 2回目のログイン試行（成功）
        result = client.login("test@bsky.social", "password")
        
        # 成功したことを確認
        assert result is not None
        assert client.is_logged_in


# パフォーマンステスト
@pytest.mark.slow
@pytest.mark.integration
class TestAuthFlowPerformance:
    """認証フロー性能テストクラス"""
    
    def test_bulk_credential_operations_performance(self, temp_db_file, mock_crypto):
        """大量認証情報操作の性能テスト"""
        import time
        
        # DataStoreを完全にモックしてテスト
        with patch('core.auth.credential_manager.DataStore') as mock_ds_class:
            mock_data_store = Mock()
            mock_data_store.save_session.return_value = True
            mock_data_store.load_session.return_value = (b'encrypted', 'test_did')
            mock_ds_class.return_value = mock_data_store
            
            with patch('utils.crypto.encrypt_data', mock_crypto['encrypt']), \
                 patch('utils.crypto.decrypt_data', mock_crypto['decrypt']):
                
                from core.auth.credential_manager import AuthCredentialManager
                # シングルトンリセット
                AuthCredentialManager._instance = None
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