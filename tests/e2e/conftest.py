#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
E2E（エンドツーエンド）テスト共通fixture設定
"""

import pytest
import tempfile
import threading
import time
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from typing import Generator, Dict, Any

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def e2e_temp_environment():
    """E2Eテスト用の完全に分離された環境"""
    with tempfile.TemporaryDirectory(prefix="ssky_e2e_") as temp_dir:
        temp_path = Path(temp_dir)
        
        # テスト用ディレクトリ構造
        data_dir = temp_path / "data"
        config_dir = temp_path / "config"
        logs_dir = temp_path / "logs"
        
        data_dir.mkdir()
        config_dir.mkdir()
        logs_dir.mkdir()
        
        # テスト用データベース
        test_db = data_dir / "test_ssky.db"
        
        # テスト用設定ファイル
        test_config = config_dir / "settings.json"
        
        environment = {
            "temp_dir": temp_path,
            "data_dir": data_dir,
            "config_dir": config_dir,
            "logs_dir": logs_dir,
            "db_file": str(test_db),
            "config_file": str(test_config)
        }
        
        yield environment


@pytest.fixture
def e2e_mock_wx_app():
    """E2Eテスト用wxPythonアプリケーションモック"""
    
    # wxPython全体をモック
    wx_mock = MagicMock()
    
    # App クラスのモック
    app_mock = MagicMock()
    app_mock.MainLoop = MagicMock()
    app_mock.ExitMainLoop = MagicMock()
    app_mock.Destroy = MagicMock()
    
    # Frame クラスのモック
    frame_mock = MagicMock()
    frame_mock.Show = MagicMock(return_value=True)
    frame_mock.Close = MagicMock(return_value=True)
    frame_mock.Destroy = MagicMock()
    
    # 基本的なwx定数
    wx_mock.ID_EXIT = 5006
    wx_mock.ID_ABOUT = 5014
    wx_mock.OK = 2
    wx_mock.ICON_INFORMATION = 64
    wx_mock.ICON_ERROR = 512
    
    # MessageBox
    wx_mock.MessageBox = MagicMock(return_value=wx_mock.OK)
    
    with patch.dict('sys.modules', {'wx': wx_mock}):
        yield {
            'wx': wx_mock,
            'app': app_mock,
            'frame': frame_mock
        }


@pytest.fixture
def e2e_mock_bluesky_api():
    """E2Eテスト用Bluesky API完全モック"""
    
    # 成功レスポンスのサンプルデータ
    sample_timeline = [
        {
            "uri": "at://test.user/app.bsky.feed.post/1",
            "cid": "test_cid_1",
            "author": {
                "did": "did:plc:testuser123",
                "handle": "test.user",
                "displayName": "テストユーザー"
            },
            "record": {
                "text": "E2Eテスト用投稿",
                "createdAt": "2024-01-01T12:00:00.000Z"
            },
            "indexedAt": "2024-01-01T12:00:01.000Z"
        }
    ]
    
    sample_profile = {
        "did": "did:plc:testuser123",
        "handle": "test.user",
        "displayName": "テストユーザー",
        "description": "E2Eテスト用プロフィール"
    }
    
    # AtprotoClientのモック
    with patch('core.client.api_client.AtprotoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # API呼び出しのモック設定
        mock_client.login.return_value = True
        mock_client.get_profile.return_value = sample_profile
        mock_client.get_timeline.return_value = Mock(feed=sample_timeline)
        mock_client.send_post.return_value = Mock(uri="at://test.user/app.bsky.feed.post/new")
        mock_client.upload_blob.return_value = Mock(ref="test_blob_ref")
        
        yield {
            'client_class': mock_client_class,
            'client': mock_client,
            'sample_timeline': sample_timeline,
            'sample_profile': sample_profile
        }


@pytest.fixture
def e2e_app_components(e2e_temp_environment, e2e_mock_wx_app, e2e_mock_bluesky_api):
    """E2Eテスト用アプリケーションコンポーネント統合セットアップ"""
    
    components = {}
    
    # 環境変数設定
    os.environ['SSKY_DATA_DIR'] = str(e2e_temp_environment['data_dir'])
    os.environ['SSKY_CONFIG_DIR'] = str(e2e_temp_environment['config_dir'])
    os.environ['PYTEST_E2E_RUNNING'] = '1'
    
    try:
        # DataStore の初期化
        from core.data_store import DataStore
        data_store = DataStore(e2e_temp_environment['db_file'])
        components['data_store'] = data_store
        
        # 暗号化モック
        with patch('utils.crypto.encrypt_data') as mock_encrypt, \
             patch('utils.crypto.decrypt_data') as mock_decrypt:
            
            mock_encrypt.return_value = b'e2e_encrypted_data'
            mock_decrypt.return_value = 'e2e_decrypted_data'
            
            # CredentialManager の初期化
            from core.auth.credential_manager import AuthCredentialManager
            AuthCredentialManager._instance = None
            credential_manager = AuthCredentialManager()
            components['credential_manager'] = credential_manager
        
        # BlueskyClient の初期化（モックAPI付き）
        from core.client.facade import BlueskyClient
        bluesky_client = BlueskyClient()
        components['bluesky_client'] = bluesky_client
        
        # 設定マネージャーの初期化
        from config.settings_manager import SettingsManager
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.settings_file = e2e_temp_environment['config_file']
        components['settings_manager'] = settings_manager
        
        # モックデータ
        components.update(e2e_mock_bluesky_api)
        components.update(e2e_mock_wx_app)
        
        yield components
        
    finally:
        # クリーンアップ
        try:
            AuthCredentialManager._instance = None
            SettingsManager._instance = None
        except:
            pass
        
        # 環境変数クリーンアップ
        for env_var in ['SSKY_DATA_DIR', 'SSKY_CONFIG_DIR', 'PYTEST_E2E_RUNNING']:
            os.environ.pop(env_var, None)


@pytest.fixture
def e2e_user_scenario_data():
    """E2Eテスト用ユーザーシナリオデータ"""
    return {
        "valid_credentials": {
            "handle": "test.user",
            "password": "test_password_123"
        },
        "invalid_credentials": {
            "handle": "invalid.user",
            "password": "wrong_password"
        },
        "test_post_content": "E2Eテストからの投稿です #テスト",
        "test_reply_content": "E2Eテストからの返信です",
        "test_user_to_follow": "follow.target.user",
        "test_user_to_block": "block.target.user",
        "test_settings_changes": {
            "timeline_refresh_interval": 60,
            "max_posts_display": 200,
            "theme": "dark",
            "language": "en"
        }
    }


@pytest.fixture
def e2e_application_lifecycle():
    """E2Eテスト用アプリケーションライフサイクル管理"""
    
    class AppLifecycleManager:
        def __init__(self):
            self.app_process = None
            self.app_thread = None
            self.is_running = False
            
        def start_app(self, components):
            """アプリケーション開始（モック環境）"""
            self.is_running = True
            # 実際のアプリ起動ではなく、モックによるシミュレーション
            return True
            
        def stop_app(self):
            """アプリケーション停止"""
            if self.is_running:
                self.is_running = False
                if self.app_thread and self.app_thread.is_alive():
                    self.app_thread.join(timeout=5)
                return True
            return False
            
        def restart_app(self, components):
            """アプリケーション再起動"""
            self.stop_app()
            time.sleep(0.1)  # 短い待機
            return self.start_app(components)
            
        def is_app_running(self):
            """アプリケーション実行状態確認"""
            return self.is_running
    
    manager = AppLifecycleManager()
    yield manager
    
    # テスト終了時のクリーンアップ
    manager.stop_app()


@pytest.fixture
def e2e_test_timeout():
    """E2Eテスト用タイムアウト設定"""
    return {
        "short": 5,      # 5秒 - 基本操作
        "medium": 15,    # 15秒 - API呼び出し
        "long": 30,      # 30秒 - 複雑なシナリオ
        "very_long": 60  # 60秒 - 全体テスト
    }


# テスト実行設定
def pytest_configure(config):
    """E2Eテスト固有の設定"""
    # E2Eテスト用マーカー
    config.addinivalue_line("markers", "e2e_smoke: E2E smoke tests")
    config.addinivalue_line("markers", "e2e_full: Full E2E test scenarios")
    config.addinivalue_line("markers", "e2e_gui: GUI-focused E2E tests")
    config.addinivalue_line("markers", "e2e_api: API-focused E2E tests")