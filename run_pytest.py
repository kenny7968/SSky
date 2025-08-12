#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - Blueskyクライアント
pytest ベースのテストランナー
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent
TESTS_DIR = PROJECT_ROOT / "tests"


def run_tests(args):
    """pytestを実行する"""
    
    # デフォルトのpytestコマンド
    cmd = ["python", "-m", "pytest"]
    
    # 引数の処理
    if args.coverage:
        # カバレッジレポート生成
        cmd.extend(["--cov", "--cov-report=html", "--cov-report=term"])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.markers:
        # 特定のマーカーのみ実行
        cmd.extend(["-m", args.markers])
    
    if args.parallel:
        # 並列実行
        cmd.extend(["-n", "auto"])
    
    if args.fast:
        # 前回失敗したテストのみ実行
        cmd.append("--lf")
    
    if args.watch:
        # ファイル監視モード
        cmd = ["python", "-m", "pytest_watch"]
    
    if args.specific:
        # 特定のファイル/ディレクトリを指定
        cmd.append(args.specific)
    else:
        # デフォルトはtestsディレクトリ
        cmd.append(str(TESTS_DIR))
    
    # その他の引数をそのまま渡す
    if args.extra:
        cmd.extend(args.extra)
    
    # コマンド実行
    print(f"実行コマンド: {' '.join(cmd)}")
    print("=" * 70)
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    # 結果サマリー
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ テスト成功！")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ テスト失敗")
        print("=" * 70)
    
    return result.returncode


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="SSky pytest テストランナー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python run_pytest.py                    # 全テスト実行
  python run_pytest.py --coverage          # カバレッジ付き実行
  python run_pytest.py -v                  # 詳細出力
  python run_pytest.py -m unit             # 単体テストのみ
  python run_pytest.py -m "not slow"       # slowマーカー以外
  python run_pytest.py -n auto             # 並列実行
  python run_pytest.py --fast              # 前回失敗したテストのみ
  python run_pytest.py tests/unit          # 特定ディレクトリ
  python run_pytest.py --watch             # ファイル監視モード
        """
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="カバレッジレポートを生成"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細な出力"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="実行するテストマーカー (例: unit, integration, 'not slow')"
    )
    
    parser.add_argument(
        "--parallel", "-n",
        action="store_true",
        help="並列実行 (マルチプロセス)"
    )
    
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="前回失敗したテストのみ実行"
    )
    
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="ファイル監視モード (pytest-watch)"
    )
    
    parser.add_argument(
        "specific",
        nargs="?",
        help="特定のファイルまたはディレクトリ"
    )
    
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="pytestに渡す追加の引数"
    )
    
    args = parser.parse_args()
    
    # pytest実行
    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()