<div align="center">
  <img src="resources/icons/app_icon.svg" alt="AutomaTeX Logo" width="128" height="128">
  
  # AutomaTeX
  
  **Modern AI-Assisted LaTeX Editor**
  
  [![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](#)
  [![Release](https://img.shields.io/github/v/release/your-username/AutomaTeX)](https://github.com/your-username/AutomaTeX/releases)
  
  [Features](#-features) •
  [Installation](#-installation) •
  [Quick Start](#-quick-start) •
  [Documentation](#-documentation)
</div>

---

## 🌟 Overview

AutomaTeX is a modern LaTeX editor designed to streamline your writing workflow while preserving LaTeX's power. It combines the ergonomics of contemporary editors with local AI tools, allowing you to focus on what truly matters: **your content**.

**Key Benefits:**
- 🔒 **Privacy-First**: All AI processing happens locally
- ⚡ **Fast & Responsive**: Optimized performance for large documents  
- 🎯 **Intuitive**: Minimal learning curve for LaTeX beginners
- 🔧 **Extensible**: Modular architecture for easy customization

---

## ✨ Features

<div align="center">
  <table>
    <tr>
      <td width="50%" valign="top">
        <h3>🤖 Local AI</h3>
        <ul>
          <li>Text completion and generation</li>
          <li>Intelligent rephrasing</li>
          <li>Document translation</li>
          <li>All processing with Ollama</li>
        </ul>
      </td>
      <td width="50%" valign="top">
        <h3>🖼️ Smart Management</h3>
        <ul>
          <li>Image paste with automatic LaTeX code</li>
          <li>Automatic file organization</li>
          <li>Unused file cleanup</li>
          <li>Integrated PDF preview</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td width="50%" valign="top">
        <h3>⌨️ Optimized Experience</h3>
        <ul>
          <li>Clean interface with light/dark themes</li>
          <li>Syntax highlighting</li>
          <li>Document outline navigation</li>
          <li>Fast search (Ctrl+F)</li>
          <li>Intuitive keyboard shortcuts</li>
        </ul>
      </td>
      <td width="50%" valign="top">
        <h3>🔒 Privacy Focused</h3>
        <ul>
          <li>No data leaves your machine</li>
          <li>AI models run locally</li>
          <li>Free and open-source</li>
          <li>No account required</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

---

## 🚀 Installation

### 📋 Prerequisites

<div align="center">
  <table>
    <tr>
      <th>Tool</th>
      <th>Description</th>
      <th>Download</th>
    </tr>
    <tr>
      <td><b>Python 3.8+</b></td>
      <td>Application runtime</td>
      <td>
        <a href="https://www.python.org/downloads/">
          <img src="https://img.shields.io/badge/Download-Python-blue?style=for-the-badge&logo=python" alt="Download Python">
        </a>
      </td>
    </tr>
    <tr>
      <td><b>LaTeX Distribution</b></td>
      <td>Document compilation</td>
      <td>
        <a href="https://miktex.org/download">
          <img src="https://img.shields.io/badge/Windows-MiKTeX-orange?style=for-the-badge&logo=windows" alt="MiKTeX">
        </a>
        <a href="https://www.tug.org/mactex/">
          <img src="https://img.shields.io/badge/macOS-MacTeX-black?style=for-the-badge&logo=apple" alt="MacTeX">
        </a>
        <a href="https://www.tug.org/texlive/">
          <img src="https://img.shields.io/badge/Linux-TeXLive-yellow?style=for-the-badge&logo=linux" alt="TeX Live">
        </a>
      </td>
    </tr>
    <tr>
      <td><b>Ollama</b></td>
      <td>Local AI engine</td>
      <td>
        <a href="https://ollama.com/">
          <img src="https://img.shields.io/badge/Download-Ollama-FF6B35?style=for-the-badge&logo=ollama" alt="Download Ollama">
        </a>
      </td>
    </tr>
  </table>
</div>

### 🛠️ Installation Steps

```bash
# Clone the repository
git clone https://github.com/your-username/AutomaTeX.git
cd AutomaTeX

# Install Python dependencies
pip install -r requirements.txt

# Download AI models (recommended)
ollama pull mistral
ollama pull codellama:7b-instruct

# Launch the application
python main.py
```

---

## 🏁 Quick Start

1. **Create New Document** → File → New
2. **Write Content** → Use the editor
3. **Use AI** → Ctrl+Shift+G to generate text
4. **Compile** → Click "Compile" button
5. **View PDF** → PDF opens automatically

---

## ⌨️ Keyboard Shortcuts

<div align="center">
  <table>
    <tr>
      <th>Function</th>
      <th>Shortcut</th>
      <th>Description</th>
    </tr>
    <tr>
      <td><b>Search</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>F</kbd></td>
      <td>Open search bar</td>
    </tr>
    <tr>
      <td><b>AI Completion</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd></td>
      <td>Complete current sentence</td>
    </tr>
    <tr>
      <td><b>AI Generation</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>G</kbd></td>
      <td>Generate text from prompt</td>
    </tr>
    <tr>
      <td><b>Rephrase</b></td>
      <td>Selection + <kbd>Ctrl</kbd> + <kbd>R</kbd></td>
      <td>Rephrase selected text</td>
    </tr>
    <tr>
      <td><b>Paste Image</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd></td>
      <td>Paste image from clipboard</td>
    </tr>
    <tr>
      <td><b>Zoom In</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>+</kbd></td>
      <td>Increase text size</td>
    </tr>
    <tr>
      <td><b>Zoom Out</b></td>
      <td><kbd>Ctrl</kbd> + <kbd>-</kbd></td>
      <td>Decrease text size</td>
    </tr>
    <tr>
      <td><b>Compile</b></td>
      <td>Compile Button</td>
      <td>Compile LaTeX document</td>
    </tr>
  </table>
</div>

---

## 📚 Documentation

### 🤖 AI Configuration

Configure AI models in **Settings** → **Manage Models**:
- **Completion**: Model for sentence completion
- **Generation**: Model for text generation  
- **Rephrase**: Model for text rephrasing
- **Debug**: Model for error correction
- **Style**: Model for style improvement

### 🖼️ Image Management

Copy an image and press <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd>:
- Automatically saved to `figures/section/subsection/`
- Sequential naming (`fig_1.png`, `fig_2.png`, etc.)
- LaTeX code inserted automatically

---

## 🛠️ Development

### Architecture

AutomaTeX follows a modular architecture:
- **app/**: GUI components and state management
- **editor/**: Text editing and syntax highlighting
- **latex/**: Compilation and translation services
- **llm/**: AI service integration
- **pdf_preview/**: Integrated PDF viewer

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <h3>🚀 Ready to transform your LaTeX experience?</h3>
  <p>
    <a href="#-installation">
      <img src="https://img.shields.io/badge/Get%20Started-Now-4CAF50?style=for-the-badge&logo=rocket" alt="Get Started">
    </a>
    <a href="https://github.com/your-username/AutomaTeX/issues">
      <img src="https://img.shields.io/badge/Report%20Bug-red?style=for-the-badge&logo=github" alt="Report Bug">
    </a>
  </p>
  
  *Made with ❤️ for the LaTeX community*
</div>