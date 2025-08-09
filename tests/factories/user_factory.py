#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ユーザーデータファクトリ (Phase 2 リファクタリング版)
"""

import factory
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from faker import Faker

# 日本語対応のためのFaker設定
fake = Faker(['ja_JP', 'en_US'])


class UserFactory(factory.Factory):
    """Blueskyユーザーデータのファクトリ"""
    
    class Meta:
        model = dict
    
    # 基本属性
    did = factory.LazyFunction(lambda: f"did:plc:{fake.uuid4().replace('-', '')[:12]}")
    handle = factory.LazyFunction(lambda: f"{fake.user_name().lower()}.bsky.social")
    displayName = factory.LazyFunction(lambda: fake.name())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    
    # プロフィール画像
    avatar = factory.LazyFunction(lambda: f"https://example.com/avatars/{fake.uuid4()}.jpg")
    banner = factory.LazyFunction(lambda: f"https://example.com/banners/{fake.uuid4()}.jpg" if fake.boolean(chance_of_getting_true=70) else None)
    
    # 統計情報
    followersCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=10000))
    followsCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=5000))
    postsCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=2000))
    
    # メタデータ
    indexedAt = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    labels = factory.LazyFunction(lambda: [])


class UserProfileFactory(UserFactory):
    """詳細なプロフィール情報を持つユーザーファクトリ"""
    
    # より詳細な説明文
    description = factory.LazyFunction(
        lambda: f"{fake.text(max_nb_chars=100)}\n\n{fake.sentence()}\n\n#{fake.word()} #{fake.word()}"
    )
    
    # より高いフォロワー数
    followersCount = factory.LazyFunction(lambda: fake.random_int(min=100, max=50000))
    followsCount = factory.LazyFunction(lambda: fake.random_int(min=50, max=10000))
    postsCount = factory.LazyFunction(lambda: fake.random_int(min=10, max=5000))


class MinimalUserFactory(UserFactory):
    """最小限の情報のみを持つユーザーファクトリ"""
    
    displayName = ""
    description = ""
    avatar = None
    banner = None
    followersCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=50))
    followsCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    postsCount = factory.LazyFunction(lambda: fake.random_int(min=0, max=10))


class TestUserFactory(UserFactory):
    """テスト用の固定データを持つユーザーファクトリ"""
    
    did = "did:plc:testuser123"
    handle = "testuser.bsky.social"
    displayName = "Test User"
    description = "これはテスト用ユーザーです"
    avatar = "https://example.com/test_avatar.jpg"
    banner = "https://example.com/test_banner.jpg"
    followersCount = 100
    followsCount = 50
    postsCount = 25


class PopularUserFactory(UserFactory):
    """人気ユーザーのファクトリ"""
    
    displayName = factory.LazyFunction(lambda: f"{fake.name()} 🔥")
    description = factory.LazyFunction(
        lambda: f"人気クリエイター | {fake.job()}\n\n{fake.text(max_nb_chars=80)}\n\n#人気 #フォロワー {fake.random_int(min=10000, max=100000)}人"
    )
    followersCount = factory.LazyFunction(lambda: fake.random_int(min=10000, max=1000000))
    followsCount = factory.LazyFunction(lambda: fake.random_int(min=500, max=10000))
    postsCount = factory.LazyFunction(lambda: fake.random_int(min=1000, max=50000))
    labels = ["verified", "popular"]


class DeveloperUserFactory(UserFactory):
    """開発者ユーザーのファクトリ"""
    
    displayName = factory.LazyFunction(lambda: f"{fake.first_name()} Dev")
    description = factory.LazyFunction(
        lambda: f"Software Developer | {fake.job()}\n\n{fake.text(max_nb_chars=60)}\n\n#developer #coding #tech"
    )
    labels = ["developer"]


# 便利な生成関数
def create_user_list(count: int = 10, factory_class: type = UserFactory) -> List[Dict[str, Any]]:
    """指定された数のユーザーリストを生成"""
    return [factory_class() for _ in range(count)]


def create_test_user_set() -> Dict[str, Dict[str, Any]]:
    """テスト用の固定ユーザーセットを生成"""
    return {
        'alice': UserFactory(
            did="did:plc:alice123",
            handle="alice.bsky.social",
            displayName="Alice Test",
            description="テストユーザーのアリスです",
            followersCount=150,
            followsCount=85,
            postsCount=42
        ),
        'bob': UserFactory(
            did="did:plc:bob456", 
            handle="bob.bsky.social",
            displayName="Bob Developer",
            description="開発者のボブです\n\n#developer #testing",
            followersCount=320,
            followsCount=180,
            postsCount=128
        ),
        'charlie': MinimalUserFactory(
            did="did:plc:charlie789",
            handle="charlie.bsky.social",
            displayName="Charlie QA"
        ),
        'popular': PopularUserFactory(
            did="did:plc:popular999",
            handle="popular.bsky.social"
        )
    }


def create_follow_relationship(follower: Dict[str, Any], following: Dict[str, Any]) -> Dict[str, Any]:
    """フォロー関係のデータを生成"""
    return {
        'follower': {
            'did': follower['did'],
            'handle': follower['handle'],
            'displayName': follower.get('displayName', '')
        },
        'following': {
            'did': following['did'],
            'handle': following['handle'],
            'displayName': following.get('displayName', '')
        },
        'createdAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }


def create_user_search_results(query: str, count: int = 5) -> List[Dict[str, Any]]:
    """ユーザー検索結果のデータを生成"""
    results = []
    for i in range(count):
        user = UserFactory()
        # 検索クエリをハンドル名や表示名に含める
        if fake.boolean(chance_of_getting_true=60):
            user['handle'] = f"{query.lower()}{fake.random_int(min=1, max=999)}.bsky.social"
        if fake.boolean(chance_of_getting_true=40):
            user['displayName'] = f"{query} {fake.first_name()}"
        results.append(user)
    return results