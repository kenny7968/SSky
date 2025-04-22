#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
投稿詳細ダイアログ
"""

import wx
import logging
from utils.url_utils import extract_urls, open_url, handle_urls_in_text, extract_urls_from_facets

# ロガーの設定
logger = logging.getLogger(__name__)

class PostDetailDialog(wx.Dialog):
    """投稿詳細ダイアログ"""
    
    def __init__(self, parent, post_data):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            post_data (dict): 投稿データ
        """
        super(PostDetailDialog, self).__init__(
            parent, 
            title=f"{post_data['username']}の投稿",
            size=(500, 300),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.post_data = post_data
        
        # UIの初期化
        self.init_ui()
        
        # キーイベントのバインド
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        
        # 中央に配置
        self.Centre()
        
    def on_key_down(self, event):
        """キー入力時の処理
        
        Args:
            event: キーイベント
        """
        key_code = event.GetKeyCode()
        
        # Escキーが押されたらダイアログを閉じる
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CLOSE)
        # Enterキーが押されたらカーソル位置のURLを開く
        elif key_code == wx.WXK_RETURN:
            self.open_url_at_cursor()
        else:
            event.Skip()
            
    def open_url_at_cursor(self):
        """カーソル位置のURLを開く"""
        # facets情報がある場合は、それを優先的に使用
        if 'facets' in self.post_data and self.post_data['facets']:
            # 投稿内容全体に対してfacetsからURLを抽出して開く
            handle_urls_in_text(self.post_data['content'], self, self.post_data['facets'])
            return
            
        # facets情報がない場合は、従来の方法でURLを検出
        # 現在のカーソル位置を取得
        pos = self.content.GetInsertionPoint()
        text = self.content.GetValue()
        
        # カーソル位置の前後のテキストを取得
        before_text = text[:pos]
        after_text = text[pos:]
        
        # URLを検出
        urls_before = extract_urls(before_text)
        urls_after = extract_urls(after_text)
        
        # カーソル位置に最も近いURLを特定
        url_to_open = None
        
        if urls_before and urls_after:
            # 前後両方にURLがある場合、より近い方を選択
            if len(before_text) - before_text.rfind(urls_before[-1]) < after_text.find(urls_after[0]):
                url_to_open = urls_before[-1]
            else:
                url_to_open = urls_after[0]
        elif urls_before:
            # 前にのみURLがある場合
            url_to_open = urls_before[-1]
        elif urls_after:
            # 後ろにのみURLがある場合
            url_to_open = urls_after[0]
            
        # URLが見つかった場合は開く
        if url_to_open:
            open_url(url_to_open)
            
    def on_url_click(self, event):
        """URLクリック時の処理
        
        Args:
            event: URLイベント
        """
        # facets情報がある場合は、それを優先的に使用
        if 'facets' in self.post_data and self.post_data['facets']:
            # 投稿内容全体に対してfacetsからURLを抽出して開く
            handle_urls_in_text(self.post_data['content'], self, self.post_data['facets'])
            return
            
        # facets情報がない場合は、従来の方法でURLを検出
        # クリックされたURLの範囲を取得
        start = event.GetURLStart()
        end = event.GetURLEnd()
        
        # URLテキストを取得
        url = self.content.GetRange(start, end)
        
        # URLを開く
        if url:
            open_url(url)
        
    def init_ui(self):
        """UIの初期化"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 投稿内容（リードオンリーエディット）- 全ての情報を含む
        content_text = f"{self.post_data['username']} {self.post_data['handle']} - {self.post_data['time']}\n\n"
        content_text += f"{self.post_data['content']}\n\n"
        content_text += f"いいね: {self.post_data['likes']}  返信: {self.post_data['replies']}  リポスト: {self.post_data['reposts']}"
        
        self.content = wx.TextCtrl(
            panel, 
            value=content_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.BORDER_SIMPLE
        )
        # フォントとサイズの設定
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.content.SetFont(font)
        # 背景色の設定（システムの背景色に合わせる）
        self.content.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        main_sizer.Add(self.content, 1, wx.ALL | wx.EXPAND, 10)
        
        # URLクリックイベントのバインド
        self.content.Bind(wx.EVT_TEXT_URL, self.on_url_click)
        
        # 区切り線
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        
        # アクションボタン
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # いいねボタン
        like_btn = wx.Button(panel, label="いいね", size=(80, -1))
        like_btn.Bind(wx.EVT_BUTTON, self.on_like)
        button_sizer.Add(like_btn, 0, wx.ALL, 5)
        
        # 返信ボタン
        reply_btn = wx.Button(panel, label="返信", size=(80, -1))
        reply_btn.Bind(wx.EVT_BUTTON, self.on_reply)
        button_sizer.Add(reply_btn, 0, wx.ALL, 5)
        
        # リポストボタン
        repost_btn = wx.Button(panel, label="リポスト", size=(80, -1))
        repost_btn.Bind(wx.EVT_BUTTON, self.on_repost)
        # 自分の投稿はリポストできない
        if self.post_data.get('is_own_post', False):
            repost_btn.Enable(False)
        button_sizer.Add(repost_btn, 0, wx.ALL, 5)
        
        # 引用ボタン
        quote_btn = wx.Button(panel, label="引用", size=(80, -1))
        quote_btn.Bind(wx.EVT_BUTTON, self.on_quote)
        button_sizer.Add(quote_btn, 0, wx.ALL, 5)
        
        # 閉じるボタン
        close_btn = wx.Button(panel, wx.ID_CLOSE, "閉じる")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        button_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
    def on_like(self, event):
        """いいねボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # 親フレームのon_likeメソッドを呼び出す
        frame = wx.GetTopLevelParent(self.GetParent())
        if hasattr(frame, 'on_like'):
            frame.on_like(event)
        
    def on_reply(self, event):
        """返信ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # 親フレームのon_replyメソッドを呼び出す
        frame = wx.GetTopLevelParent(self.GetParent())
        if hasattr(frame, 'on_reply'):
            frame.on_reply(event)
        
    def on_quote(self, event):
        """引用ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # 親フレームのon_quoteメソッドを呼び出す
        frame = wx.GetTopLevelParent(self.GetParent())
        if hasattr(frame, 'on_quote'):
            frame.on_quote(event)
            
    def on_repost(self, event):
        """リポストボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        # 親フレームのon_repostメソッドを呼び出す
        frame = wx.GetTopLevelParent(self.GetParent())
        if hasattr(frame, 'on_repost'):
            frame.on_repost(event)
        
    def on_close(self, event):
        """閉じるボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        self.EndModal(wx.ID_CLOSE)
