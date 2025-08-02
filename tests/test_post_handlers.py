#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿関連イベントハンドラのテスト
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import wx

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.handlers.post_handlers import PostHandlers
from core import events

class TestPostHandlers(unittest.TestCase):
    """PostHandlersのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 親ウィンドウのモックを作成
        self.mock_parent = MagicMock()
        self.mock_parent.statusbar = MagicMock()
        self.mock_parent.timeline = MagicMock()
        self.mock_parent.settings_manager = MagicMock()
        
        # クライアントのモックを作成
        self.mock_client = MagicMock()
        self.mock_client.is_logged_in = True
        self.mock_client.reply_to_post.return_value = {'uri': 'reply_uri'}
        self.mock_client.quote_post.return_value = {'uri': 'quote_uri'}
        self.mock_client.get_profile.return_value = {'handle': 'test_user'}
        self.mock_client.delete_post.return_value = True
        
        # 選択された投稿のモックデータ
        self.mock_selected_post = {
            'uri': 'test_uri',
            'cid': 'test_cid',
            'username': 'test_user',
            'author_handle': 'test_user.bsky.social',
            'is_own_post': False
        }
        
        # タイムラインのget_selected_postメソッドの設定
        self.mock_parent.timeline.get_selected_post.return_value = self.mock_selected_post
        
        # PostHandlersのインスタンス作成（認証デコレータ対応）
        self.post_handlers = PostHandlers(self.mock_parent, self.mock_client)
        
        # デコレータで使用されるclient属性を確実に設定
        self.post_handlers.client = self.mock_client
        
        # クラス変数をリセット
        PostHandlers._liking_post = False
        PostHandlers._deleting_post = False
        PostHandlers._reposting_post = False
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('utils.error_handler.ErrorHandler.handle_error')
    @patch('utils.error_handler.ErrorHandler.update_status_bar')
    @patch('gui.handlers.post_handlers.PostDialog')
    @patch('gui.handlers.post_handlers.pub')
    @patch('gui.handlers.post_handlers.AsyncPostHandler')
    def test_on_new_post_success(self, mock_async_handler, mock_pub, mock_dialog, mock_update_status, mock_handle_error, mock_msgbox):
        """新規投稿成功のテスト"""
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_OK
        mock_dlg.get_post_data.return_value = ("テスト投稿", None)
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        self.post_handlers.on_new_post(MagicMock())
        
        # ダイアログが表示されることを確認
        mock_dialog.assert_called_once_with(self.mock_parent)
        mock_dlg.ShowModal.assert_called_once()
        
        # 非同期投稿処理が呼ばれることを確認
        mock_async_handler.submit_post.assert_called_once_with(self.mock_client, "テスト投稿", None)
        
        # イベント購読が設定されることを確認
        self.assertGreaterEqual(mock_pub.subscribe.call_count, 2)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.PostDialog')
    def test_on_new_post_not_logged_in(self, mock_dialog, mock_msgbox):
        """未ログイン時の新規投稿テスト"""
        # クライアントのログイン状態を変更
        self.mock_client.is_logged_in = False
        
        # テスト実行
        result = self.post_handlers.on_new_post(MagicMock())
        
        # 認証デコレータによりFalseが返されることを確認
        self.assertFalse(result)
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "投稿するにはログインしてください", "エラー", unittest.mock.ANY
        )
        
        # ダイアログが表示されないことを確認
        mock_dialog.assert_not_called()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.PostDialog')
    def test_on_new_post_empty_content(self, mock_dialog, mock_auth_msgbox):
        """空の投稿内容のテスト"""
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_OK
        mock_dlg.get_post_data.return_value = ("", None)  # 空の投稿内容
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
            self.post_handlers.on_new_post(MagicMock())
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "投稿内容を入力してください", "エラー", wx.OK | wx.ICON_ERROR
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.pub')
    @patch('gui.handlers.post_handlers.AsyncPostHandler')
    def test_on_like_success(self, mock_async_handler, mock_pub, mock_msgbox):
        """いいね成功のテスト"""
        # テスト実行
        result = self.post_handlers.on_like(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # 非同期いいね処理が呼ばれることを確認
        mock_async_handler.like_post.assert_called_once_with(
            self.mock_client, 'test_uri', 'test_cid'
        )
        
        # いいね処理中フラグが設定されることを確認
        self.assertTrue(PostHandlers._liking_post)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_like_no_selection(self, mock_msgbox):
        """投稿未選択時のいいねテスト"""
        # 選択された投稿をNoneに設定
        self.mock_parent.timeline.get_selected_post.return_value = None
        
        # テスト実行
        result = self.post_handlers.on_like(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
        
        # エラーメッセージが表示されることを確認（デコレータから）
        mock_msgbox.assert_called_once()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_like_already_processing(self, mock_msgbox):
        """いいね処理中の二重実行防止テスト"""
        # いいね処理中フラグを設定
        PostHandlers._liking_post = True
        
        # テスト実行
        result = self.post_handlers.on_like(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.ReplyDialog')
    def test_on_reply_success(self, mock_dialog, mock_msgbox):
        """返信成功のテスト"""
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_OK
        mock_dlg.get_reply_data.return_value = ("返信内容", self.mock_selected_post)
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        with patch('gui.handlers.post_handlers.run_delayed'):
            result = self.post_handlers.on_reply(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # クライアントの返信メソッドが呼ばれることを確認
        self.mock_client.reply_to_post.assert_called_once_with("返信内容", self.mock_selected_post)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_reply_no_selection(self, mock_msgbox):
        """投稿未選択時の返信テスト"""
        # 選択された投稿をNoneに設定
        self.mock_parent.timeline.get_selected_post.return_value = None
        
        # テスト実行
        result = self.post_handlers.on_reply(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
        
        # エラーメッセージが表示されることを確認（デコレータから）
        mock_msgbox.assert_called_once()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.QuoteDialog')
    def test_on_quote_success(self, mock_dialog, mock_msgbox):
        """引用成功のテスト"""
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_OK
        mock_dlg.get_quote_data.return_value = ("引用コメント", self.mock_selected_post)
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        with patch('gui.handlers.post_handlers.run_delayed'):
            result = self.post_handlers.on_quote(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # クライアントの引用メソッドが呼ばれることを確認
        self.mock_client.quote_post.assert_called_once_with("引用コメント", self.mock_selected_post)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.pub')
    @patch('gui.handlers.post_handlers.AsyncPostHandler')
    @patch('gui.handlers.post_handlers.wx.MessageDialog')
    def test_on_repost_success(self, mock_dialog, mock_async_handler, mock_pub, mock_auth_msgbox):
        """リポスト成功のテスト"""
        # 確認ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_YES
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        result = self.post_handlers.on_repost(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # 確認ダイアログが表示されることを確認
        mock_dialog.assert_called_once()
        
        # 非同期リポスト処理が呼ばれることを確認
        mock_async_handler.repost.assert_called_once()
        
        # リポスト処理中フラグが設定されることを確認
        self.assertTrue(PostHandlers._reposting_post)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_repost_own_post(self, mock_msgbox):
        """自分の投稿のリポスト防止テスト"""
        # 自分の投稿に設定
        self.mock_selected_post['is_own_post'] = True
        
        # テスト実行
        result = self.post_handlers.on_repost(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "自分の投稿はリポストできません", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_repost_already_processing(self, mock_msgbox):
        """リポスト処理中の二重実行防止テスト"""
        # リポスト処理中フラグを設定
        PostHandlers._reposting_post = True
        
        # テスト実行
        result = self.post_handlers.on_repost(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.ProfileDialog')
    def test_on_profile_success(self, mock_dialog, mock_msgbox):
        """プロフィール表示成功のテスト"""
        # ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        result = self.post_handlers.on_profile(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # クライアントのプロフィール取得メソッドが呼ばれることを確認
        self.mock_client.get_profile.assert_called_once_with('test_user.bsky.social')
        
        # ダイアログが表示されることを確認
        mock_dialog.assert_called_once()
        mock_dlg.ShowModal.assert_called_once()
    
    @patch('utils.auth_decorators.wx.MessageBox')
    @patch('gui.handlers.post_handlers.wx.MessageDialog')
    def test_on_delete_success(self, mock_dialog, mock_auth_msgbox):
        """投稿削除成功のテスト"""
        # 自分の投稿に設定
        self.mock_selected_post['is_own_post'] = True
        
        # 確認ダイアログのモック設定
        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = wx.ID_YES
        mock_dialog.return_value = mock_dlg
        
        # テスト実行
        with patch('gui.handlers.post_handlers.run_delayed'):
            with patch('gui.handlers.post_handlers.wx.MessageBox'):
                result = self.post_handlers.on_delete(MagicMock())
        
        # 成功を確認
        self.assertTrue(result)
        
        # クライアントの削除メソッドが呼ばれることを確認
        self.mock_client.delete_post.assert_called_once_with('test_uri')
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_delete_not_own_post(self, mock_msgbox):
        """他人の投稿の削除防止テスト"""
        # 他人の投稿に設定
        self.mock_selected_post['is_own_post'] = False
        
        # テスト実行
        result = self.post_handlers.on_delete(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "自分の投稿のみ削除できます", "エラー", unittest.mock.ANY
        )
    
    @patch('utils.auth_decorators.wx.MessageBox')
    def test_on_delete_already_processing(self, mock_msgbox):
        """削除処理中の二重実行防止テスト"""
        # 削除処理中フラグを設定
        PostHandlers._deleting_post = True
        
        # テスト実行
        result = self.post_handlers.on_delete(MagicMock())
        
        # 失敗を確認
        self.assertFalse(result)
    
    def test_show_completion_dialog_enabled(self):
        """完了ダイアログ表示（有効）のテスト"""
        # 設定マネージャーのモック設定
        self.mock_parent.settings_manager.get.return_value = True
        
        # テスト実行
        with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
            result = self.post_handlers.show_completion_dialog("テストメッセージ", "テストタイトル")
        
        # ダイアログが表示されることを確認
        self.assertTrue(result)
        mock_msgbox.assert_called_once_with(
            "テストメッセージ", "テストタイトル", wx.OK | wx.ICON_INFORMATION
        )
    
    def test_show_completion_dialog_disabled(self):
        """完了ダイアログ表示（無効）のテスト"""
        # 設定マネージャーのモック設定
        self.mock_parent.settings_manager.get.return_value = False
        
        # テスト実行
        with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
            result = self.post_handlers.show_completion_dialog("テストメッセージ", "テストタイトル")
        
        # ダイアログが表示されないことを確認
        self.assertFalse(result)
        mock_msgbox.assert_not_called()
        
        # ステータスバーが更新されることを確認
        self.mock_parent.statusbar.SetStatusText.assert_called_with("テストメッセージ")
    
    def test_post_submit_success_handler(self):
        """投稿成功イベントハンドラのテスト"""
        # テスト実行
        with patch('gui.handlers.post_handlers.pub') as mock_pub:
            with patch('gui.handlers.post_handlers.run_delayed'):
                self.post_handlers._on_post_submit_success({'uri': 'test_uri'})
        
        # イベント購読が解除されることを確認
        self.assertGreaterEqual(mock_pub.unsubscribe.call_count, 2)
        
        # ステータスバーが更新されることを確認
        self.mock_parent.statusbar.SetStatusText.assert_called_with("投稿が完了しました")
    
    def test_post_submit_failure_handler(self):
        """投稿失敗イベントハンドラのテスト"""
        # テスト実行
        with patch('gui.handlers.post_handlers.pub') as mock_pub:
            with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
                self.post_handlers._on_post_submit_failure(Exception("テストエラー"))
        
        # イベント購読が解除されることを確認
        self.assertGreaterEqual(mock_pub.unsubscribe.call_count, 2)
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once()
        
        # ステータスバーが更新されることを確認
        self.mock_parent.statusbar.SetStatusText.assert_called_with("投稿に失敗しました")
    
    def test_like_success_handler(self):
        """いいね成功イベントハンドラのテスト"""
        # テスト実行
        with patch('gui.handlers.post_handlers.pub') as mock_pub:
            with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
                with patch('gui.handlers.post_handlers.run_delayed'):
                    self.post_handlers._on_like_success({'uri': 'like_uri'}, 'test_uri')
        
        # フラグがリセットされることを確認
        self.assertFalse(PostHandlers._liking_post)
        
        # 成功メッセージが表示されることを確認
        mock_msgbox.assert_called_once_with(
            "投稿にいいねしました", "いいね", wx.OK | wx.ICON_INFORMATION
        )
    
    def test_like_failure_handler(self):
        """いいね失敗イベントハンドラのテスト"""
        # フラグを設定
        PostHandlers._liking_post = True
        
        # テスト実行
        with patch('gui.handlers.post_handlers.pub') as mock_pub:
            with patch('gui.handlers.post_handlers.wx.MessageBox') as mock_msgbox:
                self.post_handlers._on_like_failure(Exception("いいねエラー"), 'test_uri')
        
        # フラグがリセットされることを確認
        self.assertFalse(PostHandlers._liking_post)
        
        # エラーメッセージが表示されることを確認
        mock_msgbox.assert_called_once()

if __name__ == '__main__':
    unittest.main()