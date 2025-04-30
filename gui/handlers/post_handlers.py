#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿関連イベントハンドラ
"""

import os
import wx
import logging
from pubsub import pub
from gui.dialogs.post_dialog import PostDialog
from utils.file_utils import read_binary_file, get_mime_type
from core import events

# ロガーの設定
logger = logging.getLogger(__name__)

class PostHandlers:
    """投稿関連イベントハンドラクラス"""
    
    # いいね処理中フラグ（二重いいね防止用）
    _liking_post = False
    
    # 削除処理中フラグ（二重削除防止用）
    _deleting_post = False
    
    def __init__(self, parent, client=None):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            client (BlueskyClient, optional): Blueskyクライアント
        """
        self.parent = parent
        self.client = client
        
        # 設定マネージャーの取得
        if hasattr(parent, 'settings_manager'):
            self.settings_manager = parent.settings_manager
        else:
            from config.settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
        
    def on_new_post(self, event):
        """新規投稿ダイアログを表示
        
        Args:
            event: メニューイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("投稿するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        # 投稿ダイアログの作成
        dlg = PostDialog(self.parent)
        
        # ダイアログ表示
        if dlg.ShowModal() == wx.ID_OK:
            post_content, attachment_files = dlg.get_post_data()
            if post_content:
                try:
                    # ステータスバーの更新
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("投稿中...")
                    
                    # PubSubイベントの購読
                    pub.subscribe(self._on_post_submit_success, events.POST_SUBMIT_SUCCESS)
                    pub.subscribe(self._on_post_submit_failure, events.POST_SUBMIT_FAILURE)
                    
                    # 非同期投稿処理を開始
                    from gui.handlers.async_post_handler import AsyncPostHandler
                    AsyncPostHandler.submit_post(self.client, post_content, attachment_files)
                    
                except Exception as e:
                    logger.error(f"投稿処理の開始に失敗しました: {str(e)}")
                    wx.MessageBox(f"投稿処理の開始に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("投稿に失敗しました")
            else:
                wx.MessageBox("投稿内容を入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
        
    def _on_post_submit_success(self, result):
        """投稿成功イベントハンドラ
        
        Args:
            result: 投稿結果
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_post_submit_success, events.POST_SUBMIT_SUCCESS)
        pub.unsubscribe(self._on_post_submit_failure, events.POST_SUBMIT_FAILURE)
        
        # 投稿成功
        self.show_completion_dialog("投稿が完了しました", "投稿完了")
        
        # タイムラインを更新
        if hasattr(self.parent, 'timeline'):
            self.parent.timeline.fetch_timeline(self.client)
        
        # ステータスバーの更新
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("投稿が完了しました")
    
    def _on_post_submit_failure(self, error):
        """投稿失敗イベントハンドラ
        
        Args:
            error: エラー情報
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_post_submit_success, events.POST_SUBMIT_SUCCESS)
        pub.unsubscribe(self._on_post_submit_failure, events.POST_SUBMIT_FAILURE)
        
        # エラーメッセージを表示
        logger.error(f"投稿に失敗しました: {str(error)}")
        wx.MessageBox(f"投稿に失敗しました: {str(error)}", "エラー", wx.OK | wx.ICON_ERROR)
        
        # ステータスバーの更新
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("投稿に失敗しました")
    
    def on_like(self, event):
        """いいねアクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        # いいね処理中なら何もしない（二重いいね防止）
        if PostHandlers._liking_post:
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        try:
            # いいね処理中フラグをセット
            PostHandlers._liking_post = True
            
            # いいねを付ける
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("いいねしています...")
                
            # PubSubイベントの購読
            pub.subscribe(self._on_like_success, events.LIKE_SUCCESS)
            pub.subscribe(self._on_like_failure, events.LIKE_FAILURE)
            
            # 非同期いいね処理を開始
            from gui.handlers.async_post_handler import AsyncPostHandler
            AsyncPostHandler.like_post(self.client, selected['uri'], selected['cid'])
            
            return True
            
        except Exception as e:
            logger.error(f"いいね処理の開始に失敗しました: {str(e)}")
            wx.MessageBox(f"いいね処理の開始に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("いいね処理に失敗しました")
            # いいね処理中フラグをリセット
            PostHandlers._liking_post = False
            return False
            
    def _on_like_success(self, result, uri):
        """いいね成功イベントハンドラ
        
        Args:
            result: いいね結果
            uri: 投稿のURI
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_like_success, events.LIKE_SUCCESS)
        pub.unsubscribe(self._on_like_failure, events.LIKE_FAILURE)
        
        # いいね成功
        wx.MessageBox("投稿にいいねしました", "いいね", wx.OK | wx.ICON_INFORMATION)
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("いいねしました")
        
        # タイムラインを更新（選択されていた投稿のURIを渡す）
        if hasattr(self.parent, 'timeline'):
            self.parent.timeline.fetch_timeline(self.client, uri)
        
        # いいね処理中フラグをリセット
        PostHandlers._liking_post = False
    
    def _on_like_failure(self, error, uri):
        """いいね失敗イベントハンドラ
        
        Args:
            error: エラー情報
            uri: 投稿のURI
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_like_success, events.LIKE_SUCCESS)
        pub.unsubscribe(self._on_like_failure, events.LIKE_FAILURE)
        
        # エラーメッセージを表示
        logger.error(f"いいね処理に失敗しました: {str(error)}")
        wx.MessageBox(f"いいね処理に失敗しました: {str(error)}", "エラー", wx.OK | wx.ICON_ERROR)
        
        # ステータスバーの更新
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("いいね処理に失敗しました")
        
        # いいね処理中フラグをリセット
        PostHandlers._liking_post = False
    
    def on_reply(self, event):
        """返信アクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("返信するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 返信に必要な情報があるか確認
        if not selected.get('uri') or not selected.get('cid'):
            wx.MessageBox("返信に必要な情報がありません", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 返信ダイアログを表示
        from gui.dialogs.reply_dialog import ReplyDialog
        dlg = ReplyDialog(self.parent, selected)
        
        if dlg.ShowModal() == wx.ID_OK:
            reply_text, reply_to = dlg.get_reply_data()
            
            if reply_text:
                try:
                    # 返信処理
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("返信を送信しています...")
                    
                    # 返信を送信
                    self.client.reply_to_post(reply_text, reply_to)
                    
                    # 返信成功
                    self.show_completion_dialog("返信が完了しました", "返信完了")
                    
                    # タイムラインを更新
                    if hasattr(self.parent, 'timeline'):
                        self.parent.timeline.fetch_timeline(self.client)
                    
                    dlg.Destroy()
                    return True
                    
                except Exception as e:
                    logger.error(f"返信に失敗しました: {str(e)}")
                    wx.MessageBox(f"返信に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("返信に失敗しました")
            else:
                wx.MessageBox("返信内容を入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
        return False
    
    def on_quote(self, event):
        """引用アクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("引用するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 引用に必要な情報があるか確認
        if not selected.get('uri') or not selected.get('cid'):
            wx.MessageBox("引用に必要な情報がありません", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 引用ダイアログを表示
        from gui.dialogs.quote_dialog import QuoteDialog
        dlg = QuoteDialog(self.parent, selected)
        
        if dlg.ShowModal() == wx.ID_OK:
            quote_text, quote_of = dlg.get_quote_data()
            
            if quote_text:
                try:
                    # 引用処理
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("引用を送信しています...")
                    
                    # 引用を送信
                    self.client.quote_post(quote_text, quote_of)
                    
                    # 引用成功
                    self.show_completion_dialog("引用が完了しました", "引用完了")
                    
                    # タイムラインを更新
                    if hasattr(self.parent, 'timeline'):
                        self.parent.timeline.fetch_timeline(self.client)
                    
                    dlg.Destroy()
                    return True
                    
                except Exception as e:
                    logger.error(f"引用に失敗しました: {str(e)}")
                    wx.MessageBox(f"引用に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                    if hasattr(self.parent, 'statusbar'):
                        self.parent.statusbar.SetStatusText("引用に失敗しました")
            else:
                wx.MessageBox("引用コメントを入力してください", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
        return False
        
    # リポスト処理中フラグ（二重リポスト防止用）
    _reposting_post = False
    
    def on_repost(self, event):
        """リポストアクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        # リポスト処理中なら何もしない（二重リポスト防止）
        if PostHandlers._reposting_post:
            return False
            
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("リポストするにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 自分の投稿はリポストできない
        if selected.get('is_own_post', False):
            wx.MessageBox("自分の投稿はリポストできません", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # リポストに必要な情報があるか確認
        if not selected.get('uri') or not selected.get('cid'):
            wx.MessageBox("リポストに必要な情報がありません", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 現在選択されている投稿のURIを記憶
        selected_uri = selected.get('uri')
            
        # リポスト確認ダイアログ
        dlg = wx.MessageDialog(
            self.parent,
            f"{selected['username']}の投稿をリポストしますか？",
            "リポストの確認",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                # リポスト処理中フラグをセット
                PostHandlers._reposting_post = True
                
                # リポスト処理
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("リポストしています...")
                
                # PubSubイベントの購読
                pub.subscribe(self._on_repost_success, events.REPOST_SUCCESS)
                pub.subscribe(self._on_repost_failure, events.REPOST_FAILURE)
                
                # 非同期リポスト処理を開始
                from gui.handlers.async_post_handler import AsyncPostHandler
                AsyncPostHandler.repost(self.client, {
                    'uri': selected['uri'],
                    'cid': selected['cid']
                })
                
                dlg.Destroy()
                return True
                
            except Exception as e:
                logger.error(f"リポスト処理の開始に失敗しました: {str(e)}")
                wx.MessageBox(f"リポスト処理の開始に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("リポストに失敗しました")
                # リポスト処理中フラグをリセット
                PostHandlers._reposting_post = False
                return False
        
        dlg.Destroy()
        return False
        
    def _on_repost_success(self, result, uri):
        """リポスト成功イベントハンドラ
        
        Args:
            result: リポスト結果
            uri: 投稿のURI
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_repost_success, events.REPOST_SUCCESS)
        pub.unsubscribe(self._on_repost_failure, events.REPOST_FAILURE)
        
        # リポスト成功
        wx.MessageBox("リポストが完了しました", "リポスト完了", wx.OK | wx.ICON_INFORMATION)
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("リポストが完了しました")
        
        # タイムラインを更新（選択されていた投稿のURIを渡す）
        if hasattr(self.parent, 'timeline'):
            logger.info("リポスト後にタイムラインを更新します")
            self.parent.timeline.fetch_timeline(self.client, uri)
        
        # リポスト処理中フラグをリセット
        PostHandlers._reposting_post = False
    
    def _on_repost_failure(self, error, uri):
        """リポスト失敗イベントハンドラ
        
        Args:
            error: エラー情報
            uri: 投稿のURI
        """
        # イベント購読を解除
        pub.unsubscribe(self._on_repost_success, events.REPOST_SUCCESS)
        pub.unsubscribe(self._on_repost_failure, events.REPOST_FAILURE)
        
        # エラーメッセージを表示
        logger.error(f"リポストに失敗しました: {str(error)}")
        wx.MessageBox(f"リポストに失敗しました: {str(error)}", "エラー", wx.OK | wx.ICON_ERROR)
        
        # ステータスバーの更新
        if hasattr(self.parent, 'statusbar'):
            self.parent.statusbar.SetStatusText("リポストに失敗しました")
        
        # リポスト処理中フラグをリセット
        PostHandlers._reposting_post = False
        
        # タイムラインが更新されていない場合は強制的に更新
        if hasattr(self.parent, 'timeline'):
            wx.CallAfter(self.parent.timeline.fetch_timeline, self.client)
    
    def show_completion_dialog(self, message, title):
        """完了ダイアログを表示（設定に応じて）
        
        Args:
            message (str): ダイアログメッセージ
            title (str): ダイアログタイトル
            
        Returns:
            bool: ダイアログを表示した場合はTrue
        """
        # 設定値を取得（デフォルトはTrue）
        show_dialog = self.settings_manager.get('post.show_completion_dialog', True)
        
        # 設定に応じてダイアログを表示
        if show_dialog:
            wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)
            return True
        else:
            # ダイアログを表示しない場合はステータスバーのみ更新
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText(message)
            return False
    
    def on_profile(self, event):
        """プロフィール表示アクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("プロフィールを表示するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        try:
            # ステータスバーの更新
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText(f"{selected['username']}のプロフィールを取得しています...")
                
            # 投稿者のハンドルを取得
            author_handle = selected.get('author_handle')
            if not author_handle:
                wx.MessageBox("投稿者のハンドルが取得できません", "エラー", wx.OK | wx.ICON_ERROR)
                return False
                
            # プロフィール情報を取得
            profile = self.client.get_profile(author_handle)
            
            # ステータスバーの更新
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText(f"{selected['username']}のプロフィールを表示します")
                
            # プロフィールダイアログを表示
            from gui.dialogs.profile_dialog import ProfileDialog
            dlg = ProfileDialog(self.parent, profile)
            dlg.ShowModal()
            dlg.Destroy()
            
            return True
            
        except Exception as e:
            logger.error(f"プロフィール表示に失敗しました: {str(e)}")
            wx.MessageBox(f"プロフィール表示に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            if hasattr(self.parent, 'statusbar'):
                self.parent.statusbar.SetStatusText("プロフィール表示に失敗しました")
            return False
    
    def on_delete(self, event):
        """投稿削除アクション
        
        Args:
            event: メニューイベント
            
        Returns:
            bool: 成功した場合はTrue
        """
        # 削除処理中なら何もしない（二重削除防止）
        if PostHandlers._deleting_post:
            return False
            
        # タイムラインから選択された投稿を取得
        selected = None
        if hasattr(self.parent, 'timeline') and hasattr(self.parent.timeline, 'get_selected_post'):
            selected = self.parent.timeline.get_selected_post()
            
        if not selected:
            wx.MessageBox("投稿を選択してください", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 自分の投稿かどうかを確認
        if not selected.get('is_own_post', False):
            wx.MessageBox("自分の投稿のみ削除できます", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 削除に必要な情報があるか確認
        if not selected.get('uri'):
            wx.MessageBox("投稿の削除に必要な情報がありません", "エラー", wx.OK | wx.ICON_ERROR)
            return False
            
        # 削除確認ダイアログ
        dlg = wx.MessageDialog(self.parent, "この投稿を削除してもよろしいですか？", "投稿削除の確認", 
                              wx.YES_NO | wx.ICON_QUESTION)
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                # 削除処理中フラグをセット
                PostHandlers._deleting_post = True
                
                # 投稿を削除
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("投稿を削除しています...")
                    
                self.client.delete_post(selected['uri'])
                
                # 削除成功
                wx.MessageBox("投稿を削除しました", "削除完了", wx.OK | wx.ICON_INFORMATION)
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("投稿が削除されました")
                
                # タイムラインを更新
                if hasattr(self.parent, 'timeline'):
                    self.parent.timeline.fetch_timeline(self.client)
                    
                return True
                
            except Exception as e:
                logger.error(f"投稿の削除に失敗しました: {str(e)}")
                wx.MessageBox(f"投稿の削除に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
                if hasattr(self.parent, 'statusbar'):
                    self.parent.statusbar.SetStatusText("投稿の削除に失敗しました")
                return False
            finally:
                # 削除処理中フラグをリセット
                PostHandlers._deleting_post = False
                
        dlg.Destroy()
        return False
