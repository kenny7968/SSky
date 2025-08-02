#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインデータ管理クラス
"""

import logging
import time
from utils.time_format import format_relative_time
from atproto import models
from core.exceptions import AuthenticationError

# ロガーの設定
logger = logging.getLogger(__name__)

class TimelineDataManager:
    """タイムラインデータ管理クラス
    
    タイムラインのデータ取得と処理を担当します。
    """
    
    def __init__(self, client=None):
        """初期化
        
        Args:
            client (BlueskyClient, optional): Blueskyクライアント
        """
        self.client = client
        self.posts = []
        self.post_count = 0
        self.fetch_count = 50  # デフォルト：50件
    
    def set_fetch_count(self, count):
        """取得件数を設定
        
        Args:
            count (int): 取得件数
        """
        self.fetch_count = max(10, min(100, count))  # 10〜100の範囲に制限
    
    def fetch_data(self, client=None, limit=None):
        """APIからデータを取得
        
        Args:
            client (BlueskyClient, optional): Blueskyクライアント
            limit (int, optional): 取得する投稿数
            
        Returns:
            list: 処理済みの投稿リスト
            
        Raises:
            AuthenticationError: 認証エラーの場合
            Exception: その他のエラー
        """
        # クライアントが渡された場合はインスタンス変数を更新
        if client:
            self.client = client
            
        # 取得件数の設定
        if limit:
            self.fetch_count = limit
            
        # クライアントがない場合はエラー
        if not self.client or not self.client.is_logged_in:
            logger.warning("タイムラインの取得に失敗しました: クライアントが設定されていないか、ログインしていません")
            raise Exception("タイムラインの取得にはログインしたクライアントが必要です")
            
        # タイムラインの取得
        logger.info(f"タイムラインを取得しています... (最大{self.fetch_count}件)")
        timeline_data = self.client.get_timeline(limit=self.fetch_count)
        
        # タイムラインデータを処理
        return self._process_timeline_data(timeline_data)
    
    def _process_timeline_data(self, timeline_data):
        """取得したタイムラインデータを処理
        
        Args:
            timeline_data: APIから取得したタイムラインデータ
            
        Returns:
            list: 処理済みの投稿リスト
            dict: 投稿URIから投稿データへのマッピング
        """
        # 新しく取得した投稿のURIセットを作成（高速検索用）
        new_post_uris = set()
        new_posts_dict = {}  # 一時的な辞書（URIをキー）
        
        # 取得した投稿を処理
        for post in timeline_data.feed:
            # 投稿データを適切な形式に変換
            post_data = self._format_post_data(post)
            
            uri = post_data['uri']
            if uri:
                new_post_uris.add(uri)
                new_posts_dict[uri] = post_data
        
        return new_posts_dict, new_post_uris
    
    def _format_post_data(self, post):
        """投稿データを整形
        
        Args:
            post: APIから取得した投稿データ
            
        Returns:
            dict: 整形された投稿データ
        """
        # 投稿データを適切な形式に変換
        post_data = {
            'username': post.post.author.display_name or post.post.author.handle,
            'handle': f"@{post.post.author.handle}",
            'author_handle': post.post.author.handle,  # 投稿者のハンドル（@なし）
            'content': post.post.record.text,
            'time': format_relative_time(post.post.indexed_at),  # 表示用の文字列
            'raw_timestamp': post.post.indexed_at,  # ソート用のオリジナルタイムスタンプ
            'likes': getattr(post.post, 'like_count', 0),
            'replies': getattr(post.post, 'reply_count', 0),
            'reposts': getattr(post.post, 'repost_count', 0),
            'uri': getattr(post.post, 'uri', None),  # 投稿のURI（削除に必要）
            'cid': getattr(post.post, 'cid', None),  # 投稿のCID（削除に必要）
            'is_own_post': post.post.author.handle == self.client.profile.handle,  # 自分の投稿かどうか
            # スレッド情報を追加
            'reply_parent': None,
            'reply_root': None,
            # facets情報を追加（URLなどの特殊要素の情報）
            'facets': getattr(post.post.record, 'facets', None),
            # 引用ポスト情報を初期化
            'quote_of': None,
            'is_quote_post': False
        }
        
        # embedフィールドの確認（引用ポストかどうか）
        if hasattr(post.post, 'embed'):
            post_data = self._process_embed(post.post, post_data)
        
        # スレッド情報を取得（返信の場合）
        if hasattr(post.post.record, 'reply') and post.post.record.reply:
            post_data = self._process_reply(post.post.record.reply, post_data)
            
        return post_data
    
    def _process_embed(self, post, post_data):
        """embedフィールドを処理（引用ポストなど）
        
        Args:
            post: 投稿データ
            post_data (dict): 整形中の投稿データ
            
        Returns:
            dict: 更新された投稿データ
        """
        embed = post.embed
        
        # 引用ポストの場合
        if isinstance(embed, models.AppBskyEmbedRecord.View):
            logger.debug(f"引用ポストを検出: {post.uri}")
            
            # 引用元レコードの情報を取得
            if hasattr(embed, 'record'):
                quoted_record = embed.record
                
                # ViewRecordの場合（通常のケース）
                if isinstance(quoted_record, models.AppBskyEmbedRecord.ViewRecord):
                    quoted_author = quoted_record.author
                    quoted_text = getattr(quoted_record.value, 'text', '[引用元テキストなし]')
                    
                    # 引用元情報を設定
                    post_data['is_quote_post'] = True
                    post_data['quote_of'] = {
                        'username': quoted_author.display_name or quoted_author.handle,
                        'handle': f"@{quoted_author.handle}",
                        'content': quoted_text,
                        'uri': getattr(quoted_record, 'uri', None),
                        'cid': getattr(quoted_record, 'cid', None),
                        'like_count': getattr(quoted_record, 'like_count', 0),
                        'repost_count': getattr(quoted_record, 'repost_count', 0)
                    }
                    logger.debug(f"引用元情報: {quoted_author.handle} - {quoted_text[:30]}...")
                
                # 引用元が見つからない場合
                elif isinstance(quoted_record, models.AppBskyEmbedRecord.ViewNotFound):
                    post_data['is_quote_post'] = True
                    post_data['quote_of'] = {
                        'username': '不明',
                        'handle': '@unknown',
                        'content': '[引用元投稿が見つかりません]',
                        'uri': None,
                        'cid': None
                    }
                    logger.debug("引用元投稿が見つかりません")
                
                # 引用元がブロックされている場合
                elif isinstance(quoted_record, models.AppBskyEmbedRecord.ViewBlocked):
                    post_data['is_quote_post'] = True
                    post_data['quote_of'] = {
                        'username': 'ブロック',
                        'handle': '@blocked',
                        'content': '[引用元投稿はブロックされています]',
                        'uri': None,
                        'cid': None
                    }
                    logger.debug("引用元投稿はブロックされています")
        
        # 引用ポスト + メディアの場合
        elif isinstance(embed, models.AppBskyEmbedRecordWithMedia.View):
            logger.debug(f"引用ポスト + メディアを検出: {post.uri}")
            
            # 引用元レコードの情報を取得
            if hasattr(embed, 'record') and hasattr(embed.record, 'record'):
                quoted_record = embed.record.record
                
                # ViewRecordの場合（通常のケース）
                if isinstance(quoted_record, models.AppBskyEmbedRecord.ViewRecord):
                    quoted_author = quoted_record.author
                    quoted_text = getattr(quoted_record.value, 'text', '[引用元テキストなし]')
                    
                    # 引用元情報を設定
                    post_data['is_quote_post'] = True
                    post_data['quote_of'] = {
                        'username': quoted_author.display_name or quoted_author.handle,
                        'handle': f"@{quoted_author.handle}",
                        'content': quoted_text,
                        'uri': getattr(quoted_record, 'uri', None),
                        'cid': getattr(quoted_record, 'cid', None),
                        'like_count': getattr(quoted_record, 'like_count', 0),
                        'repost_count': getattr(quoted_record, 'repost_count', 0)
                    }
                    logger.debug(f"引用元情報 (メディア付き): {quoted_author.handle} - {quoted_text[:30]}...")
        
        return post_data
    
    def _process_reply(self, reply, post_data):
        """返信情報を処理
        
        Args:
            reply: 返信データ
            post_data (dict): 整形中の投稿データ
            
        Returns:
            dict: 更新された投稿データ
        """
        logger.debug(f"返信投稿を検出: {post_data['uri']}")
        
        # 親投稿の情報
        if hasattr(reply, 'parent'):
            parent_uri = getattr(reply.parent, 'uri', None)
            parent_cid = getattr(reply.parent, 'cid', None)
            
            if parent_uri and parent_cid:
                post_data['reply_parent'] = {
                    'uri': parent_uri,
                    'cid': parent_cid
                }
                logger.debug(f"親投稿情報: {parent_uri}")
        
        # ルート投稿の情報
        if hasattr(reply, 'root'):
            root_uri = getattr(reply.root, 'uri', None)
            root_cid = getattr(reply.root, 'cid', None)
            
            if root_uri and root_cid:
                post_data['reply_root'] = {
                    'uri': root_uri,
                    'cid': root_cid
                }
                logger.debug(f"ルート投稿情報: {root_uri}")
                
        return post_data
    
    def update_timeline_data(self, existing_posts, new_posts_dict, new_post_uris):
        """タイムラインデータを更新
        
        Args:
            existing_posts (list): 既存の投稿リスト
            new_posts_dict (dict): 新しい投稿データ（URIをキー）
            new_post_uris (set): 新しい投稿のURIセット
            
        Returns:
            list: 更新された投稿リスト
        """
        # 既存の投稿URIセットとマッピングを作成
        existing_post_uris = set()
        uri_to_index = {}  # URIからリストのインデックスへのマッピング
        
        for i, post in enumerate(existing_posts):
            if 'uri' in post and post['uri']:
                uri = post['uri']
                existing_post_uris.add(uri)
                uri_to_index[uri] = i
        
        # 1. 新しく追加された投稿を特定
        added_uris = new_post_uris - existing_post_uris
        
        # 2. 更新された投稿を特定（両方のセットに存在するURI）
        updated_uris = new_post_uris.intersection(existing_post_uris)
        updated_count = 0
        
        # テンポラリの投稿リストを作成（既存の投稿をコピー）
        temp_posts = existing_posts.copy()
        
        # 既存の投稿を更新（インデックスマッピングを使用して高速化）
        for uri in updated_uris:
            if uri in uri_to_index:
                index = uri_to_index[uri]
                # 実際に変更があるかチェック（いいね数、リポスト数、返信数）
                old_post = temp_posts[index]
                new_post = new_posts_dict[uri]
                
                if (old_post['likes'] != new_post['likes'] or 
                    old_post['reposts'] != new_post['reposts'] or 
                    old_post['replies'] != new_post['replies']):
                    # 投稿を更新
                    temp_posts[index] = new_post
                    updated_count += 1
        
        # 新しい投稿を追加
        for uri in added_uris:
            temp_posts.append(new_posts_dict[uri])
        
        # 投稿を日時でソート（古い順）
        temp_posts.sort(key=lambda x: x['raw_timestamp'])
        
        # 投稿数を制限（オプション）
        max_posts = 1000  # 保持する最大投稿数
        if len(temp_posts) > max_posts:
            # 新しい投稿を優先して保持（古い投稿を削除）
            temp_posts = temp_posts[len(temp_posts) - max_posts:]
            logger.debug(f"古い投稿を削除しました。残り{len(temp_posts)}件")
        
        logger.info(f"タイムラインを更新しました: 新規={len(added_uris)}件, 更新={updated_count}件, 合計={len(temp_posts)}件")
        
        # 更新された投稿リストを返す
        return temp_posts
    
    def find_post_by_uri(self, uri):
        """URIから投稿を検索
        
        Args:
            uri (str): 検索する投稿のURI
            
        Returns:
            dict: 投稿データ。見つからない場合はNone
        """
        if not uri:
            return None
            
        for post in self.posts:
            if post.get('uri') == uri:
                return post
        return None