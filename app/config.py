"""Handle user configuration loading and saving with configparser."""

import configparser
import os
from utils import logs_console

CONFIG_FILE = "settings.conf"
DEFAULT_SECTION = "Settings"

# Default configuration values for file creation and missing keys
DEFAULT_VALUES = {
    "app_monitor": "Default",
    "pdf_monitor": "Default",
    "window_state": "Normal",
    "theme": "flatly",
    "font_size": "12",
    "editor_font_family": "Consolas",
    "treeview_font_family": "Segoe UI",
    "treeview_font_size": "10",
    "treeview_row_height": "45",
    "model_completion": "default",
    "model_generation": "default",
    "model_rephrase": "default",
    "model_debug": "default",
    "model_style": "default",
    "model_proofreading": "default",
    "gemini_api_key": "",
    "show_status_bar": "True",
    "show_pdf_preview": "True"
}

def load_config():
    """Load configuration from settings.conf with default fallbacks."""
    config = configparser.ConfigParser()
    
    # Create configuration file with defaults when missing
    if not os.path.exists(CONFIG_FILE):
        logs_console.log(f"Config file not found. Creating default '{CONFIG_FILE}'.", level='INFO')
        config[DEFAULT_SECTION] = DEFAULT_VALUES
        save_config(config[DEFAULT_SECTION])
        return dict(DEFAULT_VALUES)

    try:
        config.read(CONFIG_FILE)
        # Verify main configuration section exists
        if DEFAULT_SECTION not in config:
            config[DEFAULT_SECTION] = {}

        # Apply defaults for missing configuration keys
        settings = config[DEFAULT_SECTION]
        updated = False
        for key, value in DEFAULT_VALUES.items():
            if key not in settings:
                settings[key] = value
                updated = True
        
        if updated:
            logs_console.log("Added missing keys to config file.", level='INFO')
            save_config(settings)

        # Convert settings to dictionary format
        return dict(settings)

    except configparser.Error as e:
        logs_console.log(f"Error reading config file: {e}. Using default settings.", level='ERROR')
        return dict(DEFAULT_VALUES)

def save_config(settings_dict):
    """Save settings dictionary to configuration file with API key masking."""
    config = configparser.ConfigParser()
    
    # Validate and normalize settings
    normalized_settings = _normalize_settings(settings_dict)
    
    # Create copy for secure logging without modifying original
    log_dict = dict(normalized_settings)
    if "gemini_api_key" in log_dict and log_dict["gemini_api_key"]:
        log_dict["gemini_api_key"] = "****"  # Mask API key for security
        
    config[DEFAULT_SECTION] = normalized_settings
    
    try:
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        logs_console.log(f"Configuration saved to {CONFIG_FILE}: {log_dict}", level='INFO')
    except IOError as e:
        logs_console.log(f"Error saving config file: {e}", level='ERROR')
        raise

def _normalize_settings(settings_dict):
    """Normalize and validate settings before saving."""
    normalized = dict(settings_dict)
    
    # Convert booleans to strings for config file
    bool_keys = ["show_status_bar", "show_pdf_preview"]
    for key in bool_keys:
        if key in normalized:
            normalized[key] = str(bool(get_bool(normalized[key])))
    
    # Validate numeric values
    numeric_keys = {"font_size": (8, 72), "treeview_font_size": (8, 18), "treeview_row_height": (20, 50)}
    for key, (min_val, max_val) in numeric_keys.items():
        if key in normalized:
            try:
                val = max(min_val, min(max_val, int(normalized[key])))
                normalized[key] = str(val)
            except (ValueError, TypeError):
                normalized[key] = str(DEFAULT_VALUES.get(key, min_val))
    
    # Ensure required keys exist
    for key, default in DEFAULT_VALUES.items():
        if key not in normalized:
            normalized[key] = default
    
    return normalized

def reset_config():
    """Reset configuration to default values."""
    try:
        save_config(DEFAULT_VALUES)
        logs_console.log("Configuration reset to defaults", level='INFO')
    except Exception as e:
        logs_console.log(f"Error resetting config: {e}", level='ERROR')
        raise

def update_and_save_config(updates_dict):
    """Update existing config with new values and save atomically."""
    try:
        # Load current config
        current_config = load_config()
        
        # Apply updates
        current_config.update(updates_dict)
        
        # Save updated config
        save_config(current_config)
        
        # Notify modules that might need to reload
        _notify_config_changed(updates_dict)
        
        return current_config
    except Exception as e:
        logs_console.log(f"Error updating config: {e}", level='ERROR')
        raise

def _notify_config_changed(updates_dict):
    """Notify relevant modules when config changes."""
    try:
        # Update font if changed
        if "editor_font_family" in updates_dict:
            from app import state
            if hasattr(state, 'zoom_manager') and state.zoom_manager:
                state.zoom_manager.update_font_family(updates_dict["editor_font_family"])
        
        # Update LLM model settings
        model_keys = [k for k in updates_dict if k.startswith("model_")]
        if model_keys:
            try:
                from llm import state as llm_state
                for key in model_keys:
                    if hasattr(llm_state, key):
                        setattr(llm_state, key, updates_dict[key])
            except ImportError:
                pass  # LLM state not available yet
                
    except Exception as e:
        logs_console.log(f"Warning: config notification failed: {e}", level='WARNING')

def get_bool(value_str):
    """Convert configuration string to boolean value."""
    if isinstance(value_str, bool):
        return value_str
    if isinstance(value_str, str):
        return value_str.lower() in ['true', '1', 't', 'y', 'yes']
    return bool(value_str)

def get_treeview_font_settings(config_dict):
    """Extract and validate treeview font configuration settings."""
    import tkinter.font as tkFont
    
    # Extract font values with fallback defaults
    font_family = config_dict.get("treeview_font_family", "Segoe UI")
    font_size = config_dict.get("treeview_font_size", "10")
    row_height = config_dict.get("treeview_row_height", "30")
    
    # Validate font size within acceptable range
    try:
        font_size = max(8, min(18, int(font_size)))  # Clamp to 8-18 range
    except (ValueError, TypeError):
        font_size = 10
    
    # Validate row height within acceptable range
    try:
        row_height = max(20, min(50, int(row_height)))  # Clamp to 20-50 range
    except (ValueError, TypeError):
        row_height = 30
    
    # Verify font family availability on system
    try:
        available_fonts = tkFont.families()
        if font_family not in available_fonts:
            # Use common system fonts as fallbacks
            for fallback in ["Segoe UI", "Arial", "Helvetica", "DejaVu Sans"]:
                if fallback in available_fonts:
                    font_family = fallback
                    break
            else:
                font_family = "TkDefaultFont"
    except:
        font_family = "Segoe UI"
    
    return {
        "family": font_family,
        "size": font_size, 
        "row_height": row_height
    }

def get_available_editor_fonts():
    """Get list of available programming fonts for editor."""
    # Simple list of preferred coding fonts
    return ["Consolas", "Fira Code", "JetBrains Mono", "Cascadia Code", "Iosevka"]

def get_editor_font_settings(config_dict):
    """Extract and validate editor font configuration settings."""
    font_family = config_dict.get("editor_font_family", "Consolas")
    font_size_str = config_dict.get("font_size", "12")
    
    # Validate font size
    try:
        font_size = int(font_size_str)
        if font_size < 8:
            font_size = 8
        elif font_size > 72:
            font_size = 72
    except (ValueError, TypeError):
        font_size = 12
    
    # Use the selected font - Tkinter will handle fallback if not installed
    
    return {
        "family": font_family,
        "size": font_size
    }