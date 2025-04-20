#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
引用ダイアログ
"""

import wx
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class QuoteDialog(wx.Dialog):
    """引用ダイアログ"""
    
    def __init__(self, parent, post_data):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            post_data (dict): 引用元の投稿データ
        """
        super(QuoteDialog, self).__init__(
            parent, 
            title=f"{post_data['username']}の投稿を引用", 
            size=(500, 350),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.post_data = post_data
        
        # UIの初期化
        self.init_ui()
        
        # 中央に配置
        self.Centre()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 引用元の投稿情報
        quote_from_label = wx.StaticText(panel, label="引用元:")
        main_sizer.Add(quote_from_label, 0, wx.ALL | wx.EXPAND, 5)
        
        # 引用元の投稿内容（リードオンリー）
        quote_content = f"{self.post_data['username']} {self.post_data['handle']} - {self.post_data['time']}\n{self.post_data['content']}"
        quote_from_ctrl = wx.TextCtrl(
            panel, 
            value=quote_content,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.BORDER_SIMPLE
        )
        quote_from_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        main_sizer.Add(quote_from_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # 区切り線
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        
        # 引用内容入力エリア
        content_label = wx.StaticText(panel, label="引用コメント:")
        main_sizer.Add(content_label, 0, wx.ALL | wx.EXPAND, 5)
        
        self.content_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.content_ctrl.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        main_sizer.Add(self.content_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        quote_button = wx.Button(panel, wx.ID_OK, "引用")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        button_sizer.AddButton(quote_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(main_sizer)
        
        # フォーカスを設定
        self.content_ctrl.SetFocus()
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        
        # Ctrl+Enterが押された場合
        if ctrl_down and key_code == wx.WXK_RETURN:
            # 引用内容を取得
            quote_content = self.content_ctrl.GetValue()
            if quote_content:
                # ダイアログを閉じる（OK）
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("引用コメントを入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        else:
            # 通常のキー処理を継続
            event.Skip()
            
    def get_quote_data(self):
        """引用データを取得
        
        Returns:
            tuple: (quote_text, quote_of)のタプル
        """
        return (
            self.content_ctrl.GetValue(),
            {
                'uri': self.post_data.get('uri'),
                'cid': self.post_data.get('cid')
            }
        )
