#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証情報管理クラス（Phase 3 依存性注入対応版）
"""

import logging
import typing
from utils.crypto import encrypt_data, decrypt_data
from core.data_store import DataStore

logger = logging.getLogger(__name__)

class AuthCredentialManager:
    """認証情報の暗号化・永続化専門クラス（依存性注入対応）
    
    責任:
    - セッション情報の暗号化/復号化
    - セッション情報の永続的な保存/読み込み/削除
    - データストアへのアクセス抽象化
    
    Phase 3変更点:
    - シングルトンパターンを削除
    - データストアを外部から注入可能に変更
    - 暗号化関数も注入可能に変更（テスト性向上）
    """

    def __init__(self, data_store: DataStore = None, encrypt_func: typing.Callable = None, decrypt_func: typing.Callable = None):
        """初期化（依存性注入対応）
        
        Args:
            data_store: データストアインスタンス（未指定時はデフォルト作成）
            encrypt_func: 暗号化関数（テスト時のモック用）
            decrypt_func: 復号化関数（テスト時のモック用）
        """
        self.data_store = data_store or DataStore()
        self.encrypt_func = encrypt_func or encrypt_data
        self.decrypt_func = decrypt_func or decrypt_data
        logger.debug("AuthCredentialManager initialized with dependency injection support.")

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

            # セッションデータを暗号化（依存性注入された関数を使用）
            encrypted_session = self.encrypt_func(session_data)
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

                # 暗号化されたセッションデータを復号化（依存性注入された関数を使用）
                session_data = self.decrypt_func(encrypted_session)
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

    # Phase 3 追加: convenience メソッド
    def save_credentials(self, username: str, password: str, session_data: typing.Dict = None) -> bool:
        """認証情報を便利なフォーマットで保存
        
        Args:
            username: ユーザー名
            password: パスワード
            session_data: セッション情報辞書
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            import json
            
            # 認証情報を辞書形式で組み立て
            credentials = {
                'username': username,
                'password': password,
                'session_data': session_data or {},
                'created_at': str(typing.cast(typing.Any, __import__('datetime')).datetime.now())
            }
            
            # JSON文字列に変換して保存
            credentials_json = json.dumps(credentials)
            return self.save_encrypted_session(username, credentials_json)
            
        except Exception as e:
            logger.error(f"認証情報の保存に失敗しました: {str(e)}", exc_info=True)
            return False

    def get_stored_credentials(self) -> typing.Optional[typing.Dict]:
        """保存された認証情報を取得
        
        Returns:
            dict: 認証情報辞書、存在しない場合はNone
        """
        try:
            import json
            
            session_data, user_did = self.load_encrypted_session()
            if session_data:
                # JSON文字列から辞書に変換
                if isinstance(session_data, bytes):
                    session_data = session_data.decode('utf-8')
                
                credentials = json.loads(session_data)
                credentials['user_did'] = user_did
                return credentials
            
            return None
            
        except Exception as e:
            logger.error(f"認証情報の取得に失敗しました: {str(e)}", exc_info=True)
            return None

    def clear_credentials(self) -> bool:
        """すべての認証情報をクリア
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # 最新のセッション情報を取得してから削除
            _, user_did = self.load_encrypted_session()
            if user_did:
                return self.delete_session(user_did)
            
            logger.debug("削除対象のセッション情報が存在しませんでした")
            return True
            
        except Exception as e:
            logger.error(f"認証情報のクリアに失敗しました: {str(e)}", exc_info=True)
            return False