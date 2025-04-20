#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインフレームクラス
"""

import wx
import wx.lib.dialogs
import logging
from timeline_view import TimelineView
from atproto import Client
from atproto.exceptions import AtProtocolError
from auth_utils import AuthUtils

# ロガーの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainFrame(wx.Frame):
    """SSkyメインウィンドウクラス"""
    
    def __init__(self, parent, title):
        """初期化"""
        super(MainFrame, self).__init__(
            parent, 
            title=title, 
            size=(800, 600),
            style=wx.DEFAULT_FRAME_STYLE
        )
        
        # Blueskyクライアント
        self.client = None
        
        # ユーザー名（ログイン後に設定）
        self.username = None
        
        # 認証ユーティリティ
        self.auth_utils = AuthUtils()
        
        # UIの初期化
        self.init_ui()
        
        # 中央に配置
        self.Centre()
        
        # 保存されたセッションを読み込み
        self.load_saved_session()
        
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
        self.login_item = app_menu.Append(wx.ID_ANY, "ログイン情報の設定(&A)", "Blueskyのログイン情報を設定")
        self.logout_item = app_menu.Append(wx.ID_ANY, "ログアウト(&L)", "Blueskyからログアウト")
        self.logout_item.Enable(False)  # 初期状態では無効
        app_menu.AppendSeparator()  # 区切り線
        exit_item = app_menu.Append(wx.ID_EXIT, "終了(&X)", "アプリケーションを終了")
        
        # ポストメニュー
        post_menu = wx.Menu()
        new_post_item = post_menu.Append(wx.ID_ANY, "新規投稿(&N)\tCtrl+N", "新しい投稿を作成")
        post_menu.AppendSeparator()  # 区切り線
        like_item = post_menu.Append(wx.ID_ANY, "いいね(&L)\tCtrl+L", "投稿にいいねする")
        reply_item = post_menu.Append(wx.ID_ANY, "返信(&R)\tCtrl+R", "投稿に返信する")
        quote_item = post_menu.Append(wx.ID_ANY, "引用(&Q)\tCtrl+Q", "投稿を引用する")
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
        self.Bind(wx.EVT_MENU, self.on_login, self.login_item)
        self.Bind(wx.EVT_MENU, self.on_logout, self.logout_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_new_post, new_post_item)
        self.Bind(wx.EVT_MENU, self.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.on_delete, delete_item)
        self.Bind(wx.EVT_MENU, self.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
    
    def set_username(self, username):
        """ユーザー名を設定し、タイトルを更新"""
        self.username = username
        self.SetTitle(f"SSky - [{username}]")
    
    def load_saved_session(self):
        """保存されたログイン情報を読み込み、ログイン処理を実行"""
        try:
            # ログイン情報を読み込み
            username, password = self.auth_utils.load_credentials()
            if username and password:
                logger.info(f"保存されたログイン情報を読み込みました: {username}")
                # ログイン処理を実行
                self.perform_login(username, password, show_dialog=False)
            else:
                logger.debug("保存されたログイン情報がありません")
        except Exception as e:
            logger.error(f"ログイン情報の読み込みに失敗しました: {str(e)}")
    
    def update_login_status(self, is_logged_in):
        """ログイン状態に応じてUIを更新"""
        self.login_item.Enable(not is_logged_in)
        self.logout_item.Enable(is_logged_in)
    
    def on_login(self, event):
        """ログイン情報設定ダイアログを表示"""
        # カスタムダイアログの作成
        dlg = wx.Dialog(self, title="ログイン情報の設定", size=(400, 200))
        
        # レイアウト
        panel = wx.Panel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ユーザー名入力
        username_label = wx.StaticText(panel, label="ユーザー名（例: username.bsky.social）:")
        sizer.Add(username_label, 0, wx.ALL | wx.EXPAND, 5)
        username_ctrl = wx.TextCtrl(panel)
        sizer.Add(username_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # パスワード入力
        password_label = wx.StaticText(panel, label="アプリパスワード:")
        sizer.Add(password_label, 0, wx.ALL | wx.EXPAND, 5)
        password_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        sizer.Add(password_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK, "保存")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(sizer)
        
        # ダイアログ表示
        if dlg.ShowModal() == wx.ID_OK:
            username = username_ctrl.GetValue()
            password = password_ctrl.GetValue()
            
            if username and password:
                # ログイン情報を保存
                if self.auth_utils.save_credentials(username, password):
                    # ログイン処理を実行
                    self.perform_login(username, password)
                else:
                    wx.MessageBox("ログイン情報の保存に失敗しました", "エラー", wx.OK | wx.ICON_ERROR)
            else:
                wx.MessageBox("ユーザー名とアプリパスワードを入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def perform_login(self, username, password, show_dialog=True):
        """ログイン処理を実行"""
        try:
            # Blueskyにログイン
            self.statusbar.SetStatusText("Blueskyにログイン中...")
            self.client = Client()
            
            logger.debug(f"ログイン試行: ユーザー名={username}")
            
            try:
                # ログイン試行
                profile = self.client.login(username, password)
                
                logger.debug(f"ログイン成功: プロフィール={profile.display_name}, セッション={type(self.client._session)}")
                
                # ログイン成功
                self.set_username(profile.handle)
                self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                self.update_login_status(True)
                
                # タイムラインの更新
                self.statusbar.SetStatusText("タイムラインを更新しています...")
                self.timeline.fetch_timeline(self.client)
                self.statusbar.SetStatusText(f"{profile.handle}としてログインしました")
                
                # 成功通知ダイアログを表示（オプション）
                if show_dialog:
                    wx.MessageBox(f"{profile.handle}としてログインしました", "ログイン成功", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                # ログイン失敗
                error_message = f"ログインに失敗しました: {str(e)}\n\n2段階認証を設定しているアカウントは、アプリパスワードを使用してください。"
                logger.error(f"ログインに失敗しました: {str(e)}")
                
                if show_dialog:
                    result = wx.MessageBox(error_message, "ログイン失敗", wx.OK | wx.ICON_ERROR)
                    # OKボタンがクリックされたら、ログイン情報設定ダイアログを表示
                    if result == wx.OK:
                        self.on_login(None)
                
                self.statusbar.SetStatusText("ログインに失敗しました")
            
        except Exception as e:
            # ログイン失敗
            logger.error(f"ログイン処理中に例外が発生しました: {str(e)}", exc_info=True)
            
            if show_dialog:
                result = wx.MessageBox(f"ログインに失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                # OKボタンがクリックされたら、ログイン情報設定ダイアログを表示
                if result == wx.OK:
                    self.on_login(None)
            
            self.statusbar.SetStatusText("ログインに失敗しました")
    
    
    def on_logout(self, event):
        """ログアウト処理"""
        if self.client and self.username:
            username = self.username
            
            # ログイン情報を削除
            self.auth_utils.delete_credentials()
            
            # クライアントをリセット
            self.client = None
            self.username = None
            
            # UIを更新
            self.SetTitle("SSky")
            self.statusbar.SetStatusText("ログアウトしました")
            self.update_login_status(False)
            
            logger.info("ログアウトしました")
            
            # ログアウト通知ダイアログを表示
            wx.MessageBox(f"{username}からログアウトしました", "ログアウト完了", wx.OK | wx.ICON_INFORMATION)
    
    def on_exit(self, event):
        """アプリケーションを終了"""
        self.Close()
        
    def on_new_post(self, event):
        """新規投稿ダイアログを表示"""
        if not self.username:
            wx.MessageBox("投稿するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        dlg = wx.TextEntryDialog(self, "投稿内容を入力:", "新規投稿")
        if dlg.ShowModal() == wx.ID_OK:
            post_content = dlg.GetValue()
            if post_content:
                wx.MessageBox(f"投稿しました: {post_content}", "投稿完了", wx.OK | wx.ICON_INFORMATION)
                self.statusbar.SetStatusText("投稿が完了しました")
        dlg.Destroy()
    
    def on_like(self, event):
        """いいねアクション"""
        selected = self.timeline.get_selected_post()
        if selected:
            wx.MessageBox(f"投稿にいいねしました", "いいね", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
    
    def on_reply(self, event):
        """返信アクション"""
        selected = self.timeline.get_selected_post()
        if selected:
            dlg = wx.TextEntryDialog(self, "返信内容を入力:", "返信")
            if dlg.ShowModal() == wx.ID_OK:
                reply = dlg.GetValue()
                if reply:
                    wx.MessageBox(f"返信を投稿しました: {reply}", "返信", wx.OK | wx.ICON_INFORMATION)
            dlg.Destroy()
        else:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
    
    def on_quote(self, event):
        """引用アクション"""
        selected = self.timeline.get_selected_post()
        if selected:
            dlg = wx.TextEntryDialog(self, "引用内容を入力:", "引用")
            if dlg.ShowModal() == wx.ID_OK:
                quote = dlg.GetValue()
                if quote:
                    wx.MessageBox(f"引用を投稿しました: {quote}", "引用", wx.OK | wx.ICON_INFORMATION)
            dlg.Destroy()
        else:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
    
    def on_profile(self, event):
        """プロフィール表示アクション"""
        selected = self.timeline.get_selected_post()
        if selected:
            wx.MessageBox(f"プロフィールを表示します: {selected['username']}", "プロフィール", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
    
    def on_settings(self, event):
        """設定ダイアログを表示"""
        wx.MessageBox("設定ダイアログ（未実装）", "設定", wx.OK | wx.ICON_INFORMATION)
    
    def on_delete(self, event):
        """投稿削除アクション"""
        selected = self.timeline.get_selected_post()
        if selected:
            dlg = wx.MessageDialog(self, "この投稿を削除してもよろしいですか？", "投稿削除の確認", 
                                  wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                wx.MessageBox("投稿を削除しました", "削除完了", wx.OK | wx.ICON_INFORMATION)
                self.statusbar.SetStatusText("投稿が削除されました")
            dlg.Destroy()
        else:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
