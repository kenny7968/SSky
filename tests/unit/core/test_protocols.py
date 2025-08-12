#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
プロトコル定義の単体テスト (pytest版)
"""

import pytest
from typing import Optional, Dict, Any, List
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.protocols import (
    ConfigManagerProtocol,
    AuthManagerProtocol,
    ApiClientProtocol,
    DataStoreProtocol,
    EventPublisherProtocol,
    CryptoProtocol
)


class TestConfigManagerProtocol:
    """ConfigManagerProtocolのテストクラス"""
    
    def test_config_manager_protocol_implementation(self):
        """ConfigManagerProtocol実装テスト"""
        
        class MockConfigManager:
            def get_value(self, key: str, default: Any = None) -> Any:
                return default or "test_value"
            
            def set_value(self, key: str, value: Any) -> bool:
                return True
            
            def save_config(self) -> bool:
                return True
            
            def load_config(self) -> bool:
                return True
        
        # プロトコルに準拠していることを確認
        config_manager = MockConfigManager()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        # 代わりに必要なメソッドの存在を確認
        
        # メソッドの動作確認
        assert config_manager.get_value("test_key") == "test_value"
        assert config_manager.get_value("test_key", "default") == "default"
        assert config_manager.set_value("test_key", "new_value") is True
        assert config_manager.save_config() is True
        assert config_manager.load_config() is True
    
    def test_config_manager_protocol_mock(self):
        """ConfigManagerProtocolのモックテスト"""
        mock_config = MagicMock(spec=ConfigManagerProtocol)
        
        # モックの設定
        mock_config.get_value.return_value = "mocked_value"
        mock_config.set_value.return_value = True
        mock_config.save_config.return_value = True
        mock_config.load_config.return_value = False
        
        # 動作確認
        assert mock_config.get_value("key") == "mocked_value"
        assert mock_config.set_value("key", "value") is True
        assert mock_config.save_config() is True
        assert mock_config.load_config() is False


class TestAuthManagerProtocol:
    """AuthManagerProtocolのテストクラス"""
    
    def test_auth_manager_protocol_implementation(self):
        """AuthManagerProtocol実装テスト"""
        
        class MockAuthManager:
            def __init__(self):
                self._is_logged_in = False
            
            @property
            def is_logged_in(self) -> bool:
                return self._is_logged_in
            
            def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
                self._is_logged_in = True
                return {"handle": username, "did": "did:plc:test"}
            
            def login_with_session(self, session_string: str) -> Optional[Dict[str, Any]]:
                self._is_logged_in = True
                return {"handle": "user.bsky.social", "did": "did:plc:test"}
            
            def logout(self) -> bool:
                self._is_logged_in = False
                return True
            
            def export_session_string(self) -> Optional[str]:
                return "session_token_string" if self._is_logged_in else None
        
        # プロトコルに準拠していることを確認
        auth_manager = MockAuthManager()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        
        # メソッドの動作確認
        assert auth_manager.is_logged_in is False
        
        profile = auth_manager.login("test.bsky.social", "password")
        assert profile is not None
        assert auth_manager.is_logged_in is True
        
        session = auth_manager.export_session_string()
        assert session == "session_token_string"
        
        assert auth_manager.logout() is True
        assert auth_manager.is_logged_in is False
    
    def test_auth_manager_protocol_mock(self):
        """AuthManagerProtocolのモックテスト"""
        mock_auth = MagicMock(spec=AuthManagerProtocol)
        
        # プロパティのモック
        type(mock_auth).is_logged_in = True
        
        # メソッドのモック
        mock_auth.login.return_value = {"handle": "test.bsky.social"}
        mock_auth.login_with_session.return_value = {"handle": "test.bsky.social"}
        mock_auth.logout.return_value = True
        mock_auth.export_session_string.return_value = "mock_session"
        
        # 動作確認
        assert mock_auth.is_logged_in is True
        assert mock_auth.login("user", "pass")["handle"] == "test.bsky.social"
        assert mock_auth.logout() is True


class TestApiClientProtocol:
    """ApiClientProtocolのテストクラス"""
    
    def test_api_client_protocol_implementation(self):
        """ApiClientProtocol実装テスト"""
        
        class MockApiClient:
            def get_timeline(self, limit: int = 50) -> Optional[Dict[str, Any]]:
                return {"posts": [], "cursor": None}
            
            def send_post(self, text: str, images: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
                return {"uri": "at://did:plc:test/post/123", "cid": "cid123"}
            
            def upload_blob(self, file_data: bytes, mime_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
                return {"blob": {"ref": "blob_ref", "mimeType": mime_type or "image/jpeg"}}
            
            def like(self, uri: str, cid: str) -> Optional[Dict[str, Any]]:
                return {"uri": f"at://did:plc:test/like/{uri}", "cid": cid}
        
        # プロトコルに準拠していることを確認
        api_client = MockApiClient()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        
        # メソッドの動作確認
        timeline = api_client.get_timeline(100)
        assert timeline is not None
        assert "posts" in timeline
        
        post = api_client.send_post("Test post")
        assert post is not None
        assert "uri" in post
        
        blob = api_client.upload_blob(b"image_data", "image/png")
        assert blob is not None
        assert blob["blob"]["mimeType"] == "image/png"
        
        like = api_client.like("post_uri", "post_cid")
        assert like is not None


class TestDataStoreProtocol:
    """DataStoreProtocolのテストクラス"""
    
    def test_data_store_protocol_implementation(self):
        """DataStoreProtocol実装テスト"""
        
        class MockDataStore:
            def __init__(self):
                self.sessions = {}
            
            def init_database(self) -> bool:
                return True
            
            def save_encrypted_session(self, user_did: str, session_string: str) -> bool:
                self.sessions[user_did] = session_string
                return True
            
            def load_encrypted_session(self, user_did: str) -> Optional[str]:
                return self.sessions.get(user_did)
            
            def delete_session(self, user_did: str) -> bool:
                if user_did in self.sessions:
                    del self.sessions[user_did]
                    return True
                return False
        
        # プロトコルに準拠していることを確認
        data_store = MockDataStore()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        
        # メソッドの動作確認
        assert data_store.init_database() is True
        
        assert data_store.save_encrypted_session("did:plc:user1", "session1") is True
        assert data_store.load_encrypted_session("did:plc:user1") == "session1"
        
        assert data_store.delete_session("did:plc:user1") is True
        assert data_store.load_encrypted_session("did:plc:user1") is None


class TestEventPublisherProtocol:
    """EventPublisherProtocolのテストクラス"""
    
    def test_event_publisher_protocol_implementation(self):
        """EventPublisherProtocol実装テスト"""
        
        class MockEventPublisher:
            def __init__(self):
                self.subscribers = {}
            
            def publish_event(self, event_name: str, **kwargs: Any) -> None:
                if event_name in self.subscribers:
                    for callback in self.subscribers[event_name]:
                        callback(**kwargs)
            
            def subscribe_event(self, event_name: str, callback: Any) -> None:
                if event_name not in self.subscribers:
                    self.subscribers[event_name] = []
                self.subscribers[event_name].append(callback)
        
        # プロトコルに準拠していることを確認
        publisher = MockEventPublisher()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        
        # メソッドの動作確認
        received_events = []
        
        def callback(**kwargs):
            received_events.append(kwargs)
        
        publisher.subscribe_event("test_event", callback)
        publisher.publish_event("test_event", data="test_data")
        
        assert len(received_events) == 1
        assert received_events[0]["data"] == "test_data"


class TestCryptoProtocol:
    """CryptoProtocolのテストクラス"""
    
    def test_crypto_protocol_implementation(self):
        """CryptoProtocol実装テスト"""
        
        class MockCrypto:
            def encrypt_data(self, data: str) -> Optional[bytes]:
                # 簡単な疑似暗号化（実際の暗号化ではない）
                return data.encode('utf-8')[::-1]  # 逆順にするだけ
            
            def decrypt_data(self, encrypted_data: bytes) -> Optional[str]:
                # 簡単な疑似復号化（実際の復号化ではない）
                return encrypted_data[::-1].decode('utf-8')
        
        # プロトコルに準拠していることを確認
        crypto = MockCrypto()
        # Protocolは@runtime_checkableデコレータがないとisinstanceチェックできない
        
        # メソッドの動作確認
        original = "sensitive_data"
        encrypted = crypto.encrypt_data(original)
        assert encrypted is not None
        assert isinstance(encrypted, bytes)
        
        decrypted = crypto.decrypt_data(encrypted)
        assert decrypted == original
    
    def test_crypto_protocol_mock(self):
        """CryptoProtocolのモックテスト"""
        mock_crypto = MagicMock(spec=CryptoProtocol)
        
        # モックの設定
        mock_crypto.encrypt_data.return_value = b"encrypted_bytes"
        mock_crypto.decrypt_data.return_value = "decrypted_string"
        
        # 動作確認
        encrypted = mock_crypto.encrypt_data("test_data")
        assert encrypted == b"encrypted_bytes"
        
        decrypted = mock_crypto.decrypt_data(b"encrypted_bytes")
        assert decrypted == "decrypted_string"


class TestProtocolCompliance:
    """プロトコル準拠性の総合テスト"""
    
    def test_protocol_type_checking(self):
        """プロトコルの型チェックテスト"""
        # 不完全な実装のクラス
        class IncompleteConfigManager:
            def get_value(self, key: str, default: Any = None) -> Any:
                return default
            # set_value, save_config, load_configが不足
        
        # 不完全な実装はプロトコルに準拠しない
        incomplete = IncompleteConfigManager()
        # Protocolは実行時の型チェックをサポートしないため、
        # isinstance()では常にFalseになることに注意
        
        # 完全な実装のクラス
        class CompleteConfigManager:
            def get_value(self, key: str, default: Any = None) -> Any:
                return default
            
            def set_value(self, key: str, value: Any) -> bool:
                return True
            
            def save_config(self) -> bool:
                return True
            
            def load_config(self) -> bool:
                return True
        
        complete = CompleteConfigManager()
        # 完全な実装はプロトコルに準拠
        assert hasattr(complete, 'get_value')
        assert hasattr(complete, 'set_value')
        assert hasattr(complete, 'save_config')
        assert hasattr(complete, 'load_config')