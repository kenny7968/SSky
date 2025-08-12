#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
統合テスト共通fixture設定 (Phase 1修正)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import tempfile
import sqlite3
from pathlib import Path


@pytest.fixture
def integrated_auth_components(temp_db_file, mock_crypto):
    """統合された認証コンポーネント"""
    components = {}
    
    # DataStore は実際のsqlite3を使用（モックなし）
    from core.data_store import DataStore
    components['data_store'] = DataStore(temp_db_file)
    
    # CredentialManager の設定（暗号化関数を注入）
    from core.auth.credential_manager import AuthCredentialManager
    # シングルトンリセット
    AuthCredentialManager._instance = None
    # 暗号化関数を注入してCredentialManagerを作成
    components['credential_manager'] = AuthCredentialManager(
        data_store=components['data_store'],
        encrypt_func=mock_crypto['encrypt'],
        decrypt_func=mock_crypto['decrypt']
    )
    
    # BlueskyClient のモック設定（APIクライアントのみモック）
    with patch('core.client.api_client.AtprotoClient') as mock_atproto:
        mock_client = Mock()
        mock_atproto.return_value = mock_client
        
        from core.client.facade import BlueskyClient
        components['bluesky_client'] = BlueskyClient()
        components['mock_atproto'] = mock_client
    
    yield components
    
    # クリーンアップ
    try:
        from core.auth.credential_manager import AuthCredentialManager
        AuthCredentialManager._instance = None
    except:
        pass


@pytest.fixture
def integrated_error_handling_components(temp_db_file, mock_crypto, mock_wx):
    """統合されたエラー処理関連コンポーネント"""
    components = {}
    
    # wxのモックを追加
    components['mock_wx'] = mock_wx
    
    # DataStore は実際のsqlite3を使用（モックなし）
    from core.data_store import DataStore
    components['data_store'] = DataStore(temp_db_file)
    
    # CredentialManager の設定（暗号化関数を注入）
    from core.auth.credential_manager import AuthCredentialManager
    # シングルトンリセット
    AuthCredentialManager._instance = None
    # 暗号化関数を注入してCredentialManagerを作成
    components['credential_manager'] = AuthCredentialManager(
        data_store=components['data_store'],
        encrypt_func=mock_crypto['encrypt'],
        decrypt_func=mock_crypto['decrypt']
    )
    
    # BlueskyClient のモック設定（APIクライアントのみモック）
    with patch('core.client.api_client.AtprotoClient') as mock_atproto:
        mock_client = Mock()
        mock_atproto.return_value = mock_client
        
        from core.client.facade import BlueskyClient
        components['bluesky_client'] = BlueskyClient()
        components['mock_atproto'] = mock_client
    
    # エラーハンドラーの設定
    from core.error_handler import UnifiedErrorHandler
    components['error_handler'] = UnifiedErrorHandler(components['bluesky_client'].auth_manager)
    
    yield components
    
    # クリーンアップ
    try:
        from core.auth.credential_manager import AuthCredentialManager
        AuthCredentialManager._instance = None
    except:
        pass


@pytest.fixture  
def integrated_post_components(temp_db_file, mock_crypto):
    """統合された投稿関連コンポーネント"""
    components = {}
    
    # DataStore の設定（実際のSQLite使用）
    from core.data_store import DataStore
    components['data_store'] = DataStore(temp_db_file)
    
    # CredentialManager の設定（暗号化関数を注入）
    from core.auth.credential_manager import AuthCredentialManager
    AuthCredentialManager._instance = None
    # 暗号化関数を注入してCredentialManagerを作成
    components['credential_manager'] = AuthCredentialManager(
        data_store=components['data_store'],
        encrypt_func=mock_crypto['encrypt'],
        decrypt_func=mock_crypto['decrypt']
    )
    
    # APIクライアントのモック設定
    with patch('core.client.api_client.AtprotoClient') as mock_atproto:
        mock_client = Mock()
        mock_atproto.return_value = mock_client
        
        from core.client.facade import BlueskyClient
        components['bluesky_client'] = BlueskyClient()
        components['mock_atproto'] = mock_client
    
    yield components
    
    # クリーンアップ
    try:
        from core.auth.credential_manager import AuthCredentialManager
        AuthCredentialManager._instance = None
    except:
        pass


@pytest.fixture
def integrated_settings_components(temp_db_file):
    """統合された設定関連コンポーネント"""
    components = {}
    
    # 設定ファイル用の一時ディレクトリと一時ファイル
    import tempfile
    import json
    from pathlib import Path
    temp_dir = tempfile.mkdtemp()
    temp_config_file = Path(temp_dir) / "test_settings.json"
    
    # 初期設定を作成
    initial_settings = {
        "timeline_refresh_interval": 30,
        "max_posts_display": 100,
        "enable_notifications": True,
        "theme": "default",
        "language": "ja",
        "auto_fetch_enabled": False,
        "fetch_count": 50
    }
    
    with open(temp_config_file, 'w', encoding='utf-8') as f:
        json.dump(initial_settings, f, ensure_ascii=False, indent=2)
    
    components['temp_dir'] = temp_dir
    components['config_file'] = str(temp_config_file)
    components['initial_settings'] = initial_settings
    
    # 設定マネージャーの設定（一時ファイルパスを使用）
    from config.settings_manager import SettingsManager
    
    # シングルトンリセット
    if hasattr(SettingsManager, '_instance'):
        SettingsManager._instance = None
        
    # インスタンス作成後にファイルパスを上書きして設定をロード
    settings_manager = SettingsManager()
    settings_manager.settings_file = str(temp_config_file)
    settings_manager.load()  # 一時ファイルから設定を読み込み
    
    components['settings_manager'] = settings_manager
    
    # DataStore の設定（設定保存用）
    from core.data_store import DataStore  
    components['data_store'] = DataStore(temp_db_file)
    
    yield components
    
    # クリーンアップ
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass