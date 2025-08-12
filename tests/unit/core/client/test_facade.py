#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
BlueskyClient ファサード包括テスト (Phase 2 カバレッジ強化)

目標: 31.0% → 90%+ カバレッジ
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any, List, Optional
from atproto.exceptions import AtProtocolError
from core.exceptions import AuthenticationError


class TestBlueskyClientInitialization:
    """BlueskyClient 初期化テスト"""
    
    @pytest.mark.unit
    def test_default_initialization(self):
        """デフォルト初期化テスト"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            # モックインスタンスの設定
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_session_manager = Mock()
            mock_session_manager_class.return_value = mock_session_manager
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            mock_error_handler = Mock()
            mock_error_handler_class.return_value = mock_error_handler
            
            mock_user_manager = Mock()
            mock_user_manager_class.return_value = mock_user_manager
            
            # BlueskyClient初期化
            client = BlueskyClient()
            
            # 各コンポーネントが作成されたことを確認
            mock_api_client_class.assert_called_once()
            mock_session_manager_class.assert_called_once_with(mock_api_client)
            mock_auth_manager_class.assert_called_once_with(mock_api_client, mock_session_manager)
            mock_error_handler_class.assert_called_once_with(mock_auth_manager)
            mock_user_manager_class.assert_called_once_with(mock_api_client, mock_auth_manager)
            
            # セッションマネージャーへのクライアント登録確認
            mock_session_manager.register_client.assert_called_once_with(mock_api_client)
            
            # プロパティバインディング確認
            assert client.api_client == mock_api_client
            assert client.session_manager == mock_session_manager
            assert client.auth_manager == mock_auth_manager
            assert client.error_handler == mock_error_handler
            assert client.user_manager == mock_user_manager
            assert client.client == mock_api_client.client
    
    @pytest.mark.unit
    def test_dependency_injection_initialization(self):
        """依存性注入による初期化テスト"""
        from core.client.facade import BlueskyClient
        
        # カスタムコンポーネント
        custom_api_client = Mock()
        custom_session_manager = Mock()
        custom_auth_manager = Mock()
        custom_error_handler = Mock()
        custom_user_manager = Mock()
        
        # 依存性注入で初期化
        client = BlueskyClient(
            api_client=custom_api_client,
            session_manager=custom_session_manager,
            auth_manager=custom_auth_manager,
            error_handler=custom_error_handler,
            user_manager=custom_user_manager
        )
        
        # 注入されたコンポーネントが使用されることを確認
        assert client.api_client == custom_api_client
        assert client.session_manager == custom_session_manager
        assert client.auth_manager == custom_auth_manager
        assert client.error_handler == custom_error_handler
        assert client.user_manager == custom_user_manager
        
        # セッションマネージャー登録確認
        custom_session_manager.register_client.assert_called_once_with(custom_api_client)
    
    @pytest.mark.unit
    def test_partial_dependency_injection(self):
        """部分的依存性注入テスト"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            custom_api_client = Mock()
            
            # 部分的に依存性注入
            client = BlueskyClient(api_client=custom_api_client)
            
            # 注入されたコンポーネント確認
            assert client.api_client == custom_api_client
            
            # 他のコンポーネントはデフォルト作成されることを確認
            mock_session_manager_class.assert_called_once_with(custom_api_client)
            mock_auth_manager_class.assert_called_once()
            mock_error_handler_class.assert_called_once()
            mock_user_manager_class.assert_called_once()


