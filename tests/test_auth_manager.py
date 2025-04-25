#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証マネージャーのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.auth.auth_manager import AuthManager
from core.data_store import DataStore

class TestAuthManager(unittest.TestCase):
    """認証マネージャーのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # DataStoreのモックを作成
        self.mock_data_store = MagicMock(spec=DataStore)
        
        # AuthManagerのインスタンスを作成
        self.auth_manager = AuthManager(data_store=self.mock_data_store)
    
    @patch('core.auth.auth_manager.encrypt_data')
    def test_save_session(self, mock_encrypt):
        """save_sessionのテスト"""
        # モックの戻り値を設定
        mock_encrypt.return_value = b'encrypted_data'
        self.mock_data_store.save_session.return_value = True
        
        # テスト実行
        user_did = 'did:plc:test_user'
        session_data = 'session_data'
        result = self.auth_manager.save_session(user_did, session_data)
        
        # モックが正しく呼ばれたか確認
        mock_encrypt.assert_called_once_with(session_data)
        self.mock_data_store.save_session.assert_called_once_with(user_did, b'encrypted_data')
        
        # 結果の確認
        self.assertTrue(result)
    
    @patch('core.auth.auth_manager.encrypt_data')
    def test_save_session_encryption_failure(self, mock_encrypt):
        """暗号化失敗時のsave_sessionのテスト"""
        # モックの戻り値を設定
        mock_encrypt.return_value = None  # 暗号化失敗
        
        # テスト実行
        user_did = 'did:plc:test_user'
        session_data = 'session_data'
        result = self.auth_manager.save_session(user_did, session_data)
        
        # モックが正しく呼ばれたか確認
        mock_encrypt.assert_called_once_with(session_data)
        self.mock_data_store.save_session.assert_not_called()
        
        # 結果の確認
        self.assertFalse(result)
    
    @patch('core.auth.auth_manager.decrypt_data')
    def test_load_session(self, mock_decrypt):
        """load_sessionのテスト"""
        # モックの戻り値を設定
        self.mock_data_store.get_latest_session.return_value = ('did:plc:test_user', b'encrypted_data')
        mock_decrypt.return_value = 'session_data'
        
        # テスト実行
        session_data, user_did = self.auth_manager.load_session()
        
        # モックが正しく呼ばれたか確認
        self.mock_data_store.get_latest_session.assert_called_once()
        mock_decrypt.assert_called_once_with(b'encrypted_data')
        
        # 結果の確認
        self.assertEqual(session_data, 'session_data')
        self.assertEqual(user_did, 'did:plc:test_user')
    
    @patch('core.auth.auth_manager.decrypt_data')
    def test_load_session_no_data(self, mock_decrypt):
        """セッションデータがない場合のload_sessionのテスト"""
        # モックの戻り値を設定
        self.mock_data_store.get_latest_session.return_value = (None, None)
        
        # テスト実行
        session_data, user_did = self.auth_manager.load_session()
        
        # モックが正しく呼ばれたか確認
        self.mock_data_store.get_latest_session.assert_called_once()
        mock_decrypt.assert_not_called()
        
        # 結果の確認
        self.assertIsNone(session_data)
        self.assertIsNone(user_did)
    
    @patch('core.auth.auth_manager.decrypt_data')
    def test_load_session_decryption_failure(self, mock_decrypt):
        """復号化失敗時のload_sessionのテスト"""
        # モックの戻り値を設定
        self.mock_data_store.get_latest_session.return_value = ('did:plc:test_user', b'encrypted_data')
        mock_decrypt.return_value = None  # 復号化失敗
        
        # テスト実行
        session_data, user_did = self.auth_manager.load_session()
        
        # モックが正しく呼ばれたか確認
        self.mock_data_store.get_latest_session.assert_called_once()
        mock_decrypt.assert_called_once_with(b'encrypted_data')
        
        # 結果の確認
        self.assertIsNone(session_data)
        self.assertIsNone(user_did)
    
    def test_delete_session(self):
        """delete_sessionのテスト"""
        # モックの戻り値を設定
        self.mock_data_store.delete_session.return_value = True
        
        # テスト実行
        user_did = 'did:plc:test_user'
        result = self.auth_manager.delete_session(user_did)
        
        # モックが正しく呼ばれたか確認
        self.mock_data_store.delete_session.assert_called_once_with(user_did)
        
        # 結果の確認
        self.assertTrue(result)
    
    def test_delete_session_failure(self):
        """削除失敗時のdelete_sessionのテスト"""
        # モックの戻り値を設定
        self.mock_data_store.delete_session.return_value = False
        
        # テスト実行
        user_did = 'did:plc:test_user'
        result = self.auth_manager.delete_session(user_did)
        
        # モックが正しく呼ばれたか確認
        self.mock_data_store.delete_session.assert_called_once_with(user_did)
        
        # 結果の確認
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
