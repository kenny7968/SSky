#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
UnifiedErrorHandler包括的テスト (Phase 2 リファクタリング版)
"""

import pytest
import wx
from unittest.mock import Mock, MagicMock, patch, call
from enum import Enum

from core.error_handler import UnifiedErrorHandler, ErrorLevel
from core.exceptions import AuthenticationError
from atproto.exceptions import AtProtocolError


@pytest.fixture
def mock_auth_manager():
    """認証管理のモック"""
    mock_auth = Mock()
    mock_auth.is_logged_in = True
    return mock_auth


@pytest.fixture
def error_handler(mock_auth_manager):
    """エラーハンドラーインスタンス"""
    return UnifiedErrorHandler(mock_auth_manager)


@pytest.fixture
def mock_wx_window():
    """wxWindowのモック"""
    return Mock(spec=wx.Window)


@pytest.mark.unit
class TestUnifiedErrorHandlerInstantiation:
    """UnifiedErrorHandlerインスタンス化テスト"""
    
    def test_default_instantiation(self):
        """デフォルトインスタンス化テスト"""
        handler = UnifiedErrorHandler()
        
        assert handler is not None
        assert handler.auth_manager is None
    
    def test_with_auth_manager_instantiation(self, mock_auth_manager):
        """認証管理付きインスタンス化テスト"""
        handler = UnifiedErrorHandler(mock_auth_manager)
        
        assert handler.auth_manager is mock_auth_manager


@pytest.mark.unit 
class TestUnifiedErrorHandlerStaticErrorHandling:
    """UnifiedErrorHandler静的エラー処理テスト"""
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_with_exception(self, mock_show_dialog):
        """例外でのエラー処理テスト"""
        test_error = ValueError("Test error")
        test_operation = "テスト操作"
        
        UnifiedErrorHandler.handle_error(test_error, test_operation)
        
        expected_message = "テスト操作に失敗しました: Test error"
        mock_show_dialog.assert_called_once_with(expected_message, "エラー", None)
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_with_string(self, mock_show_dialog):
        """文字列でのエラー処理テスト"""
        test_error = "文字列エラー"
        test_operation = "文字列操作"
        
        UnifiedErrorHandler.handle_error(test_error, test_operation)
        
        expected_message = "文字列操作に失敗しました: 文字列エラー"
        mock_show_dialog.assert_called_once_with(expected_message, "エラー", None)
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_no_operation(self, mock_show_dialog):
        """操作名なしでのエラー処理テスト"""
        test_error = "単純エラー"
        
        UnifiedErrorHandler.handle_error(test_error)
        
        mock_show_dialog.assert_called_once_with("単純エラー", "エラー", None)
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_different_levels(self, mock_show_dialog):
        """異なるエラーレベルのテスト"""
        test_error = "レベルテスト"
        
        # INFO レベル
        UnifiedErrorHandler.handle_error(test_error, level=ErrorLevel.INFO)
        mock_show_dialog.assert_called_with("レベルテスト", "情報", None)
        
        # WARNING レベル
        UnifiedErrorHandler.handle_error(test_error, level=ErrorLevel.WARNING)
        mock_show_dialog.assert_called_with("レベルテスト", "警告", None)
        
        # CRITICAL レベル
        UnifiedErrorHandler.handle_error(test_error, level=ErrorLevel.CRITICAL)
        mock_show_dialog.assert_called_with("レベルテスト", "重大なエラー", None)
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_no_dialog(self, mock_show_dialog):
        """ダイアログ表示なしテスト"""
        test_error = "ノーダイアログエラー"
        
        UnifiedErrorHandler.handle_error(test_error, show_dialog=False)
        
        mock_show_dialog.assert_not_called()
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_error_with_parent(self, mock_show_dialog, mock_wx_window):
        """親ウィンドウ付きエラー処理テスト"""
        test_error = "親ウィンドウエラー"
        
        UnifiedErrorHandler.handle_error(test_error, parent=mock_wx_window)
        
        mock_show_dialog.assert_called_once_with("親ウィンドウエラー", "エラー", mock_wx_window)


@pytest.mark.unit
class TestUnifiedErrorHandlerAPIErrorHandling:
    """UnifiedErrorHandlerのAPI エラー処理テスト"""
    
    def test_handle_api_error_authentication_error(self, error_handler, mock_auth_manager):
        """認証エラーの処理テスト"""
        test_error = AtProtocolError("Authentication failed")
        
        # is_authentication_error が True を返すようにモック
        with patch.object(error_handler, 'is_authentication_error', return_value=True):
            result = error_handler.handle_api_error(test_error, "API テスト")
        
        assert result is True
        mock_auth_manager.handle_authentication_error.assert_called_once_with(test_error, "API テスト")
    
    def test_handle_api_error_non_authentication_error(self, error_handler, mock_auth_manager):
        """非認証エラーの処理テスト"""
        test_error = AtProtocolError("Network error")
        
        with patch.object(error_handler, 'is_authentication_error', return_value=False):
            result = error_handler.handle_api_error(test_error, "ネットワークテスト")
        
        assert result is False
        mock_auth_manager.handle_authentication_error.assert_not_called()
    
    def test_handle_api_error_non_atproto_error(self, error_handler):
        """AtProtocolError以外のエラー処理テスト"""
        test_error = ValueError("Generic error")
        
        result = error_handler.handle_api_error(test_error, "汎用テスト")
        
        assert result is False
    
    def test_handle_api_error_no_auth_manager(self):
        """認証管理なしでのエラー処理テスト"""
        handler = UnifiedErrorHandler(None)
        test_error = AtProtocolError("Auth error")
        
        with patch.object(handler, 'is_authentication_error', return_value=True):
            result = handler.handle_api_error(test_error)
        
        assert result is True


@pytest.mark.unit
class TestUnifiedErrorHandlerAuthenticationErrorDetection:
    """UnifiedErrorHandler認証エラー検出テスト"""
    
    def test_is_authentication_error_atproto_keywords(self, error_handler):
        """AtProtocolErrorキーワード検出テスト"""
        auth_error_messages = [
            "Authentication failed",
            "UNAUTHORIZED access",
            "invalid_token provided",
            "Token_Expired error",
            "session_expired detected",
            "Invalid_Session state",
            "access_denied by server",
            "FORBIDDEN operation"
        ]
        
        for message in auth_error_messages:
            error = AtProtocolError(message)
            assert error_handler.is_authentication_error(error) is True
    
    def test_is_authentication_error_non_auth_atproto(self, error_handler):
        """非認証AtProtocolErrorテスト"""
        non_auth_messages = [
            "Network timeout",
            "Service unavailable", 
            "Invalid parameter",
            "Resource not found",
            "Rate limit exceeded"
        ]
        
        for message in non_auth_messages:
            error = AtProtocolError(message)
            assert error_handler.is_authentication_error(error) is False
    
    def test_is_authentication_error_authentication_error_class(self, error_handler):
        """AuthenticationErrorクラステスト"""
        auth_error = AuthenticationError("Session expired")
        
        assert error_handler.is_authentication_error(auth_error) is True
    
    def test_is_authentication_error_other_exceptions(self, error_handler):
        """その他の例外テスト"""
        other_errors = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            Exception("Generic exception")
        ]
        
        for error in other_errors:
            assert error_handler.is_authentication_error(error) is False


@pytest.mark.unit
class TestUnifiedErrorHandlerAuthCheckWrapper:
    """UnifiedErrorHandlerの認証チェックラッパーテスト"""
    
    def test_handle_with_auth_check_success(self, error_handler):
        """認証チェック付き実行成功テスト"""
        def test_function(arg1, arg2, kwarg1=None):
            return f"result:{arg1}:{arg2}:{kwarg1}"
        
        result = error_handler.handle_with_auth_check(
            test_function, "pos1", "pos2", kwarg1="kw1", operation_name="テスト関数"
        )
        
        assert result == "result:pos1:pos2:kw1"
    
    def test_handle_with_auth_check_atproto_auth_error(self, error_handler):
        """認証エラーでのラッパーテスト"""
        def failing_function():
            raise AtProtocolError("Authentication failed")
        
        with patch.object(error_handler, 'handle_api_error', return_value=True):
            with pytest.raises(AuthenticationError, match="セッションが無効になりました"):
                error_handler.handle_with_auth_check(failing_function, operation_name="認証失敗テスト")
    
    def test_handle_with_auth_check_atproto_non_auth_error(self, error_handler):
        """非認証AtProtocolErrorでのラッパーテスト"""
        test_error = AtProtocolError("Network error")
        
        def failing_function():
            raise test_error
        
        with patch.object(error_handler, 'handle_api_error', return_value=False):
            with pytest.raises(AtProtocolError):
                error_handler.handle_with_auth_check(failing_function, operation_name="ネットワークエラーテスト")
    
    def test_handle_with_auth_check_generic_error(self, error_handler):
        """汎用エラーでのラッパーテスト"""
        test_error = ValueError("Generic error")
        
        def failing_function():
            raise test_error
        
        with pytest.raises(ValueError):
            error_handler.handle_with_auth_check(failing_function, operation_name="汎用エラーテスト")
    
    def test_handle_with_auth_check_default_operation_name(self, error_handler):
        """デフォルト操作名テスト"""
        def named_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            error_handler.handle_with_auth_check(named_function)


@pytest.mark.unit
class TestUnifiedErrorHandlerSafeAPICall:
    """UnifiedErrorHandlerの安全API呼び出しテスト"""
    
    def test_safe_api_call_success(self, error_handler, mock_auth_manager):
        """安全API呼び出し成功テスト"""
        def test_api():
            return "API成功"
        
        result = error_handler.safe_api_call(test_api, operation_name="APIテスト")
        
        assert result == "API成功"
    
    def test_safe_api_call_login_required_success(self, error_handler, mock_auth_manager):
        """ログイン必須API呼び出し成功テスト"""
        mock_auth_manager.is_logged_in = True
        
        def test_api():
            return "認証済みAPI成功"
        
        result = error_handler.safe_api_call(test_api, operation_name="認証APIテスト")
        
        assert result == "認証済みAPI成功"
    
    def test_safe_api_call_login_required_not_logged_in(self, error_handler, mock_auth_manager):
        """ログイン未済でのAPI呼び出しテスト"""
        mock_auth_manager.is_logged_in = False
        
        def test_api():
            return "不正な呼び出し"
        
        with pytest.raises(Exception, match="認証APIテストにはログインが必要です"):
            error_handler.safe_api_call(test_api, operation_name="認証APIテスト")
    
    def test_safe_api_call_no_login_required(self, error_handler, mock_auth_manager):
        """ログイン不要API呼び出しテスト"""
        mock_auth_manager.is_logged_in = False
        
        def test_api():
            return "パブリックAPI成功"
        
        result = error_handler.safe_api_call(test_api, operation_name="パブリックAPIテスト", require_login=False)
        
        assert result == "パブリックAPI成功"
    
    def test_safe_api_call_no_auth_manager(self):
        """認証管理なしでのAPI呼び出しテスト"""
        handler = UnifiedErrorHandler(None)
        
        def test_api():
            return "認証管理なしAPI"
        
        result = handler.safe_api_call(test_api, operation_name="無認証APIテスト")
        
        assert result == "認証管理なしAPI"
    
    def test_safe_api_call_default_operation_name(self, error_handler):
        """デフォルト操作名でのAPI呼び出しテスト"""
        def named_api_function():
            return "名前付きAPI"
        
        result = error_handler.safe_api_call(named_api_function, require_login=False)
        
        assert result == "名前付きAPI"
    
    def test_safe_api_call_authentication_error_propagation(self, error_handler):
        """認証エラー伝播テスト"""
        def failing_api():
            raise AtProtocolError("Authentication failed")
        
        with patch.object(error_handler, 'handle_with_auth_check') as mock_handle:
            mock_handle.side_effect = AuthenticationError("セッションが無効")
            
            with pytest.raises(AuthenticationError):
                error_handler.safe_api_call(failing_api, operation_name="認証失敗API", require_login=False)


@pytest.mark.unit
class TestUnifiedErrorHandlerValidationAndSuccess:
    """UnifiedErrorHandlerのバリデーション・成功処理テスト"""
    
    @patch('core.error_handler.UnifiedErrorHandler._show_error_dialog')
    def test_handle_validation_error(self, mock_show_dialog):
        """バリデーションエラー処理テスト"""
        test_message = "入力値が無効です"
        test_operation = "入力検証"
        
        UnifiedErrorHandler.handle_validation_error(test_message, test_operation)
        
        expected_message = "入力検証に失敗しました: 入力値が無効です"
        mock_show_dialog.assert_called_once_with(expected_message, "警告", None)
    
    @patch('wx.MessageBox')
    def test_handle_success_with_dialog(self, mock_message_box):
        """ダイアログ付き成功処理テスト"""
        test_message = "操作が完了しました"
        test_title = "完了"
        
        UnifiedErrorHandler.handle_success(test_message, test_title)
        
        mock_message_box.assert_called_once_with(test_message, test_title, wx.OK | wx.ICON_INFORMATION)
    
    def test_handle_success_no_dialog_with_status_bar(self):
        """ステータスバー付き成功処理テスト"""
        test_message = "ステータス更新完了"
        mock_status_bar = Mock()
        
        UnifiedErrorHandler.handle_success(test_message, show_dialog=False, status_bar=mock_status_bar)
        
        mock_status_bar.SetStatusText.assert_called_once_with(test_message)
    
    def test_handle_success_no_dialog_no_status_bar(self):
        """ダイアログもステータスバーもない成功処理テスト"""
        test_message = "ログのみ成功"
        
        # ログ出力のみの確認（例外が発生しないことを確認）
        result = UnifiedErrorHandler.handle_success(test_message, show_dialog=False)
        
        assert result is None
    
    def test_update_status_bar_success(self):
        """ステータスバー更新成功テスト"""
        mock_status_bar = Mock()
        test_message = "ステータス更新テスト"
        
        UnifiedErrorHandler.update_status_bar(mock_status_bar, test_message, success=True)
        
        mock_status_bar.SetStatusText.assert_called_once_with(test_message)
    
    def test_update_status_bar_error(self):
        """ステータスバー更新エラーテスト"""
        mock_status_bar = Mock()
        test_message = "エラーステータス"
        
        UnifiedErrorHandler.update_status_bar(mock_status_bar, test_message, success=False)
        
        mock_status_bar.SetStatusText.assert_called_once_with(test_message)
    
    def test_update_status_bar_no_status_bar(self):
        """ステータスバーなしでの更新テスト"""
        test_message = "ステータスバーなし"
        
        # 例外が発生しないことを確認
        result = UnifiedErrorHandler.update_status_bar(None, test_message)
        
        assert result is None
    
    def test_update_status_bar_exception_handling(self):
        """ステータスバー更新例外処理テスト"""
        mock_status_bar = Mock()
        mock_status_bar.SetStatusText.side_effect = Exception("Status bar error")
        
        # 例外が外部に伝播しないことを確認
        result = UnifiedErrorHandler.update_status_bar(mock_status_bar, "テストメッセージ")
        
        assert result is None


@pytest.mark.unit
class TestUnifiedErrorHandlerDialogDisplay:
    """UnifiedErrorHandlerのダイアログ表示テスト"""
    
    @patch('wx.MessageBox')
    def test_show_error_dialog_info(self, mock_message_box, mock_wx_window):
        """情報ダイアログ表示テスト"""
        UnifiedErrorHandler._show_error_dialog("情報メッセージ", "情報", mock_wx_window)
        
        mock_message_box.assert_called_once_with(
            "情報メッセージ", "情報", wx.OK | wx.ICON_INFORMATION, mock_wx_window
        )
    
    @patch('wx.MessageBox')
    def test_show_error_dialog_warning(self, mock_message_box, mock_wx_window):
        """警告ダイアログ表示テスト"""
        UnifiedErrorHandler._show_error_dialog("警告メッセージ", "警告", mock_wx_window)
        
        mock_message_box.assert_called_once_with(
            "警告メッセージ", "警告", wx.OK | wx.ICON_WARNING, mock_wx_window
        )
    
    @patch('wx.MessageBox')
    def test_show_error_dialog_error(self, mock_message_box):
        """エラーダイアログ表示テスト"""
        UnifiedErrorHandler._show_error_dialog("エラーメッセージ", "エラー")
        
        mock_message_box.assert_called_once_with(
            "エラーメッセージ", "エラー", wx.OK | wx.ICON_ERROR, None
        )
    
    @patch('wx.MessageBox')
    def test_show_error_dialog_critical(self, mock_message_box):
        """重大エラーダイアログ表示テスト"""
        UnifiedErrorHandler._show_error_dialog("重大エラー", "重大なエラー")
        
        mock_message_box.assert_called_once_with(
            "重大エラー", "重大なエラー", wx.OK | wx.ICON_ERROR, None
        )


@pytest.mark.unit
class TestUnifiedErrorHandlerContextLogging:
    """UnifiedErrorHandlerのコンテキストログ機能テスト"""
    
    def test_create_error_context(self, error_handler):
        """エラーコンテキスト作成テスト"""
        test_operation = "コンテキストテスト"
        test_context = {"user_id": "test123", "action": "save"}
        
        with patch('logging.makeLogRecord') as mock_make_record, \
             patch('logging.Formatter.formatTime') as mock_format_time:
            mock_make_record.return_value = {}
            mock_format_time.return_value = "2024-01-01 12:00:00"
            
            context = error_handler.create_error_context(test_operation, **test_context)
        
        assert context['operation'] == test_operation
        assert context['timestamp'] == "2024-01-01 12:00:00"
        assert context['context'] == test_context
    
    @patch('core.error_handler.logger')
    def test_log_error_with_context(self, mock_logger, error_handler):
        """コンテキスト付きエラーログテスト"""
        test_error = ValueError("Context error")
        test_operation = "コンテキスト操作"
        test_context = {"request_id": "req123", "user": "testuser"}
        
        with patch.object(error_handler, 'create_error_context') as mock_create_context:
            mock_create_context.return_value = {
                'operation': test_operation,
                'timestamp': '2024-01-01 12:00:00',
                'context': test_context
            }
            
            error_handler.log_error_with_context(test_error, test_operation, **test_context)
        
        mock_create_context.assert_called_once_with(test_operation, **test_context)
        mock_logger.error.assert_called_once()
        
        # ログメッセージの内容確認
        logged_message = mock_logger.error.call_args[0][0]
        assert "Context error" in logged_message
        assert test_operation in logged_message
        assert "2024-01-01 12:00:00" in logged_message
        assert str(test_context) in logged_message


@pytest.mark.unit
class TestUnifiedErrorHandlerIntegration:
    """UnifiedErrorHandler統合テスト"""
    
    def test_complete_error_handling_flow(self, error_handler, mock_auth_manager):
        """完全なエラー処理フローテスト"""
        def api_function():
            raise AtProtocolError("Authentication failed")
        
        # 認証エラーとして扱われるようにセットアップ
        with patch.object(error_handler, 'is_authentication_error', return_value=True):
            with pytest.raises(AuthenticationError):
                error_handler.safe_api_call(api_function, operation_name="統合テスト", require_login=True)
        
        # 認証マネージャーのエラー処理が呼ばれることを確認
        mock_auth_manager.handle_authentication_error.assert_called_once()
    
    def test_error_level_escalation_flow(self, error_handler):
        """エラーレベルエスカレーションフローテスト"""
        test_errors = [
            ("情報エラー", ErrorLevel.INFO),
            ("警告エラー", ErrorLevel.WARNING), 
            ("通常エラー", ErrorLevel.ERROR),
            ("重大エラー", ErrorLevel.CRITICAL)
        ]
        
        with patch('core.error_handler.UnifiedErrorHandler._show_error_dialog') as mock_dialog:
            for message, level in test_errors:
                UnifiedErrorHandler.handle_error(message, level=level)
        
        assert mock_dialog.call_count == 4
        
        # 各レベルでの呼び出しを確認
        expected_calls = [
            call("情報エラー", "情報", None),
            call("警告エラー", "警告", None),
            call("通常エラー", "エラー", None),
            call("重大エラー", "重大なエラー", None)
        ]
        mock_dialog.assert_has_calls(expected_calls)
    
    def test_multiple_error_scenarios(self, error_handler, mock_auth_manager):
        """複数エラーシナリオテスト"""
        # シナリオ1: 認証エラー
        auth_error = AtProtocolError("Token expired")
        with patch.object(error_handler, 'is_authentication_error', return_value=True):
            auth_result = error_handler.handle_api_error(auth_error, "認証テスト")
        assert auth_result is True
        
        # シナリオ2: ネットワークエラー 
        network_error = AtProtocolError("Network timeout")
        with patch.object(error_handler, 'is_authentication_error', return_value=False):
            network_result = error_handler.handle_api_error(network_error, "ネットワークテスト")
        assert network_result is False
        
        # シナリオ3: バリデーションエラー
        with patch('core.error_handler.UnifiedErrorHandler._show_error_dialog') as mock_dialog:
            UnifiedErrorHandler.handle_validation_error("無効な入力", "入力検証")
            mock_dialog.assert_called_once()
    
    def test_concurrent_error_handling_simulation(self, error_handler):
        """同時エラー処理シミュレーションテスト"""
        errors = [
            ValueError("エラー1"),
            TypeError("エラー2"),
            RuntimeError("エラー3")
        ]
        
        with patch('core.error_handler.UnifiedErrorHandler._show_error_dialog') as mock_dialog:
            for error in errors:
                UnifiedErrorHandler.handle_error(error, f"操作{type(error).__name__}")
        
        assert mock_dialog.call_count == 3
        
        # 各エラーが適切に処理されたことを確認
        call_messages = [call[0][0] for call in mock_dialog.call_args_list]
        assert "操作ValueErrorに失敗しました: エラー1" in call_messages
        assert "操作TypeErrorに失敗しました: エラー2" in call_messages
        assert "操作RuntimeErrorに失敗しました: エラー3" in call_messages