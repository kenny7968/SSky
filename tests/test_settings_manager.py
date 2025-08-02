#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
設定管理モジュールのテスト
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
import json
import shutil

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings_manager import SettingsManager

class TestSettingsManager(unittest.TestCase):
    """設定管理のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # シングルトンインスタンスをリセット
        SettingsManager._instance = None
        SettingsManager._observers = []
        
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.test_settings_file = os.path.join(self.temp_dir, 'test_config.json')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # シングルトンインスタンスをリセット
        SettingsManager._instance = None
        SettingsManager._observers = []
        
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir)
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_singleton_pattern(self, mock_ensure_dir):
        """シングルトンパターンのテスト"""
        # 1つ目のインスタンス
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager1 = SettingsManager()
        
        # 2つ目のインスタンス
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager2 = SettingsManager()
        
        # 同じインスタンスであることを確認
        self.assertIs(manager1, manager2)
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_default_settings(self, mock_ensure_dir):
        """デフォルト設定のテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # デフォルト設定値の確認
        self.assertTrue(manager.get('timeline.auto_fetch'))
        self.assertEqual(manager.get('timeline.fetch_interval'), 600)
        self.assertEqual(manager.get('timeline.fetch_count'), 50)
        self.assertTrue(manager.get('post.show_completion_dialog'))
        self.assertFalse(manager.get('advanced.enable_debug_log'))
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_get_nested_key(self, mock_ensure_dir):
        """ネストされたキーの取得テスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # ネストされたキーの取得
        result = manager.get('timeline.auto_fetch')
        self.assertTrue(result)
        
        # 存在しないキーのデフォルト値
        result = manager.get('non_existent.key', 'default_value')
        self.assertEqual(result, 'default_value')
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_set_nested_key(self, mock_ensure_dir):
        """ネストされたキーの設定テスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # ネストされたキーの設定
        result = manager.set('timeline.fetch_interval', 300)
        self.assertTrue(result)
        
        # 設定値の確認
        self.assertEqual(manager.get('timeline.fetch_interval'), 300)
        
        # 新しいネストされたキーの設定
        result = manager.set('new_section.new_key', 'new_value')
        self.assertTrue(result)
        self.assertEqual(manager.get('new_section.new_key'), 'new_value')
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_save_and_load_settings(self, mock_ensure_dir):
        """設定の保存と読み込みテスト"""
        # 設定を作成・変更・保存
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
            manager.set('timeline.fetch_interval', 300)
            manager.set('post.show_completion_dialog', False)
            result = manager.save()
            self.assertTrue(result)
        
        # 設定ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.test_settings_file))
        
        # 設定ファイルの内容を確認
        with open(self.test_settings_file, 'r', encoding='utf-8') as f:
            saved_settings = json.load(f)
            self.assertEqual(saved_settings['timeline']['fetch_interval'], 300)
            self.assertFalse(saved_settings['post']['show_completion_dialog'])
        
        # 新しいインスタンスで読み込み
        SettingsManager._instance = None
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            new_manager = SettingsManager()
        
        # 設定値の確認
        self.assertEqual(new_manager.get('timeline.fetch_interval'), 300)
        self.assertFalse(new_manager.get('post.show_completion_dialog'))
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_validation(self, mock_ensure_dir):
        """設定値バリデーションのテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # 正常な値のバリデーション
        is_valid, error = manager.validate_settings()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # 無効な値を設定
        manager.set('timeline.fetch_interval', 100)  # 180秒未満
        is_valid, error = manager.validate_settings()
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
        # 無効な投稿取得件数
        manager.set('timeline.fetch_count', 150)  # 100を超える
        is_valid, error = manager.validate_settings()
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    @patch('config.settings_manager.ensure_directory_exists')
    @patch('core.error_handler.UnifiedErrorHandler.handle_validation_error')
    def test_set_with_validation(self, mock_handle_validation_error, mock_ensure_dir):
        """バリデーション付き設定のテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # 正常な値の設定
        success, error = manager.set_with_validation('timeline.fetch_interval', 300)
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # 無効な値の設定
        success, error = manager.set_with_validation('timeline.fetch_interval', 100)
        self.assertFalse(success)
        self.assertIsNotNone(error)
        
        # 無効な投稿取得件数
        success, error = manager.set_with_validation('timeline.fetch_count', 150)
        self.assertFalse(success)
        self.assertIsNotNone(error)
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_observer_pattern(self, mock_ensure_dir):
        """Observerパターンのテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # モックObserverを作成
        mock_observer = MagicMock()
        mock_observer.on_settings_changed = MagicMock()
        
        # Observerを追加
        manager.add_observer(mock_observer)
        self.assertIn(mock_observer, manager._observers)
        
        # 設定を変更
        manager.set('timeline.fetch_interval', 300)
        
        # 通知が呼ばれたことを確認
        mock_observer.on_settings_changed.assert_called_once_with('timeline.fetch_interval')
        
        # Observerを削除
        manager.remove_observer(mock_observer)
        self.assertNotIn(mock_observer, manager._observers)
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_fix_invalid_settings(self, mock_ensure_dir):
        """無効な設定値の修正テスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # 無効な値を設定
        manager.set('timeline.fetch_interval', 100)  # 180秒未満
        manager.set('timeline.fetch_count', 0)       # 1未満
        
        # 修正メソッドを実行
        manager._fix_invalid_settings()
        
        # 修正されたことを確認
        self.assertEqual(manager.get('timeline.fetch_interval'), 180)
        self.assertEqual(manager.get('timeline.fetch_count'), 1)
        
        # 上限値の修正テスト
        manager.set('timeline.fetch_count', 150)     # 100を超える
        manager._fix_invalid_settings()
        self.assertEqual(manager.get('timeline.fetch_count'), 100)
    
    @patch('config.settings_manager.ensure_directory_exists')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('core.error_handler.UnifiedErrorHandler.handle_error')
    def test_save_permission_error(self, mock_handle_error, mock_open, mock_ensure_dir):
        """保存時の権限エラーのテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
            result = manager.save()
            self.assertFalse(result)
            # エラーハンドラーが呼ばれることを確認
            mock_handle_error.assert_called()
    
    @patch('config.settings_manager.ensure_directory_exists')
    @patch('builtins.open', side_effect=IOError("IO Error"))
    @patch('core.error_handler.UnifiedErrorHandler.handle_error')
    def test_save_io_error(self, mock_handle_error, mock_open, mock_ensure_dir):
        """保存時のIOエラーのテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
            result = manager.save()
            self.assertFalse(result)
            # エラーハンドラーが呼ばれることを確認
            mock_handle_error.assert_called()
    
    @patch('config.settings_manager.ensure_directory_exists')
    @patch('core.error_handler.UnifiedErrorHandler.handle_error')
    def test_load_invalid_json(self, mock_handle_error, mock_ensure_dir):
        """無効なJSONファイルの読み込みテスト"""
        # 無効なJSONファイルを作成
        with open(self.test_settings_file, 'w') as f:
            f.write('{ invalid json }')
        
        # SettingsManagerのインスタンス作成（エラーが発生せずデフォルト設定が使用されるはず）
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # デフォルト設定が使用されていることを確認
        self.assertTrue(manager.get('timeline.auto_fetch'))
        self.assertEqual(manager.get('timeline.fetch_interval'), 600)
        # エラーハンドラーが呼ばれることを確認
        mock_handle_error.assert_called()
    
    @patch('config.settings_manager.ensure_directory_exists')
    def test_same_value_no_notification(self, mock_ensure_dir):
        """同じ値の設定時は通知されないテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # モックObserverを作成
        mock_observer = MagicMock()
        mock_observer.on_settings_changed = MagicMock()
        manager.add_observer(mock_observer)
        
        # 現在と同じ値を設定
        current_value = manager.get('timeline.fetch_interval')
        manager.set('timeline.fetch_interval', current_value)
        
        # 通知が呼ばれていないことを確認
        mock_observer.on_settings_changed.assert_not_called()
    
    @patch('config.settings_manager.ensure_directory_exists')
    @patch('core.error_handler.UnifiedErrorHandler.handle_error')
    def test_observer_error_handling(self, mock_handle_error, mock_ensure_dir):
        """Observer通知時のエラーハンドリングテスト"""
        with patch.object(SettingsManager, 'settings_file', self.test_settings_file):
            manager = SettingsManager()
        
        # エラーを発生させるObserver
        mock_observer = MagicMock()
        mock_observer.on_settings_changed.side_effect = Exception("Observer error")
        manager.add_observer(mock_observer)
        
        # 設定変更（エラーが発生してもプログラムは継続されるはず）
        result = manager.set('timeline.fetch_interval', 300)
        self.assertTrue(result)
        # エラーハンドラーが呼ばれることを確認
        mock_handle_error.assert_called()

if __name__ == '__main__':
    unittest.main()