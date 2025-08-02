#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証情報管理クラス（リファクタリング版）
"""

import logging
import typing
from utils.crypto import encrypt_data, decrypt_data
from core.data_store import DataStore

logger = logging.getLogger(__name__)

class AuthCredentialManager:
    """認証情報の暗号化・永続化専門クラス（シングルトン）
    
    責任:
    - セッション情報の暗号化/復号化
    - セッション情報の永続的な保存/読み込み/削除
    - データストアへのアクセス抽象化
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(AuthCredentialManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初期化（一度だけ実行）"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.data_store = DataStore()
        logger.debug("AuthCredentialManager initialized with DataStore.")

    def save_encrypted_session(self, user_did: str, session_data: typing.Union[str, bytes]) -> bool:
        """セッション情報を暗号化して保存
        
        Args:
            user_did (str): ユーザーのDID
            session_data (str|bytes): セッションデータ
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            logger.info(f"セッション情報を保存します: {user_did}")
            logger.debug(f"保存するセッションデータ: 型={type(session_data)}, 長さ={len(session_data) if hasattr(session_data, '__len__') else 'N/A'}")

            # セッションデータを暗号化
            encrypted_session = encrypt_data(session_data)
            if not encrypted_session:
                logger.error("セッションデータの暗号化に失敗しました")
                return False

            logger.debug(f"暗号化されたセッションデータ: 型={type(encrypted_session)}, 長さ={len(encrypted_session) if encrypted_session else 'None'}")

            # データストアに保存
            result = self.data_store.save_session(user_did, encrypted_session)
            if result:
                logger.info(f"セッション情報を保存しました: {user_did}")
            else:
                logger.error(f"データストアへのセッション情報の保存に失敗しました: {user_did}")
            return result
        except Exception as e:
            logger.error(f"セッション情報の保存に失敗しました: {str(e)}", exc_info=True)
            return False

    def load_encrypted_session(self) -> typing.Tuple[typing.Optional[typing.Union[str, bytes]], typing.Optional[str]]:
        """セッション情報を読み込み、復号化して返す
        
        Returns:
            tuple: (session_data, user_did)のタプル。情報がない場合は(None, None)
        """
        try:
            # データストアから最新のセッション情報を取得
            user_did, encrypted_session = self.data_store.get_latest_session()

            if user_did and encrypted_session:
                logger.info(f"最新のセッション情報を取得しました: {user_did}")
                logger.debug(f"暗号化されたセッションデータ: 型={type(encrypted_session)}, 長さ={len(encrypted_session) if encrypted_session else 'None'}")

                # 暗号化されたセッションデータを復号化
                session_data = decrypt_data(encrypted_session)
                if session_data:
                    logger.info(f"最新のセッション情報を復号化しました: {user_did}")
                    logger.debug(f"復号化されたセッションデータ: 型={type(session_data)}, 長さ={len(session_data) if hasattr(session_data, '__len__') else 'N/A'}")
                    return session_data, user_did
                else:
                    logger.error("セッションデータの復号化に失敗しました")
                    return None, None
            else:
                logger.debug("セッション情報が見つかりませんでした")
                return None, None

        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}", exc_info=True)
            return None, None

    def delete_session(self, user_did: str) -> bool:
        """セッション情報を削除
        
        Args:
            user_did (str): ユーザーのDID
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            result = self.data_store.delete_session(user_did)
            if result:
                logger.info(f"セッション情報を削除しました: {user_did}")
            else:
                logger.warning(f"セッション情報の削除に失敗したか、対象が存在しませんでした: {user_did}")
            return result
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}", exc_info=True)
            return False