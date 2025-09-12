# Noctern Deployment System

This directory contains everything needed to deploy Noctern easily across different platforms.

## Quick Start

### For End Users

**Windows:**
```bash
.\deployment\scripts\install_windows.bat
```

**macOS:**
```bash
chmod +x deployment/scripts/install_macos.sh && ./deployment/scripts/install_macos.sh
```

**Linux:**
```bash
chmod +x deployment/scripts/install_linux.sh && ./deployment/scripts/install_linux.sh
```

### For Developers

**Create Release:**
```bash
python deployment/scripts/create_release.py
```

**Build Executable:**
```bash
python deployment/build/build_executable.py
```

## Directory Structure

```
deployment/
├── scripts/                 # Installation scripts
│   ├── install_windows.bat  # Windows automated installer
│   ├── install_macos.sh     # macOS automated installer
│   ├── install_linux.sh     # Linux automated installer
│   └── create_release.py    # Release automation script
├── build/                   # Build tools
│   └── build_executable.py  # PyInstaller executable builder
├── docs/                    # Deployment documentation
│   └── DEPLOYMENT.md        # Comprehensive deployment guide
└── README.md               # This file
```

## What Each Script Does

### Installation Scripts (`scripts/`)

- **`install_windows.bat`**: Windows installer that:
  - Checks Python and LaTeX installation
  - Downloads MiKTeX if needed
  - Installs Python dependencies
  - Creates desktop and Start Menu shortcuts
  - Runs final setup

- **`install_macos.sh`**: macOS installer that:
  - Checks system requirements
  - Installs Homebrew if needed
  - Installs MacTeX via Homebrew
  - Creates .app bundle and command line wrapper
  - Sets up proper PATH integration

- **`install_linux.sh`**: Linux installer that:
  - Detects distribution (Ubuntu, Fedora, Arch, etc.)
  - Installs system dependencies via package manager
  - Installs TeX Live
  - Creates desktop entry and command line wrapper
  - Handles PATH setup

### Build Tools (`build/`)

- **`build_executable.py`**: PyInstaller automation that:
  - Installs PyInstaller if needed
  - Creates optimized .spec file
  - Includes all necessary dependencies and resources
  - Builds platform-specific executables
  - Creates installation scripts for standalone distribution

### Release Automation (`scripts/`)

- **`create_release.py`**: Complete release pipeline that:
  - Validates git status and prerequisites
  - Creates source code packages
  - Builds executables for current platform
  - Creates platform-specific installer packages
  - Generates release notes and documentation
  - Creates manifest files for distribution

## Usage Examples

### Simple Installation
```bash
# Clone repository
git clone https://github.com/blavogiez/Noctern.git
cd Noctern

# Run platform-specific installer
./deployment/scripts/install_linux.sh  # or install_macos.sh, install_windows.bat
```

### Building Standalone Executable
```bash
# Install PyInstaller and build
python deployment/build/build_executable.py

# Result will be in dist/ directory
ls dist/
```

### Creating Complete Release
```bash
# Create all release packages
python deployment/scripts/create_release.py

# Result will be in releases/ directory  
ls releases/
# Noctern-v1.0.0-source.zip
# Noctern-v1.0.0-windows.zip
# Noctern-v1.0.0-linux.tar.gz
# Noctern-v1.0.0-RELEASE_NOTES.md
# Noctern-v1.0.0-manifest.json
```

## Features

### Multi-Platform Support
- **Windows**: .bat scripts, .exe executables, registry integration
- **macOS**: Shell scripts, .app bundles, LaunchServices integration  
- **Linux**: Shell scripts, desktop entries, package manager support

### Dependency Management
- Automatic Python dependency installation
- LaTeX distribution detection and installation
- System library dependency resolution
- Optional component handling (Ollama, chktex)

### User Experience
- Progress indicators and colored output
- Error handling with helpful messages
- Automatic shortcut and menu entry creation
- Configuration file setup with defaults

### Developer Experience  
- Cross-platform build automation
- Release packaging and distribution
- Git integration and version management
- Documentation generation

## Configuration

### Environment Variables
- `NOCTERN_INSTALL_DIR`: Override installation directory
- `NOCTERN_SKIP_LATEX`: Skip LaTeX installation check
- `NOCTERN_SKIP_SHORTCUTS`: Skip shortcut creation

### Build Options
You can customize builds by editing the build scripts:
- Exclude unnecessary dependencies
- Add custom resources
- Configure compression settings
- Set platform-specific options

## Troubleshooting

### Common Issues

**Permission Errors:**
- Run installer as administrator (Windows)
- Use `sudo` for system-wide installation (Linux/macOS)
- Install to user directory instead

**Python Not Found:**
- Install Python 3.8+ from python.org
- Add Python to system PATH
- Use `python3` command instead of `python`

**LaTeX Not Found:**
- Install distribution manually if auto-install fails
- Add LaTeX binaries to system PATH
- Verify with `pdflatex --version`

**Build Failures:**
- Install PyInstaller dependencies
- Clear build cache with `--clean` flag
- Check for import errors in application code

### Debug Mode
Add debug flags to installation scripts:
```bash
# Enable debug output
export NOCTERN_DEBUG=1
./deployment/scripts/install_linux.sh
```

## Contributing

To improve the deployment system:

1. Test scripts on target platforms
2. Add support for new distributions/versions
3. Improve error handling and user feedback
4. Optimize executable size and startup time
5. Add more configuration options

## Support

- **Documentation**: `deployment/docs/DEPLOYMENT.md`
- **Issues**: GitHub repository issues
- **Platform-specific help**: Check individual script comments

---

**Ready to deploy Noctern worldwide! 🌍🚀**