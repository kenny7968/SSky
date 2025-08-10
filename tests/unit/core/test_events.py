#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーションイベント定義モジュールの単体テスト
"""

import pytest

import core.events as events


class TestAuthenticationEvents:
    """認証関連イベント定数のテスト"""
    
    def test_auth_login_events(self):
        """ログインイベント定数の確認"""
        assert events.AUTH_LOGIN_ATTEMPT == "auth.login.attempt"
        assert events.AUTH_LOGIN_SUCCESS == "auth.login.success"
        assert events.AUTH_LOGIN_FAILURE == "auth.login.failure"
    
    def test_auth_session_load_events(self):
        """セッションロードイベント定数の確認"""
        assert events.AUTH_SESSION_LOAD_ATTEMPT == "auth.session.load.attempt"
        assert events.AUTH_SESSION_LOAD_SUCCESS == "auth.session.load.success"
        assert events.AUTH_SESSION_LOAD_FAILURE == "auth.session.load.failure"
    
    def test_auth_logout_events(self):
        """ログアウトイベント定数の確認"""
        assert events.AUTH_LOGOUT_SUCCESS == "auth.logout.success"
    
    def test_auth_session_management_events(self):
        """セッション管理イベント定数の確認"""
        assert events.AUTH_SESSION_INVALID == "auth.session.invalid"
        assert events.AUTH_SESSION_SAVED == "auth.session.saved"
        assert events.AUTH_SESSION_DELETED == "auth.session.deleted"


class TestPostEvents:
    """投稿関連イベント定数のテスト"""
    
    def test_post_submit_events(self):
        """投稿イベント定数の確認"""
        assert events.POST_SUBMIT_START == "post.submit.start"
        assert events.POST_SUBMIT_SUCCESS == "post.submit.success"
        assert events.POST_SUBMIT_FAILURE == "post.submit.failure"
    
    def test_like_events(self):
        """いいねイベント定数の確認"""
        assert events.LIKE_START == "post.like.start"
        assert events.LIKE_SUCCESS == "post.like.success"
        assert events.LIKE_FAILURE == "post.like.failure"
    
    def test_repost_events(self):
        """リポストイベント定数の確認"""
        assert events.REPOST_START == "post.repost.start"
        assert events.REPOST_SUCCESS == "post.repost.success"
        assert events.REPOST_FAILURE == "post.repost.failure"


class TestUIEvents:
    """UI関連イベント定数のテスト"""
    
    def test_language_changed_event(self):
        """言語変更イベント定数の確認"""
        assert events.LANGUAGE_CHANGED == "language.changed"


class TestEventNaming:
    """イベント命名規則のテスト"""
    
    def test_event_naming_consistency(self):
        """イベント名の命名規則一貫性の確認"""
        # 認証関連イベント
        auth_events = [
            events.AUTH_LOGIN_ATTEMPT,
            events.AUTH_LOGIN_SUCCESS,
            events.AUTH_LOGIN_FAILURE,
            events.AUTH_SESSION_LOAD_ATTEMPT,
            events.AUTH_SESSION_LOAD_SUCCESS,
            events.AUTH_SESSION_LOAD_FAILURE,
            events.AUTH_LOGOUT_SUCCESS,
            events.AUTH_SESSION_INVALID,
            events.AUTH_SESSION_SAVED,
            events.AUTH_SESSION_DELETED,
        ]
        
        for event in auth_events:
            assert event.startswith("auth."), f"Auth event {event} should start with 'auth.'"
        
        # 投稿関連イベント
        post_events = [
            events.POST_SUBMIT_START,
            events.POST_SUBMIT_SUCCESS,
            events.POST_SUBMIT_FAILURE,
            events.LIKE_START,
            events.LIKE_SUCCESS,
            events.LIKE_FAILURE,
            events.REPOST_START,
            events.REPOST_SUCCESS,
            events.REPOST_FAILURE,
        ]
        
        for event in post_events:
            assert event.startswith("post."), f"Post event {event} should start with 'post.'"
    
    def test_event_types_have_consistent_suffixes(self):
        """イベントタイプが一貫した接尾辞を持つことの確認"""
        # 開始イベント
        start_events = [
            events.POST_SUBMIT_START,
            events.LIKE_START,
            events.REPOST_START,
        ]
        
        for event in start_events:
            assert event.endswith(".start"), f"Start event {event} should end with '.start'"
        
        # 成功イベント
        success_events = [
            events.AUTH_LOGIN_SUCCESS,
            events.AUTH_SESSION_LOAD_SUCCESS,
            events.AUTH_LOGOUT_SUCCESS,
            events.POST_SUBMIT_SUCCESS,
            events.LIKE_SUCCESS,
            events.REPOST_SUCCESS,
        ]
        
        for event in success_events:
            assert event.endswith(".success"), f"Success event {event} should end with '.success'"
        
        # 失敗イベント
        failure_events = [
            events.AUTH_LOGIN_FAILURE,
            events.AUTH_SESSION_LOAD_FAILURE,
            events.POST_SUBMIT_FAILURE,
            events.LIKE_FAILURE,
            events.REPOST_FAILURE,
        ]
        
        for event in failure_events:
            assert event.endswith(".failure"), f"Failure event {event} should end with '.failure'"
    
    def test_no_duplicate_event_names(self):
        """重複するイベント名がないことの確認"""
        all_events = [
            events.AUTH_LOGIN_ATTEMPT,
            events.AUTH_LOGIN_SUCCESS,
            events.AUTH_LOGIN_FAILURE,
            events.AUTH_SESSION_LOAD_ATTEMPT,
            events.AUTH_SESSION_LOAD_SUCCESS,
            events.AUTH_SESSION_LOAD_FAILURE,
            events.AUTH_LOGOUT_SUCCESS,
            events.AUTH_SESSION_INVALID,
            events.AUTH_SESSION_SAVED,
            events.AUTH_SESSION_DELETED,
            events.LANGUAGE_CHANGED,
            events.POST_SUBMIT_START,
            events.POST_SUBMIT_SUCCESS,
            events.POST_SUBMIT_FAILURE,
            events.LIKE_START,
            events.LIKE_SUCCESS,
            events.LIKE_FAILURE,
            events.REPOST_START,
            events.REPOST_SUCCESS,
            events.REPOST_FAILURE,
        ]
        
        # 重複チェック
        unique_events = set(all_events)
        assert len(unique_events) == len(all_events), "Duplicate event names found"
    
    def test_event_strings_are_valid(self):
        """イベント文字列が有効であることの確認"""
        all_events = [
            events.AUTH_LOGIN_ATTEMPT,
            events.AUTH_LOGIN_SUCCESS,
            events.AUTH_LOGIN_FAILURE,
            events.AUTH_SESSION_LOAD_ATTEMPT,
            events.AUTH_SESSION_LOAD_SUCCESS,
            events.AUTH_SESSION_LOAD_FAILURE,
            events.AUTH_LOGOUT_SUCCESS,
            events.AUTH_SESSION_INVALID,
            events.AUTH_SESSION_SAVED,
            events.AUTH_SESSION_DELETED,
            events.LANGUAGE_CHANGED,
            events.POST_SUBMIT_START,
            events.POST_SUBMIT_SUCCESS,
            events.POST_SUBMIT_FAILURE,
            events.LIKE_START,
            events.LIKE_SUCCESS,
            events.LIKE_FAILURE,
            events.REPOST_START,
            events.REPOST_SUCCESS,
            events.REPOST_FAILURE,
        ]
        
        for event in all_events:
            # 文字列であることを確認
            assert isinstance(event, str), f"Event {event} should be a string"
            
            # 空でないことを確認
            assert len(event) > 0, f"Event {event} should not be empty"
            
            # 有効な文字のみを含むことを確認（英数字、ドット、アンダースコア）
            import re
            assert re.match(r'^[a-z0-9._]+$', event), f"Event {event} contains invalid characters"


class TestEventIntegration:
    """イベント統合テスト"""
    
    def test_all_events_accessible(self):
        """すべてのイベントがモジュール経由でアクセス可能であることを確認"""
        # 認証関連
        assert hasattr(events, 'AUTH_LOGIN_ATTEMPT')
        assert hasattr(events, 'AUTH_LOGIN_SUCCESS')
        assert hasattr(events, 'AUTH_LOGIN_FAILURE')
        assert hasattr(events, 'AUTH_SESSION_LOAD_ATTEMPT')
        assert hasattr(events, 'AUTH_SESSION_LOAD_SUCCESS')
        assert hasattr(events, 'AUTH_SESSION_LOAD_FAILURE')
        assert hasattr(events, 'AUTH_LOGOUT_SUCCESS')
        assert hasattr(events, 'AUTH_SESSION_INVALID')
        assert hasattr(events, 'AUTH_SESSION_SAVED')
        assert hasattr(events, 'AUTH_SESSION_DELETED')
        
        # UI関連
        assert hasattr(events, 'LANGUAGE_CHANGED')
        
        # 投稿関連
        assert hasattr(events, 'POST_SUBMIT_START')
        assert hasattr(events, 'POST_SUBMIT_SUCCESS')
        assert hasattr(events, 'POST_SUBMIT_FAILURE')
        assert hasattr(events, 'LIKE_START')
        assert hasattr(events, 'LIKE_SUCCESS')
        assert hasattr(events, 'LIKE_FAILURE')
        assert hasattr(events, 'REPOST_START')
        assert hasattr(events, 'REPOST_SUCCESS')
        assert hasattr(events, 'REPOST_FAILURE')
    
    def test_event_categorization(self):
        """イベントが適切にカテゴリ分けされていることを確認"""
        # 認証系イベントをカテゴリ別にグループ化
        auth_categories = {
            'login': [events.AUTH_LOGIN_ATTEMPT, events.AUTH_LOGIN_SUCCESS, events.AUTH_LOGIN_FAILURE],
            'session_load': [events.AUTH_SESSION_LOAD_ATTEMPT, events.AUTH_SESSION_LOAD_SUCCESS, events.AUTH_SESSION_LOAD_FAILURE],
            'logout': [events.AUTH_LOGOUT_SUCCESS],
            'session_mgmt': [events.AUTH_SESSION_INVALID, events.AUTH_SESSION_SAVED, events.AUTH_SESSION_DELETED],
        }
        
        for category, category_events in auth_categories.items():
            for event in category_events:
                if category == 'logout':
                    assert 'logout' in event or 'session' in event
                else:
                    assert category.replace('_', '.') in event or category.split('_')[0] in event
        
        # 投稿系イベントをカテゴリ別にグループ化
        post_categories = {
            'submit': [events.POST_SUBMIT_START, events.POST_SUBMIT_SUCCESS, events.POST_SUBMIT_FAILURE],
            'like': [events.LIKE_START, events.LIKE_SUCCESS, events.LIKE_FAILURE],
            'repost': [events.REPOST_START, events.REPOST_SUCCESS, events.REPOST_FAILURE],
        }
        
        for category, category_events in post_categories.items():
            for event in category_events:
                assert category in event, f"Event {event} should contain category '{category}'"


class TestEventDocumentation:
    """イベント文書化と一貫性のテスト"""
    
    def test_event_patterns_match_expected_flows(self):
        """イベントパターンが期待されるフローと一致することを確認"""
        # ログインフロー: attempt -> success/failure
        login_flow = {
            'attempt': events.AUTH_LOGIN_ATTEMPT,
            'success': events.AUTH_LOGIN_SUCCESS,
            'failure': events.AUTH_LOGIN_FAILURE
        }
        
        base_name = "auth.login"
        assert login_flow['attempt'] == f"{base_name}.attempt"
        assert login_flow['success'] == f"{base_name}.success"
        assert login_flow['failure'] == f"{base_name}.failure"
        
        # 投稿フロー: start -> success/failure
        post_flow = {
            'start': events.POST_SUBMIT_START,
            'success': events.POST_SUBMIT_SUCCESS,
            'failure': events.POST_SUBMIT_FAILURE
        }
        
        base_name = "post.submit"
        assert post_flow['start'] == f"{base_name}.start"
        assert post_flow['success'] == f"{base_name}.success"
        assert post_flow['failure'] == f"{base_name}.failure"
    
    def test_hierarchical_naming_structure(self):
        """階層的命名構造の確認"""
        # すべてのイベントが適切な階層構造を持っていることを確認
        all_events = [
            events.AUTH_LOGIN_ATTEMPT,
            events.AUTH_LOGIN_SUCCESS,
            events.AUTH_LOGIN_FAILURE,
            events.AUTH_SESSION_LOAD_ATTEMPT,
            events.AUTH_SESSION_LOAD_SUCCESS,
            events.AUTH_SESSION_LOAD_FAILURE,
            events.AUTH_LOGOUT_SUCCESS,
            events.AUTH_SESSION_INVALID,
            events.AUTH_SESSION_SAVED,
            events.AUTH_SESSION_DELETED,
            events.LANGUAGE_CHANGED,
            events.POST_SUBMIT_START,
            events.POST_SUBMIT_SUCCESS,
            events.POST_SUBMIT_FAILURE,
            events.LIKE_START,
            events.LIKE_SUCCESS,
            events.LIKE_FAILURE,
            events.REPOST_START,
            events.REPOST_SUCCESS,
            events.REPOST_FAILURE,
        ]
        
        for event in all_events:
            parts = event.split('.')
            # 少なくとも2層の階層構造を持つ（category.action 形式）
            assert len(parts) >= 2, f"Event {event} should have at least 2 hierarchy levels"
            
            # 各パートが空でないことを確認
            for part in parts:
                assert len(part) > 0, f"Empty hierarchy part found in {event}"