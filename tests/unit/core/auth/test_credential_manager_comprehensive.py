#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
AuthCredentialManager包括的テスト (Phase 3 リファクタリング版)
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch, call
from typing import Optional, Dict, Any

from core.auth.credential_manager import AuthCredentialManager
from core.data_store import DataStore


@pytest.fixture
def mock_data_store():
    """データストアのモック"""
    mock_store = Mock(spec=DataStore)
    return mock_store


@pytest.fixture
def mock_encrypt_func():
    """暗号化関数のモック"""
    def mock_encrypt(data):
        if isinstance(data, str):
            return f"encrypted_{data}".encode('utf-8')
        elif isinstance(data, bytes):
            return b"encrypted_" + data
        return None
    return mock_encrypt


@pytest.fixture
def mock_decrypt_func():
    """復号化関数のモック"""
    def mock_decrypt(data):
        if isinstance(data, bytes):
            if data.startswith(b"encrypted_"):
                return data[10:].decode('utf-8')
        elif isinstance(data, str):
            if data.startswith("encrypted_"):
                return data[10:]
        return None
    return mock_decrypt


@pytest.fixture
def credential_manager(mock_data_store, mock_encrypt_func, mock_decrypt_func):
    """テスト用認証管理インスタンス"""
    return AuthCredentialManager(
        data_store=mock_data_store,
        encrypt_func=mock_encrypt_func,
        decrypt_func=mock_decrypt_func
    )


@pytest.mark.unit
class TestAuthCredentialManagerInstantiation:
    """AuthCredentialManagerインスタンス化テスト"""
    
    def test_default_instantiation(self):
        """デフォルトインスタンス化テスト"""
        with patch('core.auth.credential_manager.DataStore') as mock_data_store_class, \
             patch('core.auth.credential_manager.encrypt_data') as mock_encrypt, \
             patch('core.auth.credential_manager.decrypt_data') as mock_decrypt:
            
            manager = AuthCredentialManager()
            
            assert manager is not None
            assert manager.data_store is not None
            assert manager.encrypt_func is not None
            assert manager.decrypt_func is not None
            mock_data_store_class.assert_called_once()
    
    def test_dependency_injection_instantiation(self, mock_data_store, mock_encrypt_func, mock_decrypt_func):
        """依存性注入によるインスタンス化テスト"""
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            encrypt_func=mock_encrypt_func,
            decrypt_func=mock_decrypt_func
        )
        
        assert manager.data_store is mock_data_store
        assert manager.encrypt_func is mock_encrypt_func
        assert manager.decrypt_func is mock_decrypt_func
    
    def test_partial_dependency_injection(self, mock_data_store):
        """部分的依存性注入テスト"""
        with patch('core.auth.credential_manager.encrypt_data') as mock_encrypt, \
             patch('core.auth.credential_manager.decrypt_data') as mock_decrypt:
            
            manager = AuthCredentialManager(data_store=mock_data_store)
            
            assert manager.data_store is mock_data_store
            assert manager.encrypt_func is mock_encrypt
            assert manager.decrypt_func is mock_decrypt


