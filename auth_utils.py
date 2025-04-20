#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証ユーティリティ
"""

import os
import sqlite3
import pickle
import base64
import time
from datetime import datetime
import win32crypt
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class AuthUtils:
    """認証情報の管理クラス"""
    
    def __init__(self, db_path="ssky_data.db"):
        """初期化"""
        self.db_path = db_path
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
            
            conn.commit()
            conn.close()
            logger.info("データベースの初期化が完了しました")
        except Exception as e:
            logger.error(f"データベースの初期化に失敗しました: {str(e)}")
            raise
    
    def encrypt_data(self, data):
        """DPAPIを使用してデータを暗号化"""
        try:
            # デバッグ情報（機密データは含めない）
            logger.debug(f"暗号化前データの型: {type(data)}")
            
            # データをシリアライズ
            serialized_data = pickle.dumps(data)
            logger.debug(f"シリアライズ後データの長さ: {len(serialized_data)}")
            
            # DPAPIで暗号化
            encrypted_data = win32crypt.CryptProtectData(
                serialized_data,
                None,  # 説明（任意）
                None,  # エントロピー（任意）
                None,  # 予約済み
                None,  # プロンプトフラグ
                0      # フラグ
            )
            
            logger.debug(f"暗号化後データの型: {type(encrypted_data)}")
            
            return encrypted_data
        except Exception as e:
            logger.error(f"データの暗号化に失敗しました: {str(e)}", exc_info=True)
            return None
    
    def decrypt_data(self, encrypted_data):
        """DPAPIを使用して暗号化されたデータを復号化"""
        try:
            logger.debug(f"復号化前データの型: {type(encrypted_data)}")
            
            # DPAPIで復号化
            try:
                decrypted_data = win32crypt.CryptUnprotectData(
                    encrypted_data,
                    None,  # 説明（任意）
                    None,  # エントロピー（任意）
                    None,  # 予約済み
                    0      # フラグ
                )
                
                # デバッグ情報（機密データは含めない）
                logger.debug(f"復号化データの型: {type(decrypted_data)}")
                
                # 戻り値の構造を確認
                if isinstance(decrypted_data, tuple):
                    logger.debug(f"復号化データはタプル、長さ: {len(decrypted_data)}")
                    if len(decrypted_data) > 1:
                        # 通常の戻り値構造（タプルの2番目の要素にデータが含まれる）
                        data = decrypted_data[1]
                    else:
                        # 1要素のタプル
                        data = decrypted_data[0]
                else:
                    # タプル以外の戻り値
                    data = decrypted_data
                
                logger.debug(f"抽出したデータの型: {type(data)}")
                
                # デシリアライズ
                result = pickle.loads(data)
                logger.debug(f"デシリアライズ後データの型: {type(result)}")
                return result
                
            except ValueError as ve:
                logger.error(f"復号化データの構造が不正です: {str(ve)}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"データの復号化に失敗しました: {str(e)}", exc_info=True)
            return None
    
    def save_session(self, user_did, session_obj):
        """セッション情報を保存"""
        try:
            logger.debug(f"保存するセッションオブジェクトの型: {type(session_obj)}")
            
            # セッションオブジェクトを暗号化
            encrypted_session = self.encrypt_data(session_obj)
            if not encrypted_session:
                logger.error("セッションの暗号化に失敗しました")
                return False
            
            logger.debug("セッションの暗号化が完了しました")
            
            # データベースに保存
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 既存のセッションを削除
                cursor.execute("DELETE FROM sessions WHERE user_did = ?", (user_did,))
                
                # 新しいセッションを保存
                cursor.execute(
                    "INSERT INTO sessions (user_did, encrypted_session, created_at) VALUES (?, ?, ?)",
                    (user_did, encrypted_session, datetime.now().isoformat())
                )
                
                conn.commit()
                conn.close()
                logger.info(f"セッション情報を保存しました: {user_did}")
                return True
            except sqlite3.Error as sqle:
                logger.error(f"データベース操作に失敗しました: {str(sqle)}", exc_info=True)
                return False
                
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗しました: {str(e)}", exc_info=True)
            return False
    
    def load_session(self, user_did=None):
        """セッション情報を読み込み"""
        try:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                if user_did:
                    # 特定のユーザーのセッションを取得
                    logger.debug(f"ユーザーID {user_did} のセッションを取得します")
                    cursor.execute(
                        "SELECT encrypted_session FROM sessions WHERE user_did = ?",
                        (user_did,)
                    )
                else:
                    # 最新のセッションを取得
                    logger.debug("最新のセッションを取得します")
                    cursor.execute(
                        "SELECT encrypted_session FROM sessions ORDER BY created_at DESC LIMIT 1"
                    )
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    logger.debug("セッションデータを取得しました")
                    
                    # 暗号化されたセッションを復号化
                    session = self.decrypt_data(result[0])
                    if session:
                        logger.debug("セッションの復号化が完了しました")
                    return session
                else:
                    logger.debug("セッションデータが見つかりませんでした")
                
                return None
            except sqlite3.Error as sqle:
                logger.error(f"データベース操作に失敗しました: {str(sqle)}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}", exc_info=True)
            return None
    
    def delete_session(self, user_did=None):
        """セッション情報を削除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_did:
                # 特定のユーザーのセッションを削除
                cursor.execute("DELETE FROM sessions WHERE user_did = ?", (user_did,))
            else:
                # すべてのセッションを削除
                cursor.execute("DELETE FROM sessions")
            
            conn.commit()
            conn.close()
            logger.info(f"セッション情報を削除しました: {user_did if user_did else 'すべて'}")
            return True
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}")
            return False
