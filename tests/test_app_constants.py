#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
AppConstantsのテスト
"""

import unittest
import os
import sys
import tempfile

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.app_constants import AppConstants, get_app_version, get_app_name

class TestAppConstants(unittest.TestCase):
    """AppConstantsクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト対象のインスタンスを作成
        self.app_constants = AppConstants()
    
    def test_singleton(self):
        """シングルトンパターンのテスト"""
        # 2つのインスタンスが同じオブジェクトを参照していることを確認
        instance1 = AppConstants()
        instance2 = AppConstants()
        self.assertIs(instance1, instance2)
    
    def test_get(self):
        """get()メソッドのテスト"""
        # 存在する定数
        self.assertEqual(self.app_constants.get("app_name"), "SSky")
        self.assertEqual(self.app_constants.get("version"), "1.0.0")
        
        # 存在しない定数
        self.assertIsNone(self.app_constants.get("nonexistent"))
        self.assertEqual(self.app_constants.get("nonexistent", "default"), "default")
        
        # ネストされた定数
        self.assertEqual(self.app_constants.get("dirs.config"), os.path.join(self.app_constants.base_dir, "config"))
        
        # 存在しないネストされた定数
        self.assertIsNone(self.app_constants.get("dirs.nonexistent"))
        self.assertEqual(self.app_constants.get("dirs.nonexistent", "default"), "default")
        self.assertIsNone(self.app_constants.get("nonexistent.key"))
    
    def test_helper_functions(self):
        """ヘルパー関数のテスト"""
        self.assertEqual(get_app_name(), "SSky")
        self.assertEqual(get_app_version(), "1.0.0")
        
        # その他のヘルパー関数
        from config.app_constants import get_api_endpoint, get_max_post_length
        self.assertEqual(get_api_endpoint(), "https://bsky.social")
        self.assertEqual(get_max_post_length(), 300)
        
        # ディレクトリ関連のヘルパー関数
        from config.app_constants import get_config_dir, get_base_dir
        self.assertEqual(get_base_dir(), self.app_constants.base_dir)
        self.assertEqual(get_config_dir(), os.path.join(self.app_constants.base_dir, "config"))

if __name__ == "__main__":
    unittest.main()
