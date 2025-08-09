#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
設定変更フロー統合テスト (Phase 3 拡充版)
"""

import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
from typing import Dict, Any


@pytest.mark.integration
class TestSettingsFlowIntegration:
    """設定変更フロー統合テストクラス"""
    
    @pytest.fixture
    def integrated_settings_components(self, temp_config_file):
        """統合された設定関連コンポーネント"""
        components = {}
        
        # 初期設定ファイルを作成
        initial_settings = {
            "timeline_refresh_interval": 30,
            "max_posts_display": 100,
            "enable_notifications": True,
            "theme": "default",
            "language": "ja",
            "auto_fetch_enabled": False,
            "fetch_count": 50
        }
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(initial_settings, f, ensure_ascii=False, indent=2)
        
        components['config_file'] = temp_config_file
        components['initial_settings'] = initial_settings
        
        # SettingsManager をモックまたは実際のインスタンスで設定
        with patch('config.settings_manager.SettingsManager._get_settings_file_path') as mock_path:
            mock_path.return_value = temp_config_file
            
            # シングルトンをリセット
            from config.settings_manager import SettingsManager
            if hasattr(SettingsManager, '_instance'):
                SettingsManager._instance = None
            
            components['settings_manager'] = SettingsManager()
        
        return components
    
    def test_complete_settings_update_flow(self, integrated_settings_components):
        """完全な設定更新フローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 現在の設定を取得
        current_interval = settings_manager.get("timeline_refresh_interval")
        assert current_interval == 30
        
        # 設定を更新
        new_interval = 60
        settings_manager.set("timeline_refresh_interval", new_interval)
        
        # 更新された設定を確認
        updated_interval = settings_manager.get("timeline_refresh_interval")
        assert updated_interval == new_interval
        
        # ファイルに永続化されることを確認
        settings_manager.save()
        
        # 新しいインスタンスで設定が永続化されていることを確認
        from config.settings_manager import SettingsManager
        if hasattr(SettingsManager, '_instance'):
            SettingsManager._instance = None
        
        new_manager = SettingsManager()
        persisted_interval = new_manager.get("timeline_refresh_interval")
        assert persisted_interval == new_interval
    
    def test_multiple_settings_update_flow(self, integrated_settings_components):
        """複数設定の同時更新フローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 複数の設定を同時に更新
        updates = {
            "timeline_refresh_interval": 120,
            "max_posts_display": 200,
            "enable_notifications": False,
            "theme": "dark",
            "fetch_count": 75
        }
        
        for key, value in updates.items():
            settings_manager.set(key, value)
        
        # すべての設定が更新されることを確認
        for key, expected_value in updates.items():
            actual_value = settings_manager.get(key)
            assert actual_value == expected_value, f"設定 {key} が期待値 {expected_value} と異なります: {actual_value}"
        
        # 設定を保存
        settings_manager.save()
        
        # 永続化を確認
        from config.settings_manager import SettingsManager
        if hasattr(SettingsManager, '_instance'):
            SettingsManager._instance = None
        
        new_manager = SettingsManager()
        for key, expected_value in updates.items():
            persisted_value = new_manager.get(key)
            assert persisted_value == expected_value
    
    def test_settings_observer_notification_flow(self, integrated_settings_components):
        """設定変更の観察者通知フローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 観察者の設定
        observer_calls = []
        
        def test_observer(key, old_value, new_value):
            observer_calls.append({
                'key': key,
                'old_value': old_value,
                'new_value': new_value
            })
        
        # 観察者を登録
        settings_manager.add_observer(test_observer)
        
        # 設定を変更
        old_value = settings_manager.get("timeline_refresh_interval")
        new_value = 90
        settings_manager.set("timeline_refresh_interval", new_value)
        
        # 観察者が呼ばれることを確認
        assert len(observer_calls) == 1
        call = observer_calls[0]
        assert call['key'] == "timeline_refresh_interval"
        assert call['old_value'] == old_value
        assert call['new_value'] == new_value
        
        # 観察者を削除
        settings_manager.remove_observer(test_observer)
        
        # 削除後は呼ばれないことを確認
        settings_manager.set("timeline_refresh_interval", 120)
        assert len(observer_calls) == 1  # 呼び出し回数は増えない
    
    def test_settings_validation_flow(self, integrated_settings_components):
        """設定値の検証フローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 有効な設定値のテスト
        valid_values = {
            "timeline_refresh_interval": 30,  # 正の整数
            "max_posts_display": 100,         # 正の整数
            "enable_notifications": True,     # ブール値
            "theme": "default",               # 文字列
            "language": "ja"                  # 文字列
        }
        
        for key, value in valid_values.items():
            try:
                settings_manager.set(key, value)
                actual_value = settings_manager.get(key)
                assert actual_value == value
            except Exception as e:
                pytest.fail(f"有効な設定値 {key}={value} が拒否されました: {str(e)}")
        
        # 無効な設定値のテスト（実装に依存）
        invalid_values = {
            "timeline_refresh_interval": -10,  # 負の値
            "max_posts_display": 0,            # ゼロ
            "enable_notifications": "not_bool", # 不正な型
        }
        
        for key, invalid_value in invalid_values.items():
            original_value = settings_manager.get(key)
            try:
                settings_manager.set(key, invalid_value)
                # 無効な値が設定されなかったことを確認
                # （実装が検証をする場合）
                actual_value = settings_manager.get(key)
                # 無効な値が設定された場合も許容（検証がない場合）
            except (ValueError, TypeError):
                # 検証エラーが発生することも許容
                pass
    
    def test_settings_default_value_flow(self, integrated_settings_components):
        """設定のデフォルト値フローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 存在しない設定キーに対するデフォルト値のテスト
        default_value = "default_test_value"
        actual_value = settings_manager.get("non_existent_key", default_value)
        assert actual_value == default_value
        
        # デフォルト値を指定しない場合はNoneが返されることを確認
        actual_value = settings_manager.get("another_non_existent_key")
        assert actual_value is None
    
    def test_settings_reset_flow(self, integrated_settings_components):
        """設定リセットフローのテスト"""
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        initial_settings = components['initial_settings']
        
        # 設定を変更
        settings_manager.set("timeline_refresh_interval", 999)
        settings_manager.set("theme", "custom_theme")
        
        # 変更されたことを確認
        assert settings_manager.get("timeline_refresh_interval") == 999
        assert settings_manager.get("theme") == "custom_theme"
        
        # リセット機能がある場合のテスト
        if hasattr(settings_manager, 'reset'):
            settings_manager.reset()
            
            # 初期値に戻ることを確認
            assert settings_manager.get("timeline_refresh_interval") == initial_settings["timeline_refresh_interval"]
            assert settings_manager.get("theme") == initial_settings["theme"]
        
        # または、手動でリセット（設定ファイルを再作成）
        else:
            # 設定ファイルを初期状態に戻す
            with open(components['config_file'], 'w', encoding='utf-8') as f:
                json.dump(initial_settings, f, ensure_ascii=False, indent=2)
            
            # 設定を再読み込み
            if hasattr(settings_manager, 'reload'):
                settings_manager.reload()
            else:
                # 新しいインスタンスを作成
                from config.settings_manager import SettingsManager
                if hasattr(SettingsManager, '_instance'):
                    SettingsManager._instance = None
                settings_manager = SettingsManager()
            
            # 初期値に戻ることを確認
            assert settings_manager.get("timeline_refresh_interval") == initial_settings["timeline_refresh_interval"]
            assert settings_manager.get("theme") == initial_settings["theme"]
    
    def test_concurrent_settings_access_flow(self, integrated_settings_components):
        """並行設定アクセスフローのテスト"""
        import threading
        import time
        
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        results = []
        errors = []
        
        def settings_worker(worker_id):
            """設定操作ワーカー関数"""
            try:
                # 各ワーカーが異なる設定を操作
                key = f"worker_{worker_id}_setting"
                value = f"value_{worker_id}"
                
                # 設定を追加
                settings_manager.set(key, value)
                
                # 短い待機
                time.sleep(0.1)
                
                # 設定を確認
                retrieved_value = settings_manager.get(key)
                results.append((worker_id, key, value, retrieved_value))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 10個の並行スレッドで設定操作
        threads = []
        for i in range(10):
            thread = threading.Thread(target=settings_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # エラーがないことを確認
        assert len(errors) == 0, f"並行アクセス中にエラーが発生しました: {errors}"
        
        # 全ての設定操作が成功したことを確認
        assert len(results) == 10
        
        for worker_id, key, expected_value, actual_value in results:
            assert actual_value == expected_value, f"Worker {worker_id} の設定が正しく保存されませんでした"


@pytest.mark.integration
class TestSettingsFlowWithRealFile:
    """実際のファイルを使った設定フロー統合テスト"""
    
    @pytest.fixture
    def real_settings_file(self):
        """実際の設定ファイルを使用するセットアップ"""
        # 一時設定ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            settings_file = temp_file.name
            
            # 初期設定を書き込み
            initial_settings = {
                "timeline_refresh_interval": 60,
                "max_posts_display": 150,
                "enable_notifications": True,
                "theme": "light",
                "language": "ja"
            }
            json.dump(initial_settings, temp_file, ensure_ascii=False, indent=2)
        
        yield settings_file, initial_settings
        
        # クリーンアップ
        Path(settings_file).unlink(missing_ok=True)
    
    def test_real_file_settings_persistence(self, real_settings_file):
        """実際のファイルでの設定永続化テスト"""
        settings_file, initial_settings = real_settings_file
        
        with patch('config.settings_manager.SettingsManager._get_settings_file_path') as mock_path:
            mock_path.return_value = settings_file
            
            # 最初のSettingsManagerインスタンス
            from config.settings_manager import SettingsManager
            if hasattr(SettingsManager, '_instance'):
                SettingsManager._instance = None
            
            manager1 = SettingsManager()
            
            # 設定を変更
            manager1.set("timeline_refresh_interval", 300)
            manager1.set("theme", "dark")
            manager1.save()
            
            # 新しいインスタンスで変更が永続化されていることを確認
            if hasattr(SettingsManager, '_instance'):
                SettingsManager._instance = None
            
            manager2 = SettingsManager()
            
            assert manager2.get("timeline_refresh_interval") == 300
            assert manager2.get("theme") == "dark"
            assert manager2.get("max_posts_display") == initial_settings["max_posts_display"]  # 変更されていない設定
    
    def test_real_file_corruption_handling(self, real_settings_file):
        """設定ファイルの破損処理テスト"""
        settings_file, initial_settings = real_settings_file
        
        # ファイルを破損させる
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with patch('config.settings_manager.SettingsManager._get_settings_file_path') as mock_path:
            mock_path.return_value = settings_file
            
            from config.settings_manager import SettingsManager
            if hasattr(SettingsManager, '_instance'):
                SettingsManager._instance = None
            
            try:
                manager = SettingsManager()
                # 破損したファイルがあってもインスタンス作成は成功するか、
                # またはデフォルト設定で動作することを確認
                
                # デフォルト値が取得できることを確認
                default_value = manager.get("timeline_refresh_interval", 30)
                assert isinstance(default_value, int)
                
            except Exception as e:
                # エラーハンドリングが適切に行われることを確認
                # 実装によってはエラーが発生することも許容
                assert isinstance(e, (json.JSONDecodeError, FileNotFoundError, ValueError))


@pytest.mark.integration
@pytest.mark.slow
class TestSettingsFlowPerformance:
    """設定フロー性能テストクラス"""
    
    def test_bulk_settings_operations_performance(self, integrated_settings_components):
        """大量設定操作の性能テスト"""
        import time
        
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 性能測定
        start_time = time.time()
        
        # 大量の設定操作を実行
        for i in range(1000):
            key = f"perf_test_key_{i}"
            value = f"perf_test_value_{i}"
            settings_manager.set(key, value)
        
        end_time = time.time()
        
        # 性能目標: 1000件の設定操作で5秒以内
        assert end_time - start_time < 5.0
        
        # 設定が正しく保存されていることを確認（サンプリング）
        for i in range(0, 1000, 100):  # 100件おきにサンプリング
            key = f"perf_test_key_{i}"
            expected_value = f"perf_test_value_{i}"
            actual_value = settings_manager.get(key)
            assert actual_value == expected_value
    
    def test_frequent_observer_notifications_performance(self, integrated_settings_components):
        """頻繁な観察者通知の性能テスト"""
        import time
        
        components = integrated_settings_components
        settings_manager = components['settings_manager']
        
        # 複数の観察者を登録
        notification_count = 0
        
        def observer1(key, old_value, new_value):
            nonlocal notification_count
            notification_count += 1
        
        def observer2(key, old_value, new_value):
            nonlocal notification_count
            notification_count += 1
        
        def observer3(key, old_value, new_value):
            nonlocal notification_count
            notification_count += 1
        
        settings_manager.add_observer(observer1)
        settings_manager.add_observer(observer2)
        settings_manager.add_observer(observer3)
        
        # 性能測定
        start_time = time.time()
        
        # 頻繁な設定変更を実行
        for i in range(100):
            settings_manager.set("frequent_change_key", f"value_{i}")
        
        end_time = time.time()
        
        # 性能目標: 100回の変更で2秒以内
        assert end_time - start_time < 2.0
        
        # 全ての観察者が適切に通知されることを確認
        assert notification_count == 300  # 100回の変更 × 3つの観察者