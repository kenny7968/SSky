#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証サービスモジュール
"""

import wx # LoginDialog のために必要
import logging
import typing
from pubsub import pub # PyPubSub をインポート
from atproto_client import Session, SessionEvent # SDK の型をインポート

from gui.dialogs.login_dialog import LoginDialog
from core.auth.credential_manager import AuthCredentialManager
from core.client import BlueskyClient
from core.exceptions import AuthenticationError
from core import events

# ロガーの設定
logger = logging.getLogger(__name__)

class AuthService:
    """認証UIフロー・イベント管理専門クラス（リファクタリング版）
    
    責任:
    - 認証プロセスのフロー管理（ログイン、ログアウト、セッション管理）
    - 認証関連のUI操作（ダイアログ表示など）
    - 認証イベントの発行と伝播
    - セッション状態の変更監視
    """

    def __init__(self, client: BlueskyClient, credential_manager: AuthCredentialManager):
        """初期化
        
        Args:
            client (BlueskyClient): Blueskyクライアントインスタンス
            credential_manager (AuthCredentialManager): 認証情報管理インスタンス
        """
        self.client = client
        self.credential_manager = credential_manager

        # SDK のセッション変更イベントを購読
        if hasattr(self.client, 'on_session_change') and callable(self.client.on_session_change):
            # 実装されたセッションハンドラを登録
            self.client.on_session_change(self._handle_session_change)
            logger.debug("AuthService initialized and subscribed to session changes.")
        else:
            logger.warning("AuthService: client does not support on_session_change. Session saving might not work automatically.")


    def _handle_session_change(self, event: SessionEvent, session: Session) -> None:
        """セッション変更イベントを処理し、セッションの保存や更新を行う
        
        Args:
            event (SessionEvent): セッションイベントの種類
            session (Session): セッションオブジェクト
        """
        logger.info(f"Session change event received: {event}")
        
        # セッションの作成や更新の場合はセッションを保存
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            self._save_current_session(session)
    
    def _save_current_session(self, session: typing.Optional[Session] = None) -> bool:
        """現在のセッションを保存
        
        Args:
            session (Session, optional): セッションオブジェクト。Noneの場合はクライアントから取得。
            
        Returns:
            bool: 保存に成功した場合はTrue
        """
        try:
            # セッション文字列をエクスポート
            if hasattr(self.client, 'export_session_string') and callable(self.client.export_session_string):
                session_string = self.client.export_session_string()
                user_did = self.client.user_did if hasattr(self.client, 'user_did') else None
                
                # セッションが指定されている場合はそちらのDIDを使用
                if session and hasattr(session, 'did') and session.did:
                    user_did = session.did
                    
                if session_string and user_did:
                    logger.debug(f"Saving session for DID: {user_did}")
                    saved = self.credential_manager.save_encrypted_session(user_did, session_string)
                    if saved:
                        # セッション保存成功イベントを発行
                        pub.sendMessage(events.AUTH_SESSION_SAVED, did=user_did)
                        return True
                    else:
                        logger.warning(f"Failed to save session for DID: {user_did}")
                else:
                    logger.warning("Could not export session string or DID is missing. Session not saved.")
            else:
                logger.warning("AuthService: client does not support export_session_string.")
                
            return False
        except Exception as e:
            logger.error(f"Error saving session: {e}", exc_info=True)
            return False

    def show_login_dialog(self, parent_window: wx.Window) -> None:
        """ログインダイアログを表示し、入力があればログイン処理を試行
        
        Args:
            parent_window (wx.Window): 親ウィンドウ
        """
        # LoginDialog は wx.Dialog を継承しているので parent が必要
        dlg = LoginDialog(parent_window)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                username, password = dlg.get_credentials()
                if username and password:
                    # ログイン処理を非同期で実行するか、UIがブロックしないように注意
                    # ここでは同期的に呼び出す
                    self.perform_login(username, password)
                else:
                    # UI 関連のエラーメッセージはUI側で出すのが一般的
                    wx.MessageBox("ユーザー名とアプリパスワードを入力してください", "入力エラー", wx.OK | wx.ICON_ERROR, parent=parent_window)
        finally:
            dlg.Destroy()


    def perform_login(self, username: str, password: str) -> bool:
        """ユーザー名とパスワードでログインを実行
        
        Args:
            username (str): ユーザー名（ハンドル）
            password (str): パスワードまたはアプリパスワード
            
        Returns:
            bool: ログイン成功時はTrue、失敗時はFalse
        """
        logger.debug("Attempting login...")
        pub.sendMessage(events.AUTH_LOGIN_ATTEMPT) # ログイン試行イベント
        try:
            # login メソッドが client に存在するか確認
            if hasattr(self.client, 'login') and callable(self.client.login):
                profile = self.client.login(username, password)
                logger.info(f"Login successful for handle: {profile.handle}")
                
                # セッションを保存
                self._save_current_session()
                
                # ログイン成功ダイアログを表示
                wx.MessageBox(f"{profile.handle}としてログインしました", "ログイン成功", wx.OK | wx.ICON_INFORMATION)
                
                # ログイン成功イベントを発行 (プロファイル情報を渡す)
                pub.sendMessage(events.AUTH_LOGIN_SUCCESS, profile=profile)
                return True
            else:
                 logger.error("AuthService: client does not support login method.")
                 pub.sendMessage(events.AUTH_LOGIN_FAILURE, error=NotImplementedError("Login method not available"))
                 return False

        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            # ログイン失敗イベントを発行 (エラー情報を渡す)
            pub.sendMessage(events.AUTH_LOGIN_FAILURE, error=e)
            return False

    def perform_logout(self) -> bool:
        """ログアウト処理を実行
        
        クライアントの状態をリセットし、保存されたセッションを削除します。
        
        Returns:
            bool: ログアウト成功時はTrue、失敗時はFalse
        """
        # client.me や client.profile など、ログイン中のユーザー情報を取得する方法を確認
        current_profile = getattr(self.client, 'profile', None) # 例: client.profile に情報があると仮定

        if current_profile and hasattr(current_profile, 'did'):
            user_did = current_profile.did
            handle = getattr(current_profile, 'handle', 'N/A')
            logger.info(f"Logging out user: {handle} ({user_did})")

            try:
                # SDKに明示的なログアウトがない場合、内部状態をリセット
                # 例: self.client.session = None など
                # ここではセッション削除のみ行う
                if hasattr(self.client, 'session'): # セッション情報をクリア
                    self.client.session = None
                if hasattr(self.client, 'profile'): # プロファイル情報もクリア
                    self.client.profile = None

                # セッション情報を永続化ストアから削除
                deleted = self.credential_manager.delete_session(user_did)
                if deleted:
                    logger.info(f"Session deleted for DID: {user_did}")
                    pub.sendMessage(events.AUTH_SESSION_DELETED, did=user_did)
                else:
                    logger.warning(f"Session for DID {user_did} not found or failed to delete.")

                # ログアウト成功イベントを発行
                pub.sendMessage(events.AUTH_LOGOUT_SUCCESS)
                return True
            except Exception as e:
                 logger.error(f"Error during logout: {e}", exc_info=True)
                 # 必要であればログアウト失敗イベントを発行
                 # pub.sendMessage(events.AUTH_LOGOUT_FAILURE, error=e)
                 return False
        else:
            logger.warning("Logout requested but not logged in or profile info unavailable.")
            # ログアウト状態であることを示すイベントを発行しても良い
            pub.sendMessage(events.AUTH_LOGOUT_SUCCESS) # すでにログアウトしている場合も成功として扱う
            return False

    def login_with_session(self, session_string: typing.Union[str, bytes], user_did: str) -> bool:
        """保存されたセッション文字列を使用してログインを試行
        
        Args:
            session_string (str|bytes): セッション文字列（復号化済み）
            user_did (str): ユーザーDID
            
        Returns:
            bool: ログイン成功時はTrue、失敗時はFalse
        """
        logger.debug(f"Attempting login with session for DID: {user_did}")
        pub.sendMessage(events.AUTH_SESSION_LOAD_ATTEMPT, did=user_did)
        try:
            # login メソッドが session_string を受け付けるか確認
            if hasattr(self.client, 'login') and callable(self.client.login):
                 # login メソッドのシグネチャを確認 session_string がキーワード引数か確認
                 # profile = self.client.login(session_string=session_string) # atproto SDK の場合
                 # BlueskyClient の実装に依存
                 profile = self.client.login_with_session(session_string) # BlueskyClient のメソッド名と仮定

                 logger.info(f"Login with session successful for handle: {profile.handle}")
                 # セッションログイン成功イベントを発行
                 pub.sendMessage(events.AUTH_SESSION_LOAD_SUCCESS, profile=profile)
                 return True
            else:
                 logger.error("AuthService: client does not support login with session method.")
                 pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=NotImplementedError("Login with session method not available"), needs_relogin=True)
                 return False

        except Exception as e:
            logger.error(f"Login with session failed for DID {user_did}: {e}", exc_info=True)
            # セッションが無効だった可能性が高い
            pub.sendMessage(events.AUTH_SESSION_INVALID, error=e, did=user_did)

            # 無効なセッション情報を削除
            deleted = self.credential_manager.delete_session(user_did)
            if deleted:
                logger.info(f"Invalid session deleted for DID: {user_did}")
                pub.sendMessage(events.AUTH_SESSION_DELETED, did=user_did)

            # セッションログイン失敗イベントを発行
            pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=e, needs_relogin=True)
            return False

    def load_and_login(self) -> bool:
        """保存されたセッションを読み込み、ログインを試行
        
        アプリケーション起動時などに自動ログインを試みる際に使用します。
        
        Returns:
            bool: ログイン成功時はTrue、失敗時はFalse
        """
        logger.debug("Attempting to load session from store...")
        try:
            session_data, user_did = self.credential_manager.load_encrypted_session()
            if session_data and user_did:
                logger.info(f"Session data found for DID: {user_did}. Attempting login.")

                # session_data が文字列であることを期待 (BlueskyClient.login_with_session が文字列を要求する場合)
                # AuthManager.load_session が返す型を確認する必要がある
                if isinstance(session_data, str):
                    session_string = session_data
                elif isinstance(session_data, bytes): # バイト列の場合デコード試行
                     try:
                         session_string = session_data.decode('latin-1') # または適切なエンコーディング
                         logger.debug("Session data decoded from bytes.")
                     except Exception as decode_error:
                         logger.error(f"Failed to decode session data: {decode_error}")
                         pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=decode_error, needs_relogin=True)
                         return False
                else:
                    logger.error(f"Loaded session data is not a string or bytes: type={type(session_data)}")
                    pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=TypeError("Invalid session data type"), needs_relogin=True)
                    return False


                # セッションでログイン試行
                return self.login_with_session(session_string, user_did)
            else:
                logger.info("No session found in store.")
                # セッションが見つからなかった場合のイベント
                pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=None, needs_relogin=False)
                return False

        except Exception as e:
            logger.error(f"Failed to load and login with session: {e}", exc_info=True)
            pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=e, needs_relogin=True)
            return False
