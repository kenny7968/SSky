#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿データファクトリ (Phase 2 リファクタリング版)
"""

import factory
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from faker import Faker
import random

from .user_factory import UserFactory

# 日本語対応のためのFaker設定
fake = Faker(['ja_JP', 'en_US'])


class PostRecordFactory(factory.Factory):
    """投稿レコード（record部分）のファクトリ"""
    
    class Meta:
        model = dict
    
    text = factory.LazyFunction(lambda: fake.text(max_nb_chars=300))
    createdAt = factory.LazyFunction(
        lambda: (datetime.now(timezone.utc) - timedelta(
            hours=random.randint(0, 72),
            minutes=random.randint(0, 59)
        )).isoformat().replace('+00:00', 'Z')
    )
    langs = ["ja"]


class PostFactory(factory.Factory):
    """Bluesky投稿データのファクトリ"""
    
    class Meta:
        model = dict
    
    # 基本属性
    uri = factory.LazyFunction(
        lambda: f"at://{fake.domain_name()}/app.bsky.feed.post/{fake.uuid4()[:8]}"
    )
    cid = factory.LazyFunction(lambda: f"test_cid_{fake.uuid4()[:8]}")
    
    # 投稿者情報
    author = factory.SubFactory(UserFactory)
    
    # 投稿内容
    record = factory.SubFactory(PostRecordFactory)
    
    # メタデータ
    indexedAt = factory.LazyFunction(
        lambda: (datetime.now(timezone.utc) - timedelta(
            minutes=random.randint(0, 30)
        )).isoformat().replace('+00:00', 'Z')
    )
    
    # エンゲージメント統計
    replyCount = factory.LazyFunction(lambda: random.randint(0, 50))
    repostCount = factory.LazyFunction(lambda: random.randint(0, 25))
    likeCount = factory.LazyFunction(lambda: random.randint(0, 100))


class ShortPostFactory(PostFactory):
    """短い投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        text=factory.LazyFunction(lambda: fake.sentence(nb_words=random.randint(3, 10)))
    )


class LongPostFactory(PostFactory):
    """長い投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        text=factory.LazyFunction(
            lambda: f"{fake.text(max_nb_chars=200)}\n\n{fake.text(max_nb_chars=150)}\n\n{fake.sentence()}"
        )
    )


class PopularPostFactory(PostFactory):
    """人気の投稿のファクトリ"""
    
    replyCount = factory.LazyFunction(lambda: random.randint(10, 200))
    repostCount = factory.LazyFunction(lambda: random.randint(5, 100))
    likeCount = factory.LazyFunction(lambda: random.randint(50, 1000))


class ReplyPostFactory(PostFactory):
    """リプライ投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        reply=factory.LazyFunction(
            lambda: {
                'root': {
                    'uri': f"at://{fake.domain_name()}/app.bsky.feed.post/{fake.uuid4()[:8]}",
                    'cid': f"root_cid_{fake.uuid4()[:8]}"
                },
                'parent': {
                    'uri': f"at://{fake.domain_name()}/app.bsky.feed.post/{fake.uuid4()[:8]}",
                    'cid': f"parent_cid_{fake.uuid4()[:8]}"
                }
            }
        )
    )


class ImagePostFactory(PostFactory):
    """画像付き投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        embed=factory.LazyFunction(
            lambda: {
                '$type': 'app.bsky.embed.images',
                'images': [
                    {
                        'alt': fake.sentence(nb_words=random.randint(2, 8)),
                        'image': {
                            'ref': f"test_image_blob_{fake.uuid4()[:8]}",
                            'mimeType': random.choice(['image/jpeg', 'image/png', 'image/gif']),
                            'size': random.randint(50000, 2000000)
                        }
                    } for _ in range(random.randint(1, 4))
                ]
            }
        )
    )


class UrlPostFactory(PostFactory):
    """URL付き投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        text=factory.LazyFunction(
            lambda: f"{fake.text(max_nb_chars=100)} {fake.url()} {fake.sentence()}"
        )
    )


class HashtagPostFactory(PostFactory):
    """ハッシュタグ付き投稿のファクトリ"""
    
    record = factory.SubFactory(
        PostRecordFactory,
        text=factory.LazyFunction(
            lambda: f"{fake.text(max_nb_chars=150)}\n\n#{fake.word()} #{fake.word()} #{fake.word()}"
        )
    )


class TestPostFactory(PostFactory):
    """テスト用の固定データを持つ投稿ファクトリ"""
    
    uri = "at://test.bsky.social/app.bsky.feed.post/testpost123"
    cid = "test_cid_fixed"
    
    author = factory.SubFactory(
        UserFactory,
        did="did:plc:testuser123",
        handle="testuser.bsky.social",
        displayName="Test User"
    )
    
    record = factory.SubFactory(
        PostRecordFactory,
        text="これはテスト用の固定投稿です",
        createdAt="2024-01-01T12:00:00.000Z"
    )
    
    indexedAt = "2024-01-01T12:00:01.000Z"
    replyCount = 5
    repostCount = 3
    likeCount = 12


