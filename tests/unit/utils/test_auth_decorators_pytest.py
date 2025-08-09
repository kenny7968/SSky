#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証デコレータの単体テスト (Phase 2 pytest版)
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import logging

from utils.auth_decorators import require_authentication, require_selection


class TestRequireAuthentication:
    """require_authentication デコレータのテストクラス"""
    
    def test_authenticated_user_success(self, mock_wx):
        """認証済みユーザーでの正常実行テスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        
        # デコレータ適用した関数を定義
        @require_authentication(mock_session)
        def test_function():
            return "success"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result == "success"
        # MessageBoxが呼ばれないことを確認
        mock_wx.MessageBox.assert_not_called()
    
    def test_unauthenticated_user_blocked(self, mock_wx):
        """未認証ユーザーでの実行ブロックテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = False
        
        # デコレータ適用した関数を定義
        @require_authentication(mock_session)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが適切な引数で呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
        call_args = mock_wx.MessageBox.call_args[0]
        assert "この操作にはログインが必要です" in call_args[0]
        assert call_args[1] == "エラー"
    
    def test_none_session_manager(self, mock_wx):
        """セッションマネージャーがNoneの場合のテスト"""
        # デコレータ適用した関数を定義
        @require_authentication(None)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_session_manager_without_is_logged_in(self, mock_wx):
        """is_logged_in属性がないセッションマネージャーのテスト"""
        # is_logged_in属性がないモックを作成
        mock_session = MagicMock()
        del mock_session.is_logged_in
        
        # デコレータ適用した関数を定義
        @require_authentication(mock_session)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_function_with_arguments(self, mock_wx):
        """引数を持つ関数での正常実行テスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        
        # デコレータ適用した引数付き関数を定義
        @require_authentication(mock_session)
        def test_function(arg1, arg2, kwarg1=None):
            return f"result: {arg1}, {arg2}, {kwarg1}"
        
        # 実行
        result = test_function("test1", "test2", kwarg1="test3")
        
        # 結果確認
        assert result == "result: test1, test2, test3"
    
    def test_function_with_exception(self, mock_wx):
        """デコレータ内でのメソッドが例外を発生させるテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        
        # デコレータ適用した例外発生関数を定義
        @require_authentication(mock_session)
        def test_function():
            raise ValueError("test exception")
        
        # 例外が適切にraise されることを確認
        with pytest.raises(ValueError, match="test exception"):
            test_function()
    
    def test_decorator_preserves_function_metadata(self):
        """デコレータが元の関数のメタデータを保持するテスト"""
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        
        def original_function():
            """Original function docstring"""
            return "original"
        
        # デコレータを適用
        decorated_function = require_authentication(mock_session)(original_function)
        
        # メタデータが保持されることを確認
        assert decorated_function.__name__ == original_function.__name__
        assert decorated_function.__doc__ == original_function.__doc__


