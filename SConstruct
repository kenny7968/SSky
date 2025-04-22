# -*- coding: utf-8 -*-

import os
import sys
import shutil
import zipfile
from pathlib import Path
from SCons.Script import Environment, Command, Alias, GetOption

# Get version number from command line arguments
AddOption(
    '--release',
    dest='release',
    type='string',
    nargs=1,
    action='store',
    help='Specify version number (e.g.: 1.0.0)'
)

release = GetOption('release')
if not release:
    release = "dev"
    print("No release version specified, using default: dev")

# Environment setup
env = Environment()

# Directory paths
build_dir = 'build'
dist_dir = 'dist'
release_dir = 'release'
package_dir = os.path.join(build_dir, f'SSky-{release}')
zip_file = os.path.join(release_dir, f'SSky-{release}.zip')

# Create build directory if it doesn't exist
if not os.path.exists(build_dir):
    os.makedirs(build_dir)

# Create release directory if it doesn't exist
if not os.path.exists(release_dir):
    os.makedirs(release_dir)

# Remove package directory if it exists
if os.path.exists(package_dir):
    shutil.rmtree(package_dir)

# Create package directory
os.makedirs(package_dir)

# Function to build with PyInstaller
def build_with_pyinstaller(target, source, env):
    # Execute PyInstaller command
    pyinstaller_cmd = 'pyinstaller --name SSky --noconsole --onedir --noupx --clean --noconfirm --log-level=INFO SSky.py'
    print(f"Executing: {pyinstaller_cmd}")
    ret = os.system(pyinstaller_cmd)
    
    if ret != 0:
        print("Error: PyInstaller execution failed")
        return 1
    
    # Check if dist directory exists
    if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, 'SSky')):
        print("Error: PyInstaller build output not found")
        return 1
    
    return 0

# Function to copy files to package directory
def copy_files_to_package(target, source, env):
    try:
        # Copy contents of SSky folder
        ssky_dir = os.path.join(dist_dir, 'SSky')
        for item in os.listdir(ssky_dir):
            src_path = os.path.join(ssky_dir, item)
            dst_path = os.path.join(package_dir, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        
        # Copy manual folder
        manual_src = 'manual'
        manual_dst = os.path.join(package_dir, 'manual')
        shutil.copytree(manual_src, manual_dst)
        
        # Copy changelog.md
        changelog_src = 'changelog.md'
        changelog_dst = os.path.join(package_dir, 'changelog.md')
        shutil.copy2(changelog_src, changelog_dst)
        
        print(f"Package directory creation completed: {package_dir}")
        return 0
    except Exception as e:
        print(f"Error: Problem occurred while copying files: {e}")
        return 1

# Function to create zip package
def create_zip_package(target, source, env):
    try:
        # Create zip file
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files in the package directory
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Convert path in zip file to relative path
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Zip package creation completed: {zip_file}")
        return 0
    except Exception as e:
        print(f"Error: Problem occurred while creating zip file: {e}")
        return 1

# Build command definition
build_cmd = env.Command('build_exe', None, build_with_pyinstaller)
copy_cmd = env.Command('copy_files', build_cmd, copy_files_to_package)
zip_cmd = env.Command('create_zip', copy_cmd, create_zip_package)

# Alias definition
env.Alias('build', [build_cmd, copy_cmd, zip_cmd])
env.Default('build')

# Function to display completion message
def show_completion_message(target, source, env):
    print(f"\n===== Build Completed =====")
    print(f"Package directory: {package_dir}")
    print(f"Zip file: {zip_file}")
    print(f"Version: {release}")
    print(f"====================\n")
    return 0

# Command to display completion message
completion_cmd = env.Command('completion', zip_cmd, show_completion_message)
env.Alias('build', completion_cmd)
