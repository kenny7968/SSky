#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインエントリーポイント
"""

import os
import wx
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app import SSkyApp

# ログディレクトリの確認と作成
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(log_dir, exist_ok=True)

# ログファイル名（日時を含める）
log_filename = os.path.join(log_dir, f'ssky_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# ロガーの設定
# コンソールとファイルの両方にログを出力
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 既存のハンドラをクリア
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# コンソールハンドラ
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# ファイルハンドラ（ローテーション機能付き）
file_handler = RotatingFileHandler(
    log_filename,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# ハンドラをロガーに追加
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.debug("アプリケーションを起動します")

if __name__ == "__main__":
    app = SSkyApp()
    app.MainLoop()
