#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ダミーデータ生成モジュール
"""

import random
from datetime import datetime, timedelta

# ダミーユーザー名のリスト
USERNAMES = [
    "青空太郎", "雲子", "晴れ男", "雨美", "虹子", "風太", "雪乃", "霧島", "星野", "月野",
    "太陽子", "天気予報士", "気象庁", "台風一郎", "雷神", "霜降り", "霞", "朝焼け", "夕焼け", "流星"
]

# ダミーハンドル名のリスト
HANDLES = [
    "@aozora", "@kumoko", "@hareo", "@amemi", "@nijiko", "@kazeta", "@yukino", "@kirishima", "@hoshino", "@tsukino",
    "@taiyoko", "@weatherman", "@jma", "@typhoon1", "@raijin", "@shimofuri", "@kasumi", "@asayake", "@yuyake", "@meteor"
]

# ダミー投稿内容のテンプレート
POST_TEMPLATES = [
    "今日の空は{}です。気分も{}！",
    "{}を見ながら{}について考えていました。",
    "今日は{}へ行ってきました。{}が印象的でした。",
    "{}が好きな人は{}もきっと好きだと思う。",
    "{}って実は{}だったんですね。知りませんでした。",
    "今日の{}は最高！{}な一日になりそう。",
    "{}について調べていたら、{}ということがわかりました。興味深い！",
    "{}を試してみたけど、{}かも。みなさんどう思いますか？",
    "{}の季節になりましたね。{}が恋しくなります。",
    "新しい{}を手に入れました！{}が特徴です。"
]

# 形容詞リスト
ADJECTIVES = [
    "美しい", "素晴らしい", "楽しい", "面白い", "不思議な", "驚くべき", "感動的な", "心地よい", "爽やかな", "穏やかな",
    "激しい", "静かな", "明るい", "暗い", "鮮やかな", "淡い", "強い", "弱い", "優しい", "厳しい"
]

# 名詞リスト
NOUNS = [
    "空", "雲", "太陽", "月", "星", "風", "雨", "雪", "霧", "虹",
    "海", "山", "川", "森", "花", "木", "鳥", "魚", "猫", "犬",
    "音楽", "映画", "本", "絵", "写真", "料理", "旅行", "散歩", "会話", "思い出"
]

def generate_dummy_posts(count=20):
    """ダミー投稿データを生成する
    
    Args:
        count (int): 生成する投稿数
        
    Returns:
        list: 投稿データのリスト
    """
    posts = []
    now = datetime.now()
    
    for i in range(count):
        # ランダムなユーザー情報
        user_index = random.randint(0, len(USERNAMES) - 1)
        username = USERNAMES[user_index]
        handle = HANDLES[user_index]
        
        # ランダムな投稿内容
        template = random.choice(POST_TEMPLATES)
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        content = template.format(adj, noun)
        
        # ランダムな投稿時間（過去24時間以内）
        minutes_ago = random.randint(0, 24 * 60)
        post_time = now - timedelta(minutes=minutes_ago)
        
        # 時間表示のフォーマット
        if minutes_ago < 60:
            time_str = f"{minutes_ago}分前"
        elif minutes_ago < 24 * 60:
            hours_ago = minutes_ago // 60
            time_str = f"{hours_ago}時間前"
        else:
            time_str = "昨日"
        
        # 投稿データ
        post = {
            'username': username,
            'handle': handle,
            'content': content,
            'time': time_str,
            'likes': random.randint(0, 100),
            'replies': random.randint(0, 20),
            'reposts': random.randint(0, 10)
        }
        
        posts.append(post)
    
    # 投稿時間の新しい順にソート
    posts.sort(key=lambda x: x['time'])
    
    return posts
