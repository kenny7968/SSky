#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
BlueskyUserManager単体テスト (Phase 2 リファクタリング版)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from atproto.exceptions import AtProtocolError

from core.client.user_manager import BlueskyUserManager
from core.client.api_client import BlueskyApiClient
from core.client.auth_manager import BlueskyAuthManager


@pytest.fixture
def mock_api_client():
    """APIクライアントのモック"""
    mock_client = Mock(spec=BlueskyApiClient)
    mock_atproto_client = Mock()
    mock_client.client = mock_atproto_client
    return mock_client


@pytest.fixture
def mock_auth_manager():
    """認証管理のモック"""
    mock_auth = Mock(spec=BlueskyAuthManager)
    mock_auth.user_did = "did:plc:test123"
    return mock_auth


@pytest.fixture
def user_manager(mock_api_client, mock_auth_manager):
    """ユーザー管理インスタンス"""
    return BlueskyUserManager(mock_api_client, mock_auth_manager)


@pytest.mark.unit
class TestBlueskyUserManagerInstantiation:
    """BlueskyUserManagerインスタンス化テスト"""
    
    def test_default_instantiation(self):
        """デフォルトインスタンス化テスト"""
        manager = BlueskyUserManager()
        
        assert manager.api_client is None
        assert manager.auth_manager is None
    
    def test_dependency_injection_instantiation(self, mock_api_client, mock_auth_manager):
        """依存性注入によるインスタンス化テスト"""
        manager = BlueskyUserManager(mock_api_client, mock_auth_manager)
        
        assert manager.api_client is mock_api_client
        assert manager.auth_manager is mock_auth_manager


@pytest.mark.unit
class TestBlueskyUserManagerFollowMethods:
    """BlueskyUserManagerフォロー機能テスト"""
    
    def test_follow_success(self, user_manager, mock_api_client):
        """フォロー成功テスト"""
        test_handle = "alice.bsky.social"
        test_result = {"uri": "at://test/follow/123"}
        
        mock_api_client.client.follow.return_value = test_result
        
        result = user_manager.follow(test_handle)
        
        mock_api_client.client.follow.assert_called_once_with(test_handle)
        assert result == test_result
    
    def test_follow_api_error(self, user_manager, mock_api_client):
        """フォローAPIエラーテスト"""
        test_handle = "alice.bsky.social"
        test_error = AtProtocolError("Follow failed")
        
        mock_api_client.client.follow.side_effect = test_error
        
        with pytest.raises(AtProtocolError):
            user_manager.follow(test_handle)
    
    def test_unfollow_with_uri_success(self, user_manager, mock_api_client, mock_auth_manager):
        """URIを使用したフォロー解除成功テスト"""
        test_handle = "alice.bsky.social"
        test_follow_uri = "at://did:plc:test123/app.bsky.graph.follow/record123"
        test_result = {"success": True}
        
        # プロフィール情報のモック（フォロー情報あり）
        mock_profile = Mock()
        mock_viewer = Mock()
        mock_viewer.following = test_follow_uri
        mock_profile.viewer = mock_viewer
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # レコード削除のモック
        mock_api_client.client.com.atproto.repo.delete_record.return_value = test_result
        
        result = user_manager.unfollow(test_handle)
        
        # プロフィール取得が呼ばれることを確認
        mock_api_client.client.get_profile.assert_called_once_with(actor=test_handle)
        
        # レコード削除が適切なパラメータで呼ばれることを確認
        mock_api_client.client.com.atproto.repo.delete_record.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.follow',
            'rkey': 'record123'
        })
        
        assert result == test_result
    
    def test_unfollow_without_uri_fallback(self, user_manager, mock_api_client):
        """URIなしでの標準APIフォロー解除テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # プロフィール情報のモック（フォロー情報なし）
        mock_profile = Mock()
        mock_profile.viewer = Mock()
        # following属性が存在しない、またはNone
        mock_profile.viewer.following = None
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 標準APIのモック
        mock_api_client.client.delete_follow.return_value = test_result
        
        result = user_manager.unfollow(test_handle)
        
        # DID解決が呼ばれることを確認
        mock_api_client.client.resolve_handle.assert_called_once_with(handle=test_handle)
        
        # 標準APIが呼ばれることを確認
        mock_api_client.client.delete_follow.assert_called_once_with(did=test_did)
        
        assert result == test_result
    
    def test_unfollow_profile_without_viewer(self, user_manager, mock_api_client):
        """viewer属性のないプロフィールでのフォロー解除テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # プロフィール情報のモック（viewer属性なし）
        mock_profile = Mock()
        # viewer属性が存在しない
        if hasattr(mock_profile, 'viewer'):
            delattr(mock_profile, 'viewer')
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 標準APIのモック
        mock_api_client.client.delete_follow.return_value = test_result
        
        result = user_manager.unfollow(test_handle)
        
        # 標準APIが使用されることを確認
        mock_api_client.client.delete_follow.assert_called_once_with(did=test_did)
        assert result == test_result


