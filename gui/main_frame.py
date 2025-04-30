#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインフレームクラス
"""

import wx
import logging
from pubsub import pub  # PubSub をインポート
from gui.timeline_view import TimelineView
from gui.handlers.auth_service import AuthService
from gui.handlers.post_handlers import PostHandlers
from core.client import BlueskyClient
from core.auth.auth_manager import AuthManager
from core import events # イベント名をインポート
from atproto_client.models.app.bsky.actor.defs import ProfileViewDetailed # 型ヒント用

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
        
        # ウィンドウクローズイベントをバインド
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # Blueskyクライアント
        self.client = BlueskyClient()
        
        # 認証マネージャー (シングルトン)
        self.auth_manager = AuthManager()
        
        # 設定マネージャー（シングルトン）
        from config.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        
        # タイムラインビューを設定マネージャーのオブザーバーとして登録
        # （TimelineViewのコンストラクタで自動的に登録されるため不要）

        # 認証サービス
        self.auth_service = AuthService(self.client, self.auth_manager)
        # ポストハンドラ (AuthService から client を取得するように変更も検討可能)
        self.post_handlers = PostHandlers(self, self.client)

        # UIの初期化
        self.init_ui()

        # PubSubイベントの購読設定
        self._subscribe_auth_events()

        # 中央に配置
        self.Centre()

        # 保存されたセッションを読み込んでログイン試行 (UI更新はイベント経由)
        self.auth_service.load_and_login()

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
        
        # ユーザー操作メニュー
        user_menu = wx.Menu()
        following_item = user_menu.Append(wx.ID_ANY, "フォロー中ユーザー一覧(&F)", "フォロー中のユーザー一覧を表示")
        followers_item = user_menu.Append(wx.ID_ANY, "フォロワー一覧(&W)", "フォロワーの一覧を表示")
        
        # メニューバーにメニューを追加
        menubar.Append(app_menu, "アプリ(&A)")
        menubar.Append(post_menu, "ポスト(&P)")
        menubar.Append(user_menu, "ユーザー操作(&U)")
        menubar.Append(settings_menu, "設定(&S)")
        
        # メニューバーをフレームに設定
        self.SetMenuBar(menubar)
        
        # イベントバインド (認証関連)
        self.Bind(wx.EVT_MENU, self._on_login_menu_select, self.login_item) # MainFrameのメソッドに変更
        self.Bind(wx.EVT_MENU, self._on_logout_menu_select, self.logout_item) # MainFrameのメソッドに変更
        self.Bind(wx.EVT_MENU, self.on_reset_database, reset_db_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        # イベントバインド (ポスト関連)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_new_post, new_post_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_repost, repost_item)
        self.Bind(wx.EVT_MENU, self.on_open_url, open_url_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_delete, delete_item)
        self.Bind(wx.EVT_MENU, self.post_handlers.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self.on_following_list, following_item)
        self.Bind(wx.EVT_MENU, self.on_followers_list, followers_item)

    # --- PubSub Event Handlers ---

    def _subscribe_auth_events(self):
        """認証関連のPubSubイベントを購読"""
        pub.subscribe(self._on_login_success, events.AUTH_LOGIN_SUCCESS)
        pub.subscribe(self._on_session_load_success, events.AUTH_SESSION_LOAD_SUCCESS)
        pub.subscribe(self._on_logout_success, events.AUTH_LOGOUT_SUCCESS)
        pub.subscribe(self._on_login_failure, events.AUTH_LOGIN_FAILURE)
        pub.subscribe(self._on_session_load_failure, events.AUTH_SESSION_LOAD_FAILURE)
        pub.subscribe(self._on_session_invalid, events.AUTH_SESSION_INVALID)
        # 必要に応じて他のイベントも購読
        # pub.subscribe(self._on_login_attempt, events.AUTH_LOGIN_ATTEMPT)
        # pub.subscribe(self._on_session_saved, events.AUTH_SESSION_SAVED)
        # pub.subscribe(self._on_session_deleted, events.AUTH_SESSION_DELETED)
        logger.debug("Subscribed to authentication events.")

    def _on_login_success(self, profile: ProfileViewDetailed):
        """ログイン成功イベントハンドラ"""
        logger.info(f"Login successful event received for: {profile.handle}")
        self.SetTitle(f"SSky - [{profile.handle}]")
        self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
        self.update_login_status(True)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(True)
        # タイムラインを取得
        self.statusbar.SetStatusText("タイムラインを更新しています...")
        if hasattr(self.timeline, 'fetch_timeline'):
            # fetch_timeline が client を引数に取るか確認
            self.timeline.fetch_timeline(self.client) # client を渡す
            self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")

    def _on_session_load_success(self, profile: ProfileViewDetailed):
        """セッションからのログイン成功イベントハンドラ"""
        logger.info(f"Session load successful event received for: {profile.handle}")
        self.SetTitle(f"SSky - [{profile.handle}]")
        self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
        self.update_login_status(True)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(True)
        # タイムラインを取得
        self.statusbar.SetStatusText("タイムラインを更新しています...")
        if hasattr(self.timeline, 'fetch_timeline'):
            self.timeline.fetch_timeline(self.client)
            self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")

    def _on_logout_success(self):
        """ログアウト成功イベントハンドラ"""
        logger.info("Logout successful event received.")
        self.SetTitle("SSky")
        self.statusbar.SetStatusText("ログアウトしました")
        self.update_login_status(False)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(False)
        elif hasattr(self.timeline, 'show_not_logged_in_message'):
             self.timeline.show_not_logged_in_message()
        # ログアウト完了ダイアログ
        # wx.MessageBox("ログアウトしました", "ログアウト完了", wx.OK | wx.ICON_INFORMATION, parent=self)


    def _on_login_failure(self, error: Exception):
        """ログイン失敗イベントハンドラ"""
        logger.error(f"Login failure event received: {error}")
        self.statusbar.SetStatusText("ログインに失敗しました")
        self.update_login_status(False)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(False)
        elif hasattr(self.timeline, 'show_not_logged_in_message'):
             self.timeline.show_not_logged_in_message()
        # エラーダイアログ表示
        error_message = f"ログインに失敗しました: {str(error)}\n\n2段階認証を設定しているアカウントは、アプリパスワードを使用してください。"
        wx.MessageBox(error_message, "ログイン失敗", wx.OK | wx.ICON_ERROR, parent=self)
        # 失敗後に再度ログインダイアログを表示するロジックが必要ならここに追加
        # self._on_login_menu_select(None)

    def _on_session_load_failure(self, error: Exception | None, needs_relogin: bool):
        """セッション読み込み失敗イベントハンドラ"""
        logger.warning(f"Session load failure event received: error={error}, needs_relogin={needs_relogin}")
        if needs_relogin:
            self.statusbar.SetStatusText("セッションが無効か、読み込みに失敗しました。再ログインが必要です。")
        else:
            self.statusbar.SetStatusText("セッション情報が見つかりませんでした。")
        self.update_login_status(False)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(False)
        elif hasattr(self.timeline, 'show_not_logged_in_message'):
             self.timeline.show_not_logged_in_message()
        # 必要ならエラーメッセージ表示
        if error:
             wx.MessageBox(f"セッションの読み込みに失敗しました: {error}", "セッションエラー", wx.OK | wx.ICON_WARNING, parent=self)

    def _on_session_invalid(self, error: Exception, did: str):
        """セッション無効イベントハンドラ"""
        logger.error(f"Session invalid event received for DID {did}: {error}")
        self.statusbar.SetStatusText("セッションが無効になりました。再ログインしてください。")
        self.update_login_status(False)
        # タイムラインビューも更新
        if hasattr(self.timeline, 'update_login_status'):
            self.timeline.update_login_status(False)
        elif hasattr(self.timeline, 'show_not_logged_in_message'):
             self.timeline.show_not_logged_in_message()
        wx.MessageBox(f"セッションが無効になりました: {error}\n再ログインが必要です。", "セッションエラー", wx.OK | wx.ICON_ERROR, parent=self)


    # --- Menu Event Handlers ---

    def _on_login_menu_select(self, event):
        """ログインメニュー選択時の処理"""
        # AuthService にログインダイアログ表示を依頼
        self.auth_service.show_login_dialog(self)

    def _on_logout_menu_select(self, event):
        """ログアウトメニュー選択時の処理"""
        # AuthService にログアウト処理を依頼
        self.auth_service.perform_logout()

    def update_login_status(self, is_logged_in):
        """ログイン状態に応じてUI（メニュー項目）を更新
        
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
        
    def OnClose(self, event):
        """ウィンドウが閉じられる前の処理
        
        Args:
            event: クローズイベント
        """
        # セッション保存は AuthService の _handle_session_change で自動的に行われるため、
        # ここでの明示的な保存は不要（重複や競合の可能性がある）
        logger.debug("MainFrame OnClose called.")
        # イベントを処理（ウィンドウを閉じる）
        event.Skip() # これによりデフォルトのクローズ処理が実行される
        
    def on_settings(self, event):
        """設定ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        from gui.dialogs.settings_dialog import SettingsDialog
        
        # 設定ダイアログの表示
        dialog = SettingsDialog(self)
        result = dialog.ShowModal()
        
        if result == wx.ID_OK:
            logger.debug("設定ダイアログがOKで閉じられました。")
            # 設定変更の通知は自動的に行われるため、ここでの処理は不要
        else:
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
                self.auth_service.perform_logout()
            
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
            
    def on_following_list(self, event):
        """フォロー中ユーザー一覧ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("フォロー中ユーザー一覧を表示するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        from gui.dialogs.following_dialog import FollowingDialog
        dialog = FollowingDialog(self, self.client)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_followers_list(self, event):
        """フォロワー一覧ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("フォロワー一覧を表示するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        from gui.dialogs.followers_dialog import FollowersDialog
        dialog = FollowersDialog(self, self.client)
        dialog.ShowModal()
        dialog.Destroy()
