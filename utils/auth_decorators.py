#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
認証関連デコレータ
"""

import functools
import wx
import logging
from typing import Callable, Any, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])

# ロガーの設定
logger = logging.getLogger(__name__)

def require_authentication(error_message: str = "この操作にはログインが必要です", return_value: Any = False) -> Callable[[F], F]:
    """認証が必要な操作のデコレータ
    
    Args:
        error_message (str): 認証エラー時のメッセージ
        return_value: 認証失敗時の戻り値
        
    Returns:
        Callable[[F], F]: デコレートされた関数
        
    Example:
        @require_authentication()
        def on_new_post(self, event):
            # 自動で認証チェックが行われる
            pass
            
        @require_authentication("投稿するにはログインしてください")
        def submit_post(self, text):
            # カスタムメッセージで認証チェック
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # クライアントが存在し、ログイン状態かチェック
            if not hasattr(self, 'client') or not self.client or not self.client.is_logged_in:
                logger.warning(f"認証が必要な操作が未ログイン状態で実行されました: {func.__name__}")
                
                # エラーメッセージをユーザーに表示
                wx.MessageBox(error_message, "エラー", wx.OK | wx.ICON_ERROR)
                
                return return_value
            
            # 認証OKの場合は元の関数を実行
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator

def require_client(error_message="クライアントが初期化されていません", return_value=None):
    """クライアントが必要な操作のデコレータ
    
    Args:
        error_message (str, optional): クライアント未初期化時のメッセージ
        return_value: クライアント未初期化時の戻り値
        
    Returns:
        function: デコレートされた関数
        
    Example:
        @require_client()
        def get_profile(self, handle):
            # クライアントの存在チェックが自動で行われる
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # クライアントが存在するかチェック
            if not hasattr(self, 'client') or not self.client:
                logger.error(f"クライアントが未初期化の状態で操作が実行されました: {func.__name__}")
                
                # エラーメッセージをユーザーに表示
                wx.MessageBox(error_message, "エラー", wx.OK | wx.ICON_ERROR)
                
                return return_value
            
            # クライアントOKの場合は元の関数を実行
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator

def require_selection(get_selection_method="get_selected_post", 
                     error_message="項目を選択してください", 
                     return_value=False):
    """選択項目が必要な操作のデコレータ
    
    Args:
        get_selection_method (str): 選択項目を取得するメソッド名
        error_message (str, optional): 未選択時のメッセージ
        return_value: 未選択時の戻り値
        
    Returns:
        function: デコレートされた関数
        
    Example:
        @require_selection()
        def on_like(self, event):
            # 投稿選択チェックが自動で行われる
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 選択項目を取得するメソッドが存在するかチェック
            if hasattr(self, 'parent') and hasattr(self.parent, 'timeline'):
                timeline = self.parent.timeline
                if hasattr(timeline, get_selection_method):
                    selected = getattr(timeline, get_selection_method)()
                    if not selected:
                        logger.debug(f"項目未選択で操作が実行されました: {func.__name__}")
                        wx.MessageBox(error_message, "エラー", wx.OK | wx.ICON_ERROR)
                        return return_value
                else:
                    logger.warning(f"選択取得メソッドが見つかりません: {get_selection_method}")
            else:
                logger.warning(f"タイムラインオブジェクトが見つかりません")
            
            # 選択項目OKの場合は元の関数を実行
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator

def combine_decorators(*decorators):
    """複数のデコレータを組み合わせるヘルパー関数
    
    Args:
        *decorators: 組み合わせるデコレータのリスト
        
    Returns:
        function: 組み合わされたデコレータ
        
    Example:
        @combine_decorators(
            require_authentication("いいねするにはログインが必要です"),
            require_selection("投稿を選択してください")
        )
        def on_like(self, event):
            pass
    """
    def decorator(func):
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator

# よく使用される組み合わせデコレータ
def require_auth_and_selection(auth_message="この操作にはログインが必要です",
                               selection_message="投稿を選択してください"):
    """認証と選択の両方が必要な操作のデコレータ
    
    Args:
        auth_message (str): 認証エラー時のメッセージ
        selection_message (str): 未選択時のメッセージ
        
    Returns:
        function: デコレートされた関数
    """
    return combine_decorators(
        require_authentication(auth_message),
        require_selection(error_message=selection_message)
    )