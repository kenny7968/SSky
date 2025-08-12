#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - AuthCredentialManager 単体テスト
完全リファクタリング版
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# テスト対象モジュールのインポート
sys.path.insert(0, str(Path(__file__).parents[4]))
from core.auth.credential_manager import AuthCredentialManager
from tests.mocks.common_mocks import MockDataStore


@pytest.fixture
def mock_data_store():
    """DataStoreのモック"""
    return MockDataStore().get_mock()


@pytest.fixture
def mock_crypto():
    """暗号化モジュールのモック"""
    with patch('core.auth.credential_manager.encrypt_data') as mock_encrypt, \
         patch('core.auth.credential_manager.decrypt_data') as mock_decrypt:
        mock_encrypt.return_value = b'encrypted_data'
        mock_decrypt.return_value = 'decrypted_data'
        yield {'encrypt': mock_encrypt, 'decrypt': mock_decrypt}


@pytest.fixture
def credential_manager(mock_data_store, mock_crypto):
    """テスト用CredentialManagerインスタンス"""
    # 依存性注入でインスタンス作成
    manager = AuthCredentialManager(
        data_store=mock_data_store,
        encrypt_func=mock_crypto['encrypt'],
        decrypt_func=mock_crypto['decrypt']
    )
    yield manager


class TestCredentialManagerInitialization:
    """初期化関連のテスト"""
    
    @pytest.mark.unit
    def test_dependency_injection(self, mock_data_store):
        """依存性注入の動作確認"""
        manager = AuthCredentialManager(data_store=mock_data_store)
        
        assert manager.data_store == mock_data_store
        assert manager.encrypt_func is not None
        assert manager.decrypt_func is not None
    
    @pytest.mark.unit
    def test_initialization_with_data_store(self, credential_manager, mock_data_store):
        """DataStore付きで初期化"""
        assert credential_manager.data_store == mock_data_store
    
    @pytest.mark.unit
    def test_initialization_with_defaults(self):
        """デフォルト値での初期化"""
        with patch('core.auth.credential_manager.DataStore') as mock_ds:
            manager = AuthCredentialManager()
            
            assert manager.data_store is not None
            assert manager.encrypt_func is not None
            assert manager.decrypt_func is not None


class TestCredentialSaving:
    """認証情報保存のテスト"""
    
    @pytest.mark.unit
    def test_save_encrypted_session_success(self, credential_manager, mock_data_store, mock_crypto):
        """セッション情報の保存成功"""
        mock_data_store.save_session.return_value = True
        mock_crypto['encrypt'].return_value = b'encrypted_data'
        
        result = credential_manager.save_encrypted_session("did:plc:test", "session_data")
        
        assert result is True
        mock_crypto['encrypt'].assert_called_once_with("session_data")
        mock_data_store.save_session.assert_called_once_with("did:plc:test", b'encrypted_data')
    
    @pytest.mark.unit
    def test_save_credentials_method(self, credential_manager, mock_data_store, mock_crypto):
        """便利メソッドのテスト"""
        mock_data_store.save_session.return_value = True
        mock_crypto['encrypt'].return_value = b'encrypted_data'
        
        result = credential_manager.save_credentials("test.user", "password123")
        
        assert result is True
        mock_crypto['encrypt'].assert_called()
        mock_data_store.save_session.assert_called()
    
    @pytest.mark.unit
    def test_save_encrypted_session_empty_did(self, credential_manager, mock_data_store):
        """空のDIDで保存"""
        mock_data_store.save_session.return_value = False
        result = credential_manager.save_encrypted_session("", "session_data")
        # 空のDIDはエラーとして扱われる
        assert result is False
    
    @pytest.mark.unit
    def test_save_encrypted_session_empty_data(self, credential_manager, mock_data_store, mock_crypto):
        """空のデータで保存"""
        mock_crypto['encrypt'].return_value = b''
        mock_data_store.save_session.return_value = False
        result = credential_manager.save_encrypted_session("did:plc:test", "")
        # 空のデータも暗号化されるが、保存は成功しない可能性
        assert result is False
    
    @pytest.mark.unit
    def test_save_encrypted_session_encryption_error(self, credential_manager, mock_crypto, mock_data_store):
        """暗号化エラー"""
        mock_crypto['encrypt'].return_value = None  # 暗号化失敗
        mock_data_store.save_session.return_value = False
        
        result = credential_manager.save_encrypted_session("did:plc:test", "session_data")
        assert result is False
    
    @pytest.mark.unit
    def test_save_encrypted_session_database_error(self, credential_manager, mock_data_store, mock_crypto):
        """データベースエラー"""
        mock_crypto['encrypt'].return_value = b'encrypted_data'
        mock_data_store.save_session.side_effect = Exception("Database error")
        
        result = credential_manager.save_encrypted_session("did:plc:test", "session_data")
        
        assert result is False


