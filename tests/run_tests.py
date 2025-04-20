#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
テスト実行スクリプト
"""

import unittest
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """すべてのテストを実行する"""
    # テストディスカバリーを実行
    test_suite = unittest.defaultTestLoader.discover('tests')
    
    # テスト実行
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # テスト結果の要約を表示
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print("\n" + "=" * 70)
    print(f"テスト結果の要約:")
    print(f"  実行したテスト数: {total_tests}")
    print(f"  成功したテスト数: {successes}")
    print(f"  失敗したテスト数: {failures}")
    print(f"  エラーが発生したテスト数: {errors}")
    print("=" * 70)
    
    # 結果に基づいて終了コード設定
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    print("SSky テストスイートを実行します...")
    sys.exit(run_tests())
