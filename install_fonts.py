#!/usr/bin/env python3
"""
Script to automatically download and install coding fonts for AutomaTeX.
Downloads Fira Code, JetBrains Mono, Cascadia Code, and Iosevka.
"""

import os
import sys
import urllib.request
import zipfile
import shutil
import tempfile
import subprocess
from pathlib import Path

# Font download URLs
FONTS = {
    "Fira Code": {
        "url": "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip",
        "folder": "ttf"
    },
    "JetBrains Mono": {
        "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
        "folder": "fonts/ttf"
    },
    "Cascadia Code": {
        "url": "https://github.com/microsoft/cascadia-code/releases/download/v2111.01/CascadiaCode-2111.01.zip",
        "folder": "ttf"
    },
    "Iosevka": {
        "url": "https://github.com/be5invis/Iosevka/releases/download/v29.0.4/PkgTTC-Iosevka-29.0.4.zip",
        "folder": ""
    }
}

def download_file(url, filename):
    """Download file with progress indication."""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract ZIP file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False

def install_font_windows(font_path):
    """Install font on Windows using multiple methods."""
    font_name = os.path.basename(font_path)
    print(f"  Installing {font_name}...")
    
    # Method 1: PowerShell Add-Type method (most reliable)
    try:
        ps_command = f"""
        Add-Type -AssemblyName System.Drawing
        $fontCollection = New-Object System.Drawing.Text.PrivateFontCollection
        $fontCollection.AddFontFile("{font_path}")
        $fontFamily = $fontCollection.Families[0]
        $fontName = $fontFamily.Name
        
        $FONTS = 0x14
        $objShell = New-Object -ComObject Shell.Application
        $objFolder = $objShell.Namespace($FONTS)
        $objFolder.CopyHere("{font_path}")
        
        Write-Host "Installed: $fontName"
        """
        
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if result.returncode == 0:
            print(f"    [OK] Installed via PowerShell Shell.Application")
            return True
        else:
            print(f"    [!] PowerShell method failed: {result.stderr.strip()}")
            
    except Exception as e:
        print(f"    [!] PowerShell method error: {e}")
    
    # Method 2: Direct copy to Fonts folder + registry
    try:
        fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
        dest_path = os.path.join(fonts_dir, font_name)
        
        # Copy font file
        shutil.copy2(font_path, dest_path)
        print(f"    [OK] Copied to {dest_path}")
        
        # Add to registry
        import winreg
        font_display_name = os.path.splitext(font_name)[0] + " (TrueType)"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                           0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, font_display_name, 0, winreg.REG_SZ, font_name)
        
        print(f"    [OK] Added to registry as '{font_display_name}'")
        return True
        
    except PermissionError:
        print(f"    [!] Permission denied - run as administrator")
        return False
    except Exception as e:
        print(f"    [!] Registry method error: {e}")
    
    # Method 3: User fonts folder (fallback)
    try:
        user_fonts_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Microsoft", "Windows", "Fonts")
        os.makedirs(user_fonts_dir, exist_ok=True)
        
        dest_path = os.path.join(user_fonts_dir, font_name)
        shutil.copy2(font_path, dest_path)
        
        # Add to user registry
        import winreg
        font_display_name = os.path.splitext(font_name)[0] + " (TrueType)"
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                           0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, font_display_name, 0, winreg.REG_SZ, font_name)
        
        print(f"    [OK] Installed to user fonts folder")
        return True
        
    except Exception as e:
        print(f"    [!] User fonts method error: {e}")
    
    print(f"    [FAIL] All installation methods failed for {font_name}")
    return False

def find_font_files(directory, extensions=['.ttf', '.otf', '.ttc']):
    """Find font files in directory."""
    font_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                font_files.append(os.path.join(root, file))
    return font_files

