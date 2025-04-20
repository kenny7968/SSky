#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
返信ダイアログ
"""

import wx
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class ReplyDialog(wx.Dialog):
    """返信ダイアログ"""
    
    def __init__(self, parent, post_data):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            post_data (dict): 返信先の投稿データ
        """
        super(ReplyDialog, self).__init__(
            parent, 
            title=f"{post_data['username']}への返信", 
            size=(500, 300),
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
        
        # 返信元の投稿情報
        reply_from_label = wx.StaticText(panel, label="返信元:")
        main_sizer.Add(reply_from_label, 0, wx.ALL | wx.EXPAND, 5)
        
        # 返信元の投稿内容（リードオンリー）
        self.reply_from_ctrl = wx.TextCtrl(
            panel, 
            value=self.post_data['content'],
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.BORDER_SIMPLE
        )
        self.reply_from_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        main_sizer.Add(self.reply_from_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # 区切り線
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        
        # 返信内容入力エリア
        content_label = wx.StaticText(panel, label="返信内容:")
        main_sizer.Add(content_label, 0, wx.ALL | wx.EXPAND, 5)
        
        # デフォルトでメンションを入れる
        default_text = f"@{self.post_data['author_handle']} "
        
        self.content_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.content_ctrl.SetValue(default_text)
        self.content_ctrl.SetInsertionPointEnd()  # カーソルを末尾に
        self.content_ctrl.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        main_sizer.Add(self.content_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        reply_button = wx.Button(panel, wx.ID_OK, "返信")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        button_sizer.AddButton(reply_button)
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
            # 返信内容を取得
            reply_content = self.content_ctrl.GetValue()
            if reply_content:
                # ダイアログを閉じる（OK）
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("返信内容を入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        else:
            # 通常のキー処理を継続
            event.Skip()
            
    def get_reply_data(self):
        """返信データを取得
        
        Returns:
            tuple: (reply_text, reply_to)のタプル
        """
        return (
            self.content_ctrl.GetValue(),
            {
                'uri': self.post_data.get('uri'),
                'cid': self.post_data.get('cid')
            }
        )
