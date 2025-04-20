#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーション設定モジュール
"""

import os
import json
import logging
from utils.file_utils import ensure_directory_exists

# ロガーの設定
logger = logging.getLogger(__name__)

class AppConfig:
    """アプリケーション設定クラス"""
    
    def __init__(self, config_file=None):
        """初期化
        
        Args:
            config_file (str, optional): 設定ファイルのパス。
                指定しない場合はデフォルトのパスを使用。
        """
        if config_file is None:
            # デフォルトの設定ファイルパス
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, 'config')
            ensure_directory_exists(config_dir)
            self.config_file = os.path.join(config_dir, 'app_config.json')
        else:
            self.config_file = config_file
            
        # デフォルト設定
        self.config = {
            # アプリケーション設定
            'app_name': 'SSky',
            'version': '1.0.0',
            
            # UI設定
            'theme': 'light',  # light または dark
            'font_size': 10,   # フォントサイズ
            'window_size': {
                'width': 800,
                'height': 600
            },
            
            # タイムライン設定
            'timeline': {
                'refresh_interval': 60,  # 秒単位
                'post_count': 50,        # 取得する投稿数
                'auto_refresh': True     # 自動更新の有効/無効
            },
            
            # その他の設定
            'debug_mode': False
        }
        
        # 設定ファイルの読み込み
        self.load()
        
    def load(self):
        """設定ファイルから設定を読み込む"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 読み込んだ設定でデフォルト設定を更新
                    self.config.update(loaded_config)
                logger.debug(f"設定ファイルを読み込みました: {self.config_file}")
            else:
                logger.debug(f"設定ファイルが存在しないため、デフォルト設定を使用します: {self.config_file}")
                # 初回起動時は設定ファイルを保存
                self.save()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {str(e)}")
            
    def save(self):
        """現在の設定をファイルに保存する"""
        try:
            # 設定ファイルのディレクトリを確認
            config_dir = os.path.dirname(self.config_file)
            ensure_directory_exists(config_dir)
            
            # 設定をJSONとして保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.debug(f"設定ファイルを保存しました: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {str(e)}")
            return False
            
    def get(self, key, default=None):
        """設定値を取得する
        
        Args:
            key (str): 設定キー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            設定値またはデフォルト値
        """
        # ネストされたキーに対応（例: 'timeline.refresh_interval'）
        if '.' in key:
            parts = key.split('.')
            value = self.config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return self.config.get(key, default)
            
    def set(self, key, value):
        """設定値を設定する
        
        Args:
            key (str): 設定キー
            value: 設定値
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # ネストされたキーに対応（例: 'timeline.refresh_interval'）
            if '.' in key:
                parts = key.split('.')
                config = self.config
                for part in parts[:-1]:
                    if part not in config:
                        config[part] = {}
                    config = config[part]
                config[parts[-1]] = value
            else:
                self.config[key] = value
            return True
        except Exception as e:
            logger.error(f"設定の更新に失敗しました: {str(e)}")
            return False
