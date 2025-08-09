@echo off
echo Installing PDF preview dependencies...
echo.

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not installed or not in PATH
    echo Please install Python with pip and try again
    pause
    exit /b 1
)

echo Installing required Python packages...
pip install pdf2image Pillow PyPDF2

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to install Python packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo PDF preview dependencies installed successfully!
echo.

echo Note: For PDF rendering to work properly, you also need:
echo  - A TeX distribution with pdflatex (like MiKTeX or TeX Live)
echo  - poppler-utils for pdf2image (on Windows, it's included)
echo.

pause