class TestBlueskyClientFactoryMethods:
    """BlueskyClient ファクトリメソッドテスト"""
    
    @pytest.mark.unit
    def test_create_for_testing_factory(self):
        """テスト用ファクトリメソッド"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            # モックコンポーネント
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            # ファクトリメソッド実行
            client = BlueskyClient.create_for_testing()
            
            # 適切にインスタンスが作成されることを確認
            assert isinstance(client, BlueskyClient)
            mock_api_client_class.assert_called_once()
    
    @pytest.mark.unit
    def test_create_for_testing_with_mock_client(self):
        """モックAPIクライアント付きテスト用ファクトリメソッド"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            custom_mock_client = Mock()
            
            # モックAPIクライアント付きでファクトリメソッド実行
            client = BlueskyClient.create_for_testing(mock_api_client=custom_mock_client)
            
            # カスタムAPIクライアントが使用されることを確認
            assert client.api_client == custom_mock_client
            mock_session_manager_class.assert_called_once_with(custom_mock_client)
    
    @pytest.mark.unit
    def test_create_with_custom_credential_manager_factory(self):
        """カスタム認証情報管理付きファクトリメソッド"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            custom_credential_manager = Mock()
            
            # ファクトリメソッド実行
            client = BlueskyClient.create_with_custom_credential_manager(custom_credential_manager)
            
            # 適切にインスタンスが作成されることを確認
            assert isinstance(client, BlueskyClient)
            mock_api_client_class.assert_called_once()


class TestBlueskyClientProperties:
    """BlueskyClient プロパティテスト"""
    
    @pytest.fixture
    def mock_client(self):
        """モック付きBlueskyClientインスタンス"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient'), \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_auth_manager
    
    @pytest.mark.unit
    def test_profile_property_getter(self, mock_client):
        """profileプロパティゲッターテスト"""
        client, mock_auth_manager = mock_client
        
        expected_profile = {"handle": "test.user", "displayName": "Test User"}
        mock_auth_manager.profile = expected_profile
        
        assert client.profile == expected_profile
    
    @pytest.mark.unit
    def test_profile_property_setter(self, mock_client):
        """profileプロパティセッターテスト"""
        client, mock_auth_manager = mock_client
        
        new_profile = {"handle": "new.user", "displayName": "New User"}
        client.profile = new_profile
        
        assert mock_auth_manager.profile == new_profile
    
    @pytest.mark.unit
    def test_is_logged_in_property_getter(self, mock_client):
        """is_logged_inプロパティゲッターテスト"""
        client, mock_auth_manager = mock_client
        
        mock_auth_manager.is_logged_in = True
        assert client.is_logged_in == True
        
        mock_auth_manager.is_logged_in = False
        assert client.is_logged_in == False
    
    @pytest.mark.unit
    def test_is_logged_in_property_setter(self, mock_client):
        """is_logged_inプロパティセッターテスト"""
        client, mock_auth_manager = mock_client
        
        client.is_logged_in = True
        assert mock_auth_manager.is_logged_in == True
        
        client.is_logged_in = False
        assert mock_auth_manager.is_logged_in == False
    
    @pytest.mark.unit
    def test_user_did_property_getter(self, mock_client):
        """user_didプロパティゲッターテスト"""
        client, mock_auth_manager = mock_client
        
        expected_did = "did:plc:test123"
        mock_auth_manager.user_did = expected_did
        
        assert client.user_did == expected_did
    
    @pytest.mark.unit
    def test_user_did_property_setter(self, mock_client):
        """user_didプロパティセッターテスト"""
        client, mock_auth_manager = mock_client
        
        new_did = "did:plc:new123"
        client.user_did = new_did
        
        assert mock_auth_manager.user_did == new_did


