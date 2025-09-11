<div align="center">
  <img src="resources/app_icon.png" alt="Noctern" width="192" height="192">
  
  [![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-Apache-green)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](#)
  
  [Installation](#installation) • [Quick Start](#quick-start) • [Features](#features) • [Documentation](#documentation)
</div>

---

## Overview

*Noctern* is the companion I always wished for during those long nights of LaTeX editing.  
Like many beginners, I often had to rely on ChatGPT to fix my compilation errors. They’re pretty good at it, *aren’t they*? But it’s even better when the help lives in the same window, with precise prompts and the right context at hand.  

This companion also has eyes: it can rephrase your sentences, refine your text, proofread it, translate...  

**What you get:**
- **Everything you expect from a LaTeX editor**: snippets, table insertion, search bar, fast image paste  
- **Time travel**: stores your version every time it is compilable, making debugging purely diff-oriented  
- **Performance optimized**: differential syntax highlighting and optimized rendering for large documents  
- **Integrated workflow**: live PDF preview with real-time compilation and source-syncing built in  
- **Free integrated AI output**: using the Gemini API with generous quotas
- **Privacy mode**: you can also run your AI models locally, privately, and offline, using *Ollama*  

*(Gemini is fast, free, and strong for text. In my opinion, it’s the best solution for a LaTeX companion.)*  
*(Local LLMs are sadly very resource-hungry, which makes it hard to match provider-level output—but the Gemini API is both faster and more reliable.)*

---

## Demonstrations

Actions speak louder than words, and so do images ;

### Preparing its cover page and inserting a table

The student used the anchors available for a quick navigation

### Ordering sauce via image pasting

Luckily enough, the writer had an image pasted in his clipboard. He could order

### Changing his mind

**Planned Demonstrations:**
- LLM-assisted document creation workflow
- Real-time PDF preview and synchronization  
- Advanced editing features and shortcuts
- Error debugging and correction process

---

## Features

### Saving time for *automatable* tasks
- **Text Completion**: Context-aware sentence and paragraph completion
- **Content Generation**: LLM-generated text from prompts and outlines
- **Rephrasing**: Style and clarity improvements for selected text
- **Document Translation**: Multi-language translation capabilities (*Helsinki-NLP*)
- **Debug Assistance**: LLM-powered LaTeX error analysis and suggestions

The system prompts are editable to give full control over the output, using placeholders for quick edits.

### Editor and interface
- **Advanced Syntax Highlighting**: Differential highlighting system optimized for performance
- **Document Navigation**: Integrated outline view with section jumping
- **Theme Support**: 15 themes writing with you in the brightest days and the darkest nights of typesetting to save your eyes
- **Zoom Control**: Text scaling for accessibility and preference

### LaTeX integration
- **Live PDF preview**: Real-time compilation with synchronized viewing
- **Error management**: Intelligent error parsing with user-friendly messages
- **Image management**: Automatic image paste with LaTeX code generation + auto deletion of file (see demo)
- **File organization**: Smart directory structure (figures in section and sub | sub²) and unused file cleanup
- **Write faster**: Extensible table | matrix insertions (7 packages) and snippets

---

## Installation

### Prerequisites

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **Python 3.8+** | Application runtime | [Download Python](https://www.python.org/downloads/) |
| **LaTeX distribution** | Document compilation | [MiKTeX](https://miktex.org/) (Windows) • [MacTeX](https://www.tug.org/mactex/) (macOS) • [TeX Live](https://www.tug.org/texlive/) (Linux) |
| **Ollama** | Local LLM engine | [Download Ollama](https://ollama.com/) |

### Setup instructions

```bash
# Clone the repository
git clone https://github.com/blavogiez/Noctern.git
cd Noctern

# Install Python dependencies
pip install -r requirements.txt

# If using Ollama, download some models
ollama pull mistral

# Launch the application
python main.py
```

---

### Key shortcuts

| Function | Shortcut | Description |
|----------|----------|-------------|
| Casual editor shortcuts | you know them | Not very original |
| LLM Completion | Ctrl+Shift+C | Complete current context |
| LLM Generation | Ctrl+Shift+G | Generate from prompt |
| Rephrase Text | Ctrl+R | Improve selected text |
| Paste Image | Ctrl+Shift+V | Insert image with LaTeX code |
| Zoom In/Out | Ctrl+±/Ctrl+- | Adjust text size |

---

## Code quality

Noctern follows a modular architecture with clean separation of concerns!

Some examples:

```
app/                    # GUI components and application state
├── main_window.py     # Primary window and configuration
├── interface.py       # Central LLM+UI orchestrator
├── panels/            # Integrated sidebar panels for LLM interactions
└── state.py           # Global application state management

editor/                 # Text editing engine and LaTeX support
├── syntax.py          # Differential syntax highlighting
├── tab.py            # Editor tab management
└── monaco_optimizer.py # Performance optimizations (Microsoft monaco like)

latex/                  # LaTeX compilation and processing
├── compiler.py        # pdflatex integration (the casual subprocess command !)
├── error_parser.py    # Error analysis and reporting (handling the trashy logs)
└── translator.py      # Document translation services (huggingface local models (Helsinki MTP Opus))

llm/                    # LLM integration layer (business logic only)
├── service.py         # Centralized LLM API facade
├── api_client.py      # Ollama and external API communication
└── completion.py      # LLM feature implementations

pdf_preview/            # Integrated PDF viewer
├── manager.py         # PDF compilation and sync (from the RAM)
├── viewer.py          # PDF rendering and display ("virtualised" from the RAM)
└── interface.py       # main application integration
```

I wanted an extreme separation of the code so as to build them separately on single-responsibility.

The code quality is honestly good - but not perfect. 

## Performances

Obviously, Tkinter limits me a bit but that was the easiest way to start and the performances were good once I optimized it a bit. 
I really wanted to make the app in Python as it's often the easiest way to deal with AI libraries (especially for the huggingface model translation). I know it is not the best and I probably wouldn't have gone for this if I were to dev this again!

- Syntax highlighting was kind of a struggle but once you apply the methods of big editors like Microsoft Monaco (diff rendering, hashing) it becomes quite fast !
- The app consumes 450mb of ram (non dependent of file size), which is decent for an app containing LLM initialization.
---

## Limitations and considerations

**Technical requirements:**

### Local stuff
- Requires local installation of LaTeX distribution (several GB)
- Large language models require substantial RAM and VRAM (8GB+ recommended)
- For example wise, I have a RTX-4060 equivalent GPU, and mistral7B is decent

**Functional limitations:**
- Limited to LaTeX document format (no WYSIWYG editing)
- Local LLMs are not powerful enough to proofread documents. They just can't produce good json and after some tests, can't be trusted for a good review, missing out on non-relevant informations. Gemini 2.5 flash scored good scores for my tests with a reasonable speed (The proofreading prompt is enormous as any mistake is not allowed), thus the proofreading can't really be ran locally with trusteable results.
- No collaborative editing or cloud synchronization features

**Learning curve:**
- Assumes familiarity with LaTeX syntax and document structure  
- LLM feature configuration requires understanding of model capabilities and sometimes prompting
- Advanced features may require command-line comfort for troubleshooting

---

## Configuration

### LLM Model Management

Configure LLM models through Settings → Manage Models:

- **Completion Model**: For sentence-level completion (recommend: mistral or codellama)
- **Generation Model**: For paragraph and section generation (recommend: mistral)
- **Rephrase Model**: For style and clarity improvements (recommend: mistral)
- **Debug Model**: For LaTeX error analysis (recommend: codellama)
- **Proofreading Model**: For academic correctivity (recommend: gemini 2.5 flash or mixtral)
---

## Personal notes

**This app is mostly a personal project. I do not think this app is as good nor performant as magnificient projects such as TeXstudio or precise neovim configurations. I am satisfied with my work and will use it for my LaTeX needs, but every need is different ! Use it if you're curious and like the demos.**

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for detLLMls.

---

<div align="center">
  <strong>Noctern: Professional LaTeX editing with local LLM assistance</strong>
  <br><br>
  <a href="#installation">Get Started</a> • 
  <a href="https://github.com/blavogiez/Noctern/issues">Report Issues</a> • 
</div>
