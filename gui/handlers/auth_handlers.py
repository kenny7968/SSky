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
        """ログイン情報設定ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        # ログインダイアログの作成
        dlg = LoginDialog(self.parent)
        
        # ダイアログ表示
        if dlg.ShowModal() == wx.ID_OK:
            username, password = dlg.get_credentials()
            
            if username and password:
                # ログイン情報を保存
                if self.auth_manager.save_credentials(username, password):
                    # ログイン処理を実行
                    self.perform_login(username, password)
                else:
                    wx.MessageBox("ログイン情報の保存に失敗しました", "エラー", wx.OK | wx.ICON_ERROR)
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
            
            logger.debug(f"ログイン試行: ユーザー名={username}")
            
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
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
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
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
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
            
            # ログイン情報を削除
            self.auth_manager.delete_credentials()
            
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
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
            
            logger.info("ログアウトしました")
            
            # ログアウト通知ダイアログを表示
            wx.MessageBox(f"{username}からログアウトしました", "ログアウト完了", wx.OK | wx.ICON_INFORMATION)
            
            return True
        
        return False
        
    def load_saved_session(self):
        """保存されたログイン情報を読み込み、ログイン処理を実行
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # ログイン情報を読み込み
            username, password = self.auth_manager.load_credentials()
            if username and password:
                logger.info(f"保存されたログイン情報を読み込みました: {username}")
                # ログイン処理を実行
                return self.perform_login(username, password, show_dialog=False)
            else:
                logger.debug("保存されたログイン情報がありません")
                # 未ログイン状態のメッセージを表示
                if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                    self.parent.timeline.show_not_logged_in_message()
                return False
        except Exception as e:
            logger.error(f"ログイン情報の読み込みに失敗しました: {str(e)}")
            # 未ログイン状態のメッセージを表示
            if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'show_not_logged_in_message'):
                self.parent.timeline.show_not_logged_in_message()
            return False
