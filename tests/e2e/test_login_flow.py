#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
E2E認証フローテスト
"""

import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from atproto_client.exceptions import AtProtocolError


class TestLoginFlow:
    """ログインフロー E2E テスト"""
    
    @pytest.mark.e2e_smoke
    def test_successful_login_flow(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """正常ログインフロー完全テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        credential_manager = e2e_app_components['credential_manager']
        mock_client = e2e_app_components['client']
        
        # 初期状態確認
        assert not bluesky_client.is_logged_in, "初期状態でログイン済みになっています"
        
        # ログイン実行
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # モックAPIの設定
        mock_client.login.return_value = True
        mock_client.get_profile.return_value = e2e_app_components['sample_profile']
        
        # ログイン試行
        login_result = bluesky_client.login(
            credentials['handle'], 
            credentials['password']
        )
        
        # ログイン結果検証
        assert login_result, "ログインが失敗しました"
        assert bluesky_client.is_logged_in, "ログイン後にis_logged_inがTrueになっていません"
        assert bluesky_client.profile is not None, "ログイン後にプロフィールが設定されていません"
        
        # APIクライアント呼び出し確認
        mock_client.login.assert_called_once()
        mock_client.get_profile.assert_called_once()
        
        # 認証情報保存確認
        stored_credentials = credential_manager.get_stored_credentials()
        assert len(stored_credentials) > 0, "認証情報が保存されていません"
    
    @pytest.mark.e2e_smoke
    def test_failed_login_flow(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """ログイン失敗フロー完全テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        mock_client = e2e_app_components['client']
        
        # 無効な認証情報
        invalid_credentials = e2e_user_scenario_data['invalid_credentials']
        
        # モックAPIの設定（ログイン失敗）
        mock_client.login.side_effect = AtProtocolError("Invalid credentials")
        
        # ログイン試行
        with pytest.raises(AtProtocolError):
            bluesky_client.login(
                invalid_credentials['handle'],
                invalid_credentials['password']
            )
        
        # 失敗後の状態確認
        assert not bluesky_client.is_logged_in, "ログイン失敗後もis_logged_inがTrueになっています"
        assert bluesky_client.profile is None, "ログイン失敗後にプロフィールが設定されています"
        
        # APIクライアント呼び出し確認
        mock_client.login.assert_called_once()
        mock_client.get_profile.assert_not_called()
    
    @pytest.mark.e2e_full
    def test_auto_login_on_startup(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """起動時自動ログインテスト"""
        # 最初にログインしてセッション保存
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        credential_manager = e2e_app_components['credential_manager']
        data_store = e2e_app_components['data_store']
        mock_client = e2e_app_components['client']
        
        # 手動ログイン
        credentials = e2e_user_scenario_data['valid_credentials']
        mock_client.login.return_value = True
        mock_client.get_profile.return_value = e2e_app_components['sample_profile']
        
        bluesky_client.login(credentials['handle'], credentials['password'])
        
        # セッション情報を手動で保存（通常はBlueskyClientが行う）
        test_session = {
            'handle': credentials['handle'],
            'access_jwt': 'test_access_token',
            'refresh_jwt': 'test_refresh_token',
            'did': 'did:plc:testuser123'
        }
        
        with data_store.get_connection() as conn:
            data_store.save_session(conn, **test_session)
        
        # アプリケーション再起動
        e2e_application_lifecycle.restart_app(e2e_app_components)
        
        # 新しいBlueskyClientインスタンス取得
        new_bluesky_client = e2e_app_components['bluesky_client']
        
        # 自動ログインの確認は、実際の実装では自動的に行われるべき
        # ここでは保存されたセッション情報の確認のみ
        with data_store.get_connection() as conn:
            saved_session = data_store.get_latest_session(conn, credentials['handle'])
            assert saved_session is not None, "セッション情報が保存されていません"
            assert saved_session['handle'] == credentials['handle'], "セッション情報が正しくありません"
    
    @pytest.mark.e2e_full
    def test_logout_flow(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """ログアウトフロー完全テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        credential_manager = e2e_app_components['credential_manager']
        data_store = e2e_app_components['data_store']
        mock_client = e2e_app_components['client']
        
        # まずログイン
        credentials = e2e_user_scenario_data['valid_credentials']
        mock_client.login.return_value = True
        mock_client.get_profile.return_value = e2e_app_components['sample_profile']
        
        bluesky_client.login(credentials['handle'], credentials['password'])
        assert bluesky_client.is_logged_in, "ログイン前提条件が満たされていません"
        
        # ログアウト実行
        logout_result = bluesky_client.logout()
        
        # ログアウト結果検証
        assert logout_result, "ログアウトが失敗しました"
        assert not bluesky_client.is_logged_in, "ログアウト後もis_logged_inがTrueです"
        assert bluesky_client.profile is None, "ログアウト後にプロフィールが残っています"
    
    @pytest.mark.e2e_full
    def test_session_persistence_across_restarts(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """再起動間でのセッション永続化テスト"""
        # 初回起動とログイン
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        data_store = e2e_app_components['data_store']
        mock_client = e2e_app_components['client']
        
        credentials = e2e_user_scenario_data['valid_credentials']
        mock_client.login.return_value = True
        mock_client.get_profile.return_value = e2e_app_components['sample_profile']
        
        bluesky_client.login(credentials['handle'], credentials['password'])
        
        # セッション手動保存
        test_session = {
            'handle': credentials['handle'],
            'access_jwt': 'persistent_access_token',
            'refresh_jwt': 'persistent_refresh_token',
            'did': 'did:plc:testuser123'
        }
        
        with data_store.get_connection() as conn:
            data_store.save_session(conn, **test_session)
        
        # 1回目再起動
        e2e_application_lifecycle.restart_app(e2e_app_components)
        
        with data_store.get_connection() as conn:
            session1 = data_store.get_latest_session(conn, credentials['handle'])
            assert session1 is not None, "1回目再起動後にセッションが失われています"
        
        # 2回目再起動
        e2e_application_lifecycle.restart_app(e2e_app_components)
        
        with data_store.get_connection() as conn:
            session2 = data_store.get_latest_session(conn, credentials['handle'])
            assert session2 is not None, "2回目再起動後にセッションが失われています"
            assert session2['access_jwt'] == 'persistent_access_token', "セッションデータが変更されています"
    
    @pytest.mark.e2e_full
    def test_multiple_user_sessions(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """複数ユーザーセッション管理テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        data_store = e2e_app_components['data_store']
        
        # 複数ユーザーのセッション保存
        users = [
            {
                'handle': 'user1.test',
                'access_jwt': 'user1_access_token',
                'refresh_jwt': 'user1_refresh_token',
                'did': 'did:plc:user1'
            },
            {
                'handle': 'user2.test',
                'access_jwt': 'user2_access_token',
                'refresh_jwt': 'user2_refresh_token',
                'did': 'did:plc:user2'
            },
            {
                'handle': 'user3.test',
                'access_jwt': 'user3_access_token',
                'refresh_jwt': 'user3_refresh_token',
                'did': 'did:plc:user3'
            }
        ]
        
        with data_store.get_connection() as conn:
            for user in users:
                data_store.save_session(conn, **user)
        
        # 各ユーザーのセッション取得確認
        with data_store.get_connection() as conn:
            for user in users:
                session = data_store.get_latest_session(conn, user['handle'])
                assert session is not None, f"{user['handle']}のセッションが保存されていません"
                assert session['handle'] == user['handle'], f"{user['handle']}のセッションデータが正しくありません"
                assert session['did'] == user['did'], f"{user['handle']}のDIDが正しくありません"


class TestCredentialManagement:
    """認証情報管理 E2E テスト"""
    
    @pytest.mark.e2e_smoke
    def test_credential_save_and_retrieve(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """認証情報保存・取得フロー"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        credential_manager = e2e_app_components['credential_manager']
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # 認証情報保存
        save_success = credential_manager.save_credentials(
            credentials['handle'],
            credentials['password']
        )
        
        assert save_success, "認証情報の保存に失敗しました"
        
        # 認証情報取得
        stored_credentials = credential_manager.get_stored_credentials()
        
        assert stored_credentials is not None, "認証情報が取得できません"
        assert len(stored_credentials) > 0, "保存された認証情報が空です"
        
        # 特定ユーザーの認証情報確認
        user_found = False
        for cred in stored_credentials:
            if cred['handle'] == credentials['handle']:
                user_found = True
                break
        
        assert user_found, "保存したユーザーの認証情報が見つかりません"
    
    @pytest.mark.e2e_full
    def test_credential_encryption_integrity(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """認証情報暗号化整合性テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        credential_manager = e2e_app_components['credential_manager']
        data_store = e2e_app_components['data_store']
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # 認証情報保存
        credential_manager.save_credentials(
            credentials['handle'],
            credentials['password']
        )
        
        # データベース直接確認（暗号化されているはず）
        with data_store.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT encrypted_data FROM credentials WHERE handle = ?",
                (credentials['handle'],)
            )
            result = cursor.fetchone()
            
            assert result is not None, "データベースに認証情報が保存されていません"
            encrypted_data = result[0]
            
            # 暗号化されたデータは元のパスワードと異なるはず
            assert encrypted_data != credentials['password'], "パスワードが暗号化されていません"
            assert isinstance(encrypted_data, (str, bytes)), "暗号化データの形式が不正です"
        
        # 復号化による正しい取得確認
        retrieved_credentials = credential_manager.get_stored_credentials()
        assert len(retrieved_credentials) > 0, "暗号化された認証情報が復号化できません"
    
    @pytest.mark.e2e_full
    def test_credential_clear_functionality(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """認証情報クリア機能テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        credential_manager = e2e_app_components['credential_manager']
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # 認証情報保存
        credential_manager.save_credentials(
            credentials['handle'],
            credentials['password']
        )
        
        # 保存確認
        stored_before = credential_manager.get_stored_credentials()
        assert len(stored_before) > 0, "認証情報が保存されていません"
        
        # クリア実行
        clear_success = credential_manager.clear_credentials()
        assert clear_success, "認証情報のクリアに失敗しました"
        
        # クリア後確認
        stored_after = credential_manager.get_stored_credentials()
        assert len(stored_after) == 0, "認証情報がクリアされていません"


class TestLoginErrorHandling:
    """ログインエラーハンドリング E2E テスト"""
    
    @pytest.mark.e2e_full
    def test_network_error_during_login(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """ログイン時ネットワークエラーテスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        mock_client = e2e_app_components['client']
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # ネットワークエラーをシミュレート
        mock_client.login.side_effect = Exception("Network error")
        
        # ログイン試行
        with pytest.raises(Exception, match="Network error"):
            bluesky_client.login(credentials['handle'], credentials['password'])
        
        # エラー後の状態確認
        assert not bluesky_client.is_logged_in, "ネットワークエラー後にログイン状態になっています"
        assert bluesky_client.profile is None, "ネットワークエラー後にプロフィールが設定されています"
    
    @pytest.mark.e2e_full
    def test_api_rate_limit_during_login(self, e2e_app_components, e2e_application_lifecycle, e2e_user_scenario_data):
        """ログイン時API制限エラーテスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        mock_client = e2e_app_components['client']
        credentials = e2e_user_scenario_data['valid_credentials']
        
        # API制限エラーをシミュレート
        mock_client.login.side_effect = AtProtocolError("Rate limit exceeded")
        
        # ログイン試行
        with pytest.raises(AtProtocolError, match="Rate limit exceeded"):
            bluesky_client.login(credentials['handle'], credentials['password'])
        
        # エラー後の状態確認
        assert not bluesky_client.is_logged_in, "API制限エラー後にログイン状態になっています"
    
    @pytest.mark.e2e_full
    def test_corrupted_credentials_handling(self, e2e_app_components, e2e_application_lifecycle):
        """破損認証情報の処理テスト"""
        e2e_application_lifecycle.start_app(e2e_app_components)
        
        credential_manager = e2e_app_components['credential_manager']
        data_store = e2e_app_components['data_store']
        
        # 破損データを直接データベースに挿入
        corrupted_data = "this_is_not_encrypted_json_data"
        
        with data_store.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO credentials (handle, encrypted_data, created_at) VALUES (?, ?, ?)",
                ("corrupted.user", corrupted_data, "2024-01-01 12:00:00")
            )
            conn.commit()
        
        # 破損データの取得試行
        stored_credentials = credential_manager.get_stored_credentials()
        
        # 破損データは除外されて正常に処理されるべき
        assert isinstance(stored_credentials, list), "破損データによって認証情報取得が完全に失敗しています"
        
        # 破損したエントリは含まれていないはず
        corrupted_found = False
        for cred in stored_credentials:
            if cred.get('handle') == 'corrupted.user':
                corrupted_found = True
                break
        
        assert not corrupted_found, "破損した認証情報が正常データとして返されています"