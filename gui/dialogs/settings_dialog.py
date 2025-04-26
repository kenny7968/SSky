#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
設定ダイアログ
"""

import wx
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class SettingsDialog(wx.Dialog):
    """設定ダイアログクラス"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        super().__init__(
            parent,
            title="設定",
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # シングルトンの設定マネージャーを取得
        from config.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        
        # 設定値のキャッシュ
        self.settings_cache = {
            'timeline': {
                'auto_fetch': self.settings_manager.get('timeline.auto_fetch', True),
                'fetch_interval': self.settings_manager.get('timeline.fetch_interval', 600)
            },
            'post': {
                'show_completion_dialog': self.settings_manager.get('post.show_completion_dialog', True)
            },
            'advanced': {
                'enable_debug_log': self.settings_manager.get('advanced.enable_debug_log', False)
            }
        }
        
        logger.debug(f"設定キャッシュを初期化しました: {self.settings_cache}")
        
        # 明示的にOKボタンとキャンセルボタンのIDを設定
        self.SetAffirmativeId(wx.ID_OK)
        self.SetEscapeId(wx.ID_CANCEL)
        
        # UIの初期化
        self.init_ui()
        
        # 設定値の読み込み
        self.load_settings()
        
        # ダイアログを中央に配置
        self.Centre()
        
    def init_ui(self):
        """UIの初期化"""
        # メインパネル
        panel = wx.Panel(self)
        
        # レイアウト
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 上部のスプリッター（カテゴリツリーと設定項目）
        splitter = wx.SplitterWindow(panel, style=wx.SP_BORDER)
        
        # カテゴリツリー
        self.tree = wx.TreeCtrl(
            splitter,
            style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_SINGLE
        )
        
        # 設定項目パネル
        self.settings_panel = wx.Panel(splitter)
        
        # カテゴリツリーの作成
        root = self.tree.AddRoot("設定")
        timeline_item = self.tree.AppendItem(root, "投稿一覧")
        post_item = self.tree.AppendItem(root, "投稿")
        advanced_item = self.tree.AppendItem(root, "高度な設定")
        
        # 最初のカテゴリを選択
        self.tree.SelectItem(timeline_item)
        
        # スプリッターの設定
        splitter.SplitVertically(self.tree, self.settings_panel)
        splitter.SetMinimumPaneSize(150)
        splitter.SetSashPosition(150)
        
        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 10)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        self.ok_button = wx.Button(panel, wx.ID_OK, "OK")
        self.cancel_button = wx.Button(panel, wx.ID_CANCEL, "キャンセル")
        
        button_sizer.AddButton(self.ok_button)
        button_sizer.AddButton(self.cancel_button)
        button_sizer.Realize()
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # イベントバインド
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_category_selected)
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        
        # デフォルトボタンの設定
        self.ok_button.SetDefault()
        
        # 初期カテゴリの設定項目を表示
        self.show_timeline_settings()
        
    def on_category_selected(self, event):
        """カテゴリが選択されたときの処理
        
        Args:
            event: ツリー選択イベント
        """
        item = event.GetItem()
        text = self.tree.GetItemText(item)
        
        if text == "投稿一覧":
            self.show_timeline_settings()
        elif text == "投稿":
            self.show_post_settings()
        elif text == "高度な設定":
            self.show_advanced_settings()
            
    def show_advanced_settings(self):
        """高度な設定項目を表示"""
        # 現在の設定パネルの子ウィジェットをクリア
        for child in self.settings_panel.GetChildren():
            child.Destroy()
        
        # 設定項目の作成
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # デバッグログの設定
        self.enable_debug_log_cb = wx.CheckBox(
            self.settings_panel,
            label="デバッグログを有効にする（再起動後に反映）"
        )
        sizer.Add(self.enable_debug_log_cb, 0, wx.ALL, 10)
        
        # 説明文（リードオンリーのテキストボックス）
        description = wx.TextCtrl(
            self.settings_panel,
            value="デバッグログを有効にすると、詳細なログが出力されます。\n"
                  "問題が発生した場合に開発者に報告する際に役立ちます。\n"
                  "この設定は再起動後に反映されます。",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL
        )
        # テキストボックスのサイズを適切に設定
        description.SetMinSize((-1, 60))
        sizer.Add(description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.settings_panel.SetSizer(sizer)
        
        # 設定値の読み込み（キャッシュから）
        self.enable_debug_log_cb.SetValue(
            self.settings_cache['advanced']['enable_debug_log']
        )
        
        # イベントハンドラをバインド
        self.enable_debug_log_cb.Bind(wx.EVT_CHECKBOX, self.on_debug_log_changed)
        
        self.settings_panel.Layout()
    
    def on_debug_log_changed(self, event):
        """デバッグログの有効/無効が変更されたときの処理
        
        Args:
            event: チェックボックスイベント
        """
        enabled = self.enable_debug_log_cb.GetValue()
        
        # キャッシュに値を保存
        self.settings_cache['advanced']['enable_debug_log'] = enabled
        logger.debug(f"デバッグログの有効/無効を変更しました: {enabled}")
    
    def show_timeline_settings(self):
        """投稿一覧の設定項目を表示"""
        # 現在の設定パネルの子ウィジェットをクリア
        for child in self.settings_panel.GetChildren():
            child.Destroy()
        
        # 設定項目の作成
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 自動取得の設定
        self.auto_fetch_cb = wx.CheckBox(self.settings_panel, label="投稿一覧を自動取得する")
        sizer.Add(self.auto_fetch_cb, 0, wx.ALL, 10)
        
        # 自動取得の間隔
        interval_sizer = wx.BoxSizer(wx.HORIZONTAL)
        interval_label = wx.StaticText(self.settings_panel, label="自動取得の間隔（秒）（最小180秒）：")
        self.fetch_interval_spin = wx.SpinCtrl(
            self.settings_panel,
            min=180,
            max=3600,
            initial=600
        )
        
        interval_sizer.Add(interval_label, 0, wx.ALIGN_CENTER_VERTICAL)
        interval_sizer.Add(self.fetch_interval_spin, 0, wx.LEFT, 5)
        
        sizer.Add(interval_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.settings_panel.SetSizer(sizer)
        
        # 設定値の読み込み（キャッシュから）
        self.auto_fetch_cb.SetValue(self.settings_cache['timeline']['auto_fetch'])
        self.fetch_interval_spin.SetValue(self.settings_cache['timeline']['fetch_interval'])
        
        # 自動取得の有効/無効に応じて間隔の設定を有効/無効化
        self.auto_fetch_cb.Bind(wx.EVT_CHECKBOX, self.on_auto_fetch_changed)
        
        # 値が変更されたときのイベントハンドラを追加
        self.fetch_interval_spin.Bind(wx.EVT_SPINCTRL, self.on_interval_changed)
        
        # 初期状態の設定
        self.fetch_interval_spin.Enable(self.settings_cache['timeline']['auto_fetch'])
        
        self.settings_panel.Layout()
    
    def show_post_settings(self):
        """投稿の設定項目を表示"""
        # 現在の設定パネルの子ウィジェットをクリア
        for child in self.settings_panel.GetChildren():
            child.Destroy()
        
        # 設定項目の作成
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 完了ダイアログの設定
        self.show_completion_dialog_cb = wx.CheckBox(
            self.settings_panel,
            label="投稿・返信・引用した時に完了ダイアログを表示する"
        )
        sizer.Add(self.show_completion_dialog_cb, 0, wx.ALL, 10)
        
        self.settings_panel.SetSizer(sizer)
        
        # 設定値の読み込み（キャッシュから）
        self.show_completion_dialog_cb.SetValue(
            self.settings_cache['post']['show_completion_dialog']
        )
        
        # イベントハンドラをバインド
        self.show_completion_dialog_cb.Bind(wx.EVT_CHECKBOX, self.on_completion_dialog_changed)
        
        self.settings_panel.Layout()
    
    def on_completion_dialog_changed(self, event):
        """完了ダイアログの表示設定が変更されたときの処理
        
        Args:
            event: チェックボックスイベント
        """
        enabled = self.show_completion_dialog_cb.GetValue()
        
        # キャッシュに値を保存
        self.settings_cache['post']['show_completion_dialog'] = enabled
        logger.debug(f"完了ダイアログの表示設定を変更しました: {enabled}")
    
    def on_auto_fetch_changed(self, event):
        """自動取得の有効/無効が変更されたときの処理
        
        Args:
            event: チェックボックスイベント
        """
        enabled = self.auto_fetch_cb.GetValue()
        self.fetch_interval_spin.Enable(enabled)
        
        # キャッシュに値を保存
        self.settings_cache['timeline']['auto_fetch'] = enabled
        logger.debug(f"自動取得の有効/無効を変更しました: {enabled}")
    
    def on_interval_changed(self, event):
        """自動取得の間隔が変更されたときの処理
        
        Args:
            event: スピンコントロールイベント
        """
        value = self.fetch_interval_spin.GetValue()
        if value < 180:
            wx.MessageBox(
                "自動取得の間隔は180秒以上に設定してください。",
                "設定エラー",
                wx.OK | wx.ICON_WARNING
            )
            self.fetch_interval_spin.SetValue(180)
            value = 180
        
        # キャッシュに値を保存
        self.settings_cache['timeline']['fetch_interval'] = value
        logger.debug(f"自動取得の間隔を変更しました: {value}秒")
    
    def load_settings(self):
        """設定値をUIに反映"""
        # カテゴリに応じた設定項目の表示
        item = self.tree.GetSelection()
        if item.IsOk():
            text = self.tree.GetItemText(item)
            if text == "投稿一覧":
                self.show_timeline_settings()
            elif text == "投稿":
                self.show_post_settings()
            elif text == "高度な設定":
                self.show_advanced_settings()
    
    def on_ok(self, event):
        """OKボタンがクリックされたときの処理
        
        Args:
            event: ボタンイベント
        """
        # 現在の設定値を保存
        logger.debug("OKボタンがクリックされました")
        
        # イベントを処理済みとしてマーク（デフォルトの動作を抑制）
        event.Skip(False)
        
        # 設定を保存
        success = self.save_settings()
        logger.debug(f"save_settings()の結果: {success}")
        
        if success:
            # バリデーションに成功した場合のみダイアログを閉じる
            logger.debug("設定の保存に成功したため、ダイアログを閉じます")
            self.EndModal(wx.ID_OK)
        else:
            # 保存に失敗した場合はダイアログを閉じない
            logger.debug("設定の保存に失敗したため、ダイアログを閉じません")
    
    def save_settings(self):
        """UIの設定値を保存
        
        Returns:
            bool: 保存に成功した場合はTrue
        """
        try:
            # キャッシュから設定値を取得
            auto_fetch = self.settings_cache['timeline']['auto_fetch']
            fetch_interval = self.settings_cache['timeline']['fetch_interval']
            show_completion_dialog = self.settings_cache['post']['show_completion_dialog']
            enable_debug_log = self.settings_cache['advanced']['enable_debug_log']
            
            # 設定値の詳細をログに出力
            logger.debug(f"保存する設定値: timeline.auto_fetch={auto_fetch}, timeline.fetch_interval={fetch_interval}, "
                         f"post.show_completion_dialog={show_completion_dialog}, advanced.enable_debug_log={enable_debug_log}")
            
            # バリデーション
            if fetch_interval < 180:
                logger.warning("自動取得の間隔が180秒未満です。180秒に設定します。")
                fetch_interval = 180
                self.settings_cache['timeline']['fetch_interval'] = 180
            
            # 設定値の保存
            logger.debug("設定値をsettings_managerに設定します")
            self.settings_manager.set('timeline.auto_fetch', auto_fetch)
            self.settings_manager.set('timeline.fetch_interval', fetch_interval)
            self.settings_manager.set('post.show_completion_dialog', show_completion_dialog)
            self.settings_manager.set('advanced.enable_debug_log', enable_debug_log)
            
            # 設定ファイルに保存
            logger.debug(f"設定の保存を試みます: {self.settings_manager.settings_file}")
            success = self.settings_manager.save()
            logger.debug(f"settings_manager.save()の結果: {success}")
            
            if not success:
                error_msg = "設定の保存に失敗しました。\n詳細はログを確認してください。"
                logger.error(error_msg)
                wx.MessageBox(
                    error_msg,
                    "保存エラー",
                    wx.OK | wx.ICON_ERROR
                )
            else:
                logger.debug("設定の保存に成功しました")
                # 成功メッセージを表示
                wx.MessageBox(
                    "設定を保存しました。",
                    "保存完了",
                    wx.OK | wx.ICON_INFORMATION
                )
            
            return success
        except Exception as e:
            # 例外が発生した場合はログに出力
            logger.error(f"save_settings()で例外が発生しました: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # エラーメッセージを表示
            wx.MessageBox(
                f"設定の保存中にエラーが発生しました。\n{str(e)}",
                "エラー",
                wx.OK | wx.ICON_ERROR
            )
            return False
