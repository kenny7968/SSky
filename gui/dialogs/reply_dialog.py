#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
返信ダイアログ
"""

import wx
import logging
from .base_post_dialog import BasePostDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class ReplyDialog(BasePostDialog):
    """返信ダイアログ"""
    
    def __init__(self, parent, post_data):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            post_data (dict): 返信先の投稿データ
        """
        # 一時的にデフォルトタイトルでBaseDialogを初期化
        super(ReplyDialog, self).__init__(
            parent, 
            title=f"Reply to {post_data['username']}", 
            size=(500, 300)
        )
        
        # i18nが初期化された後でタイトルを更新
        self.SetTitle(self.i18n.get_message("dialog.reply_to_user", username=post_data['username']))
        
        self.post_data = post_data
        
        # UIの初期化
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 返信元の投稿情報
        reply_from_label = wx.StaticText(panel, label=self.i18n.get_message("dialog.reply_to"))
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
        text_sizer = self.create_text_input_area(panel, self.i18n.get_message("dialog.reply_content_label"))
        main_sizer.Add(text_sizer, 1, wx.EXPAND)
        
        # デフォルトでメンションを入れる
        default_text = f"@{self.post_data['author_handle']} "
        self.set_text_content(default_text)
        self.set_insertion_point_end()
        
        # ボタン
        button_sizer = self.create_button_area(panel, self.i18n.get_message("dialog.reply_button"))
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(main_sizer)
        
        # フォーカスを設定
        self.set_text_focus()
        
            
    def get_reply_data(self):
        """返信データを取得
        
        Returns:
            tuple: (reply_text, reply_to)のタプル
        """
        return (
            self.get_text_content(),
            {
                'uri': self.post_data.get('uri'),
                'cid': self.post_data.get('cid')
            }
        )
    
    def show_validation_error(self):
        """検証エラーメッセージの表示（オーバーライド）"""
        self.show_error(self.i18n.get_message("error.reply_content_required"))
