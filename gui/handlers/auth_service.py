#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証サービスモジュール
"""

import wx # LoginDialog のために残す
import logging
from pubsub import pub # PyPubSub をインポート
from atproto_client import Session, SessionEvent # SDK の型をインポート

from gui.dialogs.login_dialog import LoginDialog # show_login_dialog のために残す
from core.auth.auth_manager import AuthManager
from core.client import BlueskyClient
from core import events # 定義したイベント名をインポート

# ロガーの設定
logger = logging.getLogger(__name__)

class AuthService: # クラス名を変更
    """認証プロセスを管理し、イベントを発行するサービス"""

    def __init__(self, client: BlueskyClient, auth_manager: AuthManager): # parent を削除
        """初期化"""
        self.client = client
        self.auth_manager = auth_manager

        # SDK のセッション変更イベントを購読
        # 注意: self.client が atproto_client.Client インスタンスであることを確認
        if hasattr(self.client, 'on_session_change') and callable(self.client.on_session_change):
             self.client.on_session_change(self._handle_session_change)
             logger.debug("AuthService initialized and subscribed to session changes.")
        else:
             logger.warning("AuthService: client does not support on_session_change. Session saving might not work automatically.")


    def _handle_session_change(self, event: SessionEvent, session: Session):
        """SDKからのセッション変更イベントを処理"""
        logger.info(f"Session change event received: {event}")
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            try:
                # export_session_string が client に存在するか確認
                if hasattr(self.client, 'export_session_string') and callable(self.client.export_session_string):
                    session_string = self.client.export_session_string()
                    if session_string and session and session.did:
                        logger.debug(f"Saving session for DID: {session.did}")
                        # AuthManager を介して保存
                        saved = self.auth_manager.save_session(session.did, session_string)
                        if saved:
                            # セッション保存成功イベントを発行
                            pub.sendMessage(events.AUTH_SESSION_SAVED, did=session.did)
                    else:
                        logger.warning("Could not export session string or DID is missing. Session not saved.")
                else:
                    logger.warning("AuthService: client does not support export_session_string.")
            except Exception as e:
                logger.error(f"Error saving session: {e}", exc_info=True)
        # elif event == SessionEvent.IMPORT: # 必要ならインポートイベントも処理
        #     pass

    def show_login_dialog(self, parent_window):
        """ログインダイアログを表示し、入力があればログイン処理を試行"""
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


    def perform_login(self, username, password):
        """ユーザー名とパスワードでログインを実行"""
        logger.debug("Attempting login...")
        pub.sendMessage(events.AUTH_LOGIN_ATTEMPT) # ログイン試行イベント
        try:
            # login メソッドが client に存在するか確認
            if hasattr(self.client, 'login') and callable(self.client.login):
                profile = self.client.login(username, password) # login() の引数名を修正
                logger.info(f"Login successful for handle: {profile.handle}")
                
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

    def perform_logout(self):
        """ログアウト処理を実行"""
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
                deleted = self.auth_manager.delete_session(user_did)
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

    def login_with_session(self, session_string, user_did):
        """保存されたセッション文字列を使用してログインを試行"""
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
            deleted = self.auth_manager.delete_session(user_did)
            if deleted:
                logger.info(f"Invalid session deleted for DID: {user_did}")
                pub.sendMessage(events.AUTH_SESSION_DELETED, did=user_did)

            # セッションログイン失敗イベントを発行
            pub.sendMessage(events.AUTH_SESSION_LOAD_FAILURE, error=e, needs_relogin=True)
            return False

    def load_and_login(self):
        """保存されたセッションを読み込み、ログインを試行"""
        logger.debug("Attempting to load session from store...")
        try:
            session_data, user_did = self.auth_manager.load_session() # 変更: load_session は復号化済みデータを返す想定
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
