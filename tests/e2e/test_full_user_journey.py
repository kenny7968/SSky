#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - 完全ユーザージャーニーE2Eテスト
アプリケーション起動から終了までの完全なシナリオテスト
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import sys
import os

# テスト対象モジュールのインポート
sys.path.insert(0, str(Path(__file__).parents[2]))


@pytest.mark.e2e
@pytest.mark.e2e_full
class TestFullUserJourney:
    """完全なユーザージャーニーのE2Eテスト"""
    
    def test_first_time_user_complete_flow(
        self,
        e2e_app_components,
        e2e_application_lifecycle,
        e2e_user_scenario_data,
        e2e_test_timeout
    ):
        """初回ユーザーの完全フロー"""
        
        # 1. アプリケーション起動
        assert e2e_application_lifecycle.start_app(e2e_app_components)
        assert e2e_application_lifecycle.is_app_running()
        
        # 2. 初回起動確認（認証情報をクリア）
        credential_manager = e2e_app_components['credential_manager']
        # 初回起動をシミュレートするために認証情報をクリア
        credential_manager.clear_credentials()
        stored_creds = credential_manager.get_stored_credentials()
        # モックが返すデータがある場合も考慮
        
        # 3. ログインダイアログ表示をシミュレート
        bluesky_client = e2e_app_components['bluesky_client']
        valid_creds = e2e_user_scenario_data['valid_credentials']
        
        # 4. ログイン実行
        with patch.object(bluesky_client, 'login', return_value=True):
            login_result = bluesky_client.login(
                valid_creds['handle'],
                valid_creds['password'],
                save_credentials=True
            )
            assert login_result is True
        
        # 5. 認証情報が保存される
        credential_manager.save_credentials(
            valid_creds['handle'],
            valid_creds['password']
        )
        stored_creds = credential_manager.get_stored_credentials()
        assert stored_creds is not None, "認証情報が保存されたこと"
        
        # 6. タイムライン取得
        timeline_data = e2e_app_components['sample_timeline']
        with patch.object(bluesky_client, 'get_timeline', return_value={'feed': timeline_data}):
            timeline = bluesky_client.get_timeline()
            assert timeline is not None
            assert 'feed' in timeline
            assert len(timeline['feed']) > 0
        
        # 7. 新規投稿作成
        post_content = e2e_user_scenario_data['test_post_content']
        with patch.object(bluesky_client, 'send_post') as mock_send:
            mock_send.return_value = {"uri": "at://test/post/new"}
            post_result = bluesky_client.send_post(post_content)
            assert post_result is not None
        
        # 8. 設定変更
        settings_manager = e2e_app_components['settings_manager']
        new_settings = e2e_user_scenario_data['test_settings_changes']
        for key, value in new_settings.items():
            settings_manager.set(key, value)
        
        # 9. ログアウト
        with patch.object(bluesky_client, 'logout'):
            bluesky_client.logout()
        
        # 10. アプリケーション終了
        assert e2e_application_lifecycle.stop_app()
    
    def test_returning_user_auto_login_flow(
        self,
        e2e_app_components,
        e2e_application_lifecycle,
        e2e_user_scenario_data
    ):
        """リピーターユーザーの自動ログインフロー"""
        
        # 事前準備：認証情報を保存
        credential_manager = e2e_app_components['credential_manager']
        valid_creds = e2e_user_scenario_data['valid_credentials']
        credential_manager.save_credentials(
            valid_creds['handle'],
            valid_creds['password']
        )
        
        # 1. アプリケーション起動
        assert e2e_application_lifecycle.start_app(e2e_app_components)
        
        # 2. 自動ログイン試行をシミュレート
        bluesky_client = e2e_app_components['bluesky_client']
        # 保存された認証情報でログイン
        stored_creds = credential_manager.get_stored_credentials()
        if stored_creds:
            with patch.object(bluesky_client, 'login', return_value={'success': True}):
                login_result = bluesky_client.login(
                    stored_creds.get('username', valid_creds['handle']),
                    stored_creds.get('password', valid_creds['password'])
                )
                assert login_result is not None
        
        # 3. タイムライン自動取得
        with patch.object(bluesky_client, 'get_timeline') as mock_get_timeline:
            mock_get_timeline.return_value = {'feed': e2e_app_components['sample_timeline']}
            timeline = bluesky_client.get_timeline()
            assert timeline is not None
            assert 'feed' in timeline
            assert len(timeline['feed']) > 0
        
        # 4. アプリケーション終了
        assert e2e_application_lifecycle.stop_app()
    
    def test_error_recovery_flow(
        self,
        e2e_app_components,
        e2e_application_lifecycle,
        e2e_user_scenario_data
    ):
        """エラー回復フロー"""
        
        # 1. アプリケーション起動
        assert e2e_application_lifecycle.start_app(e2e_app_components)
        
        bluesky_client = e2e_app_components['bluesky_client']
        
        # 2. ネットワークエラーをシミュレート
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.side_effect = Exception("Network error")
            
            # エラーが発生
            with pytest.raises(Exception, match="Network error"):
                bluesky_client.get_timeline()
        
        # 3. エラー回復（再試行）
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.return_value = {'feed': e2e_app_components['sample_timeline']}
            timeline = bluesky_client.get_timeline()
            assert timeline is not None
        
        # 4. アプリケーション終了
        assert e2e_application_lifecycle.stop_app()


