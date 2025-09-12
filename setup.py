#!/usr/bin/env python3
"""Noctern LaTeX Editor Setup Script

This script handles the installation and setup of Noctern.
It automatically installs Python dependencies and verifies system requirements.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Version and metadata
NOCTERN_VERSION = "1.0.0"
PYTHON_MIN_VERSION = (3, 8)

def check_python_version():
    """Check if Python version meets requirements."""
    current_version = sys.version_info[:2]
    if current_version < PYTHON_MIN_VERSION:
        print(f"❌ Python {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}+ required. Current: {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    print(f"✅ Python {current_version[0]}.{current_version[1]} detected")

def check_latex_installation():
    """Check if LaTeX is installed and accessible."""
    try:
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ pdflatex found")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  pdflatex not found - LaTeX distribution required")
    return False

def check_chktex_installation():
    """Check if chktex is installed (optional)."""
    try:
        result = subprocess.run(['chktex', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ chktex found (LaTeX linting available)")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("ℹ️  chktex not found (LaTeX linting unavailable)")
    return False

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print("\n📦 Installing Python dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_default_settings():
    """Create default settings.conf if it doesn't exist."""
    settings_file = Path('settings.conf')
    
    if settings_file.exists():
        print("ℹ️  settings.conf already exists")
        return
    
    default_settings = """[Settings]
app_monitor = Default
pdf_monitor = Default
window_state = Normal
theme = sandstone
font_size = 12
editor_font_family = Consolas
treeview_font_family = Segoe UI
treeview_font_size = 10
treeview_row_height = 45
model_completion = gemini/gemini-2.5-flash-lite
model_generation = gemini/gemini-2.5-flash-lite
model_rephrase = gemini/gemini-2.5-flash-lite
model_debug = gemini/gemini-2.5-flash-lite
model_style = gemini/gemini-2.5-flash-lite
model_proofreading = gemini/gemini-2.5-flash
gemini_api_key = 
show_status_bar = True
show_pdf_preview = True

[Session]
open_files = []
"""
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(default_settings)
    
    print("✅ Default settings.conf created")

def create_desktop_shortcut():
    """Create desktop shortcut (Windows only for now)."""
    if platform.system() != "Windows":
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Noctern.lnk")
        target = os.path.join(os.getcwd(), "main.py")
        wDir = os.getcwd()
        icon = os.path.join(os.getcwd(), "resources", "app_icon.ico")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = f'python "{target}"'
        shortcut.WorkingDirectory = wDir
        if os.path.exists(icon):
            shortcut.IconLocation = icon
        shortcut.save()
        
        print("✅ Desktop shortcut created")
        
    except ImportError:
        print("ℹ️  Desktop shortcut creation requires pywin32")
    except Exception as e:
        print(f"⚠️  Could not create desktop shortcut: {e}")

def print_latex_installation_help():
    """Print LaTeX installation instructions for each platform."""
    system = platform.system()
    
    print("\n📝 LaTeX Installation Instructions:")
    print("=" * 50)
    
    if system == "Windows":
        print("Windows:")
        print("  1. Download MiKTeX: https://miktex.org/download")
        print("  2. Run the installer and select 'Install for all users'")
        print("  3. Choose 'Install packages on-the-fly: Yes'")
        print("  4. Restart your terminal after installation")
        
    elif system == "Darwin":  # macOS
        print("macOS:")
        print("  Option 1 - Homebrew:")
        print("    brew install --cask mactex")
        print("  Option 2 - Direct download:")
        print("    Download from: https://www.tug.org/mactex/")
        
    else:  # Linux
        print("Linux:")
        print("  Ubuntu/Debian:")
        print("    sudo apt-get install texlive-full")
        print("  CentOS/RHEL/Fedora:")
        print("    sudo yum install texlive-scheme-full  # or dnf")
        print("  Arch:")
        print("    sudo pacman -S texlive-most texlive-langgerman")

def main():
    """Main setup function."""
    print("🚀 Noctern LaTeX Editor Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check if we're in the right directory
    if not os.path.exists('main.py') or not os.path.exists('requirements.txt'):
        print("❌ Please run this script from the Noctern root directory")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check LaTeX installation
    latex_ok = check_latex_installation()
    check_chktex_installation()
    
    # Create default settings
    create_default_settings()
    
    # Create desktop shortcut (Windows)
    create_desktop_shortcut()
    
    print("\n" + "=" * 50)
    
    if latex_ok:
        print("🎉 Setup completed successfully!")
        print("\nTo start Noctern:")
        print("  python main.py")
        
        # API key reminder
        print("\n💡 Don't forget to:")
        print("  1. Add your Gemini API key in settings.conf")
        print("  2. Or set up Ollama for local LLM support")
        
    else:
        print("⚠️  Setup completed with warnings")
        print("Please install LaTeX before using Noctern.")
        print_latex_installation_help()
        
        print("\nAfter installing LaTeX, you can start Noctern with:")
        print("  python main.py")

if __name__ == "__main__":
    main()