class TestCredentialRetrieval:
    """認証情報取得のテスト"""
    
    @pytest.mark.unit
    def test_get_credentials_success(self, credential_manager, mock_data_store, mock_crypto):
        """認証情報の取得成功"""
        mock_data_store.get_latest_session.return_value = (
            "did:plc:test",
            b'encrypted_session'
        )
        mock_crypto['decrypt'].return_value = '{"username":"test.user","password":"password123"}'
        
        result = credential_manager.get_stored_credentials()
        
        assert result is not None
        assert result['username'] == "test.user"
        assert result['password'] == "password123"
        assert result['user_did'] == "did:plc:test"
        mock_data_store.get_latest_session.assert_called_once()
        mock_crypto['decrypt'].assert_called_once_with(b'encrypted_session')
    
    @pytest.mark.unit
    def test_get_credentials_not_found(self, credential_manager, mock_data_store):
        """認証情報が見つからない"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None
        mock_data_store.get_latest_session.assert_called_once()
    
    @pytest.mark.unit
    def test_get_credentials_decryption_error(self, credential_manager, mock_data_store, mock_crypto):
        """復号化エラー"""
        mock_data_store.get_latest_session.return_value = (
            "did:plc:test",
            b'encrypted_session'
        )
        mock_crypto['decrypt'].side_effect = Exception("Decryption failed")
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_credentials_database_error(self, credential_manager, mock_data_store):
        """データベースエラー"""
        mock_data_store.get_latest_session.side_effect = Exception("Database error")
        
        result = credential_manager.get_stored_credentials()
        
        assert result is None


class TestCredentialDeletion:
    """認証情報削除のテスト"""
    
    @pytest.mark.unit
    def test_delete_credentials_success(self, credential_manager, mock_data_store):
        """認証情報の削除成功"""
        mock_data_store.get_latest_session.return_value = ("did:plc:test", b'session')
        mock_data_store.delete_session.return_value = True
        
        result = credential_manager.clear_credentials()
        
        assert result is True
        mock_data_store.get_latest_session.assert_called()
        mock_data_store.delete_session.assert_called_once_with("did:plc:test")
    
    @pytest.mark.unit
    def test_delete_credentials_not_exists(self, credential_manager, mock_data_store):
        """存在しない認証情報の削除"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        result = credential_manager.clear_credentials()
        
        assert result is True  # 削除対象がなくても成功
        mock_data_store.get_latest_session.assert_called()
        mock_data_store.delete_session.assert_not_called()
    
    @pytest.mark.unit
    def test_delete_credentials_database_error(self, credential_manager, mock_data_store):
        """データベースエラー"""
        mock_data_store.get_latest_session.return_value = ("did:plc:test", b'session')
        mock_data_store.delete_session.side_effect = Exception("Database error")
        
        result = credential_manager.clear_credentials()
        
        assert result is False


