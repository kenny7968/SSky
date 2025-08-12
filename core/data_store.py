#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
データ永続化モジュール
"""

import os
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Tuple, Any, List, Dict, Union

# ロガーの設定
logger = logging.getLogger(__name__)

class MigrationManager:
    """データベースマイグレーション管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.current_version = 0
        self.target_version = 1  # 現在の最新バージョン
    
    def get_current_version(self, cursor: Any) -> int:
        """現在のデータベースバージョンを取得"""
        try:
            cursor.execute("SELECT version FROM db_version ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.OperationalError:
            # db_versionテーブルが存在しない場合
            return 0
    
    def create_version_table(self, cursor):
        """バージョン管理テーブルを作成"""
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS db_version (
            id INTEGER PRIMARY KEY,
            version INTEGER,
            updated_at TIMESTAMP
        )
        ''')
    
    def update_version(self, cursor, version: int):
        """バージョン情報を更新"""
        cursor.execute(
            "INSERT INTO db_version (version, updated_at) VALUES (?, ?)",
            (version, datetime.now().isoformat())
        )
        logger.info(f"データベースバージョンを{version}に更新しました")
    
    def migrate_to_v1(self, cursor):
        """バージョン1へのマイグレーション"""
        try:
            logger.info("データベースをバージョン1に更新しています...")
            
            # usersテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                did TEXT UNIQUE,
                handle TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            ''')
            
            # sessionsテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                encrypted_session BLOB,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # 既存のcredentialsテーブルがあるか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE credentials")
                logger.info("credentialsテーブルを削除しました。ユーザーは再ログインが必要です。")
            
            # 古い形式のsessionsテーブルの移行処理
            self._migrate_old_sessions_table(cursor)
            
            logger.info("データベースをバージョン1に更新しました")
        except Exception as e:
            logger.error(f"バージョン1へのマイグレーションに失敗しました: {str(e)}")
            raise
    
    def _migrate_old_sessions_table(self, cursor: Any) -> None:
        """古い形式のsessionsテーブルからの移行"""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        if cursor.fetchone():
            # テーブル構造を確認
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 古い形式のsessionsテーブルの場合
            if 'user_did' in columns and 'user_id' not in columns:
                # 一時テーブルにリネーム
                cursor.execute("ALTER TABLE sessions RENAME TO old_sessions")
                logger.info("古い形式のsessionsテーブルを一時テーブルにリネームしました")
                
                # 新しいsessionsテーブルを作成（上で既に作成済み）
                
                # 古いデータを移行
                cursor.execute("SELECT user_did, encrypted_session, created_at FROM old_sessions")
                old_sessions = cursor.fetchall()
                
                for user_did, encrypted_session, created_at in old_sessions:
                    # usersテーブルにユーザーを追加
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (did, created_at, updated_at) VALUES (?, ?, ?)",
                        (user_did, created_at, created_at)
                    )
                    
                    # ユーザーIDを取得
                    cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
                    user_id = cursor.fetchone()[0]
                    
                    # sessionsテーブルにセッションを追加
                    cursor.execute(
                        "INSERT INTO sessions (user_id, encrypted_session, created_at) VALUES (?, ?, ?)",
                        (user_id, encrypted_session, created_at)
                    )
                
                # 古いテーブルを削除
                cursor.execute("DROP TABLE old_sessions")
                logger.info("古いデータを新しいテーブル構造に移行しました")
    
    def run_migrations(self, cursor: Any) -> bool:
        """必要なマイグレーションを実行"""
        try:
            self.create_version_table(cursor)
            current_version = self.get_current_version(cursor)
            
            # テーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            sessions_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            users_exists = cursor.fetchone() is not None
            
            # 必要なテーブルが存在しない場合は、バージョン情報をリセット
            if not sessions_exists or not users_exists:
                logger.warning("必要なテーブルが存在しません。データベースを再初期化します。")
                cursor.execute("DELETE FROM db_version")
                current_version = 0
            
            # バージョンに応じてマイグレーション
            if current_version < 1:
                self.migrate_to_v1(cursor)
                self.update_version(cursor, 1)
            
            return True
        except Exception as e:
            logger.error(f"マイグレーション実行に失敗しました: {str(e)}")
            raise