class TestBlueskyClientSessionEvents:
    """BlueskyClient セッションイベントテスト"""
    
    @pytest.fixture
    def mock_client_with_session_manager(self):
        """セッションマネージャー付きモッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient'), \
             patch('core.client.facade.BlueskySessionManager') as mock_session_manager_class, \
             patch('core.client.facade.BlueskyAuthManager'), \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_session_manager = Mock()
            mock_session_manager_class.return_value = mock_session_manager
            
            client = BlueskyClient()
            return client, mock_session_manager
    
    @pytest.mark.unit
    def test_on_session_change_registration(self, mock_client_with_session_manager):
        """セッション変更イベントハンドラ登録テスト"""
        client, mock_session_manager = mock_client_with_session_manager
        
        def test_handler(event, session):
            pass
        
        client.on_session_change(test_handler)
        
        mock_session_manager.on_session_change.assert_called_once_with(test_handler)
    
    @pytest.mark.unit
    def test_remove_session_change_handler(self, mock_client_with_session_manager):
        """セッション変更イベントハンドラ削除テスト"""
        client, mock_session_manager = mock_client_with_session_manager
        
        def test_handler(event, session):
            pass
        
        mock_session_manager.remove_session_change_handler.return_value = True
        
        result = client.remove_session_change_handler(test_handler)
        
        mock_session_manager.remove_session_change_handler.assert_called_once_with(test_handler)
        assert result == True


class TestBlueskyClientAuthentication:
    """BlueskyClient 認証テスト"""
    
    @pytest.fixture
    def mock_client_with_auth(self):
        """認証マネージャー付きモッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient'), \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_auth_manager
    
    @pytest.mark.unit
    def test_login_success(self, mock_client_with_auth):
        """ログイン成功テスト"""
        client, mock_auth_manager = mock_client_with_auth
        
        expected_profile = {"handle": "test.user", "displayName": "Test User"}
        mock_auth_manager.login.return_value = expected_profile
        
        result = client.login("test.user", "test_password")
        
        mock_auth_manager.login.assert_called_once_with("test.user", "test_password")
        assert result == expected_profile
    
    @pytest.mark.unit
    def test_login_with_session_success(self, mock_client_with_auth):
        """セッション情報ログイン成功テスト"""
        client, mock_auth_manager = mock_client_with_auth
        
        expected_profile = {"handle": "test.user", "displayName": "Test User"}
        mock_auth_manager.login_with_session.return_value = expected_profile
        
        session_string = "test_session_string"
        result = client.login_with_session(session_string)
        
        mock_auth_manager.login_with_session.assert_called_once_with(session_string)
        assert result == expected_profile
    
    @pytest.mark.unit
    def test_logout_success(self, mock_client_with_auth):
        """ログアウト成功テスト"""
        client, mock_auth_manager = mock_client_with_auth
        
        mock_auth_manager.logout.return_value = True
        
        result = client.logout()
        
        mock_auth_manager.logout.assert_called_once()
        assert result == True
    
    @pytest.mark.unit
    def test_export_session_string(self, mock_client_with_auth):
        """セッション文字列エクスポートテスト"""
        client, mock_auth_manager = mock_client_with_auth
        
        expected_session = "exported_session_string"
        mock_auth_manager.export_session_string.return_value = expected_session
        
        result = client.export_session_string()
        
        mock_auth_manager.export_session_string.assert_called_once()
        assert result == expected_session
    
    @pytest.mark.unit
    def test_handle_api_error(self, mock_client_with_auth):
        """API エラーハンドリングテスト"""
        client, mock_auth_manager = mock_client_with_auth
        
        test_error = Exception("Test API error")
        mock_auth_manager.handle_api_error.return_value = True
        
        result = client.handle_api_error(test_error, "テスト操作")
        
        mock_auth_manager.handle_api_error.assert_called_once_with(test_error, "テスト操作")
        assert result == True


class TestBlueskyClientTimeline:
    """BlueskyClient タイムラインテスト"""
    
    @pytest.fixture
    def mock_client_with_api(self):
        """APIクライアント付きモッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_api_client, mock_auth_manager
    
    @pytest.mark.unit
    def test_get_timeline_success_logged_in(self, mock_client_with_api):
        """ログイン状態でのタイムライン取得成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_with_api
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_timeline = {"feed": [{"text": "Test post"}]}
        mock_api_client.get_timeline.return_value = expected_timeline
        
        result = client.get_timeline(limit=10)
        
        mock_api_client.get_timeline.assert_called_once_with(10)
        assert result == expected_timeline
    
    @pytest.mark.unit
    def test_get_timeline_not_logged_in(self, mock_client_with_api):
        """未ログイン状態でのタイムライン取得エラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_with_api
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="タイムラインの取得にはログインが必要です"):
            client.get_timeline()
        
        # API呼び出しされないことを確認
        mock_api_client.get_timeline.assert_not_called()
    
    @pytest.mark.unit
    def test_get_timeline_api_protocol_error(self, mock_client_with_api):
        """タイムライン取得でのAtProtocolErrorテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_with_api
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        mock_auth_manager.handle_api_error.return_value = True  # 認証エラーを示す
        
        # AtProtocolErrorをシミュレート
        api_error = AtProtocolError("Authentication failed")
        mock_api_client.get_timeline.side_effect = api_error
        
        with pytest.raises(AuthenticationError):
            client.get_timeline()
        
        # エラーハンドリングが呼ばれることを確認
        mock_auth_manager.handle_api_error.assert_called_once_with(api_error, "タイムライン取得")
    
    @pytest.mark.unit
    def test_get_timeline_api_protocol_error_non_auth(self, mock_client_with_api):
        """非認証AtProtocolErrorの再スローテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_with_api
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        mock_auth_manager.handle_api_error.return_value = False  # 非認証エラーを示す
        
        # AtProtocolErrorをシミュレート
        api_error = AtProtocolError("Rate limit exceeded")
        mock_api_client.get_timeline.side_effect = api_error
        
        with pytest.raises(AtProtocolError):
            client.get_timeline()
        
        mock_auth_manager.handle_api_error.assert_called_once_with(api_error, "タイムライン取得")
    
    @pytest.mark.unit
    def test_get_timeline_generic_exception(self, mock_client_with_api):
        """タイムライン取得での一般例外テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_with_api
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        # 一般例外をシミュレート
        generic_error = ValueError("Unexpected error")
        mock_api_client.get_timeline.side_effect = generic_error
        
        with pytest.raises(ValueError):
            client.get_timeline()


