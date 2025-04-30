#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
非同期投稿処理ハンドラ
"""

import threading
import wx
from pubsub import pub
import logging
from core import events
from utils.file_utils import read_binary_file, get_mime_type

# ロガーの設定
logger = logging.getLogger(__name__)

class AsyncPostHandler:
    """非同期投稿処理クラス"""
    
    @staticmethod
    def submit_post(client, text, images=None):
        """投稿を非同期で送信
        
        Args:
            client: Blueskyクライアント
            text: 投稿内容
            images: 添付画像のリスト（オプション）
        """
        # イベント発行（投稿開始）
        wx.CallAfter(pub.sendMessage, events.POST_SUBMIT_START)
        
        # 投稿処理スレッドを開始
        thread = threading.Thread(
            target=AsyncPostHandler._post_thread,
            args=(client, text, images)
        )
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def _post_thread(client, text, images):
        """投稿処理スレッド
        
        Args:
            client: Blueskyクライアント
            text: 投稿内容
            images: 添付画像のリスト（オプション）
        """
        try:
            # 画像付き投稿
            if images:
                # 画像をアップロード
                uploaded_blobs = []
                for file_path in images:
                    # ファイルデータを読み込み
                    file_data = read_binary_file(file_path)
                    if not file_data:
                        raise Exception(f"ファイルの読み込みに失敗しました: {file_path}")
                        
                    # ファイルの種類を判定
                    mime_type = get_mime_type(file_path)
                    
                    # ファイルをアップロード
                    blob = client.upload_blob(file_data, mime_type)
                    uploaded_blobs.append(blob)
                
                # 画像付きで投稿
                result = client.send_post(text=text, images=uploaded_blobs)
            else:
                # テキストのみ投稿
                result = client.send_post(text=text)
            
            # 投稿成功イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.POST_SUBMIT_SUCCESS, result=result)
            
        except Exception as e:
            logger.error(f"投稿処理中にエラーが発生しました: {str(e)}", exc_info=True)
            # 投稿失敗イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.POST_SUBMIT_FAILURE, error=e)
    
    @staticmethod
    def like_post(client, uri, cid):
        """投稿にいいねを非同期で付ける
        
        Args:
            client: Blueskyクライアント
            uri: 投稿のURI
            cid: 投稿のCID
        """
        # イベント発行（いいね開始）
        wx.CallAfter(pub.sendMessage, events.LIKE_START, uri=uri)
        
        # いいね処理スレッドを開始
        thread = threading.Thread(
            target=AsyncPostHandler._like_thread,
            args=(client, uri, cid)
        )
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def _like_thread(client, uri, cid):
        """いいね処理スレッド
        
        Args:
            client: Blueskyクライアント
            uri: 投稿のURI
            cid: 投稿のCID
        """
        try:
            # いいねを付ける
            result = client.like(uri, cid)
            
            # いいね成功イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.LIKE_SUCCESS, result=result, uri=uri)
            
        except Exception as e:
            logger.error(f"いいね処理中にエラーが発生しました: {str(e)}", exc_info=True)
            # いいね失敗イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.LIKE_FAILURE, error=e, uri=uri)
    
    @staticmethod
    def repost(client, repost_of):
        """投稿を非同期でリポスト
        
        Args:
            client: Blueskyクライアント
            repost_of: リポスト元情報 {'uri': uri, 'cid': cid}
        """
        # イベント発行（リポスト開始）
        wx.CallAfter(pub.sendMessage, events.REPOST_START, uri=repost_of['uri'])
        
        # リポスト処理スレッドを開始
        thread = threading.Thread(
            target=AsyncPostHandler._repost_thread,
            args=(client, repost_of)
        )
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def _repost_thread(client, repost_of):
        """リポスト処理スレッド
        
        Args:
            client: Blueskyクライアント
            repost_of: リポスト元情報 {'uri': uri, 'cid': cid}
        """
        try:
            # リポストを実行
            result = client.repost(repost_of)
            
            # リポスト成功イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.REPOST_SUCCESS, result=result, uri=repost_of['uri'])
            
        except Exception as e:
            logger.error(f"リポスト処理中にエラーが発生しました: {str(e)}", exc_info=True)
            # リポスト失敗イベントを発行（UIスレッドで実行）
            wx.CallAfter(pub.sendMessage, events.REPOST_FAILURE, error=e, uri=repost_of['uri'])
