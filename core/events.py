#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
アプリケーションイベント定義モジュール

# イベント引数の小さなクラスを定義することで、将来イベントの型定義や一貫性を向上させることが可能
# 例: class AuthLoginEventArgs: pass  # ログインイベントの引数型
"""

# 認証関連イベント
# ログインイベント
AUTH_LOGIN_ATTEMPT = "auth.login.attempt"        # ログイン試行開始 (引数: なし)
AUTH_LOGIN_SUCCESS = "auth.login.success"        # ログイン成功 (引数: profile)
AUTH_LOGIN_FAILURE = "auth.login.failure"        # ログイン失敗 (引数: error)

# セッションログインイベント
# 注意: AUTH_LOGIN_SUCCESSと同じ引数を持つため、将来的に統合を検討
AUTH_SESSION_LOAD_ATTEMPT = "auth.session.load.attempt"  # セッション読み込み試行 (引数: did)
AUTH_SESSION_LOAD_SUCCESS = "auth.session.load.success"  # セッション読み込み成功 (引数: profile)
AUTH_SESSION_LOAD_FAILURE = "auth.session.load.failure"  # セッション読み込み失敗 (引数: error, needs_relogin=True/False)

# ログアウトイベント
AUTH_LOGOUT_SUCCESS = "auth.logout.success"      # ログアウト成功 (引数: なし)

# セッション管理イベント
AUTH_SESSION_INVALID = "auth.session.invalid"    # セッションが無効になった (引数: error, did)
AUTH_SESSION_SAVED = "auth.session.saved"        # セッションが保存された (引数: did)
AUTH_SESSION_DELETED = "auth.session.deleted"    # セッションが削除された (引数: did)

# 認証状態変更イベント (将来実装予定)
# AUTH_STATE_CHANGED = "auth.state.changed"      # 認証状態変更 (引数: state={'logged_in': bool, 'profile': profile or None})

# UI関連イベント (必要に応じて追加)
# UI_UPDATE_STATUS = "ui.update.status"          # ステータスバー更新 (引数: message)
# UI_UPDATE_TIMELINE = "ui.update.timeline"      # タイムライン更新要求

# 言語・国際化関連イベント
LANGUAGE_CHANGED = "language.changed"          # 言語変更 (引数: new_locale)

# 投稿関連イベント
POST_SUBMIT_START = "post.submit.start"       # 投稿処理開始 (引数: なし)
POST_SUBMIT_SUCCESS = "post.submit.success"    # 投稿成功 (引数: result)
POST_SUBMIT_FAILURE = "post.submit.failure"    # 投稿失敗 (引数: error)

# いいね関連イベント
LIKE_START = "post.like.start"             # いいね処理開始 (引数: uri)
LIKE_SUCCESS = "post.like.success"          # いいね成功 (引数: result, uri)
LIKE_FAILURE = "post.like.failure"          # いいね失敗 (引数: error, uri)

# リポスト関連イベント
REPOST_START = "post.repost.start"         # リポスト処理開始 (引数: uri)
REPOST_SUCCESS = "post.repost.success"      # リポスト成功 (引数: result, uri)
REPOST_FAILURE = "post.repost.failure"      # リポスト失敗 (引数: error, uri)
