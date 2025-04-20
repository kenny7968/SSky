#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
暗号化ユーティリティモジュール
"""

import pickle
import logging
import win32crypt

# ロガーの設定
logger = logging.getLogger(__name__)

def encrypt_data(data):
    """DPAPIを使用してデータを暗号化"""
    try:
        # デバッグ情報（機密データは含めない）
        logger.debug(f"暗号化前データの型: {type(data)}")
        
        # データをシリアライズ
        serialized_data = pickle.dumps(data)
        logger.debug(f"シリアライズ後データの長さ: {len(serialized_data)}")
        
        # DPAPIで暗号化
        encrypted_data = win32crypt.CryptProtectData(
            serialized_data,
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
        try:
            decrypted_data = win32crypt.CryptUnprotectData(
                encrypted_data,
                None,  # 説明（任意）
                None,  # エントロピー（任意）
                None,  # 予約済み
                0      # フラグ
            )
            
            # デバッグ情報（機密データは含めない）
            logger.debug(f"復号化データの型: {type(decrypted_data)}")
            
            # 戻り値の構造を確認
            if isinstance(decrypted_data, tuple):
                logger.debug(f"復号化データはタプル、長さ: {len(decrypted_data)}")
                if len(decrypted_data) > 1:
                    # 通常の戻り値構造（タプルの2番目の要素にデータが含まれる）
                    data = decrypted_data[1]
                else:
                    # 1要素のタプル
                    data = decrypted_data[0]
            else:
                # タプル以外の戻り値
                data = decrypted_data
            
            logger.debug(f"抽出したデータの型: {type(data)}")
            
            # デシリアライズ
            result = pickle.loads(data)
            logger.debug(f"デシリアライズ後データの型: {type(result)}")
            return result
            
        except ValueError as ve:
            logger.error(f"復号化データの構造が不正です: {str(ve)}", exc_info=True)
            return None
            
    except Exception as e:
        logger.error(f"データの復号化に失敗しました: {str(e)}", exc_info=True)
        return None
