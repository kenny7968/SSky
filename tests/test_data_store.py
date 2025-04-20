#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
データストアのテスト
"""

import unittest
import os
import sys
import tempfile
import sqlite3
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_store import DataStore

class TestDataStore(unittest.TestCase):
    """データストアのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_data.db')
        
        # テスト用のデータストアを作成
        self.data_store = DataStore(self.db_path)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # データベース接続を閉じる
        del self.data_store
        
        # データベースファイルを削除
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # 一時ディレクトリを削除
        os.rmdir(self.temp_dir)
    
    def test_init_db(self):
        """データベース初期化のテスト"""
        # データベースファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.db_path))
        
        # テーブルが作成されたことを確認
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # sessionsテーブルの確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        self.assertIsNotNone(cursor.fetchone())
        
        # credentialsテーブルの確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_save_and_load_credentials(self):
        """認証情報の保存と読み込みのテスト"""
        # テストデータ
        username = 'test_user'
        encrypted_password = b'encrypted_password'
        
        # 保存
        result = self.data_store.save_credentials(username, encrypted_password)
        self.assertTrue(result)
        
        # 読み込み
        loaded_username, loaded_password = self.data_store.load_credentials()
        self.assertEqual(loaded_username, username)
        self.assertEqual(loaded_password, encrypted_password)
    
    def test_delete_credentials(self):
        """認証情報の削除のテスト"""
        # テストデータを保存
        username = 'test_user'
        encrypted_password = b'encrypted_password'
        self.data_store.save_credentials(username, encrypted_password)
        
        # 削除
        result = self.data_store.delete_credentials()
        self.assertTrue(result)
        
        # 読み込み - 削除されているはず
        loaded_username, loaded_password = self.data_store.load_credentials()
        self.assertIsNone(loaded_username)
        self.assertIsNone(loaded_password)
    
    def test_load_credentials_empty(self):
        """空のデータベースからの認証情報読み込みのテスト"""
        # 読み込み
        loaded_username, loaded_password = self.data_store.load_credentials()
        self.assertIsNone(loaded_username)
        self.assertIsNone(loaded_password)
    
    def test_save_and_load_session(self):
        """セッション情報の保存と読み込みのテスト"""
        # テストデータ
        user_did = 'did:plc:test_user'
        encrypted_session = b'encrypted_session'
        
        # 保存
        result = self.data_store.save_session(user_did, encrypted_session)
        self.assertTrue(result)
        
        # 読み込み
        loaded_session = self.data_store.load_session(user_did)
        self.assertEqual(loaded_session, encrypted_session)
    
    def test_delete_session(self):
        """セッション情報の削除のテスト"""
        # テストデータを保存
        user_did = 'did:plc:test_user'
        encrypted_session = b'encrypted_session'
        self.data_store.save_session(user_did, encrypted_session)
        
        # 削除
        result = self.data_store.delete_session(user_did)
        self.assertTrue(result)
        
        # 読み込み - 削除されているはず
        loaded_session = self.data_store.load_session(user_did)
        self.assertIsNone(loaded_session)
    
    def test_load_session_empty(self):
        """空のデータベースからのセッション情報読み込みのテスト"""
        # 読み込み
        loaded_session = self.data_store.load_session('did:plc:test_user')
        self.assertIsNone(loaded_session)
    
    def test_multiple_credentials(self):
        """複数の認証情報の保存と最新の読み込みのテスト"""
        # 1つ目のテストデータを保存
        username1 = 'test_user1'
        encrypted_password1 = b'encrypted_password1'
        self.data_store.save_credentials(username1, encrypted_password1)
        
        # 2つ目のテストデータを保存
        username2 = 'test_user2'
        encrypted_password2 = b'encrypted_password2'
        self.data_store.save_credentials(username2, encrypted_password2)
        
        # 読み込み - 最新のデータが取得されるはず
        loaded_username, loaded_password = self.data_store.load_credentials()
        self.assertEqual(loaded_username, username2)
        self.assertEqual(loaded_password, encrypted_password2)
    
    def test_multiple_sessions(self):
        """複数のセッション情報の保存と読み込みのテスト"""
        # 1つ目のテストデータを保存
        user_did1 = 'did:plc:test_user1'
        encrypted_session1 = b'encrypted_session1'
        self.data_store.save_session(user_did1, encrypted_session1)
        
        # 2つ目のテストデータを保存
        user_did2 = 'did:plc:test_user2'
        encrypted_session2 = b'encrypted_session2'
        self.data_store.save_session(user_did2, encrypted_session2)
        
        # 読み込み - それぞれのユーザーのデータが取得されるはず
        loaded_session1 = self.data_store.load_session(user_did1)
        self.assertEqual(loaded_session1, encrypted_session1)
        
        loaded_session2 = self.data_store.load_session(user_did2)
        self.assertEqual(loaded_session2, encrypted_session2)

if __name__ == '__main__':
    unittest.main()
