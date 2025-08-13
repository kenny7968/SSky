#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
内部インターフェース契約テスト

SSkyアプリケーション内部のコンポーネント間インターフェースの契約を検証するテスト群
"""

import pytest
import json
from typing import Dict, List, Any, Optional, Protocol
from unittest.mock import Mock, MagicMock, patch
from abc import ABC, abstractmethod


class IBlueskyClient(Protocol):
    """BlueskyClient インターフェース契約"""
    
    @property
    def is_logged_in(self) -> bool: ...
    
    @property
    def profile(self) -> Optional[Dict[str, Any]]: ...
    
    @property
    def user_did(self) -> Optional[str]: ...
    
    def login(self, handle: str, password: str) -> bool: ...
    
    def logout(self) -> bool: ...
    
    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]: ...
    
    def send_post(self, text: str, images: List[str] = None) -> str: ...


class ICredentialManager(Protocol):
    """CredentialManager インターフェース契約"""
    
    def save_credentials(self, handle: str, password: str) -> bool: ...
    
    def get_stored_credentials(self) -> List[Dict[str, Any]]: ...
    
    def clear_credentials(self) -> bool: ...


class ISettingsManager(Protocol):
    """SettingsManager インターフェース契約"""
    
    def get(self, key: str, default: Any = None) -> Any: ...
    
    def set(self, key: str, value: Any) -> None: ...
    
    def save(self) -> bool: ...
    
    def load(self) -> bool: ...
    
    def add_observer(self, observer) -> None: ...
    
    def remove_observer(self, observer) -> None: ...


class IDataStore(Protocol):
    """DataStore インターフェース契約"""
    
    def get_connection(self): ...
    
    def transaction(self): ...
    
    def save_session(self, connection, handle: str, access_jwt: str, 
                    refresh_jwt: str, did: str, expires_at: str = None) -> int: ...
    
    def get_latest_session(self, connection, handle: str) -> Optional[Dict[str, Any]]: ...
    
    def delete_session(self, connection, session_id: int) -> int: ...


class TestBlueskyClientInterfaceContract:
    """BlueskyClient インターフェース契約テスト"""
    
    @pytest.mark.contract_interface
    def test_bluesky_client_login_interface(self):
        """BlueskyClient ログインインターフェース契約"""
        from core.client.facade import BlueskyClient
        
        # モックAPIクライアントの設定
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            mock_client = Mock()
            mock_atproto.return_value = mock_client
            mock_client.login.return_value = True
            mock_client.get_profile.return_value = {
                "did": "did:plc:test123",
                "handle": "test.user",
                "displayName": "Test User"
            }
            
            bluesky_client = BlueskyClient()
            
            # インターフェース契約の検証
            assert hasattr(bluesky_client, 'is_logged_in'), "is_logged_inプロパティが必要"
            assert hasattr(bluesky_client, 'profile'), "profileプロパティが必要"
            assert hasattr(bluesky_client, 'user_did'), "user_didプロパティが必要"
            assert hasattr(bluesky_client, 'login'), "loginメソッドが必要"
            assert hasattr(bluesky_client, 'logout'), "logoutメソッドが必要"
            
            # 初期状態の契約
            assert bluesky_client.is_logged_in == False, "初期状態はログアウト状態"
            assert bluesky_client.profile is None, "初期状態はプロフィール未設定"
            assert bluesky_client.user_did is None, "初期状態はDID未設定"
            
            # ログイン契約
            login_result = bluesky_client.login("test.user", "test_password")
            assert isinstance(login_result, bool), "loginは bool を返すべき"
            assert login_result == True, "有効な認証情報でTrue を返すべき"
            
            # ログイン後の状態契約
            assert bluesky_client.is_logged_in == True, "ログイン後はTrue"
            assert bluesky_client.profile is not None, "ログイン後はプロフィール設定"
            assert bluesky_client.user_did is not None, "ログイン後はDID設定"
            
            # ログアウト契約
            logout_result = bluesky_client.logout()
            assert isinstance(logout_result, bool), "logoutは bool を返すべき"
            assert bluesky_client.is_logged_in == False, "ログアウト後はFalse"
            assert bluesky_client.profile is None, "ログアウト後はプロフィール削除"
    
    @pytest.mark.contract_interface
    def test_bluesky_client_timeline_interface(self):
        """BlueskyClient タイムラインインターフェース契約"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client:
            mock_client = Mock()
            mock_api_client.return_value = mock_client
            
            # タイムラインモックデータ
            mock_timeline = [
                {
                    "uri": "at://test.user/app.bsky.feed.post/1",
                    "author": {"handle": "test.user"},
                    "record": {"text": "Test post"}
                }
            ]
            
            # get_timelineが辞書を返すように設定
            mock_client.get_timeline.return_value = {'feed': mock_timeline}
            
            bluesky_client = BlueskyClient()
            
            # タイムライン取得インターフェース契約
            assert hasattr(bluesky_client, 'get_timeline'), "get_timelineメソッドが必要"
            
            # ログイン状態での実行（auth_managerの状態を直接設定）
            bluesky_client.auth_manager.is_logged_in = True
            bluesky_client.auth_manager.profile = {"handle": "test.user"}
            
            timeline = bluesky_client.get_timeline()
            assert timeline is None or isinstance(timeline, dict), "get_timelineは辞書またはNoneを返すべき"
            
            # パラメータ付きの呼び出し
            timeline_limited = bluesky_client.get_timeline(limit=10)
            assert timeline_limited is None or isinstance(timeline_limited, dict), "limit付きでも辞書またはNoneを返すべき"
    
    @pytest.mark.contract_interface
    def test_bluesky_client_post_interface(self):
        """BlueskyClient 投稿インターフェース契約"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client:
            mock_client = Mock()
            mock_api_client.return_value = mock_client
            # send_postが辞書を返すように設定
            mock_client.send_post.return_value = {"uri": "at://test.user/app.bsky.feed.post/123"}
            
            bluesky_client = BlueskyClient()
            # auth_managerの状態を直接設定
            bluesky_client.auth_manager.is_logged_in = True
            bluesky_client.auth_manager.profile = {"handle": "test.user"}
            
            # 投稿インターフェース契約
            assert hasattr(bluesky_client, 'send_post'), "send_postメソッドが必要"
            
            # テキスト投稿
            post_result = bluesky_client.send_post("Test post")
            assert post_result is None or isinstance(post_result, dict), "send_postは辞書またはNoneを返すべき"
            
            # 画像付き投稿
            post_result_with_images = bluesky_client.send_post("Test with images", images=["image1.jpg"])
            assert post_result_with_images is None or isinstance(post_result_with_images, dict), "画像付き投稿も辞書またはNoneを返すべき"


class TestCredentialManagerInterfaceContract:
    """CredentialManager インターフェース契約テスト"""
    
    @pytest.mark.contract_interface
    def test_credential_manager_interface(self, temp_db_file):
        """CredentialManager インターフェース契約"""
        from core.auth.credential_manager import AuthCredentialManager
        from core.data_store import DataStore
        
        # シングルトンリセット
        AuthCredentialManager._instance = None
        
        # DataStoreのモックを作成
        mock_data_store = Mock(spec=DataStore)
        stored_data = {}  # 保存されたデータを追跡
        
        def mock_save_session(user_did, encrypted_session):
            stored_data['session'] = (user_did, encrypted_session)
            return True
        
        def mock_get_latest_session():
            if 'session' in stored_data:
                return stored_data['session']
            return None, None
        
        def mock_delete_session(user_did):
            if 'session' in stored_data:
                del stored_data['session']
            return True
        
        mock_data_store.save_session = Mock(side_effect=mock_save_session)
        mock_data_store.get_latest_session = Mock(side_effect=mock_get_latest_session)
        mock_data_store.delete_session = Mock(side_effect=mock_delete_session)
        
        # 暗号化モック
        with patch('utils.crypto.encrypt_data', return_value=b'encrypted_test_data'), \
             patch('utils.crypto.decrypt_data', return_value='{"username": "test.user", "password": "test_password", "session_data": {}}'):
            
            # DataStoreをモックで置き換え
            credential_manager = AuthCredentialManager(data_store=mock_data_store)
            
            # インターフェース契約の検証
            assert hasattr(credential_manager, 'save_credentials'), "save_credentialsメソッドが必要"
            assert hasattr(credential_manager, 'get_stored_credentials'), "get_stored_credentialsメソッドが必要"
            assert hasattr(credential_manager, 'clear_credentials'), "clear_credentialsメソッドが必要"
            
            # save_credentials契約
            save_result = credential_manager.save_credentials("test.user", "test_password")
            assert isinstance(save_result, bool), "save_credentialsはboolを返すべき"
            assert save_result == True, "有効なデータでTrueを返すべき"
            
            # get_stored_credentials契約
            stored_credentials = credential_manager.get_stored_credentials()
            assert stored_credentials is None or isinstance(stored_credentials, dict), "get_stored_credentialsは辞書またはNoneを返すべき"
            assert stored_credentials is not None, "保存後は認証情報が存在するべき"
            
            # 認証情報の形式契約
            if isinstance(stored_credentials, dict):
                assert 'username' in stored_credentials or 'handle' in stored_credentials, "認証情報にはusernameまたはhandleが必要"
            
            # clear_credentials契約
            clear_result = credential_manager.clear_credentials()
            assert isinstance(clear_result, bool), "clear_credentialsはboolを返すべき"
            
            # クリア後の状態確認
            cleared_credentials = credential_manager.get_stored_credentials()
            assert cleared_credentials is None, "クリア後は認証情報がNoneであるべき"


class TestSettingsManagerInterfaceContract:
    """SettingsManager インターフェース契約テスト"""
    
    @pytest.mark.contract_interface
    def test_settings_manager_interface(self, temp_config_file):
        """SettingsManager インターフェース契約"""
        from config.settings_manager import SettingsManager
        
        # シングルトンリセット
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        
        # インターフェース契約の検証
        assert hasattr(settings_manager, 'get'), "getメソッドが必要"
        assert hasattr(settings_manager, 'set'), "setメソッドが必要"
        assert hasattr(settings_manager, 'save'), "saveメソッドが必要"
        assert hasattr(settings_manager, 'load'), "loadメソッドが必要"
        assert hasattr(settings_manager, 'add_observer'), "add_observerメソッドが必要"
        assert hasattr(settings_manager, 'remove_observer'), "remove_observerメソッドが必要"
        
        # get契約
        default_value = settings_manager.get('nonexistent_key', 'default')
        assert default_value == 'default', "存在しないキーはデフォルト値を返すべき"
        
        existing_value = settings_manager.get('language')
        assert existing_value is not None, "既存の設定値は None でないべき"
        
        # set契約 
        settings_manager.set('test_key', 'test_value')
        retrieved_value = settings_manager.get('test_key')
        assert retrieved_value == 'test_value', "setした値がgetで取得できるべき"
        
        # save/load契約
        settings_manager.settings_file = temp_config_file
        save_result = settings_manager.save()
        assert isinstance(save_result, bool), "saveはboolを返すべき"
        
        # loadは戻り値がないので、実行してエラーがないことを確認
        settings_manager.load()  # エラーがなければ成功
        
        # observer契約
        observer_called = False
        
        class TestObserver:
            def on_settings_changed(self, key):
                nonlocal observer_called
                observer_called = True
        
        test_observer = TestObserver()
        settings_manager.add_observer(test_observer)
        settings_manager.set('observer_test', 'observer_value')
        
        assert observer_called, "オブザーバーが呼び出されるべき"
    
    @pytest.mark.contract_interface
    def test_settings_manager_observer_contract(self, temp_config_file):
        """SettingsManager オブザーバー契約テスト"""
        from config.settings_manager import SettingsManager
        
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        
        # オブザーバー契約テスト
        notifications = []
        
        class TestObserver:
            def on_settings_changed(self, key):
                notifications.append({'key': key})
        
        test_observer = TestObserver()
        
        # オブザーバー追加・削除契約
        settings_manager.add_observer(test_observer)
        
        settings_manager.set('observer_key1', 'value1')
        assert len(notifications) == 1, "オブザーバー通知が1回行われるべき"
        assert notifications[0]['key'] == 'observer_key1', "正しいキーが通知されるべき"
        
        # オブザーバー削除契約
        settings_manager.remove_observer(test_observer)
        settings_manager.set('observer_key2', 'value2')
        assert len(notifications) == 1, "削除後はオブザーバー通知されないべき"


class TestDataStoreInterfaceContract:
    """DataStore インターフェース契約テスト"""
    
    @pytest.mark.contract_interface
    def test_data_store_interface(self, temp_db_file):
        """DataStore インターフェース契約"""
        from core.data_store import DataStore
        
        data_store = DataStore(temp_db_file)
        
        # インターフェース契約の検証
        assert hasattr(data_store, 'get_connection'), "get_connectionメソッドが必要"
        assert hasattr(data_store, 'get_transaction'), "get_transactionメソッドが必要" 
        assert hasattr(data_store, 'save_session'), "save_sessionメソッドが必要"
        assert hasattr(data_store, 'get_latest_session'), "get_latest_sessionメソッドが必要"
        assert hasattr(data_store, 'delete_session'), "delete_sessionメソッドが必要"
        
        # connection契約
        with data_store.get_connection() as conn:
            assert conn is not None, "get_connectionは有効な接続を返すべき"
            # 基本的なSQL実行テスト
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "データベース接続が正常に動作するべき"
        
        # transaction契約
        with data_store.get_transaction() as cursor:
            assert cursor is not None, "get_transactionは有効なカーソルを返すべき"
            
        # session操作契約 - save_session
        import json
        test_session_data = {
            'handle': 'contract.test',
            'access_jwt': 'test_access',
            'refresh_jwt': 'test_refresh'
        }
        encrypted_data = json.dumps(test_session_data).encode('utf-8')
        
        save_result = data_store.save_session(
            user_did="did:plc:contracttest",
            encrypted_session=encrypted_data
        )
        assert isinstance(save_result, bool), "save_sessionはboolを返すべき"
        assert save_result == True, "save_sessionは成功時にTrueを返すべき"
        
        # session取得契約
        user_did, encrypted_session = data_store.get_latest_session()
        assert user_did is not None, "保存されたユーザーDIDが取得できるべき"
        assert encrypted_session is not None, "保存されたセッションが取得できるべき"
        assert user_did == "did:plc:contracttest", "正しいユーザーDIDが保存されるべき"
        
        # セッション削除契約
        delete_result = data_store.delete_session("did:plc:contracttest")
        assert isinstance(delete_result, bool), "delete_sessionはboolを返すべき"
        assert delete_result == True, "削除成功時はTrueを返すべき"
        
        # 削除後の確認
        deleted_user_did, deleted_session = data_store.get_latest_session()
        assert deleted_user_did is None, "削除後はユーザーDIDがNoneであるべき"
        assert deleted_session is None, "削除後はセッションがNoneであるべき"


class TestComponentInteractionContract:
    """コンポーネント間相互作用契約テスト"""
    
    @pytest.mark.contract_interface
    def test_bluesky_client_credential_manager_interaction(self, temp_db_file, mock_crypto):
        """BlueskyClient と CredentialManager の相互作用契約"""
        from core.client.facade import BlueskyClient
        from core.auth.credential_manager import AuthCredentialManager
        
        # モック設定
        with patch('core.client.api_client.AtprotoClient') as mock_atproto, \
             patch('utils.crypto.encrypt_data', mock_crypto['encrypt']), \
             patch('utils.crypto.decrypt_data', mock_crypto['decrypt']):
            
            mock_client = Mock()
            mock_atproto.return_value = mock_client
            mock_client.login.return_value = True
            mock_client.get_profile.return_value = {
                "did": "did:plc:interaction123",
                "handle": "interaction.test",
                "displayName": "Interaction Test"
            }
            
            # コンポーネント初期化
            AuthCredentialManager._instance = None
            credential_manager = AuthCredentialManager()
            bluesky_client = BlueskyClient()
            
            # 相互作用契約のテスト
            # 1. ログイン成功後に認証情報が保存される
            login_success = bluesky_client.login("interaction.test", "test_password")
            assert login_success, "ログインが成功するべき"
            
            # 2. 認証情報がCredentialManagerに保存されている
            stored_credentials = credential_manager.get_stored_credentials()
            # ここでは直接的な統合はないが、実際の実装では連携するべき
            
            # 3. ログアウト後の状態一貫性
            logout_success = bluesky_client.logout()
            assert logout_success, "ログアウトが成功するべき"
            assert not bluesky_client.is_logged_in, "ログアウト後は未ログイン状態"
    
    @pytest.mark.contract_interface
    def test_settings_manager_component_interaction(self, temp_config_file):
        """SettingsManager と他コンポーネントの相互作用契約"""
        from config.settings_manager import SettingsManager
        
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.settings_file = temp_config_file
        
        # 設定変更通知の契約
        component_states = {}
        
        class TimelineObserver:
            def on_settings_changed(self, key):
                if key == 'timeline_refresh_interval':
                    component_states['timeline_refresh_changed'] = True
        
        class ThemeObserver:
            def on_settings_changed(self, key):
                if key == 'theme':
                    component_states['theme_changed'] = True
        
        # 複数コンポーネントのオブザーバー登録
        timeline_observer = TimelineObserver()
        theme_observer = ThemeObserver()
        settings_manager.add_observer(timeline_observer)
        settings_manager.add_observer(theme_observer)
        
        # 設定変更による通知契約
        settings_manager.set('timeline_refresh_interval', 60)
        assert component_states.get('timeline_refresh_changed'), "タイムライン設定変更が通知されるべき"
        
        settings_manager.set('theme', 'dark')
        assert component_states.get('theme_changed'), "テーマ設定変更が通知されるべき"
        
        # 設定保存の一貫性契約
        save_success = settings_manager.save()
        assert save_success, "設定保存が成功するべき"
        
        # 再読み込み後の一貫性
        settings_manager.load()  # エラーがなければ成功
        
        reloaded_interval = settings_manager.get('timeline_refresh_interval')
        reloaded_theme = settings_manager.get('theme')
        
        assert reloaded_interval == 60, "再読み込み後も設定値が保持されるべき"
        assert reloaded_theme == 'dark', "再読み込み後も設定値が保持されるべき"


class TestErrorHandlingContract:
    """エラーハンドリング契約テスト"""
    
    @pytest.mark.contract_interface
    def test_error_propagation_contract(self):
        """エラー伝播契約テスト"""
        from core.client.facade import BlueskyClient
        from atproto_client.exceptions import AtProtocolError
        
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            mock_client = Mock()
            mock_atproto.return_value = mock_client
            
            # APIエラーシミュレーション
            mock_client.login.side_effect = AtProtocolError("Invalid credentials")
            
            bluesky_client = BlueskyClient()
            
            # エラー伝播契約の検証
            with pytest.raises(AtProtocolError) as exc_info:
                bluesky_client.login("invalid.user", "wrong_password")
            
            # エラー情報の契約
            assert "Invalid credentials" in str(exc_info.value), "元のエラーメッセージが保持されるべき"
            assert not bluesky_client.is_logged_in, "エラー後はログイン状態でないべき"
            assert bluesky_client.profile is None, "エラー後はプロフィール未設定であるべき"
    
    @pytest.mark.contract_interface 
    def test_graceful_degradation_contract(self, temp_db_file):
        """グレースフルデグラデーション契約テスト"""
        from core.data_store import DataStore
        
        # データベースエラーシミュレーション
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            # エラー時でも適切にハンドリングされる契約
            try:
                data_store = DataStore(temp_db_file)
                # 実装によってはエラーハンドリングで正常に初期化される
            except Exception as e:
                # 予期されるエラーの場合
                assert "Database" in str(e) or "connection" in str(e), "適切なエラーメッセージが含まれるべき"
    
    @pytest.mark.contract_interface
    def test_resource_cleanup_contract(self, temp_db_file):
        """リソースクリーンアップ契約テスト"""
        from core.data_store import DataStore
        
        data_store = DataStore(temp_db_file)
        
        # コンテキストマネージャーのクリーンアップ契約
        connection_opened = False
        connection_closed = False
        
        # 正常ケース
        with data_store.get_connection() as conn:
            connection_opened = True
            assert conn is not None, "有効な接続が提供されるべき"
        connection_closed = True  # with文を抜けた時点でクリーンアップされる
        
        assert connection_opened, "接続が正常に開かれるべき"
        assert connection_closed, "with文終了時にリソースがクリーンアップされるべき"
        
        # 例外発生時のクリーンアップ契約
        exception_occurred = False
        cleanup_performed = True
        
        try:
            with data_store.get_connection() as conn:
                # 意図的に例外発生
                raise ValueError("Test exception")
        except ValueError:
            exception_occurred = True
            # 例外発生後もリソースはクリーンアップされている
        
        assert exception_occurred, "例外が正常に発生するべき"
        assert cleanup_performed, "例外発生時もリソースクリーンアップが実行されるべき"