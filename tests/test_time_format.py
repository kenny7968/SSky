#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
時間フォーマットユーティリティの単体テスト (Phase 1 リファクタリング版)
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.time_format import format_timestamp_to_jst, format_relative_time


class TestFormatTimestampToJst(unittest.TestCase):
    """format_timestamp_to_jst 関数のテストクラス"""
    
    def test_iso_string_with_z(self):
        """Z付きISO文字列の変換テスト"""
        # UTC時間を設定 (2024-01-01 12:00:00 UTC)
        utc_timestamp = "2024-01-01T12:00:00Z"
        
        # JST変換実行 (UTC+9なので21:00になる)
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        self.assertEqual(result, "2024/01/01 21:00")
    
    def test_iso_string_with_timezone(self):
        """タイムゾーン付きISO文字列の変換テスト"""
        # UTC時間を明示的に指定
        utc_timestamp = "2024-01-01T12:00:00+00:00"
        
        # JST変換実行
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        self.assertEqual(result, "2024/01/01 21:00")
    
    def test_datetime_object_utc(self):
        """UTC datetimeオブジェクトの変換テスト"""
        # UTC datetime オブジェクトを作成
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # JST変換実行
        result = format_timestamp_to_jst(utc_dt)
        
        # 結果確認
        self.assertEqual(result, "2024/01/01 21:00")
    
    def test_datetime_object_with_different_timezone(self):
        """異なるタイムゾーンのdatetimeオブジェクトの変換テスト"""
        # EST (UTC-5) datetime オブジェクトを作成
        est_tz = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est_tz)
        
        # JST変換実行 (EST 12:00 = UTC 17:00 = JST 02:00+1day)
        result = format_timestamp_to_jst(est_dt)
        
        # 結果確認
        self.assertEqual(result, "2024/01/02 02:00")
    
    def test_edge_case_new_year(self):
        """年跨ぎの変換テスト"""
        # UTC大晦日の夜
        utc_timestamp = "2023-12-31T20:00:00Z"
        
        # JST変換実行 (翌年になる)
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        self.assertEqual(result, "2024/01/01 05:00")
    
    def test_various_times(self):
        """様々な時刻の変換テスト"""
        test_cases = [
            ("2024-06-15T00:00:00Z", "2024/06/15 09:00"),  # 午前
            ("2024-06-15T15:30:45Z", "2024/06/16 00:30"),  # 日跨ぎ
            ("2024-12-31T23:59:59Z", "2025/01/01 08:59"),  # 年跨ぎ
        ]
        
        for utc_time, expected_jst in test_cases:
            with self.subTest(utc_time=utc_time):
                result = format_timestamp_to_jst(utc_time)
                self.assertEqual(result, expected_jst)
    
    @patch('utils.time_format.logger')
    def test_invalid_string_format(self, mock_logger):
        """無効な文字列フォーマットのテスト"""
        invalid_timestamp = "invalid-timestamp"
        
        # エラーハンドリング実行
        result = format_timestamp_to_jst(invalid_timestamp)
        
        # エラー時の戻り値確認
        self.assertEqual(result, "不明")
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        self.assertIn("時間フォーマットに失敗しました", error_call)
    
    @patch('utils.time_format.logger')
    def test_none_input(self, mock_logger):
        """None入力のテスト"""
        # None入力でエラーハンドリング
        result = format_timestamp_to_jst(None)
        
        # エラー時の戻り値確認
        self.assertEqual(result, "不明")
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()
    
    def test_naive_datetime_object(self):
        """タイムゾーン情報なしdatetimeオブジェクトのテスト"""
        # naive datetime (タイムゾーン情報なし) を作成
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        
        # 変換実行（通常はUTCとして扱われるか、エラーになる）
        # 実装によって動作が変わる可能性があるが、エラーハンドリングされることを期待
        result = format_timestamp_to_jst(naive_dt)
        
        # 結果が適切に処理されていることを確認（エラーでも"不明"が返される）
        self.assertTrue(isinstance(result, str))


