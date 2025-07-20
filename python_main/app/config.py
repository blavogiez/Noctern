"""
This module handles loading and saving user configuration settings
from a JSON file.
"""

import json
import os
from utils import debug_console

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "auto_open_pdf": False
}

def load_config():
    """
    Loads the configuration from config.json.
    If the file doesn't exist, returns default settings.
    """
    if not os.path.exists(CONFIG_FILE):
        debug_console.log(f"Config file not found. Using default settings.", level='INFO')
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys are present
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, IOError) as e:
        debug_console.log(f"Error loading config file: {e}. Using default settings.", level='ERROR')
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Saves the given configuration dictionary to config.json.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        debug_console.log(f"Configuration saved to {CONFIG_FILE}", level='INFO')
    except IOError as e:
        debug_console.log(f"Error saving config file: {e}", level='ERROR')

