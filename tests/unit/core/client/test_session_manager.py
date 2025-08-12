#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
セッションマネージャーの単体テスト (pytest版)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import logging
from atproto import SessionEvent, Session

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from core.client.session_manager import BlueskySessionManager


@pytest.fixture
def mock_api_client():
    """APIクライアントのモックフィクスチャ"""
    mock_client = MagicMock()
    mock_client.client = MagicMock()
    mock_client.client.on_session_change = MagicMock()
    return mock_client


@pytest.fixture
def session_manager():
    """セッションマネージャーのフィクスチャ"""
    return BlueskySessionManager()


class TestBlueskySessionManagerInitialization:
    """BlueskySessionManager初期化のテストクラス"""
    
    def test_initialization_without_api_client(self):
        """APIクライアントなしでの初期化テスト"""
        manager = BlueskySessionManager()
        assert manager.api_client is None
        assert manager._session_change_handlers == []
    
    def test_initialization_with_api_client(self, mock_api_client):
        """APIクライアント付きでの初期化テスト"""
        manager = BlueskySessionManager(api_client=mock_api_client)
        assert manager.api_client == mock_api_client
        assert manager._session_change_handlers == []


class TestBlueskySessionManagerClientRegistration:
    """クライアント登録のテストクラス"""
    
    @patch('core.client.session_manager.logger')
    def test_register_client_with_valid_client(self, mock_logger, session_manager, mock_api_client):
        """有効なクライアントの登録テスト"""
        # クライアント登録実行
        session_manager.register_client(mock_api_client)
        
        # 結果確認
        assert session_manager.api_client == mock_api_client
        assert hasattr(session_manager, '_internal_session_change_handler')
        mock_logger.info.assert_called_with("セッション変更イベントのコールバック機能を初期化します")
        mock_logger.debug.assert_any_call(f"クライアントオブジェクト: {type(mock_api_client.client)}")
        mock_logger.debug.assert_called_with("セッション変更ハンドラを登録しました")
    
    def test_register_client_without_on_session_change(self, session_manager):
        """on_session_changeがないクライアントの登録テスト"""
        mock_client = MagicMock()
        mock_client.client = MagicMock(spec=[])  # on_session_changeを持たない
        
        session_manager.register_client(mock_client)
        
        # APIクライアントは登録されるが、ハンドラは登録されない
        assert session_manager.api_client == mock_client
        assert not hasattr(session_manager, '_internal_session_change_handler')


class TestBlueskySessionManagerEventHandling:
    """イベントハンドリングのテストクラス"""
    
    @patch('core.client.session_manager.logger')
    def test_on_session_change_registers_handler(self, mock_logger, session_manager):
        """セッション変更ハンドラの登録テスト"""
        # ハンドラを作成
        handler = Mock()
        
        # ハンドラを登録
        session_manager.on_session_change(handler)
        
        # 結果確認
        assert handler in session_manager._session_change_handlers
        assert len(session_manager._session_change_handlers) == 1
        mock_logger.debug.assert_called_with("外部セッション変更ハンドラが登録されました（合計: 1件）")
    
    @patch('core.client.session_manager.logger')
    def test_multiple_handlers_registration(self, mock_logger, session_manager):
        """複数ハンドラの登録テスト"""
        handlers = [Mock() for _ in range(3)]
        
        for i, handler in enumerate(handlers):
            session_manager.on_session_change(handler)
            assert len(session_manager._session_change_handlers) == i + 1
    
    @patch('core.client.session_manager.logger')
    def test_remove_session_change_handler_success(self, mock_logger, session_manager):
        """セッション変更ハンドラの削除成功テスト"""
        handler = Mock()
        session_manager.on_session_change(handler)
        
        # ハンドラを削除
        result = session_manager.remove_session_change_handler(handler)
        
        # 結果確認
        assert result is True
        assert handler not in session_manager._session_change_handlers
        assert len(session_manager._session_change_handlers) == 0
        mock_logger.debug.assert_called_with("外部セッション変更ハンドラが削除されました（合計: 0件）")
    
    def test_remove_session_change_handler_not_found(self, session_manager):
        """存在しないハンドラの削除テスト"""
        handler = Mock()
        
        # 登録されていないハンドラを削除
        result = session_manager.remove_session_change_handler(handler)
        
        # 結果確認
        assert result is False


