#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
暗号化ユーティリティのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.crypto import encrypt_data, decrypt_data

class TestCrypto(unittest.TestCase):
    """暗号化ユーティリティのテストクラス"""
    
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data_string(self, mock_protect):
        """文字列データの暗号化テスト"""
        # モックの戻り値を設定
        mock_protect.return_value = b'encrypted_data'
        
        # テスト実行
        test_data = 'test_data'
        result = encrypt_data(test_data)
        
        # モックが正しく呼ばれたか確認
        # 文字列がUTF-8でエンコードされていることを確認
        mock_protect.assert_called_once_with(b'test_data', None, None, None, None, 0)
        
        # 結果の確認
        self.assertEqual(result, b'encrypted_data')
    
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data_bytes(self, mock_protect):
        """バイト列データの暗号化テスト"""
        # モックの戻り値を設定
        mock_protect.return_value = b'encrypted_data'
        
        # テスト実行
        test_data = b'test_data'
        result = encrypt_data(test_data)
        
        # モックが正しく呼ばれたか確認
        # バイト列がそのまま使用されていることを確認
        mock_protect.assert_called_once_with(b'test_data', None, None, None, None, 0)
        
        # 結果の確認
        self.assertEqual(result, b'encrypted_data')
    
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data_unsupported_type(self, mock_protect):
        """サポートされていない型の暗号化テスト"""
        # テスト実行
        test_data = 123  # 整数型はサポートされていない
        result = encrypt_data(test_data)
        
        # モックが呼ばれていないことを確認
        mock_protect.assert_not_called()
        
        # 結果の確認
        self.assertIsNone(result)
        
    @patch('utils.crypto.win32crypt.CryptUnprotectData')
    def test_decrypt_data_utf8(self, mock_unprotect):
        """UTF-8でデコード可能なデータの復号化テスト"""
        # モックの戻り値を設定
        mock_unprotect.return_value = (None, 'test_data'.encode('utf-8'))
        
        # テスト実行
        result = decrypt_data(b'encrypted_data')
        
        # モックが正しく呼ばれたか確認
        mock_unprotect.assert_called_once_with(b'encrypted_data', None, None, None, 0)
        
        # 結果の確認
        self.assertEqual(result, 'test_data')
    
    @patch('utils.crypto.win32crypt.CryptUnprotectData')
    def test_decrypt_data_latin1(self, mock_unprotect):
        """UTF-8でデコードできないがLatin-1でデコード可能なデータの復号化テスト"""
        # UTF-8でデコードできないバイト列を作成
        invalid_utf8 = bytes([0x80, 0x81, 0x82])  # UTF-8では無効なバイト列
        
        # モックの戻り値を設定
        mock_unprotect.return_value = (None, invalid_utf8)
        
        # テスト実行
        result = decrypt_data(b'encrypted_data')
        
        # モックが正しく呼ばれたか確認
        mock_unprotect.assert_called_once_with(b'encrypted_data', None, None, None, 0)
        
        # 結果の確認
        self.assertEqual(result, invalid_utf8.decode('latin-1'))
    
    @patch('utils.crypto.win32crypt.CryptUnprotectData')
    def test_decrypt_data_error(self, mock_unprotect):
        """復号化エラーのテスト"""
        # モックが例外を発生させる
        mock_unprotect.side_effect = Exception('Decryption error')
        
        # テスト実行
        result = decrypt_data(b'encrypted_data')
        
        # 結果の確認
        self.assertIsNone(result)
        
    @patch('utils.crypto.win32crypt.CryptProtectData')
    def test_encrypt_data_error(self, mock_protect):
        """暗号化エラーのテスト"""
        # モックが例外を発生させる
        mock_protect.side_effect = Exception('Encryption error')
        
        # テスト実行
        result = encrypt_data('test_data')
        
        # 結果の確認
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
