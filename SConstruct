# SConstruct
# To build app with pyinstaller and make zip archive, including manual, changelog.

import os
import sys
import shutil
from SCons.Script import *

# --- ヘルパー関数 (ファイル操作) ---
def ensure_dir_exists(dir_path):
    """ディレクトリが存在しない場合は作成する"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")
    return dir_path

def remove_if_exists(path):
    """ファイルまたはディレクトリが存在する場合は削除する"""
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Removed directory: {path}")
        else:
            os.remove(path)
            print(f"Removed file: {path}")
    return True

def copy_directory_contents(src_dir, dst_dir):
    """ディレクトリの内容をコピーする"""
    ensure_dir_exists(dst_dir)
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    return True

# --- カスタムアクション ---
def prepare_staging_action(target, source, env):
    """ステージングディレクトリを準備する"""
    staging_dir = os.path.dirname(str(target[0]))
    app_dir = os.path.join(staging_dir, env['APP_NAME'])
    
    # 既存のディレクトリを削除
    remove_if_exists(staging_dir)
    
    # 新しいディレクトリを作成
    ensure_dir_exists(app_dir)
    
    # マーカーファイルを作成
    with open(str(target[0]), 'w') as f:
        f.write('Staging directory prepared')
    
    return 0

def copy_app_files_action(target, source, env):
    """アプリケーションファイルをコピーする"""
    target_dir = os.path.dirname(str(target[0]))
    source_dir = str(source[0])
    
    try:
        copy_directory_contents(source_dir, target_dir)
        
        # マーカーファイルを作成
        with open(str(target[0]), 'w') as f:
            f.write('Application files copied')
    except Exception as e:
        print(f"Error copying application files: {e}")
        return 1
    
    return 0

def copy_manual_action(target, source, env):
    """マニュアルディレクトリをコピーする"""
    target_dir = os.path.dirname(str(target[0]))
    source_dir = str(source[0])
    
    try:
        ensure_dir_exists(target_dir)
        copy_directory_contents(source_dir, target_dir)
        
        # マーカーファイルを作成
        with open(str(target[0]), 'w') as f:
            f.write('Manual files copied')
    except Exception as e:
        print(f"Error copying manual files: {e}")
        return 1
    
    return 0

def create_zip_action(target, source, env):
    """ZIPアーカイブを作成する"""
    target_file = str(target[0])
    source_dir = str(source[0])
    base_name = os.path.splitext(target_file)[0]
    
    try:
        # 出力ディレクトリを確保
        ensure_dir_exists(os.path.dirname(target_file))
        
        # 既存ZIPがあれば削除
        remove_if_exists(target_file)
        
        # アーカイブ作成
        shutil.make_archive(base_name=base_name, format='zip', root_dir=source_dir)
        print(f"Created ZIP archive: {target_file}")
    except Exception as e:
        print(f"Error creating ZIP archive: {e}")
        return 1
    
    return 0

def cleanup_staging_action(target, source, env):
    """ステージングディレクトリを削除する"""
    # source[0]の代わりに直接staging_dirを使用
    staging_dir = 'staging'  # ハードコードされた値を使用
    
    try:
        remove_if_exists(staging_dir)
        print(f"Successfully removed staging directory: {staging_dir}")
    except Exception as e:
        print(f"Error removing staging directory: {e}")
        return 1
    
    return 0

# --- メイン処理 ---

# .env.localファイルが存在する場合は読み込む（オプション）
try:
    from dotenv import load_dotenv
    if os.path.exists('.env.local'):
        load_dotenv('.env.local')
        print("Loaded environment variables from .env.local")
except ImportError:
    print("python-dotenv not installed, skipping .env.local")

# コマンドラインオプション定義
AddOption('--release', dest='release', type='string', nargs=1, action='store',
          metavar='REL', help='Release version string (e.g., 1.0.0 or dev20250421)')

# 環境設定
env = Environment(ENV=os.environ.copy())
release = GetOption('release')

# リリースバージョン指定がない場合はエラー終了
if not release:
    print("Error: Release version not specified.")
    print("Usage: scons --release=<your_version>")
    Exit(1)

print(f"--- Building Release: {release} ---")

# 基本設定
app_name = 'SSky'
env['APP_NAME'] = app_name  # 環境変数に追加
main_script = f'{app_name}.py'
main_script_abs_path = os.path.abspath(main_script)
manual_source_dir = 'manual'
changelog_file = 'changelog.md'

# ディレクトリ設定
dist_dir = 'dist'
pyinstaller_output_dir = os.path.join(dist_dir, app_name)
staging_dir = 'staging'
staging_app_dir = os.path.join(staging_dir, app_name)
release_dir = 'release'
zip_filename = os.path.join(release_dir, f'{app_name}-{release}.zip')

# アクションオブジェクト作成
PrepareStaging = Action(prepare_staging_action, "Preparing staging directory")
CopyAppFiles = Action(copy_app_files_action, "Copying application files")
CopyManual = Action(copy_manual_action, "Copying manual files")
CreateZip = Action(create_zip_action, "Creating ZIP archive")
CleanupStaging = Action(cleanup_staging_action, "Cleaning up staging directory")

# 前提条件チェック
if not os.path.isdir(manual_source_dir):
    print(f"Error: Manual directory '{manual_source_dir}' not found. Aborting build.")
    Exit(1)

if not os.path.exists(changelog_file):
    print(f"Error: changelog.md file '{changelog_file}' not found. Aborting build.")
    Exit(1)

# 1. PyInstaller実行
pyinstaller_marker = os.path.join(dist_dir, f'{app_name}.marker')
pyinstaller_cmd = f'pyinstaller --name {app_name} --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO {main_script_abs_path}'
built_app = env.Command(
    target=pyinstaller_marker,
    source=main_script,
    action=pyinstaller_cmd
)

# 2. ステージングディレクトリ準備
staging_prepared = env.Command(
    target=os.path.join(staging_dir, '.prepared'),
    source=[],
    action=PrepareStaging
)

# 3. アプリケーションファイルコピー
app_copied = env.Command(
    target=os.path.join(staging_app_dir, '.app_copied'),
    source=Dir(pyinstaller_output_dir),
    action=CopyAppFiles
)
Depends(app_copied, [staging_prepared, built_app])

# 4. マニュアルコピー
manual_target = os.path.join(staging_app_dir, 'manual')
manual_copied = env.Command(
    target=os.path.join(manual_target, '.manual_copied'),
    source=Dir(manual_source_dir),
    action=CopyManual
)
Depends(manual_copied, staging_prepared)

# 5. changelog.mdコピー
changelog_target = os.path.join(staging_app_dir, 'changelog.md')
changelog_copied = env.Command(
    target=changelog_target,
    source=changelog_file,
    action=Copy('$TARGET', '$SOURCE')
)
Depends(changelog_copied, staging_prepared)

# 6. ZIPアーカイブ作成
zip_file = env.Command(
    target=zip_filename,
    source=Dir(staging_dir),
    action=CreateZip
)
Depends(zip_file, [app_copied, manual_copied, changelog_copied])

# デフォルトターゲット設定
Default(zip_file)

# 注意: クリーンアップは循環参照を避けるためにデフォルトターゲットから除外
# 必要に応じて手動で実行: scons --release=<version> staging/.cleanup
cleanup = env.Command(
    target=os.path.join(staging_dir, '.cleanup'),
    source=[],  # 空のソースリストを使用して循環参照を避ける
    action=CleanupStaging
)

# クリーンアップターゲット
Clean([zip_file], [Dir('build'), Dir('dist'), Dir(staging_dir), Dir(release_dir)])

print("--- SConstruct processing finished ---")
print(f"To build, run: scons --release={release}")
print("To clean, run: scons -c")
