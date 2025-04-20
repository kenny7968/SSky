#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーションクラス
"""

import wx
from main_frame import MainFrame

class SSkyApp(wx.App):
    """SSkyアプリケーションクラス"""
    
    def OnInit(self):
        """アプリケーション初期化"""
        self.frame = MainFrame(None, title="SSky")
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True
