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

from core.data_store import DataStore, MigrationManager

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
        # データベース接続を確実に閉じる
        try:
            del self.data_store
        except:
            pass
        
        # 少し待ってからファイルを削除
        import time
        time.sleep(0.1)
        
        # データベースファイルを削除
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except:
            pass
        
        # 一時ディレクトリを削除
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_init_db(self):
        """データベース初期化のテスト"""
        # データベースファイルが作成されたことを確認
        self.assertTrue(os.path.exists(self.db_path))
        
        # テーブルが作成されたことを確認
        with self.data_store.get_connection() as conn:
            cursor = conn.cursor()
            
            # sessionsテーブルの確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            self.assertIsNotNone(cursor.fetchone())
            
            # usersテーブルの確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone())
            
            # db_versionテーブルの確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            self.assertIsNotNone(cursor.fetchone())
    
    
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
    
    def test_get_latest_session(self):
        """最新のセッション情報取得のテスト"""
        # テストデータを保存
        user_did1 = 'did:plc:test_user1'
        encrypted_session1 = b'encrypted_session1'
        self.data_store.save_session(user_did1, encrypted_session1)
        
        # 少し後に別のユーザーのセッションを保存
        import time
        time.sleep(0.1)
        user_did2 = 'did:plc:test_user2'
        encrypted_session2 = b'encrypted_session2'
        self.data_store.save_session(user_did2, encrypted_session2)
        
        # 最新のセッション情報を取得
        latest_did, latest_session = self.data_store.get_latest_session()
        
        # 最後に保存したセッションが取得されることを確認
        self.assertEqual(latest_did, user_did2)
        self.assertEqual(latest_session, encrypted_session2)
    
    def test_get_latest_session_empty(self):
        """空のデータベースから最新セッション取得のテスト"""
        # 空のデータベースから取得
        latest_did, latest_session = self.data_store.get_latest_session()
        
        # Noneが返されることを確認
        self.assertIsNone(latest_did)
        self.assertIsNone(latest_session)
    
    def test_session_update(self):
        """同一ユーザーのセッション更新のテスト"""
        # 初回セッション保存
        user_did = 'did:plc:test_user'
        encrypted_session1 = b'encrypted_session1'
        result1 = self.data_store.save_session(user_did, encrypted_session1)
        self.assertTrue(result1)
        
        # 同じユーザーで新しいセッションを保存
        encrypted_session2 = b'encrypted_session2'
        result2 = self.data_store.save_session(user_did, encrypted_session2)
        self.assertTrue(result2)
        
        # 新しいセッションが取得されることを確認
        loaded_session = self.data_store.load_session(user_did)
        self.assertEqual(loaded_session, encrypted_session2)
        
        # 古いセッションが上書きされていることを確認
        self.assertNotEqual(loaded_session, encrypted_session1)
    
    def test_database_migration(self):
        """データベースマイグレーションのテスト"""
        # データベースを初期化（すでにセットアップで実行済み）
        # マイグレーションが正常に完了していることを確認
        
        with self.data_store.get_connection() as conn:
            cursor = conn.cursor()
            
            # db_versionテーブルが存在することを確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            self.assertIsNotNone(cursor.fetchone())
            
            # バージョン情報が正しく設定されていることを確認
            cursor.execute("SELECT version FROM db_version ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 1)
    
    def test_migration_manager(self):
        """マイグレーションマネージャーのテスト"""
        # 新しいテスト用DBでマイグレーションマネージャーをテスト
        test_db_path = os.path.join(self.temp_dir, 'test_migration.db')
        migration_manager = MigrationManager(test_db_path)
        
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()
            
            # バージョンテーブル作成テスト
            migration_manager.create_version_table(cursor)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            self.assertIsNotNone(cursor.fetchone())
            
            # バージョン取得テスト
            current_version = migration_manager.get_current_version(cursor)
            self.assertEqual(current_version, 0)
            
            # バージョン更新テスト
            migration_manager.update_version(cursor, 1)
            updated_version = migration_manager.get_current_version(cursor)
            self.assertEqual(updated_version, 1)
    
    def test_connection_context_manager(self):
        """データベース接続コンテキストマネージャーのテスト"""
        # 正常な接続テスト
        with self.data_store.get_connection() as conn:
            self.assertIsNotNone(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_transaction_context_manager(self):
        """トランザクションコンテキストマネージャーのテスト"""
        user_did = 'did:plc:test_transaction'
        
        # 正常なトランザクションテスト
        with self.data_store.get_transaction() as cursor:
            cursor.execute(
                "INSERT INTO users (did, created_at, updated_at) VALUES (?, ?, ?)",
                (user_did, datetime.now().isoformat(), datetime.now().isoformat())
            )
        
        # データがコミットされていることを確認
        with self.data_store.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT did FROM users WHERE did = ?", (user_did,))
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], user_did)

if __name__ == '__main__':
    unittest.main()
