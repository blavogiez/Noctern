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
    
    # Create copy for secure logging without modifying original
    log_dict = dict(settings_dict)
    if "gemini_api_key" in log_dict and log_dict["gemini_api_key"]:
        log_dict["gemini_api_key"] = "****"  # Mask API key for security
        
    config[DEFAULT_SECTION] = settings_dict
    
    try:
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        logs_console.log(f"Configuration saved to {CONFIG_FILE}: {log_dict}", level='INFO')
    except IOError as e:
        logs_console.log(f"Error saving config file: {e}", level='ERROR')

def get_bool(value_str):
    """Convert configuration string to boolean value."""
    return value_str.lower() in ['true', '1', 't', 'y', 'yes']

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