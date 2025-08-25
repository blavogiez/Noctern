# AutomaTeX Integrated Panel System

## Overview

The integrated panel system replaces popup dialogs with embedded panels in the left sidebar, providing a unified and seamless user experience. All AI and tool interactions now happen within the main window instead of separate dialog windows.

## Architecture

### Core Components

```
app/panels/
├── __init__.py           # Package exports
├── manager.py            # PanelManager - Central panel orchestration
├── base_panel.py         # BasePanel - Common interface for all panels
├── helpers.py            # Helper functions for showing panels
└── [panel_files.py]      # Individual panel implementations
```

### SOLID Design Principles

- **Single Responsibility**: Each panel handles one specific feature
- **Open/Closed**: Easy to add new panels without modifying existing code
- **Liskov Substitution**: All panels implement the same BasePanel interface
- **Interface Segregation**: Clean, minimal interfaces for each component
- **Dependency Inversion**: Manager depends on abstractions, not implementations

## Available Panels

### 1. ProofreadingPanel (`proofreading.py`)
- **Purpose**: AI-powered document proofreading and correction
- **Features**: Error analysis, approval system, batch corrections
- **Usage**: `show_proofreading_panel(editor, initial_text)`

### 2. KeywordsPanel (`keywords.py`)
- **Purpose**: Manage LLM keywords for better AI context
- **Features**: File-specific keywords, validation, auto-save
- **Usage**: `show_keywords_panel(file_path)`

### 3. GenerationPanel (`generation.py`)
- **Purpose**: Custom AI text generation with prompts
- **Features**: Prompt history, context options, LaTeX mode
- **Usage**: `show_generation_panel(history, callbacks, initial_prompt)`

### 4. RephrasePanel (`rephrase.py`)
- **Purpose**: Rephrase selected text with custom instructions
- **Features**: Instruction input, text preview, live rephrasing
- **Usage**: `show_rephrase_panel(original_text, callbacks)`

### 5. TranslatePanel (`translate.py`)
- **Purpose**: Document translation using AI models
- **Features**: Language pair selection, preamble options, progress tracking
- **Usage**: `show_translate_panel(text, translations, callback, device)`

### 6. PromptsPanel (`prompts.py`)
- **Purpose**: Edit AI prompt templates
- **Features**: Tabbed editor, reset to defaults, unsaved changes detection
- **Usage**: `show_prompts_panel(current_prompts, defaults, save_callback)`

### 7. SnippetsPanel (`snippets.py`)
- **Purpose**: Manage LaTeX code snippets
- **Features**: CRUD operations, trigger validation, preview
- **Usage**: `show_snippets_panel(current_snippets, save_callback)`

### 8. MetricsPanel (`metrics.py`)
- **Purpose**: View AI usage statistics and metrics
- **Features**: Token usage by date, cost estimation, refresh
- **Usage**: `show_metrics_panel()`

### 9. TableInsertionPanel (`table_insertion.py`)
- **Purpose**: Insert LaTeX tables with customizable options
- **Features**: Size configuration, alignment options, live preview
- **Usage**: `show_table_insertion_panel(insert_callback)`

### 10. DebugPanel (`debug.py`)
- **Purpose**: LaTeX error analysis and debugging
- **Features**: Diff view, log analysis, AI-powered explanations
- **Usage**: `show_debug_panel(diff_content, log_content, editor_getter)`

### 11. ImageDetailsPanel (`image_details.py`)
- **Purpose**: Collect image caption and label information when pasting images
- **Features**: Caption input, label validation, callback-based workflow
- **Usage**: `show_image_details_panel(suggested_label, on_ok_callback, on_cancel_callback)`

### 12. GlobalPromptsPanel (`global_prompts.py`)
- **Purpose**: Edit global default LLM prompt templates
- **Features**: Tabbed interface, placeholder information, file-based storage
- **Usage**: `show_global_prompts_panel()`

## Usage Examples

### Basic Panel Usage
```python
from app.panels import show_keywords_panel, show_global_prompts_panel

# Show keywords panel for current file
show_keywords_panel("/path/to/file.tex")

# Show global prompts editor
show_global_prompts_panel()

# Show image details panel with callback
def on_image_ok(caption, label):
    print(f"Caption: {caption}, Label: {label}")

show_image_details_panel("fig:example_1", on_image_ok)
```

