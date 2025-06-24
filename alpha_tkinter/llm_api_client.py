# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_api_client.py
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
DEFAULT_LLM_MODEL = "mistral" # Default model to use if not specified

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
    try:
        response = requests.post(LLM_API_URL, json={
            "model": model_name,
            "prompt": prompt_text,
            "stream": True  # Enable streaming responses
        }, stream=True) # Important: set stream=True for requests library to stream content

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    # Each line is a JSON object. Decode it.
                    json_chunk = json.loads(line.decode('utf-8'))
                    # The 'response' field contains the actual text chunk
                    if "response" in json_chunk:
                        yield json_chunk["response"]
        else:
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.ConnectionError:
        raise # Re-raise connection error
    except Exception as e:
        raise requests.exceptions.RequestException(f"An unexpected error occurred: {str(e)}")