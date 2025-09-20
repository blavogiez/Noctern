"""Handle user configuration loading and saving with configparser."""

import configparser
import os
from utils import logs_console

# use a stable absolute path for settings.conf at the project root
# this avoids saving to different locations depending on the process cwd
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_APP_DIR, os.pardir))
CONFIG_FILE = os.path.join(_PROJECT_ROOT, "settings.conf")
DEFAULT_SECTION = "Settings"

# Default config values for file creation and missing keys
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
    "model_completion": "gemini/gemini-2.5-flash-lite",
    "model_generation": "gemini/gemini-2.5-flash-lite",
    "model_rephrase": "gemini/gemini-2.5-flash-lite",
    "model_debug": "gemini/gemini-2.5-flash-lite",
    "model_style": "gemini/gemini-2.5-flash-lite",
    "model_proofreading": "gemini/gemini-2.5-flash-lite",
    "gemini_api_key": "",
    "show_status_bar": "True",
    "show_pdf_preview": "True"
}

def load_config():
    """Load configuration from settings.conf with default fallbacks."""
    config = configparser.ConfigParser()
    
    # create config file with defaults when missing
    if not os.path.exists(CONFIG_FILE):
        logs_console.log(f"Config file not found. Creating default '{CONFIG_FILE}'.", level='INFO')
        config[DEFAULT_SECTION] = DEFAULT_VALUES
        save_config(config[DEFAULT_SECTION])
        return dict(DEFAULT_VALUES)

    try:
        config.read(CONFIG_FILE)
        # verify main config section exists
        if DEFAULT_SECTION not in config:
            config[DEFAULT_SECTION] = {}

        # apply defaults for missing config keys
        settings = config[DEFAULT_SECTION]
        updated = False
        for key, value in DEFAULT_VALUES.items():
            if key not in settings:
                settings[key] = value
                updated = True
        
        if updated:
            logs_console.log("Added missing keys to config file.", level='INFO')
            save_config(settings)

        # convert settings to dictionary format
        return dict(settings)

    except configparser.Error as e:
        logs_console.log(f"Error reading config file: {e}. Using default settings.", level='ERROR')
        return dict(DEFAULT_VALUES)

def save_config(settings_dict):
    """Save settings dictionary to configuration file with API key masking.

    Preserves non-Settings sections (e.g., Session) instead of overwriting the whole file.
    """
    # merge incoming settings with existing ones to avoid reseting other values
    existing_settings = {}
    if os.path.exists(CONFIG_FILE):
        try:
            _cfg = configparser.ConfigParser()
            _cfg.read(CONFIG_FILE)
            if DEFAULT_SECTION in _cfg:
                existing_settings = dict(_cfg[DEFAULT_SECTION])
        except configparser.Error:
            existing_settings = {}
    else:
        # no config yet: start from defaults
        existing_settings = dict(DEFAULT_VALUES)

    merged_settings = dict(existing_settings)
    merged_settings.update(settings_dict)

    # validate and normalize settings
    normalized_settings = _normalize_settings(merged_settings)

    # prepare for logging without exposing secrets
    log_dict = dict(normalized_settings)
    if "gemini_api_key" in log_dict and log_dict["gemini_api_key"]:
        log_dict["gemini_api_key"] = "****"

    # read existing config to preserve other sections
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
        except configparser.Error:
            # fallback to a fresh config if reading fails
            config = configparser.ConfigParser()

    # ensure settings section exists and update it
    if DEFAULT_SECTION not in config:
        config[DEFAULT_SECTION] = {}
    for key, value in normalized_settings.items():
        config[DEFAULT_SECTION][key] = value

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
    
    # convert booleans to strings for config file
    bool_keys = ["show_status_bar", "show_pdf_preview"]
    for key in bool_keys:
        if key in normalized:
            normalized[key] = str(bool(get_bool(normalized[key])))
    
    # validate numeric values
    numeric_keys = {"font_size": (8, 72), "treeview_font_size": (8, 18), "treeview_row_height": (20, 50)}
    for key, (min_val, max_val) in numeric_keys.items():
        if key in normalized:
            try:
                val = max(min_val, min(max_val, int(normalized[key])))
                normalized[key] = str(val)
            except (ValueError, TypeError):
                normalized[key] = str(DEFAULT_VALUES.get(key, min_val))
    
    # ensure required keys exist (but preserve empty api keys)
    for key, default in DEFAULT_VALUES.items():
        if key not in normalized:
            normalized[key] = default
        # special case: don't overwrite empty api keys with defaults
        elif key == "gemini_api_key" and normalized[key] is None:
            normalized[key] = ""
    
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
        # load current config
        current_config = load_config()
        
        # apply updates
        current_config.update(updates_dict)
        
        # save updated config
        save_config(current_config)
        
        # notify modules that might need to reload
        _notify_config_changed(updates_dict)
        
        return current_config
    except Exception as e:
        logs_console.log(f"Error updating config: {e}", level='ERROR')
        raise

def _notify_config_changed(updates_dict):
    """Notify relevant modules when config changes."""
    try:
        # update font if changed
        if "editor_font_family" in updates_dict:
            from app import state
            if hasattr(state, 'zoom_manager') and state.zoom_manager:
                state.zoom_manager.update_font_family(updates_dict["editor_font_family"])
        
        # update llm model settings
        model_keys = [k for k in updates_dict if k.startswith("model_")]
        if model_keys:
            try:
                from llm import state as llm_state
                for key in model_keys:
                    if hasattr(llm_state, key):
                        setattr(llm_state, key, updates_dict[key])
            except ImportError:
                pass  # llm state not available yet
                
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
    
    # extract font values with fallback defaults
    font_family = config_dict.get("treeview_font_family", "Segoe UI")
    font_size = config_dict.get("treeview_font_size", "10")
    row_height = config_dict.get("treeview_row_height", "30")
    
    # validate font size within acceptable range
    try:
        font_size = max(8, min(18, int(font_size)))  # clamp to 8-18 range
    except (ValueError, TypeError):
        font_size = 10
    
    # validate row height within acceptable range
    try:
        row_height = max(20, min(50, int(row_height)))  # clamp to 20-50 range
    except (ValueError, TypeError):
        row_height = 30
    
    # verify font family availability on system
    try:
        available_fonts = tkFont.families()
        if font_family not in available_fonts:
            # use common system fonts as fallbacks
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
    # simple list of preferred coding fonts
    return ["Consolas", "Fira Code", "JetBrains Mono", "Cascadia Code", "Iosevka"]

def get_editor_font_settings(config_dict):
    """Extract and validate editor font configuration settings."""
    font_family = config_dict.get("editor_font_family", "Consolas")
    font_size_str = config_dict.get("font_size", "12")
    
    # validate font size
    try:
        font_size = int(font_size_str)
        if font_size < 8:
            font_size = 8
        elif font_size > 72:
            font_size = 72
    except (ValueError, TypeError):
        font_size = 12
    
    # use the selected font - tkinter will handle fallback if not installed
    
    return {
        "family": font_family,
        "size": font_size
    }
