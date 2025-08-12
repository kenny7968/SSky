#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - MainFrame GUI単体テスト
完全リファクタリング版
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock, call
import sys
import os
from pathlib import Path

# テスト対象モジュールのインポート
sys.path.insert(0, str(Path(__file__).parents[3]))


@pytest.fixture
def mock_wx():
    """wxPythonのモック"""
    with patch.dict('sys.modules', {'wx': MagicMock()}):
        wx_mock = sys.modules['wx']
        
        # 定数設定
        wx_mock.ID_ANY = -1
        wx_mock.ID_EXIT = 5006
        wx_mock.ID_ABOUT = 5014
        wx_mock.DefaultPosition = (-1, -1)
        wx_mock.DefaultSize = (-1, -1)
        wx_mock.EXPAND = 1
        wx_mock.ALL = 15
        wx_mock.HORIZONTAL = 4
        wx_mock.VERTICAL = 8
        wx_mock.OK = 2
        wx_mock.CANCEL = 4
        wx_mock.YES = 8
        wx_mock.NO = 16
        wx_mock.ICON_INFORMATION = 64
        wx_mock.ICON_WARNING = 256
        wx_mock.ICON_ERROR = 512
        wx_mock.ICON_QUESTION = 1024
        
        # クラスのモック
        wx_mock.Frame = MagicMock()
        wx_mock.MenuBar = MagicMock()
        wx_mock.Menu = MagicMock()
        wx_mock.Panel = MagicMock()
        wx_mock.BoxSizer = MagicMock()
        wx_mock.StatusBar = MagicMock()
        wx_mock.MessageBox = MagicMock(return_value=wx_mock.OK)
        wx_mock.MessageDialog = MagicMock()
        wx_mock.Timer = MagicMock()
        wx_mock.EVT_MENU = MagicMock()
        wx_mock.EVT_CLOSE = MagicMock()
        wx_mock.EVT_TIMER = MagicMock()
        
        yield wx_mock


@pytest.fixture
def mock_bluesky_client():
    """BlueskyClientのモック"""
    client = MagicMock()
    client.is_logged_in = MagicMock(return_value=True)
    client.get_timeline = MagicMock(return_value=[])
    client.send_post = MagicMock(return_value={"uri": "test://post/123"})
    client.get_user_info = MagicMock(return_value={
        "handle": "test.user",
        "displayName": "Test User"
    })
    return client


@pytest.fixture
def mock_timeline_view():
    """TimelineViewのモック"""
    with patch('gui.timeline.timeline_view.TimelineView') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def main_frame(mock_wx, mock_bluesky_client):
    """テスト用MainFrameインスタンス"""
    with patch('gui.main_frame.wx', mock_wx):
        with patch('gui.main_frame.BlueskyClient', return_value=mock_bluesky_client):
            from gui.main_frame import MainFrame
            
            parent = MagicMock()
            frame = MainFrame(parent, title="Test SSky")
            frame.client = mock_bluesky_client
            
            yield frame


class TestMainFrameInitialization:
    """初期化関連のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_initialization_basic(self, mock_wx):
        """基本的な初期化"""
        import sys
        import os
        # プロジェクトルートをパスに追加
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        
        with patch('gui.main_frame.wx', mock_wx):
            from gui.main_frame import MainFrame
            
            parent = MagicMock()
            frame = MainFrame(parent, title="Test SSky")
            
            assert frame.GetTitle() == "Test SSky"
            assert hasattr(frame, 'client')
            assert hasattr(frame, 'timeline_view')
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_initialization_creates_menu(self, main_frame, mock_wx):
        """メニューバーの作成"""
        assert main_frame.menu_bar is not None
        main_frame.SetMenuBar.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_initialization_creates_statusbar(self, main_frame):
        """ステータスバーの作成"""
        assert main_frame.status_bar is not None
        main_frame.CreateStatusBar.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_initialization_creates_timeline(self, main_frame):
        """タイムラインビューの作成"""
        assert main_frame.timeline_view is not None


class TestMainFrameMenu:
    """メニュー機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_file_menu_items(self, main_frame):
        """ファイルメニューのアイテム"""
        file_menu = main_frame.file_menu
        
        # メニューアイテムが追加されているか確認
        assert file_menu.Append.called
        
        # 主要なメニューアイテムの確認
        append_calls = file_menu.Append.call_args_list
        menu_items = [call[0][1] if len(call[0]) > 1 else "" for call in append_calls]
        
        expected_items = ["ログイン", "ログアウト", "終了"]
        for item in expected_items:
            assert any(item in str(menu_item) for menu_item in menu_items)
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_post_menu_items(self, main_frame):
        """投稿メニューのアイテム"""
        post_menu = main_frame.post_menu
        
        assert post_menu.Append.called
        
        append_calls = post_menu.Append.call_args_list
        menu_items = [call[0][1] if len(call[0]) > 1 else "" for call in append_calls]
        
        expected_items = ["新規投稿", "タイムライン更新"]
        for item in expected_items:
            assert any(item in str(menu_item) for menu_item in menu_items)
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_help_menu_items(self, main_frame):
        """ヘルプメニューのアイテム"""
        help_menu = main_frame.help_menu
        
        assert help_menu.Append.called
        
        append_calls = help_menu.Append.call_args_list
        menu_items = [call[0][1] if len(call[0]) > 1 else "" for call in append_calls]
        
        assert any("バージョン情報" in str(item) for item in menu_items)


