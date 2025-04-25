#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
暗号化ユーティリティモジュール
"""

import logging
import win32crypt

# ロガーの設定
logger = logging.getLogger(__name__)

def encrypt_data(data):
    """DPAPIを使用してデータを暗号化"""
    try:
        # デバッグ情報（機密データは含めない）
        logger.debug(f"暗号化前データの型: {type(data)}")
        
        # バイト列への変換（シリアライズなし）
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
            logger.debug(f"文字列をバイト列に変換: {len(data_bytes)}バイト")
        elif isinstance(data, bytes):
            data_bytes = data
            logger.debug(f"バイト列をそのまま使用: {len(data_bytes)}バイト")
        else:
            logger.error(f"サポートされていないデータ型: {type(data)}")
            return None
        
        # DPAPIで暗号化
        encrypted_data = win32crypt.CryptProtectData(
            data_bytes,
            None,  # 説明（任意）
            None,  # エントロピー（任意）
            None,  # 予約済み
            None,  # プロンプトフラグ
            0      # フラグ
        )
        
        logger.debug(f"暗号化後データの型: {type(encrypted_data)}")
        return encrypted_data
    except Exception as e:
        logger.error(f"データの暗号化に失敗しました: {str(e)}", exc_info=True)
        return None

def decrypt_data(encrypted_data):
    """DPAPIを使用して暗号化されたデータを復号化"""
    try:
        logger.debug(f"復号化前データの型: {type(encrypted_data)}")
        
        # DPAPIで復号化
        decrypted_tuple = win32crypt.CryptUnprotectData(
            encrypted_data,
            None,  # 説明（任意）
            None,  # エントロピー（任意）
            None,  # 予約済み
            0      # フラグ
        )
        
        # タプルの2番目の要素がデータ
        raw_data = decrypted_tuple[1]
        logger.debug(f"復号化データの型: {type(raw_data)}, 長さ: {len(raw_data)}バイト")
        
        # バイト列から文字列への変換（デシリアライズなし）
        try:
            result = raw_data.decode('utf-8')
            logger.debug(f"バイト列を文字列に変換しました: 長さ{len(result)}文字")
            return result
        except UnicodeDecodeError as e:
            logger.debug(f"UTF-8でのデコードに失敗しました: {str(e)}。他のエンコーディングを試みます。")
            
            # 他のエンコーディングを試す
            try:
                # Latin-1（ISO-8859-1）は任意のバイト列をデコードできる
                result = raw_data.decode('latin-1')
                logger.debug(f"バイト列をLatin-1でデコードしました: 長さ{len(result)}文字")
                return result
            except Exception as e2:
                logger.error(f"バイト列のデコードに失敗しました: {str(e2)}")
                return raw_data
    except Exception as e:
        logger.error(f"データの復号化に失敗しました: {str(e)}", exc_info=True)
        return None