class TestBlueskyClientPostOperations:
    """BlueskyClient 投稿操作テスト"""
    
    @pytest.fixture
    def mock_client_for_posts(self):
        """投稿操作用モッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_api_client, mock_auth_manager
    
    @pytest.mark.unit
    def test_send_post_success(self, mock_client_for_posts):
        """投稿送信成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.post/123"}
        mock_api_client.send_post.return_value = expected_result
        
        result = client.send_post("Test post content")
        
        mock_api_client.send_post.assert_called_once_with("Test post content", None)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_send_post_with_images(self, mock_client_for_posts):
        """画像付き投稿送信テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.post/124"}
        mock_api_client.send_post.return_value = expected_result
        
        test_images = ["image1.jpg", "image2.png"]
        result = client.send_post("Post with images", images=test_images)
        
        mock_api_client.send_post.assert_called_once_with("Post with images", test_images)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_send_post_not_logged_in(self, mock_client_for_posts):
        """未ログイン状態での投稿送信エラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="投稿にはログインが必要です"):
            client.send_post("Test post")
        
        mock_api_client.send_post.assert_not_called()
    
    @pytest.mark.unit
    def test_send_post_api_error(self, mock_client_for_posts):
        """投稿送信でのAPIエラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        # AtProtocolErrorをシミュレート
        api_error = AtProtocolError("Post too long")
        mock_api_client.send_post.side_effect = api_error
        
        with pytest.raises(AtProtocolError):
            client.send_post("Test post")
    
    @pytest.mark.unit
    def test_send_post_generic_error(self, mock_client_for_posts):
        """投稿送信での一般エラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        # 一般例外をシミュレート
        generic_error = ConnectionError("Network error")
        mock_api_client.send_post.side_effect = generic_error
        
        with pytest.raises(ConnectionError):
            client.send_post("Test post")
    
    @pytest.mark.unit
    def test_upload_blob_success(self, mock_client_for_posts):
        """ファイルアップロード成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"ref": "blob_ref_123", "mimeType": "image/jpeg"}
        mock_api_client.upload_blob.return_value = expected_result
        
        test_data = b"test file data"
        result = client.upload_blob(test_data, "image/jpeg")
        
        mock_api_client.upload_blob.assert_called_once_with(test_data, "image/jpeg")
        assert result == expected_result
    
    @pytest.mark.unit
    def test_upload_blob_not_logged_in(self, mock_client_for_posts):
        """未ログイン状態でのファイルアップロードエラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_posts
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="ファイルのアップロードにはログインが必要です"):
            client.upload_blob(b"test data")
        
        mock_api_client.upload_blob.assert_not_called()


