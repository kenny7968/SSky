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
            
    def load_session(self):
        """セッション情報を読み込み
        
        Returns:
            tuple: (session_data, user_did)のタプル。情報がない場合は(None, None)
        """
        try:
            # データストアから最新のセッション情報を取得
            user_did, encrypted_session = self.data_store.get_latest_session()
            
            if user_did and encrypted_session:
                # 暗号化されたセッションデータを復号化
                session_data = decrypt_data(encrypted_session)
                if session_data:
                    logger.debug(f"最新のセッション情報を復号化しました: {user_did}")
                    # セキュリティ上の理由からセッション文字列の内容はログに出力しない
                    logger.debug("セッション文字列を復号化しました（セキュリティ上の理由から内容は表示しません）")
                    return session_data, user_did
                else:
                    logger.error("セッションデータの復号化に失敗しました")
                    return None, None
            else:
                logger.debug("セッション情報が見つかりませんでした")
                return None, None
                
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}")
            return None, None
    
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
