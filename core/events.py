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

# 投稿関連イベント
POST_SUBMIT_START = "post.submit.start"  # 投稿処理開始
POST_SUBMIT_SUCCESS = "post.submit.success"  # 投稿成功 (引数: result)
POST_SUBMIT_FAILURE = "post.submit.failure"  # 投稿失敗 (引数: error)

# いいね関連イベント
LIKE_START = "post.like.start"  # いいね処理開始 (引数: uri)
LIKE_SUCCESS = "post.like.success"  # いいね成功 (引数: result, uri)
LIKE_FAILURE = "post.like.failure"  # いいね失敗 (引数: error, uri)

# リポスト関連イベント
REPOST_START = "post.repost.start"  # リポスト処理開始 (引数: uri)
REPOST_SUCCESS = "post.repost.success"  # リポスト成功 (引数: result, uri)
REPOST_FAILURE = "post.repost.failure"  # リポスト失敗 (引数: error, uri)
