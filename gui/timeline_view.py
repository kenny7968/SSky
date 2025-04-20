#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインビュークラス（リストビュー実装）
"""

import wx
import wx.lib.mixins.listctrl as listmix
import logging
from utils.time_format import format_relative_time
from gui.dialogs.post_detail_dialog import PostDetailDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class TimelineView(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """タイムラインビュークラス（リストビュー実装）"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        wx.ListCtrl.__init__(
            self, 
            parent, 
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_THEME
        )
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        # カラム設定
        self.InsertColumn(0, "ユーザー", width=150)
        self.InsertColumn(1, "投稿内容", width=400)
        self.InsertColumn(2, "時間", width=100)
        
        # 選択中の投稿インデックス
        self.selected_index = -1
        
        # 投稿データの初期化
        self.posts = []
        self.post_count = 0
        
        # UIの初期化
        self.init_ui()
        
        # イベントバインド
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # アクセシビリティ
        self.SetName("タイムラインビュー")
        
        # フォーカス設定
        self.SetFocus()
        
    def init_ui(self):
        """UIの初期化"""
        # 投稿がない場合
        if not self.posts:
            # リストビューは空のままで、ステータスバーなどで通知する方が良い
            return
            
        # 投稿データをリストに追加
        for i, post in enumerate(self.posts):
            # ユーザー名のみを表示
            user_text = post['username']
            
            # リストに追加
            index = self.InsertItem(i, user_text)
            self.SetItem(index, 1, post['content'])
            self.SetItem(index, 2, post['time'])
            
            # データを関連付け
            self.SetItemData(index, i)
            
        # 最初の項目を選択
        if self.GetItemCount() > 0:
            self.Select(0)
            self.Focus(0)
            
    def on_item_selected(self, event):
        """アイテム選択時の処理
        
        Args:
            event: リストイベント
        """
        self.selected_index = event.GetIndex()
        
        # 選択された投稿の情報を取得
        post = self.posts[self.selected_index]
        is_own_post = post.get('is_own_post', False)
        
        # 親フレームのメニューバーを取得
        frame = wx.GetTopLevelParent(self)
        menubar = frame.GetMenuBar()
        
        # ポストメニューを取得（インデックス1がポストメニュー）
        post_menu = menubar.GetMenu(1)
        
        # 「投稿を削除」メニュー項目を取得（インデックス5が削除）
        delete_item = post_menu.FindItemByPosition(5)
        
        # 自分の投稿かどうかに基づいて有効/無効を設定
        if delete_item:
            delete_item.Enable(is_own_post)
        
        event.Skip()
        
    def on_item_activated(self, event):
        """アイテムアクティベート時の処理（ダブルクリックなど）
        
        Args:
            event: リストイベント
        """
        index = event.GetIndex()
        post = self.posts[index]
        
        # 投稿の詳細表示（例：ダイアログ表示）
        dlg = PostDetailDialog(self, post)
        dlg.ShowModal()
        dlg.Destroy()
        
        event.Skip()
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        shift_down = event.ShiftDown()
        
        # 選択されている項目がない場合は通常のキー処理を行う
        if self.selected_index == -1:
            event.Skip()
            return
            
        # ショートカットキーの処理
        if ctrl_down:
            if key_code == ord('N'):  # Ctrl+N
                # 新規投稿（親フレームのメソッドを呼び出す）
                frame = wx.GetTopLevelParent(self)
                if hasattr(frame, 'on_new_post'):
                    frame.on_new_post(event)
                return
            elif key_code == ord('L'):  # Ctrl+L
                self.on_like(event)
                return
            elif key_code == ord('R'):  # Ctrl+R
                if shift_down:  # Ctrl+Shift+R
                    self.on_repost(event)
                else:  # Ctrl+R
                    self.on_reply(event)
                return
            elif key_code == ord('Q'):  # Ctrl+Q
                self.on_quote(event)
                return
            elif key_code == ord('P'):  # Ctrl+P
                self.on_profile(event)
                return
        
        # Delキーで投稿削除
        if key_code == wx.WXK_DELETE:
            self.on_delete(event)
            return
            
        # Shift+F10でコンテキストメニュー表示
        if shift_down and key_code == wx.WXK_F10:
            # 選択されている項目の位置を取得
            item_rect = self.GetItemRect(self.selected_index)
            pos = wx.Point(item_rect.x + item_rect.width // 2, item_rect.y + item_rect.height // 2)
            self.show_context_menu(pos)
            return
            
        event.Skip()
        
    def on_context_menu(self, event):
        """コンテキストメニュー表示時の処理（右クリック）
        
        Args:
            event: マウスイベント
        """
        # 選択されている項目がない場合は何もしない
        if self.selected_index == -1:
            return
            
        # マウス位置を取得
        pos = event.GetPosition()
        
        # スクリーン座標からクライアント座標に変換
        pos = self.ScreenToClient(pos)
        
        # コンテキストメニューを表示
        self.show_context_menu(pos)
        
    def show_context_menu(self, pos):
        """コンテキストメニューを表示
        
        Args:
            pos: 表示位置
        """
        # 選択されている投稿
        post = self.posts[self.selected_index]
        
        # コンテキストメニューの作成
        menu = wx.Menu()
        
        # メニュー項目の追加（ショートカットキーとアクセラレータキー表示付き）
        like_item = menu.Append(wx.ID_ANY, "いいね(&L)\tCtrl+L")
        reply_item = menu.Append(wx.ID_ANY, "返信(&R)\tCtrl+R")
        repost_item = menu.Append(wx.ID_ANY, "リポスト(&T)\tCtrl+Shift+R")
        quote_item = menu.Append(wx.ID_ANY, "引用(&Q)\tCtrl+Q")
        profile_item = menu.Append(wx.ID_ANY, "投稿者のプロフィールを表示(&P)\tCtrl+P")
        delete_item = menu.Append(wx.ID_ANY, "投稿を削除(&D)\tDel")
        
        # 自分の投稿以外は削除メニューを無効化
        if not post.get('is_own_post', False):
            delete_item.Enable(False)
        
        # イベントバインド
        self.Bind(wx.EVT_MENU, self.on_like, like_item)
        self.Bind(wx.EVT_MENU, self.on_reply, reply_item)
        self.Bind(wx.EVT_MENU, self.on_quote, quote_item)
        self.Bind(wx.EVT_MENU, self.on_repost, repost_item)
        self.Bind(wx.EVT_MENU, self.on_profile, profile_item)
        self.Bind(wx.EVT_MENU, self.on_delete, delete_item)
        
        # 自分の投稿はリポストできない
        if post.get('is_own_post', False):
            repost_item.Enable(False)
        
        # メニュー表示
        self.PopupMenu(menu, pos)
        menu.Destroy()
        
    def on_like(self, event):
        """いいねアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_likeメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_like'):
                frame.on_like(event)
        
    def on_reply(self, event):
        """返信アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_replyメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_reply'):
                frame.on_reply(event)
        
    def on_quote(self, event):
        """引用アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_quoteメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_quote'):
                frame.on_quote(event)
                
    def on_repost(self, event):
        """リポストアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_repostメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_repost'):
                frame.on_repost(event)
        
    def on_profile(self, event):
        """プロフィール表示アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_profileメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_profile'):
                frame.on_profile(event)
            else:
                post = self.posts[self.selected_index]
                wx.MessageBox(f"プロフィールを表示します: {post['username']}", "プロフィール", wx.OK | wx.ICON_INFORMATION)
    
    def on_delete(self, event):
        """削除アクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index != -1:
            # 親フレームのon_deleteメソッドを呼び出す
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'on_delete'):
                frame.on_delete(event)
    
    def fetch_timeline(self, client=None, selected_uri=None):
        """Bluesky APIを使用してタイムラインを取得
        
        Args:
            client (BlueskyClient, optional): Blueskyクライアント
            selected_uri (str, optional): 選択する投稿のURI
        """
        # 現在選択されている投稿のURIを記憶（引数で指定されていない場合）
        if selected_uri is None and self.selected_index != -1 and self.selected_index < len(self.posts):
            selected_uri = self.posts[self.selected_index].get('uri')
            logger.info(f"現在選択されている投稿のURI: {selected_uri}")
        
        # クライアントが渡されなかった場合は親フレームから取得
        if not client:
            frame = wx.GetTopLevelParent(self)
            if hasattr(frame, 'client'):
                client = frame.client
        
        # クライアントがない場合は何もしない
        if not client:
            logger.warning("タイムラインの取得に失敗しました: クライアントが設定されていません")
            return
            
        try:
            # タイムラインの取得（最新50件）
            logger.info("タイムラインを取得しています...")
            timeline_data = client.get_timeline(limit=50)
            
            # 投稿データの変換と格納
            self.posts = []
            
            for post in timeline_data.feed:
                # 投稿情報のログ出力は削除
                
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
                    'is_own_post': post.post.author.handle == client.profile.handle,  # 自分の投稿かどうか
                    # スレッド情報を追加
                    'reply_parent': None,
                    'reply_root': None
                }
                
                # スレッド情報を取得（返信の場合）
                if hasattr(post.post.record, 'reply') and post.post.record.reply:
                    logger.debug(f"返信投稿を検出: {post.post.uri}")
                    
                    # 親投稿の情報
                    if hasattr(post.post.record.reply, 'parent'):
                        parent_uri = getattr(post.post.record.reply.parent, 'uri', None)
                        parent_cid = getattr(post.post.record.reply.parent, 'cid', None)
                        
                        if parent_uri and parent_cid:
                            post_data['reply_parent'] = {
                                'uri': parent_uri,
                                'cid': parent_cid
                            }
                            logger.debug(f"親投稿情報: {parent_uri}")
                    
                    # ルート投稿の情報
                    if hasattr(post.post.record.reply, 'root'):
                        root_uri = getattr(post.post.record.reply.root, 'uri', None)
                        root_cid = getattr(post.post.record.reply.root, 'cid', None)
                        
                        if root_uri and root_cid:
                            post_data['reply_root'] = {
                                'uri': root_uri,
                                'cid': root_cid
                            }
                            logger.debug(f"ルート投稿情報: {root_uri}")
                    
                    # デバッグ出力
                    logger.debug(f"スレッド情報: parent={post_data.get('reply_parent') is not None}, root={post_data.get('reply_root') is not None}")
                self.posts.append(post_data)
                
            # 投稿日時でソート（最新が下）- raw_timestampフィールドを使用
            self.posts.sort(key=lambda x: x['raw_timestamp'], reverse=False)
            self.post_count = len(self.posts)
            
            # UIの更新
            self.DeleteAllItems()
            self.init_ui()
            
            # 以前選択していた投稿と同じURIを持つ投稿を選択
            if selected_uri:
                for i, post in enumerate(self.posts):
                    if post.get('uri') == selected_uri:
                        logger.info(f"以前選択していた投稿を再選択: index={i}, uri={selected_uri}")
                        self.Select(i)
                        self.Focus(i)
                        self.selected_index = i
                        # 選択した項目が表示されるようにスクロール
                        self.EnsureVisible(i)
                        break
            
            logger.info(f"タイムラインを取得しました: {len(self.posts)}件")
            
        except Exception as e:
            logger.error(f"タイムラインの取得に失敗しました: {str(e)}", exc_info=True)
    
    def get_selected_post(self):
        """選択中の投稿データを取得
        
        Returns:
            dict: 選択中の投稿データ。選択されていない場合はNone
        """
        if 0 <= self.selected_index < len(self.posts):
            return self.posts[self.selected_index]
        return None
