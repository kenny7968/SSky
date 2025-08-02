#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
API操作を担当するクライアントクラス
"""

import logging
import mimetypes
import typing
from atproto import Client as AtprotoClient
from atproto.exceptions import AtProtocolError
from atproto import models

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyApiClient:
    """Bluesky API呼び出しを担当するクラス
    
    atprotoライブラリの直接APIラッパーとして機能し、以下を提供:
    - タイムライン取得
    - 投稿、いいね、リプライ、リポストなどのアクション
    - ユーザー関連操作（フォロー、ブロック、ミュートなど）
    """
    
    def __init__(self, session_manager=None):
        """初期化
        
        Args:
            session_manager (SessionManager, optional): セッション管理インスタンス
        """
        self.session_manager = session_manager
        self.client = AtprotoClient()
        
    def get_timeline(self, limit=50):
        """タイムラインを取得
        
        Args:
            limit (int): 取得する投稿数
            
        Returns:
            object: タイムラインデータ
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info("タイムラインを取得しています...")
        timeline_data = self.client.get_timeline(limit=limit)
        
        logger.info(f"タイムラインを取得しました: {len(timeline_data.feed)}件")
        return timeline_data
            
    def send_post(self, text, images=None):
        """投稿を送信
        
        Args:
            text (str): 投稿内容
            images (list, optional): 画像ブロブのリスト
            
        Returns:
            object: 投稿結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info("投稿を送信しています...")
        
        # 画像付き投稿
        if images:
            result = self.client.send_post(text=text, images=images)
        else:
            # テキストのみ投稿
            result = self.client.send_post(text=text)
            
        logger.info("投稿が完了しました")
        return result
            
    def upload_blob(self, file_data, mime_type=None):
        """ファイルをアップロード
        
        Args:
            file_data (bytes): ファイルデータ
            mime_type (str, optional): MIMEタイプ
            
        Returns:
            object: アップロード結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"ファイルをアップロードしています: {mime_type}")
        
        # ファイルをアップロード
        blob = self.client.upload_blob(file_data, mime_type)
        
        logger.info("ファイルのアップロードが完了しました")
        return blob
            
    def like(self, uri, cid):
        """投稿にいいねする
        
        Args:
            uri (str): 投稿のURI
            cid (str): 投稿のCID
            
        Returns:
            object: いいね結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿にいいねしています: {uri}")
        
        # いいねを付ける
        result = self.client.like(uri, cid)
        
        logger.info("いいねが完了しました")
        return result
            
    def delete_post(self, uri):
        """投稿を削除
        
        Args:
            uri (str): 投稿のURI
            
        Returns:
            object: 削除結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿を削除しています: {uri}")
        
        # 投稿を削除
        result = self.client.delete_post(uri)
        
        logger.info("投稿の削除が完了しました")
        return result
            
    def reply_to_post(self, text, reply_to):
        """投稿に返信
        
        Args:
            text (str): 返信内容
            reply_to (dict): 返信先情報 {'uri': uri, 'cid': cid, 'reply_parent': {...}, 'reply_root': {...}}
            
        Returns:
            object: 返信結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿に返信しています: {reply_to['uri']}")
        
        # 返信を送信
        # Bluesky APIでは、reply.parentとreply.rootが必要
        reply_params = {
            'parent': {
                'uri': reply_to['uri'],
                'cid': reply_to['cid']
            }
        }
        
        # ルート投稿の情報を設定
        # 返信先の投稿がすでに返信である場合（スレッド内の返信）
        if 'reply_root' in reply_to and reply_to['reply_root']:
            # 元の投稿のルートを使用
            reply_params['root'] = {
                'uri': reply_to['reply_root']['uri'],
                'cid': reply_to['reply_root']['cid']
            }
            logger.debug(f"スレッド内の返信: root={reply_params['root']['uri']}")
        elif 'reply_parent' in reply_to and reply_to['reply_parent']:
            # 返信先が返信で、ルートが設定されていない場合は親の親をルートとして使用
            reply_params['root'] = {
                'uri': reply_to['reply_parent']['uri'],
                'cid': reply_to['reply_parent']['cid']
            }
            logger.debug(f"親の親をルートとして使用: root={reply_params['root']['uri']}")
        else:
            # 返信先自体がルート（スレッドの最初の投稿への返信）
            reply_params['root'] = {
                'uri': reply_to['uri'],
                'cid': reply_to['cid']
            }
            logger.debug(f"スレッドの最初の投稿への返信: root={reply_params['root']['uri']}")
        
        result = self.client.send_post(
            text=text,
            reply_to=reply_params
        )
        
        logger.info("返信が完了しました")
        return result
            
    def quote_post(self, text, quote_of):
        """投稿を引用
        
        Args:
            text (str): 引用コメント
            quote_of (dict): 引用元情報 {'uri': uri, 'cid': cid}
            
        Returns:
            object: 引用結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿を引用しています: {quote_of['uri']}")
        
        # 引用投稿を送信
        result = self.client.send_post(
            text=text,
            quote=quote_of
        )
        
        logger.info("引用投稿が完了しました")
        return result
    
    def repost(self, repost_of):
        """投稿をリポスト
        
        Args:
            repost_of (dict): リポスト元情報 {'uri': uri, 'cid': cid}
            
        Returns:
            object: リポスト結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿をリポストしています: {repost_of['uri']}")
        
        # リポストを送信
        result = self.client.repost(
            repost_of['uri'],
            repost_of['cid']
        )
        
        logger.info("リポストが完了しました")
        return result
    
    def get_profile(self, handle):
        """プロフィールを取得
        
        Args:
            handle (str): ユーザーハンドル
            
        Returns:
            object: プロフィール情報
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"プロフィールを取得しています: {handle}")
        
        # プロフィールを取得
        profile = self.client.get_profile(handle)
        
        logger.info(f"プロフィールを取得しました: {handle}")
        return profile
    
    def get_follows(self, actor):
        """フォロー中のユーザーを取得
        
        Args:
            actor (str): ユーザーDIDまたはハンドル
            
        Returns:
            object: フォロー情報
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"フォロー中のユーザーを取得しています: {actor}")
        
        # フォロー情報を取得
        follows = self.client.get_follows(actor)
        
        logger.info(f"フォロー中のユーザーを取得しました: {actor}, {len(follows.follows)}件")
        return follows
    
    def get_followers(self, actor):
        """フォロワーを取得
        
        Args:
            actor (str): ユーザーDIDまたはハンドル
            
        Returns:
            object: フォロワー情報
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"フォロワーを取得しています: {actor}")
        
        # フォロワー情報を取得
        followers = self.client.get_followers(actor)
        
        logger.info(f"フォロワーを取得しました: {actor}, {len(followers.followers)}件")
        return followers
    
    def quote_post_advanced(self, text, quote_of):
        """投稿を引用（高度なバージョン）
        
        Args:
            text (str): 引用コメント
            quote_of (dict): 引用元情報 {'uri': uri, 'cid': cid}
            
        Returns:
            object: 引用結果
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        logger.info(f"投稿を引用しています（高度版）: {quote_of['uri']}")
        
        # 1. 引用元への参照 (StrongRef) を作成
        quote_record_ref = models.ComAtprotoRepoStrongRef.Main(
            uri=quote_of['uri'],
            cid=quote_of['cid']
        )
        
        # 2. 参照情報を埋め込みデータ (EmbedRecord) としてラップ
        embed_data = models.AppBskyEmbedRecord.Main(record=quote_record_ref)
        
        # 3. 引用を送信（日本語投稿として言語を指定）
        result = self.client.post(
            text=text,
            embed=embed_data,
            langs=['ja']  # 日本語投稿として言語を指定
        )
        
        logger.info("引用が完了しました（高度版）")
        return result