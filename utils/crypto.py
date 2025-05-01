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
        # デバッグ情報（デバッグ目的で内容も出力）
        logger.info("データを暗号化します")
        logger.debug(f"暗号化前データの型: {type(data)}, 長さ: {len(data) if hasattr(data, '__len__') else 'N/A'}")
        logger.debug(f"暗号化前データの内容: {data}")  # デバッグ目的で内容も出力
        
        # バイト列への変換（シリアライズなし）
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
            logger.debug(f"文字列をバイト列に変換: {len(data_bytes)}バイト")
            logger.debug(f"変換後バイト列の内容: {data_bytes}")  # デバッグ目的で内容も出力
        elif isinstance(data, bytes):
            data_bytes = data
            logger.debug(f"バイト列をそのまま使用: {len(data_bytes)}バイト")
            logger.debug(f"バイト列の内容: {data_bytes}")  # デバッグ目的で内容も出力
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
        logger.debug(f"暗号化後データの内容: {encrypted_data}")  # デバッグ目的で内容も出力
        logger.info("データの暗号化が完了しました")
        return encrypted_data
    except Exception as e:
        logger.error(f"データの暗号化に失敗しました: {str(e)}", exc_info=True)
        return None

def decrypt_data(encrypted_data):
    """DPAPIを使用して暗号化されたデータを復号化"""
    try:
        logger.info("暗号化されたデータを復号化します")
        logger.debug(f"復号化前データの型: {type(encrypted_data)}")
        logger.debug(f"復号化前データの内容: {encrypted_data}")  # デバッグ目的で内容も出力
        
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
        logger.debug(f"復号化データの内容（バイト列）: {raw_data}")  # デバッグ目的で内容も出力
        
        # バイト列から文字列への変換（デシリアライズなし）
        try:
            result = raw_data.decode('utf-8')
            logger.debug(f"バイト列を文字列に変換しました: 長さ{len(result)}文字")
            logger.debug(f"変換後文字列の内容: {result}")  # デバッグ目的で内容も出力
            logger.info("データの復号化が完了しました")
            return result
        except UnicodeDecodeError as e:
            logger.debug(f"UTF-8でのデコードに失敗しました: {str(e)}。他のエンコーディングを試みます。")
            
            # 他のエンコーディングを試す
            try:
                # Latin-1（ISO-8859-1）は任意のバイト列をデコードできる
                result = raw_data.decode('latin-1')
                logger.debug(f"バイト列をLatin-1でデコードしました: 長さ{len(result)}文字")
                logger.debug(f"Latin-1でデコードした文字列の内容: {result}")  # デバッグ目的で内容も出力
                logger.info("データの復号化が完了しました（Latin-1エンコーディング）")
                return result
            except Exception as e2:
                logger.error(f"バイト列のデコードに失敗しました: {str(e2)}")
                logger.debug("バイト列をそのまま返します")
                return raw_data
    except Exception as e:
        logger.error(f"データの復号化に失敗しました: {str(e)}", exc_info=True)
        return None
