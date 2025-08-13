#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインパフォーマンステスト (Phase 2 pytest版)
"""

import pytest
import time
# import psutil  # オプショナル依存性のためコメントアウト
import gc
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from tests.factories import PostFactory, TimelineFactory, UserFactory


@pytest.mark.slow
@pytest.mark.performance
class TestTimelinePerformance:
    """タイムライン関連のパフォーマンステスト"""
    
    @pytest.fixture
    def performance_api_client(self, mock_atproto_client):
        """パフォーマンステスト用APIクライアント"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            from core.client.api_client import BlueskyApiClient
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_large_timeline_loading_performance(self, performance_api_client, mock_atproto_client):
        """大量タイムラインデータの読み込み性能テスト"""
        # 大量のタイムラインデータを生成（1000件）
        large_timeline = TimelineFactory.create_timeline(count=1000, time_range_hours=168)  # 1週間分
        
        mock_timeline = MagicMock()
        mock_timeline.feed = large_timeline
        mock_atproto_client.get_timeline.return_value = mock_timeline
        
        # メモリ使用量の測定開始（psutil利用可能時のみ）
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            process = None
            initial_memory = 0
        
        # 性能測定
        start_time = time.time()
        
        result = performance_api_client.get_timeline(limit=1000)
        
        end_time = time.time()
        
        # メモリ使用量の測定終了
        if process:
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
        else:
            final_memory = 0
            memory_increase = 0
        
        # 性能評価
        execution_time = end_time - start_time
        
        # 結果検証
        assert result == mock_timeline
        assert len(result.feed) == 1000
        
        # 性能基準
        assert execution_time < 2.0, f"実行時間が遅すぎます: {execution_time:.2f}秒"
        assert memory_increase < 50, f"メモリ使用量が多すぎます: {memory_increase:.2f}MB増加"
        
        # レポート出力
        print(f"\n=== タイムライン読み込み性能レポート ===")
        print(f"データ件数: {len(result.feed)}")
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"メモリ増加: {memory_increase:.2f}MB")
        print(f"処理速度: {len(result.feed)/execution_time:.1f}件/秒")
    
    def test_timeline_scrolling_simulation_performance(self, performance_api_client, mock_atproto_client):
        """タイムラインスクロールシミュレーション性能テスト"""
        # ページング用のタイムラインデータを準備
        page_size = 50
        total_pages = 20  # 合計1000件
        
        def mock_get_timeline(limit=50, cursor=None):
            """ページング付きタイムライン取得のモック"""
            page_data = TimelineFactory.create_timeline(count=limit, time_range_hours=24)
            timeline = MagicMock()
            timeline.feed = page_data
            timeline.cursor = f"cursor_{time.time()}"  # 次のページのカーソル
            return timeline
        
        mock_atproto_client.get_timeline.side_effect = mock_get_timeline
        
        # スクロール性能の測定
        start_time = time.time()
        total_posts_loaded = 0
        page_load_times = []
        
        for page in range(total_pages):
            page_start = time.time()
            
            # タイムライン取得（スクロールダウンをシミュレート）
            timeline = performance_api_client.get_timeline(limit=page_size)
            total_posts_loaded += len(timeline.feed)
            
            page_end = time.time()
            page_load_times.append(page_end - page_start)
            
            # 実際のスクロールでは少し間隔があるため
            time.sleep(0.01)
        
        end_time = time.time()
        
        # 性能評価
        total_time = end_time - start_time
        average_page_load = sum(page_load_times) / len(page_load_times)
        max_page_load = max(page_load_times)
        
        # 結果検証
        assert total_posts_loaded == total_pages * page_size
        
        # 性能基準
        assert total_time < 10.0, f"総実行時間が長すぎます: {total_time:.2f}秒"
        assert average_page_load < 0.1, f"平均ページ読み込みが遅すぎます: {average_page_load:.3f}秒"
        assert max_page_load < 0.5, f"最大ページ読み込みが遅すぎます: {max_page_load:.3f}秒"
        
        # レポート出力
        print(f"\n=== タイムラインスクロール性能レポート ===")
        print(f"総投稿数: {total_posts_loaded}")
        print(f"ページ数: {total_pages}")
        print(f"総実行時間: {total_time:.2f}秒")
        print(f"平均ページ読み込み: {average_page_load:.3f}秒")
        print(f"最大ページ読み込み: {max_page_load:.3f}秒")
    
    def test_concurrent_timeline_requests_performance(self, performance_api_client, mock_atproto_client):
        """同時タイムライン要求の性能テスト"""
        # 同時要求用のタイムラインデータ準備
        def mock_get_timeline_with_delay(limit=50):
            """遅延付きタイムライン取得のモック"""
            time.sleep(0.1)  # ネットワーク遅延をシミュレート
            timeline_data = TimelineFactory.create_timeline(count=limit)
            timeline = MagicMock()
            timeline.feed = timeline_data
            return timeline
        
        mock_atproto_client.get_timeline.side_effect = mock_get_timeline_with_delay
        
        # 同時要求の実行
        concurrent_requests = 10
        results = []
        errors = []
        
        def timeline_request_worker(request_id):
            """ワーカー関数"""
            try:
                start_time = time.time()
                result = performance_api_client.get_timeline(limit=25)
                end_time = time.time()
                return {
                    'request_id': request_id,
                    'result': result,
                    'duration': end_time - start_time,
                    'posts_count': len(result.feed)
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'error': str(e),
                    'duration': 0,
                    'posts_count': 0
                }
        
        # 性能測定
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(timeline_request_worker, i) 
                for i in range(concurrent_requests)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if 'error' in result:
                    errors.append(result)
                else:
                    results.append(result)
        
        end_time = time.time()
        
        # 性能評価
        total_time = end_time - start_time
        successful_requests = len(results)
        failed_requests = len(errors)
        
        if results:
            average_request_time = sum(r['duration'] for r in results) / len(results)
            max_request_time = max(r['duration'] for r in results)
            total_posts = sum(r['posts_count'] for r in results)
        else:
            average_request_time = 0
            max_request_time = 0
            total_posts = 0
        
        # 結果検証
        assert failed_requests == 0, f"失敗した要求があります: {failed_requests}件"
        assert successful_requests == concurrent_requests
        
        # 性能基準（同時要求でもレスポンス時間が大幅に悪化しない）
        assert total_time < 2.0, f"同時要求の総時間が長すぎます: {total_time:.2f}秒"
        assert average_request_time < 0.5, f"平均要求時間が遅すぎます: {average_request_time:.3f}秒"
        
        # レポート出力
        print(f"\n=== 同時タイムライン要求性能レポート ===")
        print(f"同時要求数: {concurrent_requests}")
        print(f"成功要求: {successful_requests}")
        print(f"失敗要求: {failed_requests}")
        print(f"総実行時間: {total_time:.2f}秒")
        print(f"平均要求時間: {average_request_time:.3f}秒")
        print(f"最大要求時間: {max_request_time:.3f}秒")
        print(f"合計投稿数: {total_posts}")
    
    def test_memory_usage_with_large_dataset(self, performance_api_client, mock_atproto_client):
        """大量データでのメモリ使用量テスト"""
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            process = None
            initial_memory = 0
        
        # 段階的にデータサイズを増やしてメモリ使用量を監視
        data_sizes = [100, 500, 1000, 2000, 5000]
        memory_measurements = []
        
        for size in data_sizes:
            # ガベージコレクションを実行してクリーンな状態から測定
            gc.collect()
            
            # タイムラインデータを生成
            timeline_data = TimelineFactory.create_timeline(count=size)
            mock_timeline = MagicMock()
            mock_timeline.feed = timeline_data
            mock_atproto_client.get_timeline.return_value = mock_timeline
            
            # データを取得
            result = performance_api_client.get_timeline(limit=size)
            
            # メモリ使用量を測定
            if process:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
            else:
                current_memory = 0
                memory_increase = 0
            
            memory_measurements.append({
                'data_size': size,
                'memory_mb': memory_increase,
                'memory_per_item': memory_increase / size if size > 0 else 0
            })
            
            # 大量データでもメモリリークがないことを確認
            if size >= 1000:
                # 1000件あたりのメモリ使用量が合理的な範囲内であることを確認
                assert memory_increase < size * 0.1, f"メモリ使用量が多すぎます: {memory_increase:.2f}MB for {size} items"
        
        # メモリ使用パターンの分析
        print(f"\n=== メモリ使用量分析レポート ===")
        for measurement in memory_measurements:
            print(f"データ数: {measurement['data_size']:>5}, "
                  f"メモリ使用: {measurement['memory_mb']:>6.2f}MB, "
                  f"1件あたり: {measurement['memory_per_item']:>6.3f}MB")
        
        # メモリリークのチェック
        if process:
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_diff = final_memory - initial_memory
        else:
            final_memory = 0
            memory_diff = 0
        
        # 最終的なメモリ増加が合理的な範囲内であることを確認
        assert memory_diff < 100, f"テスト終了後のメモリ使用量が多すぎます: {memory_diff:.2f}MB増加"


