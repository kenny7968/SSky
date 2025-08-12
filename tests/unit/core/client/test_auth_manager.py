#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証マネージャーの単体テスト (pytest版)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from atproto.exceptions import AtProtocolError

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from core.client.auth_manager import BlueskyAuthManager
from core.exceptions import AuthenticationError


@pytest.fixture
def mock_api_client():
    """APIクライアントのモックフィクスチャ"""
    mock_client = MagicMock()
    mock_client.client = MagicMock()
    mock_client.client.me = MagicMock()
    mock_client.client.me.did = "did:plc:testuser123"
    return mock_client


@pytest.fixture
def mock_session_manager():
    """セッションマネージャーのモックフィクスチャ"""
    return MagicMock()


@pytest.fixture
def auth_manager(mock_api_client, mock_session_manager):
    """認証マネージャーのフィクスチャ"""
    return BlueskyAuthManager(
        api_client=mock_api_client,
        session_manager=mock_session_manager
    )


class TestBlueskyAuthManagerInitialization:
    """BlueskyAuthManager初期化のテストクラス"""
    
    def test_initialization_with_dependencies(self, mock_api_client, mock_session_manager):
        """依存オブジェクト付き初期化テスト"""
        manager = BlueskyAuthManager(
            api_client=mock_api_client,
            session_manager=mock_session_manager
        )
        
        assert manager.api_client == mock_api_client
        assert manager.session_manager == mock_session_manager
        assert manager.profile is None
        assert manager.is_logged_in is False
        assert manager.user_did is None
    
    def test_initialization_without_dependencies(self):
        """依存オブジェクトなし初期化テスト"""
        manager = BlueskyAuthManager()
        
        assert manager.api_client is None
        assert manager.session_manager is None
        assert manager.profile is None
        assert manager.is_logged_in is False
        assert manager.user_did is None


class TestBlueskyAuthManagerLogin:
    """ログイン機能のテストクラス"""
    
    @patch('core.client.auth_manager.logger')
    def test_login_success(self, mock_logger, auth_manager, mock_api_client):
        """ログイン成功テスト"""
        # プロフィール情報をモック
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_profile.handle = "testuser.bsky.social"
        mock_api_client.client.login.return_value = mock_profile
        
        # ログイン実行
        result = auth_manager.login("testuser.bsky.social", "password123")
        
        # 結果確認
        assert result == mock_profile
        assert auth_manager.profile == mock_profile
        assert auth_manager.is_logged_in is True
        assert auth_manager.user_did == "did:plc:testuser123"
        mock_api_client.client.login.assert_called_once_with("testuser.bsky.social", "password123")
    
    @patch('core.client.auth_manager.logger')
    def test_login_protocol_error(self, mock_logger, auth_manager, mock_api_client):
        """プロトコルエラー時のログインテスト"""
        # AtProtocolErrorを発生させる
        mock_api_client.client.login.side_effect = AtProtocolError("Invalid credentials")
        
        # ログイン実行（例外を期待）
        with pytest.raises(AtProtocolError):
            auth_manager.login("testuser.bsky.social", "wrongpassword")
        
        # 状態確認
        assert auth_manager.is_logged_in is False
        assert auth_manager.profile is None
    
    @patch('core.client.auth_manager.logger')
    def test_login_general_error(self, mock_logger, auth_manager, mock_api_client):
        """一般エラー時のログインテスト"""
        # 一般例外を発生させる
        mock_api_client.client.login.side_effect = Exception("Network error")
        
        # ログイン実行（例外を期待）
        with pytest.raises(Exception):
            auth_manager.login("testuser.bsky.social", "password123")
        
        # 状態確認
        assert auth_manager.is_logged_in is False
        assert auth_manager.profile is None


class TestBlueskyAuthManagerSessionLogin:
    """セッションログイン機能のテストクラス"""
    
    @patch('core.client.auth_manager.logger')
    def test_login_with_session_string_success(self, mock_logger, auth_manager, mock_api_client):
        """文字列セッションでのログイン成功テスト"""
        # プロフィール情報をモック
        mock_profile = MagicMock()
        mock_profile.handle = "testuser.bsky.social"
        
        # 最初の文字列試行で成功
        mock_api_client.client.login.return_value = mock_profile
        
        # セッションログイン実行
        result = auth_manager.login_with_session("session_string_data")
        
        # 結果確認
        assert result == mock_profile
        assert auth_manager.profile == mock_profile
        assert auth_manager.is_logged_in is True
        assert auth_manager.user_did == "did:plc:testuser123"
        mock_api_client.client.login.assert_called_once_with(session_string="session_string_data")
    
    @patch('core.client.auth_manager.logger')
    def test_login_with_session_bytes_fallback(self, mock_logger, auth_manager, mock_api_client):
        """バイト列フォールバックでのセッションログインテスト"""
        # プロフィール情報をモック
        mock_profile = MagicMock()
        mock_profile.handle = "testuser.bsky.social"
        
        # 最初の文字列試行は失敗、バイト列で成功
        mock_api_client.client.login.side_effect = [
            Exception("String format not supported"),
            mock_profile
        ]
        
        # セッションログイン実行
        result = auth_manager.login_with_session("session_string_data")
        
        # 結果確認
        assert result == mock_profile
        assert auth_manager.profile == mock_profile
        assert auth_manager.is_logged_in is True
        assert mock_api_client.client.login.call_count == 2
    
    @patch('core.client.auth_manager.logger')
    def test_login_with_session_failure(self, mock_logger, auth_manager, mock_api_client):
        """セッションログイン失敗テスト"""
        # 両方の試行で失敗
        mock_api_client.client.login.side_effect = Exception("Invalid session")
        
        # セッションログイン実行（例外を期待）
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.login_with_session("invalid_session")
        
        assert "セッションが無効になりました" in str(exc_info.value)
        assert auth_manager.is_logged_in is False
        assert auth_manager.profile is None


