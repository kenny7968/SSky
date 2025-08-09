#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
テストフィクスチャデータローダー (Phase 2 リファクタリング版)
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_sample_posts() -> List[Dict[str, Any]]:
    """サンプル投稿データを読み込み"""
    fixture_path = Path(__file__).parent / "sample_posts.json"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_sample_users() -> List[Dict[str, Any]]:
    """サンプルユーザーデータを読み込み"""
    fixture_path = Path(__file__).parent / "sample_users.json"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_sample_post_by_handle(handle: str) -> Dict[str, Any]:
    """指定されたハンドルの投稿を取得"""
    posts = load_sample_posts()
    for post in posts:
        if post['author']['handle'] == handle:
            return post
    raise ValueError(f"Post by {handle} not found in sample data")


def get_sample_user_by_handle(handle: str) -> Dict[str, Any]:
    """指定されたハンドルのユーザーを取得"""
    users = load_sample_users()
    for user in users:
        if user['handle'] == handle:
            return user
    raise ValueError(f"User {handle} not found in sample data")


# 便利な定数
SAMPLE_USER_HANDLES = [
    "alice.bsky.social",
    "bob.bsky.social", 
    "charlie.bsky.social",
    "dave.bsky.social",
    "eve.bsky.social",
    "frank.bsky.social",
    "grace.bsky.social",
    "henry.bsky.social",
    "iris.bsky.social",
    "jack.bsky.social"
]

SAMPLE_POST_TYPES = {
    "normal": "alice.bsky.social",
    "with_image": "bob.bsky.social", 
    "reply": "charlie.bsky.social",
    "long_text": "dave.bsky.social",
    "with_url": "eve.bsky.social"
}