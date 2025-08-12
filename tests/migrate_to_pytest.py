#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSky - unittest から pytest への移行支援スクリプト
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple

def convert_unittest_to_pytest(content: str) -> str:
    """unittestコードをpytestコードに変換"""
    
    # インポート文の変換
    content = re.sub(
        r'import unittest\n',
        'import pytest\n',
        content
    )
    
    content = re.sub(
        r'from unittest import TestCase\n',
        'import pytest\n',
        content
    )
    
    # TestCaseクラスの継承を削除
    content = re.sub(
        r'class (\w+)\(unittest\.TestCase\):',
        r'class \1:',
        content
    )
    
    # setUp を fixture に変換
    content = re.sub(
        r'def setUp\(self\):',
        '@pytest.fixture(autouse=True)\n    def setup_method(self):',
        content
    )
    
    # tearDown を fixture に変換
    content = re.sub(
        r'def tearDown\(self\):',
        '@pytest.fixture(autouse=True)\n    def teardown_method(self):',
        content
    )
    
    # アサーション変換のマッピング
    assertions = [
        (r'self\.assertEqual\(([^,]+),\s*([^)]+)\)', r'assert \1 == \2'),
        (r'self\.assertNotEqual\(([^,]+),\s*([^)]+)\)', r'assert \1 != \2'),
        (r'self\.assertTrue\(([^)]+)\)', r'assert \1'),
        (r'self\.assertFalse\(([^)]+)\)', r'assert not \1'),
        (r'self\.assertIsNone\(([^)]+)\)', r'assert \1 is None'),
        (r'self\.assertIsNotNone\(([^)]+)\)', r'assert \1 is not None'),
        (r'self\.assertIn\(([^,]+),\s*([^)]+)\)', r'assert \1 in \2'),
        (r'self\.assertNotIn\(([^,]+),\s*([^)]+)\)', r'assert \1 not in \2'),
        (r'self\.assertIs\(([^,]+),\s*([^)]+)\)', r'assert \1 is \2'),
        (r'self\.assertIsNot\(([^,]+),\s*([^)]+)\)', r'assert \1 is not \2'),
        (r'self\.assertGreater\(([^,]+),\s*([^)]+)\)', r'assert \1 > \2'),
        (r'self\.assertGreaterEqual\(([^,]+),\s*([^)]+)\)', r'assert \1 >= \2'),
        (r'self\.assertLess\(([^,]+),\s*([^)]+)\)', r'assert \1 < \2'),
        (r'self\.assertLessEqual\(([^,]+),\s*([^)]+)\)', r'assert \1 <= \2'),
        (r'self\.assertAlmostEqual\(([^,]+),\s*([^,]+),\s*places=(\d+)\)', r'assert round(\1 - \2, \3) == 0'),
        (r'self\.assertAlmostEqual\(([^,]+),\s*([^)]+)\)', r'assert \1 == pytest.approx(\2)'),
        (r'self\.assertIsInstance\(([^,]+),\s*([^)]+)\)', r'assert isinstance(\1, \2)'),
        (r'self\.assertNotIsInstance\(([^,]+),\s*([^)]+)\)', r'assert not isinstance(\1, \2)'),
    ]
    
    for pattern, replacement in assertions:
        content = re.sub(pattern, replacement, content)
    
    # assertRaises を pytest.raises に変換
    content = re.sub(
        r'with self\.assertRaises\(([^)]+)\):',
        r'with pytest.raises(\1):',
        content
    )
    
    content = re.sub(
        r'self\.assertRaises\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'with pytest.raises(\1):\n            \2(\3)',
        content
    )
    
    # subTest を parametrize に変換 (簡単なケースのみ)
    # これは複雑なので、マーカーを残して手動変換を促す
    if 'with self.subTest' in content:
        content = '# TODO: Convert subTest to @pytest.mark.parametrize\n' + content
    
    # unittest.main() を削除
    content = re.sub(
        r'if __name__ == [\'"]__main__[\'"]:\s*\n\s*unittest\.main\([^)]*\)',
        '',
        content
    )
    
    return content


def process_file(file_path: Path) -> bool:
    """ファイルを処理して変換"""
    print(f"処理中: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # unittestを使用しているか確認
        if 'unittest' not in content and 'TestCase' not in content:
            print(f"  → スキップ: unittestを使用していません")
            return False
        
        # 変換実行
        converted = convert_unittest_to_pytest(content)
        
        # 新しいファイル名
        new_file_path = file_path.parent / f"{file_path.stem}_pytest{file_path.suffix}"
        
        # 変換結果を保存
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        
        print(f"  → 変換完了: {new_file_path}")
        return True
        
    except Exception as e:
        print(f"  → エラー: {e}")
        return False


def find_unittest_files(directory: Path) -> List[Path]:
    """unittestを使用しているテストファイルを検索"""
    unittest_files = []
    
    for test_file in directory.rglob("test_*.py"):
        # 既にpytestに変換済みのファイルはスキップ
        if '_pytest' in test_file.name:
            continue
        
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'unittest' in content or 'TestCase' in content:
                    unittest_files.append(test_file)
        except Exception:
            pass
    
    return unittest_files


def main():
    """メイン処理"""
    tests_dir = Path(__file__).parent
    
    print("=" * 70)
    print("unittest → pytest 移行スクリプト")
    print("=" * 70)
    print()
    
    # unittestファイルを検索
    print("unittestを使用しているファイルを検索中...")
    unittest_files = find_unittest_files(tests_dir)
    
    if not unittest_files:
        print("unittestを使用しているファイルが見つかりませんでした。")
        return
    
    print(f"\n{len(unittest_files)}個のファイルが見つかりました:")
    for f in unittest_files:
        print(f"  - {f.relative_to(tests_dir)}")
    
    # 確認
    print("\n変換を実行しますか? [y/N]: ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("キャンセルしました。")
        return
    
    # 変換実行
    print("\n変換を開始します...")
    print("-" * 70)
    
    success_count = 0
    for file_path in unittest_files:
        if process_file(file_path):
            success_count += 1
    
    # 結果表示
    print("-" * 70)
    print(f"\n変換結果: {success_count}/{len(unittest_files)} ファイル成功")
    
    if success_count > 0:
        print("\n次のステップ:")
        print("1. 生成された *_pytest.py ファイルを確認")
        print("2. テストが正常に動作することを確認")
        print("3. 問題なければ元のファイルを置き換え")
        print("4. # TODO: マーカーがある箇所は手動で修正")


if __name__ == "__main__":
    main()