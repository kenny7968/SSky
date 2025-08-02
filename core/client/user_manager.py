#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
ユーザー関連操作を担当するクラス
"""

import logging
import typing
from datetime import datetime, timezone
from atproto.exceptions import AtProtocolError
from atproto import models

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyUserManager:
    """ユーザー関連操作を担当するクラス
    
    フォロー、ブロック、ミュート、ユーザー情報取得などの
    ユーザー関連操作を統合的に管理します。
    """
    
    def __init__(self, api_client=None, auth_manager=None):
        """初期化
        
        Args:
            api_client (BlueskyApiClient, optional): APIクライアントインスタンス
            auth_manager (BlueskyAuthManager, optional): 認証管理インスタンス
        """
        self.api_client = api_client
        self.auth_manager = auth_manager
        
    def follow(self, handle):
        """ユーザーをフォロー
        
        Args:
            handle (str): フォローするユーザーのハンドル
            
        Returns:
            object: フォロー結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーをフォローしています: {handle}")
        
        # フォローを実行
        result = self.api_client.client.follow(handle)
        
        logger.info("フォローが完了しました")
        return result
            
    def unfollow(self, handle):
        """ユーザーのフォローを解除
        
        Args:
            handle (str): フォロー解除するユーザーのハンドル
            
        Returns:
            object: フォロー解除結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーのフォローを解除しています: {handle}")
        
        # プロフィールからフォロー情報を取得
        profile = self.api_client.client.get_profile(actor=handle)
        follow_uri = None
        
        if hasattr(profile, 'viewer') and hasattr(profile.viewer, 'following'):
            follow_uri = profile.viewer.following
            logger.debug(f"フォローレコードURI: {follow_uri}")
        
        if follow_uri:
            # URIからレコードキーを抽出
            # URI形式: at://did:plc:xxxxx/app.bsky.graph.follow/yyyyy
            uri_parts = follow_uri.split('/')
            rkey = uri_parts[-1]  # 最後の部分がrkey
            
            # 自分のDIDを使用
            repo = self.auth_manager.user_did
            
            # フォローレコードのコレクション名
            collection = 'app.bsky.graph.follow'
            
            # レコードを削除（dataオブジェクトとして渡す）
            result = self.api_client.client.com.atproto.repo.delete_record(data={
                'repo': repo,
                'collection': collection,
                'rkey': rkey
            })
            logger.info("URIを使用してフォロー解除しました")
        else:
            # DIDを取得
            response = self.api_client.client.resolve_handle(handle=handle)
            target_did = response.did
            logger.debug(f"対象ユーザーのDID: {target_did}")
            
            # フォローレコードが見つからない場合は標準のAPIを使用
            logger.warning(f"フォローレコードが見つかりませんでした。標準APIを使用します: {handle}")
            result = self.api_client.client.delete_follow(did=target_did)
            logger.info("標準APIを使用してフォロー解除しました")
        
        logger.info("フォロー解除が完了しました")
        return result
            
    def block(self, handle):
        """ユーザーをブロック
        
        Args:
            handle (str): ブロックするユーザーのハンドル
            
        Returns:
            object: ブロック結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーをブロックしています: {handle}")
        
        # DIDを取得
        response = self.api_client.client.resolve_handle(handle=handle)
        target_did = response.did
        logger.debug(f"対象ユーザーのDID: {target_did}")
        
        # ブロックを実行
        # RFC-3339形式の日時（タイムゾーン情報を含む）
        created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        logger.debug(f"生成された日時フォーマット: {created_at}")
        
        try:
            # AppBskyGraphBlockRecordを使用してブロックを実行
            result = self.api_client.client.app.bsky.graph.block.create({
                'repo': self.auth_manager.user_did,
                'record': {
                    'subject': target_did,
                    'createdAt': created_at
                }
            })
            logger.info("app.bsky.graph.block.createを使用してブロックしました")
        except (AttributeError, Exception) as e1:
            logger.debug(f"app.bsky.graph.block.createでのブロックに失敗: {str(e1)}")
            # 低レベルAPIを使用（代替方法）
            result = self.api_client.client.com.atproto.repo.create_record(data={
                'repo': self.auth_manager.user_did,
                'collection': 'app.bsky.graph.block',
                'record': {
                    'subject': target_did,
                    'createdAt': created_at
                }
            })
            logger.info("低レベルAPIを使用してブロックしました")
        
        logger.info("ブロックが完了しました")
        return result
            
    def unblock(self, handle):
        """ユーザーのブロックを解除
        
        Args:
            handle (str): ブロック解除するユーザーのハンドル
            
        Returns:
            object: ブロック解除結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーのブロックを解除しています: {handle}")
        
        # DIDを取得
        response = self.api_client.client.resolve_handle(handle=handle)
        target_did = response.did
        logger.debug(f"対象ユーザーのDID: {target_did}")
        
        # プロフィールからブロック情報を取得
        profile = self.api_client.client.get_profile(actor=handle)
        block_uri = None
        
        if hasattr(profile, 'viewer') and hasattr(profile.viewer, 'blocking'):
            block_uri = profile.viewer.blocking
            logger.debug(f"ブロックレコードURI: {block_uri}")
        
        if block_uri:
            # URIからレコードキーを抽出
            # URI形式: at://did:plc:xxxxx/app.bsky.graph.block/yyyyy
            uri_parts = block_uri.split('/')
            rkey = uri_parts[-1]  # 最後の部分がrkey
            
            # 自分のDIDを使用
            repo = self.auth_manager.user_did
            
            # ブロックレコードのコレクション名
            collection = 'app.bsky.graph.block'
            
            try:
                # AppBskyGraphBlockRecordを使用してブロック解除を実行
                result = self.api_client.client.app.bsky.graph.block.delete({
                    'repo': repo,
                    'rkey': rkey
                })
                logger.info("app.bsky.graph.block.deleteを使用してブロック解除しました")
            except (AttributeError, Exception) as e1:
                logger.debug(f"app.bsky.graph.block.deleteでのブロック解除に失敗: {str(e1)}")
                # 低レベルAPIを使用（代替方法）
                result = self.api_client.client.com.atproto.repo.delete_record(data={
                    'repo': repo,
                    'collection': collection,
                    'rkey': rkey
                })
                logger.info("低レベルAPIを使用してブロック解除しました")
            
            logger.info("URIを使用してブロック解除しました")
        else:
            # ブロックレコードが見つからない場合、ブロックレコードを検索
            try:
                # ブロックコレクションからレコードを検索
                blocks_list = self.api_client.client.com.atproto.repo.list_records(data={
                    'repo': self.auth_manager.user_did,
                    'collection': 'app.bsky.graph.block',
                    'limit': 100
                })
                
                # 対象ユーザーのブロックレコードを探す
                block_record = None
                for record in blocks_list.records:
                    if record.value.get('subject') == target_did:
                        block_record = record
                        break
                
                if block_record:
                    # ブロックレコードが見つかった場合、削除
                    rkey = block_record.rkey
                    result = self.api_client.client.com.atproto.repo.delete_record(data={
                        'repo': self.auth_manager.user_did,
                        'collection': 'app.bsky.graph.block',
                        'rkey': rkey
                    })
                    logger.info(f"検索したブロックレコードを削除しました: rkey={rkey}")
                else:
                    logger.warning(f"ユーザー {handle} (DID: {target_did}) のブロックレコードが見つかりませんでした")
                    # ブロックされていない場合は成功として扱う
                    return {'success': True, 'message': 'ユーザーはブロックされていません'}
            except Exception as e2:
                logger.error(f"ブロックレコードの検索に失敗しました: {str(e2)}")
                raise Exception(f"ブロックレコードの検索に失敗しました: {str(e2)}")
        
        logger.info("ブロック解除が完了しました")
        return result
            
    def mute(self, handle):
        """ユーザーをミュート
        
        Args:
            handle (str): ミュートするユーザーのハンドル
            
        Returns:
            object: ミュート結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーをミュートしています: {handle}")
        
        # DIDを取得
        response = self.api_client.client.resolve_handle(handle=handle)
        target_did = response.did
        
        # ミュートを実行（名前空間を使用）
        try:
            # 方法1: app.bsky.graph名前空間を使用
            result = self.api_client.client.app.bsky.graph.mute_actor(data={'actor': target_did})
            logger.info("app.bsky.graph.mute_actorを使用してミュートしました")
        except (AttributeError, Exception) as e1:
            logger.debug(f"app.bsky.graph.mute_actorでのミュートに失敗: {str(e1)}")
            try:
                # 方法2: bsky.graph名前空間を使用
                result = self.api_client.client.bsky.graph.mute_actor(data={'actor': target_did})
                logger.info("bsky.graph.mute_actorを使用してミュートしました")
            except (AttributeError, Exception) as e2:
                logger.debug(f"bsky.graph.mute_actorでのミュートに失敗: {str(e2)}")
                # 方法3: 低レベルAPIを直接呼び出す
                # RFC-3339形式の日時（タイムゾーン情報を含む）
                created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                logger.debug(f"生成された日時フォーマット: {created_at}")
                
                result = self.api_client.client.com.atproto.repo.create_record(data={
                    'repo': self.auth_manager.user_did,
                    'collection': 'app.bsky.graph.mute',
                    'record': {
                        'subject': target_did,
                        'createdAt': created_at
                    }
                })
                logger.info("低レベルAPIを使用してミュートしました")
        
        logger.info("ミュートが完了しました")
        return result
            
    def unmute(self, handle):
        """ユーザーのミュートを解除
        
        Args:
            handle (str): ミュート解除するユーザーのハンドル
            
        Returns:
            object: ミュート解除結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザーのミュートを解除しています: {handle}")
        
        # DIDを取得
        response = self.api_client.client.resolve_handle(handle=handle)
        target_did = response.did
        
        # ミュート解除を実行（名前空間を使用）
        try:
            # 方法1: app.bsky.graph名前空間を使用
            result = self.api_client.client.app.bsky.graph.unmute_actor(data={'actor': target_did})
            logger.info("app.bsky.graph.unmute_actorを使用してミュート解除しました")
        except (AttributeError, Exception) as e1:
            logger.debug(f"app.bsky.graph.unmute_actorでのミュート解除に失敗: {str(e1)}")
            try:
                # 方法2: bsky.graph名前空間を使用
                result = self.api_client.client.bsky.graph.unmute_actor(data={'actor': target_did})
                logger.info("bsky.graph.unmute_actorを使用してミュート解除しました")
            except (AttributeError, Exception) as e2:
                logger.debug(f"bsky.graph.unmute_actorでのミュート解除に失敗: {str(e2)}")
                # 方法3: 低レベルAPIを直接呼び出す
                # ミュートレコードを検索して削除する必要があります
                # プロフィールからミュート情報を取得
                profile = self.api_client.client.get_profile(actor=handle)
                mute_uri = None
                
                if hasattr(profile, 'viewer') and hasattr(profile.viewer, 'muted'):
                    # ミュート状態を確認
                    is_muted = bool(profile.viewer.muted)
                    if not is_muted:
                        logger.info(f"ユーザー {handle} は既にミュート解除されています")
                        return None
                        
                # ミュートレコードを検索
                # 注意: 現在のAPIではミュートレコードのURIを直接取得する方法がないため、
                # 代替として標準のunmute_actorメソッドを試みます
                try:
                    result = self.api_client.client.unmute_actor(actor=target_did)
                    logger.info("標準APIを使用してミュート解除しました")
                except (AttributeError, Exception) as e3:
                    logger.error(f"ミュート解除に失敗しました: 適切なAPIが見つかりません: {str(e3)}")
                    raise Exception("ミュート解除の適切なAPIが見つかりませんでした")
        
        logger.info("ミュート解除が完了しました")
        return result
            
    def get_following(self, handle, limit=100, cursor=None):
        """フォロー中ユーザー一覧を取得
        
        Args:
            handle (str): ユーザーハンドル
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: フォロー中ユーザー一覧
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザー {handle} のフォロー中ユーザー一覧を取得しています...")
        
        # app.bsky.graph.getFollows APIを呼び出し
        result = self.api_client.client.app.bsky.graph.get_follows({
            'actor': handle,
            'limit': min(limit, 100),  # 最大100件まで
            'cursor': cursor
        })
        
        logger.info(f"フォロー中ユーザー一覧を取得しました: {len(result.follows)}件")
        return result
            
    def get_followers(self, handle, limit=100, cursor=None):
        """フォロワー一覧を取得
        
        Args:
            handle (str): ユーザーハンドル
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: フォロワー一覧
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ユーザー {handle} のフォロワー一覧を取得しています...")
        
        # app.bsky.graph.getFollowers APIを呼び出し
        result = self.api_client.client.app.bsky.graph.get_followers({
            'actor': handle,
            'limit': min(limit, 100),  # 最大100件まで
            'cursor': cursor
        })
        
        logger.info(f"フォロワー一覧を取得しました: {len(result.followers)}件")
        return result

    def get_blocked_users(self, limit=100, cursor=None):
        """ブロックしたユーザー一覧を取得
        
        Args:
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: ブロックしたユーザー一覧
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info("ブロックしたユーザー一覧を取得しています...")
        
        # app.bsky.graph.getBlocks APIを呼び出し
        result = self.api_client.client.app.bsky.graph.get_blocks(params={
            'limit': min(limit, 100),  # 最大100件まで
            'cursor': cursor
        })
        
        logger.info(f"ブロックしたユーザー一覧を取得しました: {len(result.blocks)}件")
        return result
            
    def get_muted_users(self, limit=100, cursor=None):
        """ミュートしたユーザー一覧を取得
        
        Args:
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: ミュートしたユーザー一覧
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info("ミュートしたユーザー一覧を取得しています...")
        
        # app.bsky.graph.getMutes APIを呼び出し
        result = self.api_client.client.app.bsky.graph.get_mutes(params={
            'limit': min(limit, 100),  # 最大100件まで
            'cursor': cursor
        })
        
        logger.info(f"ミュートしたユーザー一覧を取得しました: {len(result.mutes)}件")
        return result