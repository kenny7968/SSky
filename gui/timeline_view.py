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
TIME_UPDATE_TIMER_ID = 1001

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
        self.fetch_count = 50      # デフォルト：50件
        
        # タイマー
        self.timer = wx.Timer(self, TIMER_ID)
        self.time_update_timer = wx.Timer(self, TIME_UPDATE_TIMER_ID)
        
        # UIの初期化
        self.init_ui()
        
        # 投稿データの初期化
        self.posts = []
        self.post_count = 0
        
        # イベントバインド
        self.Bind(wx.EVT_TIMER, self.on_timer, id=TIMER_ID)
        self.Bind(wx.EVT_TIMER, self.on_time_update_timer, id=TIME_UPDATE_TIMER_ID)
        self.Bind(wx.EVT_BUTTON, self.on_fetch_button, self.fetch_button)
        
        # 時間表示更新タイマーを開始（1分ごと）
        self.time_update_timer.Start(60 * 1000)  # 60秒 = 1分
        
        # アクセシビリティ
        self.SetName("タイムラインパネル")
        
        # 設定マネージャーを取得し、オブザーバーとして登録
        from config.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        self.settings_manager.add_observer(self)
        
        # 設定から自動取得の設定を読み込む
        self.load_settings()
        
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
        self.title_label = wx.StaticText(self, label="ホームタイムライン")
        # フォントを大きくして目立たせる
        font = self.title_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(font)
        main_sizer.Add(self.title_label, 0, wx.LEFT | wx.TOP, 10)
        
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
    
    def on_time_update_timer(self, event):
        """時間表示更新タイマーイベント処理
        
        Args:
            event: タイマーイベント
        """
        logger.debug(f"時間表示更新タイマー発火: {time.strftime('%H:%M:%S')}")
        self.update_post_times()
    
    def update_post_times(self):
        """投稿の時間表示を更新"""
        if not self.list_ctrl.posts:
            return
            
        # 投稿の時間表示を更新
        updated = False
        for i, post in enumerate(self.list_ctrl.posts):
            # raw_timestampから相対時間を再計算
            new_time = format_relative_time(post['raw_timestamp'])
            
            # 表示が変わった場合のみ更新
            if new_time != post['time']:
                post['time'] = new_time
                self.list_ctrl.SetItem(i, 2, new_time)
                updated = True
                
        if updated:
            logger.debug("投稿の時間表示を更新しました")
        
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
        
    def update_login_status(self, is_logged_in):
        """ログイン状態に応じてUIを更新
        
        Args:
            is_logged_in (bool): ログイン状態
        """
        if is_logged_in:
            # ログイン状態
            self.title_label.SetLabel("ホームタイムライン")
        else:
            # 未ログイン状態
            self.title_label.SetLabel("ホームタイムライン - ログインしていません")
            
            # リストをクリア
            self.list_ctrl.DeleteAllItems()
            self.list_ctrl.posts = []
            self.list_ctrl.post_count = 0
            self.list_ctrl.selected_index = -1
            
            # ステータスバーの更新
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'statusbar'):
                frame.statusbar.SetStatusText("ログインしていません")
    
    def show_not_logged_in_message(self):
        """未ログイン状態のメッセージを表示"""
        self.update_login_status(False)
        
    def fetch_timeline(self, client=None, selected_uri=None):
        """Bluesky APIを使用してタイムラインを取得し、既存の投稿を保持しつつ更新
        
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
            # タイムラインの取得
            logger.info(f"タイムラインを取得しています... (最大{self.fetch_count}件)")
            timeline_data = client.get_timeline(limit=self.fetch_count)
            
            # 新しく取得した投稿のURIセットを作成（高速検索用）
            new_post_uris = set()
            new_posts_dict = {}  # 一時的な辞書（URIをキー）
            
            # 取得した投稿を処理
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
                    'facets': getattr(post.post.record, 'facets', None),
                    # 引用ポスト情報を初期化
                    'quote_of': None,
                    'is_quote_post': False
                }
                
                # embedフィールドの確認（引用ポストかどうか）
                from atproto import models
                if hasattr(post.post, 'embed'):
                    embed = post.post.embed
                    
                    # 引用ポストの場合
                    if isinstance(embed, models.AppBskyEmbedRecord.View):
                        logger.debug(f"引用ポストを検出: {post.post.uri}")
                        
                        # 引用元レコードの情報を取得
                        if hasattr(embed, 'record'):
                            quoted_record = embed.record
                            
                            # ViewRecordの場合（通常のケース）
                            if isinstance(quoted_record, models.AppBskyEmbedRecord.ViewRecord):
                                quoted_author = quoted_record.author
                                quoted_text = getattr(quoted_record.value, 'text', '[引用元テキストなし]')
                                
                                # 引用元情報を設定
                                post_data['is_quote_post'] = True
                                post_data['quote_of'] = {
                                    'username': quoted_author.display_name or quoted_author.handle,
                                    'handle': f"@{quoted_author.handle}",
                                    'content': quoted_text,
                                    'uri': getattr(quoted_record, 'uri', None),
                                    'cid': getattr(quoted_record, 'cid', None),
                                    'like_count': getattr(quoted_record, 'like_count', 0),
                                    'repost_count': getattr(quoted_record, 'repost_count', 0)
                                }
                                logger.debug(f"引用元情報: {quoted_author.handle} - {quoted_text[:30]}...")
                            
                            # 引用元が見つからない場合
                            elif isinstance(quoted_record, models.AppBskyEmbedRecord.ViewNotFound):
                                post_data['is_quote_post'] = True
                                post_data['quote_of'] = {
                                    'username': '不明',
                                    'handle': '@unknown',
                                    'content': '[引用元投稿が見つかりません]',
                                    'uri': None,
                                    'cid': None
                                }
                                logger.debug("引用元投稿が見つかりません")
                            
                            # 引用元がブロックされている場合
                            elif isinstance(quoted_record, models.AppBskyEmbedRecord.ViewBlocked):
                                post_data['is_quote_post'] = True
                                post_data['quote_of'] = {
                                    'username': 'ブロック',
                                    'handle': '@blocked',
                                    'content': '[引用元投稿はブロックされています]',
                                    'uri': None,
                                    'cid': None
                                }
                                logger.debug("引用元投稿はブロックされています")
                    
                    # 引用ポスト + メディアの場合
                    elif isinstance(embed, models.AppBskyEmbedRecordWithMedia.View):
                        logger.debug(f"引用ポスト + メディアを検出: {post.post.uri}")
                        
                        # 引用元レコードの情報を取得
                        if hasattr(embed, 'record') and hasattr(embed.record, 'record'):
                            quoted_record = embed.record.record
                            
                            # ViewRecordの場合（通常のケース）
                            if isinstance(quoted_record, models.AppBskyEmbedRecord.ViewRecord):
                                quoted_author = quoted_record.author
                                quoted_text = getattr(quoted_record.value, 'text', '[引用元テキストなし]')
                                
                                # 引用元情報を設定
                                post_data['is_quote_post'] = True
                                post_data['quote_of'] = {
                                    'username': quoted_author.display_name or quoted_author.handle,
                                    'handle': f"@{quoted_author.handle}",
                                    'content': quoted_text,
                                    'uri': getattr(quoted_record, 'uri', None),
                                    'cid': getattr(quoted_record, 'cid', None),
                                    'like_count': getattr(quoted_record, 'like_count', 0),
                                    'repost_count': getattr(quoted_record, 'repost_count', 0)
                                }
                                logger.debug(f"引用元情報 (メディア付き): {quoted_author.handle} - {quoted_text[:30]}...")
                
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
                
                uri = post_data['uri']
                if uri:
                    new_post_uris.add(uri)
                    new_posts_dict[uri] = post_data
            
            # 既存の投稿URIセットとマッピングを作成
            existing_post_uris = set()
            uri_to_index = {}  # URIからリストのインデックスへのマッピング
            
            for i, post in enumerate(self.list_ctrl.posts):
                if 'uri' in post and post['uri']:
                    uri = post['uri']
                    existing_post_uris.add(uri)
                    uri_to_index[uri] = i
            
            # 1. 新しく追加された投稿を特定
            added_uris = new_post_uris - existing_post_uris
            
            # 2. 更新された投稿を特定（両方のセットに存在するURI）
            updated_uris = new_post_uris.intersection(existing_post_uris)
            updated_count = 0
            
            # テンポラリの投稿リストを作成（既存の投稿をコピー）
            temp_posts = self.list_ctrl.posts.copy()
            
            # 既存の投稿を更新（インデックスマッピングを使用して高速化）
            for uri in updated_uris:
                if uri in uri_to_index:
                    index = uri_to_index[uri]
                    # 実際に変更があるかチェック（いいね数、リポスト数、返信数）
                    old_post = temp_posts[index]
                    new_post = new_posts_dict[uri]
                    
                    if (old_post['likes'] != new_post['likes'] or 
                        old_post['reposts'] != new_post['reposts'] or 
                        old_post['replies'] != new_post['replies']):
                        # 投稿を更新
                        temp_posts[index] = new_post
                        updated_count += 1
            
            # 新しい投稿を追加
            for uri in added_uris:
                temp_posts.append(new_posts_dict[uri])
            
            # 投稿を日時でソート（古い順）
            temp_posts.sort(key=lambda x: x['raw_timestamp'])
            
            # 投稿数を制限（オプション）
            max_posts = 1000  # 保持する最大投稿数
            if len(temp_posts) > max_posts:
                # 新しい投稿を優先して保持（古い投稿を削除）
                temp_posts = temp_posts[len(temp_posts) - max_posts:]
                logger.debug(f"古い投稿を削除しました。残り{len(temp_posts)}件")
            
            # リストビューをクリア
            self.list_ctrl.DeleteAllItems()
            
            # 投稿データを更新
            self.list_ctrl.posts = temp_posts
            self.list_ctrl.post_count = len(temp_posts)
            
            # リストビューに投稿を追加
            for i, post in enumerate(temp_posts):
                index = self.list_ctrl.InsertItem(i, post['username'])
                
                # 引用ポストの場合は引用元情報も表示
                if post.get('is_quote_post', False) and post.get('quote_of'):
                    quote_info = post['quote_of']
                    display_content = f"{post['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
                else:
                    display_content = post['content']
                
                self.list_ctrl.SetItem(index, 1, display_content)
                self.list_ctrl.SetItem(index, 2, post['time'])
                self.list_ctrl.SetItemData(index, i)
            
            # 以前選択していた投稿と同じURIを持つ投稿を選択
            if selected_uri:
                self.list_ctrl.select_post_by_uri(selected_uri)
            
            logger.info(f"タイムラインを更新しました: 新規={len(added_uris)}件, 更新={updated_count}件, 合計={len(temp_posts)}件")
            
            # 再描画を強制
            wx.CallAfter(self.list_ctrl.Refresh)
            
        except Exception as e:
            # 認証エラーの場合は特別な処理
            from core.client import AuthenticationError
            if isinstance(e, AuthenticationError):
                logger.error(f"認証エラー: {str(e)}")
                wx.MessageBox(
                    "セッションが無効になりました。再ログインが必要です。",
                    "認証エラー",
                    wx.OK | wx.ICON_ERROR
                )
                
                # 親フレームのログインダイアログを表示
                frame = wx.GetTopLevelParent(self)
                if hasattr(frame, 'auth_handlers') and hasattr(frame.auth_handlers, 'on_login'):
                    wx.CallAfter(frame.auth_handlers.on_login, None)
                    
                # 未ログイン状態のメッセージを表示
                self.show_not_logged_in_message()
            else:
                logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def on_open_url(self, event):
        """URLを開くアクション
        
        Args:
            event: メニューイベント
        """
        self.list_ctrl.on_open_url(event)
    
    def load_settings(self):
        """設定から自動取得の設定を読み込む"""
        auto_fetch = self.settings_manager.get('timeline.auto_fetch', True)
        fetch_interval = self.settings_manager.get('timeline.fetch_interval', 180)
        fetch_count = self.settings_manager.get('timeline.fetch_count', 50)
        logger.debug(f"設定から自動取得の設定を読み込みました: auto_fetch={auto_fetch}, fetch_interval={fetch_interval}, fetch_count={fetch_count}")
        self.set_auto_fetch(auto_fetch, fetch_interval)
        self.fetch_count = fetch_count
    
    def on_settings_changed(self, key=None):
        """設定変更時の処理
        
        Args:
            key (str, optional): 変更された設定キー
        """
        # タイムライン関連の設定が変更された場合、または全体の設定が変更された場合
        if key is None or key.startswith('timeline.'):
            logger.debug(f"設定変更を検出しました: key={key}")
            self.load_settings()
    
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
            
            # 引用ポストの場合は引用元情報も表示
            if post.get('is_quote_post', False) and post.get('quote_of'):
                quote_info = post['quote_of']
                display_content = f"{post['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
            else:
                display_content = post['content']
                
            self.SetItem(index, 1, display_content)
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
            
            # 引用ポストの場合は引用元情報も表示
            if post_data.get('is_quote_post', False) and post_data.get('quote_of'):
                quote_info = post_data['quote_of']
                display_content = f"{post_data['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
            else:
                display_content = post_data['content']
            
            # リストビューの表示を更新
            self.SetItem(index, 0, post_data['username'])
            self.SetItem(index, 1, display_content)
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
            
            # 引用ポストの場合は引用元情報も表示
            if post.get('is_quote_post', False) and post.get('quote_of'):
                quote_info = post['quote_of']
                display_content = f"{post['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
            else:
                display_content = post['content']
                
            self.SetItem(index, 1, display_content)
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
