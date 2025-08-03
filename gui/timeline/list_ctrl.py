#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
タイムラインリストコントロールクラス
"""

import wx
import wx.lib.mixins.listctrl as listmix
import logging
from gui.dialogs.post_detail_dialog import PostDetailDialog

# ロガーの設定
logger = logging.getLogger(__name__)

class TimelineListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """タイムラインリストコントロールクラス"""
    
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
        
        # イベントバインド
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # アクセシビリティ
        self.SetName("タイムラインリスト")
        
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
            
            # 引用ポストの場合は引用元情報も表示
            if post.get('is_quote_post', False) and post.get('quote_of'):
                quote_info = post['quote_of']
                display_content = f"{post['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
            else:
                display_content = post['content']
                
            self.SetItem(index, 1, display_content)
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
        
        # F5キーでタイムライン更新
        if key_code == wx.WXK_F5:
            # 親パネルのタイムライン取得メソッドを呼び出す
            parent = self.GetParent()
            if hasattr(parent, 'on_fetch_button'):
                parent.on_fetch_button(event)
            return
        
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
            elif key_code == ord('E'):  # Ctrl+E
                self.on_open_url(event)
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
        open_url_item = menu.Append(wx.ID_ANY, "URLを開く(&E)\tCtrl+E")
        menu.AppendSeparator()  # 区切り線
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
        self.Bind(wx.EVT_MENU, self.on_open_url, open_url_item)
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
    
    def on_open_url(self, event):
        """URLを開くアクション
        
        Args:
            event: メニューイベント
        """
        if self.selected_index == -1:
            return
            
        # 選択中の投稿を取得
        post = self.posts[self.selected_index]
        
        # URLユーティリティをインポート
        from utils.url_utils import handle_urls_in_text
        
        # 投稿内容からURLを検出して開く（facets情報も渡す）
        handle_urls_in_text(post['content'], self, post.get('facets'))
    
    def get_selected_post(self):
        """選択中の投稿データを取得
        
        Returns:
            dict: 選択中の投稿データ。選択されていない場合はNone
        """
        if 0 <= self.selected_index < len(self.posts):
            return self.posts[self.selected_index]
        return None
    
    def get_selected_post_uri(self):
        """選択中の投稿のURIを取得
        
        Returns:
            str: 選択中の投稿のURI。選択されていない場合はNone
        """
        post = self.get_selected_post()
        if post:
            return post.get('uri')
        return None
    
    def find_post_by_uri(self, uri):
        """URIから投稿を検索
        
        Args:
            uri (str): 検索する投稿のURI
            
        Returns:
            int: 投稿のインデックス。見つからない場合は-1
        """
        if not uri:
            return -1
            
        for i, post in enumerate(self.posts):
            if post.get('uri') == uri:
                return i
        return -1
    
    def update_post(self, index, post_data):
        """投稿を更新
        
        Args:
            index (int): 更新する投稿のインデックス
            post_data (dict): 新しい投稿データ
            
        Returns:
            bool: 更新に成功した場合はTrue
        """
        if 0 <= index < len(self.posts):
            # 投稿データを更新
            self.posts[index] = post_data
            
            # 引用ポストの場合は引用元情報も表示
            if post_data.get('is_quote_post', False) and post_data.get('quote_of'):
                quote_info = post_data['quote_of']
                display_content = f"{post_data['content']}\n\n【引用】{quote_info['handle']} - {quote_info['content']}"
            else:
                display_content = post_data['content']
            
            # リストビューの表示を更新
            self.SetItem(index, 0, post_data['username'])
            self.SetItem(index, 1, display_content)
            self.SetItem(index, 2, post_data['time'])
            
            logger.debug(f"投稿を更新しました: index={index}, uri={post_data.get('uri')}")
            return True
        return False
    
    def select_post_by_uri(self, uri):
        """URIから投稿を選択
        
        Args:
            uri (str): 選択する投稿のURI
            
        Returns:
            bool: 選択に成功した場合はTrue
        """
        index = self.find_post_by_uri(uri)
        if index >= 0:
            self.Select(index)
            self.Focus(index)
            self.selected_index = index
            # 選択した項目が表示されるようにスクロール
            self.EnsureVisible(index)
            logger.debug(f"投稿を選択しました: index={index}, uri={uri}")
            return True
        return False
    
    def remove_post_by_uri(self, uri):
        """URIから投稿を削除
        
        Args:
            uri (str): 削除する投稿のURI
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        if not uri:
            return False
            
        index = self.find_post_by_uri(uri)
        if index >= 0:
            # ローカルリストから削除
            del self.posts[index]
            self.post_count = len(self.posts)
            
            # UIから削除
            self.DeleteItem(index)
            
            # 選択状態を調整
            if self.selected_index == index:
                # 削除された項目が選択されていた場合
                if index < self.post_count:
                    # 次の項目を選択
                    self.Select(index)
                    self.selected_index = index
                elif self.post_count > 0:
                    # 最後の項目を選択
                    self.Select(self.post_count - 1)
                    self.selected_index = self.post_count - 1
                else:
                    # リストが空になった場合
                    self.selected_index = -1
            elif self.selected_index > index:
                # 削除された項目より後ろが選択されていた場合はインデックスを調整
                self.selected_index -= 1
            
            # 再描画
            self.Refresh()
            
            logger.info(f"投稿を削除しました: uri={uri}")
            return True
        
        logger.debug(f"削除対象の投稿が見つかりませんでした: uri={uri}")
        return False