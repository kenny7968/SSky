#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
データベース モッククラス

テスト用のSQLiteデータベース操作をシミュレートするモッククラス群
"""

import sqlite3
import tempfile
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, ContextManager
from unittest.mock import MagicMock, Mock, patch
from contextlib import contextmanager


class DatabaseMockData:
    """データベースモックデータ生成クラス"""
    
    @staticmethod
    def generate_session_data(handle: str, **kwargs) -> Dict[str, Any]:
        """セッションデータ生成"""
        return {
            "handle": handle,
            "access_jwt": kwargs.get("access_jwt", f"access_token_{handle}"),
            "refresh_jwt": kwargs.get("refresh_jwt", f"refresh_token_{handle}"),
            "did": kwargs.get("did", f"did:plc:{handle.replace('.', '')}"),
            "created_at": kwargs.get("created_at", datetime.utcnow().isoformat()),
            "expires_at": kwargs.get("expires_at", None)
        }
    
    @staticmethod
    def generate_credentials_data(handle: str, **kwargs) -> Dict[str, Any]:
        """認証情報データ生成"""
        return {
            "handle": handle,
            "encrypted_data": kwargs.get("encrypted_data", f"encrypted_{handle}_data"),
            "created_at": kwargs.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": kwargs.get("updated_at", datetime.utcnow().isoformat())
        }
    
    @staticmethod
    def generate_settings_data(**kwargs) -> Dict[str, Any]:
        """設定データ生成"""
        default_settings = {
            "timeline_refresh_interval": 30,
            "max_posts_display": 100,
            "enable_notifications": True,
            "theme": "default",
            "language": "ja",
            "auto_fetch_enabled": False,
            "fetch_count": 50
        }
        
        default_settings.update(kwargs)
        return default_settings


class MemoryDatabaseMock:
    """メモリ内SQLiteデータベースモック"""
    
    def __init__(self, **config):
        self.config = config
        self.connection = None
        self.is_initialized = False
        self.transaction_level = 0
        self.enable_errors = config.get("enable_errors", False)
        self.error_rate = config.get("error_rate", 0.0)
        
        # 操作カウンター
        self.operation_count = {
            "select": 0,
            "insert": 0,
            "update": 0,
            "delete": 0,
            "transaction": 0
        }
        
        self._initialize_database()
    
    def _initialize_database(self):
        """データベース初期化"""
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        
        # テーブル作成
        self._create_tables()
        self.is_initialized = True
    
    def _create_tables(self):
        """テーブル作成"""
        cursor = self.connection.cursor()
        
        # sessionsテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                handle TEXT NOT NULL,
                access_jwt TEXT,
                refresh_jwt TEXT,
                did TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        """)
        
        # credentialsテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                handle TEXT UNIQUE NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # settingsテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # schema_versionテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
    
    def _check_error_simulation(self):
        """エラーシミュレーション"""
        if self.enable_errors and self.error_rate > 0:
            import random
            if random.random() < self.error_rate:
                raise sqlite3.DatabaseError("Simulated database error")
    
    @contextmanager
    def get_connection(self):
        """接続コンテキストマネージャー"""
        if not self.is_initialized:
            self._initialize_database()
        
        try:
            self._check_error_simulation()
            yield self.connection
        except Exception as e:
            self.connection.rollback()
            raise
    
    @contextmanager
    def transaction(self):
        """トランザクションコンテキストマネージャー"""
        self.operation_count["transaction"] += 1
        self.transaction_level += 1
        
        try:
            self._check_error_simulation()
            
            if self.transaction_level == 1:
                self.connection.execute("BEGIN")
            
            yield self.connection
            
            if self.transaction_level == 1:
                self.connection.commit()
                
        except Exception as e:
            if self.transaction_level == 1:
                self.connection.rollback()
            raise
        finally:
            self.transaction_level -= 1
    
    def save_session(self, connection, handle: str, access_jwt: str, 
                    refresh_jwt: str, did: str, expires_at: str = None):
        """セッション保存"""
        self.operation_count["insert"] += 1
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (handle, access_jwt, refresh_jwt, did, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (handle, access_jwt, refresh_jwt, did, expires_at))
        
        connection.commit()
        return cursor.lastrowid
    
    def get_latest_session(self, connection, handle: str) -> Optional[Dict[str, Any]]:
        """最新セッション取得"""
        self.operation_count["select"] += 1
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE handle = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (handle,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_session(self, connection, session_id: int):
        """セッション削除"""
        self.operation_count["delete"] += 1
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        connection.commit()
        return cursor.rowcount
    
    def save_credentials(self, connection, handle: str, encrypted_data: str):
        """認証情報保存"""
        self.operation_count["insert"] += 1
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO credentials (handle, encrypted_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (handle, encrypted_data))
        
        connection.commit()
        return cursor.lastrowid
    
    def get_credentials(self, connection, handle: str = None) -> Union[List[Dict], Optional[Dict]]:
        """認証情報取得"""
        self.operation_count["select"] += 1
        cursor = connection.cursor()
        
        if handle:
            cursor.execute("""
                SELECT * FROM credentials WHERE handle = ?
            """, (handle,))
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor.execute("SELECT * FROM credentials ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_credentials(self, connection, handle: str = None):
        """認証情報削除"""
        self.operation_count["delete"] += 1
        cursor = connection.cursor()
        
        if handle:
            cursor.execute("DELETE FROM credentials WHERE handle = ?", (handle,))
        else:
            cursor.execute("DELETE FROM credentials")
        
        connection.commit()
        return cursor.rowcount
    
    def save_setting(self, connection, key: str, value: str):
        """設定保存"""
        self.operation_count["insert"] += 1
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        connection.commit()
        return cursor.lastrowid
    
    def get_setting(self, connection, key: str) -> Optional[str]:
        """設定取得"""
        self.operation_count["select"] += 1
        cursor = connection.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_all_settings(self, connection) -> Dict[str, str]:
        """全設定取得"""
        self.operation_count["select"] += 1
        cursor = connection.cursor()
        
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    def get_schema_version(self, connection) -> int:
        """スキーマバージョン取得"""
        self.operation_count["select"] += 1
        cursor = connection.cursor()
        
        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0
        except sqlite3.OperationalError:
            return 0
    
    def update_schema_version(self, connection, version: int):
        """スキーマバージョン更新"""
        self.operation_count["insert"] += 1
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version)
            VALUES (?)
        """, (version,))
        
        connection.commit()
    
    def populate_test_data(self):
        """テストデータ投入"""
        with self.get_connection() as conn:
            # テストセッション
            test_sessions = [
                DatabaseMockData.generate_session_data("test1.user"),
                DatabaseMockData.generate_session_data("test2.user"),
                DatabaseMockData.generate_session_data("test3.user")
            ]
            
            for session_data in test_sessions:
                self.save_session(conn, **session_data)
            
            # テスト認証情報
            test_credentials = [
                DatabaseMockData.generate_credentials_data("test1.user"),
                DatabaseMockData.generate_credentials_data("test2.user")
            ]
            
            for cred_data in test_credentials:
                self.save_credentials(conn, **cred_data)
            
            # テスト設定
            test_settings = DatabaseMockData.generate_settings_data()
            for key, value in test_settings.items():
                self.save_setting(conn, key, str(value))
    
    def clear_all_data(self):
        """全データクリア"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions")
            cursor.execute("DELETE FROM credentials")
            cursor.execute("DELETE FROM settings")
            conn.commit()
    
    def get_operation_count(self, operation: str) -> int:
        """操作回数取得"""
        return self.operation_count.get(operation, 0)
    
    def reset_counters(self):
        """カウンターリセット"""
        self.operation_count = {key: 0 for key in self.operation_count}
    
    def close(self):
        """データベース接続クローズ"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.is_initialized = False


class DatabaseErrorSimulator:
    """データベースエラーシミュレーター"""
    
    def __init__(self):
        self.error_scenarios = {
            "connection_timeout": sqlite3.OperationalError("Database connection timeout"),
            "table_locked": sqlite3.OperationalError("Database table is locked"),
            "disk_full": sqlite3.OperationalError("Database disk is full"),
            "corrupted": sqlite3.DatabaseError("Database file is corrupted"),
            "permission_denied": sqlite3.OperationalError("Permission denied"),
            "constraint_violation": sqlite3.IntegrityError("Constraint violation")
        }
    
    def simulate_error(self, error_type: str):
        """エラーシミュレーション実行"""
        if error_type in self.error_scenarios:
            raise self.error_scenarios[error_type]
        else:
            raise sqlite3.Error(f"Simulated error: {error_type}")
    
    @contextmanager
    def inject_error(self, error_type: str, probability: float = 1.0):
        """エラー注入コンテキスト"""
        import random
        
        if random.random() < probability:
            self.simulate_error(error_type)
        
        yield


class FileDatabaseMock:
    """ファイルベースデータベースモック（一時ファイル使用）"""
    
    def __init__(self, **config):
        self.config = config
        self.temp_file = None
        self.connection = None
        self.is_initialized = False
        
        self._create_temp_database()
    
    def _create_temp_database(self):
        """一時データベースファイル作成"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_file.close()
        
        self.connection = sqlite3.connect(self.temp_file.name)
        self.connection.row_factory = sqlite3.Row
        
        # メモリデータベースと同様のテーブル作成
        memory_mock = MemoryDatabaseMock()
        memory_mock.connection = self.connection
        memory_mock._create_tables()
        
        self.is_initialized = True
    
    @contextmanager
    def get_connection(self):
        """接続コンテキストマネージャー"""
        if not self.is_initialized:
            self._create_temp_database()
        
        try:
            yield self.connection
        except Exception as e:
            self.connection.rollback()
            raise
    
    def get_file_path(self) -> str:
        """データベースファイルパス取得"""
        return self.temp_file.name if self.temp_file else None
    
    def close(self):
        """データベース接続クローズとファイル削除"""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        if self.temp_file:
            try:
                os.unlink(self.temp_file.name)
            except (OSError, FileNotFoundError):
                pass
            self.temp_file = None
        
        self.is_initialized = False


