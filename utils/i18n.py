#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
国際化管理モジュール
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# ロガーの設定
logger = logging.getLogger(__name__)

class I18nManager:
    """国際化管理クラス
    
    責任:
    - 言語リソースの読み込み
    - メッセージの翻訳
    - 言語切り替え
    - 動的な文字列リソース管理
    """
    
    _instance: Optional['I18nManager'] = None
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.locale_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')
        self.current_locale = 'ja'  # デフォルトは日本語
        self.messages: Dict[str, Any] = {}
        self.fallback_locale = 'ja'  # フォールバック言語
        
        # 初期化時に現在の言語を読み込み
        self._load_messages(self.current_locale)
    
    def _load_messages(self, locale: str) -> bool:
        """指定された言語のメッセージを読み込み
        
        Args:
            locale (str): 言語コード（ja, en等）
            
        Returns:
            bool: 読み込み成功の可否
        """
        try:
            locale_file = os.path.join(self.locale_dir, f"{locale}.json")
            
            if not os.path.exists(locale_file):
                logger.warning(f"言語ファイルが見つかりません: {locale_file}")
                return False
            
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.messages = json.load(f)
            
            logger.debug(f"言語リソースを読み込みました: {locale}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"言語ファイルの読み込みに失敗しました: {locale_file}, エラー: {str(e)}")
            return False
    
    def get_message(self, key: str, **kwargs) -> str:
        """メッセージキーから翻訳済みメッセージを取得
        
        Args:
            key (str): メッセージキー（ドット区切り形式: "menu.login", "error.network"等）
            **kwargs: メッセージ内の変数置換用パラメータ
            
        Returns:
            str: 翻訳済みメッセージ。見つからない場合はキー名を返す
        """
        try:
            # ドット区切りキーを階層辿り
            message = self.messages
            for part in key.split('.'):
                if isinstance(message, dict) and part in message:
                    message = message[part]
                else:
                    # フォールバック処理：キー名をそのまま返す
                    logger.warning(f"メッセージキーが見つかりません: {key}")
                    return key
            
            # メッセージが文字列でない場合の処理
            if not isinstance(message, str):
                logger.warning(f"メッセージが文字列ではありません: {key}")
                return key
            
            # パラメータ置換
            if kwargs:
                try:
                    message = message.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"メッセージ内のパラメータが不足しています: {key}, 不足パラメータ: {str(e)}")
            
            return message
            
        except Exception as e:
            logger.error(f"メッセージ取得中にエラーが発生しました: {key}, エラー: {str(e)}")
            return key
    
    def set_locale(self, locale: str) -> bool:
        """言語を切り替え
        
        Args:
            locale (str): 言語コード
            
        Returns:
            bool: 切り替え成功の可否
        """
        if locale == self.current_locale:
            return True
        
        if self._load_messages(locale):
            old_locale = self.current_locale
            self.current_locale = locale
            logger.info(f"言語を切り替えました: {old_locale} -> {locale}")
            return True
        else:
            logger.error(f"言語切り替えに失敗しました: {locale}")
            return False
    
    def get_current_locale(self) -> str:
        """現在の言語コードを取得
        
        Returns:
            str: 現在の言語コード
        """
        return self.current_locale
    
    def get_available_locales(self) -> list:
        """利用可能な言語一覧を取得
        
        Returns:
            list: 利用可能な言語コードのリスト
        """
        try:
            if not os.path.exists(self.locale_dir):
                return ['ja']  # デフォルトは日本語のみ
            
            locales = []
            for file in os.listdir(self.locale_dir):
                if file.endswith('.json'):
                    locales.append(file[:-5])  # .json拡張子を除去
            
            return sorted(locales) if locales else ['ja']
            
        except OSError:
            return ['ja']

# シングルトンインスタンス作成用のヘルパー関数
def get_i18n() -> I18nManager:
    """I18nManagerのシングルトンインスタンスを取得
    
    Returns:
        I18nManager: 国際化管理インスタンス
    """
    return I18nManager()

# 簡易アクセス用のヘルパー関数
def _(key: str, **kwargs) -> str:
    """メッセージ翻訳のショートカット関数
    
    Args:
        key (str): メッセージキー
        **kwargs: メッセージ内の変数置換用パラメータ
        
    Returns:
        str: 翻訳済みメッセージ
    """
    return get_i18n().get_message(key, **kwargs)