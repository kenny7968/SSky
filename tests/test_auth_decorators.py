#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証デコレータのテスト
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.auth_decorators import (
    require_authentication, 
    require_client, 
    require_selection, 
    combine_decorators, 
    require_auth_and_selection
)

class TestAuthDecorators(unittest.TestCase):
    """認証デコレータのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用のモッククラスを作成
        self.mock_instance = MagicMock()
        self.mock_instance.client = MagicMock()
        self.mock_instance.client.is_logged_in = True
        
        # タイムライン関連のモック
        self.mock_instance.parent = MagicMock()
        self.mock_instance.parent.timeline = MagicMock()
        self.mock_instance.parent.timeline.get_selected_post.return_value = {'test': 'data'}
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_authentication_success(self, mock_msgbox):
        """認証デコレータ成功のテスト"""
        @require_authentication()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_authentication_no_client(self, mock_msgbox):
        """クライアント未設定時のテスト"""
        # クライアント未設定の状態
        instance_no_client = MagicMock()
        del instance_no_client.client
        
        @require_authentication()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(instance_no_client)
        
        # 結果確認
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "この操作にはログインが必要です", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_authentication_not_logged_in(self, mock_msgbox):
        """未ログイン時のテスト"""
        # 未ログイン状態に設定
        self.mock_instance.client.is_logged_in = False
        
        @require_authentication("カスタムメッセージ", "custom_return")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "custom_return")
        mock_msgbox.assert_called_once_with(
            "カスタムメッセージ", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_client_success(self, mock_msgbox):
        """クライアントデコレータ成功のテスト"""
        @require_client()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_client_no_client(self, mock_msgbox):
        """クライアント未設定時のテスト"""
        # クライアントをNoneに設定
        self.mock_instance.client = None
        
        @require_client("カスタムエラー", "custom_return")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "custom_return")
        mock_msgbox.assert_called_once_with(
            "カスタムエラー", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_selection_success(self, mock_msgbox):
        """選択デコレータ成功のテスト"""
        @require_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_selection_no_selection(self, mock_msgbox):
        """未選択時のテスト"""
        # 選択なしに設定
        self.mock_instance.parent.timeline.get_selected_post.return_value = None
        
        @require_selection(error_message="カスタム選択エラー", return_value="custom_return")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "custom_return")
        mock_msgbox.assert_called_once_with(
            "カスタム選択エラー", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_selection_no_timeline(self, mock_msgbox):
        """タイムラインなし時のテスト"""
        # タイムラインを削除
        del self.mock_instance.parent.timeline
        
        @require_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認（タイムラインがない場合はチェックをスキップして成功）
        self.assertEqual(result, "success")
    
    def test_combine_decorators(self):
        """デコレータ組み合わせのテスト"""
        # モックデコレータを作成
        decorator1_called = False
        decorator2_called = False
        
        def mock_decorator1(func):
            def wrapper(*args, **kwargs):
                nonlocal decorator1_called
                decorator1_called = True
                return func(*args, **kwargs)
            return wrapper
        
        def mock_decorator2(func):
            def wrapper(*args, **kwargs):
                nonlocal decorator2_called
                decorator2_called = True
                return func(*args, **kwargs)
            return wrapper
        
        @combine_decorators(mock_decorator1, mock_decorator2)
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        self.assertTrue(decorator1_called)
        self.assertTrue(decorator2_called)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_auth_and_selection_success(self, mock_msgbox):
        """認証+選択デコレータ成功のテスト"""
        @require_auth_and_selection()
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        mock_msgbox.assert_not_called()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_auth_and_selection_auth_fail(self, mock_msgbox):
        """認証+選択デコレータ認証失敗のテスト"""
        # 未ログイン状態に設定
        self.mock_instance.client.is_logged_in = False
        
        @require_auth_and_selection("認証エラー", "選択エラー")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認（認証エラーが先に発生）
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "認証エラー", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_require_auth_and_selection_selection_fail(self, mock_msgbox):
        """認証+選択デコレータ選択失敗のテスト"""
        # 選択なしに設定
        self.mock_instance.parent.timeline.get_selected_post.return_value = None
        
        @require_auth_and_selection("認証エラー", "選択エラー")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認（選択エラーが発生）
        self.assertFalse(result)
        mock_msgbox.assert_called_once_with(
            "選択エラー", "エラー", unittest.mock.ANY
        )
    
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
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_custom_selection_method(self, mock_msgbox):
        """カスタム選択メソッドのテスト"""
        # カスタム選択メソッドを設定
        self.mock_instance.parent.timeline.get_custom_selection = MagicMock(return_value={'custom': 'data'})
        
        @require_selection(get_selection_method="get_custom_selection")
        def test_method(self):
            return "success"
        
        # テスト実行
        result = test_method(self.mock_instance)
        
        # 結果確認
        self.assertEqual(result, "success")
        self.mock_instance.parent.timeline.get_custom_selection.assert_called_once()
        mock_msgbox.assert_not_called()

if __name__ == '__main__':
    unittest.main()