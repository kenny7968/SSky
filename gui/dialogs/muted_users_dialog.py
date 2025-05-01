#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ミュートしたユーザー一覧ダイアログ
"""

import wx
import logging
from gui.dialogs.user_list_dialog import UserListDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class MutedUsersDialog(UserListDialog):
    """ミュートしたユーザー一覧ダイアログ"""

    def __init__(self, parent, client):
        """初期化

        Args:
            parent: 親ウィンドウ
            client: Blueskyクライアント
        """
        super(MutedUsersDialog, self).__init__(
            parent,
            client,
            title="ミュートしたユーザー一覧",
            size=(600, 500)
        )

        # ミュート解除ボタンのイベントをバインド
        self.mute_btn.Bind(wx.EVT_BUTTON, self.on_unmute_button)

    def fetch_users(self):
        """ミュートしたユーザー一覧を取得"""
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

            # ミュートしたユーザー一覧を取得
            result = self.client.get_muted_users(limit=100, cursor=self.cursor)

            # カーソルを更新
            self.cursor = result.cursor if hasattr(result, 'cursor') else None

            # ユーザーデータを処理
            for user in result.mutes:
                # Noneの場合に空文字列を使用するように修正
                display_name = user.display_name if user.display_name is not None else user.handle
                handle = user.handle or ''
                description = getattr(user, 'description', '') or ''

                user_data = {
                    'display_name': display_name,
                    'handle': handle,
                    'description': description,
                    'is_following': False, # ミュート一覧なのでフォロー状態はここでは考慮しない
                    'is_muted': True,  # ミュート一覧なので全てTrue
                    'is_blocked': False  # デフォルトはFalse
                }

                # ブロック状態を取得（可能であれば）
                if hasattr(user, 'viewer') and hasattr(user.viewer, 'blocking'):
                    user_data['is_blocked'] = bool(user.viewer.blocking)

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
            self.update_status("ミュートしたユーザー", len(self.list_ctrl.users))

            logger.info(f"ミュートしたユーザー一覧を取得しました: {len(result.mutes)}件")

        except Exception as e:
            logger.error(f"ミュートしたユーザー一覧の取得に失敗しました: {str(e)}")
            wx.MessageBox(f"ミュートしたユーザー一覧の取得に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            self.load_more_btn.SetLabel("もっと読み込む")
            self.load_more_btn.Enable(True)
            self.update_status("読み込みエラー", len(self.list_ctrl.users))

        finally:
            self.is_loading = False

    def load_more_users(self):
        """さらにミュートしたユーザーを読み込む"""
        if not self.cursor or self.is_loading:
            return

        self.fetch_users()

    def update_button_states(self, user=None):
        """ボタンの状態を更新

        Args:
            user (dict, optional): 選択されたユーザー情報
        """
        # ミュート解除ボタンのみを有効にする
        self.follow_btn.Enable(False)
        self.block_btn.Enable(False)

        if not user:
            self.mute_btn.Enable(False)
            return

        # 自分自身の場合は操作ボタンを無効化
        if user['handle'] == self.client.profile.handle:
            self.mute_btn.Enable(False)
            return

        # ミュート状態に応じてボタンラベルを設定
        if user.get('is_muted', False):
            self.mute_btn.SetLabel("ミュート解除")
            self.mute_btn.Enable(True)
        else:
            # ミュート一覧ダイアログでミュートされていないユーザーは表示されないはずだが念のため
            self.mute_btn.SetLabel("ミュート")
            self.mute_btn.Enable(False)

    def on_unmute_button(self, event):
        """ミュート解除ボタンクリック時の処理"""
        selected_index = self.list_ctrl.GetFocusedItem()
        if selected_index == -1:
            return # ユーザーが選択されていない場合は何もしない

        user_data = self.list_ctrl.users[selected_index]
        user_handle = user_data.get('handle')

        if not user_handle:
            wx.MessageBox("ユーザーハンドルが取得できませんでした。", "エラー", wx.OK | wx.ICON_ERROR)
            return

        try:
            # ミュート解除処理を実行
            success = self.client.unmute(user_handle)

            if success:
                wx.MessageBox(f"@{user_handle} のミュートを解除しました。", "成功", wx.OK | wx.ICON_INFORMATION)
                # リストからユーザーを削除し、表示を更新
                self.list_ctrl.DeleteItem(selected_index)
                del self.list_ctrl.users[selected_index]
                self.list_ctrl.RefreshItems(selected_index, self.list_ctrl.GetItemCount() - 1)
                self.update_status("ミュートしたユーザー", len(self.list_ctrl.users))
            else:
                wx.MessageBox(f"@{user_handle} のミュート解除に失敗しました。", "エラー", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            logger.error(f"ミュート解除中にエラーが発生しました: {str(e)}")
            wx.MessageBox(f"ミュート解除中にエラーが発生しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