class TestBlueskySessionManagerInternalHandler:
    """内部ハンドラのテストクラス"""
    
    @patch('core.client.session_manager.logger')
    def test_internal_handler_executes_external_handlers(self, mock_logger, session_manager, mock_api_client):
        """内部ハンドラが外部ハンドラを実行するテスト"""
        # 外部ハンドラを作成
        external_handler1 = Mock()
        external_handler2 = Mock()
        
        # 外部ハンドラを登録
        session_manager.on_session_change(external_handler1)
        session_manager.on_session_change(external_handler2)
        
        # on_session_changeデコレータを保存する変数
        registered_handler = None
        
        def capture_decorator(func):
            nonlocal registered_handler
            registered_handler = func
            return func
        
        mock_api_client.client.on_session_change = capture_decorator
        
        # クライアントを登録
        session_manager.register_client(mock_api_client)
        
        # イベントとセッションをモック
        mock_event = SessionEvent.CREATE
        mock_session = Mock(spec=Session)
        
        # 内部ハンドラを実行
        if registered_handler:
            registered_handler(mock_event, mock_session)
        
        # 結果確認
        external_handler1.assert_called_once_with(mock_event, mock_session)
        external_handler2.assert_called_once_with(mock_event, mock_session)
        mock_logger.info.assert_any_call(f"セッション変更イベントが発生しました: {mock_event}")
    
    @patch('core.client.session_manager.logger')
    def test_internal_handler_handles_external_handler_error(self, mock_logger, session_manager, mock_api_client):
        """外部ハンドラのエラー処理テスト"""
        # エラーを発生させる外部ハンドラ
        error_handler = Mock(side_effect=Exception("Handler error"))
        normal_handler = Mock()
        
        # ハンドラを登録
        session_manager.on_session_change(error_handler)
        session_manager.on_session_change(normal_handler)
        
        # on_session_changeデコレータを保存する変数
        registered_handler = None
        
        def capture_decorator(func):
            nonlocal registered_handler
            registered_handler = func
            return func
        
        mock_api_client.client.on_session_change = capture_decorator
        
        # クライアントを登録
        session_manager.register_client(mock_api_client)
        
        # イベントとセッションをモック
        mock_event = SessionEvent.CREATE
        mock_session = Mock(spec=Session)
        
        # 内部ハンドラを実行
        if registered_handler:
            registered_handler(mock_event, mock_session)
        
        # エラーが発生してもnormal_handlerは実行される
        normal_handler.assert_called_once_with(mock_event, mock_session)
        mock_logger.error.assert_called()


class TestBlueskySessionManagerIntegration:
    """統合テストクラス"""
    
    def test_full_workflow(self, mock_api_client):
        """完全なワークフローのテスト"""
        # セッションマネージャーを作成
        manager = BlueskySessionManager()
        
        # 外部ハンドラを作成
        handler1 = Mock()
        handler2 = Mock()
        
        # ハンドラを登録
        manager.on_session_change(handler1)
        manager.on_session_change(handler2)
        
        # クライアントを登録
        registered_handler = None
        
        def capture_decorator(func):
            nonlocal registered_handler
            registered_handler = func
            return func
        
        mock_api_client.client.on_session_change = capture_decorator
        manager.register_client(mock_api_client)
        
        # イベントをトリガー
        mock_event = SessionEvent.REFRESH
        mock_session = Mock(spec=Session)
        
        if registered_handler:
            registered_handler(mock_event, mock_session)
        
        # ハンドラが呼ばれたことを確認
        handler1.assert_called_once_with(mock_event, mock_session)
        handler2.assert_called_once_with(mock_event, mock_session)
        
        # ハンドラを削除
        assert manager.remove_session_change_handler(handler1) is True
        
        # 再度イベントをトリガー
        handler1.reset_mock()
        handler2.reset_mock()
        
        if registered_handler:
            registered_handler(mock_event, mock_session)
        
        # handler1は呼ばれず、handler2のみ呼ばれる
        handler1.assert_not_called()
        handler2.assert_called_once_with(mock_event, mock_session)