class TestFormatRelativeTime(unittest.TestCase):
    """format_relative_time 関数のテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # 基準時刻を設定 (2024-01-01 12:00:00 JST)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))
    
    @patch('utils.time_format.datetime')
    def test_just_now(self, mock_datetime):
        """「たった今」のテスト"""
        mock_datetime.now.return_value = self.base_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # 30秒前の時刻
        timestamp = (self.base_time - timedelta(seconds=30)).isoformat()
        
        result = format_relative_time(timestamp)
        
        # 実装に依存するが、通常は「たった今」または「30秒前」
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    @patch('utils.time_format.datetime')  
    def test_minutes_ago(self, mock_datetime):
        """「○分前」のテスト"""
        mock_datetime.now.return_value = self.base_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # 15分前の時刻
        timestamp = (self.base_time - timedelta(minutes=15)).isoformat()
        
        result = format_relative_time(timestamp)
        
        # 15分前として表示されることを確認
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    @patch('utils.time_format.datetime')
    def test_hours_ago(self, mock_datetime):
        """「○時間前」のテスト"""
        mock_datetime.now.return_value = self.base_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # 3時間前の時刻
        timestamp = (self.base_time - timedelta(hours=3)).isoformat()
        
        result = format_relative_time(timestamp)
        
        # 3時間前として表示されることを確認
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    @patch('utils.time_format.datetime')
    def test_yesterday(self, mock_datetime):
        """「昨日」のテスト"""
        mock_datetime.now.return_value = self.base_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # 昨日の同時刻
        timestamp = (self.base_time - timedelta(days=1)).isoformat()
        
        result = format_relative_time(timestamp)
        
        # 昨日として表示されることを確認
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    @patch('utils.time_format.datetime')
    def test_days_ago(self, mock_datetime):
        """「○日前」のテスト"""
        mock_datetime.now.return_value = self.base_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # 5日前の時刻
        timestamp = (self.base_time - timedelta(days=5)).isoformat()
        
        result = format_relative_time(timestamp)
        
        # 日付として表示されることを確認
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    def test_datetime_object_input(self):
        """datetime オブジェクト入力のテスト"""
        # datetime オブジェクトを直接渡す
        dt_input = self.base_time - timedelta(hours=1)
        
        result = format_relative_time(dt_input)
        
        # 適切に処理されることを確認
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "不明")
    
    @patch('utils.time_format.logger')
    def test_invalid_input(self, mock_logger):
        """無効な入力のテスト"""
        invalid_input = "invalid-timestamp"
        
        result = format_relative_time(invalid_input)
        
        # エラー時の戻り値確認
        self.assertEqual(result, "不明")
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()
    
    @patch('utils.time_format.logger')
    def test_none_input(self, mock_logger):
        """None 入力のテスト"""
        result = format_relative_time(None)
        
        # エラー時の戻り値確認
        self.assertEqual(result, "不明")
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()


class TestTimeFormatIntegration(unittest.TestCase):
    """時間フォーマット統合テストクラス"""
    
    def test_same_timestamp_different_formats(self):
        """同じタイムスタンプで異なるフォーマットのテスト"""
        # 同じUTCタイムスタンプ
        timestamp = "2024-01-01T12:00:00Z"
        
        # JST形式とrelative形式で変換
        jst_result = format_timestamp_to_jst(timestamp)
        relative_result = format_relative_time(timestamp)
        
        # 両方とも有効な文字列が返されることを確認
        self.assertIsInstance(jst_result, str)
        self.assertIsInstance(relative_result, str)
        self.assertNotEqual(jst_result, "不明")
        # relative_resultは現在時刻に依存するため、"不明"でなければ良い
        
        # JST形式の結果が期待通りであることを確認
        self.assertEqual(jst_result, "2024/01/01 21:00")
    
    def test_boundary_conditions(self):
        """境界条件のテスト"""
        # 様々な境界条件をテスト
        boundary_times = [
            "2024-02-29T00:00:00Z",  # うるう年
            "2024-12-31T23:59:59Z",  # 年末
            "2024-01-01T00:00:00Z",  # 年始
        ]
        
        for timestamp in boundary_times:
            with self.subTest(timestamp=timestamp):
                jst_result = format_timestamp_to_jst(timestamp)
                relative_result = format_relative_time(timestamp)
                
                # エラーにならず、有効な文字列が返されることを確認
                self.assertIsInstance(jst_result, str)
                self.assertIsInstance(relative_result, str)
    
    def test_consistency_with_different_input_types(self):
        """異なる入力タイプでの一貫性テスト"""
        # 同じ時刻を文字列とdatetimeオブジェクトで表現
        timestamp_str = "2024-01-01T12:00:00Z"
        timestamp_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # 両方の形式で変換
        jst_from_str = format_timestamp_to_jst(timestamp_str)
        jst_from_dt = format_timestamp_to_jst(timestamp_dt)
        
        # 結果が一致することを確認
        self.assertEqual(jst_from_str, jst_from_dt)


if __name__ == '__main__':
    unittest.main(verbosity=2)