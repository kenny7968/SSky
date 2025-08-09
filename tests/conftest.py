#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
pytest設定とグローバルフィクスチャ (Phase 2 リファクタリング版)
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from typing import Generator, Dict, Any

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト実行時に必要な環境変数設定
os.environ.setdefault('PYTEST_RUNNING', '1')


@pytest.fixture(scope="session")
def project_root_path():
    """プロジェクトルートパスフィクスチャ"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session") 
def temp_data_dir():
    """テスト用一時データディレクトリ"""
    with tempfile.TemporaryDirectory(prefix="ssky_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_db_file(temp_data_dir):
    """テスト用一時データベースファイル"""
    db_file = temp_data_dir / "test_database.sqlite"
    yield str(db_file)
    # クリーンアップはtempDirによって自動実行


@pytest.fixture
def temp_config_file(temp_data_dir):
    """テスト用一時設定ファイル"""
    config_file = temp_data_dir / "test_config.json"
    yield str(config_file)


@pytest.fixture
def mock_wx():
    """wxPythonのモックフィクスチャ"""
    with patch.dict('sys.modules', {'wx': Mock()}):
        wx_mock = sys.modules['wx']
        
        # 共通の定数設定
        wx_mock.OK = 2
        wx_mock.ICON_ERROR = 512
        wx_mock.ICON_WARNING = 256
        wx_mock.ICON_INFORMATION = 64
        
        # MessageBox の戻り値設定
        wx_mock.MessageBox = Mock(return_value=wx_mock.OK)
        
        yield wx_mock


@pytest.fixture
def mock_atproto_client():
    """atproto Client のモックフィクスチャ"""
    with patch('core.client.api_client.AtprotoClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # デフォルトの戻り値設定
        mock_client.get_timeline.return_value = Mock(feed=[])
        mock_client.send_post.return_value = Mock(uri="test://post/123")
        mock_client.upload_blob.return_value = Mock(ref="test://blob/456")
        
        yield mock_client


@pytest.fixture
def mock_crypto():
    """暗号化処理のモックフィクスチャ"""
    with patch('utils.crypto.encrypt_data') as mock_encrypt, \
         patch('utils.crypto.decrypt_data') as mock_decrypt:
        
        mock_encrypt.return_value = b'encrypted_test_data'
        mock_decrypt.return_value = 'decrypted_test_data'
        
        yield {
            'encrypt': mock_encrypt,
            'decrypt': mock_decrypt
        }


@pytest.fixture
def mock_logger():
    """ロガーのモックフィクスチャ"""
    logger_mock = Mock()
    logger_mock.info = Mock()
    logger_mock.error = Mock()
    logger_mock.warning = Mock()
    logger_mock.debug = Mock()
    return logger_mock


@pytest.fixture
def sample_timeline_data():
    """サンプルタイムラインデータ"""
    return [
        {
            "uri": "at://alice.bsky.social/app.bsky.feed.post/1",
            "cid": "test_cid_1",
            "author": {
                "did": "did:plc:alice123",
                "handle": "alice.bsky.social",
                "displayName": "Alice Test"
            },
            "record": {
                "text": "テスト投稿1です",
                "createdAt": "2024-01-01T12:00:00.000Z",
                "langs": ["ja"]
            },
            "indexedAt": "2024-01-01T12:00:01.000Z"
        },
        {
            "uri": "at://bob.bsky.social/app.bsky.feed.post/2", 
            "cid": "test_cid_2",
            "author": {
                "did": "did:plc:bob456",
                "handle": "bob.bsky.social",
                "displayName": "Bob Test"
            },
            "record": {
                "text": "テスト投稿2です",
                "createdAt": "2024-01-01T11:30:00.000Z",
                "langs": ["ja"]
            },
            "indexedAt": "2024-01-01T11:30:01.000Z"
        }
    ]


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        "did": "did:plc:testuser123",
        "handle": "testuser.bsky.social",
        "displayName": "Test User",
        "description": "テストユーザーです",
        "avatar": "https://example.com/avatar.jpg",
        "followersCount": 100,
        "followsCount": 50,
        "postsCount": 25
    }


@pytest.fixture
def mock_settings_file(temp_config_file):
    """テスト用設定ファイルの内容を準備"""
    settings_data = {
        "timeline_refresh_interval": 30,
        "max_posts_display": 100,
        "enable_notifications": True,
        "theme": "default",
        "language": "ja"
    }
    
    import json
    with open(temp_config_file, 'w', encoding='utf-8') as f:
        json.dump(settings_data, f, ensure_ascii=False, indent=2)
    
    return temp_config_file


@pytest.fixture
def mock_data_store(temp_db_file):
    """テスト用DataStoreインスタンス"""
    # sqlite3を完全にモックせず、実際のsqlite3を使用
    from core.data_store import DataStore
    store = DataStore(temp_db_file)
    yield store


@pytest.fixture
def isolated_data_store():
    """完全に分離されたテスト用DataStore"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    
    try:
        from core.data_store import DataStore
        store = DataStore(temp_db_path)
        yield store
    finally:
        # クリーンアップ
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@pytest.fixture(autouse=True)
def reset_singletons():
    """シングルトンインスタンスのリセット（自動適用）"""
    yield
    
    # テスト終了後にシングルトンをリセット
    # AuthCredentialManager のシングルトンリセット
    try:
        from core.auth.credential_manager import AuthCredentialManager
        if hasattr(AuthCredentialManager, '_instance'):
            AuthCredentialManager._instance = None
    except ImportError:
        pass
    
    # SettingsManager のシングルトンリセット  
    try:
        from config.settings_manager import SettingsManager
        if hasattr(SettingsManager, '_instance'):
            SettingsManager._instance = None
    except ImportError:
        pass


# テスト実行時の設定
def pytest_configure(config):
    """pytest設定フック"""
    # カスタムマーカーの登録
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "gui: mark test as gui test")
    config.addinivalue_line("markers", "network: mark test requiring network")
    config.addinivalue_line("markers", "windows: mark test requiring Windows")


def pytest_collection_modifyitems(config, items):
    """テスト収集時の設定フック"""
    # プラットフォーム固有テストのスキップ設定
    import platform
    if platform.system() != "Windows":
        skip_windows = pytest.mark.skip(reason="Windows platform required")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows)


@pytest.fixture
def event_loop():
    """非同期テスト用イベントループフィクスチャ"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()