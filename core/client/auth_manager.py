#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証管理を担当するクラス
"""

import logging
import typing
from atproto import Client as AtprotoClient
from atproto.exceptions import AtProtocolError
from core.exceptions import AuthenticationError

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyAuthManager:
    """認証処理を担当するクラス
    
    ログイン/ログアウト処理、セッション管理との連携を担当します。
    """
    
    def __init__(self, api_client=None, session_manager=None):
        """初期化
        
        Args:
            api_client (BlueskyApiClient, optional): APIクライアントインスタンス
            session_manager (BlueskySessionManager, optional): セッション管理インスタンス
        """
        self.api_client = api_client
        self.session_manager = session_manager
        self.profile = None
        self.is_logged_in = False
        self.user_did = None  # ログインユーザーのDIDを保持
        
    def login(self, username: str, password: str):
        """Blueskyにログイン
        
        Args:
            username (str): ユーザー名（例: username.bsky.social）
            password (str): アプリパスワード
            
        Returns:
            object: プロフィール情報。ログイン失敗時は例外が発生
            
        Raises:
            AtProtocolError: ログイン失敗時
            Exception: その他のエラー
        """
        try:
            logger.debug(f"ログイン試行: ユーザー名={username}")
            
            # ログイン試行
            self.profile = self.api_client.client.login(username, password)
            
            logger.debug(f"ログイン成功: プロフィール={self.profile.display_name}, セッション={type(self.api_client.client._session)}")
            
            # ユーザーDIDを保存
            self.user_did = self.api_client.client.me.did
            logger.debug(f"ユーザーDID: {self.user_did}")
            
            # ログイン状態を更新
            self.is_logged_in = True
            
            return self.profile
            
        except AtProtocolError as e:
            logger.error(f"Bluesky APIエラー: {str(e)}")
            self.is_logged_in = False
            raise
            
        except Exception as e:
            logger.error(f"ログイン処理中に例外が発生しました: {str(e)}", exc_info=True)
            self.is_logged_in = False
            raise
            
    def login_with_session(self, session_string: typing.Union[str, bytes]):
        """セッション情報を使用してログイン
        
        Args:
            session_string (str): セッション情報の文字列
            
        Returns:
            object: プロフィール情報。ログイン失敗時は例外が発生
            
        Raises:
            AuthenticationError: セッションが無効な場合
            Exception: その他のエラー
        """
        try:
            logger.debug(f"セッション情報を使用してログイン試行: 型={type(session_string)}")
            
            # セッション情報をそのまま使用（バイト列への変換なし）
            # atprotoライブラリが文字列を直接処理できるか試す
            try:
                # まず文字列のままで試す
                logger.debug("文字列のままでログイン試行")
                self.profile = self.api_client.client.login(session_string=session_string)
            except Exception as e:
                logger.debug(f"文字列でのログインに失敗: {str(e)}")
                
                # 文字列での試行が失敗した場合、バイト列に変換して再試行
                if isinstance(session_string, str):
                    logger.debug("セッション情報を文字列からバイト列に変換して再試行")
                    session_bytes = session_string.encode('utf-8')
                    self.profile = self.api_client.client.login(session_string=session_bytes)
                else:
                    # 既にバイト列の場合はそのまま使用
                    logger.debug("セッション情報はバイト列なのでそのまま使用")
                    self.profile = self.api_client.client.login(session_string=session_string)
            
            # ユーザーDIDを保存
            self.user_did = self.api_client.client.me.did
            logger.debug(f"ユーザーDID: {self.user_did}")
            
            # ログイン状態を更新
            self.is_logged_in = True
            
            logger.info(f"セッションを使用したログインに成功しました: {self.profile.handle}")
            return self.profile
                
        except Exception as e:
            logger.error(f"セッションを使用したログインに失敗しました: {str(e)}")
            self.is_logged_in = False
            self.profile = None
            raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
    
    def logout(self) -> bool:
        """ログアウト処理
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # クライアントをリセット
            self.api_client.client = AtprotoClient()
            self.profile = None
            self.is_logged_in = False
            
            logger.info("ログアウトしました")
            return True
            
        except Exception as e:
            logger.error(f"ログアウト処理中に例外が発生しました: {str(e)}")
            return False
    
    def export_session_string(self) -> typing.Optional[str]:
        """セッション情報を文字列としてエクスポート
        
        Returns:
            str: セッション情報の文字列。エクスポート失敗時はNone
        """
        if not self.is_logged_in:
            logger.error("セッション情報のエクスポートに失敗しました: ログインしていません")
            return None
            
        try:
            # セッション情報をエクスポート
            session_string = self.api_client.client.export_session_string()
            logger.info("セッション情報をエクスポートしました")
            logger.debug(f"エクスポートしたセッション情報: 型={type(session_string)}, 長さ={len(session_string) if session_string else 'None'}")
            return session_string
        except Exception as e:
            logger.error(f"セッション情報のエクスポートに失敗しました: {str(e)}", exc_info=True)
            return None
    
    def handle_api_error(self, error, operation_name="API操作"):
        """API呼び出し時のエラーを処理
        
        Args:
            error: 発生したエラー
            operation_name: 操作の名前（エラーメッセージ用）
            
        Returns:
            bool: 再ログインが必要な場合はTrue
        """
        if isinstance(error, AtProtocolError):
            # 認証エラーかどうかを確認
            if "auth" in str(error).lower() or "authentication" in str(error).lower():
                logger.error(f"{operation_name}中に認証エラーが発生しました: {str(error)}")
                
                # ログイン状態をリセット
                self.is_logged_in = False
                self.profile = None
                
                # 再ログインが必要
                return True
        
        # その他のエラー
        logger.error(f"{operation_name}中にエラーが発生しました: {str(error)}")
        return False