class TimelineFactory:
    """タイムラインデータのファクトリ"""
    
    @staticmethod
    def create_timeline(
        count: int = 20,
        post_types: Optional[List[str]] = None,
        time_range_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """多様なタイプの投稿を含むタイムラインを生成"""
        
        if post_types is None:
            post_types = ['normal', 'short', 'long', 'popular', 'reply', 'image', 'url', 'hashtag']
        
        factory_map = {
            'normal': PostFactory,
            'short': ShortPostFactory,
            'long': LongPostFactory,
            'popular': PopularPostFactory,
            'reply': ReplyPostFactory,
            'image': ImagePostFactory,
            'url': UrlPostFactory,
            'hashtag': HashtagPostFactory
        }
        
        posts = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(count):
            post_type = random.choice(post_types)
            factory_class = factory_map.get(post_type, PostFactory)
            
            # 時系列順に並ぶように時間を調整
            post_time = base_time - timedelta(
                hours=random.uniform(0, time_range_hours),
                minutes=random.randint(0, 59)
            )
            
            post = factory_class()
            post['record']['createdAt'] = post_time.isoformat().replace('+00:00', 'Z')
            post['indexedAt'] = (post_time + timedelta(seconds=random.randint(1, 60))).isoformat().replace('+00:00', 'Z')
            
            posts.append(post)
        
        # 作成時間順にソート（新しいものが最初）
        posts.sort(key=lambda p: p['record']['createdAt'], reverse=True)
        
        return posts
    
    @staticmethod
    def create_user_timeline(user_data: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """特定ユーザーのタイムラインを生成"""
        posts = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(count):
            post_time = base_time - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            post = PostFactory()
            post['author'] = user_data
            post['uri'] = f"at://{user_data['handle']}/app.bsky.feed.post/{fake.uuid4()[:8]}"
            post['record']['createdAt'] = post_time.isoformat().replace('+00:00', 'Z')
            post['indexedAt'] = (post_time + timedelta(seconds=random.randint(1, 60))).isoformat().replace('+00:00', 'Z')
            
            posts.append(post)
        
        # 作成時間順にソート
        posts.sort(key=lambda p: p['record']['createdAt'], reverse=True)
        
        return posts
    
    @staticmethod
    def create_conversation_thread(root_post: Dict[str, Any], reply_count: int = 5) -> List[Dict[str, Any]]:
        """会話スレッドを生成"""
        thread = [root_post]
        parent_post = root_post
        
        for i in range(reply_count):
            reply_time = datetime.fromisoformat(
                parent_post['record']['createdAt'].replace('Z', '+00:00')
            ) + timedelta(minutes=random.randint(1, 120))
            
            reply = ReplyPostFactory()
            reply['record']['reply'] = {
                'root': {
                    'uri': root_post['uri'],
                    'cid': root_post['cid']
                },
                'parent': {
                    'uri': parent_post['uri'],
                    'cid': parent_post['cid']
                }
            }
            reply['record']['createdAt'] = reply_time.isoformat().replace('+00:00', 'Z')
            reply['indexedAt'] = (reply_time + timedelta(seconds=random.randint(1, 60))).isoformat().replace('+00:00', 'Z')
            
            thread.append(reply)
            parent_post = reply
        
        return thread


# 便利な生成関数
def create_mixed_timeline(count: int = 50) -> List[Dict[str, Any]]:
    """多様なコンテンツを含む混合タイムラインを生成"""
    return TimelineFactory.create_timeline(
        count=count,
        post_types=['normal', 'short', 'long', 'popular', 'reply', 'image', 'url', 'hashtag'],
        time_range_hours=48
    )


def create_test_post_set() -> Dict[str, Dict[str, Any]]:
    """テスト用の固定投稿セットを生成"""
    return {
        'simple': TestPostFactory(),
        'long': LongPostFactory(
            uri="at://test.bsky.social/app.bsky.feed.post/longpost123",
            cid="test_cid_long"
        ),
        'image': ImagePostFactory(
            uri="at://test.bsky.social/app.bsky.feed.post/imagepost123",
            cid="test_cid_image"
        ),
        'reply': ReplyPostFactory(
            uri="at://test.bsky.social/app.bsky.feed.post/replypost123",
            cid="test_cid_reply"
        ),
        'popular': PopularPostFactory(
            uri="at://test.bsky.social/app.bsky.feed.post/popularpost123",
            cid="test_cid_popular"
        )
    }