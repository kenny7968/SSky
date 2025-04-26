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
    # 設定マネージャーからデバッグログの有効/無効を取得
    try:
        from config.settings_manager import SettingsManager
        settings_manager = SettingsManager()
        enable_debug_log = settings_manager.get('advanced.enable_debug_log', False)
    except Exception:
        # 設定マネージャーの取得に失敗した場合はデフォルト値を使用
        enable_debug_log = False
    
    # ログディレクトリの確認と作成
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
    ensure_directory_exists(log_dir)

    # ログファイル名（日時を含める）
    log_filename = os.path.join(log_dir, f'{app_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    # ロガーの設定
    # コンソールとファイルの両方にログを出力
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # ロガー自体のレベルはDEBUGに設定

    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    # デバッグログが有効な場合はDEBUG、無効な場合はINFO
    console_handler.setLevel(logging.DEBUG if enable_debug_log else logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # ファイルハンドラ（ローテーション機能付き）
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # ファイルには常にDEBUGレベルで出力
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # ハンドラをロガーに追加
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # サードパーティライブラリのログレベルを調整
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)  # HTTPリクエストのログを抑制
    
    # デバッグログが無効な場合は、ルートロガー以外のすべてのロガーのレベルをINFOに設定
    if not enable_debug_log:
        for logger_name in logging.root.manager.loggerDict:
            if logger_name != '':  # ルートロガー以外
                logging.getLogger(logger_name).setLevel(logging.INFO)
    
    logger.debug(f"{app_name}のロギング設定を完了しました（デバッグログ: {'有効' if enable_debug_log else '無効'}）")
    
    return logger
