#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ブロックしたユーザー一覧ダイアログ
"""

import wx
import logging
from gui.dialogs.user_list_dialog import UserListDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class BlockedUsersDialog(UserListDialog):
    """ブロックしたユーザー一覧ダイアログ"""
    
    def __init__(self, parent, client):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            client: Blueskyクライアント
        """
        super(BlockedUsersDialog, self).__init__(
            parent, 
            client,
            title="ブロックしたユーザー一覧",
            size=(600, 500)
        )
        
    def fetch_users(self):
        """ブロックしたユーザー一覧を取得"""
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
            
            # ブロックしたユーザー一覧を取得
            result = self.client.get_blocked_users(limit=100, cursor=self.cursor)
            
            # カーソルを更新
            self.cursor = result.cursor if hasattr(result, 'cursor') else None
            
            # ユーザーデータを処理
            for user in result.blocks:
                # Noneの場合に空文字列を使用するように修正
                display_name = user.display_name if user.display_name is not None else user.handle
                handle = user.handle or ''
                description = getattr(user, 'description', '') or ''
                
                user_data = {
                    'display_name': display_name,
                    'handle': handle,
                    'description': description,
                    'is_following': False, # ブロック一覧なのでフォロー状態はここでは考慮しない
                    'is_muted': False,  # デフォルトはFalse
                    'is_blocked': True  # ブロック一覧なので全てTrue
                }
                
                # ミュート状態を取得（可能であれば）
                if hasattr(user, 'viewer') and hasattr(user.viewer, 'muted'):
                    user_data['is_muted'] = bool(user.viewer.muted)
                
                self.list_ctrl.users.append(user_data)
                
                # リストビューに追加
                index = self.list_ctrl.InsertItem(len(self.list_ctrl.users), display_name)
                self.list_ctrl.SetItem(index, 1, f"@{handle}")
                self.list_ctrl.SetItem(index, 2, description)
                
            # もっと読み込むボタンの状態を更新
            if self.cursor:
                self.load_more_btn.SetLabel("もっと読み込む")
                self.load_more_btn.Enable(True)
            else:
                self.load_more_btn.SetLabel("これ以上ありません")
                self.load_more_btn.Enable(False)
                
            # ステータスを更新
            self.update_status("ブロックしたユーザー", len(self.list_ctrl.users))
                
            logger.info(f"ブロックしたユーザー一覧を取得しました: {len(result.blocks)}件")
            
        except Exception as e:
            logger.error(f"ブロックしたユーザー一覧の取得に失敗しました: {str(e)}")
            wx.MessageBox(f"ブロックしたユーザー一覧の取得に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            self.load_more_btn.SetLabel("もっと読み込む")
            self.load_more_btn.Enable(True)
            self.update_status("読み込みエラー", len(self.list_ctrl.users))
        
        finally:
            self.is_loading = False
            
    def load_more_users(self):
        """さらにブロックしたユーザーを読み込む"""
        if not self.cursor or self.is_loading:
            return
            
        self.fetch_users()

    def update_button_states(self, user=None):
        """ボタンの状態を更新
        
        Args:
            user (dict, optional): 選択されたユーザー情報
        """
        # ブロック解除ボタンのみを有効にする
        self.follow_btn.Enable(False)
        self.mute_btn.Enable(False)

        if not user:
            self.block_btn.Enable(False)
            return

        # 自分自身の場合は操作ボタンを無効化
        if user['handle'] == self.client.profile.handle:
            self.block_btn.Enable(False)
            return

        # ブロック状態に応じてボタンラベルを設定
        if user.get('is_blocked', False):
            self.block_btn.SetLabel("ブロック解除")
            self.block_btn.Enable(True)
        else:
            # ブロック一覧ダイアログでブロックされていないユーザーは表示されないはずだが念のため
            self.block_btn.SetLabel("ブロック")
            self.block_btn.Enable(False)
