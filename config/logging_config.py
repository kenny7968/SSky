#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ロギング設定モジュール
"""

import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from utils.file_utils import ensure_directory_exists

def setup_logging(app_name="ssky"):
    """アプリケーションのロギング設定を行う
    
    Args:
        app_name (str): アプリケーション名（ログファイル名のプレフィックス）
        
    Returns:
        logging.Logger: 設定済みのロガーオブジェクト
    """
    # ログディレクトリの確認と作成
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
    ensure_directory_exists(log_dir)

    # ログファイル名（日時を含める）
    log_filename = os.path.join(log_dir, f'{app_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    # ロガーの設定
    # コンソールとファイルの両方にログを出力
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
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
    
    # サードパーティライブラリのログレベルを調整
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)  # HTTPリクエストのログを抑制
    logging.getLogger('gui.timeline_view').setLevel(logging.INFO)  # タイムラインビューのログを調整
    
    logger.debug(f"{app_name}のロギング設定を完了しました")
    
    return logger
