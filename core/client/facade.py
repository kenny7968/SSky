#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
統合ファサードクラス
"""

import logging
import typing
from typing import Optional, Dict, Any, List, Callable, Union
from atproto import SessionEvent, Session
from atproto.exceptions import AtProtocolError
from core.exceptions import AuthenticationError
from core.client.api_client import BlueskyApiClient
from core.client.auth_manager import BlueskyAuthManager
from core.client.session_manager import BlueskySessionManager
from core.client.user_manager import BlueskyUserManager
from core.error_handler import UnifiedErrorHandler

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyClient:
    """Blueskyクライアントファサードクラス（Phase 3 依存性注入対応）
    
    分割された各コンポーネントのファサードとして機能し、
    既存のコードとの互換性を維持します。
    
    Phase 3変更点:
    - 全コンポーネントを外部から注入可能に変更
    - 後方互換性を維持しつつ、テスト時の依存性差し替えを容易にする
    """
    
    def __init__(self, 
                 api_client: BlueskyApiClient = None,
                 session_manager: BlueskySessionManager = None,
                 auth_manager: BlueskyAuthManager = None,
                 error_handler: UnifiedErrorHandler = None,
                 user_manager: BlueskyUserManager = None):
        """初期化（依存性注入対応）
        
        Args:
            api_client: APIクライアント（未指定時はデフォルト作成）
            session_manager: セッション管理（未指定時はデフォルト作成）
            auth_manager: 認証管理（未指定時はデフォルト作成）
            error_handler: エラーハンドラー（未指定時はデフォルト作成）
            user_manager: ユーザー管理（未指定時はデフォルト作成）
        """
        # コンポーネントの注入または作成
        self.api_client = api_client or BlueskyApiClient()
        
        # セッションマネージャーの初期化（api_clientに依存）
        if session_manager is not None:
            self.session_manager = session_manager
        else:
            self.session_manager = BlueskySessionManager(self.api_client)
        
        # 認証マネージャーの初期化（api_client, session_managerに依存）
        if auth_manager is not None:
            self.auth_manager = auth_manager
        else:
            self.auth_manager = BlueskyAuthManager(self.api_client, self.session_manager)
        
        # エラーハンドラーの初期化（auth_managerに依存）
        if error_handler is not None:
            self.error_handler = error_handler
        else:
            self.error_handler = UnifiedErrorHandler(self.auth_manager)
        
        # ユーザーマネージャーの初期化（api_client, auth_managerに依存）
        if user_manager is not None:
            self.user_manager = user_manager
        else:
            self.user_manager = BlueskyUserManager(self.api_client, self.auth_manager)
        
        # セッションマネージャーにAPIクライアントを登録
        self.session_manager.register_client(self.api_client)
        
        # プロパティのバインド
        self._bind_properties()
    
    def _bind_properties(self):
        """プロパティをバインド"""
        # クライアントプロパティ
        self.client = self.api_client.client

    # Phase 3 追加: ファクトリメソッド
    @classmethod
    def create_for_testing(cls, mock_api_client=None, mock_credential_manager=None):
        """テスト用のインスタンスを作成
        
        Args:
            mock_api_client: モックされたAPIクライアント
            mock_credential_manager: モックされた認証情報管理
            
        Returns:
            BlueskyClient: テスト用設定済みインスタンス
        """
        # モックされたコンポーネントを使用してインスタンス作成
        api_client = mock_api_client or BlueskyApiClient()
        
        # 他のコンポーネントもモック対応で作成
        session_manager = BlueskySessionManager(api_client)
        auth_manager = BlueskyAuthManager(api_client, session_manager)
        error_handler = UnifiedErrorHandler(auth_manager)
        user_manager = BlueskyUserManager(api_client, auth_manager)
        
        return cls(
            api_client=api_client,
            session_manager=session_manager,
            auth_manager=auth_manager,
            error_handler=error_handler,
            user_manager=user_manager
        )
    
    @classmethod  
    def create_with_custom_credential_manager(cls, credential_manager):
        """カスタム認証情報管理を使用するインスタンスを作成
        
        Args:
            credential_manager: カスタム認証情報管理インスタンス
            
        Returns:
            BlueskyClient: カスタム設定済みインスタンス
        """
        # 認証情報管理が注入されたAPIクライアントを作成
        api_client = BlueskyApiClient()
        
        # 他のコンポーネントも作成
        session_manager = BlueskySessionManager(api_client)
        auth_manager = BlueskyAuthManager(api_client, session_manager)
        error_handler = UnifiedErrorHandler(auth_manager)
        user_manager = BlueskyUserManager(api_client, auth_manager)
        
        # 認証情報管理を注入 (実際のauth_managerの実装に応じて調整が必要)
        # auth_manager.credential_manager = credential_manager
        
        return cls(
            api_client=api_client,
            session_manager=session_manager,
            auth_manager=auth_manager,
            error_handler=error_handler,
            user_manager=user_manager
        )
    
    @property
    def profile(self):
        """プロフィール情報"""
        return self.auth_manager.profile
    
    @profile.setter
    def profile(self, value):
        """プロフィール情報を設定"""
        self.auth_manager.profile = value
    
    @property
    def is_logged_in(self):
        """ログイン状態"""
        return self.auth_manager.is_logged_in
    
    @is_logged_in.setter
    def is_logged_in(self, value):
        """ログイン状態を設定"""
        self.auth_manager.is_logged_in = value
    
    @property
    def user_did(self):
        """ユーザーDID"""
        return self.auth_manager.user_did
    
    @user_did.setter
    def user_did(self, value):
        """ユーザーDIDを設定"""
        self.auth_manager.user_did = value
    
    # セッション変更イベント関連のメソッド
    def on_session_change(self, handler: Callable[[SessionEvent, Session], None]) -> None:
        """セッション変更イベントのハンドラを登録
        
        Args:
            handler: セッション変更イベントを処理するコールバック関数
        """
        return self.session_manager.on_session_change(handler)
    
    def remove_session_change_handler(self, handler: Callable[[SessionEvent, Session], None]) -> bool:
        """登録されたセッション変更イベントのハンドラを削除
        
        Args:
            handler: 削除するハンドラ
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        return self.session_manager.remove_session_change_handler(handler)
    
    # 認証関連のメソッド
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Blueskyにログイン
        
        Args:
            username (str): ユーザー名
            password (str): アプリパスワード
            
        Returns:
            Optional[Dict[str, Any]]: プロフィール情報
        """
        return self.auth_manager.login(username, password)
    
    def login_with_session(self, session_string: str) -> Optional[Dict[str, Any]]:
        """セッション情報を使用してログイン
        
        Args:
            session_string (str): セッション情報の文字列
            
        Returns:
            Optional[Dict[str, Any]]: プロフィール情報
        """
        return self.auth_manager.login_with_session(session_string)
    
    def logout(self) -> bool:
        """ログアウト処理
        
        Returns:
            bool: 成功した場合はTrue
        """
        return self.auth_manager.logout()
    
    def export_session_string(self) -> Optional[str]:
        """セッション情報を文字列としてエクスポート
        
        Returns:
            str: セッション情報の文字列
        """
        return self.auth_manager.export_session_string()
    
    def handle_api_error(self, error: Exception, operation_name: str = "API操作") -> bool:
        """API呼び出し時のエラーを処理
        
        Args:
            error: 発生したエラー
            operation_name: 操作の名前
            
        Returns:
            bool: 再ログインが必要な場合はTrue
        """
        return self.auth_manager.handle_api_error(error, operation_name)
    
    # タイムライン関連のメソッド
    def get_timeline(self, limit: int = 50) -> Optional[Dict[str, Any]]:
        """タイムラインを取得
        
        Args:
            limit (int): 取得する投稿数
            
        Returns:
            Optional[Dict[str, Any]]: タイムラインデータ
            
        Raises:
            AuthenticationError: 認証エラーの場合
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("タイムラインの取得に失敗しました: ログインしていません")
            raise Exception("タイムラインの取得にはログインが必要です")
            
        try:
            return self.api_client.get_timeline(limit)
            
        except AtProtocolError as e:
            # 認証エラーかどうかを確認
            if self.handle_api_error(e, "タイムライン取得"):
                # 認証エラーの場合は特別なエラーを発生させる
                raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
            # その他のAPIエラーはそのまま再発生
            raise
            
        except Exception as e:
            logger.error(f"タイムライン取得中に例外が発生しました: {str(e)}", exc_info=True)
            raise
    
    # 投稿関連のメソッド
    def send_post(self, text: str, images: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """投稿を送信
        
        Args:
            text (str): 投稿内容
            images (Optional[List[Any]]): 画像ブロブのリスト
            
        Returns:
            Optional[Dict[str, Any]]: 投稿結果
        """
        if not self.is_logged_in:
            logger.error("投稿に失敗しました: ログインしていません")
            raise Exception("投稿にはログインが必要です")
            
        try:
            return self.api_client.send_post(text, images)
            
        except AtProtocolError as e:
            logger.error(f"投稿時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"投稿中に例外が発生しました: {str(e)}", exc_info=True)
            raise
    
    def upload_blob(self, file_data: bytes, mime_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """ファイルをアップロード
        
        Args:
            file_data (bytes): ファイルデータ
            mime_type (Optional[str]): MIMEタイプ
            
        Returns:
            Optional[Dict[str, Any]]: アップロード結果
        """
        if not self.is_logged_in:
            logger.error("ファイルのアップロードに失敗しました: ログインしていません")
            raise Exception("ファイルのアップロードにはログインが必要です")
            
        return self.api_client.upload_blob(file_data, mime_type)
    
    def like(self, uri: str, cid: str) -> Optional[Dict[str, Any]]:
        """投稿にいいねする
        
        Args:
            uri (str): 投稿のURI
            cid (str): 投稿のCID
            
        Returns:
            object: いいね結果
        """
        if not self.is_logged_in:
            logger.error("いいねに失敗しました: ログインしていません")
            raise Exception("いいねにはログインが必要です")
            
        return self.api_client.like(uri, cid)
    
    def delete_post(self, uri):
        """投稿を削除
        
        Args:
            uri (str): 投稿のURI
            
        Returns:
            object: 削除結果
        """
        if not self.is_logged_in:
            logger.error("投稿の削除に失敗しました: ログインしていません")
            raise Exception("投稿の削除にはログインが必要です")
            
        return self.api_client.delete_post(uri)
    
    def reply_to_post(self, text, reply_to):
        """投稿に返信
        
        Args:
            text (str): 返信内容
            reply_to (dict): 返信先情報
            
        Returns:
            object: 返信結果
        """
        if not self.is_logged_in:
            logger.error("返信に失敗しました: ログインしていません")
            raise Exception("返信にはログインが必要です")
            
        return self.api_client.reply_to_post(text, reply_to)
    
    def quote_post(self, text, quote_of):
        """投稿を引用
        
        Args:
            text (str): 引用コメント
            quote_of (dict): 引用元情報
            
        Returns:
            object: 引用結果
        """
        if not self.is_logged_in:
            logger.error("引用に失敗しました: ログインしていません")
            raise Exception("引用にはログインが必要です")
            
        return self.api_client.quote_post(text, quote_of)
    
    def repost(self, repost_of):
        """投稿をリポスト
        
        Args:
            repost_of (dict): リポスト元情報
            
        Returns:
            object: リポスト結果
        """
        if not self.is_logged_in:
            logger.error("リポストに失敗しました: ログインしていません")
            raise Exception("リポストにはログインが必要です")
            
        return self.api_client.repost(repost_of)
    
    def get_profile(self, handle):
        """プロフィールを取得
        
        Args:
            handle (str): ユーザーハンドル
            
        Returns:
            object: プロフィール情報
        """
        if not self.is_logged_in:
            logger.error("プロフィールの取得に失敗しました: ログインしていません")
            raise Exception("プロフィールの取得にはログインが必要です")
            
        return self.api_client.get_profile(handle)
    
    
    # ユーザー管理関連のメソッド
    def follow(self, handle):
        """ユーザーをフォロー
        
        Args:
            handle (str): フォローするユーザーのハンドル
            
        Returns:
            object: フォロー結果
        """
        if not self.is_logged_in:
            logger.error("フォローに失敗しました: ログインしていません")
            raise Exception("フォローにはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.follow, handle, operation_name="フォロー"
        )
    
    def unfollow(self, handle):
        """ユーザーのフォローを解除
        
        Args:
            handle (str): フォロー解除するユーザーのハンドル
            
        Returns:
            object: フォロー解除結果
        """
        if not self.is_logged_in:
            logger.error("フォロー解除に失敗しました: ログインしていません")
            raise Exception("フォロー解除にはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.unfollow, handle, operation_name="フォロー解除"
        )
    
    def block(self, handle):
        """ユーザーをブロック
        
        Args:
            handle (str): ブロックするユーザーのハンドル
            
        Returns:
            object: ブロック結果
        """
        if not self.is_logged_in:
            logger.error("ブロックに失敗しました: ログインしていません")
            raise Exception("ブロックにはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.block, handle, operation_name="ブロック"
        )
    
    def unblock(self, handle):
        """ユーザーのブロックを解除
        
        Args:
            handle (str): ブロック解除するユーザーのハンドル
            
        Returns:
            object: ブロック解除結果
        """
        if not self.is_logged_in:
            logger.error("ブロック解除に失敗しました: ログインしていません")
            raise Exception("ブロック解除にはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.unblock, handle, operation_name="ブロック解除"
        )
    
    def mute(self, handle):
        """ユーザーをミュート
        
        Args:
            handle (str): ミュートするユーザーのハンドル
            
        Returns:
            object: ミュート結果
        """
        if not self.is_logged_in:
            logger.error("ミュートに失敗しました: ログインしていません")
            raise Exception("ミュートにはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.mute, handle, operation_name="ミュート"
        )
    
    def unmute(self, handle):
        """ユーザーのミュートを解除
        
        Args:
            handle (str): ミュート解除するユーザーのハンドル
            
        Returns:
            object: ミュート解除結果
        """
        if not self.is_logged_in:
            logger.error("ミュート解除に失敗しました: ログインしていません")
            raise Exception("ミュート解除にはログインが必要です")
            
        return self.error_handler.safe_api_call(
            self.user_manager.unmute, handle, operation_name="ミュート解除"
        )
    
    def get_following(self, handle, limit=100, cursor=None):
        """フォロー中ユーザー一覧を取得
        
        Args:
            handle (str): ユーザーハンドル
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: フォロー中ユーザー一覧
        """
        if not self.is_logged_in:
            logger.error("フォロー中ユーザー一覧の取得に失敗しました: ログインしていません")
            raise Exception("フォロー中ユーザー一覧の取得にはログインが必要です")
            
        return self.error_handler.handle_with_auth_check(
            self.user_manager.get_following, handle, limit, cursor,
            operation_name="フォロー中ユーザー一覧取得"
        )
    
    def get_followers(self, handle, limit=100, cursor=None):
        """フォロワー一覧を取得
        
        Args:
            handle (str): ユーザーハンドル
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: フォロワー一覧
        """
        if not self.is_logged_in:
            logger.error("フォロワー一覧の取得に失敗しました: ログインしていません")
            raise Exception("フォロワー一覧の取得にはログインが必要です")
            
        return self.error_handler.handle_with_auth_check(
            self.user_manager.get_followers, handle, limit, cursor,
            operation_name="フォロワー一覧取得"
        )
    
    def get_blocked_users(self, limit=100, cursor=None):
        """ブロックしたユーザー一覧を取得
        
        Args:
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: ブロックしたユーザー一覧
        """
        if not self.is_logged_in:
            logger.error("ブロックしたユーザー一覧の取得に失敗しました: ログインしていません")
            raise Exception("ブロックしたユーザー一覧の取得にはログインが必要です")
            
        return self.error_handler.handle_with_auth_check(
            self.user_manager.get_blocked_users, limit, cursor,
            operation_name="ブロックしたユーザー一覧取得"
        )
    
    def get_muted_users(self, limit=100, cursor=None):
        """ミュートしたユーザー一覧を取得
        
        Args:
            limit (int, optional): 取得する最大数（最大100）
            cursor (str, optional): ページネーション用カーソル
            
        Returns:
            object: ミュートしたユーザー一覧
        """
        if not self.is_logged_in:
            logger.error("ミュートしたユーザー一覧の取得に失敗しました: ログインしていません")
            raise Exception("ミュートしたユーザー一覧の取得にはログインが必要です")
            
        return self.error_handler.handle_with_auth_check(
            self.user_manager.get_muted_users, limit, cursor,
            operation_name="ミュートしたユーザー一覧取得"
        )
    
    def quote_post_advanced(self, text, quote_of):
        """投稿を引用（高度な機能）
        
        Args:
            text (str): 引用コメント
            quote_of (dict): 引用元情報
            
        Returns:
            object: 引用結果
        """
        if not self.is_logged_in:
            logger.error("引用に失敗しました: ログインしていません")
            raise Exception("引用にはログインが必要です")
            
        return self.api_client.quote_post_advanced(text, quote_of)