class TestBlueskyClientPostInteractions:
    """BlueskyClient 投稿相互作用テスト"""
    
    @pytest.fixture
    def mock_client_for_interactions(self):
        """投稿相互作用用モッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_api_client, mock_auth_manager
    
    @pytest.mark.unit
    def test_like_post_success(self, mock_client_for_interactions):
        """投稿いいね成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.like/123"}
        mock_api_client.like.return_value = expected_result
        
        result = client.like("at://post/uri", "post_cid")
        
        mock_api_client.like.assert_called_once_with("at://post/uri", "post_cid")
        assert result == expected_result
    
    @pytest.mark.unit
    def test_like_post_not_logged_in(self, mock_client_for_interactions):
        """未ログイン状態での投稿いいねエラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="いいねにはログインが必要です"):
            client.like("at://post/uri", "post_cid")
        
        mock_api_client.like.assert_not_called()
    
    @pytest.mark.unit
    def test_delete_post_success(self, mock_client_for_interactions):
        """投稿削除成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"success": True}
        mock_api_client.delete_post.return_value = expected_result
        
        result = client.delete_post("at://post/uri")
        
        mock_api_client.delete_post.assert_called_once_with("at://post/uri")
        assert result == expected_result
    
    @pytest.mark.unit
    def test_reply_to_post_success(self, mock_client_for_interactions):
        """投稿返信成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.post/reply123"}
        mock_api_client.reply_to_post.return_value = expected_result
        
        reply_to_data = {"uri": "at://original/post", "cid": "original_cid"}
        result = client.reply_to_post("Reply text", reply_to_data)
        
        mock_api_client.reply_to_post.assert_called_once_with("Reply text", reply_to_data)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_quote_post_success(self, mock_client_for_interactions):
        """投稿引用成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.post/quote123"}
        mock_api_client.quote_post.return_value = expected_result
        
        quote_of_data = {"uri": "at://quoted/post", "cid": "quoted_cid"}
        result = client.quote_post("Quote comment", quote_of_data)
        
        mock_api_client.quote_post.assert_called_once_with("Quote comment", quote_of_data)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_repost_success(self, mock_client_for_interactions):
        """リポスト成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.repost/123"}
        mock_api_client.repost.return_value = expected_result
        
        repost_of_data = {"uri": "at://reposted/post", "cid": "reposted_cid"}
        result = client.repost(repost_of_data)
        
        mock_api_client.repost.assert_called_once_with(repost_of_data)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_get_profile_success(self, mock_client_for_interactions):
        """プロフィール取得成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_interactions
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_profile = {"handle": "target.user", "displayName": "Target User"}
        mock_api_client.get_profile.return_value = expected_profile
        
        result = client.get_profile("target.user")
        
        mock_api_client.get_profile.assert_called_once_with("target.user")
        assert result == expected_profile


