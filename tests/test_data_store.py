#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
データストアの単体テスト (Phase 1 リファクタリング版)
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.data_store import DataStore, MigrationManager


class TestDataStore(unittest.TestCase):
    """データストアの単体テストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # 一時ファイルを作成
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # テスト用データストアを初期化
        self.data_store = DataStore(self.db_path)
    
    def tearDown(self):
        """各テスト後のクリーンアップ"""
        # データストアを削除
        if hasattr(self, 'data_store'):
            del self.data_store
        
        # 一時ファイルを削除
        try:
            os.unlink(self.db_path)
        except (OSError, FileNotFoundError):
            pass
    
    def test_database_initialization(self):
        """データベース初期化のテスト"""
        # データベースファイルが作成されることを確認
        self.assertTrue(os.path.exists(self.db_path))
        
        # 必要なテーブルが作成されることを確認
        with self.data_store.get_connection() as conn:
            cursor = conn.cursor()
            
            # sessionsテーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            self.assertIsNotNone(cursor.fetchone(), "sessionsテーブルが作成されていません")
            
            # usersテーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone(), "usersテーブルが作成されていません")
            
            # db_versionテーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            self.assertIsNotNone(cursor.fetchone(), "db_versionテーブルが作成されていません")
    
    def test_save_and_load_session(self):
        """セッション保存と読み込みのテスト"""
        # テストデータ
        user_did = 'did:plc:test_user'
        session_data = b'encrypted_session_data'
        
        # セッション保存
        result = self.data_store.save_session(user_did, session_data)
        self.assertTrue(result, "セッションの保存に失敗しました")
        
        # セッション読み込み
        loaded_data = self.data_store.load_session(user_did)
        self.assertEqual(loaded_data, session_data, "読み込まれたセッションデータが一致しません")
    
    def test_session_update(self):
        """セッション更新のテスト"""
        user_did = 'did:plc:test_user'
        
        # 最初のセッション
        session_data1 = b'session_data_1'
        self.data_store.save_session(user_did, session_data1)
        
        # セッション更新
        session_data2 = b'session_data_2'
        self.data_store.save_session(user_did, session_data2)
        
        # 最新のセッションが取得されることを確認
        loaded_data = self.data_store.load_session(user_did)
        self.assertEqual(loaded_data, session_data2, "更新されたセッションデータが取得されません")
    
    def test_delete_session(self):
        """セッション削除のテスト"""
        user_did = 'did:plc:test_user'
        session_data = b'session_to_delete'
        
        # セッション保存
        self.data_store.save_session(user_did, session_data)
        
        # セッション削除
        result = self.data_store.delete_session(user_did)
        self.assertTrue(result, "セッションの削除に失敗しました")
        
        # セッションが削除されていることを確認
        loaded_data = self.data_store.load_session(user_did)
        self.assertIsNone(loaded_data, "セッションが削除されていません")
    
    def test_load_nonexistent_session(self):
        """存在しないセッションの読み込みテスト"""
        result = self.data_store.load_session('nonexistent_user')
        self.assertIsNone(result, "存在しないセッションでNoneが返されていません")
    
    def test_multiple_users(self):
        """複数ユーザーのセッション管理テスト"""
        # ユーザー1のセッション
        user1_did = 'did:plc:user1'
        user1_data = b'user1_session'
        self.data_store.save_session(user1_did, user1_data)
        
        # ユーザー2のセッション
        user2_did = 'did:plc:user2'
        user2_data = b'user2_session'
        self.data_store.save_session(user2_did, user2_data)
        
        # それぞれのセッションが正しく取得されることを確認
        loaded1 = self.data_store.load_session(user1_did)
        loaded2 = self.data_store.load_session(user2_did)
        
        self.assertEqual(loaded1, user1_data, "ユーザー1のセッションが正しく取得されません")
        self.assertEqual(loaded2, user2_data, "ユーザー2のセッションが正しく取得されません")
    
    def test_get_latest_session(self):
        """最新セッション取得のテスト"""
        # ユーザー1のセッション（先に保存）
        user1_did = 'did:plc:user1'
        user1_data = b'user1_session'
        self.data_store.save_session(user1_did, user1_data)
        
        # 少し待ってからユーザー2のセッション
        import time
        time.sleep(0.01)
        user2_did = 'did:plc:user2'
        user2_data = b'user2_session'
        self.data_store.save_session(user2_did, user2_data)
        
        # 最新セッション取得
        latest_did, latest_data = self.data_store.get_latest_session()
        
        # 最後に保存されたセッションが取得されることを確認
        self.assertEqual(latest_did, user2_did, "最新のユーザーDIDが取得されません")
        self.assertEqual(latest_data, user2_data, "最新のセッションデータが取得されません")
    
    def test_get_latest_session_empty(self):
        """空のデータベースでの最新セッション取得テスト"""
        latest_did, latest_data = self.data_store.get_latest_session()
        
        self.assertIsNone(latest_did, "空のデータベースでNoneが返されていません")
        self.assertIsNone(latest_data, "空のデータベースでNoneが返されていません")
    
    def test_connection_context_manager(self):
        """コネクションコンテキストマネージャーのテスト"""
        with self.data_store.get_connection() as conn:
            self.assertIsNotNone(conn, "コネクションが取得できません")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1, "データベース接続が正しく動作しません")
    
    def test_transaction_context_manager(self):
        """トランザクションコンテキストマネージャーのテスト"""
        user_did = 'did:plc:transaction_test'
        
        # トランザクション内でのデータ操作
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
            self.assertIsNotNone(result, "トランザクションがコミットされていません")
            self.assertEqual(result[0], user_did, "正しいデータがコミットされていません")


class TestMigrationManager(unittest.TestCase):
    """マイグレーションマネージャーの単体テストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # 一時ファイルを作成
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # テスト用マイグレーションマネージャー
        self.migration_manager = MigrationManager(self.db_path)
    
    def tearDown(self):
        """各テスト後のクリーンアップ"""
        # 一時ファイルを削除
        try:
            os.unlink(self.db_path)
        except (OSError, FileNotFoundError):
            pass
    
    def test_initial_version(self):
        """初期バージョンのテスト"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 初期バージョンは0であることを確認
            version = self.migration_manager.get_current_version(cursor)
            self.assertEqual(version, 0, "初期バージョンが0ではありません")
    
    def test_create_version_table(self):
        """バージョンテーブル作成のテスト"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # バージョンテーブル作成
            self.migration_manager.create_version_table(cursor)
            
            # テーブルが作成されたことを確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, "db_versionテーブルが作成されていません")
    
    def test_update_version(self):
        """バージョン更新のテスト"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # バージョンテーブル作成
            self.migration_manager.create_version_table(cursor)
            
            # バージョン更新
            new_version = 1
            self.migration_manager.update_version(cursor, new_version)
            
            # バージョンが更新されたことを確認
            updated_version = self.migration_manager.get_current_version(cursor)
            self.assertEqual(updated_version, new_version, "バージョンが正しく更新されていません")
    
    @patch('core.data_store.logger')
    def test_migrate_to_v1(self, mock_logger):
        """バージョン1へのマイグレーションテスト"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # マイグレーション実行
            self.migration_manager.migrate_to_v1(cursor)
            
            # 必要なテーブルが作成されたことを確認
            tables = ['users', 'sessions']
            for table_name in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                result = cursor.fetchone()
                self.assertIsNotNone(result, f"{table_name}テーブルが作成されていません")
            
            # ログが出力されることを確認
            self.assertTrue(mock_logger.info.called, "マイグレーション時にログが出力されていません")
    
    @patch('core.data_store.logger')
    def test_migrate_to_v1_with_old_credentials_table(self, mock_logger):
        """古いcredentialsテーブルがある場合のマイグレーションテスト"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 古いcredentialsテーブルを作成
            cursor.execute("CREATE TABLE credentials (id INTEGER PRIMARY KEY, data TEXT)")
            cursor.execute("INSERT INTO credentials (data) VALUES ('test_data')")
            conn.commit()
            
            # マイグレーション実行
            self.migration_manager.migrate_to_v1(cursor)
            
            # credentialsテーブルが削除されたことを確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
            result = cursor.fetchone()
            self.assertIsNone(result, "credentialsテーブルが削除されていません")
            
            # 削除のログが出力されることを確認
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            deletion_logged = any("credentialsテーブルを削除しました" in msg for msg in log_calls)
            self.assertTrue(deletion_logged, "credentialsテーブル削除のログが出力されていません")


if __name__ == '__main__':
    unittest.main(verbosity=2)