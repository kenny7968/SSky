#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーションイベント定義モジュール
"""

# 認証関連イベント
AUTH_LOGIN_ATTEMPT = "auth.login.attempt" # ログイン試行開始
AUTH_LOGIN_SUCCESS = "auth.login.success" # ログイン成功 (引数: profile)
AUTH_LOGIN_FAILURE = "auth.login.failure" # ログイン失敗 (引数: error)
AUTH_LOGOUT_SUCCESS = "auth.logout.success" # ログアウト成功
AUTH_SESSION_LOAD_ATTEMPT = "auth.session.load.attempt" # セッション読み込み試行
AUTH_SESSION_LOAD_SUCCESS = "auth.session.load.success" # セッション読み込み成功 (引数: profile)
AUTH_SESSION_LOAD_FAILURE = "auth.session.load.failure" # セッション読み込み失敗 (引数: error, optional: needs_relogin=True)
AUTH_SESSION_INVALID = "auth.session.invalid" # セッションが無効になった (引数: error)
AUTH_SESSION_SAVED = "auth.session.saved" # セッションが保存された (引数: did)
AUTH_SESSION_DELETED = "auth.session.deleted" # セッションが削除された (引数: did)

# UI関連イベント (必要に応じて追加)
# UI_UPDATE_STATUS = "ui.update.status" # ステータスバー更新 (引数: message)
# UI_UPDATE_TIMELINE = "ui.update.timeline" # タイムライン更新要求
