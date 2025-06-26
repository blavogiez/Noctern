# File: llm_api_client.py
# automa_tex_pyqt/services/llm_api_client.py
"""
Client for interacting with the LLM (Large Language Model) API.
This module now supports streaming responses from the LLM.

This module handles sending requests to the LLM backend and processing
the basic response structure.
"""
import requests
import json

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate"
DEFAULT_LLM_MODEL = "mistral"  # Default model for general text generation (e.g., mistral)
LATEX_CODE_MODEL = "codellama:7b-code" # Specific model for LaTeX code generation (e.g., codellama:7b-code)

def request_llm_generation(prompt_text, model_name=DEFAULT_LLM_MODEL):
    """
    Sends a generation request to the LLM API.

    Args:
        prompt_text (str): The prompt to send to the LLM.
        model_name (str): The name of the LLM model to use (default: "mistral").

    Returns:
        Generator[str, None, None]: A generator that yields text chunks as they are received.

    Raises:
        requests.exceptions.ConnectionError: If unable to connect to the LLM API.
        requests.exceptions.RequestException: For other HTTP-related errors (e.g., non-200 status).
        json.JSONDecodeError: If a received chunk is not valid JSON.
    """
    response = requests.post(LLM_API_URL, json={
        "model": model_name,
        "prompt": prompt_text,
        "stream": True
    }, stream=True)

    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

    for line in response.iter_lines():
        if line:
            json_chunk = json.loads(line.decode('utf-8'))
            if "response" in json_chunk:
                yield json_chunk["response"]
