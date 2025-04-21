import os
import sys
import shutil
import zipfile
from pathlib import Path
from SCons.Script import Environment, Command, Alias, GetOption

# コマンドライン引数からバージョン番号を取得
AddOption(
    '--release',
    dest='release',
    type='string',
    nargs=1,
    action='store',
    help='バージョン番号を指定します（例：1.0.0）'
)

release = GetOption('release')
if not release:
    print("エラー: バージョン番号を指定してください（例：scons --release=1.0.0）")
    sys.exit(1)

# 環境設定
env = Environment()

# ディレクトリパス
build_dir = 'build'
dist_dir = 'dist'
release_dir = 'release'
package_dir = os.path.join(build_dir, f'SSky-{release}')
zip_file = os.path.join(release_dir, f'SSky-{release}.zip')

# ビルドディレクトリが存在しない場合は作成
if not os.path.exists(build_dir):
    os.makedirs(build_dir)

# リリースディレクトリが存在しない場合は作成
if not os.path.exists(release_dir):
    os.makedirs(release_dir)

# パッケージディレクトリが存在する場合は削除
if os.path.exists(package_dir):
    shutil.rmtree(package_dir)

# パッケージディレクトリを作成
os.makedirs(package_dir)

# PyInstallerでビルドする関数
def build_with_pyinstaller(target, source, env):
    # PyInstallerコマンドを実行
    pyinstaller_cmd = 'pyinstaller --name SSky --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO SSky.py'
    print(f"実行中: {pyinstaller_cmd}")
    ret = os.system(pyinstaller_cmd)
    
    if ret != 0:
        print("エラー: PyInstallerの実行に失敗しました")
        return 1
    
    # distディレクトリが存在するか確認
    if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, 'SSky')):
        print("エラー: PyInstallerのビルド結果が見つかりません")
        return 1
    
    return 0

# ファイルをパッケージディレクトリにコピーする関数
def copy_files_to_package(target, source, env):
    try:
        # SSkyフォルダの内容をコピー
        ssky_dir = os.path.join(dist_dir, 'SSky')
        for item in os.listdir(ssky_dir):
            src_path = os.path.join(ssky_dir, item)
            dst_path = os.path.join(package_dir, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        
        # manualフォルダをコピー
        manual_src = 'manual'
        manual_dst = os.path.join(package_dir, 'manual')
        shutil.copytree(manual_src, manual_dst)
        
        # changelog.mdをコピー
        changelog_src = 'changelog.md'
        changelog_dst = os.path.join(package_dir, 'changelog.md')
        shutil.copy2(changelog_src, changelog_dst)
        
        print(f"パッケージディレクトリの作成が完了しました: {package_dir}")
        return 0
    except Exception as e:
        print(f"エラー: ファイルのコピー中に問題が発生しました: {e}")
        return 1

# zipファイルを作成する関数
def create_zip_package(target, source, env):
    try:
        # zipファイルを作成
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # パッケージディレクトリ内のすべてのファイルを追加
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # zipファイル内のパスを相対パスに変換
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"zipパッケージの作成が完了しました: {zip_file}")
        return 0
    except Exception as e:
        print(f"エラー: zipファイルの作成中に問題が発生しました: {e}")
        return 1

# ビルドコマンドの定義
build_cmd = env.Command('build_exe', None, build_with_pyinstaller)
copy_cmd = env.Command('copy_files', build_cmd, copy_files_to_package)
zip_cmd = env.Command('create_zip', copy_cmd, create_zip_package)

# エイリアスの定義
env.Alias('build', [build_cmd, copy_cmd, zip_cmd])
env.Default('build')

# 完了メッセージを表示する関数
def show_completion_message(target, source, env):
    print(f"\n===== ビルド完了 =====")
    print(f"パッケージディレクトリ: {package_dir}")
    print(f"zipファイル: {zip_file}")
    print(f"バージョン: {release}")
    print(f"====================\n")
    return 0

# 完了メッセージを表示するコマンド
completion_cmd = env.Command('completion', zip_cmd, show_completion_message)
env.Alias('build', completion_cmd)