### Custom Panel Implementation
```python
from app.panels.base_panel import BasePanel

class CustomPanel(BasePanel):
    def get_panel_title(self) -> str:
        return "My Custom Panel"
    
    def create_content(self):
        # Create your UI components here
        pass
    
    def focus_main_widget(self):
        # Focus the main input widget
        pass
```

### Integrating with Existing Code
```python
# Old way (popup dialog)
dialog = MyDialog(parent, options)
dialog.show()

# New way (integrated panel)
from app.panels import show_my_panel
show_my_panel(options)
```

## Panel Lifecycle

1. **Creation**: Panel instance created with required parameters
2. **Setup**: `create_panel()` builds UI structure with header and content
3. **Display**: Panel replaces outline/debug in left sidebar
4. **Interaction**: User interacts with panel controls
5. **Focus**: `focus_main_widget()` sets focus to primary input
6. **Close**: Panel closes and restores original sidebar content

## UI Behavior

### Sidebar Management
- **Single Panel**: Only one panel visible at a time
- **Original Content**: Outline and debug panels are hidden when a panel is active
- **Restoration**: Original content restored when panel is closed
- **Close Button**: All panels have a "×" button in the top-right corner

### Focus Management
- Panels automatically focus their main input widget when shown
- Keyboard navigation works within panels
- Tab/Shift+Tab cycles through panel controls

### Theming Integration
- All panels respect the current application theme
- Theme colors accessed via `get_theme_color()` method
- Consistent styling across all panel types

## Migration Guide

### Converting Existing Dialogs

1. **Create Panel Class**: Inherit from `BasePanel`
2. **Implement Required Methods**: `get_panel_title()`, `create_content()`, `focus_main_widget()`
3. **Create Helper Function**: Add to `helpers.py` and export in `__init__.py`
4. **Update Callers**: Replace dialog calls with panel helper functions

### Example Migration
```python
# Before (dialog)
def show_my_dialog(parent, options):
    dialog = tk.Toplevel(parent)
    # ... setup dialog
    dialog.wait_window()

# After (panel)
class MyPanel(BasePanel):
    def __init__(self, parent_container, theme_getter, options, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        self.options = options
    
    def get_panel_title(self) -> str:
        return "My Feature"
    
    def create_content(self):
        # Build UI in self.content_frame
        pass
    
    def focus_main_widget(self):
        # Focus primary input
        pass

# Helper function
def show_my_panel(options):
    if not state.panel_manager:
        return
    panel = MyPanel(None, state.get_theme_setting, options)
    state.panel_manager.show_panel(panel)
```

## Best Practices

### Panel Design
- Keep panels focused on a single task
- Use clear, descriptive titles
- Implement proper keyboard shortcuts
- Provide visual feedback for actions
- Handle errors gracefully

### Performance
- Lazy-load heavy content when possible
- Debounce frequent operations (search, preview updates)
- Dispose of resources properly in close handlers
- Use appropriate widget hierarchies for scrolling

### User Experience
- Auto-focus the most important input field
- Provide clear action buttons
- Show progress for long operations
- Offer keyboard shortcuts for common actions
- Remember user preferences where appropriate

### Code Quality
- Follow existing code style and patterns
- Add appropriate logging for debugging
- Handle edge cases (empty inputs, missing data)
- Write clear docstrings for public methods
- Use type hints for better IDE support

## Troubleshooting

### Common Issues
1. **Panel not showing**: Check if `state.panel_manager` is initialized
2. **Focus problems**: Ensure `focus_main_widget()` is properly implemented
3. **Theme issues**: Use `get_theme_color()` instead of hardcoded colors
4. **Layout problems**: Check grid/pack configurations in `create_content()`

### Debugging Tips
- Enable debug logging to trace panel lifecycle
- Check the panel manager state for active panels
- Verify parent-child widget relationships
- Test with different themes and window sizes

## Future Enhancements

### Planned Features
- Panel state persistence across sessions
- Multi-panel support (split panes)
- Panel resizing and docking options
- Drag-and-drop panel reordering
- Custom keyboard shortcuts per panel

### Extension Points
- Plugin system for third-party panels
- Theme-specific panel styles
- Panel templates for common patterns
- Integration with external tools
- Collaborative editing features

---

*This documentation is part of the AutomaTeX project and follows the established patterns and conventions.*