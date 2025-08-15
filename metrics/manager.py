import json
from datetime import datetime
import os

METRICS_FILE = "metrics.json"

def get_metrics_path():
    # Ensure path is relative to project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(project_root, 'data', METRICS_FILE)

def load_metrics():
    """Load metrics from JSON file."""
    path = get_metrics_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_metrics(data):
    """Save metrics to JSON file."""
    path = get_metrics_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving metrics: {e}")

def record_usage(input_tokens: int, output_tokens: int):
    """Record new token usage for current date."""
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return

    metrics = load_metrics()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if today_str not in metrics:
        metrics[today_str] = {"input": 0, "output": 0}

    metrics[today_str]["input"] += input_tokens
    metrics[today_str]["output"] += output_tokens

    save_metrics(metrics)
