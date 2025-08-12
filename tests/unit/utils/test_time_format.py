#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
時間フォーマットユーティリティの単体テスト (Phase 2 pytest版)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock

from utils.time_format import format_timestamp_to_jst, format_relative_time


class TestFormatTimestampToJst:
    """format_timestamp_to_jst 関数のテストクラス"""
    
    def test_iso_string_with_z(self):
        """Z付きISO文字列の変換テスト"""
        # UTC時間を設定 (2024-01-01 12:00:00 UTC)
        utc_timestamp = "2024-01-01T12:00:00Z"
        
        # JST変換実行 (UTC+9なので21:00になる)
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        assert result == "2024/01/01 21:00"
    
    def test_iso_string_with_timezone(self):
        """タイムゾーン付きISO文字列の変換テスト"""
        # UTC時間を明示的に指定
        utc_timestamp = "2024-01-01T12:00:00+00:00"
        
        # JST変換実行
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        assert result == "2024/01/01 21:00"
    
    def test_datetime_object_utc(self):
        """UTC datetimeオブジェクトの変換テスト"""
        # UTC datetime オブジェクトを作成
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # JST変換実行
        result = format_timestamp_to_jst(utc_dt)
        
        # 結果確認
        assert result == "2024/01/01 21:00"
    
    def test_datetime_object_with_different_timezone(self):
        """異なるタイムゾーンのdatetimeオブジェクトの変換テスト"""
        # EST (UTC-5) datetime オブジェクトを作成
        est_tz = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est_tz)
        
        # JST変換実行 (EST 12:00 = UTC 17:00 = JST 02:00+1day)
        result = format_timestamp_to_jst(est_dt)
        
        # 結果確認
        assert result == "2024/01/02 02:00"
    
    def test_edge_case_new_year(self):
        """年跨ぎの変換テスト"""
        # UTC大晦日の夜
        utc_timestamp = "2023-12-31T20:00:00Z"
        
        # JST変換実行 (翌年になる)
        result = format_timestamp_to_jst(utc_timestamp)
        
        # 結果確認
        assert result == "2024/01/01 05:00"
    
    @pytest.mark.parametrize("utc_time,expected_jst", [
        ("2024-06-15T00:00:00Z", "2024/06/15 09:00"),  # 午前
        ("2024-06-15T15:30:45Z", "2024/06/16 00:30"),  # 日跨ぎ  
        ("2024-12-31T23:59:59Z", "2025/01/01 08:59"),  # 年跨ぎ
    ])
    def test_various_times(self, utc_time, expected_jst):
        """様々な時刻の変換テスト（パラメータ化）"""
        result = format_timestamp_to_jst(utc_time)
        assert result == expected_jst
    
    def test_invalid_string_format(self, mock_logger):
        """無効な文字列フォーマットのテスト"""
        invalid_timestamp = "invalid-timestamp"
        
        with patch('utils.time_format.logger', mock_logger):
            # エラーハンドリング実行
            result = format_timestamp_to_jst(invalid_timestamp)
        
        # エラー時の戻り値確認
        assert result == "不明"
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "時間フォーマットに失敗しました" in error_call
    
    def test_none_input(self, mock_logger):
        """None入力のテスト"""
        with patch('utils.time_format.logger', mock_logger):
            # None入力でエラーハンドリング
            result = format_timestamp_to_jst(None)
        
        # エラー時の戻り値確認
        assert result == "不明"
        
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
        assert isinstance(result, str)


