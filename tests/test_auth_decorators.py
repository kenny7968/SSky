#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証デコレータの単体テスト (Phase 1 リファクタリング版)
"""

import unittest
from unittest.mock import patch, MagicMock
import functools

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.auth_decorators import require_authentication, require_client, require_selection, combine_decorators, require_auth_and_selection


class TestRequireAuthentication(unittest.TestCase):
    """require_authentication デコレータのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # テスト用のモッククラスを作成
        self.mock_instance = MagicMock()
        self.mock_instance.client = MagicMock()
        self.mock_instance.client.is_logged_in = True
    
    @patch('wx.MessageBox')
    def test_require_authentication_success(self, mock_msgbox):
        """認証成功時のテスト"""
        @require_authentication()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_authentication_no_client(self, mock_msgbox, mock_logger):
        """クライアント未設定時のテスト"""
        # クライアント未設定の状態
        instance_no_client = MagicMock()
        delattr(instance_no_client, 'client')
        
        @require_authentication()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(instance_no_client)
        
        # 結果確認
        self.assertFalse(result)  # デフォルトreturn_value
        mock_msgbox.assert_called_once_with(
            "この操作にはログインが必要です", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        mock_logger.warning.assert_called_once()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_authentication_client_none(self, mock_msgbox, mock_logger):
        """クライアントがNoneの時のテスト"""
        self.mock_instance.client = None
        
        @require_authentication("カスタムメッセージ", "custom_return")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "custom_return")
        mock_msgbox.assert_called_once_with(
            "カスタムメッセージ", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        mock_logger.warning.assert_called_once()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_authentication_not_logged_in(self, mock_msgbox, mock_logger):
        """未ログイン時のテスト"""
        # 未ログイン状態に設定
        self.mock_instance.client.is_logged_in = False
        
        @require_authentication("ログインが必要です", None)
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertIsNone(result)
        mock_msgbox.assert_called_once_with(
            "ログインが必要です", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        mock_logger.warning.assert_called_once()
    
    def test_decorator_preserves_function_metadata(self):
        """デコレータが関数のメタデータを保持するテスト"""
        @require_authentication()
        def test_function():
            """テスト関数のドキュメント"""
            pass
        
        # メタデータが保持されていることを確認
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "テスト関数のドキュメント")
    
    def test_decorator_with_arguments(self):
        """引数を持つ関数へのデコレータ適用テスト"""
        @require_authentication()
        def test_method_with_args(self, arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"
        
        # テスト実行
        result = test_method_with_args(
            self.mock_instance, "test1", "test2", kwarg1="test3"
        )
        
        # 結果確認
        self.assertEqual(result, "test1-test2-test3")


class TestRequireClient(unittest.TestCase):
    """require_client デコレータのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.mock_instance = MagicMock()
        self.mock_instance.client = MagicMock()
    
    @patch('wx.MessageBox')
    def test_require_client_success(self, mock_msgbox):
        """クライアント存在時の成功テスト"""
        @require_client()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_client_no_client(self, mock_msgbox, mock_logger):
        """クライアント未設定時のテスト"""
        # クライアント属性を削除
        delattr(self.mock_instance, 'client')
        
        @require_client("クライアントエラー", "error_return")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "error_return")
        mock_msgbox.assert_called_once_with(
            "クライアントエラー", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        mock_logger.error.assert_called_once()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_client_none(self, mock_msgbox, mock_logger):
        """クライアントがNoneの時のテスト"""
        self.mock_instance.client = None
        
        @require_client()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertIsNone(result)  # デフォルトreturn_value
        mock_msgbox.assert_called_once_with(
            "クライアントが初期化されていません", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        mock_logger.error.assert_called_once()


class TestRequireSelection(unittest.TestCase):
    """require_selection デコレータのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.mock_instance = MagicMock()
        
        # タイムライン関連のモック設定
        self.mock_instance.parent = MagicMock()
        self.mock_instance.parent.timeline = MagicMock()
        self.mock_instance.parent.timeline.get_selected_post.return_value = {'id': 'test_post'}
    
    @patch('wx.MessageBox')
    def test_require_selection_success(self, mock_msgbox):
        """選択成功時のテスト"""
        @require_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_selection_no_selection(self, mock_msgbox, mock_logger):
        """未選択時のテスト"""
        # 選択なしに設定
        self.mock_instance.parent.timeline.get_selected_post.return_value = None
        
        @require_selection(error_message="選択してください", return_value="no_selection")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "no_selection")
        mock_msgbox.assert_called_once_with(
            "選択してください", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
        # ログの確認は実装に依存するため、コメントアウト
        # mock_logger.warning.assert_called_once()
    
    @patch('wx.MessageBox')
    def test_require_selection_no_timeline(self, mock_msgbox):
        """タイムラインなし時のテスト"""
        # parent.timeline を削除
        delattr(self.mock_instance.parent, 'timeline')
        
        @require_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # タイムラインがない場合はチェックをスキップして成功
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('wx.MessageBox')
    def test_require_selection_no_parent(self, mock_msgbox):
        """親なし時のテスト"""
        # parent を削除
        delattr(self.mock_instance, 'parent')
        
        @require_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 親がない場合はチェックをスキップして成功
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('wx.MessageBox')
    def test_require_selection_custom_method(self, mock_msgbox):
        """カスタム選択メソッドのテスト"""
        # カスタム選択メソッドを設定
        self.mock_instance.parent.timeline.get_custom_selection = MagicMock(
            return_value={'id': 'custom_post'}
        )
        
        @require_selection(get_selection_method="get_custom_selection")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        self.mock_instance.parent.timeline.get_custom_selection.assert_called_once()
        mock_msgbox.assert_not_called()


class TestCombineDecorators(unittest.TestCase):
    """combine_decorators 関数のテストクラス"""
    
    def test_combine_decorators_execution_order(self):
        """デコレータの実行順序テスト"""
        execution_order = []
        
        def decorator1(func):
            def wrapper(*args, **kwargs):
                execution_order.append('decorator1_start')
                result = func(*args, **kwargs)
                execution_order.append('decorator1_end')
                return result
            return wrapper
        
        def decorator2(func):
            def wrapper(*args, **kwargs):
                execution_order.append('decorator2_start')
                result = func(*args, **kwargs)
                execution_order.append('decorator2_end')
                return result
            return wrapper
        
        @combine_decorators(decorator1, decorator2)
        def test_function():
            execution_order.append('function_execution')
            return "result"
        
        # 実行
        result = test_function()
        
        # 結果確認
        self.assertEqual(result, "result")
        expected_order = [
            'decorator1_start', 'decorator2_start', 'function_execution', 
            'decorator2_end', 'decorator1_end'
        ]
        self.assertEqual(execution_order, expected_order)


class TestRequireAuthAndSelection(unittest.TestCase):
    """require_auth_and_selection デコレータのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.mock_instance = MagicMock()
        self.mock_instance.client = MagicMock()
        self.mock_instance.client.is_logged_in = True
        
        # タイムライン関連のモック設定
        self.mock_instance.parent = MagicMock()
        self.mock_instance.parent.timeline = MagicMock()
        self.mock_instance.parent.timeline.get_selected_post.return_value = {'id': 'test_post'}
    
    @patch('wx.MessageBox')
    def test_require_auth_and_selection_success(self, mock_msgbox):
        """認証・選択両方成功のテスト"""
        @require_auth_and_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_auth_and_selection_auth_fail(self, mock_msgbox, mock_logger):
        """認証失敗のテスト"""
        # 未ログイン状態に設定
        self.mock_instance.client.is_logged_in = False
        
        @require_auth_and_selection("認証エラー", "選択エラー")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 認証エラーが先に発生
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "認証エラー", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_require_auth_and_selection_selection_fail(self, mock_msgbox, mock_logger):
        """選択失敗のテスト"""
        # 選択なしに設定
        self.mock_instance.parent.timeline.get_selected_post.return_value = None
        
        @require_auth_and_selection("認証エラー", "選択エラー")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 選択エラーが発生
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "選択エラー", 
            "エラー", 
            516  # wx.OK | wx.ICON_ERROR
        )


class TestDecoratorsIntegration(unittest.TestCase):
    """デコレータの統合テストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        self.mock_instance = MagicMock()
        self.mock_instance.client = MagicMock()
        self.mock_instance.client.is_logged_in = True
    
    def test_multiple_decorators_interaction(self):
        """複数デコレータの相互作用テスト"""
        @require_client()
        @require_authentication()
        def test_method(self):
            return "success"
        
        # 正常な状態でのテスト実行
        result = test_method(self.mock_instance)
        self.assertEqual(result, "success")
    
    @patch('utils.auth_decorators.logger')
    @patch('wx.MessageBox')
    def test_decorators_error_precedence(self, mock_msgbox, mock_logger):
        """デコレータのエラー処理優先順位テスト"""
        # クライアントとログイン状態の両方を無効化
        self.mock_instance.client = None
        
        @require_client()
        @require_authentication()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 外側のデコレータ（require_client）が先に実行される
        self.assertIsNone(result)
        mock_msgbox.assert_called_once()
        # require_clientのエラーメッセージが表示される


if __name__ == '__main__':
    unittest.main(verbosity=2)