def verify_font_installation():
    """Verify that fonts are properly installed and available in Tkinter."""
    try:
        import tkinter as tk
        import tkinter.font as tkFont
        
        root = tk.Tk()
        root.withdraw()
        
        target_fonts = ["Fira Code", "JetBrains Mono", "Cascadia Code", "Iosevka"]
        installed_fonts = []
        
        print("\n" + "=" * 40)
        print("VERIFICATION: Checking installed fonts...")
        print("=" * 40)
        
        for font_name in target_fonts:
            try:
                test_font = tkFont.Font(family=font_name, size=12)
                actual_family = test_font.actual()['family']
                
                if actual_family.lower() == font_name.lower():
                    print(f"[OK] {font_name}: AVAILABLE")
                    installed_fonts.append(font_name)
                else:
                    print(f"[FAIL] {font_name}: NOT AVAILABLE (fallback: {actual_family})")
                    
            except Exception as e:
                print(f"[ERROR] {font_name}: ERROR ({e})")
        
        root.destroy()
        
        print(f"\nSuccessfully installed: {len(installed_fonts)}/{len(target_fonts)} fonts")
        
        if installed_fonts:
            print("\nFonts ready for AutomaTeX:")
            for font in installed_fonts:
                print(f"  - {font}")
        
        if len(installed_fonts) < len(target_fonts):
            print("\nTroubleshooting:")
            print("- Try running as Administrator")
            print("- Restart your computer")
            print("- Check Windows Fonts folder manually")
            
        return installed_fonts
        
    except ImportError:
        print("Cannot verify fonts - Tkinter not available")
        return []
    except Exception as e:
        print(f"Verification error: {e}")
        return []

def main():
    """Main installation function."""
    print("AutomaTeX Font Installer")
    print("=" * 40)
    print("This script will download and install coding fonts:")
    print("- Fira Code")
    print("- JetBrains Mono") 
    print("- Cascadia Code")
    print("- Iosevka")
    print()
    
    # Check if running as administrator
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("WARNING: Not running as administrator.")
            print("Some fonts may not install properly.")
            print("Consider running as administrator for best results.")
            print()
    except:
        pass
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Working directory: {temp_dir}")
        
        installed_count = 0
        total_fonts = len(FONTS)
        
        for font_name, font_info in FONTS.items():
            print(f"\n--- Installing {font_name} ---")
            
            # Download
            zip_filename = os.path.join(temp_dir, f"{font_name.replace(' ', '_')}.zip")
            if not download_file(font_info["url"], zip_filename):
                print(f"Failed to download {font_name}")
                continue
            
            # Extract
            extract_dir = os.path.join(temp_dir, font_name.replace(' ', '_'))
            os.makedirs(extract_dir, exist_ok=True)
            
            if not extract_zip(zip_filename, extract_dir):
                print(f"Failed to extract {font_name}")
                continue
            
            # Find font files
            if font_info["folder"]:
                font_search_dir = os.path.join(extract_dir, font_info["folder"])
            else:
                font_search_dir = extract_dir
                
            font_files = find_font_files(font_search_dir)
            
            if not font_files:
                print(f"No font files found for {font_name}")
                continue
            
            # Install fonts
            print(f"Found {len(font_files)} font files")
            font_installed = False
            
            for font_file in font_files:
                print(f"Installing {os.path.basename(font_file)}...")
                if install_font_windows(font_file):
                    font_installed = True
                else:
                    print(f"Failed to install {os.path.basename(font_file)}")
            
            if font_installed:
                print(f"[SUCCESS] {font_name} installed successfully")
                installed_count += 1
            else:
                print(f"[FAILED] Failed to install {font_name}")
            
            # Clean up ZIP file
            try:
                os.remove(zip_filename)
            except:
                pass
    
    print(f"\n" + "=" * 40)
    print(f"Installation complete!")
    print(f"Processed {installed_count}/{total_fonts} fonts")
    
    # Verify installation
    verified_fonts = verify_font_installation()
    
    if verified_fonts:
        print(f"\nSUCCESS! {len(verified_fonts)} fonts are now available in AutomaTeX.")
        print("You can now select these fonts in Settings -> Display Settings -> Editor Font")
    else:
        print("\nNo fonts were successfully installed.")
        print("Try running this script as Administrator or install fonts manually.")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)