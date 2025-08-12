#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
GUIテスト共通fixture設定
"""

import pytest
import tempfile
import threading
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from typing import Generator, Dict, Any

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def gui_test_environment():
    """GUIテスト用環境設定"""
    with tempfile.TemporaryDirectory(prefix="ssky_gui_test_") as temp_dir:
        temp_path = Path(temp_dir)
        
        environment = {
            "temp_dir": temp_path,
            "data_dir": temp_path / "data",
            "config_dir": temp_path / "config",
            "db_file": str(temp_path / "data" / "gui_test.db"),
            "config_file": str(temp_path / "config" / "gui_settings.json")
        }
        
        # ディレクトリ作成
        environment["data_dir"].mkdir()
        environment["config_dir"].mkdir()
        
        yield environment


@pytest.fixture
def comprehensive_wx_mock():
    """包括的なwxPythonモック"""
    
    # メインwxモジュール
    wx_mock = MagicMock()
    
    # 基本定数
    wx_mock.ID_EXIT = 5006
    wx_mock.ID_ABOUT = 5014
    wx_mock.ID_NEW = 5001
    wx_mock.ID_OPEN = 5002
    wx_mock.ID_SAVE = 5003
    wx_mock.ID_CLOSE = 5004
    wx_mock.ID_CUT = 5030
    wx_mock.ID_COPY = 5031
    wx_mock.ID_PASTE = 5032
    
    # ダイアログ定数
    wx_mock.OK = 2
    wx_mock.CANCEL = 8
    wx_mock.YES = 2
    wx_mock.NO = 8
    wx_mock.YES_NO = 6
    
    # アイコン定数
    wx_mock.ICON_ERROR = 512
    wx_mock.ICON_WARNING = 256
    wx_mock.ICON_INFORMATION = 64
    wx_mock.ICON_QUESTION = 128
    
    # ウィンドウスタイル定数
    wx_mock.DEFAULT_FRAME_STYLE = 541072128
    wx_mock.MINIMIZE_BOX = 1024
    wx_mock.MAXIMIZE_BOX = 2048
    wx_mock.RESIZE_BORDER = 64
    wx_mock.CLOSE_BOX = 4096
    
    # リストコントロール定数
    wx_mock.LC_REPORT = 1
    wx_mock.LC_SINGLE_SEL = 4
    wx_mock.LC_NO_HEADER = 1073741824
    
    # 色定数
    wx_mock.Colour = MagicMock()
    wx_mock.BLACK = MagicMock()
    wx_mock.WHITE = MagicMock()
    wx_mock.RED = MagicMock()
    wx_mock.BLUE = MagicMock()
    
    # App クラスモック
    app_mock = MagicMock()
    app_mock.MainLoop = MagicMock()
    app_mock.ExitMainLoop = MagicMock()
    app_mock.Destroy = MagicMock()
    app_mock.ProcessPendingEvents = MagicMock()
    wx_mock.App = MagicMock(return_value=app_mock)
    
    # Frame クラスモック
    frame_mock = MagicMock()
    frame_mock.Show = MagicMock(return_value=True)
    frame_mock.Hide = MagicMock()
    frame_mock.Close = MagicMock(return_value=True)
    frame_mock.Destroy = MagicMock()
    frame_mock.SetTitle = MagicMock()
    frame_mock.SetSize = MagicMock()
    frame_mock.SetPosition = MagicMock()
    frame_mock.Centre = MagicMock()
    frame_mock.Center = MagicMock()
    wx_mock.Frame = MagicMock(return_value=frame_mock)
    
    # Panel クラスモック
    panel_mock = MagicMock()
    panel_mock.SetBackgroundColour = MagicMock()
    panel_mock.Refresh = MagicMock()
    wx_mock.Panel = MagicMock(return_value=panel_mock)
    
    # Sizer関連モック
    sizer_mock = MagicMock()
    sizer_mock.Add = MagicMock()
    sizer_mock.AddSpacer = MagicMock()
    sizer_mock.Fit = MagicMock()
    sizer_mock.SetSizeHints = MagicMock()
    wx_mock.BoxSizer = MagicMock(return_value=sizer_mock)
    wx_mock.StaticBoxSizer = MagicMock(return_value=sizer_mock)
    wx_mock.FlexGridSizer = MagicMock(return_value=sizer_mock)
    wx_mock.VERTICAL = 8
    wx_mock.HORIZONTAL = 4
    wx_mock.ALL = 15
    wx_mock.EXPAND = 8192
    
    # コントロール類モック
    button_mock = MagicMock()
    button_mock.Bind = MagicMock()
    button_mock.SetLabel = MagicMock()
    button_mock.Enable = MagicMock()
    button_mock.Disable = MagicMock()
    wx_mock.Button = MagicMock(return_value=button_mock)
    
    text_ctrl_mock = MagicMock()
    text_ctrl_mock.GetValue = MagicMock(return_value="")
    text_ctrl_mock.SetValue = MagicMock()
    text_ctrl_mock.Clear = MagicMock()
    text_ctrl_mock.AppendText = MagicMock()
    wx_mock.TextCtrl = MagicMock(return_value=text_ctrl_mock)
    
    list_ctrl_mock = MagicMock()
    list_ctrl_mock.GetFirstSelected = MagicMock(return_value=-1)
    list_ctrl_mock.GetNextSelected = MagicMock(return_value=-1)
    list_ctrl_mock.GetItemCount = MagicMock(return_value=0)
    list_ctrl_mock.InsertItem = MagicMock(return_value=0)
    list_ctrl_mock.SetItem = MagicMock()
    list_ctrl_mock.DeleteAllItems = MagicMock()
    list_ctrl_mock.InsertColumn = MagicMock()
    wx_mock.ListCtrl = MagicMock(return_value=list_ctrl_mock)
    
    static_text_mock = MagicMock()
    static_text_mock.SetLabel = MagicMock()
    wx_mock.StaticText = MagicMock(return_value=static_text_mock)
    
    # メニュー関連モック
    menu_mock = MagicMock()
    menu_mock.Append = MagicMock()
    menu_mock.AppendSeparator = MagicMock()
    wx_mock.Menu = MagicMock(return_value=menu_mock)
    
    menu_bar_mock = MagicMock()
    menu_bar_mock.Append = MagicMock()
    wx_mock.MenuBar = MagicMock(return_value=menu_bar_mock)
    
    # ダイアログ関連モック
    wx_mock.MessageBox = MagicMock(return_value=wx_mock.OK)
    
    dialog_mock = MagicMock()
    dialog_mock.ShowModal = MagicMock(return_value=wx_mock.OK)
    dialog_mock.Destroy = MagicMock()
    wx_mock.Dialog = MagicMock(return_value=dialog_mock)
    wx_mock.MessageDialog = MagicMock(return_value=dialog_mock)
    
    # イベント関連モック
    event_mock = MagicMock()
    event_mock.GetId = MagicMock(return_value=1001)
    event_mock.Skip = MagicMock()
    wx_mock.Event = MagicMock(return_value=event_mock)
    wx_mock.CommandEvent = MagicMock(return_value=event_mock)
    wx_mock.CloseEvent = MagicMock(return_value=event_mock)
    
    # イベントタイプ定数
    wx_mock.EVT_BUTTON = MagicMock()
    wx_mock.EVT_MENU = MagicMock()
    wx_mock.EVT_CLOSE = MagicMock()
    wx_mock.EVT_TEXT = MagicMock()
    wx_mock.EVT_LIST_ITEM_SELECTED = MagicMock()
    wx_mock.EVT_LIST_ITEM_ACTIVATED = MagicMock()
    
    # Timer関連モック
    timer_mock = MagicMock()
    timer_mock.Start = MagicMock()
    timer_mock.Stop = MagicMock()
    timer_mock.IsRunning = MagicMock(return_value=False)
    wx_mock.Timer = MagicMock(return_value=timer_mock)
    wx_mock.EVT_TIMER = MagicMock()
    
    # CallAfter、CallLater
    wx_mock.CallAfter = MagicMock()
    wx_mock.CallLater = MagicMock()
    
    with patch.dict('sys.modules', {'wx': wx_mock}):
        yield {
            'wx': wx_mock,
            'app': app_mock,
            'frame': frame_mock,
            'panel': panel_mock,
            'button': button_mock,
            'text_ctrl': text_ctrl_mock,
            'list_ctrl': list_ctrl_mock,
            'static_text': static_text_mock,
            'menu': menu_mock,
            'menu_bar': menu_bar_mock,
            'dialog': dialog_mock,
            'sizer': sizer_mock,
            'timer': timer_mock,
            'event': event_mock
        }


@pytest.fixture
def gui_backend_components(gui_test_environment, comprehensive_wx_mock):
    """GUI用バックエンドコンポーネント"""
    components = {}
    
    # 環境変数設定
    os.environ['PYTEST_GUI_RUNNING'] = '1'
    
    try:
        # DataStore
        from core.data_store import DataStore
        data_store = DataStore(gui_test_environment['db_file'])
        components['data_store'] = data_store
        
        # 暗号化モック
        with patch('utils.crypto.encrypt_data') as mock_encrypt, \
             patch('utils.crypto.decrypt_data') as mock_decrypt:
            
            mock_encrypt.return_value = b'gui_encrypted_data'
            mock_decrypt.return_value = 'gui_decrypted_data'
            
            # CredentialManager
            from core.auth.credential_manager import AuthCredentialManager
            AuthCredentialManager._instance = None
            credential_manager = AuthCredentialManager()
            components['credential_manager'] = credential_manager
        
        # BlueskyClient（APIクライアントモック付き）
        with patch('core.client.api_client.AtprotoClient') as mock_atproto:
            mock_client = Mock()
            mock_atproto.return_value = mock_client
            
            # デフォルトレスポンス設定
            mock_client.get_timeline.return_value = Mock(feed=[])
            mock_client.send_post.return_value = Mock(uri="test://post/gui")
            mock_client.get_profile.return_value = {
                "did": "did:plc:guitest",
                "handle": "gui.test",
                "displayName": "GUI Test User"
            }
            
            from core.client.facade import BlueskyClient
            bluesky_client = BlueskyClient()
            components['bluesky_client'] = bluesky_client
            components['mock_api_client'] = mock_client
        
        # SettingsManager
        from config.settings_manager import SettingsManager
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.settings_file = gui_test_environment['config_file']
        components['settings_manager'] = settings_manager
        
        # wxPythonモック
        components.update(comprehensive_wx_mock)
        
        yield components
        
    finally:
        # クリーンアップ
        try:
            AuthCredentialManager._instance = None
            SettingsManager._instance = None
        except:
            pass
        
        os.environ.pop('PYTEST_GUI_RUNNING', None)


@pytest.fixture
def gui_app_instance(gui_backend_components):
    """GUIアプリケーションインスタンス"""
    
    # SSkyAppのモック
    with patch('gui.app.SSkyApp') as mock_app_class:
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app
        
        # アプリの基本メソッド
        mock_app.MainLoop = MagicMock()
        mock_app.ExitMainLoop = MagicMock()
        mock_app.Destroy = MagicMock()
        mock_app.ProcessPendingEvents = MagicMock()
        
        # メインフレーム
        mock_main_frame = MagicMock()
        mock_app.main_frame = mock_main_frame
        
        yield {
            'app_class': mock_app_class,
            'app': mock_app,
            'main_frame': mock_main_frame
        }


@pytest.fixture
def gui_main_frame_mock(gui_backend_components, gui_app_instance):
    """メインフレームモック"""
    
    # MainFrameクラスのモック
    with patch('gui.main_frame.MainFrame') as mock_frame_class:
        mock_frame = MagicMock()
        mock_frame_class.return_value = mock_frame
        
        # フレームの基本プロパティ
        mock_frame.timeline_view = MagicMock()
        mock_frame.status_bar = MagicMock()
        mock_frame.menu_bar = MagicMock()
        
        # フレームメソッド
        mock_frame.Show = MagicMock(return_value=True)
        mock_frame.Hide = MagicMock()
        mock_frame.Close = MagicMock(return_value=True)
        mock_frame.Destroy = MagicMock()
        mock_frame.SetTitle = MagicMock()
        mock_frame.UpdateAuthStatus = MagicMock()
        mock_frame.RefreshTimeline = MagicMock()
        
        # イベントハンドラ
        mock_frame.OnLogin = MagicMock()
        mock_frame.OnLogout = MagicMock()
        mock_frame.OnPost = MagicMock()
        mock_frame.OnRefresh = MagicMock()
        mock_frame.OnSettings = MagicMock()
        mock_frame.OnExit = MagicMock()
        
        yield {
            'frame_class': mock_frame_class,
            'frame': mock_frame,
            'timeline_view': mock_frame.timeline_view
        }


@pytest.fixture
def gui_dialog_mocks(gui_backend_components):
    """GUIダイアログモック集"""
    
    mocks = {}
    
    # ログインダイアログ
    with patch('gui.dialogs.login_dialog.LoginDialog') as mock_login_class:
        mock_login = MagicMock()
        mock_login_class.return_value = mock_login
        mock_login.ShowModal.return_value = gui_backend_components['wx'].OK
        mock_login.GetCredentials.return_value = ("test.user", "test_password")
        mocks['login_dialog'] = mock_login
        mocks['login_dialog_class'] = mock_login_class
    
    # 投稿ダイアログ
    with patch('gui.dialogs.post_dialog.PostDialog') as mock_post_class:
        mock_post = MagicMock()
        mock_post_class.return_value = mock_post
        mock_post.ShowModal.return_value = gui_backend_components['wx'].OK
        mock_post.GetPostContent.return_value = "Test post content"
        mock_post.GetSelectedImages.return_value = []
        mocks['post_dialog'] = mock_post
        mocks['post_dialog_class'] = mock_post_class
    
    # 設定ダイアログ
    with patch('gui.dialogs.settings_dialog.SettingsDialog') as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        mock_settings.ShowModal.return_value = gui_backend_components['wx'].OK
        mock_settings.GetSettings.return_value = {
            "timeline_refresh_interval": 30,
            "max_posts_display": 100
        }
        mocks['settings_dialog'] = mock_settings
        mocks['settings_dialog_class'] = mock_settings_class
    
    # エラーダイアログ
    with patch('gui.dialogs.error_dialog.ErrorDialog') as mock_error_class:
        mock_error = MagicMock()
        mock_error_class.return_value = mock_error
        mock_error.ShowModal.return_value = gui_backend_components['wx'].OK
        mocks['error_dialog'] = mock_error
        mocks['error_dialog_class'] = mock_error_class
    
    yield mocks


@pytest.fixture
def gui_timeline_mock(gui_backend_components):
    """タイムラインビューモック"""
    
    # TimelineViewクラスのモック
    with patch('gui.timeline.timeline_view.TimelineView') as mock_timeline_class:
        mock_timeline = MagicMock()
        mock_timeline_class.return_value = mock_timeline
        
        # タイムラインの基本プロパティ
        mock_timeline.timeline_list = MagicMock()
        mock_timeline.refresh_timer = MagicMock()
        mock_timeline.is_auto_refresh_enabled = False
        
        # タイムラインメソッド
        mock_timeline.UpdateTimeline = MagicMock()
        mock_timeline.ClearTimeline = MagicMock()
        mock_timeline.AddPost = MagicMock()
        mock_timeline.RemovePost = MagicMock()
        mock_timeline.GetSelectedPost = MagicMock(return_value=None)
        mock_timeline.StartAutoRefresh = MagicMock()
        mock_timeline.StopAutoRefresh = MagicMock()
        mock_timeline.RefreshNow = MagicMock()
        
        # リストコントロール関連
        list_ctrl_mock = gui_backend_components['list_ctrl']
        mock_timeline.timeline_list = list_ctrl_mock
        
        yield {
            'timeline_class': mock_timeline_class,
            'timeline': mock_timeline,
            'list_ctrl': list_ctrl_mock
        }


@pytest.fixture
def gui_accessibility_mock():
    """アクセシビリティ機能モック"""
    
    accessibility_mock = MagicMock()
    
    # スクリーンリーダー対応
    accessibility_mock.announce_text = MagicMock()
    accessibility_mock.set_focus_description = MagicMock()
    accessibility_mock.enable_keyboard_navigation = MagicMock()
    
    # キーボードショートカット
    accessibility_mock.register_shortcut = MagicMock()
    accessibility_mock.unregister_shortcut = MagicMock()
    accessibility_mock.handle_shortcut = MagicMock()
    
    # 高コントラストテーマ
    accessibility_mock.apply_high_contrast = MagicMock()
    accessibility_mock.restore_normal_contrast = MagicMock()
    
    # フォントサイズ調整
    accessibility_mock.increase_font_size = MagicMock()
    accessibility_mock.decrease_font_size = MagicMock()
    accessibility_mock.reset_font_size = MagicMock()
    
    yield accessibility_mock


@pytest.fixture
def gui_event_simulation():
    """GUIイベントシミュレーション"""
    
    class EventSimulator:
        def __init__(self, wx_mock):
            self.wx = wx_mock
            self.event_handlers = {}
        
        def register_handler(self, event_type, handler):
            """イベントハンドラ登録"""
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
        
        def simulate_button_click(self, button_id):
            """ボタンクリックシミュレーション"""
            event = MagicMock()
            event.GetId.return_value = button_id
            
            if 'button_click' in self.event_handlers:
                for handler in self.event_handlers['button_click']:
                    handler(event)
            
            return event
        
        def simulate_menu_select(self, menu_id):
            """メニュー選択シミュレーション"""
            event = MagicMock()
            event.GetId.return_value = menu_id
            
            if 'menu_select' in self.event_handlers:
                for handler in self.event_handlers['menu_select']:
                    handler(event)
            
            return event
        
        def simulate_text_input(self, text_ctrl, text):
            """テキスト入力シミュレーション"""
            text_ctrl.SetValue(text)
            
            event = MagicMock()
            event.GetString.return_value = text
            
            if 'text_input' in self.event_handlers:
                for handler in self.event_handlers['text_input']:
                    handler(event)
            
            return event
        
        def simulate_window_close(self):
            """ウィンドウクローズシミュレーション"""
            event = MagicMock()
            event.CanVeto.return_value = True
            event.Veto = MagicMock()
            
            if 'window_close' in self.event_handlers:
                for handler in self.event_handlers['window_close']:
                    handler(event)
            
            return event
        
        def simulate_list_selection(self, list_ctrl, index):
            """リスト選択シミュレーション"""
            list_ctrl.GetFirstSelected.return_value = index
            
            event = MagicMock()
            event.GetIndex.return_value = index
            
            if 'list_select' in self.event_handlers:
                for handler in self.event_handlers['list_select']:
                    handler(event)
            
            return event
        
        def simulate_timer_event(self, timer_id):
            """タイマーイベントシミュレーション"""
            event = MagicMock()
            event.GetId.return_value = timer_id
            
            if 'timer' in self.event_handlers:
                for handler in self.event_handlers['timer']:
                    handler(event)
            
            return event
    
    yield EventSimulator


@pytest.fixture
def gui_test_data():
    """GUIテスト用サンプルデータ"""
    return {
        "sample_posts": [
            {
                "uri": "at://gui.test/app.bsky.feed.post/1",
                "cid": "gui_test_cid_1",
                "author": {
                    "did": "did:plc:guitest1",
                    "handle": "gui.test1",
                    "displayName": "GUIテストユーザー1"
                },
                "record": {
                    "text": "GUIテスト用投稿1",
                    "createdAt": "2024-01-01T12:00:00.000Z"
                },
                "indexedAt": "2024-01-01T12:00:01.000Z"
            },
            {
                "uri": "at://gui.test/app.bsky.feed.post/2",
                "cid": "gui_test_cid_2",
                "author": {
                    "did": "did:plc:guitest2",
                    "handle": "gui.test2",
                    "displayName": "GUIテストユーザー2"
                },
                "record": {
                    "text": "GUIテスト用投稿2\n#テスト #GUI",
                    "createdAt": "2024-01-01T11:30:00.000Z"
                },
                "indexedAt": "2024-01-01T11:30:01.000Z"
            }
        ],
        "test_credentials": {
            "handle": "gui.testuser",
            "password": "gui_test_password_123"
        },
        "test_post_content": "GUIテストからの投稿です",
        "test_settings": {
            "timeline_refresh_interval": 45,
            "max_posts_display": 150,
            "theme": "dark",
            "enable_sound": True
        }
    }


# pytest設定フック
def pytest_configure(config):
    """GUIテスト固有の設定"""
    config.addinivalue_line("markers", "gui_smoke: GUI smoke tests")
    config.addinivalue_line("markers", "gui_integration: GUI integration tests")
    config.addinivalue_line("markers", "gui_accessibility: GUI accessibility tests")
    config.addinivalue_line("markers", "gui_dialog: GUI dialog tests")
    config.addinivalue_line("markers", "gui_timeline: GUI timeline tests")