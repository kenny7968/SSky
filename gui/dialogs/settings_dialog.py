#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
設定ダイアログ
"""

import wx
import logging
from .base_dialog import BaseDialog
from utils.i18n import get_i18n

# ロガーの設定
logger = logging.getLogger(__name__)

class SettingsDialog(BaseDialog):
    """設定ダイアログクラス"""
    
    def __init__(self, parent):
        """初期化
        
        Args:
            parent: 親ウィンドウ
        """
        # 国際化システムの取得
        self.i18n = get_i18n()
        
        super().__init__(
            parent,
            title=self.i18n.get_message("settings.title"),
            size=(500, 400)
        )
        
        # ダイアログが破棄中かどうかを示すフラグ
        self.is_being_destroyed = False
        
        # シングルトンの設定マネージャーを取得
        from config.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        
        # 設定値のキャッシュ
        self.settings_cache = {
            'timeline': {
                'fetch_count': self.settings_manager.get('timeline.fetch_count', 50),
                'auto_fetch': self.settings_manager.get('timeline.auto_fetch', True),
                'fetch_interval': self.settings_manager.get('timeline.fetch_interval', 600)
            },
            'post': {
                'show_completion_dialog': self.settings_manager.get('post.show_completion_dialog', True)
            },
            'language': {
                'locale': self.settings_manager.get('language.locale', 'ja')
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
        root = self.tree.AddRoot(self.i18n.get_message("settings.title"))
        timeline_item = self.tree.AppendItem(root, self.i18n.get_message("settings.categories.timeline"))
        post_item = self.tree.AppendItem(root, self.i18n.get_message("settings.categories.post"))
        language_item = self.tree.AppendItem(root, self.i18n.get_message("settings.categories.language"))
        advanced_item = self.tree.AppendItem(root, self.i18n.get_message("settings.categories.advanced"))
        
        # 最初のカテゴリを選択
        self.tree.SelectItem(timeline_item)
        
        # スプリッターの設定
        splitter.SplitVertically(self.tree, self.settings_panel)
        splitter.SetMinimumPaneSize(150)
        splitter.SetSashPosition(150)
        
        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 10)
        
        # ボタン
        button_sizer = wx.StdDialogButtonSizer()
        self.ok_button = wx.Button(panel, wx.ID_OK, self.i18n.get_message("button.ok"))
        self.cancel_button = wx.Button(panel, wx.ID_CANCEL, self.i18n.get_message("button.cancel"))
        
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
        
    def Destroy(self):
        """ダイアログを破棄する前に呼び出される
        
        Returns:
            bool: 破棄に成功した場合はTrue
        """
        # ダイアログが破棄中であることを示すフラグを設定
        self.is_being_destroyed = True
        return super().Destroy()
    
    def on_category_selected(self, event):
        """カテゴリが選択されたときの処理
        
        Args:
            event: ツリー選択イベント
        """
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
        item = event.GetItem()
        text = self.tree.GetItemText(item)
        
        if text == self.i18n.get_message("settings.categories.timeline"):
            self.show_timeline_settings()
        elif text == self.i18n.get_message("settings.categories.post"):
            self.show_post_settings()
        elif text == self.i18n.get_message("settings.categories.language"):
            self.show_language_settings()
        elif text == self.i18n.get_message("settings.categories.advanced"):
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
            label=self.i18n.get_message("settings.advanced.enable_debug_log")
        )
        sizer.Add(self.enable_debug_log_cb, 0, wx.ALL, 10)
        
        # 説明文（リードオンリーのテキストボックス）
        description = wx.TextCtrl(
            self.settings_panel,
            value=self.i18n.get_message("settings.advanced.debug_log_description"),
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
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
        enabled = self.enable_debug_log_cb.GetValue()
        
        # キャッシュに値を保存
        self.settings_cache['advanced']['enable_debug_log'] = enabled
        logger.debug(f"デバッグログの有効/無効を変更しました: {enabled}")
    
    def show_language_settings(self):
        """言語設定項目を表示"""
        # 現在の設定パネルの子ウィジェットをクリア
        for child in self.settings_panel.GetChildren():
            child.Destroy()
        
        # 設定項目の作成
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 言語選択
        language_sizer = wx.BoxSizer(wx.HORIZONTAL)
        language_label = wx.StaticText(self.settings_panel, label=self.i18n.get_message("settings.language.label"))
        language_sizer.Add(language_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # 言語選択コンボボックス
        self.language_choice = wx.Choice(self.settings_panel)
        
        # 利用可能な言語を取得してコンボボックスに追加
        available_languages = self.settings_manager.get_available_languages()
        for locale_code, display_name in available_languages:
            self.language_choice.Append(display_name, locale_code)
        
        language_sizer.Add(self.language_choice, 1, wx.EXPAND)
        sizer.Add(language_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 説明文
        description = wx.TextCtrl(
            self.settings_panel,
            value=self.i18n.get_message("settings.language.description"),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL
        )
        description.SetMinSize((-1, 50))
        sizer.Add(description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.settings_panel.SetSizer(sizer)
        
        # 設定値の読み込み（キャッシュから）
        current_locale = self.settings_cache['language']['locale']
        for i in range(self.language_choice.GetCount()):
            if self.language_choice.GetClientData(i) == current_locale:
                self.language_choice.SetSelection(i)
                break
        
        # イベントハンドラをバインド
        self.language_choice.Bind(wx.EVT_CHOICE, self.on_language_changed)
        
        self.settings_panel.Layout()
    
    def on_language_changed(self, event):
        """言語が変更されたときの処理
        
        Args:
            event: 選択イベント
        """
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
        
        selection = self.language_choice.GetSelection()
        if selection != wx.NOT_FOUND:
            locale_code = self.language_choice.GetClientData(selection)
            
            # キャッシュに値を保存
            self.settings_cache['language']['locale'] = locale_code
            logger.debug(f"言語を変更しました: {locale_code}")
            
            # 即座にI18nシステムを更新
            try:
                from utils.i18n import get_i18n
                i18n = get_i18n()
                if i18n.set_locale(locale_code):
                    logger.info(f"言語をリアルタイム更新しました: {locale_code}")
                    # ダイアログのタイトルと説明文を更新
                    self.update_language_ui()
                else:
                    logger.error(f"言語のリアルタイム更新に失敗しました: {locale_code}")
            except Exception as e:
                logger.error(f"言語更新中にエラーが発生しました: {str(e)}")
    
    def update_language_ui(self):
        """言語変更時のUI更新"""
        try:
            # 現在表示中のカテゴリを再表示して言語を反映
            item = self.tree.GetSelection()
            if item.IsOk():
                text = self.tree.GetItemText(item)
                if text == self.i18n.get_message("settings.categories.language"):
                    # 言語設定画面の説明文を更新
                    self.show_language_settings()
        except Exception as e:
            logger.warning(f"UIの言語更新に失敗しました: {str(e)}")
    
    def show_timeline_settings(self):
        """投稿一覧の設定項目を表示"""
        # 現在の設定パネルの子ウィジェットをクリア
        for child in self.settings_panel.GetChildren():
            child.Destroy()
        
        # 設定項目の作成
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 投稿の取得件数
        count_sizer = wx.BoxSizer(wx.HORIZONTAL)
        count_label = wx.StaticText(self.settings_panel, label="投稿の取得件数（最大100件）：")
        self.fetch_count_spin = wx.SpinCtrl(
            self.settings_panel,
            min=1,
            max=100,
            initial=50
        )
        
        count_sizer.Add(count_label, 0, wx.ALIGN_CENTER_VERTICAL)
        count_sizer.Add(self.fetch_count_spin, 0, wx.LEFT, 5)
        
        sizer.Add(count_sizer, 0, wx.ALL, 10)
        
        # 自動取得の設定
        self.auto_fetch_cb = wx.CheckBox(self.settings_panel, label="投稿一覧を自動取得する")
        sizer.Add(self.auto_fetch_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
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
        self.fetch_count_spin.SetValue(self.settings_cache['timeline']['fetch_count'])
        self.auto_fetch_cb.SetValue(self.settings_cache['timeline']['auto_fetch'])
        self.fetch_interval_spin.SetValue(self.settings_cache['timeline']['fetch_interval'])
        
        # 自動取得の有効/無効に応じて間隔の設定を有効/無効化
        self.auto_fetch_cb.Bind(wx.EVT_CHECKBOX, self.on_auto_fetch_changed)
        
        # 値が変更されたときのイベントハンドラを追加
        self.fetch_count_spin.Bind(wx.EVT_SPINCTRL, self.on_count_changed)
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
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
        enabled = self.show_completion_dialog_cb.GetValue()
        
        # キャッシュに値を保存
        self.settings_cache['post']['show_completion_dialog'] = enabled
        logger.debug(f"完了ダイアログの表示設定を変更しました: {enabled}")
    
    def on_auto_fetch_changed(self, event):
        """自動取得の有効/無効が変更されたときの処理
        
        Args:
            event: チェックボックスイベント
        """
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
        enabled = self.auto_fetch_cb.GetValue()
        self.fetch_interval_spin.Enable(enabled)
        
        # キャッシュに値を保存
        self.settings_cache['timeline']['auto_fetch'] = enabled
        logger.debug(f"自動取得の有効/無効を変更しました: {enabled}")
    
    def on_count_changed(self, event):
        """投稿の取得件数が変更されたときの処理
        
        Args:
            event: スピンコントロールイベント
        """
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
        value = self.fetch_count_spin.GetValue()
        if value < 1:
            wx.MessageBox(
                "投稿の取得件数は1以上に設定してください。",
                "設定エラー",
                wx.OK | wx.ICON_WARNING
            )
            self.fetch_count_spin.SetValue(1)
            value = 1
        elif value > 100:
            wx.MessageBox(
                "投稿の取得件数は100以下に設定してください。",
                "設定エラー",
                wx.OK | wx.ICON_WARNING
            )
            self.fetch_count_spin.SetValue(100)
            value = 100
        
        # キャッシュに値を保存
        self.settings_cache['timeline']['fetch_count'] = value
        logger.debug(f"投稿の取得件数を変更しました: {value}件")
    
    def on_interval_changed(self, event):
        """自動取得の間隔が変更されたときの処理
        
        Args:
            event: スピンコントロールイベント
        """
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
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
        # ダイアログが破棄中の場合は何もしない
        if self.is_being_destroyed:
            return
            
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
            fetch_count = self.settings_cache['timeline']['fetch_count']
            auto_fetch = self.settings_cache['timeline']['auto_fetch']
            fetch_interval = self.settings_cache['timeline']['fetch_interval']
            show_completion_dialog = self.settings_cache['post']['show_completion_dialog']
            locale = self.settings_cache['language']['locale']
            enable_debug_log = self.settings_cache['advanced']['enable_debug_log']
            
            # 設定値の詳細をログに出力
            logger.debug(f"保存する設定値: timeline.fetch_count={fetch_count}, timeline.auto_fetch={auto_fetch}, "
                         f"timeline.fetch_interval={fetch_interval}, post.show_completion_dialog={show_completion_dialog}, "
                         f"language.locale={locale}, advanced.enable_debug_log={enable_debug_log}")
            
            # バリデーション
            if fetch_count < 1 or fetch_count > 100:
                logger.warning(f"投稿の取得件数が範囲外です。値: {fetch_count}")
                if fetch_count < 1:
                    fetch_count = 1
                    self.settings_cache['timeline']['fetch_count'] = 1
                elif fetch_count > 100:
                    fetch_count = 100
                    self.settings_cache['timeline']['fetch_count'] = 100
                
            if fetch_interval < 180:
                logger.warning("自動取得の間隔が180秒未満です。180秒に設定します。")
                fetch_interval = 180
                self.settings_cache['timeline']['fetch_interval'] = 180
            
            # 設定値の保存
            logger.debug("設定値をsettings_managerに設定します")
            self.settings_manager.set('timeline.fetch_count', fetch_count)
            self.settings_manager.set('timeline.auto_fetch', auto_fetch)
            self.settings_manager.set('timeline.fetch_interval', fetch_interval)
            self.settings_manager.set('post.show_completion_dialog', show_completion_dialog)
            
            # 言語設定の保存（バリデーション付きで設定）
            success_lang, error_msg = self.settings_manager.set_with_validation('language.locale', locale)
            if not success_lang:
                logger.warning(f"言語設定の保存に失敗しました: {error_msg}")
            
            self.settings_manager.set('advanced.enable_debug_log', enable_debug_log)
            
            # 設定ファイルに保存
            logger.debug(f"設定の保存を試みます: {self.settings_manager.settings_file}")
            success = self.settings_manager.save()
            logger.debug(f"settings_manager.save()の結果: {success}")
            
            if not success:
                error_msg = self.i18n.get_message("settings.messages.save_error")
                logger.error(error_msg)
                wx.MessageBox(
                    error_msg,
                    self.i18n.get_message("settings.messages.save_error_title"),
                    wx.OK | wx.ICON_ERROR
                )
            else:
                logger.debug("設定の保存に成功しました")
            
            return success
        except Exception as e:
            # 例外が発生した場合はログに出力
            logger.error(f"save_settings()で例外が発生しました: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # エラーメッセージを表示
            wx.MessageBox(
                self.i18n.get_message("settings.messages.save_exception", error=str(e)),
                self.i18n.get_message("settings.messages.save_exception_title"),
                wx.OK | wx.ICON_ERROR
            )
            return False
