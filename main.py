#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
メインエントリーポイント
"""

import wx
from app import SSkyApp

if __name__ == "__main__":
    app = SSkyApp()
    app.MainLoop()
