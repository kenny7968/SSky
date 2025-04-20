#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーションクラス
"""

import wx
import logging
from gui.main_frame import MainFrame
from config.app_config import AppConfig

# ロガーの設定
logger = logging.getLogger(__name__)

class SSkyApp(wx.App):
    """SSkyアプリケーションクラス"""
    
    def __init__(self):
        """初期化"""
        # 設定の読み込み
        self.config = AppConfig()
        
        super(SSkyApp, self).__init__()
        
    def OnInit(self):
        """アプリケーション初期化"""
        # ウィンドウサイズの取得
        width = self.config.get('window_size.width', 800)
        height = self.config.get('window_size.height', 600)
        
        # メインフレームの作成
        self.frame = MainFrame(
            None, 
            title=self.config.get('app_name', 'SSky'),
            size=(width, height)
        )
        
        # フレームの表示
        self.frame.Show()
        self.SetTopWindow(self.frame)
        
        logger.info("アプリケーションを初期化しました")
        
        return True
        
    def OnExit(self):
        """アプリケーション終了時の処理"""
        logger.info("アプリケーションを終了します")
        return super(SSkyApp, self).OnExit()