@pytest.mark.unit
class TestAuthCredentialManagerBasicOperations:
    """AuthCredentialManager基本操作テスト"""
    
    def test_save_encrypted_session_success(self, credential_manager, mock_data_store):
        """暗号化セッション保存成功テスト"""
        test_user_did = "did:plc:test123"
        test_session_data = "session_data_content"
        
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session(test_user_did, test_session_data)
        
        assert result is True
        mock_data_store.save_session.assert_called_once_with(test_user_did, b"encrypted_session_data_content")
    
    def test_save_encrypted_session_bytes_input(self, credential_manager, mock_data_store):
        """バイト入力での暗号化セッション保存テスト"""
        test_user_did = "did:plc:test123"
        test_session_data = b"session_data_bytes"
        
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session(test_user_did, test_session_data)
        
        assert result is True
        mock_data_store.save_session.assert_called_once_with(test_user_did, b"encrypted_session_data_bytes")
    
    def test_save_encrypted_session_encryption_failure(self, credential_manager, mock_data_store):
        """暗号化失敗時のテスト"""
        test_user_did = "did:plc:test123"
        test_session_data = "session_data"
        
        # 暗号化が失敗する（None を返す）モックに変更
        credential_manager.encrypt_func = Mock(return_value=None)
        
        result = credential_manager.save_encrypted_session(test_user_did, test_session_data)
        
        assert result is False
        mock_data_store.save_session.assert_not_called()
    
    def test_save_encrypted_session_datastore_failure(self, credential_manager, mock_data_store):
        """データストア保存失敗テスト"""
        test_user_did = "did:plc:test123"
        test_session_data = "session_data"
        
        mock_data_store.save_session.return_value = False
        
        result = credential_manager.save_encrypted_session(test_user_did, test_session_data)
        
        assert result is False
    
    def test_save_encrypted_session_exception_handling(self, credential_manager, mock_data_store):
        """保存時例外処理テスト"""
        test_user_did = "did:plc:test123"
        test_session_data = "session_data"
        
        mock_data_store.save_session.side_effect = Exception("Database error")
        
        result = credential_manager.save_encrypted_session(test_user_did, test_session_data)
        
        assert result is False
    
    def test_load_encrypted_session_success(self, credential_manager, mock_data_store):
        """暗号化セッション読み込み成功テスト"""
        test_user_did = "did:plc:test123"
        test_encrypted_data = b"encrypted_session_data"
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        
        session_data, user_did = credential_manager.load_encrypted_session()
        
        assert session_data == "session_data"
        assert user_did == test_user_did
    
    def test_load_encrypted_session_no_data(self, credential_manager, mock_data_store):
        """セッションデータなしテスト"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        session_data, user_did = credential_manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None
    
    def test_load_encrypted_session_decryption_failure(self, credential_manager, mock_data_store):
        """復号化失敗テスト"""
        test_user_did = "did:plc:test123"
        test_encrypted_data = b"invalid_encrypted_data"
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        
        session_data, user_did = credential_manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None
    
    def test_load_encrypted_session_exception_handling(self, credential_manager, mock_data_store):
        """読み込み時例外処理テスト"""
        mock_data_store.get_latest_session.side_effect = Exception("Database error")
        
        session_data, user_did = credential_manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None
    
    def test_delete_session_success(self, credential_manager, mock_data_store):
        """セッション削除成功テスト"""
        test_user_did = "did:plc:test123"
        
        mock_data_store.delete_session.return_value = True
        
        result = credential_manager.delete_session(test_user_did)
        
        assert result is True
        mock_data_store.delete_session.assert_called_once_with(test_user_did)
    
    def test_delete_session_failure(self, credential_manager, mock_data_store):
        """セッション削除失敗テスト"""
        test_user_did = "did:plc:test123"
        
        mock_data_store.delete_session.return_value = False
        
        result = credential_manager.delete_session(test_user_did)
        
        assert result is False
    
    def test_delete_session_exception_handling(self, credential_manager, mock_data_store):
        """削除時例外処理テスト"""
        test_user_did = "did:plc:test123"
        
        mock_data_store.delete_session.side_effect = Exception("Database error")
        
        result = credential_manager.delete_session(test_user_did)
        
        assert result is False


@pytest.mark.unit
class TestAuthCredentialManagerPhase3Features:
    """AuthCredentialManagerのPhase3機能テスト"""
    
    def test_save_credentials_success(self, credential_manager, mock_data_store):
        """認証情報保存成功テスト"""
        test_username = "test_user"
        test_password = "test_password"
        test_session_data = {"access_token": "token123", "refresh_token": "refresh456"}
        
        mock_data_store.save_session.return_value = True
        
        with patch('json.dumps') as mock_json_dumps:
            mock_json_dumps.return_value = '{"username": "test_user", "password": "test_password"}'
            
            result = credential_manager.save_credentials(test_username, test_password, test_session_data)
        
        assert result is True
        
        # JSON形式での保存が呼び出されたことを確認
        mock_json_dumps.assert_called_once()
        call_args = mock_json_dumps.call_args[0][0]
        assert call_args['username'] == test_username
        assert call_args['password'] == test_password
        assert call_args['session_data'] == test_session_data
        assert 'created_at' in call_args
    
    def test_save_credentials_no_session_data(self, credential_manager, mock_data_store):
        """セッションデータなしでの認証情報保存テスト"""
        test_username = "test_user"
        test_password = "test_password"
        
        mock_data_store.save_session.return_value = True
        
        with patch('json.dumps') as mock_json_dumps:
            mock_json_dumps.return_value = '{"username": "test_user"}'
            
            result = credential_manager.save_credentials(test_username, test_password)
        
        assert result is True
        
        call_args = mock_json_dumps.call_args[0][0]
        assert call_args['session_data'] == {}
    
    def test_save_credentials_json_error(self, credential_manager, mock_data_store):
        """JSON変換エラーテスト"""
        test_username = "test_user"
        test_password = "test_password"
        
        with patch('json.dumps') as mock_json_dumps:
            mock_json_dumps.side_effect = ValueError("JSON encoding failed")
            
            result = credential_manager.save_credentials(test_username, test_password)
        
        assert result is False
    
    def test_get_stored_credentials_success(self, credential_manager, mock_data_store):
        """保存された認証情報取得成功テスト"""
        test_user_did = "did:plc:test123"
        test_credentials_dict = {
            "username": "test_user",
            "password": "test_password",
            "session_data": {"token": "abc123"},
            "created_at": "2024-01-01T12:00:00"
        }
        test_encrypted_data = f"encrypted_{json.dumps(test_credentials_dict)}".encode('utf-8')
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        
        result = credential_manager.get_stored_credentials()
        
        assert result is not None
        assert result['username'] == "test_user"
        assert result['password'] == "test_password" 
        assert result['session_data']['token'] == "abc123"
        assert result['user_did'] == test_user_did
    
    def test_get_stored_credentials_bytes_session_data(self, credential_manager, mock_data_store):
        """バイト形式セッションデータの認証情報取得テスト"""
        test_user_did = "did:plc:test123"
        test_credentials_dict = {
            "username": "test_user",
            "password": "test_password"
        }
        test_encrypted_data = f"encrypted_{json.dumps(test_credentials_dict)}".encode('utf-8')
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        
        # 復号化関数がbytesを返すように変更
        def mock_decrypt_bytes(data):
            if isinstance(data, bytes) and data.startswith(b"encrypted_"):
                return data[10:]  # bytesのまま返す
            return None
        
        credential_manager.decrypt_func = mock_decrypt_bytes
        
        result = credential_manager.get_stored_credentials()
        
        assert result is not None
        assert result['username'] == "test_user"
        assert result['user_did'] == test_user_did
    
    def test_get_stored_credentials_no_data(self, credential_manager, mock_data_store):
        """認証情報データなしテスト"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None
    
    def test_get_stored_credentials_json_decode_error(self, credential_manager, mock_data_store):
        """JSON復号化エラーテスト"""
        test_user_did = "did:plc:test123"
        test_encrypted_data = b"encrypted_invalid_json"
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None
    
    def test_get_stored_credentials_exception_handling(self, credential_manager, mock_data_store):
        """認証情報取得例外処理テスト"""
        mock_data_store.get_latest_session.side_effect = Exception("Database error")
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None
    
    def test_clear_credentials_success(self, credential_manager, mock_data_store):
        """認証情報クリア成功テスト"""
        test_user_did = "did:plc:test123"
        test_encrypted_data = b"encrypted_session_data"
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        mock_data_store.delete_session.return_value = True
        
        result = credential_manager.clear_credentials()
        
        assert result is True
        mock_data_store.delete_session.assert_called_once_with(test_user_did)
    
    def test_clear_credentials_no_existing_data(self, credential_manager, mock_data_store):
        """既存データなしでの認証情報クリアテスト"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        result = credential_manager.clear_credentials()
        
        assert result is True
        mock_data_store.delete_session.assert_not_called()
    
    def test_clear_credentials_delete_failure(self, credential_manager, mock_data_store):
        """認証情報削除失敗テスト"""
        test_user_did = "did:plc:test123"
        test_encrypted_data = b"encrypted_session_data"
        
        mock_data_store.get_latest_session.return_value = (test_user_did, test_encrypted_data)
        mock_data_store.delete_session.return_value = False
        
        result = credential_manager.clear_credentials()
        
        assert result is False
    
    def test_clear_credentials_load_session_exception_handling(self, credential_manager):
        """認証情報クリア（load_encrypted_session例外）処理テスト"""
        # load_encrypted_sessionメソッド自体が例外処理を行い(None, None)を返すため、
        # 実際のclear_credentialsレベルで例外を発生させるためには、
        # load_encrypted_sessionをパッチしてExceptionを発生させる
        with patch.object(credential_manager, 'load_encrypted_session') as mock_load:
            mock_load.side_effect = Exception("Session loading error")
            
            result = credential_manager.clear_credentials()
            
            assert result is False


@pytest.mark.unit
class TestAuthCredentialManagerEncryptionErrorHandling:
    """AuthCredentialManager暗号化エラーハンドリングテスト"""
    
    def test_encryption_function_failure(self, mock_data_store, mock_decrypt_func):
        """暗号化関数失敗テスト"""
        def failing_encrypt_func(data):
            raise Exception("Encryption failed")
        
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            encrypt_func=failing_encrypt_func,
            decrypt_func=mock_decrypt_func
        )
        
        result = manager.save_encrypted_session("did:plc:test", "test_data")
        
        assert result is False
        mock_data_store.save_session.assert_not_called()
    
    def test_decryption_function_failure(self, mock_data_store, mock_encrypt_func):
        """復号化関数失敗テスト"""
        def failing_decrypt_func(data):
            raise Exception("Decryption failed")
        
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            encrypt_func=mock_encrypt_func,
            decrypt_func=failing_decrypt_func
        )
        
        mock_data_store.get_latest_session.return_value = ("did:plc:test", b"encrypted_data")
        
        session_data, user_did = manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None
    
    def test_encryption_returns_none(self, mock_data_store, mock_decrypt_func):
        """暗号化がNoneを返すテスト"""
        def none_encrypt_func(data):
            return None
        
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            encrypt_func=none_encrypt_func,
            decrypt_func=mock_decrypt_func
        )
        
        result = manager.save_encrypted_session("did:plc:test", "test_data")
        
        assert result is False
    
    def test_decryption_returns_none(self, mock_data_store, mock_encrypt_func):
        """復号化がNoneを返すテスト"""
        def none_decrypt_func(data):
            return None
        
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            encrypt_func=mock_encrypt_func,
            decrypt_func=none_decrypt_func
        )
        
        mock_data_store.get_latest_session.return_value = ("did:plc:test", b"encrypted_data")
        
        session_data, user_did = manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None
    
    def test_malformed_encrypted_data_handling(self, mock_data_store):
        """不正な暗号化データの処理テスト"""
        def strict_decrypt_func(data):
            if not isinstance(data, bytes) or not data.startswith(b"encrypted_"):
                raise ValueError("Invalid encrypted data format")
            return data[10:].decode('utf-8')
        
        manager = AuthCredentialManager(
            data_store=mock_data_store,
            decrypt_func=strict_decrypt_func
        )
        
        # 不正なフォーマットのデータ
        mock_data_store.get_latest_session.return_value = ("did:plc:test", b"malformed_data")
        
        session_data, user_did = manager.load_encrypted_session()
        
        assert session_data is None
        assert user_did is None


@pytest.mark.unit
class TestAuthCredentialManagerDataTypeHandling:
    """AuthCredentialManagerデータタイプ処理テスト"""
    
    def test_string_session_data_handling(self, credential_manager, mock_data_store):
        """文字列セッションデータ処理テスト"""
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session("did:plc:test", "string_data")
        
        assert result is True
        mock_data_store.save_session.assert_called_once_with("did:plc:test", b"encrypted_string_data")
    
    def test_bytes_session_data_handling(self, credential_manager, mock_data_store):
        """バイトセッションデータ処理テスト"""
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session("did:plc:test", b"bytes_data")
        
        assert result is True
        mock_data_store.save_session.assert_called_once_with("did:plc:test", b"encrypted_bytes_data")
    
    def test_empty_session_data_handling(self, credential_manager, mock_data_store):
        """空セッションデータ処理テスト"""
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session("did:plc:test", "")
        
        assert result is True
        mock_data_store.save_session.assert_called_once_with("did:plc:test", b"encrypted_")
    
    def test_large_session_data_handling(self, credential_manager, mock_data_store):
        """大容量セッションデータ処理テスト"""
        large_data = "x" * 10000  # 10KB のデータ
        mock_data_store.save_session.return_value = True
        
        result = credential_manager.save_encrypted_session("did:plc:test", large_data)
        
        assert result is True
        expected_encrypted = f"encrypted_{large_data}".encode('utf-8')
        mock_data_store.save_session.assert_called_once_with("did:plc:test", expected_encrypted)


@pytest.mark.unit  
class TestAuthCredentialManagerIntegration:
    """AuthCredentialManager統合テスト"""
    
    def test_complete_credentials_lifecycle(self, credential_manager, mock_data_store):
        """完全な認証情報ライフサイクルテスト"""
        test_username = "integration_user"
        test_password = "integration_password"
        test_session_data = {"token": "integration_token"}
        
        # 保存
        mock_data_store.save_session.return_value = True
        save_result = credential_manager.save_credentials(test_username, test_password, test_session_data)
        assert save_result is True
        
        # 保存されたデータを取得用にセットアップ
        saved_call = mock_data_store.save_session.call_args[0]
        saved_did = saved_call[0]
        saved_encrypted_data = saved_call[1]
        
        mock_data_store.get_latest_session.return_value = (saved_did, saved_encrypted_data)
        
        # 取得
        retrieved_credentials = credential_manager.get_stored_credentials()
        assert retrieved_credentials is not None
        assert retrieved_credentials['username'] == test_username
        assert retrieved_credentials['password'] == test_password
        assert retrieved_credentials['session_data']['token'] == "integration_token"
        
        # クリア
        mock_data_store.delete_session.return_value = True
        clear_result = credential_manager.clear_credentials()
        assert clear_result is True
    
    def test_multiple_save_load_cycles(self, credential_manager, mock_data_store):
        """複数回保存読み込みサイクルテスト"""
        test_sessions = [
            ("user1", "pass1", {"token": "token1"}),
            ("user2", "pass2", {"token": "token2"}),
            ("user3", "pass3", {"token": "token3"})
        ]
        
        mock_data_store.save_session.return_value = True
        
        for username, password, session_data in test_sessions:
            result = credential_manager.save_credentials(username, password, session_data)
            assert result is True
        
        # 最後に保存されたデータが取得されることを検証
        # (最新セッション取得動作をシミュレート)
        last_call = mock_data_store.save_session.call_args_list[-1][0]
        mock_data_store.get_latest_session.return_value = (last_call[0], last_call[1])
        
        retrieved = credential_manager.get_stored_credentials()
        assert retrieved['username'] == "user3"
        assert retrieved['session_data']['token'] == "token3"
    
    def test_concurrent_operations_simulation(self, credential_manager, mock_data_store):
        """同時操作シミュレーションテスト"""
        # 保存中に読み込みが発生するシナリオ
        mock_data_store.save_session.return_value = True
        mock_data_store.get_latest_session.return_value = (None, None)
        
        # 保存処理
        save_result = credential_manager.save_credentials("user", "pass")
        assert save_result is True
        
        # 同時に読み込み処理（まだデータがない状態）
        retrieved = credential_manager.get_stored_credentials()
        assert retrieved is None
        
        # 保存処理完了後の読み込み
        saved_call = mock_data_store.save_session.call_args[0]
        mock_data_store.get_latest_session.return_value = (saved_call[0], saved_call[1])
        
        retrieved = credential_manager.get_stored_credentials()
        assert retrieved is not None
        assert retrieved['username'] == "user"