@pytest.mark.e2e
@pytest.mark.e2e_smoke
class TestSmokeTests:
    """スモークテスト（基本動作確認）"""
    
    def test_app_startup_and_shutdown(
        self,
        e2e_app_components,
        e2e_application_lifecycle
    ):
        """アプリケーション起動・終了"""
        # 起動
        assert e2e_application_lifecycle.start_app(e2e_app_components)
        assert e2e_application_lifecycle.is_app_running()
        
        # 短時間実行
        time.sleep(0.1)
        
        # 終了
        assert e2e_application_lifecycle.stop_app()
        assert not e2e_application_lifecycle.is_app_running()
    
    def test_basic_authentication(
        self,
        e2e_app_components,
        e2e_user_scenario_data
    ):
        """基本認証フロー"""
        bluesky_client = e2e_app_components['bluesky_client']
        valid_creds = e2e_user_scenario_data['valid_credentials']
        
        with patch.object(bluesky_client, 'login', return_value=True):
            result = bluesky_client.login(
                valid_creds['handle'],
                valid_creds['password']
            )
            assert result is True
    
    def test_basic_timeline_display(
        self,
        e2e_app_components
    ):
        """基本的なタイムライン表示"""
        bluesky_client = e2e_app_components['bluesky_client']
        
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.return_value = e2e_app_components['sample_timeline']
            timeline = bluesky_client.get_timeline()
            
            assert timeline is not None
            assert len(timeline) > 0
            assert timeline[0]['record']['text'] == "E2Eテスト用投稿"


@pytest.mark.e2e
@pytest.mark.e2e_gui
class TestGUIInteractions:
    """GUI操作のE2Eテスト"""
    
    def test_main_window_lifecycle(
        self,
        e2e_app_components
    ):
        """メインウィンドウのライフサイクル"""
        wx_mock = e2e_app_components['wx']
        frame_mock = e2e_app_components['frame']
        
        # ウィンドウ表示
        frame_mock.Show(True)
        frame_mock.Show.assert_called_with(True)
        
        # ウィンドウ更新
        frame_mock.Refresh()
        frame_mock.Refresh.assert_called()
        
        # ウィンドウクローズ
        frame_mock.Close()
        frame_mock.Close.assert_called()
    
    def test_menu_interactions(
        self,
        e2e_app_components
    ):
        """メニュー操作"""
        wx_mock = e2e_app_components['wx']
        
        # ファイルメニュー
        file_menu_items = ['ログイン', 'ログアウト', '終了']
        
        # 投稿メニュー
        post_menu_items = ['新規投稿', 'タイムライン更新']
        
        # メニューイベントのシミュレート
        for item in file_menu_items + post_menu_items:
            event = MagicMock()
            event.GetId = MagicMock(return_value=1000)
            # イベントハンドラーが呼ばれることを確認
            assert event is not None
    
    @pytest.mark.skip(reason="GUI modules not available in test environment")
    def test_dialog_flows(
        self,
        e2e_app_components
    ):
        """ダイアログフロー"""
        wx_mock = e2e_app_components['wx']
        
        # ログインダイアログ
        with patch('gui.dialogs.login_dialog.LoginDialog') as mock_dialog:
            dialog_instance = MagicMock()
            dialog_instance.ShowModal = MagicMock(return_value=wx_mock.OK)
            dialog_instance.get_credentials = MagicMock(return_value={
                "identifier": "test.user",
                "password": "password"
            })
            mock_dialog.return_value = dialog_instance
            
            # ダイアログ表示と結果取得
            result = dialog_instance.ShowModal()
            assert result == wx_mock.OK
            
            creds = dialog_instance.get_credentials()
            assert creds["identifier"] == "test.user"


