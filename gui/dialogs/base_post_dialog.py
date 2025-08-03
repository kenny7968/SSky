#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿系ダイアログ基底クラス
"""

import wx
import logging
from .base_dialog import BaseDialog

logger = logging.getLogger(__name__)

class BasePostDialog(BaseDialog):
    """投稿系ダイアログ基底クラス
    
    責任:
    - 投稿テキスト入力エリアの共通処理
    - Ctrl+Enter送信処理
    - 文字数カウント表示
    - 添付ファイル管理の基本処理
    """
    
    def __init__(self, parent, title, size=(500, 300), **kwargs):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            title (str): ダイアログタイトル
            size (tuple): ダイアログサイズ
            **kwargs: その他のwx.Dialogパラメータ
        """
        super(BasePostDialog, self).__init__(parent, title, size, **kwargs)
        
        # 投稿関連の属性
        self.text_ctrl = None
        self.char_count_label = None
        self.attachment_files = []
        
    def on_key_down(self, event):
        """キー入力時の処理（BaseDialogをオーバーライド）
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        
        # Ctrl+Enterが押された場合
        if ctrl_down and key_code == wx.WXK_RETURN:
            self.handle_send_shortcut()
            return
        # Escキーが押された場合
        elif key_code == wx.WXK_ESCAPE:
            self.handle_escape_key()
            return
        
        # その他のキー処理は継続
        event.Skip()
    
    def handle_send_shortcut(self):
        """Ctrl+Enter送信処理"""
        if self.validate_content():
            self.EndModal(wx.ID_OK)
        else:
            self.show_validation_error()
    
    def handle_escape_key(self):
        """Escキー処理"""
        if self.text_ctrl and self.text_ctrl.GetValue().strip():
            if self.confirm("投稿内容が入力されています。本当に閉じますか？"):
                self.EndModal(wx.ID_CANCEL)
        else:
            self.EndModal(wx.ID_CANCEL)
    
    def validate_content(self):
        """投稿内容の検証
        
        Returns:
            bool: 有効な内容の場合True
        """
        if not self.text_ctrl:
            return False
        
        content = self.text_ctrl.GetValue()
        return bool(content.strip())
    
    def show_validation_error(self):
        """検証エラーメッセージの表示"""
        self.show_error("投稿内容を入力してください")
    
    def update_char_count(self):
        """文字数カウント更新"""
        if not self.text_ctrl or not self.char_count_label:
            return
        
        content = self.text_ctrl.GetValue()
        char_count = len(content)
        max_chars = 300  # Blueskyの文字数制限
        
        self.char_count_label.SetLabel(f"{char_count}/{max_chars}")
        
        # 文字数制限を超えた場合の色変更
        if char_count > max_chars:
            self.char_count_label.SetForegroundColour(wx.Colour(255, 0, 0))  # 赤色
        else:
            self.char_count_label.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
    
    def create_text_input_area(self, panel, label_text="投稿内容:"):
        """テキスト入力エリアの作成
        
        Args:
            panel: 親パネル
            label_text (str): ラベルテキスト
            
        Returns:
            wx.BoxSizer: 作成されたサイザー
        """
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ラベル
        label = wx.StaticText(panel, label=label_text)
        sizer.Add(label, 0, wx.ALL | wx.EXPAND, 5)
        
        # テキスト入力コントロール
        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.text_ctrl.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_text_change)
        sizer.Add(self.text_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        
        return sizer
    
    def create_char_count_display(self, panel):
        """文字数カウント表示の作成
        
        Args:
            panel: 親パネル
            
        Returns:
            wx.StaticText: 文字数表示ラベル
        """
        self.char_count_label = wx.StaticText(panel, label="0/300")
        self.update_char_count()
        return self.char_count_label
    
    def create_button_area(self, panel, ok_label="送信"):
        """ボタンエリアの作成
        
        Args:
            panel: 親パネル
            ok_label (str): OKボタンのラベル
            
        Returns:
            wx.StdDialogButtonSizer: 作成されたボタンサイザー
        """
        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK, ok_label)
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        return button_sizer
    
    def on_text_change(self, event):
        """テキスト変更時の処理
        
        Args:
            event: テキストイベント
        """
        self.update_char_count()
        event.Skip()
    
    def get_text_content(self):
        """テキスト内容の取得
        
        Returns:
            str: 入力されたテキスト内容
        """
        if self.text_ctrl:
            return self.text_ctrl.GetValue()
        return ""
    
    def set_text_content(self, content):
        """テキスト内容の設定
        
        Args:
            content (str): 設定するテキスト内容
        """
        if self.text_ctrl:
            self.text_ctrl.SetValue(content)
            self.update_char_count()
    
    def set_text_focus(self):
        """テキストコントロールにフォーカスを設定"""
        if self.text_ctrl:
            self.text_ctrl.SetFocus()
    
    def set_insertion_point_end(self):
        """カーソルを末尾に移動"""
        if self.text_ctrl:
            self.text_ctrl.SetInsertionPointEnd()