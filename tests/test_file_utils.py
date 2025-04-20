#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ファイル操作ユーティリティのテスト
"""

import unittest
from unittest.mock import patch, mock_open
import os
import sys
import tempfile
import shutil

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.file_utils import ensure_directory_exists, get_mime_type, read_binary_file, get_file_size

class TestFileUtils(unittest.TestCase):
    """ファイル操作ユーティリティのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_file.txt')
        
        # テスト用ファイルを作成
        with open(self.test_file_path, 'w') as f:
            f.write('test content')
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_directory_exists_new(self):
        """新しいディレクトリの作成テスト"""
        # 新しいディレクトリのパス
        new_dir = os.path.join(self.temp_dir, 'new_dir')
        
        # ディレクトリが存在しないことを確認
        self.assertFalse(os.path.exists(new_dir))
        
        # テスト実行
        result = ensure_directory_exists(new_dir)
        
        # 結果の確認
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
    
    def test_ensure_directory_exists_existing(self):
        """既存のディレクトリの確認テスト"""
        # テスト実行
        result = ensure_directory_exists(self.temp_dir)
        
        # 結果の確認
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.isdir(self.temp_dir))
    
    @patch('os.makedirs')
    def test_ensure_directory_exists_error(self, mock_makedirs):
        """ディレクトリ作成エラーのテスト"""
        # モックが例外を発生させる
        mock_makedirs.side_effect = Exception('Directory creation error')
        
        # テスト実行
        result = ensure_directory_exists('/invalid/path')
        
        # 結果の確認
        self.assertFalse(result)
    
    def test_get_mime_type(self):
        """MIMEタイプ取得のテスト"""
        # テスト実行
        result = get_mime_type(self.test_file_path)
        
        # 結果の確認
        self.assertEqual(result, 'text/plain')
    
    def test_get_mime_type_unknown(self):
        """不明なMIMEタイプのテスト"""
        # 拡張子のないファイルパス
        unknown_file = os.path.join(self.temp_dir, 'unknown_file')
        
        # テスト実行
        result = get_mime_type(unknown_file)
        
        # 結果の確認
        self.assertEqual(result, 'application/octet-stream')
    
    def test_read_binary_file(self):
        """バイナリファイル読み込みのテスト"""
        # テスト実行
        result = read_binary_file(self.test_file_path)
        
        # 結果の確認
        self.assertEqual(result, b'test content')
    
    @patch('builtins.open', side_effect=Exception('File read error'))
    def test_read_binary_file_error(self, mock_open):
        """ファイル読み込みエラーのテスト"""
        # テスト実行
        result = read_binary_file('/invalid/path')
        
        # 結果の確認
        self.assertIsNone(result)
    
    def test_get_file_size(self):
        """ファイルサイズ取得のテスト"""
        # テスト実行
        result = get_file_size(self.test_file_path)
        
        # 結果の確認
        self.assertEqual(result, 12)  # 'test content'の長さ
    
    def test_get_file_size_error(self):
        """ファイルサイズ取得エラーのテスト"""
        # テスト実行
        result = get_file_size('/invalid/path')
        
        # 結果の確認
        self.assertEqual(result, -1)

if __name__ == '__main__':
    unittest.main()
