#!/usr/bin/env python3
"""
Noctern Release Automation Script
Automates the process of creating releases with executables, documentation, and distribution packages.
"""

import os
import sys
import json
import shutil
import zipfile
import tarfile
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Release configuration
VERSION = "1.0.0"
RELEASE_NAME = f"Noctern-v{VERSION}"
SUPPORTED_PLATFORMS = ["windows", "macos", "linux"]

def get_git_info():
    """Get current git information."""
    try:
        # Get current commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            text=True
        ).strip()[:8]
        
        # Get current branch
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            text=True
        ).strip()
        
        # Check if working directory is clean
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'], 
            text=True
        ).strip()
        
        is_clean = len(status) == 0
        
        return {
            'commit': commit_hash,
            'branch': branch,
            'clean': is_clean
        }
    except subprocess.CalledProcessError:
        return None

def check_prerequisites():
    """Check if all prerequisites are met for release creation."""
    print("🔍 Checking prerequisites...")
    
    # Check if we're in the right directory
    if not os.path.exists('main.py') or not os.path.exists('requirements.txt'):
        print("❌ Please run this script from the Noctern root directory")
        return False
    
    # Check git status
    git_info = get_git_info()
    if not git_info:
        print("⚠️  Not in a git repository")
    elif not git_info['clean']:
        print("⚠️  Working directory has uncommitted changes")
        response = input("Continue anyway? (y/N): ")
        if not response.lower().startswith('y'):
            return False
    else:
        print(f"✅ Git status clean (branch: {git_info['branch']}, commit: {git_info['commit']})")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if deployment scripts exist
    required_files = [
        'deployment/scripts/install_windows.bat',
        'deployment/scripts/install_macos.sh',
        'deployment/scripts/install_linux.sh',
        'deployment/build/build_executable.py',
        'setup.py'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        return False
    
    print("✅ All required files present")
    return True

def create_source_package():
    """Create source code package."""
    print("📦 Creating source package...")
    
    # Files to exclude from source package
    exclude_patterns = [
        '__pycache__',
        '*.pyc', 
        '*.pyo',
        '.git',
        '.pytest_cache',
        'build',
        'dist',
        'app_logs',
        'latex_debug_system',
        '.vscode',
        '.claude',
        'settings.conf',  # User-specific
        '*.log'
    ]
    
    def should_exclude(path):
        for pattern in exclude_patterns:
            if pattern in path or path.endswith(pattern.replace('*', '')):
                return True
        return False
    
    # Create source archive
    source_dir = f"releases/{RELEASE_NAME}-source"
    os.makedirs(source_dir, exist_ok=True)
    
    # Copy files
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        
        for file in files:
            src_path = os.path.join(root, file)
            if not should_exclude(src_path):
                rel_path = os.path.relpath(src_path, '.')
                dst_path = os.path.join(source_dir, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
    
    # Create source archive
    archive_path = f"releases/{RELEASE_NAME}-source.zip"
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arc_path)
    
    # Clean up temporary directory
    shutil.rmtree(source_dir)
    
    print(f"✅ Source package created: {archive_path}")
    return archive_path

def build_executables():
    """Build executables for all supported platforms."""
    print("🔨 Building executables...")
    
    # Only build for current platform in this implementation
    # Cross-compilation would require platform-specific environments
    
    try:
        # Run the build script
        result = subprocess.run([
            sys.executable, 
            'deployment/build/build_executable.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Executable built successfully")
            return True
        else:
            print("❌ Executable build failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_installer_packages():
    """Create installer packages for each platform."""
    print("📦 Creating installer packages...")
    
    packages = []
    
    # Windows package
    if os.path.exists('dist/Noctern.exe'):
        win_dir = f"releases/{RELEASE_NAME}-windows"
        os.makedirs(win_dir, exist_ok=True)
        
        # Copy executable
        shutil.copy('dist/Noctern.exe', win_dir)
        
        # Copy installer script
        shutil.copy('deployment/scripts/install_windows.bat', win_dir)
        
        # Copy documentation
        shutil.copy('README.md', win_dir)
        shutil.copy('LICENSE', win_dir)
        
        # Create archive
        win_zip = f"releases/{RELEASE_NAME}-windows.zip"
        with zipfile.ZipFile(win_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(win_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, win_dir)
                    zf.write(file_path, arc_path)
        
        shutil.rmtree(win_dir)
        packages.append(win_zip)
        print(f"✅ Windows package: {win_zip}")
    
    # macOS package (if executable exists)
    if os.path.exists('dist/Noctern'):
        mac_dir = f"releases/{RELEASE_NAME}-macos"
        os.makedirs(mac_dir, exist_ok=True)
        
        # Copy executable
        shutil.copy('dist/Noctern', mac_dir)
        
        # Copy installer script
        shutil.copy('deployment/scripts/install_macos.sh', mac_dir)
        
        # Copy documentation
        shutil.copy('README.md', mac_dir)
        shutil.copy('LICENSE', mac_dir)
        
        # Create tarball (more common on Unix systems)
        mac_tar = f"releases/{RELEASE_NAME}-macos.tar.gz"
        with tarfile.open(mac_tar, 'w:gz') as tf:
            for root, dirs, files in os.walk(mac_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, mac_dir)
                    tf.add(file_path, arcname=arc_path)
        
        shutil.rmtree(mac_dir)
        packages.append(mac_tar)
        print(f"✅ macOS package: {mac_tar}")
    
    # Linux package (if executable exists)
    if os.path.exists('dist/Noctern'):
        linux_dir = f"releases/{RELEASE_NAME}-linux"
        os.makedirs(linux_dir, exist_ok=True)
        
        # Copy executable
        shutil.copy('dist/Noctern', linux_dir)
        
        # Copy installer script  
        shutil.copy('deployment/scripts/install_linux.sh', linux_dir)
        
        # Copy documentation
        shutil.copy('README.md', linux_dir)
        shutil.copy('LICENSE', linux_dir)
        
        # Create tarball
        linux_tar = f"releases/{RELEASE_NAME}-linux.tar.gz"
        with tarfile.open(linux_tar, 'w:gz') as tf:
            for root, dirs, files in os.walk(linux_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, linux_dir)
                    tf.add(file_path, arcname=arc_path)
        
        shutil.rmtree(linux_dir)
        packages.append(linux_tar)
        print(f"✅ Linux package: {linux_tar}")
    
    return packages

def create_release_notes():
    """Create release notes."""
    print("📝 Creating release notes...")
    
    # Read changelog if it exists
    changelog_content = ""
    if os.path.exists('CHANGELOG.md'):
        with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
            changelog_content = f.read()
    
    # Get git info
    git_info = get_git_info()
    
    # Create release notes
    release_notes = f"""# Noctern v{VERSION} Release

## What's New

{f"See CHANGELOG.md for detailed changes." if changelog_content else "This is the initial release of Noctern LaTeX Editor."}

## Features

- **LaTeX Editor**: Full-featured LaTeX editor with syntax highlighting
- **LLM Integration**: AI-powered text completion, generation, and proofreading
- **Live PDF Preview**: Real-time PDF compilation and preview
- **Multi-Platform**: Windows, macOS, and Linux support
- **Local & Cloud LLMs**: Support for both Gemini API and local Ollama models

## Installation

### Quick Install (Recommended)

**Windows:**
```bash
# Download and extract Noctern-v{VERSION}-windows.zip
# Run install_windows.bat as Administrator
```

**macOS:**
```bash  
# Download and extract Noctern-v{VERSION}-macos.tar.gz
chmod +x install_macos.sh
./install_macos.sh
```

**Linux:**
```bash
# Download and extract Noctern-v{VERSION}-linux.tar.gz  
chmod +x install_linux.sh
./install_linux.sh
```

### From Source
```bash
# Download Noctern-v{VERSION}-source.zip
# Extract and run:
python setup.py
python main.py
```

## System Requirements

- Python 3.8+ (for source installation)
- LaTeX distribution (MiKTeX/MacTeX/TeX Live)
- 4GB RAM minimum, 8GB recommended
- 2GB disk space

## Configuration

1. **Get Gemini API Key** (recommended):
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Add key to settings.conf: `gemini_api_key = your_key_here`

2. **Or install Ollama** for local models:
   ```bash
   # Install Ollama from ollama.com
   ollama pull mistral
   ```

## Support

- **Documentation**: See deployment/docs/DEPLOYMENT.md
- **Issues**: [GitHub Issues](https://github.com/blavogiez/Noctern/issues)
- **Discussions**: [GitHub Discussions](https://github.com/blavogiez/Noctern/discussions)

## Technical Details

- **Built with**: Python, tkinter/ttkbootstrap
- **LLM APIs**: Google Gemini, Ollama
- **PDF Rendering**: pdf2image, PyPDF2
{f"- **Build**: {git_info['commit']} ({git_info['branch']})" if git_info else ""}
- **Release Date**: {datetime.now().strftime('%Y-%m-%d')}

---

**Thank you for using Noctern! 🚀**
"""
    
    # Write release notes
    notes_file = f"releases/{RELEASE_NAME}-RELEASE_NOTES.md"
    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write(release_notes)
    
    print(f"✅ Release notes: {notes_file}")
    return notes_file

def create_release_manifest():
    """Create a manifest file with all release information."""
    print("📋 Creating release manifest...")
    
    git_info = get_git_info()
    
    manifest = {
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "build_date": datetime.now().isoformat(),
        "git_info": git_info,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "files": []
    }
    
    # List all files in releases directory
    if os.path.exists('releases'):
        for item in os.listdir('releases'):
            item_path = os.path.join('releases', item)
            if os.path.isfile(item_path):
                manifest["files"].append({
                    "name": item,
                    "size": os.path.getsize(item_path),
                    "type": "source" if "source" in item else "binary" if any(p in item for p in SUPPORTED_PLATFORMS) else "documentation"
                })
    
    # Write manifest
    manifest_file = f"releases/{RELEASE_NAME}-manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Manifest: {manifest_file}")
    return manifest_file

def main():
    """Main release creation function."""
    print("🚀 Noctern Release Creator")
    print("=" * 50)
    print(f"Creating release: {RELEASE_NAME}")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create releases directory
    os.makedirs('releases', exist_ok=True)
    
    # Create source package
    try:
        source_package = create_source_package()
    except Exception as e:
        print(f"❌ Failed to create source package: {e}")
        sys.exit(1)
    
    # Build executables
    print()
    executable_built = build_executables()
    
    # Create installer packages
    if executable_built:
        print()
        try:
            packages = create_installer_packages()
        except Exception as e:
            print(f"❌ Failed to create installer packages: {e}")
            packages = []
    else:
        packages = []
        print("⚠️  Skipping installer packages (no executables)")
    
    # Create documentation
    print()
    try:
        release_notes = create_release_notes()
        manifest = create_release_manifest()
    except Exception as e:
        print(f"❌ Failed to create documentation: {e}")
        sys.exit(1)
    
    # Summary
    print()
    print("=" * 50)
    print("🎉 Release created successfully!")
    print()
    print("📁 Release files:")
    
    if os.path.exists('releases'):
        total_size = 0
        for item in sorted(os.listdir('releases')):
            item_path = os.path.join('releases', item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"  📄 {item} ({size_mb:.1f} MB)")
        
        print(f"\n📊 Total size: {total_size / (1024 * 1024):.1f} MB")
    
    print(f"\n📍 Release directory: releases/")
    
    # GitHub release command suggestion
    if get_git_info():
        print(f"\n💡 To create GitHub release:")
        print(f"   gh release create v{VERSION} releases/* --title \"{RELEASE_NAME}\" --notes-file releases/{RELEASE_NAME}-RELEASE_NOTES.md")

if __name__ == "__main__":
    main()