@pytest.mark.slow
@pytest.mark.performance
class TestPostingPerformance:
    """投稿関連のパフォーマンステスト"""
    
    @pytest.fixture
    def performance_posting_client(self, mock_atproto_client):
        """投稿性能テスト用クライアント"""
        with patch('core.client.api_client.AtprotoClient') as mock_atproto_class:
            from core.client.api_client import BlueskyApiClient
            client = BlueskyApiClient()
            mock_atproto_class.return_value = mock_atproto_client
            client.client = mock_atproto_client
            return client
    
    def test_bulk_posting_performance(self, performance_posting_client, mock_atproto_client):
        """大量投稿の性能テスト"""
        # 投稿成功のモック
        def mock_send_post(text, images=None):
            time.sleep(0.05)  # API遅延をシミュレート
            return MagicMock(uri=f"at://test.bsky.social/app.bsky.feed.post/{time.time()}")
        
        mock_atproto_client.send_post.side_effect = mock_send_post
        
        # 大量投稿のテストデータ
        post_count = 50
        post_texts = [f"テスト投稿 {i+1}: {PostFactory()['record']['text'][:100]}" for i in range(post_count)]
        
        # 性能測定
        start_time = time.time()
        successful_posts = 0
        failed_posts = 0
        post_times = []
        
        for i, text in enumerate(post_texts):
            post_start = time.time()
            
            try:
                result = performance_posting_client.send_post(text)
                if result:
                    successful_posts += 1
                else:
                    failed_posts += 1
            except Exception:
                failed_posts += 1
            
            post_end = time.time()
            post_times.append(post_end - post_start)
        
        end_time = time.time()
        
        # 性能評価
        total_time = end_time - start_time
        average_post_time = sum(post_times) / len(post_times)
        posts_per_second = successful_posts / total_time
        
        # 結果検証
        assert failed_posts == 0, f"失敗した投稿があります: {failed_posts}件"
        assert successful_posts == post_count
        
        # 性能基準
        assert total_time < 30.0, f"大量投稿の総時間が長すぎます: {total_time:.2f}秒"
        assert average_post_time < 1.0, f"平均投稿時間が遅すぎます: {average_post_time:.3f}秒"
        
        # レポート出力
        print(f"\n=== 大量投稿性能レポート ===")
        print(f"投稿数: {post_count}")
        print(f"成功投稿: {successful_posts}")
        print(f"失敗投稿: {failed_posts}")
        print(f"総実行時間: {total_time:.2f}秒")
        print(f"平均投稿時間: {average_post_time:.3f}秒")
        print(f"投稿速度: {posts_per_second:.1f}件/秒")
    
    def test_image_upload_performance(self, performance_posting_client, mock_atproto_client):
        """画像アップロード性能テスト"""
        # 画像アップロードのモック
        def mock_upload_blob(data, mime_type):
            # ファイルサイズに応じた遅延をシミュレート
            delay = len(data) / 1024 / 1024 * 0.1  # 1MBあたり0.1秒
            time.sleep(delay)
            return MagicMock(ref=f"blob_{time.time()}")
        
        mock_atproto_client.upload_blob.side_effect = mock_upload_blob
        
        # 様々なサイズの画像データをシミュレート
        image_sizes = [
            (50 * 1024, "image/jpeg"),      # 50KB
            (200 * 1024, "image/jpeg"),     # 200KB  
            (500 * 1024, "image/png"),      # 500KB
            (1024 * 1024, "image/jpeg"),    # 1MB
            (2 * 1024 * 1024, "image/png") # 2MB
        ]
        
        upload_results = []
        
        for size, mime_type in image_sizes:
            # テストデータの生成
            test_data = b"x" * size
            
            # アップロード性能の測定
            start_time = time.time()
            
            try:
                result = performance_posting_client.upload_blob(test_data, mime_type)
                success = result is not None
            except Exception:
                success = False
            
            end_time = time.time()
            
            upload_time = end_time - start_time
            upload_speed = size / 1024 / upload_time if upload_time > 0 else 0  # KB/s
            
            upload_results.append({
                'size_kb': size / 1024,
                'mime_type': mime_type,
                'upload_time': upload_time,
                'upload_speed': upload_speed,
                'success': success
            })
        
        # 結果検証
        for result in upload_results:
            assert result['success'], f"アップロード失敗: {result['size_kb']}KB {result['mime_type']}"
            
            # 性能基準（ファイルサイズに応じた合理的なアップロード時間）
            expected_max_time = result['size_kb'] / 1024 * 5  # 1MBあたり最大5秒
            assert result['upload_time'] < expected_max_time, \
                f"アップロード時間が遅すぎます: {result['upload_time']:.2f}秒 (期待値: < {expected_max_time:.2f}秒)"
        
        # レポート出力
        print(f"\n=== 画像アップロード性能レポート ===")
        for result in upload_results:
            print(f"サイズ: {result['size_kb']:>7.1f}KB, "
                  f"タイプ: {result['mime_type']:>10}, "
                  f"時間: {result['upload_time']:>6.3f}秒, "
                  f"速度: {result['upload_speed']:>8.1f}KB/s")


