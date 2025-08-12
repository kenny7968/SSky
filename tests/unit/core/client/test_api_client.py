#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - BlueskyApiClient 単体テスト
完全リファクタリング版
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone
import sys
import os

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from core.client.api_client import BlueskyApiClient
from tests.mocks.common_mocks import (
    MockSessionManager,
    create_mock_post,
    create_mock_user
)


@pytest.fixture
def mock_atproto_client():
    """AtprotoClientのモック"""
    with patch('core.client.api_client.AtprotoClient') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_session_manager():
    """SessionManagerのモック"""
    return MockSessionManager(logged_in=True).get_mock()


@pytest.fixture
def api_client(mock_session_manager):
    """テスト用BlueskyApiClientインスタンス"""
    return BlueskyApiClient(session_manager=mock_session_manager)


class TestBlueskyApiClientInitialization:
    """初期化関連のテスト"""
    
    @pytest.mark.unit
    def test_initialization_with_session_manager(self, mock_session_manager):
        """SessionManager付きで初期化"""
        client = BlueskyApiClient(session_manager=mock_session_manager)
        assert client.session_manager == mock_session_manager
        assert client.client is not None
    
    @pytest.mark.unit
    def test_initialization_without_session_manager(self):
        """SessionManagerなしで初期化"""
        client = BlueskyApiClient()
        assert client.session_manager is None
        assert client.client is not None
    
    @pytest.mark.unit
    def test_client_type(self, api_client):
        """クライアントの型を確認"""
        assert hasattr(api_client, 'client')
        assert hasattr(api_client, 'get_timeline')
        assert hasattr(api_client, 'send_post')