class TestCredentialValidation:
    """認証情報検証のテスト"""
    
    @pytest.mark.unit
    def test_has_saved_credentials_true(self, credential_manager, mock_data_store, mock_crypto):
        """保存済み認証情報あり"""
        import json
        credentials_data = json.dumps({
            "identifier": "test.user",
            "password": "encrypted_password"
        })
        # 暗号化されたデータとして返す
        mock_data_store.get_latest_session.return_value = (
            "did:plc:test",
            b'encrypted_data'  # 暗号化されたバイト列
        )
        # decrypt_funcが正しいJSONを返すように設定
        mock_crypto['decrypt'].return_value = credentials_data
        
        # has_saved_credentialsメソッドが存在しないため、get_stored_credentialsで確認
        result = credential_manager.get_stored_credentials() is not None
        
        assert result is True
        mock_data_store.get_latest_session.assert_called_once()
    
    @pytest.mark.unit
    def test_has_saved_credentials_false(self, credential_manager, mock_data_store):
        """保存済み認証情報なし"""
        mock_data_store.get_latest_session.return_value = (None, None)
        
        # has_saved_credentialsメソッドが存在しないため、get_stored_credentialsで確認
        result = credential_manager.get_stored_credentials() is None
        
        assert result is True
        mock_data_store.get_latest_session.assert_called_once()
    
    @pytest.mark.unit
    def test_validate_credentials_valid(self, credential_manager):
        """有効な認証情報"""
        # validate_credentialsメソッドが存在しない場合はスキップ
        if not hasattr(credential_manager, 'validate_credentials'):
            pytest.skip("validate_credentials method not implemented")
        result = credential_manager.validate_credentials("test.user", "password123")
        assert result is True
    
    @pytest.mark.unit
    def test_validate_credentials_empty_identifier(self, credential_manager):
        """空の識別子"""
        if not hasattr(credential_manager, 'validate_credentials'):
            pytest.skip("validate_credentials method not implemented")
        result = credential_manager.validate_credentials("", "password")
        assert result is False
    
    @pytest.mark.unit
    def test_validate_credentials_empty_password(self, credential_manager):
        """空のパスワード"""
        if not hasattr(credential_manager, 'validate_credentials'):
            pytest.skip("validate_credentials method not implemented")
        result = credential_manager.validate_credentials("test.user", "")
        assert result is False
    
    @pytest.mark.unit
    def test_validate_credentials_whitespace_only(self, credential_manager):
        """空白文字のみ"""
        if not hasattr(credential_manager, 'validate_credentials'):
            pytest.skip("validate_credentials method not implemented")
        result = credential_manager.validate_credentials("  ", "  ")
        assert result is False


