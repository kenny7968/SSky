#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
時間フォーマットユーティリティのテスト
"""

import unittest
from datetime import datetime, timezone, timedelta
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.time_format import format_relative_time

class TestTimeFormat(unittest.TestCase):
    """時間フォーマットユーティリティのテストクラス"""
    
    def test_format_just_now(self):
        """たった今の時間フォーマットのテスト"""
        # 現在時刻
        now = datetime.now(timezone.utc)
        
        # テスト実行
        result = format_relative_time(now)
        
        # 結果の確認
        self.assertEqual(result, "たった今")
        
    def test_format_minutes_ago(self):
        """数分前の時間フォーマットのテスト"""
        # 現在時刻から10分前
        now = datetime.now(timezone.utc)
        time_10min_ago = now - timedelta(minutes=10)
        
        # テスト実行
        result = format_relative_time(time_10min_ago)
        
        # 結果の確認
        self.assertEqual(result, "10分前")
        
    def test_format_hours_ago(self):
        """数時間前の時間フォーマットのテスト"""
        # 現在時刻から3時間前
        now = datetime.now(timezone.utc)
        time_3hours_ago = now - timedelta(hours=3)
        
        # テスト実行
        result = format_relative_time(time_3hours_ago)
        
        # 結果の確認
        self.assertEqual(result, "3時間前")
        
    def test_format_yesterday(self):
        """昨日の時間フォーマットのテスト"""
        # 現在時刻から1日前
        now = datetime.now(timezone.utc)
        time_yesterday = now - timedelta(days=1)
        
        # テスト実行
        result = format_relative_time(time_yesterday)
        
        # 結果の確認
        self.assertEqual(result, "昨日")
        
    def test_format_days_ago(self):
        """数日前の時間フォーマットのテスト"""
        # 現在時刻から3日前
        now = datetime.now(timezone.utc)
        time_3days_ago = now - timedelta(days=3)
        
        # テスト実行
        result = format_relative_time(time_3days_ago)
        
        # 結果の確認
        self.assertEqual(result, "3日前")
        
    def test_format_iso_string(self):
        """ISO形式の文字列の時間フォーマットのテスト"""
        # 現在時刻から2時間前のISO形式文字列
        now = datetime.now(timezone.utc)
        time_2hours_ago = now - timedelta(hours=2)
        iso_string = time_2hours_ago.isoformat().replace('+00:00', 'Z')
        
        # テスト実行
        result = format_relative_time(iso_string)
        
        # 結果の確認
        self.assertEqual(result, "2時間前")
        
    def test_format_error(self):
        """エラーケースのテスト"""
        # 不正な形式の文字列
        invalid_time = "invalid_time_format"
        
        # テスト実行
        result = format_relative_time(invalid_time)
        
        # 結果の確認
        self.assertEqual(result, "不明")

if __name__ == '__main__':
    unittest.main()
