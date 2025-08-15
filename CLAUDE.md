# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutomaTeX is a modern LaTeX editor with AI assistance that runs locally. It's a Python desktop application built with ttkbootstrap (Tkinter) that provides LaTeX editing, compilation, PDF preview, and AI-powered text generation/completion using Ollama models.

## Development Commands

### Running the Application
```bash
python main.py
```

### Testing
```bash
pytest
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Prerequisites Setup
- Python 3.8+
- LaTeX distribution (MiKTeX/MacTeX/TeXLive) 
- Ollama with models (mistral, codellama:7b-instruct recommended)

## Architecture Overview

### Core Application Structure
- **main.py**: Entry point that initializes GUI, subsystems (compiler, LLM service, translator), and starts the Tkinter event loop
- **app/**: Main GUI components and application state management
  - `main_window.py`: GUI setup and window management
  - `state.py`: Global application state
  - `actions.py`: User action handlers
  - `config.py`: Configuration loading/saving (settings.conf)

### Key Subsystems
- **editor/**: Text editing functionality (syntax highlighting, search, snippets, structure navigation)
- **latex/**: LaTeX compilation and translation services
- **llm/**: AI service integration with Ollama for completion, generation, rephrasing
- **pdf_preview/**: Integrated PDF viewer with synchronization
- **pre_compiler/**: Error checking and validation
- **metrics/**: Usage tracking and analytics

### Configuration
Settings are stored in `settings.conf` using configparser with these key sections:
- Model assignments (completion, generation, rephrase, debug, style)
- UI preferences (theme, font size, window state, monitor selection)
- Feature toggles (status bar, PDF preview)

### AI Integration Pattern
The LLM service uses lazy initialization and getter functions to access application state, allowing modular integration:
```python
llm_service.initialize_llm_service(
    root_window=root_window,
    active_editor_getter=lambda: state.get_current_tab().editor if state.get_current_tab() else None,
    active_filepath_getter=lambda: state.get_current_tab().file_path if state.get_current_tab() else None
)
```

### Key Features Implementation
- **Image Pasting**: Automatic LaTeX code generation and organized file structure (figures/section/subsection/)
- **AI Completion**: Context-aware text completion and generation via keyboard shortcuts
- **PDF Synchronization**: Bidirectional sync between editor cursor and PDF position
- **Translation**: Document translation with automatic file naming

## Important Development Guidelines

### Performance Optimizations
- Deferred initialization of heavy components (snippets, translation service) to improve startup time
- Heavy updates (syntax highlighting) scheduled with `root_window.after()` to avoid blocking UI
- Lazy loading of LLM models to reduce memory footprint

### Code Conventions
- Use getter functions (lambdas) for accessing dynamic application state
- Initialize services with callback functions rather than direct references for better modularity
- Configuration changes should update both runtime state and persist to settings.conf
- Error handling includes user-friendly status messages and debug logging

### Comment Standards
- Write all comments in English only
- Use professional but informal tone
- Keep comments clear and concise
- Start with action verbs (Initialize, Handle, Process, Create, Load)
- No articles ("a", "the") unless critical for clarity
- No ending punctuation except docstrings
- Max 80 characters per line
- Avoid time-specific language ("now", "currently", "will be")
- Use present tense for describing what code does
- Format: Docstrings `"""Action verb + brief description."""` | Inline `# Action verb + explanation`
- Example: "Handle file operations" not "This will handle file operations"

### Testing
- Tests located in `tests/` directory
- Use pytest with configuration in `pytest.ini`
- Focus on editor events, error parsing, search functionality, and theme management