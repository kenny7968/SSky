#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
フォロワー一覧ダイアログ
"""

import wx
import logging
from gui.dialogs.user_list_dialog import UserListDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class FollowersDialog(UserListDialog):
    """フォロワー一覧ダイアログ"""
    
    def __init__(self, parent, client):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            client: Blueskyクライアント
        """
        super(FollowersDialog, self).__init__(
            parent, 
            client,
            title=f"{client.profile.handle}のフォロワー",
            size=(600, 500)
        )
        
    def fetch_users(self):
        """フォロワー一覧を取得"""
        if self.is_loading:
            return
            
        self.is_loading = True
        
        # ユーザーリストとリストビューをクリア（カーソルがNoneの場合のみ）
        if self.cursor is None:
            self.list_ctrl.users = []
            self.list_ctrl.DeleteAllItems()
        
        try:
            # ローディング表示
            self.load_more_btn.SetLabel("読み込み中...")
            self.load_more_btn.Enable(False)
            self.update_status("読み込み中...", len(self.list_ctrl.users))
            
            # フォロワー一覧を取得
            result = self.client.get_followers(self.client.profile.handle, limit=100, cursor=self.cursor)
            
            # カーソルを更新
            self.cursor = result.cursor if hasattr(result, 'cursor') else None
            
            # ユーザーデータを処理
            for user in result.followers:
                # Noneの場合に空文字列を使用するように修正
                display_name = user.display_name if user.display_name is not None else user.handle
                handle = user.handle or ''
                description = getattr(user, 'description', '') or ''
                
                user_data = {
                    'display_name': display_name,
                    'handle': handle,
                    'description': description,
                    'is_following': False,  # デフォルトはFalse
                    'is_muted': False,  # デフォルトはFalse
                    'is_blocked': False  # デフォルトはFalse
                }
                
                # フォロー状態、ミュート状態、ブロック状態を取得（可能であれば）
                if hasattr(user, 'viewer'):
                    if hasattr(user.viewer, 'following'):
                        user_data['is_following'] = bool(user.viewer.following)
                    if hasattr(user.viewer, 'muted'):
                        user_data['is_muted'] = bool(user.viewer.muted)
                    if hasattr(user.viewer, 'blocking'):
                        user_data['is_blocked'] = bool(user.viewer.blocking)
                
                self.list_ctrl.users.append(user_data)
                
                # リストビューに追加
                index = self.list_ctrl.InsertItem(len(self.list_ctrl.users), display_name)
                self.list_ctrl.SetItem(index, 1, f"@{handle}")
                self.list_ctrl.SetItem(index, 2, description)
                
            # この行は不要なので削除
            
            # もっと読み込むボタンの状態を更新
            if self.cursor:
                self.load_more_btn.SetLabel("もっと読み込む")
                self.load_more_btn.Enable(True)
            else:
                self.load_more_btn.SetLabel("これ以上ありません")
                self.load_more_btn.Enable(False)
                
            # ステータスを更新
            self.update_status("フォロワー", len(self.list_ctrl.users))
                
            logger.info(f"フォロワー一覧を取得しました: {len(result.followers)}件")
            
        except Exception as e:
            logger.error(f"フォロワー一覧の取得に失敗しました: {str(e)}")
            wx.MessageBox(f"フォロワー一覧の取得に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            self.load_more_btn.SetLabel("もっと読み込む")
            self.load_more_btn.Enable(True)
            self.update_status("読み込みエラー", len(self.list_ctrl.users))
        
        finally:
            self.is_loading = False
            
    def load_more_users(self):
        """さらにフォロワーを読み込む"""
        if not self.cursor or self.is_loading:
            return
            
        self.fetch_users()