class DatabaseMockFactory:
    """データベースモックファクトリー"""
    
    @staticmethod
    def create_memory_mock(**config) -> MemoryDatabaseMock:
        """メモリデータベースモック作成"""
        return MemoryDatabaseMock(**config)
    
    @staticmethod
    def create_file_mock(**config) -> FileDatabaseMock:
        """ファイルデータベースモック作成"""
        return FileDatabaseMock(**config)
    
    @staticmethod
    def create_error_simulator() -> DatabaseErrorSimulator:
        """エラーシミュレーター作成"""
        return DatabaseErrorSimulator()
    
    @staticmethod
    def create_performance_mock(delay: float = 0.0, **config) -> MemoryDatabaseMock:
        """パフォーマンステスト用モック作成"""
        mock = MemoryDatabaseMock(**config)
        
        # 遅延追加
        if delay > 0:
            original_connection = mock.get_connection
            
            @contextmanager
            def delayed_connection():
                time.sleep(delay)
                with original_connection() as conn:
                    yield conn
            
            mock.get_connection = delayed_connection
        
        return mock
    
    @staticmethod
    def create_integration_mock(populate_data: bool = True, **config) -> MemoryDatabaseMock:
        """統合テスト用モック作成"""
        mock = MemoryDatabaseMock(**config)
        
        if populate_data:
            mock.populate_test_data()
        
        return mock