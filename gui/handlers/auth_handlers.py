#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証関連イベントハンドラ
"""

import wx
import logging
from gui.dialogs.login_dialog import LoginDialog
from core.auth.auth_manager import AuthManager
from core.client import BlueskyClient

# ロガーの設定
logger = logging.getLogger(__name__)

class AuthHandlers:
    """認証関連イベントハンドラクラス"""
    
    def __init__(self, parent, client=None, auth_manager=None):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            client (BlueskyClient, optional): Blueskyクライアント
            auth_manager (AuthManager, optional): 認証マネージャー
        """
        self.parent = parent
        self.client = client if client else BlueskyClient()
        self.auth_manager = auth_manager if auth_manager else AuthManager()
        
    def on_login(self, event):
        """ログインダイアログを表示
        
        Args:
            event: メニューイベント
        """
        # ログインダイアログの作成
        dlg = LoginDialog(self.parent)
        
        # ダイアログ表示
        if dlg.ShowModal() == wx.ID_OK:
            username, password = dlg.get_credentials()
            
            if username and password:
                # 直接ログイン処理を実行
                self.perform_login(username, password)
                # セッション保存処理は削除（on_session_changeコールバックで自動的に処理される）
                # エラーメッセージは perform_login 内で表示されるので、ここでは何もしない
            else:
                wx.MessageBox("ユーザー名とアプリパスワードを入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
        
    def perform_login(self, username, password, show_dialog=True):
        """ログイン処理を実行
        
        Args:
            username (str): ユーザー名
            password (str): パスワード
            show_dialog (bool): ダイアログを表示するかどうか
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # ステータスバーの更新
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("Blueskyにログイン中...")
            
            # ユーザー名はログに出力しない（セキュリティ上の理由から）
            logger.debug("ログイン試行を開始します")
            
            try:
                # ログイン試行
                profile = self.client.login(username, password)
                
                logger.debug(f"ログイン成功: プロフィール={profile.display_name}")
                
                # ログイン成功
                if hasattr(self.parent, 'set_username'):
                    self.parent.set_username(profile.handle)
                
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                
                if hasattr(self.parent, 'update_login_status'):
                    self.parent.update_login_status(True)
                
                # タイムラインビューのログイン状態を更新
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                    self.parent.timeline.update_login_status(True)
                
                # タイムラインの更新
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("タイムラインを更新しています...")
                
                if hasattr(self.parent, 'timeline'):
                    self.parent.timeline.fetch_timeline(self.client)
                    
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                
                # 成功通知ダイアログを表示（オプション）
                if show_dialog:
                    wx.MessageBox(f"{profile.handle}としてログインしました", "ログイン成功", wx.OK | wx.ICON_INFORMATION)
                
                return True
                
            except Exception as e:
                # ログイン失敗
                error_message = f"ログインに失敗しました: {str(e)}\n\n2段階認証を設定しているアカウントは、アプリパスワードを使用してください。"
                logger.error(f"ログインに失敗しました: {str(e)}")
                
                if show_dialog:
                    result = wx.MessageBox(error_message, "ログイン失敗", wx.OK | wx.ICON_ERROR)
                    # OKボタンがクリックされたら、ログイン情報設定ダイアログを表示
                    if result == wx.OK:
                        self.on_login(None)
                
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("ログインに失敗しました")
                
                # 未ログイン状態のメッセージを表示
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                    self.parent.timeline.update_login_status(False)
                elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                    self.parent.timeline.show_not_logged_in_message()
                
                return False
            
        except Exception as e:
            # ログイン失敗
            logger.error(f"ログイン処理中に例外が発生しました: {str(e)}", exc_info=True)
            
            if show_dialog:
                result = wx.MessageBox(f"ログインに失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                # OKボタンがクリックされたら、ログイン情報設定ダイアログを表示
                if result == wx.OK:
                    self.on_login(None)
            
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("ログインに失敗しました")
            
            # 未ログイン状態のメッセージを表示
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                self.parent.timeline.update_login_status(False)
            elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
            
            return False
            
    def on_logout(self, event):
        """ログアウト処理
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        if self.client and hasattr(self.client, 'profile') and self.client.profile:
            username = self.client.profile.handle
            
            # セッション情報を削除
            if self.client.user_did:
                self.auth_manager.delete_session(self.client.user_did)
            
            # クライアントをリセット
            self.client.logout()
            
            # UIを更新
            if hasattr(self.parent, 'SetTitle'):
                self.parent.SetTitle("SSky")
            
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("ログアウトしました")
            
            if hasattr(self.parent, 'update_login_status'):
                self.parent.update_login_status(False)
                
            # タイムラインビューを更新（「ログインしていません」表示）
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                self.parent.timeline.update_login_status(False)
            elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
            
            logger.info("ログアウトしました")
            
            # ログアウト通知ダイアログを表示
            wx.MessageBox(f"{username}からログアウトしました", "ログアウト完了", wx.OK | wx.ICON_INFORMATION)
            
            return True
        
        return False
        
    def login_with_session(self, session_string, user_did=None):
        """セッション情報を使用してログイン処理を実行
        
        Args:
            session_string (str): セッション情報の文字列
            user_did (str, optional): ユーザーのDID
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # ステータスバーの更新
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("セッション情報を使用してログイン中...")
            
            logger.debug("セッション情報を使用してログイン試行")
            
            try:
                # セッションでログイン
                profile = self.client.login_with_session(session_string)
                
                logger.debug(f"セッションを使用したログイン成功: プロフィール={profile.display_name}")
                
                # ログイン成功
                if hasattr(self.parent, 'set_username'):
                    self.parent.set_username(profile.handle)
                
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                
                if hasattr(self.parent, 'update_login_status'):
                    self.parent.update_login_status(True)
                
                # タイムラインビューのログイン状態を更新
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                    self.parent.timeline.update_login_status(True)
                
                # タイムラインの更新
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("タイムラインを更新しています...")
                
                if hasattr(self.parent, 'timeline'):
                    self.parent.timeline.fetch_timeline(self.client)
                    
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                
                return True
                
            except Exception as e:
                # セッションが無効な場合
                logger.error(f"セッションを使用したログインに失敗しました: {str(e)}")
                
                # セッション情報が無効な場合は削除
                if user_did:
                    self.auth_manager.delete_session(user_did)
                
                # 未ログイン状態のメッセージを表示
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("セッションが無効です。再ログインが必要です。")
                
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                    self.parent.timeline.update_login_status(False)
                elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                    self.parent.timeline.show_not_logged_in_message()
                
                return False
            
        except Exception as e:
            # その他のエラー
            logger.error(f"セッションを使用したログイン処理中に例外が発生しました: {str(e)}", exc_info=True)
            
            # 未ログイン状態のメッセージを表示
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("ログインに失敗しました")
            
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                self.parent.timeline.update_login_status(False)
            elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
            
            return False
    
    def load_session(self):
        """保存されたセッション情報を読み込み、ログイン処理を実行
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # セッション情報を読み込み
            session_string, user_did = self.auth_manager.load_session()
            if session_string:
                logger.info(f"保存されたセッション情報を読み込みました: {user_did}")
                
                # セッション情報がバイト列の場合はLatin-1でデコード
                if isinstance(session_string, bytes):
                    try:
                        decoded_session = session_string.decode('latin-1')
                        logger.debug(f"セッション情報をLatin-1でデコードしました: 長さ{len(decoded_session)}文字")
                        session_string = decoded_session
                    except Exception as e:
                        logger.error(f"セッション情報のデコードに失敗しました: {str(e)}")
                        # デコードに失敗した場合は、そのまま使用
                
                # セッションでログイン
                return self.login_with_session(session_string, user_did)
            
            # セッション情報がない場合は、ログインしない状態を維持
            logger.debug("セッション情報が見つかりませんでした。ログインしていない状態を維持します。")
            
            # 未ログイン状態のメッセージを表示
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                self.parent.timeline.update_login_status(False)
            elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
                
            # 親フレームのログイン状態も更新
            if hasattr(self.parent, 'update_login_status'):
                self.parent.update_login_status(False)
                
            return False
            
        except Exception as e:
            logger.error(f"セッション情報の読み込みに失敗しました: {str(e)}")
            # 未ログイン状態のメッセージを表示
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'update_login_status'):
                self.parent.timeline.update_login_status(False)
            elif hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
                
            # 親フレームのログイン状態も更新
            if hasattr(self.parent, 'update_login_status'):
                self.parent.update_login_status(False)
                
            return False
