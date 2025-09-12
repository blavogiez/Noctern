#!/bin/bash
# Noctern macOS Installation Script
# This script automatically sets up Noctern on macOS systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================================"
echo " Noctern LaTeX Editor - macOS Installation"
echo "========================================================"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only"
    exit 1
fi

print_info "Detected macOS $(sw_vers -productVersion)"

# Check Python installation
echo "[1/6] Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" &> /dev/null; then
        print_status "Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        echo "Please install Python 3.8+ from https://www.python.org/downloads/"
        exit 1
    fi
elif command -v python &> /dev/null; then
    if python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_status "Python $PYTHON_VERSION found"
        PYTHON_CMD="python"
    else
        print_error "Python 3.8+ required"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.8+"
    echo "Install via:"
    echo "  - Homebrew: brew install python"
    echo "  - Direct: https://www.python.org/downloads/"
    exit 1
fi

# Check if Homebrew is installed
echo "[2/6] Checking Homebrew..."
if command -v brew &> /dev/null; then
    print_status "Homebrew found"
    HOMEBREW_AVAILABLE=true
else
    print_warning "Homebrew not found"
    echo "Homebrew makes LaTeX installation easier."
    read -p "Would you like to install Homebrew? (y/N): " install_brew
    if [[ $install_brew =~ ^[Yy]$ ]]; then
        print_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        HOMEBREW_AVAILABLE=true
        print_status "Homebrew installed"
    else
        HOMEBREW_AVAILABLE=false
    fi
fi

# Check LaTeX installation
echo "[3/6] Checking LaTeX installation..."
if command -v pdflatex &> /dev/null; then
    print_status "LaTeX found ($(pdflatex --version | head -n1 | cut -d' ' -f1-2))"
else
    print_warning "LaTeX not found"
    echo ""
    if [[ $HOMEBREW_AVAILABLE == true ]]; then
        read -p "Would you like to install MacTeX via Homebrew? (y/N): " install_latex
        if [[ $install_latex =~ ^[Yy]$ ]]; then
            print_info "Installing MacTeX (this may take a while)..."
            brew install --cask mactex
            
            # Add TeX Live to PATH
            export PATH="/usr/local/texlive/2023/bin/universal-darwin:$PATH"
            echo 'export PATH="/usr/local/texlive/2023/bin/universal-darwin:$PATH"' >> ~/.zprofile
            
            print_status "MacTeX installed"
        else
            print_warning "Continuing without LaTeX"
            echo "You can install MacTeX later from: https://www.tug.org/mactex/"
        fi
    else
        echo "Please install MacTeX from: https://www.tug.org/mactex/"
        echo "Or install Homebrew first for easier installation"
    fi
fi

# Install Python dependencies
echo "[4/6] Installing Python dependencies..."
if [[ $HOMEBREW_AVAILABLE == true ]] && ! command -v pip3 &> /dev/null; then
    print_info "Installing pip via Homebrew..."
    brew install python
fi

$PYTHON_CMD -m pip install --upgrade pip --user
if ! $PYTHON_CMD -m pip install -r requirements.txt --user; then
    print_error "Failed to install dependencies"
    echo "Make sure you're in the Noctern directory and have write permissions"
    exit 1
fi

print_status "Dependencies installed"

# Create Applications folder shortcut
echo "[5/6] Creating application shortcuts..."

# Create a wrapper script
WRAPPER_SCRIPT="/usr/local/bin/noctern"
if [[ -w "/usr/local/bin" ]] || sudo -n true 2>/dev/null; then
    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
cd "$(dirname "$0")/../../../$(pwd)"
$PYTHON_CMD main.py "\$@"
EOF
    
    if [[ ! -w "/usr/local/bin" ]]; then
        sudo mv "$WRAPPER_SCRIPT" /usr/local/bin/noctern
        sudo chmod +x /usr/local/bin/noctern
    else
        chmod +x "$WRAPPER_SCRIPT"
    fi
    print_status "Command line wrapper created (noctern)"
else
    print_warning "Cannot create command line wrapper (no sudo access)"
fi

# Create .app bundle if osascript is available
if command -v osascript &> /dev/null; then
    APP_DIR="$HOME/Applications/Noctern.app"
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"
    
    # Create Info.plist
    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Noctern</string>
    <key>CFBundleIdentifier</key>
    <string>com.noctern.app</string>
    <key>CFBundleName</key>
    <string>Noctern</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
</dict>
</plist>
EOF
    
    # Create executable script
    cat > "$APP_DIR/Contents/MacOS/Noctern" << EOF
#!/bin/bash
cd "$(pwd)"
$PYTHON_CMD main.py
EOF
    chmod +x "$APP_DIR/Contents/MacOS/Noctern"
    
    # Copy icon if it exists
    if [[ -f "resources/app_icon.png" ]]; then
        cp "resources/app_icon.png" "$APP_DIR/Contents/Resources/icon.png"
    fi
    
    print_status "Application bundle created in ~/Applications"
fi

# Run setup script
echo "[6/6] Running final setup..."
if ! $PYTHON_CMD setup.py; then
    print_error "Setup script failed"
    exit 1
fi

echo ""
echo "========================================================"
echo " Installation completed successfully!"
echo "========================================================"
echo ""
echo "Noctern has been installed. You can now:"
echo ""
if [[ -f "/usr/local/bin/noctern" ]]; then
    echo "  • Run from terminal: noctern"
fi
if [[ -d "$HOME/Applications/Noctern.app" ]]; then
    echo "  • Launch from ~/Applications/Noctern.app"
fi
echo "  • Run from source: $PYTHON_CMD main.py"
echo ""
echo "Important notes:"
echo "  • Add your Gemini API key in settings.conf for LLM features"
echo "  • Or install Ollama for local LLM support"
echo "  • Make sure LaTeX is properly installed for compilation"
echo ""
echo "For Ollama installation:"
echo "  brew install ollama"
echo "  ollama serve"
echo "  ollama pull mistral"
echo ""

read -p "Would you like to launch Noctern now? (y/N): " launch_now
if [[ $launch_now =~ ^[Yy]$ ]]; then
    echo "Launching Noctern..."
    $PYTHON_CMD main.py &
fi

echo ""
echo "Thank you for installing Noctern!"