class DataStore:
    """データ永続化クラス（Phase 3 依存性注入強化版）
    
    SQLiteを使用してセッション情報などのデータを永続化します。
    
    Phase 3変更点:
    - カスタム接続ファクトリ関数を注入可能
    - テスト時のメモリDB簡単使用
    - 設定可能なマイグレーション管理
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 connection_factory: Optional[callable] = None,
                 migration_manager: Optional['MigrationManager'] = None,
                 auto_init: bool = True):
        """初期化（依存性注入強化版）
        
        Args:
            db_path: データベースファイルのパス（未指定の場合はデフォルト）
            connection_factory: 接続作成関数（テスト時のモック用）
            migration_manager: マイグレーション管理インスタンス
            auto_init: 自動初期化フラグ（False時は手動で_init_db()呼び出し要）
        """
        if db_path is None:
            # デフォルトのデータベースパス
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, 'ssky_data.db')
        else:
            self.db_path = db_path
        
        # 接続ファクトリの注入（テスト時のモック対応）
        self.connection_factory = connection_factory or (lambda: sqlite3.connect(self.db_path))
        
        # マイグレーション管理の注入
        self.migration_manager = migration_manager or MigrationManager(self.db_path)
        
        # 自動初期化
        if auto_init:
            self._init_db()
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャー（依存性注入対応）"""
        conn = None
        try:
            # 注入された接続ファクトリを使用
            conn = self.connection_factory()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"データベース操作でエラーが発生しました: {str(e)}")
            raise
        finally:
            # メモリ内データベースの場合は接続を閉じない
            if conn and not hasattr(self, '_memory_conn'):
                conn.close()
    
    @contextmanager
    def get_transaction(self):
        """トランザクション付きデータベース接続のコンテキストマネージャー"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"トランザクション実行中にエラーが発生しました: {str(e)}")
                raise
        
    def _init_db(self):
        """データベースの初期化"""
        try:
            with self.get_transaction() as cursor:
                self.migration_manager.run_migrations(cursor)
            logger.info("データベースの初期化が完了しました")
        except Exception as e:
            logger.error(f"データベースの初期化に失敗しました: {str(e)}")
            raise

    # Phase 3 追加: ファクトリメソッド
    @classmethod
    def create_in_memory(cls, migration_manager: Optional['MigrationManager'] = None):
        """テスト用のメモリ内データベースを作成
        
        Args:
            migration_manager: カスタムマイグレーション管理（テスト用）
            
        Returns:
            DataStore: メモリ内データベースを使用するインスタンス
        """
        import sqlite3
        
        # 単一のメモリ内データベース接続を保持
        # check_same_thread=Falseにより、複数スレッドからアクセス可能
        memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
        
        # メモリ内データベース接続ファクトリ
        def memory_connection_factory():
            return memory_conn
        
        # メモリ用のマイグレーション管理（パスは使用されない）
        if migration_manager is None:
            migration_manager = MigrationManager(":memory:")
        
        instance = cls(
            db_path=":memory:",
            connection_factory=memory_connection_factory,
            migration_manager=migration_manager
        )
        
        # 接続を保持（closeメソッドで閉じるため）
        instance._memory_conn = memory_conn
        
        return instance
    
    @classmethod  
    def create_for_testing(cls, temp_path: str = None):
        """テスト用の一時データベースを作成
        
        Args:
            temp_path: 一時データベースのパス（未指定時は自動生成）
            
        Returns:
            DataStore: テスト用データベースを使用するインスタンス
        """
        import tempfile
        import os
        
        if temp_path is None:
            # 一時ファイルを作成
            fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='ssky_test_')
            os.close(fd)  # ファイルディスクリプタを閉じる
        
        return cls(db_path=temp_path)
    
    @classmethod
    def create_with_custom_migration(cls, db_path: str, custom_migrations: List[callable]):
        """カスタムマイグレーションを持つデータベースを作成
        
        Args:
            db_path: データベースファイルのパス
            custom_migrations: カスタムマイグレーション関数のリスト
            
        Returns:
            DataStore: カスタムマイグレーション対応インスタンス
        """
        # カスタムマイグレーション管理を作成
        custom_manager = MigrationManager(db_path)
        # custom_manager.custom_migrations = custom_migrations  # 実装に応じて調整
        
        return cls(
            db_path=db_path,
            migration_manager=custom_manager
        )
            
    def save_session(self, user_did: str, encrypted_session: bytes) -> bool:
        """セッション情報を保存
        
        Args:
            user_did: ユーザーのDID
            encrypted_session: 暗号化されたセッション情報
            
        Returns:
            成功した場合はTrue
        """
        try:
            logger.debug(f"セッション情報を保存します: {user_did}")
            
            with self.get_transaction() as cursor:
                # ユーザー情報を保存または更新
                now = datetime.now().isoformat()
                cursor.execute(
                    "INSERT OR IGNORE INTO users (did, created_at, updated_at) VALUES (?, ?, ?)",
                    (user_did, now, now)
                )
                
                # ユーザーが既に存在する場合は更新
                cursor.execute(
                    "UPDATE users SET updated_at = ? WHERE did = ?",
                    (now, user_did)
                )
                
                # ユーザーIDを取得
                cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
                user_result = cursor.fetchone()
                if not user_result:
                    raise ValueError(f"ユーザーの作成または取得に失敗しました: {user_did}")
                user_id = user_result[0]
                
                # 既存のセッション情報を削除
                cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                
                # 新しいセッション情報を保存
                cursor.execute(
                    "INSERT INTO sessions (user_id, encrypted_session, created_at) VALUES (?, ?, ?)",
                    (user_id, encrypted_session, now)
                )
            
            logger.info(f"セッション情報を保存しました: {user_did}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗しました: {str(e)}")
            return False
            
    def load_session(self, user_did: str) -> Optional[bytes]:
        """セッション情報を読み込み
        
        Args:
            user_did: ユーザーのDID
            
        Returns:
            暗号化されたセッション情報。情報がない場合はNone
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # ユーザーIDを取得
                cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
                result = cursor.fetchone()
                
                if not result:
                    logger.debug(f"ユーザーが見つかりませんでした: {user_did}")
                    return None
                    
                user_id = result[0]
                
                # セッション情報を取得
                cursor.execute(
                    "SELECT encrypted_session FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                    (user_id,)
                )
                
                result = cursor.fetchone()
                
                if result:
                    encrypted_session = result[0]
                    logger.debug(f"セッション情報を取得しました: {user_did}")
                    return encrypted_session
                else:
                    logger.debug(f"セッション情報が見つかりませんでした: {user_did}")
                    return None
                
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}")
            return None
            
    def delete_session(self, user_did: str) -> bool:
        """セッション情報を削除
        
        Args:
            user_did: ユーザーのDID
            
        Returns:
            成功した場合はTrue
        """
        try:
            with self.get_transaction() as cursor:
                # ユーザーIDを取得
                cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
                result = cursor.fetchone()
                
                if not result:
                    logger.debug(f"ユーザーが見つかりませんでした: {user_did}")
                    return True  # ユーザーが存在しない場合は成功とみなす
                    
                user_id = result[0]
                
                # セッション情報を削除
                cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            logger.info(f"セッション情報を削除しました: {user_did}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}")
            return False
            
    def get_latest_session(self) -> Tuple[Optional[str], Optional[bytes]]:
        """最新のセッション情報を取得
        
        Returns:
            (user_did, encrypted_session)のタプル。情報がない場合は(None, None)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 最新のセッション情報を取得
                cursor.execute("""
                    SELECT u.did, s.encrypted_session 
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    ORDER BY s.created_at DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                
                if result:
                    user_did, encrypted_session = result
                    logger.debug(f"最新のセッション情報を取得しました: {user_did}")
                    return user_did, encrypted_session
                else:
                    logger.debug("セッション情報が見つかりませんでした")
                    return None, None
                
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}")
            return None, None
    
    def close(self):
        """データベース接続をクローズ
        
        注: このクラスではコンテキストマネージャーを使用しているため、
        通常は明示的にcloseを呼ぶ必要はありません。
        テスト時のクリーンアップ用に提供されています。
        """
        # メモリ内データベースの場合は接続を閉じる
        if hasattr(self, '_memory_conn'):
            try:
                self._memory_conn.close()
                logger.debug("メモリ内データベース接続を閉じました")
            except Exception as e:
                logger.debug(f"メモリ内データベース接続のクローズ時にエラー: {e}")
        else:
            # 通常のファイルベースのデータベースの場合
            logger.debug("DataStore.close()が呼ばれました（no-op）")