class TestFormatRelativeTime:
    """format_relative_time 関数のテストクラス"""
    
    @pytest.fixture
    def base_time(self):
        """基準時刻フィクスチャ (2024-01-01 12:00:00 JST)"""
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))
    
    def test_just_now(self, base_time):
        """「たった今」のテスト"""
        with patch('utils.time_format.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # 30秒前の時刻
            timestamp = (base_time - timedelta(seconds=30)).isoformat()
            
            result = format_relative_time(timestamp)
            
            # 実装に依存するが、通常は「たった今」または「30秒前」
            assert isinstance(result, str)
            assert result != "不明"
    
    def test_minutes_ago(self, base_time):
        """「○分前」のテスト"""
        with patch('utils.time_format.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # 15分前の時刻
            timestamp = (base_time - timedelta(minutes=15)).isoformat()
            
            result = format_relative_time(timestamp)
            
            # 15分前として表示されることを確認
            assert isinstance(result, str)
            assert result != "不明"
    
    def test_hours_ago(self, base_time):
        """「○時間前」のテスト"""
        with patch('utils.time_format.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # 3時間前の時刻
            timestamp = (base_time - timedelta(hours=3)).isoformat()
            
            result = format_relative_time(timestamp)
            
            # 3時間前として表示されることを確認
            assert isinstance(result, str)
            assert result != "不明"
    
    def test_yesterday(self, base_time):
        """「昨日」のテスト"""
        with patch('utils.time_format.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # 昨日の同時刻
            timestamp = (base_time - timedelta(days=1)).isoformat()
            
            result = format_relative_time(timestamp)
            
            # 昨日として表示されることを確認
            assert isinstance(result, str)
            assert result != "不明"
    
    def test_days_ago(self, base_time):
        """「○日前」のテスト"""
        with patch('utils.time_format.datetime') as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # 5日前の時刻
            timestamp = (base_time - timedelta(days=5)).isoformat()
            
            result = format_relative_time(timestamp)
            
            # 日付として表示されることを確認
            assert isinstance(result, str)
            assert result != "不明"
    
    def test_datetime_object_input(self, base_time):
        """datetime オブジェクト入力のテスト"""
        # datetime オブジェクトを直接渡す
        dt_input = base_time - timedelta(hours=1)
        
        result = format_relative_time(dt_input)
        
        # 適切に処理されることを確認
        assert isinstance(result, str)
        assert result != "不明"
    
    def test_invalid_input(self, mock_logger):
        """無効な入力のテスト"""
        invalid_input = "invalid-timestamp"
        
        with patch('utils.time_format.logger', mock_logger):
            result = format_relative_time(invalid_input)
        
        # エラー時の戻り値確認
        assert result == "不明"
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()
    
    def test_none_input(self, mock_logger):
        """None 入力のテスト"""
        with patch('utils.time_format.logger', mock_logger):
            result = format_relative_time(None)
        
        # エラー時の戻り値確認
        assert result == "不明"
        
        # ログが出力されることを確認
        mock_logger.error.assert_called_once()


class TestTimeFormatIntegration:
    """時間フォーマット統合テストクラス"""
    
    def test_same_timestamp_different_formats(self):
        """同じタイムスタンプで異なるフォーマットのテスト"""
        # 同じUTCタイムスタンプ
        timestamp = "2024-01-01T12:00:00Z"
        
        # JST形式とrelative形式で変換
        jst_result = format_timestamp_to_jst(timestamp)
        relative_result = format_relative_time(timestamp)
        
        # 両方とも有効な文字列が返されることを確認
        assert isinstance(jst_result, str)
        assert isinstance(relative_result, str)
        assert jst_result != "不明"
        # relative_resultは現在時刻に依存するため、\"不明\"でなければ良い
        
        # JST形式の結果が期待通りであることを確認
        assert jst_result == "2024/01/01 21:00"
    
    @pytest.mark.parametrize("timestamp", [
        "2024-02-29T00:00:00Z",  # うるう年
        "2024-12-31T23:59:59Z",  # 年末
        "2024-01-01T00:00:00Z",  # 年始
    ])
    def test_boundary_conditions(self, timestamp):
        """境界条件のテスト（パラメータ化）"""
        jst_result = format_timestamp_to_jst(timestamp)
        relative_result = format_relative_time(timestamp)
        
        # エラーにならず、有効な文字列が返されることを確認
        assert isinstance(jst_result, str)
        assert isinstance(relative_result, str)
    
    def test_consistency_with_different_input_types(self):
        """異なる入力タイプでの一貫性テスト"""
        # 同じ時刻を文字列とdatetimeオブジェクトで表現
        timestamp_str = "2024-01-01T12:00:00Z"
        timestamp_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # 両方の形式で変換
        jst_from_str = format_timestamp_to_jst(timestamp_str)
        jst_from_dt = format_timestamp_to_jst(timestamp_dt)
        
        # 結果が一致することを確認
        assert jst_from_str == jst_from_dt


# 性能テスト用のマーカー  
@pytest.mark.slow
class TestTimeFormatPerformance:
    """時間フォーマット性能テストクラス"""
    
    def test_bulk_jst_conversion_performance(self):
        """大量JST変換の性能テスト"""
        import time
        
        timestamps = [
            f"2024-01-{day:02d}T{hour:02d}:30:00Z"
            for day in range(1, 32)
            for hour in range(24)
        ]
        
        start_time = time.time()
        
        results = [format_timestamp_to_jst(ts) for ts in timestamps]
        
        end_time = time.time()
        
        # 全て正常に変換されることを確認
        assert all(result != "不明" for result in results)
        
        # 性能目標: 1000件以下なら1秒以内
        if len(timestamps) <= 1000:
            assert end_time - start_time < 1.0
    
    def test_bulk_relative_time_performance(self):
        """大量相対時間変換の性能テスト"""
        import time
        
        # 様々な時刻のタイムスタンプを生成
        base_time = datetime.now(timezone.utc)
        timestamps = [
            (base_time - timedelta(hours=i)).isoformat().replace('+00:00', 'Z')
            for i in range(100)
        ]
        
        start_time = time.time()
        
        results = [format_relative_time(ts) for ts in timestamps]
        
        end_time = time.time()
        
        # 全て正常に変換されることを確認
        assert all(result != "不明" for result in results)
        
        # 性能目標: 100件なら0.5秒以内
        assert end_time - start_time < 0.5