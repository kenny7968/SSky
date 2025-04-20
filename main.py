#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインエントリーポイント
"""

import os
import wx
import logging
from config.logging_config import setup_logging
from gui.app import SSkyApp

# ロギングの設定
logger = setup_logging()

logger.debug("アプリケーションを起動します")

if __name__ == "__main__":
    app = SSkyApp()
    app.MainLoop()
