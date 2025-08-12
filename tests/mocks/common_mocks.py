#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - 共通モックユーティリティ
テスト全体で再利用可能なモック定義
"""

from unittest.mock import Mock, MagicMock, PropertyMock
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class MockBlueskyApiClient:
    """BlueskyApiClientのモック"""
    
    def __init__(self):
        self.client = Mock()
        self._setup_default_responses()
    
    def _setup_default_responses(self):
        """デフォルトのレスポンスを設定"""
        # タイムライン取得
        self.client.get_timeline = Mock(return_value=self._get_default_timeline())
        
        # 投稿送信
        self.client.send_post = Mock(return_value={
            "uri": "at://test.user/app.bsky.feed.post/123",
            "cid": "test_cid_123"
        })
        
        # ユーザー情報取得
        self.client.get_user_info = Mock(return_value=self._get_default_user())
        
        # ブロブアップロード
        self.client.upload_blob = Mock(return_value={
            "ref": "test_blob_ref",
            "mimeType": "image/jpeg",
            "size": 1024
        })
        
        # 削除
        self.client.delete_post = Mock(return_value=True)
        
        # いいね
        self.client.like_post = Mock(return_value={
            "uri": "at://test.user/app.bsky.feed.like/456"
        })
        
        # リポスト
        self.client.repost = Mock(return_value={
            "uri": "at://test.user/app.bsky.feed.repost/789"
        })
    
    def _get_default_timeline(self) -> List[Dict[str, Any]]:
        """デフォルトのタイムラインデータ"""
        return [
            {
                "post": {
                    "uri": "at://alice.bsky.social/app.bsky.feed.post/1",
                    "cid": "cid_1",
                    "author": {
                        "did": "did:plc:alice",
                        "handle": "alice.bsky.social",
                        "displayName": "Alice",
                        "avatar": "https://example.com/alice.jpg"
                    },
                    "record": {
                        "text": "テスト投稿1",
                        "createdAt": "2024-01-01T12:00:00.000Z"
                    },
                    "replyCount": 5,
                    "repostCount": 10,
                    "likeCount": 20,
                    "indexedAt": "2024-01-01T12:00:01.000Z"
                }
            },
            {
                "post": {
                    "uri": "at://bob.bsky.social/app.bsky.feed.post/2",
                    "cid": "cid_2",
                    "author": {
                        "did": "did:plc:bob",
                        "handle": "bob.bsky.social",
                        "displayName": "Bob"
                    },
                    "record": {
                        "text": "テスト投稿2",
                        "createdAt": "2024-01-01T11:00:00.000Z"
                    },
                    "replyCount": 2,
                    "repostCount": 5,
                    "likeCount": 15,
                    "indexedAt": "2024-01-01T11:00:01.000Z"
                }
            }
        ]
    
    def _get_default_user(self) -> Dict[str, Any]:
        """デフォルトのユーザー情報"""
        return {
            "did": "did:plc:testuser",
            "handle": "test.bsky.social",
            "displayName": "Test User",
            "description": "テストユーザーです",
            "avatar": "https://example.com/avatar.jpg",
            "banner": "https://example.com/banner.jpg",
            "followersCount": 100,
            "followsCount": 50,
            "postsCount": 200,
            "indexedAt": "2024-01-01T00:00:00.000Z"
        }
    
    def set_timeline_response(self, timeline_data: List[Dict[str, Any]]):
        """タイムラインレスポンスをカスタマイズ"""
        self.client.get_timeline.return_value = timeline_data
    
    def set_error_response(self, method_name: str, exception: Exception):
        """エラーレスポンスを設定"""
        getattr(self.client, method_name).side_effect = exception
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.client


class MockSessionManager:
    """SessionManagerのモック"""
    
    def __init__(self, logged_in: bool = True):
        self.manager = Mock()
        self.logged_in = logged_in
        self._setup_default_behavior()
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.manager.is_logged_in = Mock(return_value=self.logged_in)
        self.manager.get_session = Mock(return_value={
            "accessJwt": "test_access_token",
            "refreshJwt": "test_refresh_token",
            "handle": "test.user",
            "did": "did:plc:testuser"
        } if self.logged_in else None)
        
        self.manager.login = Mock(return_value=self.logged_in)
        self.manager.logout = Mock()
        self.manager.refresh_session = Mock(return_value=self.logged_in)
    
    def set_logged_in(self, logged_in: bool):
        """ログイン状態を設定"""
        self.logged_in = logged_in
        self.manager.is_logged_in.return_value = logged_in
        if not logged_in:
            self.manager.get_session.return_value = None
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.manager


class MockCredentialManager:
    """CredentialManagerのモック"""
    
    def __init__(self, has_credentials: bool = True):
        self.manager = Mock()
        self.has_credentials = has_credentials
        self._setup_default_behavior()
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.manager.get_credentials = Mock(return_value={
            "identifier": "test.user",
            "password": "encrypted_password"
        } if self.has_credentials else None)
        
        self.manager.save_credentials = Mock(return_value=True)
        self.manager.delete_credentials = Mock(return_value=True)
        self.manager.has_saved_credentials = Mock(return_value=self.has_credentials)
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.manager


class MockDataStore:
    """DataStoreのモック"""
    
    def __init__(self):
        self.store = Mock()
        self._data = {}
        self._setup_default_behavior()
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.store.save_post = Mock(side_effect=self._save_post)
        self.store.get_posts = Mock(side_effect=self._get_posts)
        self.store.delete_post = Mock(side_effect=self._delete_post)
        self.store.clear_posts = Mock(side_effect=self._clear_posts)
        self.store.get_post_count = Mock(side_effect=self._get_post_count)
    
    def _save_post(self, post_data: Dict[str, Any]):
        """投稿を保存"""
        uri = post_data.get("uri", f"test://post/{len(self._data)}")
        self._data[uri] = post_data
        return True
    
    def _get_posts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """投稿を取得"""
        posts = list(self._data.values())
        return posts[:limit]
    
    def _delete_post(self, uri: str) -> bool:
        """投稿を削除"""
        if uri in self._data:
            del self._data[uri]
            return True
        return False
    
    def _clear_posts(self):
        """全投稿をクリア"""
        self._data.clear()
    
    def _get_post_count(self) -> int:
        """投稿数を取得"""
        return len(self._data)
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.store


class MockSettingsManager:
    """SettingsManagerのモック"""
    
    def __init__(self):
        self.manager = Mock()
        self._settings = self._get_default_settings()
        self._setup_default_behavior()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "timeline_refresh_interval": 30,
            "max_posts_display": 100,
            "enable_notifications": True,
            "theme": "default",
            "language": "ja",
            "font_size": 12,
            "auto_login": True
        }
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.manager.get = Mock(side_effect=self._get_setting)
        self.manager.set = Mock(side_effect=self._set_setting)
        self.manager.get_all = Mock(return_value=self._settings.copy())
        self.manager.reset = Mock(side_effect=self._reset_settings)
        self.manager.save = Mock(return_value=True)
        self.manager.load = Mock(return_value=True)
    
    def _get_setting(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self._settings.get(key, default)
    
    def _set_setting(self, key: str, value: Any):
        """設定値を設定"""
        self._settings[key] = value
    
    def _reset_settings(self):
        """設定をリセット"""
        self._settings = self._get_default_settings()
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.manager


class MockWxApp:
    """wxPython Appのモック"""
    
    def __init__(self):
        self.app = Mock()
        self._setup_default_behavior()
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.app.MainLoop = Mock()
        self.app.ExitMainLoop = Mock()
        self.app.GetTopWindow = Mock(return_value=Mock())
        self.app.SetTopWindow = Mock()
        self.app.ProcessPendingEvents = Mock()
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.app


class MockWxFrame:
    """wxPython Frameのモック"""
    
    def __init__(self, title: str = "Test Frame"):
        self.frame = Mock()
        self.title = title
        self._setup_default_behavior()
    
    def _setup_default_behavior(self):
        """デフォルトの動作を設定"""
        self.frame.SetTitle = Mock()
        self.frame.GetTitle = Mock(return_value=self.title)
        self.frame.Show = Mock()
        self.frame.Hide = Mock()
        self.frame.Close = Mock()
        self.frame.Destroy = Mock()
        self.frame.SetMenuBar = Mock()
        self.frame.CreateStatusBar = Mock(return_value=Mock())
        self.frame.SetStatusText = Mock()
        self.frame.Refresh = Mock()
        self.frame.Update = Mock()
    
    def get_mock(self) -> Mock:
        """モックインスタンスを取得"""
        return self.frame


def create_mock_post(
    uri: str = "at://test/post/1",
    text: str = "テスト投稿",
    author_handle: str = "test.user",
    author_name: str = "Test User",
    created_at: Optional[datetime] = None,
    like_count: int = 0,
    repost_count: int = 0,
    reply_count: int = 0
) -> Dict[str, Any]:
    """モック投稿データを作成"""
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    
    return {
        "post": {
            "uri": uri,
            "cid": f"cid_{uri.split('/')[-1]}",
            "author": {
                "did": f"did:plc:{author_handle.replace('.', '')}",
                "handle": author_handle,
                "displayName": author_name
            },
            "record": {
                "text": text,
                "createdAt": created_at.isoformat()
            },
            "replyCount": reply_count,
            "repostCount": repost_count,
            "likeCount": like_count,
            "indexedAt": created_at.isoformat()
        }
    }


def create_mock_user(
    handle: str = "test.user",
    display_name: str = "Test User",
    description: str = "テストユーザー",
    followers: int = 100,
    following: int = 50,
    posts: int = 200
) -> Dict[str, Any]:
    """モックユーザーデータを作成"""
    return {
        "did": f"did:plc:{handle.replace('.', '')}",
        "handle": handle,
        "displayName": display_name,
        "description": description,
        "avatar": f"https://example.com/{handle}/avatar.jpg",
        "banner": f"https://example.com/{handle}/banner.jpg",
        "followersCount": followers,
        "followsCount": following,
        "postsCount": posts,
        "indexedAt": datetime.now(timezone.utc).isoformat()
    }