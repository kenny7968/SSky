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
    """認証情報の管理クラス（シングルトン）"""

    _instance = None # シングルトンインスタンス

    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(AuthManager, cls).__new__(cls)
            cls._instance._initialized = False # 初期化フラグを追加
        return cls._instance

    def __init__(self):
        """初期化（一度だけ実行）"""
        if hasattr(self, '_initialized') and self._initialized: # 初期化済みかチェック
            return
        self._initialized = True # 初期化フラグを立てる
        self.data_store = DataStore() # 常に新しいDataStoreを作成（シングルトンなので一度だけ）
        logger.debug("AuthManager initialized with DataStore.") # デバッグログ追加

    def save_session(self, user_did, session_data):
        """セッション情報を保存

        Args:
            user_did (str): ユーザーのDID
            session_data (object): セッションデータ

        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # セッションデータの情報をログに出力
            logger.info(f"セッション情報を保存します: {user_did}")
            logger.debug(f"保存するセッションデータ: 型={type(session_data)}, 長さ={len(session_data) if hasattr(session_data, '__len__') else 'N/A'}")
            # logger.debug(f"セッションデータの内容: {session_data}") # 機密情報を含む可能性があるためコメントアウト推奨

            # セッションデータを暗号化
            encrypted_session = encrypt_data(session_data)
            if not encrypted_session:
                logger.error("セッションデータの暗号化に失敗しました")
                return False

            logger.debug(f"暗号化されたセッションデータ: 型={type(encrypted_session)}, 長さ={len(encrypted_session) if encrypted_session else 'None'}")
            # logger.debug(f"暗号化されたセッションデータの内容: {encrypted_session}") # 暗号化されていてもログ出力は慎重に

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

    def load_session(self):
        """セッション情報を読み込み

        Returns:
            tuple: (session_data, user_did)のタプル。情報がない場合は(None, None)
        """
        try:
            # データストアから最新のセッション情報を取得
            user_did, encrypted_session = self.data_store.get_latest_session()

            if user_did and encrypted_session:
                logger.info(f"最新のセッション情報を取得しました: {user_did}")
                logger.debug(f"暗号化されたセッションデータ: 型={type(encrypted_session)}, 長さ={len(encrypted_session) if encrypted_session else 'None'}")
                # logger.debug(f"暗号化されたセッションデータの内容: {encrypted_session}") # 暗号化されていてもログ出力は慎重に

                # 暗号化されたセッションデータを復号化
                session_data = decrypt_data(encrypted_session)
                if session_data:
                    logger.info(f"最新のセッション情報を復号化しました: {user_did}")
                    logger.debug(f"復号化されたセッションデータ: 型={type(session_data)}, 長さ={len(session_data) if hasattr(session_data, '__len__') else 'N/A'}")
                    # logger.debug(f"復号化されたセッションデータの内容: {session_data}") # 機密情報を含む可能性があるためコメントアウト推奨
                    return session_data, user_did
                else:
                    logger.error("セッションデータの復号化に失敗しました")
                    # 復号化失敗時はセッションを削除するなどの対応も検討可能
                    # self.delete_session(user_did)
                    return None, None
            else:
                logger.debug("セッション情報が見つかりませんでした")
                return None, None

        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}", exc_info=True)
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
            result = self.data_store.delete_session(user_did)
            if result:
                logger.info(f"セッション情報を削除しました: {user_did}")
            else:
                logger.warning(f"セッション情報の削除に失敗したか、対象が存在しませんでした: {user_did}")
            return result # DataStoreの戻り値をそのまま返す
        except Exception as e:
            logger.error(f"セッション情報の削除に失敗しました: {str(e)}", exc_info=True) # エラー詳細をログに
            return False
