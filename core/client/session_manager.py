#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
セッション管理を担当するクラス
"""

import logging
import typing
from atproto import SessionEvent, Session

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskySessionManager:
    """セッション管理を担当するクラス
    
    セッション変更イベントの処理、セッションの管理を担当します。
    """
    
    def __init__(self, api_client=None):
        """初期化
        
        Args:
            api_client (BlueskyApiClient, optional): APIクライアントインスタンス
        """
        self.api_client = api_client
        
        # セッション変更イベント処理用の外部ハンドラを保持するリスト
        self._session_change_handlers = []
        
    def register_client(self, api_client):
        """APIクライアントを登録
        
        Args:
            api_client (BlueskyApiClient): APIクライアントインスタンス
        """
        self.api_client = api_client
        
        if hasattr(self.api_client, 'client') and hasattr(self.api_client.client, 'on_session_change'):
            # 内部ハンドラを登録
            logger.info("セッション変更イベントのコールバック機能を初期化します")
            logger.debug(f"クライアントオブジェクト: {type(self.api_client.client)}")
            
            @self.api_client.client.on_session_change
            def _internal_session_change_handler(event: SessionEvent, session: Session):
                try:
                    # イベントの種類をログに記録
                    logger.info(f"セッション変更イベントが発生しました: {event}")
                    logger.debug(f"セッションオブジェクト: 型={type(session)}")
                    
                    # 登録された外部ハンドラを実行
                    for handler in self._session_change_handlers:
                        try:
                            handler(event, session)
                        except Exception as handler_error:
                            logger.error(f"外部セッションハンドラの実行中にエラーが発生しました: {str(handler_error)}", exc_info=True)
                except Exception as e:
                    logger.error(f"セッション変更イベント処理中にエラーが発生しました: {str(e)}", exc_info=True)
            
            # ガベージコレクションが発生しないようにインスタンス変数に保存
            self._internal_session_change_handler = _internal_session_change_handler
            logger.debug("セッション変更ハンドラを登録しました")
    
    def on_session_change(self, handler: typing.Callable[[SessionEvent, Session], None]) -> None:
        """セッション変更イベントの外部ハンドラを登録
        
        Args:
            handler: セッション変更イベントを処理するコールバック関数
        """
        self._session_change_handlers.append(handler)
        logger.debug(f"外部セッション変更ハンドラが登録されました（合計: {len(self._session_change_handlers)}件）")
        
    def remove_session_change_handler(self, handler: typing.Callable[[SessionEvent, Session], None]) -> bool:
        """登録されたセッション変更イベントのハンドラを削除
        
        Args:
            handler: 削除するハンドラ
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        if handler in self._session_change_handlers:
            self._session_change_handlers.remove(handler)
            logger.debug(f"外部セッション変更ハンドラが削除されました（合計: {len(self._session_change_handlers)}件）")
            return True
        return False