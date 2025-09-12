@echo off
REM Noctern Windows Installation Script
REM This script automatically sets up Noctern on Windows systems

title Noctern Installation - Windows

echo.
echo ========================================================
echo  Noctern LaTeX Editor - Windows Installation
echo ========================================================
echo.

REM Check for administrative privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator
    echo Some features like MiKTeX installation may require elevation
    echo.
)

REM Check Python installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ first
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python 3.8+ required
    pause
    exit /b 1
)

echo [OK] Python found

REM Check if MiKTeX is installed
echo [2/6] Checking LaTeX installation...
pdflatex --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] MiKTeX not found
    echo.
    set /p install_miktex="Would you like to download and install MiKTeX? (y/N): "
    if /i "%install_miktex%"=="y" (
        echo Downloading MiKTeX installer...
        powershell -Command "Invoke-WebRequest -Uri 'https://miktex.org/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-23.10-x64.exe' -OutFile 'miktex-installer.exe'"
        if exist "miktex-installer.exe" (
            echo Starting MiKTeX installation...
            echo Please follow the installer instructions and restart this script after installation
            start /wait miktex-installer.exe
            del "miktex-installer.exe" >nul 2>&1
            echo.
            echo MiKTeX installation completed. Please restart this script.
            pause
            exit /b 0
        ) else (
            echo [ERROR] Failed to download MiKTeX installer
            echo Please install MiKTeX manually from https://miktex.org/download
        )
    ) else (
        echo Continuing without MiKTeX - you'll need to install it manually
    )
) else (
    echo [OK] LaTeX found
)

REM Install Python dependencies
echo [3/6] Installing Python dependencies...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo Make sure you're in the Noctern directory
    pause
    exit /b 1
)

echo [OK] Dependencies installed

REM Create desktop shortcut
echo [4/6] Creating desktop shortcut...
set "desktop=%USERPROFILE%\Desktop"
set "shortcut=%desktop%\Noctern.lnk"
set "target=%CD%\main.py"
set "icon=%CD%\resources\app_icon.ico"

powershell -Command "$WScript = New-Object -ComObject WScript.Shell; $Shortcut = $WScript.CreateShortcut('%shortcut%'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '\"%target%\"'; $Shortcut.WorkingDirectory = '%CD%'; if (Test-Path '%icon%') { $Shortcut.IconLocation = '%icon%' }; $Shortcut.Save()"

if exist "%shortcut%" (
    echo [OK] Desktop shortcut created
) else (
    echo [WARNING] Could not create desktop shortcut
)

REM Create Start Menu entry
echo [5/6] Creating Start Menu entry...
set "startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "startshortcut=%startmenu%\Noctern.lnk"

powershell -Command "$WScript = New-Object -ComObject WScript.Shell; $Shortcut = $WScript.CreateShortcut('%startshortcut%'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '\"%target%\"'; $Shortcut.WorkingDirectory = '%CD%'; if (Test-Path '%icon%') { $Shortcut.IconLocation = '%icon%' }; $Shortcut.Save()"

if exist "%startshortcut%" (
    echo [OK] Start Menu entry created
) else (
    echo [WARNING] Could not create Start Menu entry
)

REM Final setup
echo [6/6] Final setup...
python setup.py
if %errorLevel% neq 0 (
    echo [ERROR] Setup script failed
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  Installation completed successfully!
echo ========================================================
echo.
echo Noctern has been installed. You can now:
echo.
echo  1. Run from desktop shortcut
echo  2. Run from Start Menu
echo  3. Run from command line: python main.py
echo.
echo Important notes:
echo  - Add your Gemini API key in settings.conf for LLM features
echo  - Or install Ollama for local LLM support
echo  - Make sure MiKTeX is properly installed for LaTeX compilation
echo.
set /p launch="Would you like to launch Noctern now? (y/N): "
if /i "%launch%"=="y" (
    echo Launching Noctern...
    start python main.py
)

echo.
echo Thank you for installing Noctern!
pause