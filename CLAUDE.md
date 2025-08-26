# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutomaTeX is a modern AI-assisted LaTeX editor built with Python and ttkbootstrap. It provides local AI integration through Ollama for text completion, generation, and proofreading, along with an integrated PDF preview system.

## Development Commands

### Running the Application
```bash
python main.py
```

### Testing
Run PDF preview tests:
```bash
python pdf_preview/test.py
python pdf_preview/test_comprehensive.py
```

Run specific test suites with pytest:
```bash
python -m pytest tests/ -v
```

### Dependencies Installation
```bash
pip install -r requirements.txt
```

## Architecture Overview

### Core Modules

**app/**: GUI components and application state
- `main_window.py`: Primary window setup and configuration  
- `state.py`: Global application state management
- `interface.py`: CENTRAL ORCHESTRATOR - All LLM+UI coordination here
- `theme.py`: UI theming and visual customization
- `zoom.py`: Text scaling and zoom functionality
- `panels/`: Integrated sidebar panels for all AI interactions (NO popup dialogs)
- Tab operations, shortcuts, and UI visibility controls

**editor/**: Text editing engine and LaTeX support
- `syntax.py`: Differential LaTeX syntax highlighting with performance optimization
- `syntax_highlighter.py`: Core highlighting implementation
- `syntax_tracker.py`: Line-based change tracking for efficient updates
- `tab.py`: Editor tab management and EditorTab class
- `monaco_optimizer.py`: Performance optimizations for large files
- Document outline, search, snippets, and image management

**latex/**: LaTeX compilation and processing
- `compiler.py`: pdflatex integration and compilation management
- `error_parser.py`: LaTeX error parsing and user-friendly messages
- `translator.py`: Document translation services

**llm/**: AI/LLM integration layer (PURE BUSINESS LOGIC)
- `service.py`: Centralized LLM API facade with callback support
- `api_client.py`: Ollama and external API communication
- `completion.py`, `generation.py`, `proofreading.py`: Core AI features with callbacks
- `schemas/`: Data validation and response parsing
- NO UI IMPORTS: All panel management handled by app/interface.py

**pdf_preview/**: Integrated PDF viewer
- `manager.py`: PDF compilation and synchronization
- `viewer.py`: PDF rendering and display
- `interface.py`: Integration with main application
- Live preview with auto-compilation and editor synchronization

**debug_system/**: LaTeX debugging and error analysis
- `coordinator.py`: Debug workflow coordination
- `llm_analyzer.py`: AI-powered error analysis
- `error_parser.py`: LaTeX error interpretation
- `quick_fixes.py`: Automated error correction

### Key Design Patterns

**Performance Optimization**: 
- Differential syntax highlighting tracks only changed lines
- Large file threshold (2000+ lines) triggers optimized rendering
- Monaco editor optimizations for responsive editing

**AI Integration**:
- Local-first approach using Ollama for privacy
- Modular service architecture with integrated sidebar panels (NO popup dialogs)
- Streaming responses for real-time feedback
- All AI features accessed via sidebar panels (generation, proofreading, rephrase, etc.)

**State Management**:
- Centralized application state with getter functions
- Weak references for memory-efficient editor tracking
- Event-driven architecture for UI updates

## Critical Implementation Notes

**UI Guidelines**: NEVER use emojis in any UI elements, titles, labels, or text content. Keep all interface text clean and professional without emoji characters.

**Syntax Highlighting**: Uses differential highlighting system that only processes changed lines. The `syntax_tracker.py` module maintains line state to optimize performance on large documents.

**AI Service**: Clean separation between LLM logic and UI orchestration. The `llm/` module provides pure business logic with callback support, while `app/interface.py` handles all UI orchestration and panel management. LLM modules never directly call UI components - they use callbacks provided by the app layer.

**PDF Preview**: Automatically synchronizes with LaTeX compilation. Uses pdf2image for rendering and caches pages for performance.

**Editor Tabs**: Managed through `EditorTab` class with weak reference tracking. Each tab maintains its own syntax highlighting state.

## Testing Strategy

- PDF preview module has comprehensive test suites
- Use pytest for structured testing with `pytest.ini` configuration
- Individual module testing through direct Python execution

## Dependencies

Core: ttkbootstrap, Pillow, PyPDF2, pdf2image
AI: ollama, google-generativeai
LaTeX: Requires system pdflatex installation (MiKTeX/TeX Live)

## Refactor Plan: LLM/App Responsibility Separation

### Architecture Pattern
- **LLM module**: Pure business logic with callback parameters
- **App/Interface**: Central orchestrator for all LLM+UI interactions
- **No Bridge Pattern**: Direct callback-based communication

### Implementation Rules
1. LLM modules NEVER import `app.panels`
2. All `show_*_panel()` calls happen in `app/interface.py`
3. LLM functions accept optional callbacks for UI integration
4. Simple, comprehensible, production-ready code