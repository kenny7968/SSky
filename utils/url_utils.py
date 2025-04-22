#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
URL関連ユーティリティ
"""

import re
import wx
import webbrowser
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

# URLを検出する正規表現パターン
# https://から始まるURLと、www.から始まるURLの両方を検出
URL_PATTERN = r'(?:https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!./?=&#+]*)*)|(?:www\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!./?=&#+]*)*)'

def extract_urls(text):
    """テキストからURLを抽出する
    
    Args:
        text (str): 対象テキスト
        
    Returns:
        list: 抽出されたURLのリスト
    """
    if not text:
        return []
        
    # URLを検出
    urls = re.findall(URL_PATTERN, text)
    return urls

def open_url(url):
    """URLをデフォルトブラウザで開く
    
    Args:
        url (str): 開くURL
        
    Returns:
        bool: 成功した場合はTrue
    """
    try:
        # www.で始まるURLにhttps://を追加
        if url.startswith('www.'):
            url = 'https://' + url
            
        logger.info(f"URLを開きます: {url}")
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"URLを開けませんでした: {str(e)}")
        wx.MessageBox(f"URLを開けませんでした: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        return False

def extract_urls_from_facets(facets):
    """facetsからURLを抽出する
    
    Args:
        facets (list): facetsリスト
        
    Returns:
        list: 抽出されたURLのリスト
    """
    if not facets:
        return []
        
    urls = []
    
    try:
        for facet in facets:
            # featuresプロパティがあるか確認
            if not hasattr(facet, 'features'):
                continue
                
            for feature in facet.features:
                # Linkタイプのfeatureからuriを取得
                if hasattr(feature, '$type'):
                    type_value = getattr(feature, '$type')
                    if type_value == 'app.bsky.richtext.facet#link' and hasattr(feature, 'uri'):
                        urls.append(feature.uri)
                # 新しいAPIでは型情報が異なる可能性があるため、代替チェック
                elif hasattr(feature, 'uri'):
                    urls.append(feature.uri)
    except Exception as e:
        logger.error(f"facetsからのURL抽出中にエラーが発生しました: {str(e)}")
    
    return urls

def handle_urls_in_text(text, parent=None, facets=None):
    """テキスト内のURLを処理し、必要に応じてブラウザで開く
    
    Args:
        text (str): 対象テキスト
        parent (wx.Window, optional): 親ウィンドウ
        facets (list, optional): facetsリスト
        
    Returns:
        bool: URLが開かれた場合はTrue
    """
    # まずfacetsからURLを抽出
    urls = []
    if facets:
        urls = extract_urls_from_facets(facets)
        logger.debug(f"facetsから抽出されたURL: {urls}")
    
    # facetsからURLが見つからなかった場合は正規表現で抽出
    if not urls:
        urls = extract_urls(text)
        logger.debug(f"正規表現で抽出されたURL: {urls}")
    
    # URLが見つからない場合
    if not urls:
        if parent:
            wx.MessageBox("URLが見つかりませんでした", "情報", wx.OK | wx.ICON_INFORMATION)
        return False
        
    # URLが1つの場合は直接開く
    if len(urls) == 1:
        return open_url(urls[0])
        
    # URLが複数ある場合はダイアログで選択
    if parent:
        dlg = wx.SingleChoiceDialog(
            parent,
            "開くURLを選択してください",
            "URL選択",
            urls
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            selected_url = dlg.GetStringSelection()
            dlg.Destroy()
            return open_url(selected_url)
            
        dlg.Destroy()
        
    return False
