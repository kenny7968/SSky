#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
時間フォーマットユーティリティ
"""

import logging
from datetime import datetime, timezone

# ロガーの設定
logger = logging.getLogger(__name__)

def format_relative_time(timestamp):
    """タイムスタンプを表示用の相対時間文字列に変換
    
    Args:
        timestamp: ISO形式の文字列またはdatetimeオブジェクト
        
    Returns:
        str: 「たった今」「10分前」「3時間前」「昨日」などの相対時間文字列
    """
    try:
        # タイムスタンプがUTC時間の場合
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        # 現在時刻との差を計算
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        # 表示形式を決定
        if diff.days > 0:
            if diff.days == 1:
                return "昨日"
            else:
                return f"{diff.days}日前"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}時間前"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}分前"
        else:
            return "たった今"
    except Exception as e:
        logger.error(f"時間フォーマットに失敗しました: {str(e)}")
        return "不明"
