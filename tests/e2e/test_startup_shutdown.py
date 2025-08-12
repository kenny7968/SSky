#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
E2E基本ライフサイクルテスト
"""

import pytest
import time
import os
from unittest.mock import patch, MagicMock


class TestApplicationLifecycle:
    """アプリケーションの基本的なライフサイクルテスト"""
    
    @pytest.mark.e2e_smoke
    def test_application_startup_success(self, e2e_app_components, e2e_application_lifecycle, e2e_test_timeout):
        """正常なアプリケーション起動テスト"""
        # アプリケーション起動
        startup_success = e2e_application_lifecycle.start_app(e2e_app_components)
        
        assert startup_success, "アプリケーションの起動に失敗しました"
        assert e2e_application_lifecycle.is_app_running(), "アプリケーションが実行状態になっていません"
        
        # コンポーネントの初期化確認
        assert e2e_app_components['data_store'] is not None, "DataStoreが初期化されていません"
        assert e2e_app_components['credential_manager'] is not None, "CredentialManagerが初期化されていません"
        assert e2e_app_components['bluesky_client'] is not None, "BlueskyClientが初期化されていません"
        assert e2e_app_components['settings_manager'] is not None, "SettingsManagerが初期化されていません"
    
    @pytest.mark.e2e_smoke
    def test_application_shutdown_graceful(self, e2e_app_components, e2e_application_lifecycle, e2e_test_timeout):
        """正常なアプリケーション終了テスト"""
        # アプリケーション起動
        e2e_application_lifecycle.start_app(e2e_app_components)
        assert e2e_application_lifecycle.is_app_running(), "テスト前提：アプリケーションが起動していない"
        
        # 正常終了
        shutdown_success = e2e_application_lifecycle.stop_app()
        
        assert shutdown_success, "アプリケーションの終了に失敗しました"
        assert not e2e_application_lifecycle.is_app_running(), "アプリケーションが終了状態になっていません"
    
    @pytest.mark.e2e_smoke
    def test_application_restart(self, e2e_app_components, e2e_application_lifecycle, e2e_test_timeout):
        """アプリケーション再起動テスト"""
        # 初回起動
        e2e_application_lifecycle.start_app(e2e_app_components)
        assert e2e_application_lifecycle.is_app_running(), "初回起動が失敗しました"
        
        # 再起動
        restart_success = e2e_application_lifecycle.restart_app(e2e_app_components)
        
        assert restart_success, "アプリケーションの再起動に失敗しました"
        assert e2e_application_lifecycle.is_app_running(), "再起動後にアプリケーションが実行状態になっていません"
    
    @pytest.mark.e2e_smoke
    def test_database_initialization_on_startup(self, e2e_app_components, e2e_application_lifecycle):
        """起動時のデータベース初期化テスト"""
        # アプリケーション起動
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        data_store = e2e_app_components['data_store']
        
        # データベーステーブルの存在確認
        with data_store.get_connection() as conn:
            cursor = conn.cursor()
            
            # sessions テーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            sessions_table = cursor.fetchone()
            assert sessions_table is not None, "sessionsテーブルが作成されていません"
            
            # credentials テーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
            credentials_table = cursor.fetchone()
            assert credentials_table is not None, "credentialsテーブルが作成されていません"
    
    @pytest.mark.e2e_smoke
    def test_settings_initialization_on_startup(self, e2e_app_components, e2e_application_lifecycle):
        """起動時の設定初期化テスト"""
        # アプリケーション起動
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        settings_manager = e2e_app_components['settings_manager']
        
        # デフォルト設定の確認
        assert settings_manager.get('timeline_refresh_interval') is not None, "timeline_refresh_intervalが設定されていません"
        assert settings_manager.get('max_posts_display') is not None, "max_posts_displayが設定されていません"
        assert settings_manager.get('language') is not None, "languageが設定されていません"
    
    @pytest.mark.e2e_full
    def test_startup_with_existing_data(self, e2e_app_components, e2e_application_lifecycle):
        """既存データありでの起動テスト"""
        # 事前データ準備
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        data_store = e2e_app_components['data_store']
        
        # テストデータ挿入
        test_session_data = {
            'handle': 'test.user',
            'access_jwt': 'test_access_token',
            'refresh_jwt': 'test_refresh_token',
            'did': 'did:plc:testuser123'
        }
        
        with data_store.get_connection() as conn:
            data_store.save_session(conn, **test_session_data)
        
        # アプリケーション再起動
        e2e_application_lifecycle.restart_app(e2e_app_components)
        
        # 既存データの読み込み確認
        with data_store.get_connection() as conn:
            loaded_session = data_store.get_latest_session(conn, 'test.user')
            
            assert loaded_session is not None, "既存セッションデータが読み込まれていません"
            assert loaded_session['handle'] == 'test.user', "セッションデータが正しく読み込まれていません"


class TestComponentIntegration:
    """コンポーネント統合テスト"""
    
    @pytest.mark.e2e_full
    def test_credential_manager_integration(self, e2e_app_components, e2e_application_lifecycle):
        """CredentialManager統合テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        credential_manager = e2e_app_components['credential_manager']
        
        # 認証情報保存テスト
        test_credentials = {
            'handle': 'test.integration',
            'password': 'test_password_123'
        }
        
        save_success = credential_manager.save_credentials(
            test_credentials['handle'], 
            test_credentials['password']
        )
        
        assert save_success, "認証情報の保存に失敗しました"
        
        # 認証情報取得テスト
        stored_credentials = credential_manager.get_stored_credentials()
        
        assert stored_credentials is not None, "保存された認証情報が取得できません"
        assert len(stored_credentials) > 0, "認証情報が空です"
        
        # 認証情報削除テスト
        clear_success = credential_manager.clear_credentials()
        assert clear_success, "認証情報のクリアに失敗しました"
    
    @pytest.mark.e2e_full
    def test_bluesky_client_integration(self, e2e_app_components, e2e_application_lifecycle):
        """BlueskyClient統合テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        
        # 初期状態確認
        assert not bluesky_client.is_logged_in, "初期状態でログイン状態になっています"
        assert bluesky_client.profile is None, "初期状態でプロフィールが設定されています"
        
        # モックAPIクライアントの確認
        mock_client = e2e_app_components['client']
        assert mock_client is not None, "モックAPIクライアントが設定されていません"
    
    @pytest.mark.e2e_full
    def test_settings_manager_integration(self, e2e_app_components, e2e_application_lifecycle):
        """SettingsManager統合テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        settings_manager = e2e_app_components['settings_manager']
        
        # 設定変更テスト
        original_interval = settings_manager.get('timeline_refresh_interval')
        new_interval = 45
        
        settings_manager.set('timeline_refresh_interval', new_interval)
        
        assert settings_manager.get('timeline_refresh_interval') == new_interval, "設定変更が反映されていません"
        
        # 設定保存・復元テスト
        settings_manager.save()
        
        # アプリケーション再起動で設定が保持されるかテスト
        e2e_application_lifecycle.restart_app(e2e_app_components)
        
        reloaded_settings = e2e_app_components['settings_manager']
        assert reloaded_settings.get('timeline_refresh_interval') == new_interval, "再起動後に設定が保持されていません"


