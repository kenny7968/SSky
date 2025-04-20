#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ファイル操作ユーティリティ
"""

import os
import logging
import mimetypes

# ロガーの設定
logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path):
    """ディレクトリが存在することを確認し、存在しない場合は作成する
    
    Args:
        directory_path (str): 確認/作成するディレクトリのパス
        
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.debug(f"ディレクトリを作成しました: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"ディレクトリの作成に失敗しました: {str(e)}")
        return False

def get_mime_type(file_path):
    """ファイルのMIMEタイプを取得する
    
    Args:
        file_path (str): MIMEタイプを取得するファイルのパス
        
    Returns:
        str: ファイルのMIMEタイプ。判定できない場合は'application/octet-stream'
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    return mime_type

def read_binary_file(file_path):
    """バイナリファイルを読み込む
    
    Args:
        file_path (str): 読み込むファイルのパス
        
    Returns:
        bytes: ファイルの内容。エラーの場合はNone
    """
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"ファイルの読み込みに失敗しました: {str(e)}")
        return None

def get_file_size(file_path):
    """ファイルサイズを取得する
    
    Args:
        file_path (str): サイズを取得するファイルのパス
        
    Returns:
        int: ファイルサイズ（バイト）。エラーの場合は-1
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"ファイルサイズの取得に失敗しました: {str(e)}")
        return -1