@pytest.mark.slow
@pytest.mark.performance
class TestDatabasePerformance:
    """データベース関連のパフォーマンステスト"""
    
    def test_bulk_data_insertion_performance(self, temp_db_file):
        """大量データ挿入性能テスト"""
        import sqlite3
        
        # 実際のSQLite接続を使用
        real_connection = sqlite3.connect(":memory:")
        
        # テーブル作成
        cursor = real_connection.cursor()
        cursor.execute("""
            CREATE TABLE test_posts (
                id INTEGER PRIMARY KEY,
                uri TEXT NOT NULL,
                author_handle TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                indexed_at DATETIME NOT NULL
            )
        """)
        real_connection.commit()
        
        # 大量データの準備
        test_posts = [PostFactory() for _ in range(1000)]
        
        # 一括挿入の性能測定
        start_time = time.time()
        
        for post in test_posts:
            cursor.execute("""
                INSERT INTO test_posts (uri, author_handle, content, created_at, indexed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                post['uri'],
                post['author']['handle'],
                post['record']['text'][:500],  # 長すぎるテキストは切り取り
                post['record']['createdAt'],
                post['indexedAt']
            ))
        
        real_connection.commit()
        end_time = time.time()
        
        # 性能評価
        insertion_time = end_time - start_time
        insertions_per_second = len(test_posts) / insertion_time
        
        # 挿入されたデータの確認
        cursor.execute("SELECT COUNT(*) FROM test_posts")
        inserted_count = cursor.fetchone()[0]
        
        # 結果検証
        assert inserted_count == len(test_posts)
        
        # 性能基準
        assert insertion_time < 5.0, f"大量挿入時間が遅すぎます: {insertion_time:.2f}秒"
        assert insertions_per_second > 100, f"挿入速度が遅すぎます: {insertions_per_second:.1f}件/秒"
        
        # レポート出力
        print(f"\n=== データベース挿入性能レポート ===")
        print(f"挿入件数: {len(test_posts)}")
        print(f"実行時間: {insertion_time:.3f}秒")
        print(f"挿入速度: {insertions_per_second:.1f}件/秒")
        
        real_connection.close()
    
    def test_complex_query_performance(self, temp_db_file):
        """複雑クエリ性能テスト"""
        with patch('core.data_store.sqlite3') as mock_sqlite:
            import sqlite3
            
            # 実際のSQLite接続を使用
            real_connection = sqlite3.connect(":memory:")
            mock_sqlite.connect.return_value = real_connection
            
            # テストデータの準備とテーブル作成
            cursor = real_connection.cursor()
            cursor.execute("""
                CREATE TABLE test_posts (
                    id INTEGER PRIMARY KEY,
                    uri TEXT NOT NULL,
                    author_handle TEXT NOT NULL,
                    author_name TEXT,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    like_count INTEGER DEFAULT 0,
                    repost_count INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_author_handle ON test_posts(author_handle)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_created_at ON test_posts(created_at)
            """)
            
            # 大量テストデータの挿入
            test_posts = [PostFactory() for _ in range(2000)]
            
            for post in test_posts:
                cursor.execute("""
                    INSERT INTO test_posts 
                    (uri, author_handle, author_name, content, created_at, like_count, repost_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    post['uri'],
                    post['author']['handle'],
                    post['author'].get('displayName', ''),
                    post['record']['text'][:500],
                    post['record']['createdAt'],
                    post.get('likeCount', 0),
                    post.get('repostCount', 0)
                ))
            
            real_connection.commit()
            
            # 複雑クエリのテスト
            complex_queries = [
                # 人気投稿の取得
                """
                SELECT * FROM test_posts 
                WHERE like_count > 10 
                ORDER BY like_count DESC, created_at DESC 
                LIMIT 50
                """,
                
                # 特定ユーザーの投稿履歴
                """
                SELECT * FROM test_posts 
                WHERE author_handle LIKE '%.bsky.social' 
                ORDER BY created_at DESC 
                LIMIT 100
                """,
                
                # 統計クエリ
                """
                SELECT 
                    author_handle,
                    COUNT(*) as post_count,
                    AVG(like_count) as avg_likes,
                    MAX(like_count) as max_likes
                FROM test_posts 
                GROUP BY author_handle 
                HAVING post_count > 1
                ORDER BY avg_likes DESC
                LIMIT 20
                """,
                
                # 時間範囲での検索
                """
                SELECT * FROM test_posts 
                WHERE created_at >= datetime('2024-01-01T00:00:00Z')
                AND content LIKE '%テスト%'
                ORDER BY created_at DESC
                """
            ]
            
            query_results = []
            
            for i, query in enumerate(complex_queries):
                # クエリ性能の測定
                start_time = time.time()
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                end_time = time.time()
                
                query_time = end_time - start_time
                result_count = len(results)
                
                query_results.append({
                    'query_id': i + 1,
                    'execution_time': query_time,
                    'result_count': result_count,
                    'records_per_second': result_count / query_time if query_time > 0 else 0
                })
                
                # 性能基準（複雑クエリでも合理的な時間内で実行される）
                assert query_time < 2.0, f"クエリ{i+1}の実行時間が遅すぎます: {query_time:.3f}秒"
            
            # レポート出力
            print(f"\n=== 複雑クエリ性能レポート ===")
            for result in query_results:
                print(f"クエリ{result['query_id']}: "
                      f"実行時間: {result['execution_time']:.3f}秒, "
                      f"結果件数: {result['result_count']}, "
                      f"処理速度: {result['records_per_second']:.1f}件/秒")
            
            real_connection.close()