#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインフレームクラス
"""

import wx
from timeline_view import TimelineView

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
        
        # ユーザー名（ログイン後に設定）
        self.username = None
        
        # UIの初期化
        self.init_ui()
        
        # 中央に配置
        self.Centre()
        
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
        login_item = app_menu.Append(wx.ID_ANY, "Blueskyにログイン(&A)", "Blueskyにログイン")
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
        self.Bind(wx.EVT_MENU, self.on_login, login_item)
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
    
    def on_login(self, event):
        """ログインダイアログを表示"""
        dlg = wx.TextEntryDialog(self, "Blueskyのユーザー名を入力してください:", "ログイン")
        if dlg.ShowModal() == wx.ID_OK:
            username = dlg.GetValue()
            if username:
                self.set_username(username)
                self.statusbar.SetStatusText(f"{username}としてログインしました")
        dlg.Destroy()
    
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
