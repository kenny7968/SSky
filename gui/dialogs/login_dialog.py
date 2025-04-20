#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ログインダイアログ
"""

import wx
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class LoginDialog(wx.Dialog):
    """ログイン情報設定ダイアログ"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        super(LoginDialog, self).__init__(
            parent, 
            title="ログイン情報の設定", 
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # UIの初期化
        self.init_ui()
        
        # 中央に配置
        self.Centre()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ユーザー名入力
        username_label = wx.StaticText(panel, label="ユーザー名（例: username.bsky.social）:")
        sizer.Add(username_label, 0, wx.ALL | wx.EXPAND, 5)
        self.username_ctrl = wx.TextCtrl(panel)
        sizer.Add(self.username_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # パスワード入力
        password_label = wx.StaticText(panel, label="アプリパスワード:")
        sizer.Add(password_label, 0, wx.ALL | wx.EXPAND, 5)
        self.password_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        sizer.Add(self.password_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK, "保存")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(sizer)
        
    def get_credentials(self):
        """入力されたログイン情報を取得
        
        Returns:
            tuple: (username, password)のタプル
        """
        return (
            self.username_ctrl.GetValue(),
            self.password_ctrl.GetValue()
        )
        
    def set_credentials(self, username, password=""):
        """ログイン情報を設定
        
        Args:
            username (str): ユーザー名
            password (str, optional): パスワード
        """
        self.username_ctrl.SetValue(username)
        if password:
            self.password_ctrl.SetValue(password)
