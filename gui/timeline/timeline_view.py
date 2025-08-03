#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインビュークラス（UI部分）
"""

import wx
import logging
import time
from utils.time_format import format_relative_time
from gui.timeline.list_ctrl import TimelineListCtrl
from gui.timeline.data_manager import TimelineDataManager
from core.exceptions import AuthenticationError

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
        
        # データマネージャーの初期化
        self.data_manager = TimelineDataManager()
        
        # 自動取得の設定
        self.auto_fetch_enabled = False
        self.fetch_interval = 180  # デフォルト：180秒
        self.fetch_count = 50      # デフォルト：50件
        
        # タイマー
        self.timer = wx.Timer(self, TIMER_ID)
        self.time_update_timer = wx.Timer(self, TIME_UPDATE_TIMER_ID)
        
        # 親ウィンドウのDestroyイベントをバインド
        top_parent = wx.GetTopLevelParent(self)
        top_parent.Bind(wx.EVT_WINDOW_DESTROY, self.on_parent_destroy)
        
        # UIの初期化
        self.init_ui()
        
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
        """Bluesky APIを使用してタイムラインを取得し、UI更新処理
        
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
            # データマネージャーに設定を適用
            self.data_manager.client = client
            self.data_manager.set_fetch_count(self.fetch_count)
            
            # データマネージャーからデータを取得
            new_posts_dict, new_post_uris = self.data_manager.fetch_data()
            
            # 既存のデータを更新
            temp_posts = self.data_manager.update_timeline_data(
                self.list_ctrl.posts,
                new_posts_dict,
                new_post_uris
            )
            
            # UIを更新
            self._update_timeline_display(temp_posts, selected_uri)
            
        except Exception as e:
            # 認証エラーの場合は特別な処理
            if isinstance(e, AuthenticationError):
                logger.error(f"認証エラー: {str(e)}")
                wx.MessageBox(
                    "セッションが無効になりました。再ログインが必要です。",
                    "認証エラー",
                    wx.OK | wx.ICON_ERROR
                )
                # 認証エラーが発生した場合、UIを未ログイン状態に更新する
                self.show_not_logged_in_message()
            else:
                logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def _update_timeline_display(self, posts, selected_uri=None):
        """タイムライン表示を更新
        
        Args:
            posts (list): 表示する投稿リスト
            selected_uri (str, optional): 選択する投稿のURI
        """
        # リストビューをクリア
        self.list_ctrl.DeleteAllItems()
        
        # 投稿データを更新
        self.list_ctrl.posts = posts
        self.list_ctrl.post_count = len(posts)
        
        # リストビューに投稿を追加
        for i, post in enumerate(posts):
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
        
        # 再描画を強制
        wx.CallAfter(self.list_ctrl.Refresh)
    
    def on_open_url(self, event):
        """URLを開くアクション
        
        Args:
            event: メニューイベント
        """
        self.list_ctrl.on_open_url(event)
    
    def remove_post_by_uri(self, uri):
        """URIから投稿を削除
        
        Args:
            uri (str): 削除する投稿のURI
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        return self.list_ctrl.remove_post_by_uri(uri)
    
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
        
    def Destroy(self):
        """ウィンドウ破棄時の処理"""
        self.stop_timers()
        # 設定マネージャーからオブザーバーを削除
        if hasattr(self, 'settings_manager'):
            self.settings_manager.remove_observer(self)
        return super(TimelineView, self).Destroy()
        
    def stop_timers(self):
        """タイマーを停止"""
        if hasattr(self, 'timer') and self.timer.IsRunning():
            self.timer.Stop()
            logger.debug("自動取得タイマーを停止しました")
            
        if hasattr(self, 'time_update_timer') and self.time_update_timer.IsRunning():
            self.time_update_timer.Stop()
            logger.debug("時間表示更新タイマーを停止しました")
            
    def on_parent_destroy(self, event):
        """親ウィンドウ破棄時の処理
        
        Args:
            event: ウィンドウ破棄イベント
        """
        self.stop_timers()
        event.Skip()  # イベントを伝播させる