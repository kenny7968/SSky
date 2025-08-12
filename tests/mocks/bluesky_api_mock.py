#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
Bluesky API モッククラス

テスト用のBluesky API応答をシミュレートするモッククラス群
"""

import json
import time
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Union
from unittest.mock import MagicMock, Mock
from atproto_client.exceptions import AtProtocolError


class BlueskyApiMockData:
    """Bluesky API モックデータ生成クラス"""
    
    @staticmethod
    def generate_user_profile(handle: str, display_name: str = None, **kwargs) -> Dict[str, Any]:
        """ユーザープロフィール生成"""
        return {
            "did": f"did:plc:{handle.replace('.', '').replace('-', '')}123",
            "handle": handle,
            "displayName": display_name or f"テストユーザー {handle}",
            "description": kwargs.get("description", f"{handle}のテストプロフィール"),
            "avatar": kwargs.get("avatar", f"https://example.com/avatar/{handle}.jpg"),
            "banner": kwargs.get("banner"),
            "followersCount": kwargs.get("followers_count", random.randint(10, 1000)),
            "followsCount": kwargs.get("follows_count", random.randint(5, 500)),
            "postsCount": kwargs.get("posts_count", random.randint(1, 100)),
            "createdAt": kwargs.get("created_at", "2023-01-01T00:00:00.000Z"),
            "labels": kwargs.get("labels", [])
        }
    
    @staticmethod
    def generate_post(author_handle: str, text: str, **kwargs) -> Dict[str, Any]:
        """投稿データ生成"""
        post_id = kwargs.get("post_id", f"post{random.randint(1000, 9999)}")
        created_time = kwargs.get("created_at") or (
            datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 1440))
        ).isoformat()
        
        post = {
            "uri": f"at://{author_handle}/app.bsky.feed.post/{post_id}",
            "cid": f"cid_{post_id}",
            "author": BlueskyApiMockData.generate_user_profile(author_handle),
            "record": {
                "text": text,
                "createdAt": created_time,
                "langs": kwargs.get("langs", ["ja"])
            },
            "indexedAt": created_time,
            "replyCount": kwargs.get("reply_count", random.randint(0, 50)),
            "repostCount": kwargs.get("repost_count", random.randint(0, 100)),
            "likeCount": kwargs.get("like_count", random.randint(0, 200))
        }
        
        # メディア添付
        if kwargs.get("include_images"):
            post["record"]["embed"] = {
                "type": "app.bsky.embed.images",
                "images": [
                    {
                        "alt": f"画像{i+1}",
                        "ref": f"blob_ref_{i}",
                        "mimeType": "image/jpeg"
                    }
                    for i in range(kwargs.get("image_count", 1))
                ]
            }
        
        # リプライ情報
        if kwargs.get("is_reply"):
            parent_uri = kwargs.get("parent_uri", f"at://{author_handle}/app.bsky.feed.post/parent123")
            post["record"]["reply"] = {
                "root": {"uri": parent_uri, "cid": "parent_cid"},
                "parent": {"uri": parent_uri, "cid": "parent_cid"}
            }
        
        return post
    
    @staticmethod
    def generate_timeline(post_count: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """タイムラインデータ生成"""
        posts = []
        test_users = kwargs.get("test_users", [
            "alice.test", "bob.test", "charlie.test", "diana.test", "eve.test"
        ])
        
        for i in range(post_count):
            author = random.choice(test_users)
            text_variations = [
                f"テスト投稿 {i+1} です",
                f"今日の天気はいいですね #{i+1}",
                f"プログラミング楽しい！ #coding #{i+1}",
                f"おはようございます 🌅 #{i+1}",
                f"今度の休日は何をしようかな #{i+1}",
                f"新機能をテスト中です #{i+1} #開発"
            ]
            
            text = random.choice(text_variations)
            
            post = BlueskyApiMockData.generate_post(
                author_handle=author,
                text=text,
                post_id=f"timeline_{i:04d}",
                include_images=random.random() < 0.3,  # 30%の確率で画像付き
                is_reply=random.random() < 0.2,  # 20%の確率でリプライ
                **kwargs
            )
            
            posts.append(post)
        
        return posts
    
    @staticmethod
    def generate_error_response(error_type: str, message: str = None) -> AtProtocolError:
        """エラーレスポンス生成"""
        error_messages = {
            "invalid_credentials": "Invalid identifier or password",
            "rate_limit": "Rate limit exceeded. Try again later",
            "network_error": "Network connection failed",
            "server_error": "Internal server error",
            "not_found": "Resource not found",
            "forbidden": "Access forbidden",
            "invalid_request": "Invalid request parameters"
        }
        
        error_message = message or error_messages.get(error_type, "Unknown error")
        return AtProtocolError(error_message)


class BlueskyApiClientMock:
    """Bluesky API クライアント モック"""
    
    def __init__(self, **config):
        self.config = config
        self.is_logged_in = False
        self.current_user = None
        self.response_delay = config.get("response_delay", 0.0)
        self.error_rate = config.get("error_rate", 0.0)
        self.network_issues = config.get("simulate_network_issues", False)
        
        # 設定可能な応答データ
        self.mock_timeline = BlueskyApiMockData.generate_timeline(
            config.get("timeline_size", 20)
        )
        self.mock_users = {}
        self.mock_posts = {}
        
        # カウンター（テスト検証用）
        self.call_count = {
            "login": 0,
            "get_timeline": 0,
            "send_post": 0,
            "get_profile": 0,
            "upload_blob": 0
        }
    
    def _simulate_network_delay(self):
        """ネットワーク遅延シミュレーション"""
        if self.response_delay > 0:
            time.sleep(self.response_delay)
    
    def _check_error_simulation(self, operation: str):
        """エラーシミュレーション"""
        if self.network_issues and random.random() < 0.1:
            raise BlueskyApiMockData.generate_error_response("network_error")
        
        if random.random() < self.error_rate:
            error_types = ["server_error", "rate_limit", "invalid_request"]
            error_type = random.choice(error_types)
            raise BlueskyApiMockData.generate_error_response(error_type)
    
    def login(self, identifier: str, password: str) -> bool:
        """ログインモック"""
        self.call_count["login"] += 1
        self._simulate_network_delay()
        self._check_error_simulation("login")
        
        # 無効な認証情報の場合
        if identifier == "invalid.user" or password == "wrong_password":
            raise BlueskyApiMockData.generate_error_response("invalid_credentials")
        
        # 正常ログイン
        self.is_logged_in = True
        self.current_user = BlueskyApiMockData.generate_user_profile(
            handle=identifier,
            display_name=f"モックユーザー {identifier}"
        )
        
        return True
    
    def logout(self) -> bool:
        """ログアウトモック"""
        self.is_logged_in = False
        self.current_user = None
        return True
    
    def get_timeline(self, limit: int = 50, cursor: str = None) -> Mock:
        """タイムライン取得モック"""
        self.call_count["get_timeline"] += 1
        self._simulate_network_delay()
        self._check_error_simulation("get_timeline")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        # カーソル処理のシミュレーション
        start_index = 0
        if cursor:
            try:
                start_index = int(cursor)
            except ValueError:
                start_index = 0
        
        end_index = min(start_index + limit, len(self.mock_timeline))
        feed_posts = self.mock_timeline[start_index:end_index]
        
        # 次のカーソル
        next_cursor = str(end_index) if end_index < len(self.mock_timeline) else None
        
        response = Mock()
        response.feed = feed_posts
        response.cursor = next_cursor
        
        return response
    
    def send_post(self, text: str, images: List[Dict] = None, reply_to: str = None) -> Mock:
        """投稿送信モック"""
        self.call_count["send_post"] += 1
        self._simulate_network_delay()
        self._check_error_simulation("send_post")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        if len(text) > 280:
            raise BlueskyApiMockData.generate_error_response("invalid_request", "Text too long")
        
        # 新規投稿を生成
        post_id = f"mock_{int(time.time())}_{random.randint(100, 999)}"
        new_post = BlueskyApiMockData.generate_post(
            author_handle=self.current_user["handle"],
            text=text,
            post_id=post_id,
            include_images=bool(images),
            image_count=len(images) if images else 0,
            is_reply=bool(reply_to),
            parent_uri=reply_to
        )
        
        # モックタイムラインに追加
        self.mock_timeline.insert(0, new_post)
        self.mock_posts[new_post["uri"]] = new_post
        
        response = Mock()
        response.uri = new_post["uri"]
        response.cid = new_post["cid"]
        
        return response
    
    def get_profile(self, handle: str = None) -> Dict[str, Any]:
        """プロフィール取得モック"""
        self.call_count["get_profile"] += 1
        self._simulate_network_delay()
        self._check_error_simulation("get_profile")
        
        target_handle = handle or (self.current_user["handle"] if self.current_user else None)
        
        if not target_handle:
            raise BlueskyApiMockData.generate_error_response("invalid_request", "No handle specified")
        
        # 既存ユーザーまたは新規生成
        if target_handle in self.mock_users:
            return self.mock_users[target_handle]
        elif target_handle == "nonexistent.user":
            raise BlueskyApiMockData.generate_error_response("not_found", "User not found")
        else:
            profile = BlueskyApiMockData.generate_user_profile(target_handle)
            self.mock_users[target_handle] = profile
            return profile
    
    def upload_blob(self, data: bytes, mime_type: str = None) -> Mock:
        """ファイルアップロードモック"""
        self.call_count["upload_blob"] += 1
        self._simulate_network_delay()
        self._check_error_simulation("upload_blob")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        if not data:
            raise BlueskyApiMockData.generate_error_response("invalid_request", "No data provided")
        
        # ファイルサイズ制限チェック
        if len(data) > 1024 * 1024:  # 1MB制限
            raise BlueskyApiMockData.generate_error_response("invalid_request", "File too large")
        
        blob_ref = f"blob_{int(time.time())}_{random.randint(100, 999)}"
        
        response = Mock()
        response.ref = blob_ref
        response.mimeType = mime_type or "application/octet-stream"
        response.size = len(data)
        
        return response
    
    def follow_user(self, handle: str) -> Mock:
        """フォローモック"""
        self._simulate_network_delay()
        self._check_error_simulation("follow")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        response = Mock()
        response.uri = f"at://{self.current_user['handle']}/app.bsky.graph.follow/follow_{handle}"
        response.success = True
        
        return response
    
    def block_user(self, handle: str) -> Mock:
        """ブロックモック"""
        self._simulate_network_delay()
        self._check_error_simulation("block")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        response = Mock()
        response.uri = f"at://{self.current_user['handle']}/app.bsky.graph.block/block_{handle}"
        response.success = True
        
        return response
    
    def search_users(self, query: str, limit: int = 25) -> Mock:
        """ユーザー検索モック"""
        self._simulate_network_delay()
        self._check_error_simulation("search")
        
        if not query:
            raise BlueskyApiMockData.generate_error_response("invalid_request", "Empty query")
        
        # 検索結果を生成
        search_results = []
        for i in range(min(limit, 10)):  # 最大10件
            handle = f"{query.lower()}.user{i+1}"
            profile = BlueskyApiMockData.generate_user_profile(
                handle=handle,
                display_name=f"{query} ユーザー {i+1}"
            )
            search_results.append(profile)
        
        response = Mock()
        response.actors = search_results
        
        return response
    
    def get_post(self, uri: str) -> Dict[str, Any]:
        """投稿詳細取得モック"""
        self._simulate_network_delay()
        self._check_error_simulation("get_post")
        
        if uri in self.mock_posts:
            return self.mock_posts[uri]
        else:
            raise BlueskyApiMockData.generate_error_response("not_found", "Post not found")
    
    def delete_post(self, uri: str) -> Mock:
        """投稿削除モック"""
        self._simulate_network_delay()
        self._check_error_simulation("delete_post")
        
        if not self.is_logged_in:
            raise BlueskyApiMockData.generate_error_response("forbidden", "Not logged in")
        
        if uri in self.mock_posts:
            del self.mock_posts[uri]
            # タイムラインからも削除
            self.mock_timeline = [p for p in self.mock_timeline if p["uri"] != uri]
        
        response = Mock()
        response.success = True
        
        return response
    
    def reset_mock_data(self):
        """モックデータリセット"""
        self.mock_timeline = BlueskyApiMockData.generate_timeline(
            self.config.get("timeline_size", 20)
        )
        self.mock_users.clear()
        self.mock_posts.clear()
        self.call_count = {key: 0 for key in self.call_count}
    
    def set_mock_timeline(self, posts: List[Dict[str, Any]]):
        """カスタムタイムライン設定"""
        self.mock_timeline = posts.copy()
    
    def add_mock_user(self, handle: str, profile_data: Dict[str, Any]):
        """モックユーザー追加"""
        self.mock_users[handle] = profile_data
    
    def get_call_count(self, operation: str) -> int:
        """API呼び出し回数取得"""
        return self.call_count.get(operation, 0)
    
    def get_total_calls(self) -> int:
        """総API呼び出し回数"""
        return sum(self.call_count.values())