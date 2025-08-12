#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
カスタム例外クラスの単体テスト (pytest版)
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.exceptions import (
    SSkyError,
    AuthenticationError,
    ValidationError,
    NetworkError,
    BlueskyAPIError,
    SessionError,
    PostError,
    DataStoreError,
    ConfigurationError
)


class TestSSkyError:
    """SSkyError基底例外クラスのテスト"""
    
    def test_ssky_error_creation(self):
        """SSkyError作成テスト"""
        error = SSkyError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_ssky_error_inheritance(self):
        """SSkyError継承関係テスト"""
        error = SSkyError()
        assert isinstance(error, Exception)
        assert isinstance(error, SSkyError)


class TestAuthenticationError:
    """AuthenticationError例外クラスのテスト"""
    
    def test_authentication_error_creation(self):
        """AuthenticationError作成テスト"""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, SSkyError)
        assert isinstance(error, AuthenticationError)
    
    def test_authentication_error_inheritance(self):
        """AuthenticationError継承関係テスト"""
        error = AuthenticationError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, AuthenticationError)


class TestValidationError:
    """ValidationError例外クラスのテスト"""
    
    def test_validation_error_creation(self):
        """ValidationError作成テスト"""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, SSkyError)
        assert isinstance(error, ValidationError)
    
    def test_validation_error_inheritance(self):
        """ValidationError継承関係テスト"""
        error = ValidationError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, ValidationError)


class TestNetworkError:
    """NetworkError例外クラスのテスト"""
    
    def test_network_error_creation(self):
        """NetworkError作成テスト"""
        error = NetworkError("Connection timeout")
        assert str(error) == "Connection timeout"
        assert isinstance(error, SSkyError)
        assert isinstance(error, NetworkError)
    
    def test_network_error_inheritance(self):
        """NetworkError継承関係テスト"""
        error = NetworkError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, NetworkError)


class TestBlueskyAPIError:
    """BlueskyAPIError例外クラスのテスト"""
    
    def test_bluesky_api_error_creation_basic(self):
        """BlueskyAPIError基本作成テスト"""
        error = BlueskyAPIError("API request failed")
        assert str(error) == "API request failed"
        assert error.status_code is None
        assert error.response_data is None
        assert isinstance(error, SSkyError)
        assert isinstance(error, BlueskyAPIError)
    
    def test_bluesky_api_error_creation_with_status_code(self):
        """ステータスコード付きBlueskyAPIError作成テスト"""
        error = BlueskyAPIError("Not found", status_code=404)
        assert str(error) == "Not found"
        assert error.status_code == 404
        assert error.response_data is None
    
    def test_bluesky_api_error_creation_with_response_data(self):
        """レスポンスデータ付きBlueskyAPIError作成テスト"""
        response_data = {"error": "Invalid token", "code": "AUTH_001"}
        error = BlueskyAPIError("Authentication error", response_data=response_data)
        assert str(error) == "Authentication error"
        assert error.status_code is None
        assert error.response_data == response_data
    
    def test_bluesky_api_error_creation_full(self):
        """完全パラメータ付きBlueskyAPIError作成テスト"""
        response_data = {"error": "Rate limited", "retry_after": 60}
        error = BlueskyAPIError(
            "Rate limit exceeded",
            status_code=429,
            response_data=response_data
        )
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.response_data == response_data
        assert error.response_data["retry_after"] == 60
    
    def test_bluesky_api_error_inheritance(self):
        """BlueskyAPIError継承関係テスト"""
        error = BlueskyAPIError("Test")
        assert isinstance(error, SSkyError)
        assert isinstance(error, BlueskyAPIError)


class TestSessionError:
    """SessionError例外クラスのテスト"""
    
    def test_session_error_creation(self):
        """SessionError作成テスト"""
        error = SessionError("Session expired")
        assert str(error) == "Session expired"
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, SessionError)
        assert isinstance(error, SSkyError)
    
    def test_session_error_inheritance(self):
        """SessionError継承関係テスト"""
        error = SessionError()
        # SessionErrorはAuthenticationErrorを継承
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, SessionError)
        assert isinstance(error, SSkyError)


class TestPostError:
    """PostError例外クラスのテスト"""
    
    def test_post_error_creation(self):
        """PostError作成テスト"""
        error = PostError("Post too long")
        assert str(error) == "Post too long"
        assert isinstance(error, SSkyError)
        assert isinstance(error, PostError)
    
    def test_post_error_inheritance(self):
        """PostError継承関係テスト"""
        error = PostError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, PostError)


class TestDataStoreError:
    """DataStoreError例外クラスのテスト"""
    
    def test_data_store_error_creation(self):
        """DataStoreError作成テスト"""
        error = DataStoreError("Database connection failed")
        assert str(error) == "Database connection failed"
        assert isinstance(error, SSkyError)
        assert isinstance(error, DataStoreError)
    
    def test_data_store_error_inheritance(self):
        """DataStoreError継承関係テスト"""
        error = DataStoreError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, DataStoreError)


class TestConfigurationError:
    """ConfigurationError例外クラスのテスト"""
    
    def test_configuration_error_creation(self):
        """ConfigurationError作成テスト"""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, SSkyError)
        assert isinstance(error, ConfigurationError)
    
    def test_configuration_error_inheritance(self):
        """ConfigurationError継承関係テスト"""
        error = ConfigurationError()
        assert isinstance(error, SSkyError)
        assert isinstance(error, ConfigurationError)


class TestExceptionUsage:
    """例外の実際の使用シナリオテスト"""
    
    def test_raising_and_catching_ssky_error(self):
        """SSkyError例外の発生とキャッチテスト"""
        def raise_ssky_error():
            raise SSkyError("General application error")
        
        with pytest.raises(SSkyError) as exc_info:
            raise_ssky_error()
        
        assert str(exc_info.value) == "General application error"
    
    def test_raising_and_catching_specific_errors(self):
        """特定の例外の発生とキャッチテスト"""
        def raise_auth_error():
            raise AuthenticationError("Login failed")
        
        # 特定の例外をキャッチ
        with pytest.raises(AuthenticationError) as exc_info:
            raise_auth_error()
        
        assert str(exc_info.value) == "Login failed"
        
        # 基底クラスでもキャッチ可能
        with pytest.raises(SSkyError):
            raise_auth_error()
    
    def test_bluesky_api_error_with_context(self):
        """コンテキスト付きBlueskyAPIErrorテスト"""
        def api_call():
            response_data = {
                "error": "Rate limited",
                "message": "Too many requests",
                "retry_after": 30
            }
            raise BlueskyAPIError(
                "API rate limit exceeded",
                status_code=429,
                response_data=response_data
            )
        
        with pytest.raises(BlueskyAPIError) as exc_info:
            api_call()
        
        error = exc_info.value
        assert str(error) == "API rate limit exceeded"
        assert error.status_code == 429
        assert error.response_data["retry_after"] == 30
    
    def test_exception_hierarchy(self):
        """例外階層の動作テスト"""
        # SessionErrorはAuthenticationErrorとSSkyErrorの両方でキャッチ可能
        session_error = SessionError("Session invalid")
        
        # SessionErrorとして
        assert isinstance(session_error, SessionError)
        
        # AuthenticationErrorとして
        assert isinstance(session_error, AuthenticationError)
        
        # SSkyErrorとして
        assert isinstance(session_error, SSkyError)
        
        # Exceptionとして
        assert isinstance(session_error, Exception)