class TestBlueskyClientUserManagement:
    """BlueskyClient ユーザー管理テスト"""
    
    @pytest.fixture
    def mock_client_for_user_management(self):
        """ユーザー管理用モッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient'), \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler') as mock_error_handler_class, \
             patch('core.client.facade.BlueskyUserManager') as mock_user_manager_class:
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            mock_error_handler = Mock()
            mock_error_handler_class.return_value = mock_error_handler
            
            mock_user_manager = Mock()
            mock_user_manager_class.return_value = mock_user_manager
            
            client = BlueskyClient()
            return client, mock_auth_manager, mock_error_handler, mock_user_manager
    
    @pytest.mark.unit
    def test_follow_user_success(self, mock_client_for_user_management):
        """ユーザーフォロー成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://follow/123"}
        mock_error_handler.safe_api_call.return_value = expected_result
        
        result = client.follow("target.user")
        
        mock_error_handler.safe_api_call.assert_called_once_with(
            mock_user_manager.follow, "target.user", operation_name="フォロー"
        )
        assert result == expected_result
    
    @pytest.mark.unit
    def test_follow_user_not_logged_in(self, mock_client_for_user_management):
        """未ログイン状態でのフォローエラーテスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="フォローにはログインが必要です"):
            client.follow("target.user")
        
        mock_error_handler.safe_api_call.assert_not_called()
    
    @pytest.mark.unit
    def test_unfollow_user_success(self, mock_client_for_user_management):
        """ユーザーフォロー解除成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"success": True}
        mock_error_handler.safe_api_call.return_value = expected_result
        
        result = client.unfollow("target.user")
        
        mock_error_handler.safe_api_call.assert_called_once_with(
            mock_user_manager.unfollow, "target.user", operation_name="フォロー解除"
        )
        assert result == expected_result
    
    @pytest.mark.unit
    def test_block_user_success(self, mock_client_for_user_management):
        """ユーザーブロック成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://block/123"}
        mock_error_handler.safe_api_call.return_value = expected_result
        
        result = client.block("target.user")
        
        mock_error_handler.safe_api_call.assert_called_once_with(
            mock_user_manager.block, "target.user", operation_name="ブロック"
        )
        assert result == expected_result
    
    @pytest.mark.unit
    def test_mute_user_success(self, mock_client_for_user_management):
        """ユーザーミュート成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://mute/123"}
        mock_error_handler.safe_api_call.return_value = expected_result
        
        result = client.mute("target.user")
        
        mock_error_handler.safe_api_call.assert_called_once_with(
            mock_user_manager.mute, "target.user", operation_name="ミュート"
        )
        assert result == expected_result
    
    @pytest.mark.unit
    def test_get_following_success(self, mock_client_for_user_management):
        """フォロー中ユーザー一覧取得成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"follows": [{"handle": "user1"}, {"handle": "user2"}]}
        mock_error_handler.handle_with_auth_check.return_value = expected_result
        
        result = client.get_following("test.user", limit=50, cursor="cursor123")
        
        mock_error_handler.handle_with_auth_check.assert_called_once_with(
            mock_user_manager.get_following, "test.user", 50, "cursor123",
            operation_name="フォロー中ユーザー一覧取得"
        )
        assert result == expected_result
    
    @pytest.mark.unit
    def test_get_blocked_users_success(self, mock_client_for_user_management):
        """ブロックしたユーザー一覧取得成功テスト"""
        client, mock_auth_manager, mock_error_handler, mock_user_manager = mock_client_for_user_management
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"blocks": [{"handle": "blocked1"}, {"handle": "blocked2"}]}
        mock_error_handler.handle_with_auth_check.return_value = expected_result
        
        result = client.get_blocked_users(limit=25)
        
        mock_error_handler.handle_with_auth_check.assert_called_once_with(
            mock_user_manager.get_blocked_users, 25, None,
            operation_name="ブロックしたユーザー一覧取得"
        )
        assert result == expected_result


class TestBlueskyClientAdvancedFeatures:
    """BlueskyClient 高度な機能テスト"""
    
    @pytest.fixture
    def mock_client_for_advanced(self):
        """高度な機能用モッククライアント"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            
            client = BlueskyClient()
            return client, mock_api_client, mock_auth_manager
    
    @pytest.mark.unit
    def test_quote_post_advanced_success(self, mock_client_for_advanced):
        """高度な引用投稿成功テスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_advanced
        
        # ログイン状態設定
        mock_auth_manager.is_logged_in = True
        
        expected_result = {"uri": "at://test.user/app.bsky.feed.post/advquote123"}
        mock_api_client.quote_post_advanced.return_value = expected_result
        
        quote_of_data = {"uri": "at://quoted/post", "cid": "quoted_cid", "metadata": {"advanced": True}}
        result = client.quote_post_advanced("Advanced quote comment", quote_of_data)
        
        mock_api_client.quote_post_advanced.assert_called_once_with("Advanced quote comment", quote_of_data)
        assert result == expected_result
    
    @pytest.mark.unit
    def test_quote_post_advanced_not_logged_in(self, mock_client_for_advanced):
        """未ログイン状態での高度な引用投稿エラーテスト"""
        client, mock_api_client, mock_auth_manager = mock_client_for_advanced
        
        # 未ログイン状態設定
        mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="引用にはログインが必要です"):
            client.quote_post_advanced("Comment", {"uri": "test"})
        
        mock_api_client.quote_post_advanced.assert_not_called()


class TestBlueskyClientLoggingIntegration:
    """BlueskyClient ログ統合テスト"""
    
    @pytest.mark.unit
    def test_logging_integration_timeline_error(self, caplog):
        """タイムライン取得エラー時のログ出力テスト"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            mock_auth_manager.is_logged_in = False
            
            client = BlueskyClient()
            
            with caplog.at_level(logging.ERROR):
                try:
                    client.get_timeline()
                except Exception:
                    pass
            
            # ログメッセージが出力されることを確認
            assert "タイムラインの取得に失敗しました: ログインしていません" in caplog.text
    
    @pytest.mark.unit 
    def test_logging_integration_post_error(self, caplog):
        """投稿送信エラー時のログ出力テスト"""
        from core.client.facade import BlueskyClient
        
        with patch('core.client.facade.BlueskyApiClient') as mock_api_client_class, \
             patch('core.client.facade.BlueskySessionManager'), \
             patch('core.client.facade.BlueskyAuthManager') as mock_auth_manager_class, \
             patch('core.client.facade.UnifiedErrorHandler'), \
             patch('core.client.facade.BlueskyUserManager'):
            
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client
            
            mock_auth_manager = Mock()
            mock_auth_manager_class.return_value = mock_auth_manager
            mock_auth_manager.is_logged_in = True
            
            # AtProtocolErrorをシミュレート
            api_error = AtProtocolError("API error occurred")
            mock_api_client.send_post.side_effect = api_error
            
            client = BlueskyClient()
            
            with caplog.at_level(logging.ERROR):
                try:
                    client.send_post("Test post")
                except Exception:
                    pass
            
            # ログメッセージが出力されることを確認
            assert "投稿時にBluesky APIエラー" in caplog.text