#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーション定数管理モジュール
"""

import os
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class AppConstants:
    """アプリケーション定数管理クラス
    
    責任:
    - アプリケーション定数の提供
    - バージョン情報、APIエンドポイントなどのハードコードされた不変値の管理
    """
    
    _instance = None
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(AppConstants, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化（一度だけ実行）"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        # ベースディレクトリの取得
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # すべての定数をコード内に直接定義
        self.constants = {
            # アプリケーション情報
            'app_name': 'SSky',
            'version': '1.0.0',
            'api_endpoint': 'https://bsky.social',
            
            # システム制限値
            'max_post_length': 300,
            'max_image_size': 1024 * 1024 * 5,  # 5MB
            'max_attachments': 4,
            'supported_image_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            
            # API設定
            'max_retries': 3,
            'retry_delay': 1,
            'timeout': 30,
            'connection_timeout': 10,
            'max_connections': 10,
            
            # デバッグ設定
            'debug_mode': False,
            
            # ディレクトリパス（実行時に計算）
            'dirs': {
                'config': os.path.join(self.base_dir, 'config'),
                'log': os.path.join(self.base_dir, 'log'),
                'data': os.path.join(self.base_dir, 'data'),
                'settings': os.path.join(self.base_dir, 'settings'),
                'assets': os.path.join(self.base_dir, 'assets'),
            },
            
            # 更新チェック関連
            'update_check_url': '',
            'update_interval': 7,  # 日単位
        }
    
    def get(self, key, default=None):
        """定数値を取得する
        
        Args:
            key (str): 定数キー（ドット区切りでネストされた値にアクセス可能）
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            定数値またはデフォルト値
        """
        if '.' in key:
            parts = key.split('.')
            value = self.constants
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return self.constants.get(key, default)

# シングルトンインスタンス取得用のヘルパー関数
def get_app_constants():
    """アプリケーション定数のシングルトンインスタンスを取得する"""
    return AppConstants()

# 便利なアクセサメソッド
def get_app_name():
    """アプリケーション名を取得する"""
    return get_app_constants().get('app_name')

def get_app_version():
    """アプリケーションのバージョンを取得する"""
    return get_app_constants().get('version')

def get_api_endpoint():
    """APIエンドポイントを取得する"""
    return get_app_constants().get('api_endpoint')

def get_debug_mode():
    """デバッグモードかどうかを取得する"""
    return get_app_constants().get('debug_mode', False)

def get_max_retries():
    """APIリクエストの最大リトライ回数を取得する"""
    return get_app_constants().get('max_retries', 3)

def get_retry_delay():
    """APIリクエストのリトライ間隔（秒）を取得する"""
    return get_app_constants().get('retry_delay', 1)

def get_timeout():
    """APIリクエストのタイムアウト（秒）を取得する"""
    return get_app_constants().get('timeout', 30)

def get_max_connections():
    """最大同時接続数を取得する"""
    return get_app_constants().get('max_connections', 10)

def get_connection_timeout():
    """接続タイムアウト（秒）を取得する"""
    return get_app_constants().get('connection_timeout', 10)

def get_update_check_url():
    """アップデートチェック用URLを取得する"""
    return get_app_constants().get('update_check_url', '')

def get_update_interval():
    """アップデートチェックの間隔（日数）を取得する"""
    return get_app_constants().get('update_interval', 7)

def get_max_post_length():
    """投稿の最大文字数を取得する"""
    return get_app_constants().get('max_post_length', 300)

def get_max_image_size():
    """添付画像の最大サイズを取得する"""
    return get_app_constants().get('max_image_size', 1024 * 1024 * 5)

def get_max_attachments():
    """添付ファイルの最大数を取得する"""
    return get_app_constants().get('max_attachments', 4)

def get_supported_image_formats():
    """サポートする画像形式を取得する"""
    return get_app_constants().get('supported_image_formats', ['jpg', 'jpeg', 'png', 'gif', 'webp'])

def get_user_agent():
    """ユーザーエージェントを取得する"""
    return f"SSky/{get_app_version()} (https://github.com/kenny7968/SSky)"

# ディレクトリパス取得関数
def get_base_dir():
    """アプリケーションのベースディレクトリを取得する"""
    return get_app_constants().base_dir

def get_config_dir():
    """設定ディレクトリを取得する"""
    return get_app_constants().get('dirs.config')

def get_log_dir():
    """ログディレクトリを取得する"""
    log_dir = get_app_constants().get('dirs.log')
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            logger.error(f"ログディレクトリの作成に失敗しました: {e}")
    return log_dir

def get_data_dir():
    """データディレクトリを取得する"""
    data_dir = get_app_constants().get('dirs.data')
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except Exception as e:
            logger.error(f"データディレクトリの作成に失敗しました: {e}")
    return data_dir

def get_settings_dir():
    """設定ディレクトリを取得する"""
    settings_dir = get_app_constants().get('dirs.settings')
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(settings_dir):
        try:
            os.makedirs(settings_dir)
        except Exception as e:
            logger.error(f"設定ディレクトリの作成に失敗しました: {e}")
    return settings_dir

def get_assets_dir():
    """アセットディレクトリを取得する"""
    return get_app_constants().get('dirs.assets')

def get_app_icon_path():
    """アプリケーションアイコンのパスを取得する"""
    return os.path.join(get_assets_dir(), "icon.ico")

def get_db_path():
    """データベースファイルのパスを取得する"""
    return os.path.join(get_data_dir(), "ssky.db")

def get_settings_path():
    """ユーザー設定ファイルのパスを取得する"""
    return os.path.join(get_settings_dir(), "config.json")

# アプリケーション全体で使用する定数
MAX_POST_LENGTH = get_max_post_length()
MAX_IMAGE_SIZE = get_max_image_size()
MAX_ATTACHMENTS = get_max_attachments()
SUPPORTED_IMAGE_FORMATS = get_supported_image_formats()
USER_AGENT = get_user_agent()

# デバッグモードの設定
DEBUG = get_debug_mode()