@pytest.mark.unit
class TestBlueskyUserManagerBlockMethods:
    """BlueskyUserManagerブロック機能テスト"""
    
    @patch('core.client.user_manager.datetime')
    def test_block_success_high_level_api(self, mock_datetime, user_manager, mock_api_client, mock_auth_manager):
        """高レベルAPIによるブロック成功テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"uri": "at://test/block/123"}
        test_created_at = "2024-01-01T12:00:00Z"
        
        # 固定された日時のモック
        mock_now = Mock()
        mock_now.isoformat.return_value = test_created_at.replace('Z', '+00:00')
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone = timezone
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 高レベルAPIのモック
        mock_api_client.client.app.bsky.graph.block.create.return_value = test_result
        
        result = user_manager.block(test_handle)
        
        # DID解決が呼ばれることを確認
        mock_api_client.client.resolve_handle.assert_called_once_with(handle=test_handle)
        
        # 高レベルAPIが適切なパラメータで呼ばれることを確認
        mock_api_client.client.app.bsky.graph.block.create.assert_called_once_with({
            'repo': mock_auth_manager.user_did,
            'record': {
                'subject': test_did,
                'createdAt': test_created_at
            }
        })
        
        assert result == test_result
    
    @patch('core.client.user_manager.datetime')
    def test_block_fallback_to_low_level_api(self, mock_datetime, user_manager, mock_api_client, mock_auth_manager):
        """低レベルAPIへのフォールバックブロックテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"uri": "at://test/block/123"}
        test_created_at = "2024-01-01T12:00:00Z"
        
        # 固定された日時のモック
        mock_now = Mock()
        mock_now.isoformat.return_value = test_created_at.replace('Z', '+00:00')
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone = timezone
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 高レベルAPIが失敗し、低レベルAPIが成功
        mock_api_client.client.app.bsky.graph.block.create.side_effect = AttributeError("Method not found")
        mock_api_client.client.com.atproto.repo.create_record.return_value = test_result
        
        result = user_manager.block(test_handle)
        
        # 低レベルAPIが呼ばれることを確認
        mock_api_client.client.com.atproto.repo.create_record.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.block',
            'record': {
                'subject': test_did,
                'createdAt': test_created_at
            }
        })
        
        assert result == test_result
    
    def test_unblock_with_uri_success(self, user_manager, mock_api_client, mock_auth_manager):
        """URIを使用したブロック解除成功テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_block_uri = "at://did:plc:test123/app.bsky.graph.block/record123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # プロフィール情報のモック（ブロック情報あり）
        mock_profile = Mock()
        mock_viewer = Mock()
        mock_viewer.blocking = test_block_uri
        mock_profile.viewer = mock_viewer
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # 高レベルAPIのモック
        mock_api_client.client.app.bsky.graph.block.delete.return_value = test_result
        
        result = user_manager.unblock(test_handle)
        
        # 高レベルAPIが適切なパラメータで呼ばれることを確認
        mock_api_client.client.app.bsky.graph.block.delete.assert_called_once_with({
            'repo': mock_auth_manager.user_did,
            'rkey': 'record123'
        })
        
        assert result == test_result
    
    def test_unblock_with_uri_fallback_to_low_level(self, user_manager, mock_api_client, mock_auth_manager):
        """URIを使用したブロック解除で低レベルAPIフォールバックテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_block_uri = "at://did:plc:test123/app.bsky.graph.block/record123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # プロフィール情報のモック（ブロック情報あり）
        mock_profile = Mock()
        mock_viewer = Mock()
        mock_viewer.blocking = test_block_uri
        mock_profile.viewer = mock_viewer
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # 高レベルAPIが失敗し、低レベルAPIが成功
        mock_api_client.client.app.bsky.graph.block.delete.side_effect = AttributeError("Method not found")
        mock_api_client.client.com.atproto.repo.delete_record.return_value = test_result
        
        result = user_manager.unblock(test_handle)
        
        # 低レベルAPIが呼ばれることを確認
        mock_api_client.client.com.atproto.repo.delete_record.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.block',
            'rkey': 'record123'
        })
        
        assert result == test_result
    
    def test_unblock_search_and_delete_records(self, user_manager, mock_api_client, mock_auth_manager):
        """レコード検索によるブロック解除テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # プロフィール情報のモック（ブロック情報なし）
        mock_profile = Mock()
        mock_profile.viewer = Mock()
        mock_profile.viewer.blocking = None
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # レコード検索のモック
        mock_record = Mock()
        mock_record.rkey = "record123"
        mock_record.value = {"subject": test_did}
        
        mock_blocks_list = Mock()
        mock_blocks_list.records = [mock_record]
        mock_api_client.client.com.atproto.repo.list_records.return_value = mock_blocks_list
        
        # レコード削除のモック
        mock_api_client.client.com.atproto.repo.delete_record.return_value = test_result
        
        result = user_manager.unblock(test_handle)
        
        # レコード検索が呼ばれることを確認
        mock_api_client.client.com.atproto.repo.list_records.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.block',
            'limit': 100
        })
        
        # レコード削除が呼ばれることを確認
        mock_api_client.client.com.atproto.repo.delete_record.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.block',
            'rkey': 'record123'
        })
        
        assert result == test_result
    
    def test_unblock_record_not_found(self, user_manager, mock_api_client, mock_auth_manager):
        """ブロックレコードが見つからない場合のテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # プロフィール情報のモック（ブロック情報なし）
        mock_profile = Mock()
        mock_profile.viewer = Mock()
        mock_profile.viewer.blocking = None
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # レコード検索のモック（該当なし）
        mock_blocks_list = Mock()
        mock_blocks_list.records = []  # 空のレコードリスト
        mock_api_client.client.com.atproto.repo.list_records.return_value = mock_blocks_list
        
        result = user_manager.unblock(test_handle)
        
        # ブロックされていない場合の結果が返されることを確認
        assert result == {'success': True, 'message': 'ユーザーはブロックされていません'}