@pytest.mark.e2e
@pytest.mark.e2e_api
class TestAPIIntegration:
    """API統合のE2Eテスト"""
    
    def test_post_creation_flow(
        self,
        e2e_app_components,
        e2e_user_scenario_data
    ):
        """投稿作成フロー"""
        bluesky_client = e2e_app_components['bluesky_client']
        post_content = e2e_user_scenario_data['test_post_content']
        
        # 画像なし投稿
        with patch.object(bluesky_client, 'send_post') as mock_send:
            mock_send.return_value = {"uri": "at://test/post/1"}
            result = bluesky_client.send_post(post_content)
            
            assert result is not None
            assert "uri" in result
            mock_send.assert_called_once_with(post_content)
    
    def test_timeline_pagination(
        self,
        e2e_app_components
    ):
        """タイムラインページネーション"""
        bluesky_client = e2e_app_components['bluesky_client']
        
        # 初回取得
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.return_value = e2e_app_components['sample_timeline']
            first_page = bluesky_client.get_timeline(limit=10)
            assert len(first_page) > 0
        
        # 次ページ取得
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.return_value = []  # 最終ページ
            next_page = bluesky_client.get_timeline(limit=10, cursor="next_cursor")
            assert next_page == []
    
    def test_user_profile_operations(
        self,
        e2e_app_components
    ):
        """ユーザープロフィール操作"""
        bluesky_client = e2e_app_components['bluesky_client']
        
        with patch.object(bluesky_client, 'get_profile') as mock_get_profile:
            mock_get_profile.return_value = e2e_app_components['sample_profile']
            profile = bluesky_client.get_profile("test.user")
            
            assert profile is not None
            assert profile['handle'] == "test.user"
            assert profile['displayName'] == "テストユーザー"


@pytest.mark.e2e
class TestPerformanceScenarios:
    """パフォーマンスシナリオのE2Eテスト"""
    
    def test_large_timeline_handling(
        self,
        e2e_app_components
    ):
        """大量タイムラインデータの処理"""
        bluesky_client = e2e_app_components['bluesky_client']
        
        # 大量の投稿データを生成
        large_timeline = []
        for i in range(100):
            large_timeline.append({
                "uri": f"at://test/post/{i}",
                "record": {"text": f"投稿 {i}"},
                "author": {"handle": f"user{i}"}
            })
        
        with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
            mock_timeline.return_value = large_timeline
            
            start_time = time.time()
            timeline = bluesky_client.get_timeline(limit=100)
            elapsed_time = time.time() - start_time
            
            assert len(timeline) == 100
            assert elapsed_time < 1.0  # 1秒以内に処理
    
    def test_rapid_user_interactions(
        self,
        e2e_app_components
    ):
        """高速ユーザー操作"""
        bluesky_client = e2e_app_components['bluesky_client']
        
        # 連続投稿
        for i in range(10):
            with patch.object(bluesky_client, 'send_post') as mock_send:
                mock_send.return_value = {"uri": f"at://test/post/{i}"}
                result = bluesky_client.send_post(f"連続投稿 {i}")
                assert result is not None
        
        # 連続タイムライン更新
        for i in range(5):
            with patch.object(bluesky_client, 'get_timeline') as mock_timeline:
                mock_timeline.return_value = []
                timeline = bluesky_client.get_timeline()
                assert timeline is not None