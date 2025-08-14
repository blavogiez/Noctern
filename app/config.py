"""
This module handles loading and saving user configuration settings
from a .conf file using configparser.
"""

import configparser
import os
from utils import debug_console

CONFIG_FILE = "settings.conf"
DEFAULT_SECTION = "Settings"

# Define default values here. These will be used to create the file if it doesn't exist,
# and to retrieve values if a specific key is missing.
DEFAULT_VALUES = {
    "app_monitor": "Default",
    "pdf_monitor": "Default",
    "window_state": "Normal",
    "theme": "flatly",
    "font_size": "12",
    "treeview_font_family": "Segoe UI",
    "treeview_font_size": "10",
    "treeview_row_height": "30",
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
    """
    Loads the configuration from settings.conf.
    If the file or a key doesn't exist, it uses and saves the default settings.
    
    Returns:
        A dictionary containing the configuration settings.
    """
    config = configparser.ConfigParser()
    
    # If the file doesn't exist, create it with default values.
    if not os.path.exists(CONFIG_FILE):
        debug_console.log(f"Config file not found. Creating default '{CONFIG_FILE}'.", level='INFO')
        config[DEFAULT_SECTION] = DEFAULT_VALUES
        save_config(config[DEFAULT_SECTION])
        return dict(DEFAULT_VALUES)

    try:
        config.read(CONFIG_FILE)
        # Ensure the main section exists
        if DEFAULT_SECTION not in config:
            config[DEFAULT_SECTION] = {}

        # Check for missing keys and apply defaults
        settings = config[DEFAULT_SECTION]
        updated = False
        for key, value in DEFAULT_VALUES.items():
            if key not in settings:
                settings[key] = value
                updated = True
        
        if updated:
            debug_console.log("Added missing keys to config file.", level='INFO')
            save_config(settings)

        # Return the settings as a dictionary
        return dict(settings)

    except configparser.Error as e:
        debug_console.log(f"Error reading config file: {e}. Using default settings.", level='ERROR')
        return dict(DEFAULT_VALUES)

def save_config(settings_dict):
    """
    Saves the given settings dictionary to settings.conf.
    The API key is not logged for security.
    
    Args:
        settings_dict (dict): A dictionary of settings to save.
    """
    config = configparser.ConfigParser()
    
    # Create a copy for logging to avoid modifying the original dict
    log_dict = dict(settings_dict)
    if "gemini_api_key" in log_dict and log_dict["gemini_api_key"]:
        log_dict["gemini_api_key"] = "****" # Mask the key for logging
        
    config[DEFAULT_SECTION] = settings_dict
    
    try:
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        debug_console.log(f"Configuration saved to {CONFIG_FILE}: {log_dict}", level='INFO')
    except IOError as e:
        debug_console.log(f"Error saving config file: {e}", level='ERROR')

def get_bool(value_str):
    """Helper to convert string from config to boolean."""
    return value_str.lower() in ['true', '1', 't', 'y', 'yes']

def get_treeview_font_settings(config_dict):
    """Helper to get treeview font settings from config with validation."""
    import tkinter.font as tkFont
    
    # Get values with defaults
    font_family = config_dict.get("treeview_font_family", "Segoe UI")
    font_size = config_dict.get("treeview_font_size", "10")
    row_height = config_dict.get("treeview_row_height", "30")
    
    # Validate and convert font size
    try:
        font_size = max(8, min(18, int(font_size)))  # Clamp between 8-18
    except (ValueError, TypeError):
        font_size = 10
    
    # Validate and convert row height  
    try:
        row_height = max(20, min(50, int(row_height)))  # Clamp between 20-50
    except (ValueError, TypeError):
        row_height = 30
    
    # Validate font family exists
    try:
        available_fonts = tkFont.families()
        if font_family not in available_fonts:
            # Fallback to common system fonts
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