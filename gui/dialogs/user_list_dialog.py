#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ユーザー一覧ダイアログ基底クラス
"""

import wx
import wx.lib.mixins.listctrl as listmix
import logging
import weakref

# ロガーの設定
logger = logging.getLogger(__name__)

class UserListDialog(wx.Dialog):
    """ユーザー一覧ダイアログ基底クラス"""
    
    def __init__(self, parent, client, title, size=(600, 500)):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            client: Blueskyクライアント
            title (str): ダイアログタイトル
            size (tuple): ウィンドウサイズ
        """
        super(UserListDialog, self).__init__(
            parent, 
            title=title,
            size=size,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.client = client
        self.cursor = None  # ページネーション用カーソル
        self.is_loading = False  # 読み込み中フラグ
        
        # UIの初期化
        self.init_ui()
        
        # キーイベントのバインド
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # 中央に配置
        self.Centre()
        
        # ユーザー一覧を取得
        self.fetch_users()
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        
        # Escキーが押されたらダイアログを閉じる
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CLOSE)
        else:
            event.Skip()
        
    def init_ui(self):
        """UIの初期化"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ステータスラベル
        self.status_label = wx.StaticText(panel, label="読み込み中...", style=wx.ALIGN_CENTER)
        main_sizer.Add(self.status_label, 0, wx.EXPAND | wx.ALL, 5)
        
        # リストコントロール
        self.list_ctrl = UserListCtrl(panel)
        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # 操作ボタン
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # フォロー/フォロー解除ボタン
        self.follow_btn = wx.Button(panel, label="フォロー", size=(120, -1))
        self.follow_btn.Bind(wx.EVT_BUTTON, self.on_follow)
        button_sizer.Add(self.follow_btn, 0, wx.ALL, 5)
        
        # ミュート/ミュート解除ボタン
        self.mute_btn = wx.Button(panel, label="ミュート", size=(120, -1))
        self.mute_btn.Bind(wx.EVT_BUTTON, self.on_mute)
        button_sizer.Add(self.mute_btn, 0, wx.ALL, 5)
        
        # ブロック/ブロック解除ボタン
        self.block_btn = wx.Button(panel, label="ブロック", size=(120, -1))
        self.block_btn.Bind(wx.EVT_BUTTON, self.on_block)
        button_sizer.Add(self.block_btn, 0, wx.ALL, 5)
        
        # 閉じるボタン
        close_btn = wx.Button(panel, wx.ID_CLOSE, "閉じる")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        button_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # もっと読み込むボタン
        self.load_more_btn = wx.Button(panel, label="もっと読み込む", size=(150, -1))
        self.load_more_btn.Bind(wx.EVT_BUTTON, self.on_load_more)
        main_sizer.Add(self.load_more_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        panel.SetSizer(main_sizer)
        
        # 初期状態ではボタンを無効化
        self.follow_btn.Enable(False)
        self.mute_btn.Enable(False)
        self.block_btn.Enable(False)
        self.load_more_btn.Enable(False)
        
    def fetch_users(self):
        """ユーザー一覧を取得（サブクラスでオーバーライド）"""
        pass
        
    def load_more_users(self):
        """さらにユーザーを読み込む（サブクラスでオーバーライド）"""
        pass
        
    def update_button_states(self, user=None):
        """ボタンの状態を更新
        
        Args:
            user (dict, optional): 選択されたユーザー情報
        """
        if not user:
            # ユーザーが選択されていない場合は全てのボタンを無効化
            self.follow_btn.Enable(False)
            self.mute_btn.Enable(False)
            self.block_btn.Enable(False)
            return
            
        # 自分自身の場合は操作ボタンを無効化
        if user['handle'] == self.client.profile.handle:
            self.follow_btn.Enable(False)
            self.mute_btn.Enable(False)
            self.block_btn.Enable(False)
            return
            
        # フォロー状態に応じてボタンラベルを設定
        if user.get('is_following', False):
            self.follow_btn.SetLabel("フォロー解除")
        else:
            self.follow_btn.SetLabel("フォロー")
            
        # ミュート状態に応じてボタンラベルを設定
        if user.get('is_muted', False):
            self.mute_btn.SetLabel("ミュート解除")
        else:
            self.mute_btn.SetLabel("ミュート")
            
        # ブロック状態に応じてボタンラベルを設定
        if user.get('is_blocked', False):
            self.block_btn.SetLabel("ブロック解除")
        else:
            self.block_btn.SetLabel("ブロック")
            
        # ボタンを有効化
        self.follow_btn.Enable(True)
        self.mute_btn.Enable(True)
        self.block_btn.Enable(True)
        
    def on_follow(self, event):
        """フォロー/フォロー解除ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        selected_user = self.list_ctrl.get_selected_user()
        if not selected_user:
            return
            
        handle = selected_user['handle']
        
        try:
            if selected_user.get('is_following', False):
                # フォロー解除
                self.client.unfollow(handle)
                selected_user['is_following'] = False
                wx.MessageBox(f"{selected_user['display_name']}のフォローを解除しました", 
                             "フォロー解除完了", wx.OK | wx.ICON_INFORMATION)
            else:
                # フォロー
                self.client.follow(handle)
                selected_user['is_following'] = True
                wx.MessageBox(f"{selected_user['display_name']}をフォローしました", 
                             "フォロー完了", wx.OK | wx.ICON_INFORMATION)
                
            # ボタンの状態を更新
            self.update_button_states(selected_user)
            
            # リストビューを更新
            self.list_ctrl.update_user(self.list_ctrl.selected_index, selected_user)
            
        except Exception as e:
            logger.error(f"フォロー操作に失敗しました: {str(e)}")
            wx.MessageBox(f"フォロー操作に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        
    def on_mute(self, event):
        """ミュート/ミュート解除ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        selected_user = self.list_ctrl.get_selected_user()
        if not selected_user:
            return
            
        handle = selected_user['handle']
        
        try:
            if selected_user.get('is_muted', False):
                # ミュート解除
                self.client.unmute(handle)
                selected_user['is_muted'] = False
                wx.MessageBox(f"{selected_user['display_name']}のミュートを解除しました", 
                             "ミュート解除完了", wx.OK | wx.ICON_INFORMATION)
            else:
                # ミュート
                self.client.mute(handle)
                selected_user['is_muted'] = True
                wx.MessageBox(f"{selected_user['display_name']}をミュートしました", 
                             "ミュート完了", wx.OK | wx.ICON_INFORMATION)
                
            # ボタンの状態を更新
            self.update_button_states(selected_user)
            
            # リストビューを更新
            self.list_ctrl.update_user(self.list_ctrl.selected_index, selected_user)
            
        except Exception as e:
            logger.error(f"ミュート操作に失敗しました: {str(e)}")
            wx.MessageBox(f"ミュート操作に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        
    def on_block(self, event):
        """ブロック/ブロック解除ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        selected_user = self.list_ctrl.get_selected_user()
        if not selected_user:
            return
            
        handle = selected_user['handle']
        
        try:
            if selected_user.get('is_blocked', False):
                # ブロック解除
                self.client.unblock(handle)
                selected_user['is_blocked'] = False
                wx.MessageBox(f"{selected_user['display_name']}のブロックを解除しました", 
                             "ブロック解除完了", wx.OK | wx.ICON_INFORMATION)
            else:
                # ブロック
                self.client.block(handle)
                selected_user['is_blocked'] = True
                wx.MessageBox(f"{selected_user['display_name']}をブロックしました", 
                             "ブロック完了", wx.OK | wx.ICON_INFORMATION)
                
            # ボタンの状態を更新
            self.update_button_states(selected_user)
            
            # リストビューを更新
            self.list_ctrl.update_user(self.list_ctrl.selected_index, selected_user)
            
        except Exception as e:
            logger.error(f"ブロック操作に失敗しました: {str(e)}")
            wx.MessageBox(f"ブロック操作に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        
    def on_load_more(self, event):
        """もっと読み込むボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        if not self.is_loading and self.cursor:
            self.load_more_users()
        
    def on_close(self, event):
        """閉じるボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        self.EndModal(wx.ID_CLOSE)
        
    def Destroy(self):
        """ダイアログ破棄時の処理"""
        # イベントハンドラの解除
        self.Unbind(wx.EVT_CHAR_HOOK)
        
        # ボタンのイベントハンドラを解除
        if hasattr(self, 'follow_btn'):
            self.follow_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'mute_btn'):
            self.mute_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'block_btn'):
            self.block_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'load_more_btn'):
            self.load_more_btn.Unbind(wx.EVT_BUTTON)
            
        # リストコントロールのイベントハンドラを解除
        if hasattr(self, 'list_ctrl'):
            self.list_ctrl.cleanup()
            
        logger.debug("UserListDialogのリソースを解放しました")
        return super(UserListDialog, self).Destroy()
        
    def update_status(self, message, count=None, total=None):
        """ステータスラベルを更新
        
        Args:
            message (str): 表示するメッセージ
            count (int, optional): 現在の件数
            total (int, optional): 合計件数
        """
        if count is not None and total is not None:
            status_text = f"{message} ({count}/{total}件)"
        elif count is not None:
            status_text = f"{message} ({count}件)"
        else:
            status_text = message
            
        self.status_label.SetLabel(status_text)


class UserListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """ユーザー一覧リストコントロールクラス"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        wx.ListCtrl.__init__(
            self, 
            parent, 
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_THEME
        )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        # 親への弱参照を保持
        self.parent_ref = weakref.ref(parent)
        
        # カラム設定
        self.InsertColumn(0, "ユーザー名", width=150)
        self.InsertColumn(1, "ハンドル", width=150)
        self.InsertColumn(2, "説明", width=300)
        
        # 選択中のユーザーインデックス
        self.selected_index = -1
        
        # ユーザーデータの初期化
        self.users = []
        
        # イベントバインド
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        
    def on_item_selected(self, event):
        """アイテム選択時の処理
        
        Args:
            event: リストイベント
        """
        self.selected_index = event.GetIndex()
        
        # 親ダイアログのボタン状態を更新（弱参照を使用）
        parent_panel = self.GetParent()
        if parent_panel:
            dialog = parent_panel.GetParent()
            if dialog and not dialog.IsBeingDeleted() and hasattr(dialog, 'update_button_states'):
                user = self.get_selected_user()
                dialog.update_button_states(user)
        
        event.Skip()
        
    def cleanup(self):
        """リソースの解放"""
        # イベントハンドラの解除
        self.Unbind(wx.EVT_LIST_ITEM_SELECTED)
        
        # 親への参照をクリア
        self.parent_ref = None
        
    def get_selected_user(self):
        """選択中のユーザーデータを取得
        
        Returns:
            dict: 選択中のユーザーデータ。選択されていない場合はNone
        """
        if 0 <= self.selected_index < len(self.users):
            return self.users[self.selected_index]
        return None
        
    def update_user(self, index, user_data):
        """ユーザーデータを更新
        
        Args:
            index (int): 更新するユーザーのインデックス
            user_data (dict): 新しいユーザーデータ
            
        Returns:
            bool: 更新に成功した場合はTrue
        """
        if 0 <= index < len(self.users):
            # ユーザーデータを更新
            self.users[index] = user_data
            
            # Noneの場合に空文字列を使用するように修正
            display_name = user_data['display_name'] or ''
            handle = user_data['handle'] or ''
            description = user_data.get('description', '') or ''
            
            # リストビューの表示を更新
            self.SetItem(index, 0, display_name)
            self.SetItem(index, 1, f"@{handle}")
            self.SetItem(index, 2, description)
            
            return True
        return False
