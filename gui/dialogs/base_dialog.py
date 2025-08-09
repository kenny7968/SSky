#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ダイアログ基底クラス
"""

import wx
import logging
from utils.i18n import get_i18n

logger = logging.getLogger(__name__)

class BaseDialog(wx.Dialog):
    """ダイアログ基底クラス
    
    責任:
    - 共通のダイアログ初期化処理
    - キーボードショートカット処理
    - エラー表示の統一
    - レスポンシブレイアウトの基本実装
    """
    
    def __init__(self, parent, title, size=(400, 300), **kwargs):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            title (str): ダイアログタイトル
            size (tuple): ダイアログサイズ
            **kwargs: その他のwx.Dialogパラメータ
        """
        # 国際化管理インスタンス
        self.i18n = get_i18n()
        
        # デフォルトスタイルを設定
        default_style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        style = kwargs.pop('style', default_style)
        
        super(BaseDialog, self).__init__(
            parent, 
            title=title, 
            size=size,
            style=style,
            **kwargs
        )
        
        self.setup_dialog()
        self.bind_events()
        
        # 中央に配置
        self.Centre()
        
    def setup_dialog(self):
        """ダイアログの基本設定
        
        サブクラスでオーバーライドして具体的なUI構築を行う
        """
        pass
    
    def bind_events(self):
        """共通イベントバインド"""
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
    
    def on_key_down(self, event):
        """共通キーボード処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        
        # Escキーでダイアログを閉じる
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        
        # その他のキー処理は継続
        event.Skip()
    
    def on_close(self, event):
        """ダイアログクローズ時の処理
        
        Args:
            event: クローズイベント
        """
        self.EndModal(wx.ID_CANCEL)
    
    def show_error(self, message, title=None):
        """エラーメッセージの統一表示
        
        Args:
            message (str): エラーメッセージ
            title (str): ダイアログタイトル
        """
        if title is None:
            title = self.i18n.get_message("error.title")
        wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)
    
    def show_warning(self, message, title=None):
        """警告メッセージの統一表示
        
        Args:
            message (str): 警告メッセージ
            title (str): ダイアログタイトル
        """
        if title is None:
            title = self.i18n.get_message("error.warning")
        wx.MessageBox(message, title, wx.OK | wx.ICON_WARNING)
    
    def show_info(self, message, title=None):
        """情報メッセージの統一表示
        
        Args:
            message (str): 情報メッセージ
            title (str): ダイアログタイトル
        """
        if title is None:
            title = self.i18n.get_message("error.info")
        wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)
    
    def confirm(self, message, title=None):
        """確認ダイアログの統一表示
        
        Args:
            message (str): 確認メッセージ
            title (str): ダイアログタイトル
            
        Returns:
            bool: ユーザーが「はい」を選択した場合True
        """
        if title is None:
            title = self.i18n.get_message("error.confirm")
        dlg = wx.MessageDialog(
            self,
            message,
            title,
            wx.YES_NO | wx.ICON_QUESTION
        )
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        return result