#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインビュークラス（リストビュー実装）
"""

import wx
import wx.lib.mixins.listctrl as listmix
import logging
from datetime import datetime, timezone, timedelta

# ロガーの設定
logger = logging.getLogger(__name__)

class TimelineView(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """タイムラインビュークラス（リストビュー実装）"""
    
    def __init__(self, parent):
        """初期化"""
        wx.ListCtrl.__init__(
            self, 
            parent, 
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_THEME
        )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        # カラム設定
        self.InsertColumn(0, "ユーザー", width=150)
        self.InsertColumn(1, "投稿内容", width=400)
        self.InsertColumn(2, "時間", width=100)
        
        # 選択中の投稿インデックス
        self.selected_index = -1
        
        # 投稿データの初期化
        self.posts = []
        self.post_count = 0
        
        # UIの初期化
        self.init_ui()
        
        # イベントバインド
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # アクセシビリティ
        self.SetName("タイムラインビュー")
        
        # フォーカス設定
        self.SetFocus()
        
    def init_ui(self):
        """UIの初期化"""
        # 投稿がない場合
        if not self.posts:
            # リストビューは空のままで、ステータスバーなどで通知する方が良い
            return
            
        # 投稿データをリストに追加
        for i, post in enumerate(self.posts):
            # ユーザー名のみを表示
            user_text = post['username']
            
            # リストに追加
            index = self.InsertItem(i, user_text)
            self.SetItem(index, 1, post['content'])
            self.SetItem(index, 2, post['time'])
            
            # データを関連付け
            self.SetItemData(index, i)
            
        # 最初の項目を選択
        if self.GetItemCount() > 0:
            self.Select(0)
            self.Focus(0)
            
    def on_item_selected(self, event):
        """アイテム選択時の処理"""
        self.selected_index = event.GetIndex()
        event.Skip()
        
    def on_item_activated(self, event):
        """アイテムアクティベート時の処理（ダブルクリックなど）"""
        index = event.GetIndex()
        post = self.posts[index]
        
        # 投稿の詳細表示（例：ダイアログ表示）
        dlg = PostDetailDialog(self, post)
        dlg.ShowModal()
        dlg.Destroy()
        
        event.Skip()
        
    def on_key_down(self, event):
        """キー入力時の処理"""
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        shift_down = event.ShiftDown()
        
        # 選択されている項目がない場合は通常のキー処理を行う
        if self.selected_index == -1:
            event.Skip()
            return
            
        # ショートカットキーの処理
        if ctrl_down:
            if key_code == ord('N'):  # Ctrl+N
                # 新規投稿（親フレームのメソッドを呼び出す）
                frame = wx.GetTopLevelParent(self)
                if hasattr(frame, 'on_new_post'):
                    frame.on_new_post(event)
                return
            elif key_code == ord('L'):  # Ctrl+L
                self.on_like(event)
                return
            elif key_code == ord('R'):  # Ctrl+R
                self.on_reply(event)
                return
            elif key_code == ord('Q'):  # Ctrl+Q
                self.on_quote(event)
                return
            elif key_code == ord('P'):  # Ctrl+P
                self.on_profile(event)
                return
        
        # Delキーで投稿削除
        if key_code == wx.WXK_DELETE:
            self.on_delete(event)
            return
            
        # Shift+F10でコンテキストメニュー表示
        if shift_down and key_code == wx.WXK_F10:
            # 選択されている項目の位置を取得
            item_rect = self.GetItemRect(self.selected_index)
            pos = wx.Point(item_rect.x + item_rect.width // 2, item_rect.y + item_rect.height // 2)
            self.show_context_menu(pos)
            return
            
        event.Skip()
        
    def on_context_menu(self, event):
        """コンテキストメニュー表示時の処理（右クリック）"""
        # 選択されている項目がない場合は何もしない
        if self.selected_index == -1:
            return
            
        # マウス位置を取得
        pos = event.GetPosition()
        
        # スクリーン座標からクライアント座標に変換
        pos = self.ScreenToClient(pos)
        
        # コンテキストメニューを表示
        self.show_context_menu(pos)
        
    def show_context_menu(self, pos):
        """コンテキストメニューを表示"""
        # 選択されている投稿
        post = self.posts[self.selected_index]
        
        # コンテキストメニューの作成
        menu = wx.Menu()
        
        # メニュー項目の追加（ショートカットキーとアクセラレータキー表示付き）
        like_item = menu.Append(wx.ID_ANY, "いいね(&L)\tCtrl+L")
        reply_item = menu.Append(wx.ID_ANY, "返信(&R)\tCtrl+R")
        quote_item = menu.Append(wx.ID_ANY, "引用(&Q)\tCtrl+Q")
        profile_item = menu.Append(wx.ID_ANY, "投稿者のプロフィールを表示(&P)\tCtrl+P")
        delete_item = menu.Append(wx.ID_ANY, "投稿を削除(&D)\tDel")
        
        # イベントバインド
        self.Bind(wx.EVT_MENU, self.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_delete, delete_item)
        
        # メニュー表示
        self.PopupMenu(menu, pos)
        menu.Destroy()
        
    def on_like(self, event):
        """いいねアクション"""
        if self.selected_index != -1:
            post = self.posts[self.selected_index]
            wx.MessageBox(f"投稿にいいねしました", "いいね", wx.OK | wx.ICON_INFORMATION)
        
    def on_reply(self, event):
        """返信アクション"""
        if self.selected_index != -1:
            post = self.posts[self.selected_index]
            dlg = wx.TextEntryDialog(self, "返信内容を入力:", "返信")
            if dlg.ShowModal() == wx.ID_OK:
                reply = dlg.GetValue()
                if reply:
                    wx.MessageBox(f"返信を投稿しました: {reply}", "返信", wx.OK | wx.ICON_INFORMATION)
            dlg.Destroy()
        
    def on_quote(self, event):
        """引用アクション"""
        if self.selected_index != -1:
            post = self.posts[self.selected_index]
            dlg = wx.TextEntryDialog(self, "引用内容を入力:", "引用")
            if dlg.ShowModal() == wx.ID_OK:
                quote = dlg.GetValue()
                if quote:
                    wx.MessageBox(f"引用を投稿しました: {quote}", "引用", wx.OK | wx.ICON_INFORMATION)
            dlg.Destroy()
        
    def on_profile(self, event):
        """プロフィール表示アクション"""
        if self.selected_index != -1:
            post = self.posts[self.selected_index]
            wx.MessageBox(f"プロフィールを表示します: {post['username']}", "プロフィール", wx.OK | wx.ICON_INFORMATION)
    
    def on_delete(self, event):
        """削除アクション"""
        if self.selected_index != -1:
            # 親フレームのon_deleteメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_delete'):
                frame.on_delete(event)
    
    def fetch_timeline(self, client=None):
        """Bluesky APIを使用してタイムラインを取得"""
        # クライアントが渡されなかった場合は親フレームから取得
        if not client:
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'client'):
                client = frame.client
        
        # クライアントがない場合は何もしない
        if not client:
            logger.warning("タイムラインの取得に失敗しました: クライアントが設定されていません")
            return
            
        try:
            # タイムラインの取得（最新50件）
            logger.info("タイムラインを取得しています...")
            timeline_data = client.get_timeline(limit=50)
            
            # 投稿データの変換と格納
            self.posts = []
            
            for post in timeline_data.feed:
                # 投稿データを適切な形式に変換
                post_data = {
                    'username': post.post.author.display_name or post.post.author.handle,
                    'handle': f"@{post.post.author.handle}",
                    'content': post.post.record.text,
                    'time': self._format_time(post.post.indexed_at),  # 表示用の文字列
                    'raw_timestamp': post.post.indexed_at,  # ソート用のオリジナルタイムスタンプ
                    'likes': getattr(post.post, 'like_count', 0),
                    'replies': getattr(post.post, 'reply_count', 0),
                    'reposts': getattr(post.post, 'repost_count', 0)
                }
                self.posts.append(post_data)
                
            # 投稿日時でソート（最新が下）- raw_timestampフィールドを使用
            self.posts.sort(key=lambda x: x['raw_timestamp'], reverse=False)
            self.post_count = len(self.posts)
            
            # UIの更新
            self.DeleteAllItems()
            self.init_ui()
            
            logger.info(f"タイムラインを取得しました: {len(self.posts)}件")
            
        except Exception as e:
            logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def _format_time(self, timestamp):
        """タイムスタンプを表示用の時間文字列に変換"""
        try:
            # タイムスタンプがUTC時間の場合
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            # 現在時刻との差を計算
            now = datetime.now(timezone.utc)
            diff = now - dt
            
            # 表示形式を決定
            if diff.days > 0:
                if diff.days == 1:
                    return "昨日"
                else:
                    return f"{diff.days}日前"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours}時間前"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes}分前"
            else:
                return "たった今"
        except Exception as e:
            logger.error(f"時間フォーマットに失敗しました: {str(e)}")
            return "不明"
    
    def get_selected_post(self):
        """選択中の投稿データを取得"""
        if 0 <= self.selected_index < len(self.posts):
            return self.posts[self.selected_index]
        return None


class PostDetailDialog(wx.Dialog):
    """投稿詳細ダイアログ"""
    
    def __init__(self, parent, post_data):
        """初期化"""
        super(PostDetailDialog, self).__init__(
            parent, 
            title=f"{post_data['username']}の投稿",
            size=(500, 300),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.post_data = post_data
        
        # UIの初期化
        self.init_ui()
        
        # キーイベントのバインド
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # 中央に配置
        self.Centre()
        
    def on_key_down(self, event):
        """キー入力時の処理"""
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
        
        # 投稿内容（リードオンリーエディット）- 全ての情報を含む
        content_text = f"{self.post_data['username']} {self.post_data['handle']} - {self.post_data['time']}\n\n"
        content_text += f"{self.post_data['content']}\n\n"
        content_text += f"いいね: {self.post_data['likes']}  返信: {self.post_data['replies']}  リポスト: {self.post_data['reposts']}"
        
        content = wx.TextCtrl(
            panel, 
            value=content_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.BORDER_SIMPLE
        )
        # フォントとサイズの設定
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        content.SetFont(font)
        # 背景色の設定（システムの背景色に合わせる）
        content.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        main_sizer.Add(content, 1, wx.ALL | wx.EXPAND, 10)
        
        # 区切り線
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        
        # アクションボタン
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # いいねボタン
        like_btn = wx.Button(panel, label="いいね", size=(80, -1))
        like_btn.Bind(wx.EVT_BUTTON, self.on_like)
        button_sizer.Add(like_btn, 0, wx.ALL, 5)
        
        # 返信ボタン
        reply_btn = wx.Button(panel, label="返信", size=(80, -1))
        reply_btn.Bind(wx.EVT_BUTTON, self.on_reply)
        button_sizer.Add(reply_btn, 0, wx.ALL, 5)
        
        # 引用ボタン
        quote_btn = wx.Button(panel, label="引用", size=(80, -1))
        quote_btn.Bind(wx.EVT_BUTTON, self.on_quote)
        button_sizer.Add(quote_btn, 0, wx.ALL, 5)
        
        # 閉じるボタン
        close_btn = wx.Button(panel, wx.ID_CLOSE, "閉じる")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        button_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
    def on_like(self, event):
        """いいねボタンクリック時の処理"""
        wx.MessageBox(f"投稿にいいねしました", "いいね", wx.OK | wx.ICON_INFORMATION)
        
    def on_reply(self, event):
        """返信ボタンクリック時の処理"""
        dlg = wx.TextEntryDialog(self, "返信内容を入力:", "返信")
        if dlg.ShowModal() == wx.ID_OK:
            reply = dlg.GetValue()
            if reply:
                wx.MessageBox(f"返信を投稿しました: {reply}", "返信", wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()
        
    def on_quote(self, event):
        """引用ボタンクリック時の処理"""
        dlg = wx.TextEntryDialog(self, "引用内容を入力:", "引用")
        if dlg.ShowModal() == wx.ID_OK:
            quote = dlg.GetValue()
            if quote:
                wx.MessageBox(f"引用を投稿しました: {quote}", "引用", wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()
        
    def on_close(self, event):
        """閉じるボタンクリック時の処理"""
        self.EndModal(wx.ID_CLOSE)
