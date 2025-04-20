#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
暗号化ユーティリティのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import pickle
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.crypto import encrypt_data, decrypt_data

class TestCrypto(unittest.TestCase):
    """暗号化ユーティリティのテストクラス"""
    
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data(self, mock_protect):
        """encrypt_dataのテスト"""
        # モックの戻り値を設定
        mock_protect.return_value = b'encrypted_data'
        
        # テスト実行
        test_data = 'test_data'
        result = encrypt_data(test_data)
        
        # モックが正しく呼ばれたか確認
        mock_protect.assert_called_once()
        
        # 結果の確認
        self.assertEqual(result, b'encrypted_data')
        
    @patch('utils.crypto.win32crypt.CryptUnprotectData')
    @patch('utils.crypto.pickle.loads')
    def test_decrypt_data(self, mock_loads, mock_unprotect):
        """decrypt_dataのテスト"""
        # モックの戻り値を設定
        mock_unprotect.return_value = (None, b'decrypted_data')
        mock_loads.return_value = 'test_data'
        
        # テスト実行
        result = decrypt_data(b'encrypted_data')
        
        # モックが正しく呼ばれたか確認
        mock_unprotect.assert_called_once_with(b'encrypted_data', None, None, None, 0)
        mock_loads.assert_called_once_with(b'decrypted_data')
        
        # 結果の確認
        self.assertEqual(result, 'test_data')
        
    @patch('utils.crypto.win32crypt.CryptUnprotectData')
    def test_decrypt_data_error(self, mock_unprotect):
        """decrypt_dataのエラーケースのテスト"""
        # モックが例外を発生させる
        mock_unprotect.side_effect = Exception('Decryption error')
        
        # テスト実行
        result = decrypt_data(b'encrypted_data')
        
        # 結果の確認
        self.assertIsNone(result)
        
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data_error(self, mock_protect):
        """encrypt_dataのエラーケースのテスト"""
        # モックが例外を発生させる
        mock_protect.side_effect = Exception('Encryption error')
        
        # テスト実行
        result = encrypt_data('test_data')
        
        # 結果の確認
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
