#!/bin/bash
# Noctern Linux Installation Script
# This script automatically sets up Noctern on Linux systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================================"
echo " Noctern LaTeX Editor - Linux Installation"
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

# Detect Linux distribution
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
    print_info "Detected $PRETTY_NAME"
else
    print_warning "Cannot detect Linux distribution"
    DISTRO="unknown"
fi

# Check Python installation
echo "[1/7] Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" &> /dev/null; then
        print_status "Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
elif command -v python &> /dev/null; then
    if python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_status "Python $PYTHON_VERSION found"
        PYTHON_CMD="python"
        PIP_CMD="pip"
    else
        print_error "Python 3.8+ required"
        exit 1
    fi
else
    print_error "Python not found"
    echo "Please install Python 3.8+ first:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt update && sudo apt install python3 python3-pip"
            ;;
        fedora)
            echo "  sudo dnf install python3 python3-pip"
            ;;
        centos|rhel)
            echo "  sudo yum install python3 python3-pip"
            ;;
        arch)
            echo "  sudo pacman -S python python-pip"
            ;;
        *)
            echo "  Use your distribution's package manager to install python3"
            ;;
    esac
    exit 1
fi

# Check pip installation
echo "[2/7] Checking pip installation..."
if command -v $PIP_CMD &> /dev/null; then
    print_status "pip found"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_status "pip found"
else
    print_error "pip not found"
    echo "Please install pip first:"
    case $DISTRO in
        ubuntu|debian)
            echo "  sudo apt install python3-pip"
            ;;
        fedora)
            echo "  sudo dnf install python3-pip"
            ;;
        centos|rhel)
            echo "  sudo yum install python3-pip"
            ;;
        arch)
            echo "  sudo pacman -S python-pip"
            ;;
        *)
            echo "  Use your distribution's package manager to install python3-pip"
            ;;
    esac
    exit 1
fi

# Check for LaTeX installation
echo "[3/7] Checking LaTeX installation..."
if command -v pdflatex &> /dev/null; then
    LATEX_VERSION=$(pdflatex --version | head -n1 | cut -d' ' -f1-2)
    print_status "LaTeX found ($LATEX_VERSION)"
else
    print_warning "LaTeX not found"
    read -p "Would you like to install TeX Live? (y/N): " install_latex
    if [[ $install_latex =~ ^[Yy]$ ]]; then
        print_info "Installing TeX Live..."
        case $DISTRO in
            ubuntu|debian)
                sudo apt update
                sudo apt install -y texlive-full
                ;;
            fedora)
                sudo dnf install -y texlive-scheme-full
                ;;
            centos|rhel)
                if command -v dnf &> /dev/null; then
                    sudo dnf install -y texlive-scheme-full
                else
                    sudo yum install -y texlive texlive-latex
                fi
                ;;
            arch)
                sudo pacman -S texlive-most texlive-langgerman
                ;;
            *)
                print_error "Automatic LaTeX installation not supported for $DISTRO"
                echo "Please install TeX Live manually using your package manager"
                ;;
        esac
        
        if command -v pdflatex &> /dev/null; then
            print_status "TeX Live installed successfully"
        else
            print_warning "TeX Live installation may have failed"
        fi
    else
        print_warning "Continuing without LaTeX"
        echo "You can install it later using your package manager"
    fi
fi

# Install system dependencies for PDF rendering
echo "[4/7] Installing system dependencies..."
case $DISTRO in
    ubuntu|debian)
        print_info "Installing system dependencies via apt..."
        sudo apt update
        sudo apt install -y python3-dev python3-tk libpoppler-dev pkg-config
        ;;
    fedora)
        print_info "Installing system dependencies via dnf..."
        sudo dnf install -y python3-devel python3-tkinter poppler-devel pkgconfig
        ;;
    centos|rhel)
        print_info "Installing system dependencies..."
        if command -v dnf &> /dev/null; then
            sudo dnf install -y python3-devel tkinter poppler-devel pkgconfig
        else
            sudo yum install -y python3-devel tkinter poppler-devel pkgconfig
        fi
        ;;
    arch)
        print_info "Installing system dependencies via pacman..."
        sudo pacman -S python tk poppler pkgconf --needed
        ;;
    *)
        print_warning "Unknown distribution - you may need to install system dependencies manually"
        echo "Required packages: python3-dev, python3-tk, libpoppler-dev, pkg-config"
        ;;
esac

print_status "System dependencies installed"

# Install Python dependencies
echo "[5/7] Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip --user
if ! $PYTHON_CMD -m pip install -r requirements.txt --user; then
    print_error "Failed to install Python dependencies"
    echo "Make sure you're in the Noctern directory"
    exit 1
fi

print_status "Python dependencies installed"

# Create desktop entry
echo "[6/7] Creating desktop integration..."
DESKTOP_FILE="$HOME/.local/share/applications/noctern.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Noctern
Comment=LaTeX Editor with LLM Integration
Exec=$PYTHON_CMD $(pwd)/main.py
Icon=$(pwd)/resources/app_icon.png
Terminal=false
Categories=Office;WordProcessor;Education;
MimeType=text/x-tex;
EOF

if [[ -f "$DESKTOP_FILE" ]]; then
    chmod +x "$DESKTOP_FILE"
    
    # Update desktop database if available
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi
    
    print_status "Desktop entry created"
else
    print_warning "Could not create desktop entry"
fi

# Create command line shortcut
if [[ -w "$HOME/.local/bin" ]] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    WRAPPER_SCRIPT="$HOME/.local/bin/noctern"
    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
cd "$(pwd)"
$PYTHON_CMD main.py "\$@"
EOF
    chmod +x "$WRAPPER_SCRIPT"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        if [[ -f ~/.zshrc ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        fi
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    print_status "Command line wrapper created (noctern)"
else
    print_warning "Could not create command line wrapper"
fi

# Run setup script
echo "[7/7] Running final setup..."
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
echo "  • Launch from applications menu (Noctern)"
if [[ -f "$HOME/.local/bin/noctern" ]]; then
    echo "  • Run from terminal: noctern"
    echo "    (restart terminal or source ~/.bashrc if command not found)"
fi
echo "  • Run from source: $PYTHON_CMD main.py"
echo ""
echo "Important notes:"
echo "  • Add your Gemini API key in settings.conf for LLM features"
echo "  • Or install Ollama for local LLM support:"
echo "    curl -fsSL https://ollama.com/install.sh | sh"
echo "    ollama serve"
echo "    ollama pull mistral"
echo "  • Make sure LaTeX is properly installed for compilation"
echo ""

read -p "Would you like to launch Noctern now? (y/N): " launch_now
if [[ $launch_now =~ ^[Yy]$ ]]; then
    echo "Launching Noctern..."
    $PYTHON_CMD main.py &
fi

echo ""
echo "Thank you for installing Noctern!"