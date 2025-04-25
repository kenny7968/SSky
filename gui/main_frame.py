#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインフレームクラス
"""

import wx
import logging
from gui.timeline_view import TimelineView
from gui.handlers.auth_handlers import AuthHandlers
from gui.handlers.post_handlers import PostHandlers
from core.client import BlueskyClient
from core.auth.auth_manager import AuthManager

# ロガーの設定
logger = logging.getLogger(__name__)

class MainFrame(wx.Frame):
    """SSkyメインウィンドウクラス"""
    
    def __init__(self, parent, title, size=(800, 600)):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            title (str): ウィンドウタイトル
            size (tuple): ウィンドウサイズ
        """
        super(MainFrame, self).__init__(
            parent, 
            title=title, 
            size=size,
            style=wx.DEFAULT_FRAME_STYLE
        )
        
        # Blueskyクライアント
        self.client = BlueskyClient()
        
        # ユーザー名（ログイン後に設定）
        self.username = None
        
        # 認証マネージャー
        self.auth_manager = AuthManager()
        
        # 設定マネージャー
        from config.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        
        # イベントハンドラ
        self.auth_handlers = AuthHandlers(self, self.client, self.auth_manager)
        self.post_handlers = PostHandlers(self, self.client)
        
        # UIの初期化
        self.init_ui()
        
        # 中央に配置
        self.Centre()
        
        # 保存されたセッションを読み込み
        self.auth_handlers.load_session()
        
        # 設定に基づいて自動取得を設定
        self.apply_timeline_settings()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        
        # レイアウト
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # メニューバーの作成
        self.create_menu_bar()
        
        # タイムラインビューの作成
        self.timeline = TimelineView(panel)
        main_sizer.Add(self.timeline, 1, wx.EXPAND | wx.ALL, 5)
        
        # ステータスバーの作成
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("準備完了")
        
        panel.SetSizer(main_sizer)
        
    def create_menu_bar(self):
        """メニューバーの作成"""
        menubar = wx.MenuBar()
        
        # アプリメニュー
        app_menu = wx.Menu()
        self.login_item = app_menu.Append(wx.ID_ANY, "Blueskyにログイン(&A)", "Blueskyにログイン")
        self.logout_item = app_menu.Append(wx.ID_ANY, "ログアウト(&L)", "Blueskyからログアウト")
        self.logout_item.Enable(False)  # 初期状態では無効
        app_menu.AppendSeparator()  # 区切り線
        reset_db_item = app_menu.Append(wx.ID_ANY, "データベースをリセット(&R)", "データベースをリセットして再初期化")
        app_menu.AppendSeparator()  # 区切り線
        exit_item = app_menu.Append(wx.ID_EXIT, "終了(&X)", "アプリケーションを終了")
        
        # ポストメニュー
        post_menu = wx.Menu()
        new_post_item = post_menu.Append(wx.ID_ANY, "新規投稿(&N)\tCtrl+N", "新しい投稿を作成")
        post_menu.AppendSeparator()  # 区切り線
        like_item = post_menu.Append(wx.ID_ANY, "いいね(&L)\tCtrl+L", "投稿にいいねする")
        reply_item = post_menu.Append(wx.ID_ANY, "返信(&R)\tCtrl+R", "投稿に返信する")
        repost_item = post_menu.Append(wx.ID_ANY, "リポスト(&T)\tCtrl+Shift+R", "投稿をリポストする")
        quote_item = post_menu.Append(wx.ID_ANY, "引用(&Q)\tCtrl+Q", "投稿を引用する")
        open_url_item = post_menu.Append(wx.ID_ANY, "URLを開く(&E)\tCtrl+E", "投稿内のURLを開く")
        delete_item = post_menu.Append(wx.ID_ANY, "投稿を削除(&D)\tDel", "投稿を削除する")
        post_menu.AppendSeparator()  # 区切り線
        profile_item = post_menu.Append(wx.ID_ANY, "投稿者のプロフィールを表示(&P)\tCtrl+P", "投稿者のプロフィールを表示")
        
        # 設定メニュー
        settings_menu = wx.Menu()
        settings_item = settings_menu.Append(wx.ID_ANY, "設定(&S)", "アプリケーション設定")
        
        # メニューバーにメニューを追加
        menubar.Append(app_menu, "アプリ(&A)")
        menubar.Append(post_menu, "ポスト(&P)")
        menubar.Append(settings_menu, "設定(&S)")
        
        # メニューバーをフレームに設定
        self.SetMenuBar(menubar)
        
        # イベントバインド
        self.Bind(wx.EVT_MENU, self.auth_handlers.on_login, self.login_item)
        self.Bind(wx.EVT_MENU, self.auth_handlers.on_logout, self.logout_item)
        self.Bind(wx.EVT_MENU, self.on_reset_database, reset_db_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_new_post, new_post_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_repost, repost_item)
        self.Bind(wx.EVT_MENU, self.on_open_url, open_url_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_delete, delete_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
    
    def set_username(self, username):
        """ユーザー名を設定し、タイトルを更新
        
        Args:
            username (str): ユーザー名
        """
        self.username = username
        self.SetTitle(f"SSky - [{username}]")
        
        # ログイン状態も更新
        self.update_login_status(True)
    
    def update_login_status(self, is_logged_in):
        """ログイン状態に応じてUIを更新
        
        Args:
            is_logged_in (bool): ログイン状態
        """
        self.login_item.Enable(not is_logged_in)
        self.logout_item.Enable(is_logged_in)
    
    def on_exit(self, event):
        """アプリケーションを終了
        
        Args:
            event: メニューイベント
        """
        self.Close()
        
    def on_settings(self, event):
        """設定ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        from gui.dialogs.settings_dialog import SettingsDialog
        from config.settings_manager import SettingsManager
        
        # 設定マネージャーの取得
        if not hasattr(self, 'settings_manager'):
            self.settings_manager = SettingsManager()
        
        # 設定ダイアログの表示
        dialog = SettingsDialog(self, self.settings_manager)
        result = dialog.ShowModal()
        
        if result == wx.ID_OK:
            # 設定が変更された場合の処理
            # タイムラインの自動更新設定を反映
            logger = logging.getLogger(__name__)
            logger.debug("設定ダイアログがOKで閉じられました。設定を反映します。")
            
            # タイムラインの自動更新設定を反映
            if hasattr(self, 'timeline'):
                auto_fetch = self.settings_manager.get('timeline.auto_fetch', True)
                fetch_interval = self.settings_manager.get('timeline.fetch_interval', 180)
                logger.debug(f"タイムラインの自動更新設定: auto_fetch={auto_fetch}, fetch_interval={fetch_interval}")
                
                # タイムラインの自動更新設定を反映するメソッドがあれば呼び出す
                if hasattr(self.timeline, 'set_auto_fetch'):
                    self.timeline.set_auto_fetch(auto_fetch, fetch_interval)
        else:
            logger = logging.getLogger(__name__)
            logger.debug("設定ダイアログがキャンセルで閉じられました。")
        
        dialog.Destroy()
        
    # イベントハンドラのプロキシメソッド
    def on_like(self, event):
        """いいねアクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_like(event)
        
    def on_reply(self, event):
        """返信アクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_reply(event)
        
    def on_quote(self, event):
        """引用アクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_quote(event)
        
    def on_repost(self, event):
        """リポストアクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_repost(event)
        
    def on_profile(self, event):
        """プロフィール表示アクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_profile(event)
        
    def on_delete(self, event):
        """投稿削除アクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_delete(event)
        
    def on_new_post(self, event):
        """新規投稿アクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        self.post_handlers.on_new_post(event)
        
    def on_open_url(self, event):
        """URLを開くアクション（プロキシ）
        
        Args:
            event: メニューイベント
        """
        if hasattr(self, 'timeline') and hasattr(self.timeline, 'on_open_url'):
            self.timeline.on_open_url(event)
    
    def on_reset_database(self, event):
        """データベースをリセット
        
        Args:
            event: メニューイベント
        """
        # 確認ダイアログを表示
        dlg = wx.MessageDialog(
            self,
            "データベースをリセットすると、すべてのログイン情報とセッション情報が削除されます。\n"
            "アプリケーションを再起動する必要があります。\n\n"
            "続行しますか？",
            "データベースのリセット確認",
            wx.YES_NO | wx.ICON_EXCLAMATION
        )
        
        result = dlg.ShowModal()
        dlg.Destroy()
        
        if result == wx.ID_YES:
            import os
            
            # データベースファイルのパスを取得
            db_path = self.auth_manager.data_store.db_path
            
            # ログアウト処理を実行（セッション情報をクリア）
            if self.client and hasattr(self.client, 'profile') and self.client.profile:
                self.auth_handlers.on_logout(None)
            
            # データベースファイルを削除
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                    logger.info(f"データベースファイルを削除しました: {db_path}")
                    
                    # 成功メッセージを表示
                    wx.MessageBox(
                        "データベースをリセットしました。\n"
                        "アプリケーションを再起動してください。",
                        "データベースのリセット完了",
                        wx.OK | wx.ICON_INFORMATION
                    )
                    
                    # アプリケーションを終了
                    self.Close()
                else:
                    logger.warning(f"データベースファイルが見つかりませんでした: {db_path}")
                    wx.MessageBox(
                        "データベースファイルが見つかりませんでした。\n"
                        "アプリケーションを再起動してください。",
                        "警告",
                        wx.OK | wx.ICON_WARNING
                    )
            except Exception as e:
                logger.error(f"データベースファイルの削除に失敗しました: {str(e)}")
                wx.MessageBox(
                    f"データベースファイルの削除に失敗しました: {str(e)}\n"
                    "アプリケーションを再起動して再試行してください。",
                    "エラー",
                    wx.OK | wx.ICON_ERROR
                )
    
    def apply_timeline_settings(self):
        """設定に基づいてタイムラインの自動取得を設定"""
        if hasattr(self, 'timeline') and hasattr(self.timeline, 'set_auto_fetch'):
            # 設定マネージャーから自動取得の設定を取得
            auto_fetch = self.settings_manager.get('timeline.auto_fetch', True)
            fetch_interval = self.settings_manager.get('timeline.fetch_interval', 180)
            
            logger.debug(f"タイムラインの自動更新設定を適用: auto_fetch={auto_fetch}, fetch_interval={fetch_interval}")
            
            # タイムラインビューに設定を適用
            self.timeline.set_auto_fetch(auto_fetch, fetch_interval)