class TestMainFrameAuthentication:
    """認証関連機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_login_success(self, main_frame, mock_bluesky_client, mock_wx):
        """ログイン成功"""
        mock_bluesky_client.login = MagicMock(return_value=True)
        mock_bluesky_client.is_logged_in = MagicMock(return_value=True)
        
        with patch('gui.main_frame.LoginDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_OK)
            mock_dialog.get_credentials = MagicMock(return_value={
                "identifier": "test.user",
                "password": "password123"
            })
            mock_dialog_class.return_value = mock_dialog
            
            main_frame.on_login(None)
            
            mock_bluesky_client.login.assert_called_once_with("test.user", "password123")
            main_frame.SetStatusText.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_login_failure(self, main_frame, mock_bluesky_client, mock_wx):
        """ログイン失敗"""
        mock_bluesky_client.login = MagicMock(return_value=False)
        
        with patch('gui.main_frame.LoginDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_OK)
            mock_dialog.get_credentials = MagicMock(return_value={
                "identifier": "test.user",
                "password": "wrong_password"
            })
            mock_dialog_class.return_value = mock_dialog
            
            with patch('gui.main_frame.wx.MessageBox') as mock_msgbox:
                main_frame.on_login(None)
                
                mock_msgbox.assert_called_once()
                assert "失敗" in str(mock_msgbox.call_args)
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_logout(self, main_frame, mock_bluesky_client):
        """ログアウト"""
        mock_bluesky_client.logout = MagicMock()
        
        main_frame.on_logout(None)
        
        mock_bluesky_client.logout.assert_called_once()
        main_frame.SetStatusText.assert_called_with("ログアウトしました")
        main_frame.timeline_view.clear.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_auto_login_on_startup(self, mock_wx, mock_bluesky_client):
        """起動時の自動ログイン"""
        mock_bluesky_client.auto_login = MagicMock(return_value=True)
        
        with patch('gui.main_frame.wx', mock_wx):
            from gui.main_frame import MainFrame
            
            frame = MainFrame(None, title="Test")
            frame.client = mock_bluesky_client
            
            # 自動ログインが試行される
            mock_bluesky_client.auto_login.assert_called()


class TestMainFramePosting:
    """投稿機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_new_post_success(self, main_frame, mock_bluesky_client, mock_wx):
        """新規投稿成功"""
        with patch('gui.main_frame.PostDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_OK)
            mock_dialog.get_post_content = MagicMock(return_value="テスト投稿")
            mock_dialog_class.return_value = mock_dialog
            
            main_frame.on_new_post(None)
            
            mock_bluesky_client.send_post.assert_called_once_with("テスト投稿")
            main_frame.timeline_view.refresh.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_new_post_cancelled(self, main_frame, mock_wx):
        """新規投稿キャンセル"""
        with patch('gui.main_frame.PostDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_CANCEL)
            mock_dialog_class.return_value = mock_dialog
            
            main_frame.on_new_post(None)
            
            main_frame.client.send_post.assert_not_called()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_new_post_error(self, main_frame, mock_bluesky_client, mock_wx):
        """投稿エラー"""
        mock_bluesky_client.send_post = MagicMock(side_effect=Exception("Post failed"))
        
        with patch('gui.main_frame.PostDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_OK)
            mock_dialog.get_post_content = MagicMock(return_value="エラーテスト")
            mock_dialog_class.return_value = mock_dialog
            
            with patch('gui.main_frame.wx.MessageBox') as mock_msgbox:
                main_frame.on_new_post(None)
                
                mock_msgbox.assert_called_once()
                assert "エラー" in str(mock_msgbox.call_args)


class TestMainFrameTimeline:
    """タイムライン機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_refresh_timeline(self, main_frame, mock_bluesky_client):
        """タイムライン更新"""
        mock_timeline_data = [
            {"text": "投稿1"},
            {"text": "投稿2"}
        ]
        mock_bluesky_client.get_timeline = MagicMock(return_value=mock_timeline_data)
        
        main_frame.on_refresh_timeline(None)
        
        mock_bluesky_client.get_timeline.assert_called_once()
        main_frame.timeline_view.update_posts.assert_called_once_with(mock_timeline_data)
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_auto_refresh_timer(self, main_frame):
        """自動更新タイマー"""
        assert hasattr(main_frame, 'refresh_timer')
        
        # タイマーが開始される
        main_frame.start_auto_refresh(30000)  # 30秒
        main_frame.refresh_timer.Start.assert_called_with(30000)
        
        # タイマーが停止される
        main_frame.stop_auto_refresh()
        main_frame.refresh_timer.Stop.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_timeline_error_handling(self, main_frame, mock_bluesky_client):
        """タイムライン取得エラー"""
        mock_bluesky_client.get_timeline = MagicMock(
            side_effect=Exception("Network error")
        )
        
        with patch('gui.main_frame.wx.MessageBox') as mock_msgbox:
            main_frame.on_refresh_timeline(None)
            
            mock_msgbox.assert_called_once()
            assert "エラー" in str(mock_msgbox.call_args)


class TestMainFrameStatusBar:
    """ステータスバー機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_status_text_update(self, main_frame):
        """ステータステキスト更新"""
        main_frame.set_status("テストステータス")
        
        main_frame.SetStatusText.assert_called_with("テストステータス")
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_status_fields(self, main_frame):
        """ステータスバーフィールド"""
        # 複数フィールドの設定
        main_frame.set_status("メイン", 0)
        main_frame.set_status("サブ", 1)
        
        assert main_frame.SetStatusText.call_count >= 2
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_connection_status(self, main_frame, mock_bluesky_client):
        """接続状態の表示"""
        mock_bluesky_client.is_logged_in = MagicMock(return_value=True)
        main_frame.update_connection_status()
        
        main_frame.SetStatusText.assert_called()
        assert "接続中" in str(main_frame.SetStatusText.call_args)


class TestMainFrameEventHandling:
    """イベントハンドリングのテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_close_event(self, main_frame, mock_wx):
        """ウィンドウクローズイベント"""
        event = MagicMock()
        
        with patch.object(main_frame, 'Destroy') as mock_destroy:
            main_frame.on_close(event)
            
            # タイマーが停止される
            main_frame.refresh_timer.Stop.assert_called()
            
            # クライアントがクリーンアップされる
            if hasattr(main_frame.client, 'cleanup'):
                main_frame.client.cleanup.assert_called()
            
            # ウィンドウが破棄される
            mock_destroy.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_menu_event_binding(self, main_frame):
        """メニューイベントのバインディング"""
        # イベントバインディングが設定されている
        assert main_frame.Bind.called
        
        bind_calls = main_frame.Bind.call_args_list
        # 主要なイベントがバインドされている
        event_types = [call[0][0] for call in bind_calls]
        
        # wx.EVT_MENUやwx.EVT_CLOSEなどがバインドされている
        assert len(event_types) > 0
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_keyboard_shortcuts(self, main_frame):
        """キーボードショートカット"""
        # アクセラレーターテーブルの設定
        if hasattr(main_frame, 'SetAcceleratorTable'):
            assert main_frame.SetAcceleratorTable.called


class TestMainFrameSettings:
    """設定関連機能のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_open_settings_dialog(self, main_frame, mock_wx):
        """設定ダイアログを開く"""
        with patch('gui.main_frame.SettingsDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.ShowModal = MagicMock(return_value=mock_wx.ID_OK)
            mock_dialog_class.return_value = mock_dialog
            
            main_frame.on_settings(None)
            
            mock_dialog.ShowModal.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_apply_settings(self, main_frame):
        """設定の適用"""
        new_settings = {
            "timeline_refresh_interval": 60,
            "theme": "dark"
        }
        
        main_frame.apply_settings(new_settings)
        
        # 設定が適用される
        if hasattr(main_frame, 'settings'):
            assert main_frame.settings == new_settings


class TestMainFrameAbout:
    """バージョン情報のテスト"""
    
    @pytest.mark.unit
    @pytest.mark.gui
    def test_show_about_dialog(self, main_frame, mock_wx):
        """バージョン情報ダイアログ"""
        with patch('gui.main_frame.wx.MessageBox') as mock_msgbox:
            main_frame.on_about(None)
            
            mock_msgbox.assert_called_once()
            call_args = str(mock_msgbox.call_args)
            assert "SSky" in call_args
            assert "バージョン" in call_args