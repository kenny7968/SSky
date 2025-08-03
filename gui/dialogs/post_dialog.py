#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿ダイアログ
"""

import os
import wx
import logging
import mimetypes
from utils.file_utils import get_mime_type
from .base_post_dialog import BasePostDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class PostDialog(BasePostDialog):
    """新規投稿ダイアログ"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        super(PostDialog, self).__init__(
            parent, 
            title="新規投稿（Ctrl+Enterで送信）", 
            size=(500, 300)
        )
        
        # 添付ファイルのリスト（最大4つまで）
        self.attachment_labels = []
        
        # UIの初期化
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 投稿内容入力エリア
        text_sizer = self.create_text_input_area(panel, "投稿内容:")
        main_sizer.Add(text_sizer, 1, wx.EXPAND)
        
        # 添付ファイル関連のコントロール
        attachment_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 画像添付ボタン
        image_btn = wx.Button(panel, label="画像を添付", size=(120, -1))
        image_btn.Bind(wx.EVT_BUTTON, self.on_attach_image)
        attachment_sizer.Add(image_btn, 0, wx.ALL, 5)
        
        # 添付ファイル表示エリア
        attachment_label = wx.StaticText(panel, label="添付ファイル: なし")
        self.attachment_labels.append(attachment_label)
        attachment_sizer.Add(attachment_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        main_sizer.Add(attachment_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # ボタン
        button_sizer = self.create_button_area(panel, "投稿")
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(main_sizer)
        
            
    def on_attach_image(self, event):
        """画像添付ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # すでに4つのファイルが添付されている場合
        if len(self.attachment_files) >= 4:
            wx.MessageBox("添付できるファイルは最大4つまでです", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        # ファイル選択ダイアログを表示
        wildcard = "画像ファイル (*.jpg;*.jpeg;*.png;*.gif)|*.jpg;*.jpeg;*.png;*.gif"
        dlg = wx.FileDialog(
            self, 
            message="画像ファイルを選択してください",
            defaultDir="", 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            self.attachment_files.append(file_path)
            
            # 添付ファイルラベルを更新
            file_names = [os.path.basename(f) for f in self.attachment_files]
            self.attachment_labels[0].SetLabel(f"添付ファイル: {', '.join(file_names)}")
            
            # レイアウトを更新
            self.Layout()
            
        dlg.Destroy()
        
    
    def get_post_data(self):
        """投稿データを取得
        
        Returns:
            tuple: (content, attachment_files)のタプル
        """
        return (
            self.get_text_content(),
            self.attachment_files
        )
