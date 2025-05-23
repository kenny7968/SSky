#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
非同期処理ユーティリティモジュール
"""

import threading
import wx
from pubsub import pub
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

def run_delayed(func, delay_seconds, *args, **kwargs):
    """指定した秒数後に関数を実行するユーティリティ
    
    Args:
        func: 実行する関数
        delay_seconds: 遅延秒数
        *args, **kwargs: funcに渡す引数
        
    Returns:
        threading.Timer: 起動したタイマー
    """
    def _delayed_func():
        try:
            wx.CallAfter(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"遅延実行中にエラーが発生しました: {str(e)}", exc_info=True)
    
    timer = threading.Timer(delay_seconds, _delayed_func)
    timer.daemon = True
    timer.start()
    return timer

def run_async(func, callback=None, error_callback=None, *args, **kwargs):
    """関数を非同期で実行するユーティリティ
    
    Args:
        func: 実行する関数
        callback: 成功時のコールバック関数（オプション）
        error_callback: エラー時のコールバック関数（オプション）
        *args, **kwargs: funcに渡す引数
        
    Returns:
        threading.Thread: 起動したスレッド
    """
    def _worker():
        try:
            result = func(*args, **kwargs)
            if callback:
                wx.CallAfter(callback, result)
        except Exception as e:
            logger.error(f"非同期処理中にエラーが発生しました: {str(e)}", exc_info=True)
            if error_callback:
                wx.CallAfter(error_callback, e)
    
    thread = threading.Thread(target=_worker)
    thread.daemon = True
    thread.start()
    return thread
