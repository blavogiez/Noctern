import json
from datetime import datetime
import os

METRICS_FILE = "metrics.json"

def get_metrics_path():
    # Assure que le chemin est relatif au répertoire racine du projet
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(project_root, 'data', METRICS_FILE)

def load_metrics():
    """Charge les métriques depuis le fichier JSON."""
    path = get_metrics_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_metrics(data):
    """Sauvegarde les métriques dans le fichier JSON."""
    path = get_metrics_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Erreur lors de la sauvegarde des métriques : {e}")

def record_usage(input_tokens: int, output_tokens: int):
    """
    Enregistre une nouvelle utilisation de tokens pour la date actuelle.

    Args:
        input_tokens (int): Le nombre de tokens en entrée.
        output_tokens (int): Le nombre de tokens en sortie.
    """
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return

    metrics = load_metrics()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if today_str not in metrics:
        metrics[today_str] = {"input": 0, "output": 0}

    metrics[today_str]["input"] += input_tokens
    metrics[today_str]["output"] += output_tokens

    save_metrics(metrics)
