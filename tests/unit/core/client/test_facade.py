#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
BlueskyClientファサードクラス単体テスト (Phase 2 リファクタリング版)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Optional, Dict, Any, List, Callable

from core.client.facade import BlueskyClient
from core.client.api_client import BlueskyApiClient
from core.client.auth_manager import BlueskyAuthManager
from core.client.session_manager import BlueskySessionManager
from core.client.user_manager import BlueskyUserManager
from core.error_handler import UnifiedErrorHandler
from core.exceptions import AuthenticationError
from atproto.exceptions import AtProtocolError


@pytest.mark.unit
class TestBlueskyClientInstantiation:
    """BlueskyClientインスタンス化テスト"""
    
    def test_default_instantiation(self):
        """デフォルトインスタンス化テスト"""
        with patch.multiple(
            'core.client.facade',
            BlueskyApiClient=Mock(),
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient()
            
            assert client is not None
            assert client.api_client is not None
            assert client.session_manager is not None
            assert client.auth_manager is not None
            assert client.error_handler is not None
            assert client.user_manager is not None
    
    def test_dependency_injection_instantiation(self):
        """依存性注入によるインスタンス化テスト"""
        # モックコンポーネントを作成
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = Mock()
        mock_session_manager = Mock(spec=BlueskySessionManager)
        mock_auth_manager = Mock(spec=BlueskyAuthManager)
        mock_error_handler = Mock(spec=UnifiedErrorHandler)
        mock_user_manager = Mock(spec=BlueskyUserManager)
        
        # 依存性注入でインスタンス作成
        client = BlueskyClient(
            api_client=mock_api_client,
            session_manager=mock_session_manager,
            auth_manager=mock_auth_manager,
            error_handler=mock_error_handler,
            user_manager=mock_user_manager
        )
        
        # 注入されたコンポーネントが使用されることを確認
        assert client.api_client is mock_api_client
        assert client.session_manager is mock_session_manager
        assert client.auth_manager is mock_auth_manager
        assert client.error_handler is mock_error_handler
        assert client.user_manager is mock_user_manager
    
    def test_partial_dependency_injection(self):
        """部分的依存性注入テスト"""
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = Mock()
        
        with patch.multiple(
            'core.client.facade',
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient(api_client=mock_api_client)
            
            # 注入されたコンポーネントが使用される
            assert client.api_client is mock_api_client
            # 他のコンポーネントはデフォルトで作成される
            assert client.session_manager is not None
            assert client.auth_manager is not None
            assert client.error_handler is not None
            assert client.user_manager is not None


@pytest.mark.unit
class TestBlueskyClientFactoryMethods:
    """BlueskyClientファクトリメソッドテスト"""
    
    def test_create_for_testing_basic(self):
        """基本的なテスト用インスタンス作成テスト"""
        with patch.multiple(
            'core.client.facade',
            BlueskyApiClient=Mock(),
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient.create_for_testing()
            
            assert isinstance(client, BlueskyClient)
            assert client.api_client is not None
            assert client.session_manager is not None
            assert client.auth_manager is not None
            assert client.error_handler is not None
            assert client.user_manager is not None
    
    def test_create_for_testing_with_mock_api_client(self):
        """モックAPIクライアントを使用したテスト用インスタンス作成テスト"""
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = Mock()
        
        with patch.multiple(
            'core.client.facade',
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient.create_for_testing(mock_api_client=mock_api_client)
            
            assert isinstance(client, BlueskyClient)
            assert client.api_client is mock_api_client
    
    def test_create_with_custom_credential_manager(self):
        """カスタム認証情報管理を使用するインスタンス作成テスト"""
        mock_credential_manager = Mock()
        
        with patch.multiple(
            'core.client.facade',
            BlueskyApiClient=Mock(),
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient.create_with_custom_credential_manager(mock_credential_manager)
            
            assert isinstance(client, BlueskyClient)
            assert client.api_client is not None
            assert client.session_manager is not None
            assert client.auth_manager is not None
            assert client.error_handler is not None
            assert client.user_manager is not None


@pytest.mark.unit
class TestBlueskyClientProperties:
    """BlueskyClientプロパティテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_auth_manager = Mock()
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_profile_property_getter(self):
        """プロフィールプロパティゲッターテスト"""
        test_profile = {"did": "did:test", "handle": "test.bsky.social"}
        self.mock_auth_manager.profile = test_profile
        
        assert self.client.profile == test_profile
    
    def test_profile_property_setter(self):
        """プロフィールプロパティセッターテスト"""
        test_profile = {"did": "did:test", "handle": "test.bsky.social"}
        
        self.client.profile = test_profile
        
        assert self.mock_auth_manager.profile == test_profile
    
    def test_is_logged_in_property_getter(self):
        """ログイン状態プロパティゲッターテスト"""
        self.mock_auth_manager.is_logged_in = True
        
        assert self.client.is_logged_in is True
        
        self.mock_auth_manager.is_logged_in = False
        
        assert self.client.is_logged_in is False
    
    def test_is_logged_in_property_setter(self):
        """ログイン状態プロパティセッターテスト"""
        self.client.is_logged_in = True
        
        assert self.mock_auth_manager.is_logged_in is True
        
        self.client.is_logged_in = False
        
        assert self.mock_auth_manager.is_logged_in is False
    
    def test_user_did_property_getter(self):
        """ユーザーDIDプロパティゲッターテスト"""
        test_did = "did:plc:test123"
        self.mock_auth_manager.user_did = test_did
        
        assert self.client.user_did == test_did
    
    def test_user_did_property_setter(self):
        """ユーザーDIDプロパティセッターテスト"""
        test_did = "did:plc:test123"
        
        self.client.user_did = test_did
        
        assert self.mock_auth_manager.user_did == test_did


@pytest.mark.unit 
class TestBlueskyClientEventHandling:
    """BlueskyClientイベントハンドリングテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_auth_manager = Mock()
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_on_session_change_registration(self):
        """セッション変更イベントハンドラ登録テスト"""
        test_handler = Mock()
        
        self.client.on_session_change(test_handler)
        
        self.mock_session_manager.on_session_change.assert_called_once_with(test_handler)
    
    def test_remove_session_change_handler(self):
        """セッション変更イベントハンドラ削除テスト"""
        test_handler = Mock()
        self.mock_session_manager.remove_session_change_handler.return_value = True
        
        result = self.client.remove_session_change_handler(test_handler)
        
        self.mock_session_manager.remove_session_change_handler.assert_called_once_with(test_handler)
        assert result is True
    
    def test_remove_session_change_handler_not_found(self):
        """存在しないセッション変更イベントハンドラ削除テスト"""
        test_handler = Mock()
        self.mock_session_manager.remove_session_change_handler.return_value = False
        
        result = self.client.remove_session_change_handler(test_handler)
        
        self.mock_session_manager.remove_session_change_handler.assert_called_once_with(test_handler)
        assert result is False


@pytest.mark.unit
class TestBlueskyClientAuthenticationMethods:
    """BlueskyClient認証メソッドテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_auth_manager = Mock()
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_login_success(self):
        """ログイン成功テスト"""
        test_profile = {"did": "did:test", "handle": "test.bsky.social"}
        self.mock_auth_manager.login.return_value = test_profile
        
        result = self.client.login("test_user", "test_password")
        
        self.mock_auth_manager.login.assert_called_once_with("test_user", "test_password")
        assert result == test_profile
    
    def test_login_with_session_success(self):
        """セッション文字列を使用したログイン成功テスト"""
        test_profile = {"did": "did:test", "handle": "test.bsky.social"}
        test_session = "test_session_string"
        self.mock_auth_manager.login_with_session.return_value = test_profile
        
        result = self.client.login_with_session(test_session)
        
        self.mock_auth_manager.login_with_session.assert_called_once_with(test_session)
        assert result == test_profile
    
    def test_logout_success(self):
        """ログアウト成功テスト"""
        self.mock_auth_manager.logout.return_value = True
        
        result = self.client.logout()
        
        self.mock_auth_manager.logout.assert_called_once()
        assert result is True
    
    def test_export_session_string(self):
        """セッション文字列エクスポートテスト"""
        test_session_string = "exported_session_string"
        self.mock_auth_manager.export_session_string.return_value = test_session_string
        
        result = self.client.export_session_string()
        
        self.mock_auth_manager.export_session_string.assert_called_once()
        assert result == test_session_string
    
    def test_handle_api_error(self):
        """APIエラー処理テスト"""
        test_error = AtProtocolError("Test API error")
        self.mock_auth_manager.handle_api_error.return_value = True
        
        result = self.client.handle_api_error(test_error, "テスト操作")
        
        self.mock_auth_manager.handle_api_error.assert_called_once_with(test_error, "テスト操作")
        assert result is True


@pytest.mark.unit
class TestBlueskyClientTimelineMethods:
    """BlueskyClientタイムラインメソッドテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_auth_manager = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_get_timeline_success(self):
        """タイムライン取得成功テスト"""
        test_timeline_data = {"feed": [{"uri": "test://post/1"}]}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.get_timeline.return_value = test_timeline_data
        
        result = self.client.get_timeline(limit=25)
        
        self.mock_api_client.get_timeline.assert_called_once_with(25)
        assert result == test_timeline_data
    
    def test_get_timeline_not_logged_in(self):
        """未ログイン状態でのタイムライン取得テスト"""
        self.mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="タイムラインの取得にはログインが必要です"):
            self.client.get_timeline()
    
    def test_get_timeline_api_error_auth_required(self):
        """認証エラーが必要なAPIエラーテスト"""
        self.mock_auth_manager.is_logged_in = True
        test_error = AtProtocolError("Authentication failed")
        self.mock_api_client.get_timeline.side_effect = test_error
        self.mock_auth_manager.handle_api_error.return_value = True  # 再認証が必要
        
        with pytest.raises(AuthenticationError, match="セッションが無効になりました"):
            self.client.get_timeline()
        
        self.mock_auth_manager.handle_api_error.assert_called_once_with(test_error, "タイムライン取得")
    
    def test_get_timeline_api_error_no_auth_required(self):
        """再認証不要なAPIエラーテスト"""
        self.mock_auth_manager.is_logged_in = True
        test_error = AtProtocolError("Network error")
        self.mock_api_client.get_timeline.side_effect = test_error
        self.mock_auth_manager.handle_api_error.return_value = False  # 再認証不要
        
        with pytest.raises(AtProtocolError, match="Network error"):
            self.client.get_timeline()


@pytest.mark.unit
class TestBlueskyClientPostMethods:
    """BlueskyClient投稿メソッドテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_auth_manager = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_send_post_success(self):
        """投稿送信成功テスト"""
        test_result = {"uri": "test://post/123", "cid": "test_cid"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.send_post.return_value = test_result
        
        result = self.client.send_post("テスト投稿")
        
        self.mock_api_client.send_post.assert_called_once_with("テスト投稿", None)
        assert result == test_result
    
    def test_send_post_with_images(self):
        """画像付き投稿送信テスト"""
        test_result = {"uri": "test://post/123", "cid": "test_cid"}
        test_images = [{"blob": "image_blob_1"}]
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.send_post.return_value = test_result
        
        result = self.client.send_post("テスト投稿", images=test_images)
        
        self.mock_api_client.send_post.assert_called_once_with("テスト投稿", test_images)
        assert result == test_result
    
    def test_send_post_not_logged_in(self):
        """未ログイン状態での投稿送信テスト"""
        self.mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="投稿にはログインが必要です"):
            self.client.send_post("テスト投稿")
    
    def test_upload_blob_success(self):
        """ブロブアップロード成功テスト"""
        test_result = {"blob": {"ref": "test_blob_ref"}}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.upload_blob.return_value = test_result
        
        test_file_data = b"test_file_content"
        result = self.client.upload_blob(test_file_data, "image/png")
        
        self.mock_api_client.upload_blob.assert_called_once_with(test_file_data, "image/png")
        assert result == test_result
    
    def test_upload_blob_not_logged_in(self):
        """未ログイン状態でのブロブアップロードテスト"""
        self.mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="ファイルのアップロードにはログインが必要です"):
            self.client.upload_blob(b"test_data")


@pytest.mark.unit
class TestBlueskyClientUserInteractionMethods:
    """BlueskyClientユーザー操作メソッドテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_auth_manager = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_follow_success(self):
        """フォロー成功テスト"""
        test_result = {"uri": "test://follow/123"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.safe_api_call.return_value = test_result
        
        result = self.client.follow("test.bsky.social")
        
        self.mock_error_handler.safe_api_call.assert_called_once_with(
            self.mock_user_manager.follow, "test.bsky.social", operation_name="フォロー"
        )
        assert result == test_result
    
    def test_follow_not_logged_in(self):
        """未ログイン状態でのフォローテスト"""
        self.mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="フォローにはログインが必要です"):
            self.client.follow("test.bsky.social")
    
    def test_unfollow_success(self):
        """フォロー解除成功テスト"""
        test_result = {"success": True}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.safe_api_call.return_value = test_result
        
        result = self.client.unfollow("test.bsky.social")
        
        self.mock_error_handler.safe_api_call.assert_called_once_with(
            self.mock_user_manager.unfollow, "test.bsky.social", operation_name="フォロー解除"
        )
        assert result == test_result
    
    def test_block_success(self):
        """ブロック成功テスト"""
        test_result = {"uri": "test://block/123"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.safe_api_call.return_value = test_result
        
        result = self.client.block("test.bsky.social")
        
        self.mock_error_handler.safe_api_call.assert_called_once_with(
            self.mock_user_manager.block, "test.bsky.social", operation_name="ブロック"
        )
        assert result == test_result
    
    def test_mute_success(self):
        """ミュート成功テスト"""
        test_result = {"uri": "test://mute/123"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.safe_api_call.return_value = test_result
        
        result = self.client.mute("test.bsky.social")
        
        self.mock_error_handler.safe_api_call.assert_called_once_with(
            self.mock_user_manager.mute, "test.bsky.social", operation_name="ミュート"
        )
        assert result == test_result
    
    def test_get_following_success(self):
        """フォロー中ユーザー取得成功テスト"""
        test_result = {"follows": [{"handle": "user1.bsky.social"}]}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.handle_with_auth_check.return_value = test_result
        
        result = self.client.get_following("test.bsky.social", limit=50)
        
        self.mock_error_handler.handle_with_auth_check.assert_called_once_with(
            self.mock_user_manager.get_following, "test.bsky.social", 50, None,
            operation_name="フォロー中ユーザー一覧取得"
        )
        assert result == test_result
    
    def test_get_blocked_users_success(self):
        """ブロック済みユーザー取得成功テスト"""
        test_result = {"blocks": [{"handle": "blocked_user.bsky.social"}]}
        self.mock_auth_manager.is_logged_in = True
        self.mock_error_handler.handle_with_auth_check.return_value = test_result
        
        result = self.client.get_blocked_users(limit=50)
        
        self.mock_error_handler.handle_with_auth_check.assert_called_once_with(
            self.mock_user_manager.get_blocked_users, 50, None,
            operation_name="ブロックしたユーザー一覧取得"
        )
        assert result == test_result


@pytest.mark.unit
class TestBlueskyClientPostInteractionMethods:
    """BlueskyClient投稿操作メソッドテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の設定"""
        self.mock_api_client = Mock(spec=BlueskyApiClient)
        self.mock_api_client.client = Mock()
        self.mock_auth_manager = Mock()
        self.mock_session_manager = Mock(spec=BlueskySessionManager)
        self.mock_error_handler = Mock(spec=UnifiedErrorHandler)
        self.mock_user_manager = Mock(spec=BlueskyUserManager)
        
        self.client = BlueskyClient(
            api_client=self.mock_api_client,
            session_manager=self.mock_session_manager,
            auth_manager=self.mock_auth_manager,
            error_handler=self.mock_error_handler,
            user_manager=self.mock_user_manager
        )
    
    def test_like_success(self):
        """いいね成功テスト"""
        test_result = {"uri": "test://like/123"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.like.return_value = test_result
        
        result = self.client.like("test://post/123", "test_cid")
        
        self.mock_api_client.like.assert_called_once_with("test://post/123", "test_cid")
        assert result == test_result
    
    def test_like_not_logged_in(self):
        """未ログイン状態でのいいねテスト"""
        self.mock_auth_manager.is_logged_in = False
        
        with pytest.raises(Exception, match="いいねにはログインが必要です"):
            self.client.like("test://post/123", "test_cid")
    
    def test_delete_post_success(self):
        """投稿削除成功テスト"""
        test_result = {"success": True}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.delete_post.return_value = test_result
        
        result = self.client.delete_post("test://post/123")
        
        self.mock_api_client.delete_post.assert_called_once_with("test://post/123")
        assert result == test_result
    
    def test_reply_to_post_success(self):
        """返信成功テスト"""
        test_result = {"uri": "test://reply/123"}
        test_reply_to = {"uri": "test://post/original", "cid": "original_cid"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.reply_to_post.return_value = test_result
        
        result = self.client.reply_to_post("返信テスト", test_reply_to)
        
        self.mock_api_client.reply_to_post.assert_called_once_with("返信テスト", test_reply_to)
        assert result == test_result
    
    def test_quote_post_success(self):
        """引用投稿成功テスト"""
        test_result = {"uri": "test://quote/123"}
        test_quote_of = {"uri": "test://post/original", "cid": "original_cid"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.quote_post.return_value = test_result
        
        result = self.client.quote_post("引用テスト", test_quote_of)
        
        self.mock_api_client.quote_post.assert_called_once_with("引用テスト", test_quote_of)
        assert result == test_result
    
    def test_repost_success(self):
        """リポスト成功テスト"""
        test_result = {"uri": "test://repost/123"}
        test_repost_of = {"uri": "test://post/original", "cid": "original_cid"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.repost.return_value = test_result
        
        result = self.client.repost(test_repost_of)
        
        self.mock_api_client.repost.assert_called_once_with(test_repost_of)
        assert result == test_result
    
    def test_get_profile_success(self):
        """プロフィール取得成功テスト"""
        test_result = {"handle": "test.bsky.social", "did": "did:plc:test"}
        self.mock_auth_manager.is_logged_in = True
        self.mock_api_client.get_profile.return_value = test_result
        
        result = self.client.get_profile("test.bsky.social")
        
        self.mock_api_client.get_profile.assert_called_once_with("test.bsky.social")
        assert result == test_result


@pytest.mark.unit
class TestBlueskyClientPropertyBinding:
    """BlueskyClientプロパティバインディングテスト"""
    
    def test_client_property_binding(self):
        """clientプロパティバインディングテスト"""
        mock_atproto_client = Mock()
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = mock_atproto_client
        
        with patch.multiple(
            'core.client.facade',
            BlueskySessionManager=Mock(),
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient(api_client=mock_api_client)
            
            # clientプロパティがapi_client.clientにバインドされることを確認
            assert client.client is mock_atproto_client


@pytest.mark.unit
class TestBlueskyClientIntegration:
    """BlueskyClient統合テスト"""
    
    def test_component_registration_flow(self):
        """コンポーネント登録フローテスト"""
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = Mock()
        mock_session_manager = Mock(spec=BlueskySessionManager)
        
        with patch.multiple(
            'core.client.facade',
            BlueskyAuthManager=Mock(),
            UnifiedErrorHandler=Mock(),
            BlueskyUserManager=Mock()
        ):
            client = BlueskyClient(
                api_client=mock_api_client,
                session_manager=mock_session_manager
            )
            
            # セッションマネージャーにAPIクライアントが登録されることを確認
            mock_session_manager.register_client.assert_called_once_with(mock_api_client)
    
    def test_error_propagation_integration(self):
        """エラー伝播統合テスト"""
        mock_api_client = Mock(spec=BlueskyApiClient)
        mock_api_client.client = Mock()
        mock_auth_manager = Mock()
        mock_session_manager = Mock(spec=BlueskySessionManager)
        mock_error_handler = Mock(spec=UnifiedErrorHandler)
        mock_user_manager = Mock(spec=BlueskyUserManager)
        
        # APIエラーをシミュレート
        test_error = AtProtocolError("Test error")
        mock_api_client.get_timeline.side_effect = test_error
        mock_auth_manager.is_logged_in = True
        mock_auth_manager.handle_api_error.return_value = False  # 再認証不要
        
        client = BlueskyClient(
            api_client=mock_api_client,
            session_manager=mock_session_manager,
            auth_manager=mock_auth_manager,
            error_handler=mock_error_handler,
            user_manager=mock_user_manager
        )
        
        # エラーが適切に伝播されることを確認
        with pytest.raises(AtProtocolError):
            client.get_timeline()
        
        # エラーハンドラーが呼び出されることを確認
        mock_auth_manager.handle_api_error.assert_called_once_with(test_error, "タイムライン取得")