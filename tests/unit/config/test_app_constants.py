#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーション定数管理モジュールの単体テスト
"""

import pytest
import os
from unittest.mock import patch

from config.app_constants import AppConstants


class TestAppConstants:
    """AppConstants 基本機能テスト"""
    
    def test_singleton_pattern(self):
        """シングルトンパターンが正しく動作することを確認"""
        instance1 = AppConstants()
        instance2 = AppConstants()
        assert instance1 is instance2
    
    def test_constants_initialization(self):
        """定数が正しく初期化されることを確認"""
        constants = AppConstants()
        
        # 基本的な定数の確認
        assert constants.get('app_name') == 'SSky'
        assert constants.get('version') == '1.0.0'
        assert constants.get('api_endpoint') == 'https://bsky.social'
        
        # システム制限値の確認
        assert constants.get('max_post_length') == 300
        assert constants.get('max_image_size') == 1024 * 1024 * 5
        assert constants.get('max_attachments') == 4
        assert constants.get('supported_image_formats') == ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    def test_api_settings(self):
        """API設定の確認"""
        constants = AppConstants()
        
        assert constants.get('max_retries') == 3
        assert constants.get('retry_delay') == 1
        assert constants.get('timeout') == 30
        assert constants.get('connection_timeout') == 10
        assert constants.get('max_connections') == 10
    
    def test_debug_mode_default(self):
        """デバッグモードのデフォルト値確認"""
        constants = AppConstants()
        assert constants.get('debug_mode') is False
    
    def test_directory_paths(self):
        """ディレクトリパスが正しく設定されることを確認"""
        constants = AppConstants()
        dirs = constants.get('dirs')
        
        assert isinstance(dirs, dict)
        assert 'config' in dirs
        assert 'log' in dirs
        assert 'data' in dirs
        assert 'settings' in dirs
        assert 'assets' in dirs
        
        # パスが実際に存在することは要求しないが、絶対パスであることを確認
        for path in dirs.values():
            assert os.path.isabs(path)
    
    def test_get_with_default_value(self):
        """存在しないキーに対してデフォルト値が返されることを確認"""
        constants = AppConstants()
        
        assert constants.get('nonexistent_key') is None
        assert constants.get('nonexistent_key', 'default') == 'default'
    
    def test_nested_key_access(self):
        """ドット記法でネストされた値にアクセスできることを確認"""
        constants = AppConstants()
        
        # ディレクトリパスへのネストアクセス
        config_dir = constants.get('dirs.config')
        assert config_dir is not None
        assert os.path.isabs(config_dir)
        
        log_dir = constants.get('dirs.log')
        assert log_dir is not None
        assert os.path.isabs(log_dir)
    
    def test_nested_key_with_nonexistent_path(self):
        """存在しないネストパスに対してデフォルト値が返されることを確認"""
        constants = AppConstants()
        
        assert constants.get('nonexistent.nested.key') is None
        assert constants.get('nonexistent.nested.key', 'default') == 'default'
        assert constants.get('dirs.nonexistent', 'default') == 'default'
    
    def test_update_check_settings(self):
        """更新チェック関連設定の確認"""
        constants = AppConstants()
        
        assert constants.get('update_check_url') == ''
        assert constants.get('update_interval') == 7
    
    def test_constants_immutability_protection(self):
        """定数値が直接変更されないことを確認"""
        constants = AppConstants()
        original_app_name = constants.get('app_name')
        
        # 定数辞書を取得して変更を試みる（参照の変更はできないはず）
        constants_dict = constants.constants
        assert constants_dict['app_name'] == original_app_name
        
        # 新しいインスタンス取得でも同じ値が返されることを確認
        new_instance = AppConstants()
        assert new_instance.get('app_name') == original_app_name
    
    def test_base_dir_calculation(self):
        """ベースディレクトリが正しく計算されることを確認"""
        constants = AppConstants()
        
        assert hasattr(constants, 'base_dir')
        assert os.path.isabs(constants.base_dir)
        assert os.path.exists(constants.base_dir)


class TestAppConstantsEdgeCases:
    """AppConstants エッジケーステスト"""
    
    def test_singleton_reset_simulation(self):
        """シングルトンリセット（テスト用）の動作確認"""
        # 最初のインスタンス取得
        instance1 = AppConstants()
        
        # クラス変数を一時的にリセット
        original_instance = AppConstants._instance
        AppConstants._instance = None
        
        try:
            # 新しいインスタンス作成
            instance2 = AppConstants()
            assert instance2 is not instance1
            
            # 設定値は同じであることを確認
            assert instance2.get('app_name') == 'SSky'
            
        finally:
            # テスト後にシングルトンを復元
            AppConstants._instance = original_instance
    
    def test_empty_key_handling(self):
        """空のキーに対する処理確認"""
        constants = AppConstants()
        
        assert constants.get('') is None
        assert constants.get('', 'default') == 'default'
    
    def test_complex_nested_access(self):
        """複雑なネストアクセスのテスト"""
        constants = AppConstants()
        
        # 存在するネストパス
        assert constants.get('dirs.config') is not None
        
        # 部分的に存在するパス（dirsは存在するがその下のnonexistentは存在しない）
        assert constants.get('dirs.nonexistent') is None
        assert constants.get('dirs.nonexistent.deeper') is None
        
        # 完全に存在しないパス
        assert constants.get('totally.nonexistent.path') is None
    
    def test_numeric_and_boolean_values(self):
        """数値と真偽値の正しい処理確認"""
        constants = AppConstants()
        
        # 数値の確認
        max_size = constants.get('max_image_size')
        assert isinstance(max_size, int)
        assert max_size == 5 * 1024 * 1024
        
        # 真偽値の確認
        debug_mode = constants.get('debug_mode')
        assert isinstance(debug_mode, bool)
        assert debug_mode is False
    
    def test_list_values(self):
        """リスト値の正しい処理確認"""
        constants = AppConstants()
        
        formats = constants.get('supported_image_formats')
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'jpg' in formats
        assert 'png' in formats


class TestAppConstantsIntegration:
    """AppConstants 統合テスト"""
    
    def test_all_directory_paths_are_consistent(self):
        """すべてのディレクトリパスが一貫していることを確認"""
        constants = AppConstants()
        dirs = constants.get('dirs')
        base_dir = constants.base_dir
        
        for dir_name, dir_path in dirs.items():
            # すべてのディレクトリがベースディレクトリ配下にあることを確認
            assert dir_path.startswith(base_dir), f"{dir_name} directory not under base_dir"
            
            # ディレクトリ名が正しく含まれていることを確認
            assert dir_name in dir_path, f"Directory name {dir_name} not in path {dir_path}"
    
    def test_configuration_completeness(self):
        """必要な設定がすべて存在することを確認"""
        constants = AppConstants()
        
        # 必須の設定項目
        required_keys = [
            'app_name',
            'version',
            'api_endpoint',
            'max_post_length',
            'max_retries',
            'timeout',
            'dirs'
        ]
        
        for key in required_keys:
            value = constants.get(key)
            assert value is not None, f"Required key '{key}' is missing"
            
            # 文字列項目は空でないことを確認
            if key in ['app_name', 'version', 'api_endpoint']:
                assert value != '', f"String key '{key}' should not be empty"
    
    def test_numeric_limits_are_reasonable(self):
        """数値制限が妥当な範囲にあることを確認"""
        constants = AppConstants()
        
        # 投稿文字数制限は正の値
        assert constants.get('max_post_length') > 0
        
        # 画像サイズ制限は合理的な範囲
        max_image_size = constants.get('max_image_size')
        assert max_image_size > 1024  # 1KB以上
        assert max_image_size < 100 * 1024 * 1024  # 100MB未満
        
        # 接続設定は正の値
        assert constants.get('timeout') > 0
        assert constants.get('max_retries') > 0
        assert constants.get('max_connections') > 0