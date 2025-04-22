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

# ロガーの設定
logger = logging.getLogger(__name__)

class PostDialog(wx.Dialog):
    """新規投稿ダイアログ"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        super(PostDialog, self).__init__(
            parent, 
            title="新規投稿（Ctrl+Enterで送信）", 
            size=(500, 300),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # 添付ファイルのリスト（最大4つまで）
        self.attachment_files = []
        self.attachment_labels = []
        
        # UIの初期化
        self.init_ui()
        
        # イベントバインド
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 中央に配置
        self.Centre()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 投稿内容入力エリア
        content_label = wx.StaticText(panel, label="投稿内容:")
        main_sizer.Add(content_label, 0, wx.ALL | wx.EXPAND, 5)
        
        self.content_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.content_ctrl.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        main_sizer.Add(self.content_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
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
        button_sizer = wx.StdDialogButtonSizer()
        post_button = wx.Button(panel, wx.ID_OK, "投稿")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        button_sizer.AddButton(post_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(main_sizer)
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        
        # Ctrl+Enterが押された場合
        if ctrl_down and key_code == wx.WXK_RETURN:
            # 投稿内容を取得
            post_content = self.content_ctrl.GetValue()
            if post_content:
                # ダイアログを閉じる（OK）
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("投稿内容を入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        # Escキーが押された場合
        elif key_code == wx.WXK_ESCAPE:
            # 投稿内容をチェック
            self.check_content_and_close(wx.ID_CANCEL)
            return  # イベントを処理済みとしてSkipしない
        else:
            # 通常のキー処理を継続
            event.Skip()
            
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
        
    def on_cancel(self, event):
        """キャンセルボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # 投稿内容をチェック
        self.check_content_and_close(wx.ID_CANCEL)
        
    def on_close(self, event):
        """ダイアログが閉じられる時の処理
        
        Args:
            event: クローズイベント
        """
        # 投稿内容をチェック
        self.check_content_and_close(wx.ID_CANCEL)
        
    def check_content_and_close(self, result):
        """投稿内容をチェックして、必要に応じて確認ダイアログを表示
        
        Args:
            result: ダイアログの結果コード
        """
        # 投稿内容を取得
        post_content = self.content_ctrl.GetValue()
        
        # 投稿内容が入力されている場合
        if post_content.strip():
            # 確認ダイアログを表示
            dlg = wx.MessageDialog(
                self,
                "投稿内容が入力されています。本当に閉じますか？",
                "確認",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            # ユーザーの選択を取得
            if dlg.ShowModal() == wx.ID_YES:
                # 「はい」が選択された場合、ダイアログを閉じる
                self.EndModal(result)
            
            dlg.Destroy()
        else:
            # 投稿内容が入力されていない場合、そのまま閉じる
            self.EndModal(result)
    
    def get_post_data(self):
        """投稿データを取得
        
        Returns:
            tuple: (content, attachment_files)のタプル
        """
        return (
            self.content_ctrl.GetValue(),
            self.attachment_files
        )
