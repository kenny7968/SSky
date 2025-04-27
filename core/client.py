#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
Blueskyクライアントラッパーモジュール
"""

import logging
import mimetypes
from atproto import Client as AtprotoClient
from atproto.exceptions import AtProtocolError
from atproto import models

# 認証エラー用の例外クラス
class AuthenticationError(Exception):
    """認証エラーを表す例外クラス"""
    pass

# ロガーの設定
logger = logging.getLogger(__name__)

class BlueskyClient:
    """Blueskyクライアントラッパークラス"""
    
    def __init__(self):
        """初期化"""
        self.client = AtprotoClient()
        self.profile = None
        self.is_logged_in = False
        self.user_did = None  # ログインユーザーのDIDを保持
        
        # データストアの初期化
        from core.data_store import DataStore
        self.data_store = DataStore()
        
    def handle_api_error(self, error, operation_name="API操作"):
        """API呼び出し時のエラーを処理
        
        Args:
            error: 発生したエラー
            operation_name: 操作の名前（エラーメッセージ用）
            
        Returns:
            bool: 再ログインが必要な場合はTrue
        """
        if isinstance(error, AtProtocolError):
            # 認証エラーかどうかを確認
            if "auth" in str(error).lower() or "authentication" in str(error).lower():
                logger.error(f"{operation_name}中に認証エラーが発生しました: {str(error)}")
                
                # ログイン状態をリセット
                self.is_logged_in = False
                self.profile = None
                
                # 再ログインが必要
                return True
        
        # その他のエラー
        logger.error(f"{operation_name}中にエラーが発生しました: {str(error)}")
        return False
    
    def export_session_string(self):
        """セッション情報を文字列としてエクスポート
        
        Returns:
            str: セッション情報の文字列。エクスポート失敗時はNone
        """
        if not self.is_logged_in:
            logger.error("セッション情報のエクスポートに失敗しました: ログインしていません")
            return None
            
        try:
            # セッション情報をエクスポート
            session_string = self.client.export_session_string()
            logger.debug("セッション情報をエクスポートしました")
            # セキュリティ上の理由からセッション文字列の内容はログに出力しない
            logger.debug("セッション文字列をエクスポートしました（セキュリティ上の理由から内容は表示しません）")
            return session_string
        except Exception as e:
            logger.error(f"セッション情報のエクスポートに失敗しました: {str(e)}")
            return None
    
    def login_with_session(self, session_string):
        """セッション情報を使用してログイン
        
        Args:
            session_string (str): セッション情報の文字列
            
        Returns:
            object: プロフィール情報。ログイン失敗時は例外が発生
            
        Raises:
            AuthenticationError: セッションが無効な場合
            Exception: その他のエラー
        """
        try:
            logger.debug(f"セッション情報を使用してログイン試行: 型={type(session_string)}")
            
            # セッション情報をそのまま使用（バイト列への変換なし）
            # atprotoライブラリが文字列を直接処理できるか試す
            try:
                # まず文字列のままで試す
                logger.debug("文字列のままでログイン試行")
                self.profile = self.client.login(session_string=session_string)
            except Exception as e:
                logger.debug(f"文字列でのログインに失敗: {str(e)}")
                
                # 文字列での試行が失敗した場合、バイト列に変換して再試行
                if isinstance(session_string, str):
                    logger.debug("セッション情報を文字列からバイト列に変換して再試行")
                    session_bytes = session_string.encode('utf-8')
                    self.profile = self.client.login(session_string=session_bytes)
                else:
                    # 既にバイト列の場合はそのまま使用
                    logger.debug("セッション情報はバイト列なのでそのまま使用")
                    self.profile = self.client.login(session_string=session_string)
            
            # ユーザーDIDを保存
            self.user_did = self.client.me.did
            logger.debug(f"ユーザーDID: {self.user_did}")
            
            # ログイン状態を更新
            self.is_logged_in = True
            
            logger.info(f"セッションを使用したログインに成功しました: {self.profile.handle}")
            return self.profile
                
        except Exception as e:
            logger.error(f"セッションを使用したログインに失敗しました: {str(e)}")
            self.is_logged_in = False
            self.profile = None
            raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
    
    def login(self, username, password):
        """Blueskyにログイン
        
        Args:
            username (str): ユーザー名（例: username.bsky.social）
            password (str): アプリパスワード
            
        Returns:
            object: プロフィール情報。ログイン失敗時は例外が発生
            
        Raises:
            AtProtocolError: ログイン失敗時
            Exception: その他のエラー
        """
        try:
            logger.debug(f"ログイン試行: ユーザー名={username}")
            
            # ログイン試行
            self.profile = self.client.login(username, password)
            
            logger.debug(f"ログイン成功: プロフィール={self.profile.display_name}, セッション={type(self.client._session)}")
            
            # ユーザーDIDを保存
            self.user_did = self.client.me.did
            logger.debug(f"ユーザーDID: {self.user_did}")
            
            # ログイン状態を更新
            self.is_logged_in = True
            
            return self.profile
            
        except AtProtocolError as e:
            logger.error(f"Bluesky APIエラー: {str(e)}")
            self.is_logged_in = False
            raise
            
        except Exception as e:
            logger.error(f"ログイン処理中に例外が発生しました: {str(e)}", exc_info=True)
            self.is_logged_in = False
            raise
            
    def logout(self):
        """ログアウト処理
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            # クライアントをリセット
            self.client = AtprotoClient()
            self.profile = None
            self.is_logged_in = False
            
            logger.info("ログアウトしました")
            return True
            
        except Exception as e:
            logger.error(f"ログアウト処理中に例外が発生しました: {str(e)}")
            return False
            
    def get_timeline(self, limit=50):
        """タイムラインを取得
        
        Args:
            limit (int): 取得する投稿数
            
        Returns:
            object: タイムラインデータ。取得失敗時は例外が発生
            
        Raises:
            AuthenticationError: 認証エラーの場合
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("タイムラインの取得に失敗しました: ログインしていません")
            raise Exception("タイムラインの取得にはログインが必要です")
            
        try:
            logger.info("タイムラインを取得しています...")
            timeline_data = self.client.get_timeline(limit=limit)
            
            logger.info(f"タイムラインを取得しました: {len(timeline_data.feed)}件")
            return timeline_data
            
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
            
    def send_post(self, text, images=None):
        """投稿を送信
        
        Args:
            text (str): 投稿内容
            images (list, optional): 画像ブロブのリスト
            
        Returns:
            object: 投稿結果。投稿失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("投稿に失敗しました: ログインしていません")
            raise Exception("投稿にはログインが必要です")
            
        try:
            logger.info("投稿を送信しています...")
            
            # 画像付き投稿
            if images:
                result = self.client.send_post(text=text, images=images)
            else:
                # テキストのみ投稿
                result = self.client.send_post(text=text)
                
            logger.info("投稿が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"投稿時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"投稿中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def upload_blob(self, file_data, mime_type=None):
        """ファイルをアップロード
        
        Args:
            file_data (bytes): ファイルデータ
            mime_type (str, optional): MIMEタイプ
            
        Returns:
            object: アップロード結果。アップロード失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("ファイルのアップロードに失敗しました: ログインしていません")
            raise Exception("ファイルのアップロードにはログインが必要です")
            
        try:
            logger.info(f"ファイルをアップロードしています: {mime_type}")
            
            # ファイルをアップロード
            blob = self.client.upload_blob(file_data, mime_type)
            
            logger.info("ファイルのアップロードが完了しました")
            return blob
            
        except AtProtocolError as e:
            logger.error(f"ファイルアップロード時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"ファイルアップロード中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def like(self, uri, cid):
        """投稿にいいねする
        
        Args:
            uri (str): 投稿のURI
            cid (str): 投稿のCID
            
        Returns:
            object: いいね結果。いいね失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("いいねに失敗しました: ログインしていません")
            raise Exception("いいねにはログインが必要です")
            
        try:
            logger.info(f"投稿にいいねしています: {uri}")
            
            # いいねを付ける
            result = self.client.like(uri, cid)
            
            logger.info("いいねが完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"いいね時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"いいね中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def delete_post(self, uri):
        """投稿を削除
        
        Args:
            uri (str): 投稿のURI
            
        Returns:
            object: 削除結果。削除失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("投稿の削除に失敗しました: ログインしていません")
            raise Exception("投稿の削除にはログインが必要です")
            
        try:
            logger.info(f"投稿を削除しています: {uri}")
            
            # 投稿を削除
            result = self.client.delete_post(uri)
            
            logger.info("投稿の削除が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"投稿削除時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"投稿削除中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def reply_to_post(self, text, reply_to):
        """投稿に返信
        
        Args:
            text (str): 返信内容
            reply_to (dict): 返信先情報 {'uri': uri, 'cid': cid, 'reply_parent': {...}, 'reply_root': {...}}
            
        Returns:
            object: 返信結果。返信失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("返信に失敗しました: ログインしていません")
            raise Exception("返信にはログインが必要です")
            
        try:
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
            
        except AtProtocolError as e:
            logger.error(f"返信時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"返信中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def quote_post(self, text, quote_of):
        """投稿を引用
        
        Args:
            text (str): 引用コメント
            quote_of (dict): 引用元情報 {'uri': uri, 'cid': cid}
            
        Returns:
            object: 引用結果。引用失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("引用に失敗しました: ログインしていません")
            raise Exception("引用にはログインが必要です")
            
        try:
            logger.info(f"投稿を引用しています: {quote_of['uri']}")
            
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
            
            logger.info("引用が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"引用時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"引用中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def repost(self, repost_of):
        """投稿をリポスト
        
        Args:
            repost_of (dict): リポスト元情報 {'uri': uri, 'cid': cid}
            
        Returns:
            object: リポスト結果。リポスト失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("リポストに失敗しました: ログインしていません")
            raise Exception("リポストにはログインが必要です")
            
        try:
            logger.info(f"投稿をリポストしています: {repost_of['uri']}")
            
            # リポストを送信
            result = self.client.repost(
                repost_of['uri'],
                repost_of['cid']
            )
            
            logger.info("リポストが完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"リポスト時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"リポスト中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def get_profile(self, handle):
        """ユーザープロフィールを取得
        
        Args:
            handle (str): ユーザーハンドル
            
        Returns:
            object: プロフィール情報。取得失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("プロフィールの取得に失敗しました: ログインしていません")
            raise Exception("プロフィールの取得にはログインが必要です")
            
        try:
            logger.info(f"ユーザープロフィールを取得しています: {handle}")
            
            # プロフィールを取得
            profile = self.client.get_profile(actor=handle)
            
            logger.info("プロフィールの取得が完了しました")
            return profile
            
        except AtProtocolError as e:
            logger.error(f"プロフィール取得時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"プロフィール取得中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def follow(self, handle):
        """ユーザーをフォロー
        
        Args:
            handle (str): フォローするユーザーのハンドル
            
        Returns:
            object: フォロー結果。フォロー失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("フォローに失敗しました: ログインしていません")
            raise Exception("フォローにはログインが必要です")
            
        try:
            logger.info(f"ユーザーをフォローしています: {handle}")
            
            # フォローを実行
            result = self.client.follow(handle)
            
            logger.info("フォローが完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"フォロー時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"フォロー中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def unfollow(self, handle):
        """ユーザーのフォローを解除
        
        Args:
            handle (str): フォロー解除するユーザーのハンドル
            
        Returns:
            object: フォロー解除結果。フォロー解除失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("フォロー解除に失敗しました: ログインしていません")
            raise Exception("フォロー解除にはログインが必要です")
            
        try:
            logger.info(f"ユーザーのフォローを解除しています: {handle}")
            
            # プロフィールからフォロー情報を取得
            profile = self.client.get_profile(actor=handle)
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
                repo = self.user_did
                
                # フォローレコードのコレクション名
                collection = 'app.bsky.graph.follow'
                
                # レコードを削除（dataオブジェクトとして渡す）
                result = self.client.com.atproto.repo.delete_record(data={
                    'repo': repo,
                    'collection': collection,
                    'rkey': rkey
                })
                logger.info("URIを使用してフォロー解除しました")
            else:
                # DIDを取得
                response = self.client.resolve_handle(handle=handle)
                target_did = response.did
                logger.debug(f"対象ユーザーのDID: {target_did}")
                
                # フォローレコードが見つからない場合は標準のAPIを使用
                logger.warning(f"フォローレコードが見つかりませんでした。標準APIを使用します: {handle}")
                result = self.client.delete_follow(did=target_did)
                logger.info("標準APIを使用してフォロー解除しました")
            
            logger.info("フォロー解除が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"フォロー解除時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"フォロー解除中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def block(self, handle):
        """ユーザーをブロック
        
        Args:
            handle (str): ブロックするユーザーのハンドル
            
        Returns:
            object: ブロック結果。ブロック失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("ブロックに失敗しました: ログインしていません")
            raise Exception("ブロックにはログインが必要です")
            
        try:
            logger.info(f"ユーザーをブロックしています: {handle}")
            
            # DIDを取得
            response = self.client.resolve_handle(handle=handle)
            target_did = response.did
            
            # ブロックを実行
            result = self.client.block_user(did=target_did)
            
            logger.info("ブロックが完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"ブロック時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"ブロック中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def unblock(self, handle):
        """ユーザーのブロックを解除
        
        Args:
            handle (str): ブロック解除するユーザーのハンドル
            
        Returns:
            object: ブロック解除結果。ブロック解除失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("ブロック解除に失敗しました: ログインしていません")
            raise Exception("ブロック解除にはログインが必要です")
            
        try:
            logger.info(f"ユーザーのブロックを解除しています: {handle}")
            
            # DIDを取得
            response = self.client.resolve_handle(handle=handle)
            target_did = response.did
            
            # ブロック解除を実行
            result = self.client.delete_block(did=target_did)
            
            logger.info("ブロック解除が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"ブロック解除時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"ブロック解除中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def mute(self, handle):
        """ユーザーをミュート
        
        Args:
            handle (str): ミュートするユーザーのハンドル
            
        Returns:
            object: ミュート結果。ミュート失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("ミュートに失敗しました: ログインしていません")
            raise Exception("ミュートにはログインが必要です")
            
        try:
            logger.info(f"ユーザーをミュートしています: {handle}")
            
            # DIDを取得
            response = self.client.resolve_handle(handle=handle)
            target_did = response.did
            
            # ミュートを実行（名前空間を使用）
            try:
                # 方法1: app.bsky.graph名前空間を使用
                result = self.client.app.bsky.graph.mute_actor(data={'actor': target_did})
                logger.info("app.bsky.graph.mute_actorを使用してミュートしました")
            except (AttributeError, Exception) as e1:
                logger.debug(f"app.bsky.graph.mute_actorでのミュートに失敗: {str(e1)}")
                try:
                    # 方法2: bsky.graph名前空間を使用
                    result = self.client.bsky.graph.mute_actor(data={'actor': target_did})
                    logger.info("bsky.graph.mute_actorを使用してミュートしました")
                except (AttributeError, Exception) as e2:
                    logger.debug(f"bsky.graph.mute_actorでのミュートに失敗: {str(e2)}")
                    # 方法3: 低レベルAPIを直接呼び出す
                    from datetime import datetime
                    result = self.client.com.atproto.repo.create_record(data={
                        'repo': self.user_did,
                        'collection': 'app.bsky.graph.mute',
                        'record': {
                            'subject': target_did,
                            'createdAt': datetime.now().isoformat()
                        }
                    })
                    logger.info("低レベルAPIを使用してミュートしました")
            
            logger.info("ミュートが完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"ミュート時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"ミュート中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
    def unmute(self, handle):
        """ユーザーのミュートを解除
        
        Args:
            handle (str): ミュート解除するユーザーのハンドル
            
        Returns:
            object: ミュート解除結果。ミュート解除失敗時は例外が発生
            
        Raises:
            AtProtocolError: API呼び出し失敗時
            Exception: その他のエラー
        """
        if not self.is_logged_in:
            logger.error("ミュート解除に失敗しました: ログインしていません")
            raise Exception("ミュート解除にはログインが必要です")
            
        try:
            logger.info(f"ユーザーのミュートを解除しています: {handle}")
            
            # DIDを取得
            response = self.client.resolve_handle(handle=handle)
            target_did = response.did
            
            # ミュート解除を実行（名前空間を使用）
            try:
                # 方法1: app.bsky.graph名前空間を使用
                result = self.client.app.bsky.graph.unmute_actor(data={'actor': target_did})
                logger.info("app.bsky.graph.unmute_actorを使用してミュート解除しました")
            except (AttributeError, Exception) as e1:
                logger.debug(f"app.bsky.graph.unmute_actorでのミュート解除に失敗: {str(e1)}")
                try:
                    # 方法2: bsky.graph名前空間を使用
                    result = self.client.bsky.graph.unmute_actor(data={'actor': target_did})
                    logger.info("bsky.graph.unmute_actorを使用してミュート解除しました")
                except (AttributeError, Exception) as e2:
                    logger.debug(f"bsky.graph.unmute_actorでのミュート解除に失敗: {str(e2)}")
                    # 方法3: 低レベルAPIを直接呼び出す
                    # ミュートレコードを検索して削除する必要があります
                    # プロフィールからミュート情報を取得
                    profile = self.client.get_profile(actor=handle)
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
                        result = self.client.unmute_actor(actor=target_did)
                        logger.info("標準APIを使用してミュート解除しました")
                    except (AttributeError, Exception) as e3:
                        logger.error(f"ミュート解除に失敗しました: 適切なAPIが見つかりません: {str(e3)}")
                        raise Exception("ミュート解除の適切なAPIが見つかりませんでした")
            
            logger.info("ミュート解除が完了しました")
            return result
            
        except AtProtocolError as e:
            logger.error(f"ミュート解除時にBluesky APIエラー: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"ミュート解除中に例外が発生しました: {str(e)}", exc_info=True)
            raise
            
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
        if not self.is_logged_in:
            logger.error("フォロー中ユーザー一覧の取得に失敗しました: ログインしていません")
            raise Exception("フォロー中ユーザー一覧の取得にはログインが必要です")
            
        try:
            logger.info(f"ユーザー {handle} のフォロー中ユーザー一覧を取得しています...")
            
            # app.bsky.graph.getFollows APIを呼び出し
            result = self.client.app.bsky.graph.get_follows({
                'actor': handle,
                'limit': min(limit, 100),  # 最大100件まで
                'cursor': cursor
            })
            
            logger.info(f"フォロー中ユーザー一覧を取得しました: {len(result.follows)}件")
            return result
            
        except AtProtocolError as e:
            # 認証エラーかどうかを確認
            if self.handle_api_error(e, "フォロー中ユーザー一覧取得"):
                # 認証エラーの場合は特別なエラーを発生させる
                raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
            # その他のAPIエラーはそのまま再発生
            raise
            
        except Exception as e:
            logger.error(f"フォロー中ユーザー一覧の取得に失敗しました: {str(e)}")
            raise
            
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
        if not self.is_logged_in:
            logger.error("フォロワー一覧の取得に失敗しました: ログインしていません")
            raise Exception("フォロワー一覧の取得にはログインが必要です")
            
        try:
            logger.info(f"ユーザー {handle} のフォロワー一覧を取得しています...")
            
            # app.bsky.graph.getFollowers APIを呼び出し
            result = self.client.app.bsky.graph.get_followers({
                'actor': handle,
                'limit': min(limit, 100),  # 最大100件まで
                'cursor': cursor
            })
            
            logger.info(f"フォロワー一覧を取得しました: {len(result.followers)}件")
            return result
            
        except AtProtocolError as e:
            # 認証エラーかどうかを確認
            if self.handle_api_error(e, "フォロワー一覧取得"):
                # 認証エラーの場合は特別なエラーを発生させる
                raise AuthenticationError("セッションが無効になりました。再ログインが必要です。") from e
            # その他のAPIエラーはそのまま再発生
            raise
            
        except Exception as e:
            logger.error(f"フォロワー一覧の取得に失敗しました: {str(e)}")
            raise