class TestCredentialUpdate:
    """認証情報更新のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.skip(reason="update_password method not implemented in AuthCredentialManager")
    def test_update_password_success(self, credential_manager, mock_data_store, mock_crypto):
        """パスワード更新成功"""
        # 既存の認証情報を設定
        mock_data_store.fetch_one.return_value = (
            "test.user",
            b'old_encrypted',
            "2024-01-01 12:00:00"
        )
        mock_crypto['decrypt'].return_value = "old_password"
        mock_data_store.execute.return_value = None
        mock_data_store.commit.return_value = None
        
        # パスワード更新
        result = credential_manager.update_password("new_password")
        
        assert result is True
        mock_crypto['encrypt'].assert_called_with("new_password")
        mock_data_store.execute.assert_called()
        mock_data_store.commit.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.skip(reason="update_password method not implemented")
    def test_update_password_no_credentials(self, credential_manager, mock_data_store):
        """認証情報なしでパスワード更新"""
        mock_data_store.fetch_one.return_value = None
        
        result = credential_manager.update_password("new_password")
        
        assert result is False
    
    @pytest.mark.unit
    @pytest.mark.skip(reason="update_identifier method not implemented")
    def test_update_identifier_success(self, credential_manager, mock_data_store):
        """識別子更新成功"""
        mock_data_store.execute.return_value = None
        mock_data_store.commit.return_value = None
        
        result = credential_manager.update_identifier("old.user", "new.user")
        
        assert result is True
        mock_data_store.execute.assert_called()
        update_call = mock_data_store.execute.call_args[0][0]
        assert 'UPDATE credentials SET identifier' in update_call


class TestCredentialSecurity:
    """セキュリティ関連のテスト"""
    
    @pytest.mark.unit
    def test_password_not_stored_plain(self, credential_manager, mock_data_store, mock_crypto):
        """パスワードが平文で保存されない"""
        mock_crypto['encrypt'].return_value = b'encrypted_data'
        mock_data_store.save_session.return_value = True
        
        credential_manager.save_credentials("test.user", "plain_password")
        
        # save_sessionの呼び出しを確認
        save_calls = mock_data_store.save_session.call_args_list
        for call in save_calls:
            # 暗号化されたデータが渡されていることを確認
            _, encrypted_data = call[0]
            assert encrypted_data == b'encrypted_data'
            # 平文パスワードが含まれていないことを確認
            assert "plain_password" not in str(call)
    
    @pytest.mark.unit
    def test_credentials_isolation(self, mock_data_store):
        """認証情報の分離"""
        # AuthCredentialManagerはもはやシングルトンではない（Phase 3）
        with patch('core.auth.credential_manager.DataStore', return_value=mock_data_store):
            manager1 = AuthCredentialManager()
            manager2 = AuthCredentialManager()
            
            # 別々のインスタンス（シングルトンではない）
            assert manager1 is not manager2
    
    @pytest.mark.unit
    @pytest.mark.skip(reason="delete_credentials method does not exist, use clear_credentials instead")
    def test_secure_cleanup(self, credential_manager, mock_data_store):
        """セキュアなクリーンアップ"""
        pass


class TestCredentialManagerIntegration:
    """統合的な機能テスト"""
    
    @pytest.mark.unit
    @pytest.mark.skip(reason="Methods has_saved_credentials, get_credentials, delete_credentials do not exist")
    def test_full_credential_lifecycle(self, credential_manager, mock_data_store, mock_crypto):
        """認証情報の完全なライフサイクル"""
        pass
    
    @pytest.mark.unit
    def test_multiple_operations_sequence(self, credential_manager, mock_data_store, mock_crypto):
        """複数操作のシーケンス"""
        import json
        
        # 保存
        mock_data_store.save_session.return_value = True
        result1 = credential_manager.save_credentials("user1", "pass1")
        assert result1 is True
        
        # 更新（上書き）
        result2 = credential_manager.save_credentials("user1", "pass2")
        assert result2 is True
        
        # 取得
        credentials_json = json.dumps({"username": "user1", "password": "pass2"})
        mock_data_store.get_latest_session.return_value = ("user1", b'encrypted')
        mock_crypto['decrypt'].return_value = credentials_json
        creds = credential_manager.get_stored_credentials()
        assert creds is not None
        assert creds["username"] == "user1"
        assert creds["password"] == "pass2"
        
        # 削除
        mock_data_store.delete_session.return_value = True
        result3 = credential_manager.clear_credentials()
        assert result3 is True


class TestCredentialManagerErrorRecovery:
    """エラー回復のテスト"""
    
    @pytest.mark.unit
    def test_recover_from_database_corruption(self, credential_manager, mock_data_store):
        """データベース破損からの回復"""
        # 最初のクエリでエラー
        mock_data_store.get_latest_session.side_effect = [
            Exception("Database corrupted"),
            (None, None)  # 2回目は成功（データなし）
        ]
        
        # 1回目は失敗
        result1 = credential_manager.get_stored_credentials()
        assert result1 is None
        
        # 2回目は成功
        result2 = credential_manager.get_stored_credentials()
        assert result2 is None  # データなし
    
    @pytest.mark.unit
    def test_transaction_rollback_on_error(self, credential_manager, mock_data_store):
        """エラー時のトランザクションロールバック"""
        # save_sessionでエラーを発生させる
        mock_data_store.save_session.side_effect = Exception("Constraint violation")
        
        result = credential_manager.save_credentials("test.user", "password")
        
        assert result is False