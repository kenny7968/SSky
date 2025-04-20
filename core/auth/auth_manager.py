#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証マネージャーモジュール
"""

import logging
from utils.crypto import encrypt_data, decrypt_data
from core.data_store import DataStore

# ロガーの設定
logger = logging.getLogger(__name__)

class AuthManager:
    """認証情報の管理クラス"""
    
    def __init__(self, data_store=None):
        """初期化
        
        Args:
            data_store (DataStore, optional): データストアインスタンス。
                指定しない場合は新しいインスタンスを作成。
        """
        self.data_store = data_store if data_store else DataStore()
    
    def save_credentials(self, username, password):
        """ログイン情報を保存
        
        Args:
            username (str): ユーザー名
            password (str): パスワード
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            logger.debug(f"ログイン情報を保存します: {username}")
            
            # パスワードを暗号化
            encrypted_password = encrypt_data(password)
            if not encrypted_password:
                logger.error("パスワードの暗号化に失敗しました")
                return False
            
            logger.debug("パスワードの暗号化が完了しました")
            
            # データストアに保存
            return self.data_store.save_credentials(username, encrypted_password)
                
        except Exception as e:
            logger.error(f"ログイン情報の保存に失敗しました: {str(e)}", exc_info=True)
            return False
    
    def load_credentials(self):
        """ログイン情報を読み込み
        
        Returns:
            tuple: (username, password)のタプル。情報がない場合は(None, None)
        """
        try:
            # データストアからログイン情報を取得
            username, encrypted_password = self.data_store.load_credentials()
            
            if username and encrypted_password:
                logger.debug(f"ログイン情報を取得しました: {username}")
                
                # 暗号化されたパスワードを復号化
                password = decrypt_data(encrypted_password)
                if password:
                    logger.debug("パスワードの復号化が完了しました")
                    return username, password
                else:
                    logger.error("パスワードの復号化に失敗しました")
                    return None, None
            else:
                logger.debug("ログイン情報が見つかりませんでした")
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
            # データストアからログイン情報を削除
            return self.data_store.delete_credentials()
        except Exception as e:
            logger.error(f"ログイン情報の削除に失敗しました: {str(e)}")
            return False
            
    def save_session(self, user_did, session_data):
        """セッション情報を保存
        
        Args:
            user_did (str): ユーザーのDID
            session_data (object): セッションデータ
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # セッションデータを暗号化
            encrypted_session = encrypt_data(session_data)
            if not encrypted_session:
                logger.error("セッションデータの暗号化に失敗しました")
                return False
                
            # データストアに保存
            return self.data_store.save_session(user_did, encrypted_session)
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗しました: {str(e)}")
            return False
            
    def load_session(self, user_did):
        """セッション情報を読み込み
        
        Args:
            user_did (str): ユーザーのDID
            
        Returns:
            object: セッションデータ。情報がない場合はNone
        """
        try:
            # データストアからセッション情報を取得
            encrypted_session = self.data_store.load_session(user_did)
            
            if encrypted_session:
                # 暗号化されたセッションデータを復号化
                session_data = decrypt_data(encrypted_session)
                if session_data:
                    logger.debug(f"セッション情報を復号化しました: {user_did}")
                    return session_data
                else:
                    logger.error("セッションデータの復号化に失敗しました")
                    return None
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
            # データストアからセッション情報を削除
            return self.data_store.delete_session(user_did)
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}")
            return False