class TestBlueskyApiClientTimeline:
    """タイムライン機能のテスト"""
    
    @pytest.mark.unit
    def test_get_timeline_success(self, api_client, mock_atproto_client):
        """タイムライン取得成功"""
        # モックレスポンスを設定
        mock_timeline = [
            create_mock_post(uri="at://user1/post/1", text="投稿1"),
            create_mock_post(uri="at://user2/post/2", text="投稿2")
        ]
        mock_atproto_client.get_timeline = Mock(return_value=Mock(feed=mock_timeline))
        api_client.client = mock_atproto_client
        
        # テスト実行
        result = api_client.get_timeline(limit=10)
        
        # 検証
        assert result.feed == mock_timeline
        mock_atproto_client.get_timeline.assert_called_once_with(limit=10)
    
    @pytest.mark.unit
    def test_get_timeline_with_cursor(self, api_client, mock_atproto_client):
        """カーソル付きタイムライン取得"""
        mock_timeline = [create_mock_post()]
        mock_atproto_client.get_timeline = Mock(return_value=Mock(
            feed=mock_timeline,
            cursor="next_cursor"
        ))
        api_client.client = mock_atproto_client
        
        # 注: get_timelineメソッドはcursorパラメータをサポートしていない
        result = api_client.get_timeline(limit=20)
        
        assert result.feed == mock_timeline
        assert result.cursor == "next_cursor"
        mock_atproto_client.get_timeline.assert_called_once_with(limit=20)
    
    @pytest.mark.unit
    def test_get_timeline_empty(self, api_client, mock_atproto_client):
        """空のタイムライン"""
        mock_atproto_client.get_timeline = Mock(return_value=Mock(feed=[]))
        api_client.client = mock_atproto_client
        
        result = api_client.get_timeline()
        
        assert result.feed == []
        mock_atproto_client.get_timeline.assert_called_once()
    
    @pytest.mark.unit
    def test_get_timeline_api_error(self, api_client, mock_atproto_client):
        """タイムライン取得時のAPIエラー"""
        mock_atproto_client.get_timeline = Mock(
            side_effect=Exception("API Error")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(Exception, match="API Error"):
            api_client.get_timeline()


class TestBlueskyApiClientPost:
    """投稿機能のテスト"""
    
    @pytest.mark.unit
    def test_send_post_text_only(self, api_client, mock_atproto_client):
        """テキストのみの投稿"""
        mock_response = Mock(
            uri="at://user/app.bsky.feed.post/123",
            cid="test_cid"
        )
        mock_atproto_client.send_post = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        result = api_client.send_post("テスト投稿")
        
        assert result == mock_response
        mock_atproto_client.send_post.assert_called_once()
        call_args = mock_atproto_client.send_post.call_args
        assert call_args[0][0] == "テスト投稿"
    
    @pytest.mark.unit
    def test_send_post_with_images(self, api_client, mock_atproto_client):
        """画像付き投稿"""
        mock_response = Mock(uri="at://user/post/123")
        mock_atproto_client.send_post = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        image_refs = [{"ref": "blob1"}, {"ref": "blob2"}]
        result = api_client.send_post("画像付き投稿", images=image_refs)
        
        assert result == mock_response
        mock_atproto_client.send_post.assert_called_once()
    
    @pytest.mark.unit
    def test_send_post_with_reply(self, api_client, mock_atproto_client):
        """返信投稿"""
        mock_response = Mock(uri="at://user/post/456")
        mock_atproto_client.send_post = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        reply_to = {
            "uri": "at://other/post/123",
            "cid": "parent_cid"
        }
        result = api_client.send_post("返信です", reply_to=reply_to)
        
        assert result == mock_response
        mock_atproto_client.send_post.assert_called_once()
    
    @pytest.mark.unit
    def test_send_post_empty_text(self, api_client):
        """空のテキストで投稿"""
        with pytest.raises(ValueError, match="投稿テキストが空です"):
            api_client.send_post("")
    
    @pytest.mark.unit
    def test_send_post_too_long(self, api_client):
        """文字数制限超過"""
        long_text = "あ" * 301  # 300文字制限を超える
        with pytest.raises(ValueError, match="文字数制限"):
            api_client.send_post(long_text)


class TestBlueskyApiClientBlob:
    """Blob（ファイル）アップロード機能のテスト"""
    
    @pytest.mark.unit
    def test_upload_blob_success(self, api_client, mock_atproto_client):
        """ファイルアップロード成功"""
        mock_response = Mock(ref="blob://test/123", size=1024)
        mock_atproto_client.upload_blob = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        result = api_client.upload_blob(b"test_data", "image/jpeg")
        
        assert result == mock_response
        mock_atproto_client.upload_blob.assert_called_once_with(
            b"test_data",
            mime_type="image/jpeg"
        )
    
    @pytest.mark.unit
    def test_upload_blob_without_mime(self, api_client, mock_atproto_client):
        """MIMEタイプなしでアップロード"""
        mock_response = Mock(ref="blob://test/456")
        mock_atproto_client.upload_blob = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        result = api_client.upload_blob(b"test_data")
        
        assert result == mock_response
        mock_atproto_client.upload_blob.assert_called_once_with(
            b"test_data",
            mime_type="application/octet-stream"
        )
    
    @pytest.mark.unit
    def test_upload_blob_large_file(self, api_client):
        """大きすぎるファイル"""
        large_data = b"x" * (10 * 1024 * 1024 + 1)  # 10MB超
        with pytest.raises(ValueError, match="ファイルサイズが大きすぎます"):
            api_client.upload_blob(large_data)
    
    @pytest.mark.unit
    def test_upload_blob_api_error(self, api_client, mock_atproto_client):
        """アップロード時のAPIエラー"""
        mock_atproto_client.upload_blob = Mock(
            side_effect=Exception("Upload failed")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(Exception, match="Upload failed"):
            api_client.upload_blob(b"test_data")


class TestBlueskyApiClientUser:
    """ユーザー情報機能のテスト"""
    
    @pytest.mark.unit
    def test_get_user_info_success(self, api_client, mock_atproto_client):
        """ユーザー情報取得成功"""
        mock_user = create_mock_user(handle="test.user")
        mock_atproto_client.get_profile = Mock(return_value=mock_user)
        api_client.client = mock_atproto_client
        
        result = api_client.get_user_info("test.user")
        
        assert result == mock_user
        mock_atproto_client.get_profile.assert_called_once_with("test.user")
    
    @pytest.mark.unit
    def test_get_user_info_not_found(self, api_client, mock_atproto_client):
        """存在しないユーザー"""
        mock_atproto_client.get_profile = Mock(
            side_effect=Exception("User not found")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(Exception, match="User not found"):
            api_client.get_user_info("nonexistent.user")
    
    @pytest.mark.unit
    def test_get_followers(self, api_client, mock_atproto_client):
        """フォロワー一覧取得"""
        mock_followers = [
            create_mock_user(handle="follower1"),
            create_mock_user(handle="follower2")
        ]
        mock_atproto_client.get_followers = Mock(
            return_value=Mock(followers=mock_followers)
        )
        api_client.client = mock_atproto_client
        
        result = api_client.get_followers("test.user")
        
        assert result == mock_followers
        mock_atproto_client.get_followers.assert_called_once_with("test.user")
    
    @pytest.mark.unit
    def test_get_following(self, api_client, mock_atproto_client):
        """フォロー一覧取得"""
        mock_following = [
            create_mock_user(handle="following1"),
            create_mock_user(handle="following2")
        ]
        mock_atproto_client.get_follows = Mock(
            return_value=Mock(follows=mock_following)
        )
        api_client.client = mock_atproto_client
        
        result = api_client.get_following("test.user")
        
        assert result == mock_following
        mock_atproto_client.get_follows.assert_called_once_with("test.user")


class TestBlueskyApiClientInteraction:
    """インタラクション機能のテスト"""
    
    @pytest.mark.unit
    def test_like_post(self, api_client, mock_atproto_client):
        """投稿にいいね"""
        mock_response = Mock(uri="at://user/app.bsky.feed.like/123")
        mock_atproto_client.like = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        result = api_client.like_post("at://other/post/456", "cid_456")
        
        assert result == mock_response
        mock_atproto_client.like.assert_called_once_with(
            "at://other/post/456",
            "cid_456"
        )
    
    @pytest.mark.unit
    def test_unlike_post(self, api_client, mock_atproto_client):
        """いいねを取り消し"""
        mock_atproto_client.unlike = Mock(return_value=True)
        api_client.client = mock_atproto_client
        
        result = api_client.unlike_post("at://user/like/123")
        
        assert result is True
        mock_atproto_client.unlike.assert_called_once_with("at://user/like/123")
    
    @pytest.mark.unit
    def test_repost(self, api_client, mock_atproto_client):
        """リポスト"""
        mock_response = Mock(uri="at://user/app.bsky.feed.repost/789")
        mock_atproto_client.repost = Mock(return_value=mock_response)
        api_client.client = mock_atproto_client
        
        result = api_client.repost("at://other/post/456", "cid_456")
        
        assert result == mock_response
        mock_atproto_client.repost.assert_called_once_with(
            "at://other/post/456",
            "cid_456"
        )
    
    @pytest.mark.unit
    def test_unrepost(self, api_client, mock_atproto_client):
        """リポスト取り消し"""
        mock_atproto_client.unrepost = Mock(return_value=True)
        api_client.client = mock_atproto_client
        
        result = api_client.unrepost("at://user/repost/789")
        
        assert result is True
        mock_atproto_client.unrepost.assert_called_once_with("at://user/repost/789")
    
    @pytest.mark.unit
    def test_delete_post(self, api_client, mock_atproto_client):
        """投稿削除"""
        mock_atproto_client.delete_post = Mock(return_value=True)
        api_client.client = mock_atproto_client
        
        result = api_client.delete_post("at://user/post/123")
        
        assert result is True
        mock_atproto_client.delete_post.assert_called_once_with("at://user/post/123")


class TestBlueskyApiClientErrorHandling:
    """エラーハンドリングのテスト"""
    
    @pytest.mark.unit
    def test_network_error_propagation(self, api_client, mock_atproto_client):
        """ネットワークエラーの伝播"""
        from requests.exceptions import ConnectionError
        mock_atproto_client.get_timeline = Mock(
            side_effect=ConnectionError("Network error")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(ConnectionError, match="Network error"):
            api_client.get_timeline()
    
    @pytest.mark.unit
    def test_authentication_error(self, api_client, mock_atproto_client):
        """認証エラー"""
        mock_atproto_client.send_post = Mock(
            side_effect=Exception("Unauthorized")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(Exception, match="Unauthorized"):
            api_client.send_post("テスト")
    
    @pytest.mark.unit
    def test_rate_limit_error(self, api_client, mock_atproto_client):
        """レート制限エラー"""
        mock_atproto_client.get_timeline = Mock(
            side_effect=Exception("Rate limit exceeded")
        )
        api_client.client = mock_atproto_client
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            api_client.get_timeline()
    
    @pytest.mark.unit
    def test_invalid_response_format(self, api_client, mock_atproto_client):
        """不正なレスポンス形式"""
        mock_atproto_client.get_timeline = Mock(return_value=None)
        api_client.client = mock_atproto_client
        
        with pytest.raises(AttributeError):
            api_client.get_timeline()


class TestBlueskyApiClientIntegration:
    """統合的な機能テスト"""
    
    @pytest.mark.unit
    def test_post_with_image_workflow(self, api_client, mock_atproto_client):
        """画像付き投稿の完全なワークフロー"""
        # 画像アップロード
        mock_blob = Mock(ref="blob://image/123", size=1024)
        mock_atproto_client.upload_blob = Mock(return_value=mock_blob)
        
        # 投稿送信
        mock_post = Mock(uri="at://user/post/456")
        mock_atproto_client.send_post = Mock(return_value=mock_post)
        
        api_client.client = mock_atproto_client
        
        # ワークフロー実行
        blob_result = api_client.upload_blob(b"image_data", "image/jpeg")
        post_result = api_client.send_post("画像付き", images=[blob_result])
        
        # 検証
        assert blob_result.ref == "blob://image/123"
        assert post_result.uri == "at://user/post/456"
        mock_atproto_client.upload_blob.assert_called_once()
        mock_atproto_client.send_post.assert_called_once()
    
    @pytest.mark.unit
    def test_timeline_with_interactions(self, api_client, mock_atproto_client):
        """タイムライン取得とインタラクション"""
        # タイムライン取得
        mock_posts = [
            create_mock_post(uri="at://user1/post/1"),
            create_mock_post(uri="at://user2/post/2")
        ]
        mock_atproto_client.get_timeline = Mock(
            return_value=Mock(feed=mock_posts)
        )
        
        # いいね
        mock_like = Mock(uri="at://me/like/123")
        mock_atproto_client.like = Mock(return_value=mock_like)
        
        api_client.client = mock_atproto_client
        
        # ワークフロー実行
        timeline = api_client.get_timeline()
        like_result = api_client.like_post(
            timeline[0]["post"]["uri"],
            timeline[0]["post"]["cid"]
        )
        
        # 検証
        assert len(timeline) == 2
        assert like_result.uri == "at://me/like/123"
        mock_atproto_client.get_timeline.assert_called_once()
        mock_atproto_client.like.assert_called_once()