class TestBlueskyAuthManagerLogout:
    """ログアウト機能のテストクラス"""
    
    @patch('core.client.auth_manager.logger')
    @patch('core.client.auth_manager.AtprotoClient')
    def test_logout_success(self, mock_atproto_client, mock_logger, auth_manager):
        """ログアウト成功テスト"""
        # 事前にログイン状態を設定
        auth_manager.profile = MagicMock()
        auth_manager.is_logged_in = True
        auth_manager.user_did = "did:plc:testuser123"
        
        # ログアウト実行
        result = auth_manager.logout()
        
        # 結果確認
        assert result is True
        assert auth_manager.profile is None
        assert auth_manager.is_logged_in is False
        mock_atproto_client.assert_called_once()
    
    @patch('core.client.auth_manager.logger')
    @patch('core.client.auth_manager.AtprotoClient')
    def test_logout_with_error(self, mock_atproto_client, mock_logger, auth_manager):
        """ログアウト時エラーテスト"""
        # AtprotoClientの初期化でエラー
        mock_atproto_client.side_effect = Exception("Client reset error")
        
        # ログアウト実行
        result = auth_manager.logout()
        
        # 結果確認
        assert result is False


class TestBlueskyAuthManagerSessionExport:
    """セッションエクスポート機能のテストクラス"""
    
    @patch('core.client.auth_manager.logger')
    def test_export_session_string_success(self, mock_logger, auth_manager, mock_api_client):
        """セッションエクスポート成功テスト"""
        # ログイン状態を設定
        auth_manager.is_logged_in = True
        mock_api_client.client.export_session_string.return_value = "exported_session_data"
        
        # エクスポート実行
        result = auth_manager.export_session_string()
        
        # 結果確認
        assert result == "exported_session_data"
        mock_api_client.client.export_session_string.assert_called_once()
    
    @patch('core.client.auth_manager.logger')
    def test_export_session_string_not_logged_in(self, mock_logger, auth_manager):
        """未ログイン時のセッションエクスポートテスト"""
        # ログインしていない状態
        auth_manager.is_logged_in = False
        
        # エクスポート実行
        result = auth_manager.export_session_string()
        
        # 結果確認
        assert result is None
        mock_logger.error.assert_called_with("セッション情報のエクスポートに失敗しました: ログインしていません")
    
    @patch('core.client.auth_manager.logger')
    def test_export_session_string_with_error(self, mock_logger, auth_manager, mock_api_client):
        """エクスポート時エラーテスト"""
        # ログイン状態を設定
        auth_manager.is_logged_in = True
        mock_api_client.client.export_session_string.side_effect = Exception("Export error")
        
        # エクスポート実行
        result = auth_manager.export_session_string()
        
        # 結果確認
        assert result is None


class TestBlueskyAuthManagerErrorHandling:
    """エラーハンドリング機能のテストクラス"""
    
    def test_is_authentication_error_with_atprotocol_error(self, auth_manager):
        """AtProtocolError認証エラー判定テスト"""
        errors = [
            AtProtocolError("Authentication failed"),
            AtProtocolError("unauthorized access"),
            AtProtocolError("invalid_token"),
            AtProtocolError("Auth error occurred")
        ]
        
        for error in errors:
            assert auth_manager.is_authentication_error(error) is True
    
    def test_is_authentication_error_with_non_auth_error(self, auth_manager):
        """非認証エラー判定テスト"""
        errors = [
            AtProtocolError("Network timeout"),
            Exception("General error"),
            ValueError("Invalid value")
        ]
        
        for error in errors:
            assert auth_manager.is_authentication_error(error) is False
    
    @patch('core.client.auth_manager.logger')
    def test_handle_authentication_error_with_auth_error(self, mock_logger, auth_manager):
        """認証エラー処理テスト"""
        # 事前にログイン状態を設定
        auth_manager.is_logged_in = True
        auth_manager.profile = MagicMock()
        auth_manager.user_did = "did:plc:testuser123"
        
        # 認証エラーを処理
        error = AtProtocolError("Authentication failed")
        result = auth_manager.handle_authentication_error(error, "テスト操作")
        
        # 結果確認
        assert result is True
        assert auth_manager.is_logged_in is False
        assert auth_manager.profile is None
        assert auth_manager.user_did is None
    
    @patch('core.client.auth_manager.logger')
    def test_handle_authentication_error_with_non_auth_error(self, mock_logger, auth_manager):
        """非認証エラー処理テスト"""
        # 事前にログイン状態を設定
        auth_manager.is_logged_in = True
        auth_manager.profile = MagicMock()
        auth_manager.user_did = "did:plc:testuser123"
        
        # 非認証エラーを処理
        error = Exception("Network error")
        result = auth_manager.handle_authentication_error(error, "テスト操作")
        
        # 結果確認
        assert result is False
        # 状態は変更されない
        assert auth_manager.is_logged_in is True
        assert auth_manager.profile is not None
        assert auth_manager.user_did == "did:plc:testuser123"