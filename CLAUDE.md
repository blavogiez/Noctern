# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python main.py
```

### Testing
```bash
pytest
```

### Dependencies Management
```bash
pip install -r requirements.txt
```

### LaTeX Compilation Requirements
- Ensure LaTeX distribution is installed (MiKTeX, MacTeX, or TeX Live)
- pdflatex must be available in system PATH
- Optional: chktex for LaTeX linting

## Architecture Overview

AutomaTeX is a Python-based LaTeX editor with LLM integration, built using tkinter/ttkbootstrap for the GUI. The application follows a modular architecture with clean separation of concerns:

### Core Architecture Modules

**Application Layer (`app/`)**
- `main_window.py` - Primary GUI setup and window management
- `interface.py` - Central orchestrator for LLM+UI interactions and user actions
- `state.py` - Global application state management with getter functions
- `panels/` - Integrated sidebar panels for LLM interactions

**Editor Layer (`editor/`)**
- `syntax.py` - Differential syntax highlighting system optimized for performance
- `tab.py` - Editor tab management with weak reference tracking
- `monaco_optimizer.py` - Performance optimizations inspired by Monaco editor

**LaTeX Integration (`latex/`)**
- `compiler.py` - pdflatex subprocess integration and compilation management
- `error_parser.py` - LaTeX error log analysis and user-friendly reporting
- `translator.py` - Document translation using HuggingFace Helsinki models

**LLM Integration (`llm/`)**
- `service.py` - Centralized LLM API facade and service initialization
- `api_client.py` - Ollama and Google Gemini API communication
- `completion.py`, `generation.py`, `rephrase.py` - Feature-specific LLM implementations

**PDF Preview (`pdf_preview/`)**
- `manager.py` - PDF compilation and synchronization from RAM
- `viewer.py` - PDF rendering and display with virtualized viewing
- `interface.py` - Integration with main application

### Key Design Patterns

**Modular Initialization**: All subsystems use getter functions for late binding and modularity (see `main.py:32-65`)

**Performance Optimizations**: 
- Differential syntax highlighting processes only changed lines
- Monaco-style optimization with update throttling and debouncing
- Weak reference management for tab tracking
- Background processing for compilation and LLM operations

**LLM Architecture**: Pure business logic in `llm/` modules with callback support, UI orchestration handled exclusively in `app/interface.py`. No direct UI imports in LLM modules.

**Event-Driven Updates**: Text modification events trigger throttled updates to syntax highlighting, outline view, and PDF preview with rate limiting.

## Key Integration Points

### LLM Service Integration
The LLM system supports both local (Ollama) and cloud (Google Gemini) models:
- Initialize via `llm_service.initialize_llm_service()` with GUI callbacks
- Feature modules (`completion.py`, `generation.py`, etc.) provide business logic
- UI orchestration happens through `app/interface.py` panel callbacks

### PDF Preview System
- Automatic PDF compilation triggered by text changes (rate-limited)
- RAM-based PDF virtualization for performance
- SyncTeX integration for bidirectional editor-PDF navigation

### Editor Performance
- Uses differential highlighting - only processes changed text ranges
- Monaco optimization with update suppression during rapid typing
- Line number updates scheduled separately from syntax highlighting

## Configuration Management

Settings stored in `settings.conf` using ConfigParser format. Key configuration areas:
- Theme management with 15 available themes
- LLM model selection and API configuration
- PDF preview and status bar visibility
- Window geometry and monitor selection
- Performance optimization toggles

## Development Guidelines

### File Organization
- Maintain strict separation between UI (`app/`) and business logic (`llm/`, `latex/`, `editor/`)
- Use getter functions for cross-module dependencies to enable late binding
- Keep editor optimizations separate in `monaco_optimizer.py`

### Performance Considerations
- All syntax highlighting must use differential processing
- LLM operations should be non-blocking with progress indicators
- PDF operations should work from RAM when possible
- Use weak references for tab management to prevent memory leaks

### Testing
- Tests located in `tests/` directory
- Use `pytest` for running tests
- Test configuration in `pytest.ini`