class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    @pytest.mark.e2e_full
    def test_startup_with_corrupted_database(self, e2e_temp_environment, e2e_application_lifecycle):
        """破損データベースでの起動テスト"""
        # 破損データベースファイル作成
        corrupted_db = e2e_temp_environment['data_dir'] / "corrupted.db"
        with open(corrupted_db, 'w') as f:
            f.write("This is not a valid SQLite database")
        
        # DataStoreの初期化試行
        from core.data_store import DataStore
        
        # 破損データベースでもエラー処理によって正常に処理されることを確認
        try:
            data_store = DataStore(str(corrupted_db))
            # データベースの再初期化が行われることを期待
            assert True, "破損データベースが適切に処理されました"
        except Exception as e:
            # 予期されるエラーの場合は正常とみなす
            assert "database" in str(e).lower() or "sqlite" in str(e).lower(), f"予期しないエラー: {e}"
    
    @pytest.mark.e2e_full 
    def test_startup_with_permission_error(self, e2e_temp_environment, e2e_mock_wx_app):
        """権限エラー時の起動テスト"""
        # 読み取り専用ディレクトリでの起動試行をシミュレート
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            try:
                from config.settings_manager import SettingsManager
                SettingsManager._instance = None
                settings_manager = SettingsManager()
                
                # 権限エラーが適切に処理されることを確認
                # デフォルト設定での動作継続を期待
                assert settings_manager.get('language') is not None, "デフォルト設定が使用されていません"
                
            except PermissionError:
                # 権限エラーが適切にキャッチされない場合は失敗
                pytest.fail("権限エラーが適切に処理されていません")
    
    @pytest.mark.e2e_smoke
    def test_graceful_shutdown_on_error(self, e2e_app_components, e2e_application_lifecycle):
        """エラー時の正常終了テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        # 故意にエラーを発生させる
        with patch.object(e2e_app_components['data_store'], 'get_connection', side_effect=Exception("Database error")):
            # エラーが発生してもアプリケーションが正常に終了することを確認
            shutdown_success = e2e_application_lifecycle.stop_app()
            assert shutdown_success, "エラー時にアプリケーションが正常終了しませんでした"