class TestRequireSelection:
    """require_selection デコレータのテストクラス"""
    
    def test_with_valid_selection(self):
        """有効な選択がある場合のテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1, "text": "selected item"}
        
        # デコレータ適用した関数を定義
        @require_selection(mock_list_ctrl)
        def test_function():
            return "success"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result == "success"
    
    def test_with_no_selection(self, mock_wx):
        """選択がない場合のテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = None
        
        # デコレータ適用した関数を定義
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが適切に呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
        call_args = mock_wx.MessageBox.call_args[0]
        assert "項目を選択してください" in call_args[0]
    
    def test_with_none_list_ctrl(self, mock_wx):
        """リストコントロールがNoneの場合のテスト"""
        # デコレータ適用した関数を定義
        @require_selection(None)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_list_ctrl_without_get_selected_item(self, mock_wx):
        """get_selected_itemメソッドがないリストコントロールのテスト"""
        mock_list_ctrl = MagicMock()
        del mock_list_ctrl.get_selected_item
        
        # デコレータ適用した関数を定義
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_get_selected_item_raises_exception(self, mock_wx):
        """get_selected_itemが例外を発生させる場合のテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.side_effect = RuntimeError("Selection error")
        
        # デコレータ適用した関数を定義
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_function_with_arguments_and_selection(self):
        """引数を持つ関数での選択ありテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1, "text": "selected"}
        
        # デコレータ適用した引数付き関数を定義
        @require_selection(mock_list_ctrl)
        def test_function(arg1, arg2=None):
            return f"result: {arg1}, {arg2}"
        
        # 実行
        result = test_function("test1", arg2="test2")
        
        # 結果確認
        assert result == "result: test1, test2"
    
    def test_decorator_preserves_function_metadata(self):
        """デコレータが元の関数のメタデータを保持するテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1}
        
        def original_function():
            """Original selection function docstring"""
            return "original"
        
        # デコレータを適用
        decorated_function = require_selection(mock_list_ctrl)(original_function)
        
        # メタデータが保持されることを確認
        assert decorated_function.__name__ == original_function.__name__
        assert decorated_function.__doc__ == original_function.__doc__


class TestDecoratorsIntegration:
    """デコレータ統合テストクラス"""
    
    def test_combined_decorators_both_pass(self, mock_wx):
        """認証と選択の両方が成功する場合のテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1, "text": "selected"}
        
        # 両方のデコレータを適用した関数を定義
        @require_authentication(mock_session)
        @require_selection(mock_list_ctrl)
        def test_function():
            return "success"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result == "success"
        # MessageBoxが呼ばれないことを確認
        mock_wx.MessageBox.assert_not_called()
    
    def test_combined_decorators_auth_fails(self, mock_wx):
        """認証が失敗する場合のテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = False
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1, "text": "selected"}
        
        # 両方のデコレータを適用した関数を定義
        @require_authentication(mock_session)
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # 認証エラーのMessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
        call_args = mock_wx.MessageBox.call_args[0]
        assert "この操作にはログインが必要です" in call_args[0]
    
    def test_combined_decorators_selection_fails(self, mock_wx):
        """選択が失敗する場合のテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = None
        
        # 両方のデコレータを適用した関数を定義
        @require_authentication(mock_session)
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # 選択エラーのMessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
        call_args = mock_wx.MessageBox.call_args[0]
        assert "項目を選択してください" in call_args[0]
    
    def test_combined_decorators_both_fail(self, mock_wx):
        """認証と選択の両方が失敗する場合のテスト"""
        # モックの設定
        mock_session = MagicMock()
        mock_session.is_logged_in = False
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = None
        
        # 両方のデコレータを適用した関数を定義
        @require_authentication(mock_session)
        @require_selection(mock_list_ctrl)
        def test_function():
            return "should not execute"
        
        # 実行
        result = test_function()
        
        # 結果確認
        assert result is None
        
        # 認証が先にチェックされるため、認証エラーが表示される
        mock_wx.MessageBox.assert_called_once()
        call_args = mock_wx.MessageBox.call_args[0]
        assert "この操作にはログインが必要です" in call_args[0]


# エラー処理テスト
class TestDecoratorsErrorHandling:
    """デコレータエラーハンドリングテストクラス"""
    
    def test_require_authentication_with_logger_error(self, mock_wx, mock_logger):
        """require_authentication でのログエラーテスト"""
        mock_session = MagicMock()
        mock_session.is_logged_in = False
        
        with patch('utils.auth_decorators.logger', mock_logger):
            @require_authentication(mock_session)
            def test_function():
                return "should not execute"
            
            result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxとログが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()
    
    def test_require_selection_with_logger_error(self, mock_wx, mock_logger):
        """require_selection でのログエラーテスト"""
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = None
        
        with patch('utils.auth_decorators.logger', mock_logger):
            @require_selection(mock_list_ctrl)
            def test_function():
                return "should not execute"
            
            result = test_function()
        
        # 結果確認
        assert result is None
        
        # MessageBoxが呼ばれることを確認
        mock_wx.MessageBox.assert_called_once()


# パフォーマンステスト
@pytest.mark.slow
class TestDecoratorsPerformance:
    """デコレータパフォーマンステストクラス"""
    
    def test_authentication_check_performance(self):
        """認証チェックの性能テスト"""
        import time
        
        mock_session = MagicMock()
        mock_session.is_logged_in = True
        
        @require_authentication(mock_session)
        def test_function():
            return "success"
        
        # 大量実行での性能測定
        start_time = time.time()
        
        results = [test_function() for _ in range(1000)]
        
        end_time = time.time()
        
        # 全て成功することを確認
        assert all(result == "success" for result in results)
        
        # 性能目標: 1000回実行で1秒以内
        assert end_time - start_time < 1.0
    
    def test_selection_check_performance(self):
        """選択チェックの性能テスト"""
        import time
        
        mock_list_ctrl = MagicMock()
        mock_list_ctrl.get_selected_item.return_value = {"id": 1}
        
        @require_selection(mock_list_ctrl)
        def test_function():
            return "success"
        
        # 大量実行での性能測定
        start_time = time.time()
        
        results = [test_function() for _ in range(1000)]
        
        end_time = time.time()
        
        # 全て成功することを確認
        assert all(result == "success" for result in results)
        
        # 性能目標: 1000回実行で1秒以内
        assert end_time - start_time < 1.0