@pytest.mark.unit
class TestBlueskyUserManagerMuteMethods:
    """BlueskyUserManagerミュート機能テスト"""
    
    def test_mute_success_high_level_api(self, user_manager, mock_api_client):
        """高レベルAPIによるミュート成功テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"uri": "at://test/mute/123"}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 高レベルAPIのモック
        mock_api_client.client.app.bsky.graph.mute_actor.return_value = test_result
        
        result = user_manager.mute(test_handle)
        
        # DID解決が呼ばれることを確認
        mock_api_client.client.resolve_handle.assert_called_once_with(handle=test_handle)
        
        # 高レベルAPIが適切なパラメータで呼ばれることを確認
        mock_api_client.client.app.bsky.graph.mute_actor.assert_called_once_with(data={'actor': test_did})
        
        assert result == test_result
    
    def test_mute_fallback_to_bsky_graph(self, user_manager, mock_api_client):
        """bsky.graphへのフォールバックミュートテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"uri": "at://test/mute/123"}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # app.bsky.graphが失敗し、bsky.graphが成功
        mock_api_client.client.app.bsky.graph.mute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.mute_actor.return_value = test_result
        
        result = user_manager.mute(test_handle)
        
        # フォールバックAPIが呼ばれることを確認
        mock_api_client.client.bsky.graph.mute_actor.assert_called_once_with(data={'actor': test_did})
        
        assert result == test_result
    
    @patch('core.client.user_manager.datetime')
    def test_mute_fallback_to_low_level_api(self, mock_datetime, user_manager, mock_api_client, mock_auth_manager):
        """低レベルAPIへのフォールバックミュートテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"uri": "at://test/mute/123"}
        test_created_at = "2024-01-01T12:00:00Z"
        
        # 固定された日時のモック
        mock_now = Mock()
        mock_now.isoformat.return_value = test_created_at.replace('Z', '+00:00')
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone = timezone
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 両方の高レベルAPIが失敗し、低レベルAPIが成功
        mock_api_client.client.app.bsky.graph.mute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.mute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.com.atproto.repo.create_record.return_value = test_result
        
        result = user_manager.mute(test_handle)
        
        # 低レベルAPIが呼ばれることを確認
        mock_api_client.client.com.atproto.repo.create_record.assert_called_once_with(data={
            'repo': mock_auth_manager.user_did,
            'collection': 'app.bsky.graph.mute',
            'record': {
                'subject': test_did,
                'createdAt': test_created_at
            }
        })
        
        assert result == test_result
    
    def test_unmute_success_high_level_api(self, user_manager, mock_api_client):
        """高レベルAPIによるミュート解除成功テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 高レベルAPIのモック
        mock_api_client.client.app.bsky.graph.unmute_actor.return_value = test_result
        
        result = user_manager.unmute(test_handle)
        
        # 高レベルAPIが適切なパラメータで呼ばれることを確認
        mock_api_client.client.app.bsky.graph.unmute_actor.assert_called_once_with(data={'actor': test_did})
        
        assert result == test_result
    
    def test_unmute_fallback_to_bsky_graph(self, user_manager, mock_api_client):
        """bsky.graphへのフォールバックミュート解除テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # app.bsky.graphが失敗し、bsky.graphが成功
        mock_api_client.client.app.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.unmute_actor.return_value = test_result
        
        result = user_manager.unmute(test_handle)
        
        # フォールバックAPIが呼ばれることを確認
        mock_api_client.client.bsky.graph.unmute_actor.assert_called_once_with(data={'actor': test_did})
        
        assert result == test_result
    
    def test_unmute_already_unmuted(self, user_manager, mock_api_client):
        """既にミュート解除済みユーザーのテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 両方の高レベルAPIが失敗
        mock_api_client.client.app.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        
        # プロフィール情報のモック（ミュート解除済み）
        mock_profile = Mock()
        mock_viewer = Mock()
        mock_viewer.muted = False
        mock_profile.viewer = mock_viewer
        mock_api_client.client.get_profile.return_value = mock_profile
        
        result = user_manager.unmute(test_handle)
        
        # 既にミュート解除済みの場合はNoneが返される
        assert result is None
    
    def test_unmute_fallback_to_standard_api(self, user_manager, mock_api_client):
        """標準APIへのフォールバックミュート解除テスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        test_result = {"success": True}
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 両方の高レベルAPIが失敗
        mock_api_client.client.app.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        
        # プロフィール情報のモック（ミュート状態）
        mock_profile = Mock()
        mock_viewer = Mock()
        mock_viewer.muted = True
        mock_profile.viewer = mock_viewer
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # 標準APIのモック
        mock_api_client.client.unmute_actor.return_value = test_result
        
        result = user_manager.unmute(test_handle)
        
        # 標準APIが呼ばれることを確認
        mock_api_client.client.unmute_actor.assert_called_once_with(actor=test_did)
        
        assert result == test_result


@pytest.mark.unit
class TestBlueskyUserManagerListMethods:
    """BlueskyUserManagerリスト取得機能テスト"""
    
    def test_get_following_success(self, user_manager, mock_api_client):
        """フォロー中ユーザー取得成功テスト"""
        test_handle = "alice.bsky.social"
        test_result = Mock()
        test_result.follows = [
            {"handle": "bob.bsky.social", "did": "did:plc:bob123"},
            {"handle": "charlie.bsky.social", "did": "did:plc:charlie456"}
        ]
        
        mock_api_client.client.app.bsky.graph.get_follows.return_value = test_result
        
        result = user_manager.get_following(test_handle, limit=50)
        
        mock_api_client.client.app.bsky.graph.get_follows.assert_called_once_with({
            'actor': test_handle,
            'limit': 50,
            'cursor': None
        })
        
        assert result == test_result
    
    def test_get_following_with_cursor(self, user_manager, mock_api_client):
        """カーソル付きフォロー中ユーザー取得テスト"""
        test_handle = "alice.bsky.social"
        test_cursor = "cursor123"
        test_result = Mock()
        test_result.follows = [{"handle": "bob.bsky.social"}]
        test_result.cursor = "next_cursor"
        
        mock_api_client.client.app.bsky.graph.get_follows.return_value = test_result
        
        result = user_manager.get_following(test_handle, limit=25, cursor=test_cursor)
        
        mock_api_client.client.app.bsky.graph.get_follows.assert_called_once_with({
            'actor': test_handle,
            'limit': 25,
            'cursor': test_cursor
        })
        
        assert result == test_result
    
    def test_get_following_limit_capping(self, user_manager, mock_api_client):
        """フォロー中ユーザー取得制限キャップテスト"""
        test_handle = "alice.bsky.social"
        test_result = Mock()
        test_result.follows = []
        
        mock_api_client.client.app.bsky.graph.get_follows.return_value = test_result
        
        # 制限を100を超えて設定
        result = user_manager.get_following(test_handle, limit=150)
        
        # 制限が100にキャップされることを確認
        mock_api_client.client.app.bsky.graph.get_follows.assert_called_once_with({
            'actor': test_handle,
            'limit': 100,
            'cursor': None
        })
    
    def test_get_followers_success(self, user_manager, mock_api_client):
        """フォロワー取得成功テスト"""
        test_handle = "alice.bsky.social"
        test_result = Mock()
        test_result.followers = [
            {"handle": "bob.bsky.social", "did": "did:plc:bob123"},
            {"handle": "charlie.bsky.social", "did": "did:plc:charlie456"}
        ]
        
        mock_api_client.client.app.bsky.graph.get_followers.return_value = test_result
        
        result = user_manager.get_followers(test_handle, limit=50)
        
        mock_api_client.client.app.bsky.graph.get_followers.assert_called_once_with({
            'actor': test_handle,
            'limit': 50,
            'cursor': None
        })
        
        assert result == test_result
    
    def test_get_blocked_users_success(self, user_manager, mock_api_client):
        """ブロック済みユーザー取得成功テスト"""
        test_result = Mock()
        test_result.blocks = [
            {"handle": "blocked1.bsky.social", "did": "did:plc:blocked123"},
            {"handle": "blocked2.bsky.social", "did": "did:plc:blocked456"}
        ]
        
        mock_api_client.client.app.bsky.graph.get_blocks.return_value = test_result
        
        result = user_manager.get_blocked_users(limit=50)
        
        mock_api_client.client.app.bsky.graph.get_blocks.assert_called_once_with(params={
            'limit': 50,
            'cursor': None
        })
        
        assert result == test_result
    
    def test_get_muted_users_success(self, user_manager, mock_api_client):
        """ミュート済みユーザー取得成功テスト"""
        test_result = Mock()
        test_result.mutes = [
            {"handle": "muted1.bsky.social", "did": "did:plc:muted123"},
            {"handle": "muted2.bsky.social", "did": "did:plc:muted456"}
        ]
        
        mock_api_client.client.app.bsky.graph.get_mutes.return_value = test_result
        
        result = user_manager.get_muted_users(limit=50)
        
        mock_api_client.client.app.bsky.graph.get_mutes.assert_called_once_with(params={
            'limit': 50,
            'cursor': None
        })
        
        assert result == test_result


@pytest.mark.unit
class TestBlueskyUserManagerErrorHandling:
    """BlueskyUserManagerエラーハンドリングテスト"""
    
    def test_follow_error_propagation(self, user_manager, mock_api_client):
        """フォローエラー伝播テスト"""
        test_handle = "alice.bsky.social"
        test_error = AtProtocolError("Follow API failed")
        
        mock_api_client.client.follow.side_effect = test_error
        
        with pytest.raises(AtProtocolError):
            user_manager.follow(test_handle)
    
    def test_block_did_resolution_error(self, user_manager, mock_api_client):
        """ブロック時DID解決エラーテスト"""
        test_handle = "nonexistent.bsky.social"
        test_error = AtProtocolError("Handle not found")
        
        mock_api_client.client.resolve_handle.side_effect = test_error
        
        with pytest.raises(AtProtocolError):
            user_manager.block(test_handle)
    
    def test_unblock_search_error(self, user_manager, mock_api_client, mock_auth_manager):
        """ブロック解除時レコード検索エラーテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # プロフィール情報のモック（ブロック情報なし）
        mock_profile = Mock()
        mock_profile.viewer = Mock()
        mock_profile.viewer.blocking = None
        mock_api_client.client.get_profile.return_value = mock_profile
        
        # レコード検索エラー
        test_error = AtProtocolError("Record search failed")
        mock_api_client.client.com.atproto.repo.list_records.side_effect = test_error
        
        with pytest.raises(Exception, match="ブロックレコードの検索に失敗しました"):
            user_manager.unblock(test_handle)
    
    def test_mute_complete_api_failure(self, user_manager, mock_api_client, mock_auth_manager):
        """ミュート時全APIエラーテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 全てのAPIが失敗
        mock_api_client.client.app.bsky.graph.mute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.mute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.com.atproto.repo.create_record.side_effect = AtProtocolError("Create record failed")
        
        with pytest.raises(AtProtocolError):
            user_manager.mute(test_handle)
    
    def test_unmute_complete_api_failure(self, user_manager, mock_api_client):
        """ミュート解除時全APIエラーテスト"""
        test_handle = "alice.bsky.social"
        test_did = "did:plc:alice123"
        
        # DID解決のモック
        mock_resolve_response = Mock()
        mock_resolve_response.did = test_did
        mock_api_client.client.resolve_handle.return_value = mock_resolve_response
        
        # 全てのAPIが失敗
        mock_api_client.client.app.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        mock_api_client.client.bsky.graph.unmute_actor.side_effect = AttributeError("Method not found")
        
        # プロフィール確認もスキップ、標準APIも失敗
        mock_api_client.client.get_profile.return_value = Mock()  # viewer.mutedなし
        mock_api_client.client.unmute_actor.side_effect = AttributeError("Method not found")
        
        with pytest.raises(Exception, match="ミュート解除の適切なAPIが見つかりませんでした"):
            user_manager.unmute(test_handle)