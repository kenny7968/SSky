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

# ロガーの設定
logger = logging.getLogger(__name__)

class DataStore:
    """データ永続化クラス"""
    
    def __init__(self, db_path=None):
        """初期化
        
        Args:
            db_path (str, optional): データベースファイルのパス。
                指定しない場合はデフォルトのパスを使用。
        """
        if db_path is None:
            # デフォルトのデータベースパス
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, 'ssky_data.db')
        else:
            self.db_path = db_path
            
        # データベースの初期化
        self._init_db()
        
    def _init_db(self):
        """データベースの初期化"""
        try:
            # データベースが存在しない場合は作成
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # テーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            sessions_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            users_exists = cursor.fetchone() is not None
            
            # 必要なテーブルが存在しない場合は、バージョン情報をリセット
            if not sessions_exists or not users_exists:
                logger.warning("必要なテーブルが存在しません。データベースを再初期化します。")
                # バージョン管理テーブルが存在する場合は削除
                cursor.execute("DROP TABLE IF EXISTS db_version")
                current_version = 0
            else:
                # バージョン管理テーブルの作成
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER,
                    updated_at TIMESTAMP
                )
                ''')
                
                # 現在のバージョンを確認
                cursor.execute("SELECT version FROM db_version ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                current_version = result[0] if result else 0
            
            # バージョン管理テーブルの作成（再作成の場合もある）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_version (
                id INTEGER PRIMARY KEY,
                version INTEGER,
                updated_at TIMESTAMP
            )
            ''')
            
            # バージョンに応じてマイグレーション
            if current_version < 1:
                self._migrate_to_v1(cursor)
                
            conn.commit()
            conn.close()
            logger.info("データベースの初期化が完了しました")
        except Exception as e:
            logger.error(f"データベースの初期化に失敗しました: {str(e)}")
            raise
            
    def _migrate_to_v1(self, cursor):
        """バージョン1へのマイグレーション
        
        Args:
            cursor: データベースカーソル
        """
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
                # credentialsテーブルが存在する場合は削除
                cursor.execute("DROP TABLE credentials")
                logger.info("credentialsテーブルを削除しました。ユーザーは再ログインが必要です。")
            
            # 既存のsessionsテーブルがあるか確認（古い形式）
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
            
            # バージョン情報を更新
            cursor.execute(
                "INSERT INTO db_version (version, updated_at) VALUES (?, ?)",
                (1, datetime.now().isoformat())
            )
            
            logger.info("データベースをバージョン1に更新しました")
        except Exception as e:
            logger.error(f"バージョン1へのマイグレーションに失敗しました: {str(e)}")
            raise
            
    def save_session(self, user_did, encrypted_session):
        """セッション情報を保存
        
        Args:
            user_did (str): ユーザーのDID
            encrypted_session (bytes): 暗号化されたセッション情報
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            logger.debug(f"セッション情報を保存します: {user_did}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ユーザー情報を保存または更新
            cursor.execute(
                "INSERT OR IGNORE INTO users (did, created_at, updated_at) VALUES (?, ?, ?)",
                (user_did, datetime.now().isoformat(), datetime.now().isoformat())
            )
            
            # ユーザーが既に存在する場合は更新
            cursor.execute(
                "UPDATE users SET updated_at = ? WHERE did = ?",
                (datetime.now().isoformat(), user_did)
            )
            
            # ユーザーIDを取得
            cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
            user_id = cursor.fetchone()[0]
            
            # 既存のセッション情報を削除
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            # 新しいセッション情報を保存
            cursor.execute(
                "INSERT INTO sessions (user_id, encrypted_session, created_at) VALUES (?, ?, ?)",
                (user_id, encrypted_session, datetime.now().isoformat())
            )
            
            conn.commit()
            conn.close()
            logger.info(f"セッション情報を保存しました: {user_did}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗しました: {str(e)}")
            return False
            
    def load_session(self, user_did):
        """セッション情報を読み込み
        
        Args:
            user_did (str): ユーザーのDID
            
        Returns:
            bytes: 暗号化されたセッション情報。情報がない場合はNone
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ユーザーIDを取得
            cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
            result = cursor.fetchone()
            
            if not result:
                logger.debug(f"ユーザーが見つかりませんでした: {user_did}")
                conn.close()
                return None
                
            user_id = result[0]
            
            # セッション情報を取得
            cursor.execute(
                "SELECT encrypted_session FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
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
            
    def delete_session(self, user_did):
        """セッション情報を削除
        
        Args:
            user_did (str): ユーザーのDID
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ユーザーIDを取得
            cursor.execute("SELECT id FROM users WHERE did = ?", (user_did,))
            result = cursor.fetchone()
            
            if not result:
                logger.debug(f"ユーザーが見つかりませんでした: {user_did}")
                conn.close()
                return True  # ユーザーが存在しない場合は成功とみなす
                
            user_id = result[0]
            
            # セッション情報を削除
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"セッション情報を削除しました: {user_did}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}")
            return False
            
    def get_latest_session(self):
        """最新のセッション情報を取得
        
        Returns:
            tuple: (user_did, encrypted_session)のタプル。情報がない場合は(None, None)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 最新のセッション情報を取得
            cursor.execute("""
                SELECT u.did, s.encrypted_session 
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.created_at DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
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
