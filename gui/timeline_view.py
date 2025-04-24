#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインビュークラス（リストビュー実装）
"""

import wx
import wx.lib.mixins.listctrl as listmix
import logging
import time
from utils.time_format import format_relative_time
from gui.dialogs.post_detail_dialog import PostDetailDialog

# ロガーの設定
logger = logging.getLogger(__name__)

# タイマーID
TIMER_ID = 1000

class TimelineView(wx.Panel):
    """タイムラインビュークラス"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        super(TimelineView, self).__init__(parent)
        
        # 自動取得の設定
        self.auto_fetch_enabled = False
        self.fetch_interval = 180  # デフォルト：180秒
        
        # タイマー
        self.timer = wx.Timer(self, TIMER_ID)
        
        # UIの初期化
        self.init_ui()
        
        # 投稿データの初期化
        self.posts = []
        self.post_count = 0
        
        # イベントバインド
        self.Bind(wx.EVT_TIMER, self.on_timer, id=TIMER_ID)
        self.Bind(wx.EVT_BUTTON, self.on_fetch_button, self.fetch_button)
        
        # アクセシビリティ
        self.SetName("タイムラインパネル")
        
    def init_ui(self):
        """UIの初期化"""
        # メインレイアウト
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ツールバー
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # タイムライン取得ボタン
        self.fetch_button = wx.Button(self, label="タイムライン取得", size=(150, -1))
        self.fetch_button.SetToolTip("タイムラインを取得します (F5)")
        toolbar_sizer.Add(self.fetch_button, 0, wx.ALL, 5)
        
        main_sizer.Add(toolbar_sizer, 0, wx.EXPAND)
        
        # タイトルラベル
        title_label = wx.StaticText(self, label="ホームタイムライン")
        # フォントを大きくして目立たせる
        font = title_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title_label.SetFont(font)
        main_sizer.Add(title_label, 0, wx.LEFT | wx.TOP, 10)
        
        # リストビュー
        self.list_ctrl = TimelineListCtrl(self)
        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
    def on_timer(self, event):
        """タイマーイベント処理（自動取得）
        
        Args:
            event: タイマーイベント
        """
        logger.debug(f"自動取得タイマー発火: {time.strftime('%H:%M:%S')}")
        self.fetch_timeline()
        
    def on_fetch_button(self, event):
        """タイムライン取得ボタンのイベント処理
        
        Args:
            event: ボタンイベント
        """
        logger.debug("タイムライン取得ボタンがクリックされました")
        self.fetch_timeline()
        
    def set_auto_fetch(self, enabled, interval=180):
        """自動取得の設定
        
        Args:
            enabled (bool): 自動取得の有効/無効
            interval (int, optional): 取得間隔（秒）. デフォルトは180秒.
        """
        self.auto_fetch_enabled = enabled
        self.fetch_interval = max(180, interval)  # 最小180秒
        
        # タイマーの設定
        if self.timer.IsRunning():
            self.timer.Stop()
            
        if enabled:
            # ミリ秒単位でタイマーを設定
            self.timer.Start(self.fetch_interval * 1000)
            logger.debug(f"自動取得を有効化しました: {self.fetch_interval}秒間隔")
        else:
            logger.debug("自動取得を無効化しました")
            
        # レイアウトの更新
        self.Layout()
        
    def show_not_logged_in_message(self):
        """未ログイン状態のメッセージを表示"""
        self.list_ctrl.show_not_logged_in_message()
        
    def fetch_timeline(self, client=None, selected_uri=None):
        """Bluesky APIを使用してタイムラインを取得
        
        Args:
            client (BlueskyClient, optional): Blueskyクライアント
            selected_uri (str, optional): 選択する投稿のURI
        """
        # 現在選択されている投稿のURIを記憶（引数で指定されていない場合）
        if selected_uri is None:
            selected_uri = self.list_ctrl.get_selected_post_uri()
            
        # クライアントが渡されなかった場合は親フレームから取得
        if not client:
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'client'):
                client = frame.client
        
        # クライアントがない場合は未ログイン状態のメッセージを表示
        if not client or not client.is_logged_in:
            logger.warning("タイムラインの取得に失敗しました: クライアントが設定されていません")
            self.show_not_logged_in_message()
            return
            
        try:
            # タイムラインの取得（最新50件）
            logger.info("タイムラインを取得しています...")
            timeline_data = client.get_timeline(limit=50)
            
            # 投稿データの変換
            new_posts = []
            edited_posts = []
            
            for post in timeline_data.feed:
                # 投稿データを適切な形式に変換
                post_data = {
                    'username': post.post.author.display_name or post.post.author.handle,
                    'handle': f"@{post.post.author.handle}",
                    'author_handle': post.post.author.handle,  # 投稿者のハンドル（@なし）
                    'content': post.post.record.text,
                    'time': format_relative_time(post.post.indexed_at),  # 表示用の文字列
                    'raw_timestamp': post.post.indexed_at,  # ソート用のオリジナルタイムスタンプ
                    'likes': getattr(post.post, 'like_count', 0),
                    'replies': getattr(post.post, 'reply_count', 0),
                    'reposts': getattr(post.post, 'repost_count', 0),
                    'uri': getattr(post.post, 'uri', None),  # 投稿のURI（削除に必要）
                    'cid': getattr(post.post, 'cid', None),  # 投稿のCID（削除に必要）
                    'is_own_post': post.post.author.handle == client.profile.handle,  # 自分の投稿かどうか
                    # スレッド情報を追加
                    'reply_parent': None,
                    'reply_root': None,
                    # facets情報を追加（URLなどの特殊要素の情報）
                    'facets': getattr(post.post.record, 'facets', None)
                }
                
                # スレッド情報を取得（返信の場合）
                if hasattr(post.post.record, 'reply') and post.post.record.reply:
                    logger.debug(f"返信投稿を検出: {post.post.uri}")
                    
                    # 親投稿の情報
                    if hasattr(post.post.record.reply, 'parent'):
                        parent_uri = getattr(post.post.record.reply.parent, 'uri', None)
                        parent_cid = getattr(post.post.record.reply.parent, 'cid', None)
                        
                        if parent_uri and parent_cid:
                            post_data['reply_parent'] = {
                                'uri': parent_uri,
                                'cid': parent_cid
                            }
                            logger.debug(f"親投稿情報: {parent_uri}")
                    
                    # ルート投稿の情報
                    if hasattr(post.post.record.reply, 'root'):
                        root_uri = getattr(post.post.record.reply.root, 'uri', None)
                        root_cid = getattr(post.post.record.reply.root, 'cid', None)
                        
                        if root_uri and root_cid:
                            post_data['reply_root'] = {
                                'uri': root_uri,
                                'cid': root_cid
                            }
                            logger.debug(f"ルート投稿情報: {root_uri}")
                
                # 既存の投稿かどうかをチェック
                existing_post_index = self.list_ctrl.find_post_by_uri(post_data['uri'])
                
                if existing_post_index >= 0:
                    # 既存の投稿がある場合、内容が変更されているかチェック
                    existing_post = self.list_ctrl.posts[existing_post_index]
                    if existing_post['content'] != post_data['content']:
                        # 内容が変更されている場合は編集された投稿として記録
                        logger.debug(f"編集された投稿を検出: {post_data['uri']}")
                        edited_posts.append((existing_post_index, post_data))
                else:
                    # 新しい投稿の場合はリストに追加
                    new_posts.append(post_data)
            
            # 編集された投稿を更新
            if edited_posts:
                for index, post_data in edited_posts:
                    self.list_ctrl.update_post(index, post_data)
                
                # 編集された投稿がある旨の警告ダイアログを表示
                wx.MessageBox(
                    f"{len(edited_posts)}件の投稿が編集されています。",
                    "投稿の編集を検出",
                    wx.OK | wx.ICON_INFORMATION
                )
            
            # 新しい投稿を追加
            if new_posts:
                # 投稿日時でソート（最新が下）- raw_timestampフィールドを使用
                new_posts.sort(key=lambda x: x['raw_timestamp'], reverse=False)
                self.list_ctrl.add_posts(new_posts)
                logger.info(f"新しい投稿を追加しました: {len(new_posts)}件")
            
            # 以前選択していた投稿と同じURIを持つ投稿を選択
            if selected_uri:
                self.list_ctrl.select_post_by_uri(selected_uri)
            
            logger.info(f"タイムラインを取得しました: 新規={len(new_posts)}件, 編集={len(edited_posts)}件")
            
        except Exception as e:
            logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def on_open_url(self, event):
        """URLを開くアクション
        
        Args:
            event: メニューイベント
        """
        self.list_ctrl.on_open_url(event)
    
    def get_selected_post(self):
        """選択中の投稿データを取得
        
        Returns:
            dict: 選択中の投稿データ。選択されていない場合はNone
        """
        return self.list_ctrl.get_selected_post()


class TimelineListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """タイムラインリストコントロールクラス"""
    
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
        
        # カラム設定
        self.InsertColumn(0, "ユーザー", width=150)
        self.InsertColumn(1, "投稿内容", width=400)
        self.InsertColumn(2, "時間", width=100)
        
        # 選択中の投稿インデックス
        self.selected_index = -1
        
        # 投稿データの初期化
        self.posts = []
        self.post_count = 0
        
        # イベントバインド
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # アクセシビリティ
        self.SetName("タイムラインリスト")
        
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
        """アイテム選択時の処理
        
        Args:
            event: リストイベント
        """
        self.selected_index = event.GetIndex()
        
        # 選択された投稿の情報を取得
        post = self.posts[self.selected_index]
        is_own_post = post.get('is_own_post', False)
        
        # 親フレームのメニューバーを取得
        frame = wx.GetTopLevelParent(self)
        menubar = frame.GetMenuBar()
        
        # ポストメニューを取得（インデックス1がポストメニュー）
        post_menu = menubar.GetMenu(1)
        
        # 「投稿を削除」メニュー項目を取得（インデックス5が削除）
        delete_item = post_menu.FindItemByPosition(5)
        
        # 自分の投稿かどうかに基づいて有効/無効を設定
        if delete_item:
            delete_item.Enable(is_own_post)
        
        event.Skip()
        
    def on_item_activated(self, event):
        """アイテムアクティベート時の処理（ダブルクリックなど）
        
        Args:
            event: リストイベント
        """
        index = event.GetIndex()
        post = self.posts[index]
        
        # 投稿の詳細表示（例：ダイアログ表示）
        dlg = PostDetailDialog(self, post)
        dlg.ShowModal()
        dlg.Destroy()
        
        event.Skip()
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        shift_down = event.ShiftDown()
        
        # F5キーでタイムライン更新
        if key_code == wx.WXK_F5:
            # 親パネルのタイムライン取得メソッドを呼び出す
            parent = self.GetParent()
            if hasattr(parent, 'on_fetch_button'):
                parent.on_fetch_button(event)
            return
        
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
                if shift_down:  # Ctrl+Shift+R
                    self.on_repost(event)
                else:  # Ctrl+R
                    self.on_reply(event)
                return
            elif key_code == ord('Q'):  # Ctrl+Q
                self.on_quote(event)
                return
            elif key_code == ord('P'):  # Ctrl+P
                self.on_profile(event)
                return
            elif key_code == ord('E'):  # Ctrl+E
                self.on_open_url(event)
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
        """コンテキストメニュー表示時の処理（右クリック）
        
        Args:
            event: マウスイベント
        """
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
        """コンテキストメニューを表示
        
        Args:
            pos: 表示位置
        """
        # 選択されている投稿
        post = self.posts[self.selected_index]
        
        # コンテキストメニューの作成
        menu = wx.Menu()
        
        # メニュー項目の追加（ショートカットキーとアクセラレータキー表示付き）
        like_item = menu.Append(wx.ID_ANY, "いいね(&L)\tCtrl+L")
        reply_item = menu.Append(wx.ID_ANY, "返信(&R)\tCtrl+R")
        repost_item = menu.Append(wx.ID_ANY, "リポスト(&T)\tCtrl+Shift+R")
        quote_item = menu.Append(wx.ID_ANY, "引用(&Q)\tCtrl+Q")
        profile_item = menu.Append(wx.ID_ANY, "投稿者のプロフィールを表示(&P)\tCtrl+P")
        open_url_item = menu.Append(wx.ID_ANY, "URLを開く(&E)\tCtrl+E")
        menu.AppendSeparator()  # 区切り線
        delete_item = menu.Append(wx.ID_ANY, "投稿を削除(&D)\tDel")
        
        # 自分の投稿以外は削除メニューを無効化
        if not post.get('is_own_post', False):
            delete_item.Enable(False)
        
        # イベントバインド
        self.Bind(wx.EVT_MENU, self.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.on_repost, repost_item)
        self.Bind(wx.EVT_MENU, self.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_open_url, open_url_item)
        self.Bind(wx.EVT_MENU, self.on_delete, delete_item)
        
        # 自分の投稿はリポストできない
        if post.get('is_own_post', False):
            repost_item.Enable(False)
        
        # メニュー表示
        self.PopupMenu(menu, pos)
        menu.Destroy()
        
    def on_like(self, event):
        """いいねアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_likeメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_like'):
                frame.on_like(event)
        
    def on_reply(self, event):
        """返信アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_replyメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_reply'):
                frame.on_reply(event)
        
    def on_quote(self, event):
        """引用アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_quoteメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_quote'):
                frame.on_quote(event)
                
    def on_repost(self, event):
        """リポストアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_repostメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_repost'):
                frame.on_repost(event)
        
    def on_profile(self, event):
        """プロフィール表示アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_profileメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_profile'):
                frame.on_profile(event)
            else:
                post = self.posts[self.selected_index]
                wx.MessageBox(f"プロフィールを表示します: {post['username']}", "プロフィール", wx.OK | wx.ICON_INFORMATION)
    
    def on_delete(self, event):
        """削除アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_deleteメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_delete'):
                frame.on_delete(event)
    
    def show_not_logged_in_message(self):
        """未ログイン状態のメッセージを表示"""
        # リストをクリア
        self.DeleteAllItems()
        self.posts = []
        self.post_count = 0
        self.selected_index = -1
        
        # 「ログインしていません」というアイテムを追加
        index = self.InsertItem(0, "")
        self.SetItem(index, 1, "ログインしていません")
        self.SetItem(index, 2, "")
        
        # ステータスバーの更新
        frame = wx.GetTopLevelParent(self)
        if hasattr(frame, 'statusbar'):
            frame.statusbar.SetStatusText("ログインしていません")
    
    def fetch_timeline(self, client=None, selected_uri=None):
        """Bluesky APIを使用してタイムラインを取得
        
        Args:
            client (BlueskyClient, optional): Blueskyクライアント
            selected_uri (str, optional): 選択する投稿のURI
        """
        # 現在選択されている投稿のURIを記憶（引数で指定されていない場合）
        if selected_uri is None and self.selected_index != -1 and self.selected_index < len(self.posts):
            selected_uri = self.posts[self.selected_index].get('uri')
            logger.info(f"現在選択されている投稿のURI: {selected_uri}")
        
        # クライアントが渡されなかった場合は親フレームから取得
        if not client:
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'client'):
                client = frame.client
        
        # クライアントがない場合は未ログイン状態のメッセージを表示
        if not client or not client.is_logged_in:
            logger.warning("タイムラインの取得に失敗しました: クライアントが設定されていません")
            self.show_not_logged_in_message()
            return
            
        try:
            # タイムラインの取得（最新50件）
            logger.info("タイムラインを取得しています...")
            timeline_data = client.get_timeline(limit=50)
            
            # 投稿データの変換と格納
            self.posts = []
            
            for post in timeline_data.feed:
                # 投稿情報のログ出力は削除
                
                # 投稿データを適切な形式に変換
                post_data = {
                    'username': post.post.author.display_name or post.post.author.handle,
                    'handle': f"@{post.post.author.handle}",
                    'author_handle': post.post.author.handle,  # 投稿者のハンドル（@なし）
                    'content': post.post.record.text,
                    'time': format_relative_time(post.post.indexed_at),  # 表示用の文字列
                    'raw_timestamp': post.post.indexed_at,  # ソート用のオリジナルタイムスタンプ
                    'likes': getattr(post.post, 'like_count', 0),
                    'replies': getattr(post.post, 'reply_count', 0),
                    'reposts': getattr(post.post, 'repost_count', 0),
                    'uri': getattr(post.post, 'uri', None),  # 投稿のURI（削除に必要）
                    'cid': getattr(post.post, 'cid', None),  # 投稿のCID（削除に必要）
                    'is_own_post': post.post.author.handle == client.profile.handle,  # 自分の投稿かどうか
                    # スレッド情報を追加
                    'reply_parent': None,
                    'reply_root': None,
                    # facets情報を追加（URLなどの特殊要素の情報）
                    'facets': getattr(post.post.record, 'facets', None)
                }
                
                # スレッド情報を取得（返信の場合）
                if hasattr(post.post.record, 'reply') and post.post.record.reply:
                    logger.debug(f"返信投稿を検出: {post.post.uri}")
                    
                    # 親投稿の情報
                    if hasattr(post.post.record.reply, 'parent'):
                        parent_uri = getattr(post.post.record.reply.parent, 'uri', None)
                        parent_cid = getattr(post.post.record.reply.parent, 'cid', None)
                        
                        if parent_uri and parent_cid:
                            post_data['reply_parent'] = {
                                'uri': parent_uri,
                                'cid': parent_cid
                            }
                            logger.debug(f"親投稿情報: {parent_uri}")
                    
                    # ルート投稿の情報
                    if hasattr(post.post.record.reply, 'root'):
                        root_uri = getattr(post.post.record.reply.root, 'uri', None)
                        root_cid = getattr(post.post.record.reply.root, 'cid', None)
                        
                        if root_uri and root_cid:
                            post_data['reply_root'] = {
                                'uri': root_uri,
                                'cid': root_cid
                            }
                            logger.debug(f"ルート投稿情報: {root_uri}")
                    
                    # デバッグ出力
                    logger.debug(f"スレッド情報: parent={post_data.get('reply_parent') is not None}, root={post_data.get('reply_root') is not None}")
                self.posts.append(post_data)
                
            # 投稿日時でソート（最新が下）- raw_timestampフィールドを使用
            self.posts.sort(key=lambda x: x['raw_timestamp'], reverse=False)
            self.post_count = len(self.posts)
            
            # UIの更新
            self.DeleteAllItems()
            self.init_ui()
            
            # 以前選択していた投稿と同じURIを持つ投稿を選択
            if selected_uri:
                for i, post in enumerate(self.posts):
                    if post.get('uri') == selected_uri:
                        logger.info(f"以前選択していた投稿を再選択: index={i}, uri={selected_uri}")
                        self.Select(i)
                        self.Focus(i)
                        self.selected_index = i
                        # 選択した項目が表示されるようにスクロール
                        self.EnsureVisible(i)
                        break
            
            logger.info(f"タイムラインを取得しました: {len(self.posts)}件")
            
        except Exception as e:
            logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def on_open_url(self, event):
        """URLを開くアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index == -1:
            return
            
        # 選択中の投稿を取得
        post = self.posts[self.selected_index]
        
        # URLユーティリティをインポート
        from utils.url_utils import handle_urls_in_text
        
        # 投稿内容からURLを検出して開く（facets情報も渡す）
        handle_urls_in_text(post['content'], self, post.get('facets'))
    
    def get_selected_post(self):
        """選択中の投稿データを取得
        
        Returns:
            dict: 選択中の投稿データ。選択されていない場合はNone
        """
        if 0 <= self.selected_index < len(self.posts):
            return self.posts[self.selected_index]
        return None
    
    def get_selected_post_uri(self):
        """選択中の投稿のURIを取得
        
        Returns:
            str: 選択中の投稿のURI。選択されていない場合はNone
        """
        post = self.get_selected_post()
        if post:
            return post.get('uri')
        return None
    
    def find_post_by_uri(self, uri):
        """URIから投稿を検索
        
        Args:
            uri (str): 検索する投稿のURI
            
        Returns:
            int: 投稿のインデックス。見つからない場合は-1
        """
        if not uri:
            return -1
            
        for i, post in enumerate(self.posts):
            if post.get('uri') == uri:
                return i
        return -1
    
    def update_post(self, index, post_data):
        """投稿を更新
        
        Args:
            index (int): 更新する投稿のインデックス
            post_data (dict): 新しい投稿データ
            
        Returns:
            bool: 更新に成功した場合はTrue
        """
        if 0 <= index < len(self.posts):
            # 投稿データを更新
            self.posts[index] = post_data
            
            # リストビューの表示を更新
            self.SetItem(index, 0, post_data['username'])
            self.SetItem(index, 1, post_data['content'])
            self.SetItem(index, 2, post_data['time'])
            
            logger.debug(f"投稿を更新しました: index={index}, uri={post_data.get('uri')}")
            return True
        return False
    
    def add_posts(self, new_posts):
        """新しい投稿を追加
        
        Args:
            new_posts (list): 追加する投稿のリスト
            
        Returns:
            int: 追加された投稿の数
        """
        if not new_posts:
            return 0
            
        # 現在の投稿数
        current_count = len(self.posts)
        
        # 新しい投稿を追加
        self.posts.extend(new_posts)
        self.post_count = len(self.posts)
        
        # リストビューに追加
        for i, post in enumerate(new_posts, start=current_count):
            index = self.InsertItem(i, post['username'])
            self.SetItem(index, 1, post['content'])
            self.SetItem(index, 2, post['time'])
            self.SetItemData(index, i)
        
        logger.debug(f"新しい投稿を追加しました: {len(new_posts)}件")
        return len(new_posts)
    
    def select_post_by_uri(self, uri):
        """URIから投稿を選択
        
        Args:
            uri (str): 選択する投稿のURI
            
        Returns:
            bool: 選択に成功した場合はTrue
        """
        index = self.find_post_by_uri(uri)
        if index >= 0:
            self.Select(index)
            self.Focus(index)
            self.selected_index = index
            # 選択した項目が表示されるようにスクロール
            self.EnsureVisible(index)
            logger.debug(f"投稿を選択しました: index={index}, uri={uri}")
            return True
        return False
