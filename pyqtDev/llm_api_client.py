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
    try:
        print(f"[LLM_API_CLIENT] Connecting to {LLM_API_URL} with model '{model_name}'...")
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": True
            },
            stream=True,
            timeout=120
        )
        print(f"[LLM_API_CLIENT] HTTP status: {response.status_code}")
        response.raise_for_status()
        got_any_response = False
        chunk_count = 0
        for line in response.iter_lines():
            if not line:
                continue
            for part in line.split(b"\r"):
                part = part.strip()
                if not part:
                    continue
                try:
                    json_chunk = json.loads(part.decode("utf-8"))
                    if "response" in json_chunk:
                        got_any_response = True
                        chunk_count += 1
                        print(f"[LLM_API_CLIENT] Received chunk {chunk_count}: {repr(json_chunk['response'][:60])}...")
                        yield json_chunk["response"]
                    elif "done" in json_chunk and json_chunk["done"]:
                        print("[LLM_API_CLIENT] Received 'done' from backend.")
                        return
                except Exception as e:
                    print(f"[LLM_API_CLIENT] Could not decode chunk: {e} | Raw: {repr(part)}")
        if not got_any_response:
            print("[LLM_API_CLIENT] WARNING: No response chunks received from backend. Check your model and prompt.")
        else:
            print(f"[LLM_API_CLIENT] Finished streaming response from backend. Total chunks: {chunk_count}")
    except Exception as e:
        print(f"[LLM_API_CLIENT] LLM API request failed: {e}")
        raise
