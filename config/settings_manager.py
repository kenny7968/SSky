#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
設定管理モジュール
"""

import os
import json
import logging
from utils.file_utils import ensure_directory_exists

# ロガーの設定
logger = logging.getLogger(__name__)

class SettingsManager:
    """設定管理クラス（シングルトン）"""
    
    _instance = None
    _observers = []  # 設定変更の通知先リスト
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化（一度だけ実行）"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        # settingsフォルダにconfig.jsonを配置
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings_dir = os.path.join(base_dir, 'settings')
        ensure_directory_exists(settings_dir)  # フォルダが存在しない場合は作成
        self.settings_file = os.path.join(settings_dir, 'config.json')
        
        # デバッグ用にパスをログ出力
        logger.debug(f"設定ファイルのパス: {self.settings_file}")
        
        # デフォルト設定
        self.default_settings = {
            "timeline": {
                "auto_fetch": True,        # 投稿一覧を自動取得する
                "fetch_interval": 600,     # 自動取得の間隔（秒）
                "fetch_count": 50          # 投稿の取得件数（最大100件）
            },
            "post": {
                "show_completion_dialog": True  # 投稿・返信・引用時に完了ダイアログを表示
            },
            "advanced": {
                "enable_debug_log": False  # デバッグログを有効にする
            }
        }
        
        # 現在の設定（初期値はデフォルト設定）
        self.settings = self.default_settings.copy()
        
        # 設定ファイルの読み込み
        self.load()
    
    def load(self):
        """設定ファイルから設定を読み込む"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 読み込んだ設定でデフォルト設定を更新
                    self._update_nested_dict(self.settings, loaded_settings)
                logger.debug(f"設定ファイルを読み込みました: {self.settings_file}")
                
                # 読み込んだ設定値のバリデーション
                is_valid, error_message = self.validate_settings()
                if not is_valid:
                    logger.warning(f"設定ファイルに無効な値があります: {error_message}")
                    # 無効な値を修正
                    self._fix_invalid_settings()
                    # 修正した設定を保存
                    self.save()
            else:
                logger.debug(f"設定ファイルが存在しないため、デフォルト設定を使用します: {self.settings_file}")
                # 初回起動時は設定ファイルを保存
                self.save()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {str(e)}")
    
    def add_observer(self, observer):
        """設定変更の通知先を追加
        
        Args:
            observer: 通知先オブジェクト（on_settings_changedメソッドを持つ）
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"設定変更の通知先を追加しました: {observer}")

    def remove_observer(self, observer):
        """設定変更の通知先を削除
        
        Args:
            observer: 通知先オブジェクト
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"設定変更の通知先を削除しました: {observer}")

    def notify_observers(self, key=None):
        """設定変更を通知
        
        Args:
            key (str, optional): 変更された設定キー。Noneの場合は全体の変更を通知
        """
        for observer in self._observers:
            if hasattr(observer, 'on_settings_changed'):
                try:
                    observer.on_settings_changed(key)
                    logger.debug(f"設定変更を通知しました: observer={observer}, key={key}")
                except Exception as e:
                    logger.error(f"設定変更の通知中にエラーが発生しました: {str(e)}")
    
    def save(self):
        """現在の設定をファイルに保存する（変更通知付き）"""
        try:
            # 設定ファイルのディレクトリを確認
            settings_dir = os.path.dirname(self.settings_file)
            ensure_directory_exists(settings_dir)
            
            # 書き込み権限のチェック
            if os.path.exists(self.settings_file):
                if not os.access(self.settings_file, os.W_OK):
                    logger.error(f"設定ファイルへの書き込み権限がありません: {self.settings_file}")
                    return False
            
            # 設定をJSONとして保存
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            logger.debug(f"設定ファイルを保存しました: {self.settings_file}")
            
            # 設定変更を通知（全体の変更として通知）
            self.notify_observers()
            
            return True
        except PermissionError as e:
            logger.error(f"設定ファイルへのアクセス権限がありません: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        except IOError as e:
            logger.error(f"設定ファイルの入出力エラー: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {str(e)}")
            # エラーの詳細をログに出力
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get(self, key, default=None):
        """設定値を取得する
        
        Args:
            key (str): 設定キー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            設定値またはデフォルト値
        """
        # ネストされたキーに対応（例: 'timeline.auto_fetch'）
        if '.' in key:
            parts = key.split('.')
            value = self.settings
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return self.settings.get(key, default)
    
    def set(self, key, value):
        """設定値を設定する（変更通知付き）
        
        Args:
            key (str): 設定キー
            value: 設定値
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # 現在の値を取得
            old_value = self.get(key)
            
            # 値が変更されない場合は何もしない
            if old_value == value:
                return True
                
            # ネストされたキーに対応（例: 'timeline.auto_fetch'）
            if '.' in key:
                parts = key.split('.')
                settings = self.settings
                for part in parts[:-1]:
                    if part not in settings:
                        settings[part] = {}
                    settings = settings[part]
                settings[parts[-1]] = value
            else:
                self.settings[key] = value
                
            # 設定変更を通知
            self.notify_observers(key)
            
            return True
        except Exception as e:
            logger.error(f"設定の更新に失敗しました: {str(e)}")
            return False
    
    def validate_settings(self):
        """設定値のバリデーションを行う
        
        Returns:
            tuple: (is_valid, error_message)
                is_valid: バリデーション結果（True/False）
                error_message: エラーメッセージ（エラーがない場合はNone）
        """
        # 自動取得の間隔のバリデーション
        fetch_interval = self.get('timeline.fetch_interval', 180)
        if fetch_interval < 180:
            return False, "自動取得の間隔は180秒以上に設定してください。"
        
        # 投稿の取得件数のバリデーション
        fetch_count = self.get('timeline.fetch_count', 50)
        if fetch_count < 1 or fetch_count > 100:
            return False, "投稿の取得件数は1以上100以下に設定してください。"
        
        # 他のバリデーションルールがあれば追加
        
        return True, None
    
    def set_with_validation(self, key, value):
        """バリデーションを行いながら設定値を設定する
        
        Args:
            key (str): 設定キー
            value: 設定値
            
        Returns:
            tuple: (success, error_message)
                success: 設定の更新に成功したかどうか（True/False）
                error_message: エラーメッセージ（エラーがない場合はNone）
        """
        # 特定の設定値のバリデーション
        if key == 'timeline.fetch_interval' and value < 180:
            return False, "自動取得の間隔は180秒以上に設定してください。"
        
        # 投稿の取得件数のバリデーション
        if key == 'timeline.fetch_count' and (value < 1 or value > 100):
            return False, "投稿の取得件数は1以上100以下に設定してください。"
        
        # 設定値の更新
        success = self.set(key, value)
        if not success:
            return False, "設定の更新に失敗しました。"
        
        return True, None
    
    def _fix_invalid_settings(self):
        """無効な設定値を修正する"""
        # 自動取得の間隔が180秒未満の場合は180秒に設定
        fetch_interval = self.get('timeline.fetch_interval', 180)
        if fetch_interval < 180:
            self.set('timeline.fetch_interval', 180)
            logger.info("自動取得の間隔が180秒未満だったため、180秒に設定しました。")
        
        # 投稿の取得件数が範囲外の場合は修正
        fetch_count = self.get('timeline.fetch_count', 50)
        if fetch_count < 1:
            self.set('timeline.fetch_count', 1)
            logger.info("投稿の取得件数が1未満だったため、1に設定しました。")
        elif fetch_count > 100:
            self.set('timeline.fetch_count', 100)
            logger.info("投稿の取得件数が100を超えていたため、100に設定しました。")
    
    def _update_nested_dict(self, d, u):
        """ネストされた辞書を更新する
        
        Args:
            d (dict): 更新される辞書
            u (dict): 更新する辞書
            
        Returns:
            dict: 更新された辞書
        """
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._update_nested_dict(d.get(k, {}), v)
            else:
                d[k] = v
        return d
