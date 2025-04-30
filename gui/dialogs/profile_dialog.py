#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
プロフィールダイアログ
"""

import wx
import logging
import weakref

# ロガーの設定
logger = logging.getLogger(__name__)

class ProfileDialog(wx.Dialog):
    """投稿者プロフィールダイアログ"""
    
    def __init__(self, parent, profile_data):
        """初期化
        
        Args:
            parent: 親ウィンドウ
            profile_data (object): プロフィールデータ
        """
        super(ProfileDialog, self).__init__(
            parent, 
            title=f"{profile_data.display_name or profile_data.handle}のプロフィール",
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.profile_data = profile_data
        
        # 親フレームからクライアントを取得（弱参照を使用）
        self.client = None
        self.parent_ref = weakref.ref(parent)
        frame = wx.GetTopLevelParent(parent)
        if hasattr(frame, 'client'):
            # クライアントへの直接参照を保持（クライアントはシングルトンなので問題ない）
            self.client = frame.client
        
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
        else:
            event.Skip()
        
    def init_ui(self):
        """UIの初期化"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # プロフィール情報の整形
        profile_text = self.format_profile_text()
        
        # プロフィール情報（リードオンリーテキストボックス）
        self.profile_ctrl = wx.TextCtrl(
            panel, 
            value=profile_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.BORDER_SIMPLE
        )
        # フォントとサイズの設定
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.profile_ctrl.SetFont(font)
        # 背景色の設定（システムの背景色に合わせる）
        self.profile_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        main_sizer.Add(self.profile_ctrl, 1, wx.ALL | wx.EXPAND, 10)
        
        # 区切り線
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.ALL, 5)
        
        # ボタンエリア
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # フォローボタン
        self.follow_btn = wx.Button(panel, label="フォロー", size=(100, -1))
        self.follow_btn.Bind(wx.EVT_BUTTON, self.on_follow)
        button_sizer.Add(self.follow_btn, 0, wx.ALL, 5)
        
        # フォロー解除ボタン
        self.unfollow_btn = wx.Button(panel, label="フォロー解除", size=(100, -1))
        self.unfollow_btn.Bind(wx.EVT_BUTTON, self.on_unfollow)
        button_sizer.Add(self.unfollow_btn, 0, wx.ALL, 5)
        
        # ブロックボタン
        self.block_btn = wx.Button(panel, label="ブロック", size=(100, -1))
        self.block_btn.Bind(wx.EVT_BUTTON, self.on_block)
        button_sizer.Add(self.block_btn, 0, wx.ALL, 5)
        
        # ミュートボタン
        self.mute_btn = wx.Button(panel, label="ミュート", size=(100, -1))
        self.mute_btn.Bind(wx.EVT_BUTTON, self.on_mute)
        button_sizer.Add(self.mute_btn, 0, wx.ALL, 5)
        
        # 閉じるボタン
        close_btn = wx.Button(panel, wx.ID_CLOSE, "閉じる")
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        button_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # フォロー状態に応じてボタンの有効/無効を設定
        self.update_follow_buttons()
        
    def format_profile_text(self):
        """プロフィール情報をテキスト形式に整形
        
        Returns:
            str: 整形されたプロフィールテキスト
        """
        profile = self.profile_data
        
        # 基本情報
        text = f"表示名: {profile.display_name or '未設定'}\n"
        text += f"ハンドル: @{profile.handle}\n"
        
        # 説明文
        if hasattr(profile, 'description') and profile.description:
            text += f"\n説明:\n{profile.description}\n"
        
        # フォロワー数・フォロー数
        if hasattr(profile, 'followers_count'):
            text += f"\nフォロワー: {profile.followers_count or 0}\n"
        if hasattr(profile, 'follows_count'):
            text += f"フォロー: {profile.follows_count or 0}\n"
        
        # 投稿数
        if hasattr(profile, 'posts_count'):
            text += f"投稿数: {profile.posts_count or 0}\n"
        
        return text
        
    def update_follow_buttons(self):
        """フォロー状態に応じてボタンの有効/無効を設定"""
        # 自分自身のプロフィールの場合
        if self.client and self.client.profile and self.profile_data.handle == self.client.profile.handle:
            self.follow_btn.Enable(False)
            self.unfollow_btn.Enable(False)
            self.block_btn.Enable(False)
            self.mute_btn.Enable(False)
            return
            
        # フォロー状態を確認
        is_following = False
        if hasattr(self.profile_data, 'viewer') and hasattr(self.profile_data.viewer, 'following'):
            is_following = bool(self.profile_data.viewer.following)
        
        # ブロック状態を確認
        is_blocked = False
        if hasattr(self.profile_data, 'viewer') and hasattr(self.profile_data.viewer, 'blocking'):
            is_blocked = bool(self.profile_data.viewer.blocking)
            
        # ミュート状態を確認
        is_muted = False
        if hasattr(self.profile_data, 'viewer') and hasattr(self.profile_data.viewer, 'muted'):
            is_muted = bool(self.profile_data.viewer.muted)
        
        # ボタンの有効/無効を設定
        self.follow_btn.Enable(not is_following and not is_blocked)
        self.unfollow_btn.Enable(is_following and not is_blocked)
        
        # ブロックボタンのラベルを設定
        if is_blocked:
            self.block_btn.SetLabel("ブロック解除")
        else:
            self.block_btn.SetLabel("ブロック")
            
        # ミュートボタンのラベルを設定
        if is_muted:
            self.mute_btn.SetLabel("ミュート解除")
        else:
            self.mute_btn.SetLabel("ミュート")
        
    def on_follow(self, event):
        """フォローボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("フォローするにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        try:
            # フォロー処理
            handle = self.profile_data.handle
            self.client.follow(handle)
            
            # 成功メッセージ
            wx.MessageBox(f"{self.profile_data.display_name or handle}をフォローしました", 
                         "フォロー完了", wx.OK | wx.ICON_INFORMATION)
            
            # ボタンの状態を更新
            self.follow_btn.Enable(False)
            self.unfollow_btn.Enable(True)
            
        except Exception as e:
            logger.error(f"フォロー処理に失敗しました: {str(e)}")
            wx.MessageBox(f"フォロー処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        
    def on_unfollow(self, event):
        """フォロー解除ボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("フォロー解除するにはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        # 確認ダイアログ
        dlg = wx.MessageDialog(
            self,
            f"{self.profile_data.display_name or self.profile_data.handle}のフォローを解除しますか？",
            "フォロー解除の確認",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                # フォロー解除処理
                handle = self.profile_data.handle
                self.client.unfollow(handle)
                
                # 成功メッセージ
                wx.MessageBox(f"{self.profile_data.display_name or handle}のフォローを解除しました", 
                             "フォロー解除完了", wx.OK | wx.ICON_INFORMATION)
                
                # ボタンの状態を更新
                self.follow_btn.Enable(True)
                self.unfollow_btn.Enable(False)
                
            except Exception as e:
                logger.error(f"フォロー解除処理に失敗しました: {str(e)}")
                wx.MessageBox(f"フォロー解除処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
        
    def on_block(self, event):
        """ブロックボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("ブロック操作にはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        handle = self.profile_data.handle
        display_name = self.profile_data.display_name or handle
        
        # ブロック状態を確認
        is_blocked = False
        if hasattr(self.profile_data, 'viewer') and hasattr(self.profile_data.viewer, 'blocking'):
            is_blocked = bool(self.profile_data.viewer.blocking)
            
        if is_blocked:
            # ブロック解除の確認ダイアログ
            dlg = wx.MessageDialog(
                self,
                f"{display_name}のブロックを解除しますか？",
                "ブロック解除の確認",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if dlg.ShowModal() == wx.ID_YES:
                try:
                    # ブロック解除処理
                    self.client.unblock(handle)
                    
                    # 成功メッセージ
                    wx.MessageBox(f"{display_name}のブロックを解除しました", 
                                 "ブロック解除完了", wx.OK | wx.ICON_INFORMATION)
                    
                    # ブロック状態を更新
                    if hasattr(self.profile_data, 'viewer'):
                        if not hasattr(self.profile_data.viewer, 'blocking'):
                            setattr(self.profile_data.viewer, 'blocking', False)
                        else:
                            self.profile_data.viewer.blocking = False
                    
                    # ボタンの状態を更新
                    self.update_follow_buttons()
                    
                except Exception as e:
                    logger.error(f"ブロック解除処理に失敗しました: {str(e)}")
                    wx.MessageBox(f"ブロック解除処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            
            dlg.Destroy()
        else:
            # ブロックの確認ダイアログ
            dlg = wx.MessageDialog(
                self,
                f"{display_name}をブロックしますか？\n\nブロックすると、相手のコンテンツが表示されなくなり、相手もあなたのコンテンツを見ることができなくなります。",
                "ブロックの確認",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if dlg.ShowModal() == wx.ID_YES:
                try:
                    # ブロック処理
                    self.client.block(handle)
                    
                    # 成功メッセージ
                    wx.MessageBox(f"{display_name}をブロックしました", 
                                 "ブロック完了", wx.OK | wx.ICON_INFORMATION)
                    
                    # ブロック状態を更新
                    if hasattr(self.profile_data, 'viewer'):
                        if not hasattr(self.profile_data.viewer, 'blocking'):
                            setattr(self.profile_data.viewer, 'blocking', True)
                        else:
                            self.profile_data.viewer.blocking = True
                    
                    # ボタンの状態を更新
                    self.update_follow_buttons()
                    
                except Exception as e:
                    logger.error(f"ブロック処理に失敗しました: {str(e)}")
                    wx.MessageBox(f"ブロック処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            
            dlg.Destroy()
    
    def on_mute(self, event):
        """ミュートボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        if not self.client or not self.client.is_logged_in:
            wx.MessageBox("ミュート操作にはログインしてください", "エラー", wx.OK | wx.ICON_ERROR)
            return
            
        handle = self.profile_data.handle
        display_name = self.profile_data.display_name or handle
        
        # ミュート状態を確認
        is_muted = False
        if hasattr(self.profile_data, 'viewer') and hasattr(self.profile_data.viewer, 'muted'):
            is_muted = bool(self.profile_data.viewer.muted)
            
        if is_muted:
            # ミュート解除の確認ダイアログ
            dlg = wx.MessageDialog(
                self,
                f"{display_name}のミュートを解除しますか？",
                "ミュート解除の確認",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if dlg.ShowModal() == wx.ID_YES:
                try:
                    # ミュート解除処理
                    self.client.unmute(handle)
                    
                    # 成功メッセージ
                    wx.MessageBox(f"{display_name}のミュートを解除しました", 
                                 "ミュート解除完了", wx.OK | wx.ICON_INFORMATION)
                    
                    # ミュート状態を更新
                    if hasattr(self.profile_data, 'viewer'):
                        if not hasattr(self.profile_data.viewer, 'muted'):
                            setattr(self.profile_data.viewer, 'muted', False)
                        else:
                            self.profile_data.viewer.muted = False
                    
                    # ボタンの状態を更新
                    self.update_follow_buttons()
                    
                except Exception as e:
                    logger.error(f"ミュート解除処理に失敗しました: {str(e)}")
                    wx.MessageBox(f"ミュート解除処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            
            dlg.Destroy()
        else:
            # ミュートの確認ダイアログ
            dlg = wx.MessageDialog(
                self,
                f"{display_name}をミュートしますか？\n\nミュートすると、相手のコンテンツがタイムラインに表示されなくなります。相手にはミュートされたことは通知されません。",
                "ミュートの確認",
                wx.YES_NO | wx.ICON_QUESTION
            )
            
            if dlg.ShowModal() == wx.ID_YES:
                try:
                    # ミュート処理
                    self.client.mute(handle)
                    
                    # 成功メッセージ
                    wx.MessageBox(f"{display_name}をミュートしました", 
                                 "ミュート完了", wx.OK | wx.ICON_INFORMATION)
                    
                    # ミュート状態を更新
                    if hasattr(self.profile_data, 'viewer'):
                        if not hasattr(self.profile_data.viewer, 'muted'):
                            setattr(self.profile_data.viewer, 'muted', True)
                        else:
                            self.profile_data.viewer.muted = True
                    
                    # ボタンの状態を更新
                    self.update_follow_buttons()
                    
                except Exception as e:
                    logger.error(f"ミュート処理に失敗しました: {str(e)}")
                    wx.MessageBox(f"ミュート処理に失敗しました: {str(e)}", "エラー", wx.OK | wx.ICON_ERROR)
            
            dlg.Destroy()
    
    def on_close(self, event):
        """閉じるボタンクリック時の処理
        
        Args:
            event: ボタンイベント
        """
        self.EndModal(wx.ID_CLOSE)
        
    def Destroy(self):
        """ダイアログ破棄時の処理"""
        # イベントハンドラの解除
        self.Unbind(wx.EVT_CHAR_HOOK)
        
        # ボタンのイベントハンドラを解除
        if hasattr(self, 'follow_btn'):
            self.follow_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'unfollow_btn'):
            self.unfollow_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'block_btn'):
            self.block_btn.Unbind(wx.EVT_BUTTON)
        if hasattr(self, 'mute_btn'):
            self.mute_btn.Unbind(wx.EVT_BUTTON)
            
        # 親への参照をクリア
        self.parent_ref = None
        self.client = None
        
        logger.debug("ProfileDialogのリソースを解放しました")
        return super(ProfileDialog, self).Destroy()
