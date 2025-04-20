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
            
            # sessionsテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_did TEXT,
                encrypted_session BLOB,
                created_at TIMESTAMP
            )
            ''')
            
            # credentialsテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                username TEXT,
                encrypted_password BLOB,
                created_at TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("データベースの初期化が完了しました")
        except Exception as e:
            logger.error(f"データベースの初期化に失敗しました: {str(e)}")
            raise
            
    def save_credentials(self, username, encrypted_password):
        """ログイン情報を保存
        
        Args:
            username (str): ユーザー名
            encrypted_password (bytes): 暗号化されたパスワード
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            logger.debug(f"ログイン情報を保存します: {username}")
            
            # データベースに保存
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 既存のログイン情報を削除
                cursor.execute("DELETE FROM credentials")
                
                # 新しいログイン情報を保存
                cursor.execute(
                    "INSERT INTO credentials (username, encrypted_password, created_at) VALUES (?, ?, ?)",
                    (username, encrypted_password, datetime.now().isoformat())
                )
                
                conn.commit()
                conn.close()
                logger.info(f"ログイン情報を保存しました: {username}")
                return True
            except sqlite3.Error as sqle:
                logger.error(f"データベース操作に失敗しました: {str(sqle)}", exc_info=True)
                return False
                
        except Exception as e:
            logger.error(f"ログイン情報の保存に失敗しました: {str(e)}", exc_info=True)
            return False
            
    def load_credentials(self):
        """ログイン情報を読み込み
        
        Returns:
            tuple: (username, encrypted_password)のタプル。
                   情報がない場合は(None, None)
        """
        try:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 最新のログイン情報を取得
                logger.debug("ログイン情報を取得します")
                cursor.execute(
                    "SELECT username, encrypted_password FROM credentials ORDER BY created_at DESC LIMIT 1"
                )
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    username, encrypted_password = result
                    logger.debug(f"ログイン情報を取得しました: {username}")
                    return username, encrypted_password
                else:
                    logger.debug("ログイン情報が見つかりませんでした")
                    return None, None
                
            except sqlite3.Error as sqle:
                logger.error(f"データベース操作に失敗しました: {str(sqle)}", exc_info=True)
                return None, None
                
        except Exception as e:
            logger.error(f"ログイン情報の読み込みに失敗しました: {str(e)}", exc_info=True)
            return None, None
            
    def delete_credentials(self):
        """ログイン情報を削除
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # すべてのログイン情報を削除
            cursor.execute("DELETE FROM credentials")
            
            conn.commit()
            conn.close()
            logger.info("ログイン情報を削除しました")
            return True
        except Exception as e:
            logger.error(f"ログイン情報の削除に失敗しました: {str(e)}")
            return False
            
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
            
            # 既存のセッション情報を削除
            cursor.execute("DELETE FROM sessions WHERE user_did = ?", (user_did,))
            
            # 新しいセッション情報を保存
            cursor.execute(
                "INSERT INTO sessions (user_did, encrypted_session, created_at) VALUES (?, ?, ?)",
                (user_did, encrypted_session, datetime.now().isoformat())
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
            
            # セッション情報を取得
            cursor.execute(
                "SELECT encrypted_session FROM sessions WHERE user_did = ? ORDER BY created_at DESC LIMIT 1",
                (user_did,)
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
            
            # セッション情報を削除
            cursor.execute("DELETE FROM sessions WHERE user_did = ?", (user_did,))
            
            conn.commit()
            conn.close()
            logger.info(f"セッション情報を削除しました: {user_did}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}")
            return False
