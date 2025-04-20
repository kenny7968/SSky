#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーション設定のテスト
"""

import unittest
import os
import sys
import tempfile
import json
import shutil

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.app_config import AppConfig

class TestAppConfig(unittest.TestCase):
    """アプリケーション設定のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """デフォルト設定のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # 結果の確認
        self.assertEqual(config.get('app_name'), 'SSky')
        self.assertEqual(config.get('version'), '1.0.0')
        self.assertEqual(config.get('theme'), 'light')
        self.assertEqual(config.get('font_size'), 10)
        self.assertEqual(config.get('window_size.width'), 800)
        self.assertEqual(config.get('window_size.height'), 600)
        self.assertEqual(config.get('timeline.refresh_interval'), 60)
        self.assertEqual(config.get('timeline.post_count'), 50)
        self.assertTrue(config.get('timeline.auto_refresh'))
        self.assertFalse(config.get('debug_mode'))
    
    def test_save_and_load(self):
        """設定の保存と読み込みのテスト"""
        # 設定を作成して保存
        config = AppConfig(self.config_path)
        config.set('theme', 'dark')
        config.set('font_size', 12)
        config.save()
        
        # 設定ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.config_path))
        
        # 設定ファイルの内容を確認
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config['theme'], 'dark')
            self.assertEqual(saved_config['font_size'], 12)
        
        # 新しいインスタンスで読み込み
        new_config = AppConfig(self.config_path)
        
        # 結果の確認
        self.assertEqual(new_config.get('theme'), 'dark')
        self.assertEqual(new_config.get('font_size'), 12)
    
    def test_get_with_default(self):
        """デフォルト値を指定したget()のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # 存在しないキーにデフォルト値を指定
        result = config.get('non_existent_key', 'default_value')
        
        # 結果の確認
        self.assertEqual(result, 'default_value')
    
    def test_get_nested_key(self):
        """ネストされたキーのget()のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # ネストされたキーを取得
        result = config.get('window_size.width')
        
        # 結果の確認
        self.assertEqual(result, 800)
    
    def test_get_nested_key_not_found(self):
        """存在しないネストされたキーのget()のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # 存在しないネストされたキーを取得
        result = config.get('window_size.non_existent', 'default_value')
        
        # 結果の確認
        self.assertEqual(result, 'default_value')
    
    def test_set_nested_key(self):
        """ネストされたキーのset()のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # ネストされたキーを設定
        config.set('window_size.width', 1024)
        
        # 結果の確認
        self.assertEqual(config.get('window_size.width'), 1024)
    
    def test_set_new_nested_key(self):
        """新しいネストされたキーのset()のテスト"""
        # テスト実行
        config = AppConfig(self.config_path)
        
        # 新しいネストされたキーを設定
        config.set('new_section.new_key', 'new_value')
        
        # 結果の確認
        self.assertEqual(config.get('new_section.new_key'), 'new_value')

if __name__ == '__main__':
    unittest.main()
