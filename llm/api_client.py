"""
This module provides a client for interacting with a Large Language Model (LLM) API.
It is designed to send text generation requests and handle streaming responses,
providing real-time output as the LLM generates text.
"""

import json
import requests
from utils import debug_console
from llm import state as llm_state

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate" # Default URL for the LLM API.
MODELS_API_URL = "http://localhost:11434/api/tags" # URL to get the list of available models.
DEFAULT_LLM_MODEL = "mistral" # Default LLM model to be used if not specified in the request.

def get_available_models():
    """
    Fetches the list of available models from the LLM API.

    Returns:
        list: A list of model names, or an empty list if an error occurs.
    """
    try:
        response = requests.get(MODELS_API_URL, timeout=5)
        response.raise_for_status()
        models_data = response.json()
        
        # The API returns a list of model objects, we need to extract the name.
        # The format is typically {"models": [{"name": "model:tag", ...}]}
        model_names = [model['name'] for model in models_data.get('models', [])]
        debug_console.log(f"Successfully fetched available models: {model_names}", level='INFO')
        return model_names
    except requests.exceptions.RequestException as e:
        debug_console.log(f"Could not fetch available models from API: {e}", level='ERROR')
        return []
    except (KeyError, json.JSONDecodeError) as e:
        debug_console.log(f"Error parsing models response from API: {e}", level='ERROR')
        return []

def request_llm_generation(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True):
    """
    Sends a text generation request to the configured LLM API endpoint.

    This function can operate in both streaming and non-streaming modes.
    In streaming mode (default), it yields chunks of the generated text as they become available.
    In non-streaming mode, it yields a single dictionary with the complete result.

    Args:
        prompt_text (str): The input text (prompt) to send to the LLM for generation.
        model_name (str, optional): The name of the LLM model to use for generation.
                                    Defaults to `DEFAULT_LLM_MODEL`.
        stream (bool, optional): Whether to use streaming. Defaults to True.

    Yields:
        dict: A dictionary containing the status of the generation:
              - (stream=True) {"success": True, "chunk": str, "done": False} for streaming text chunks.
              - (stream=True) {"success": True, "data": str, "done": True} when generation is complete.
              - (stream=False) {"success": True, "data": str, "done": True} for the complete response.
              - {"success": False, "error": str, "done": True} if an error occurs.
    """
    debug_console.log(f"Initiating LLM generation request for model '{model_name}'. Stream: {stream}. Prompt (first 100 chars): '{prompt_text[:100]}...'", level='INFO')
    try:
        # Send a POST request to the LLM API with a very short timeout for the initial connection.
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": stream,
                "options": {
                    "num_predict": 1024
                }
            },
            stream=stream,
            timeout=(3.1, 120)  # (connect_timeout, read_timeout)
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx).

        if not stream:
            # Handling for non-streaming responses remains the same.
            json_data = response.json()
            if "response" in json_data:
                debug_console.log("LLM non-stream request successful.", level='SUCCESS')
                yield {"success": True, "data": json_data["response"], "done": True}
            else:
                debug_console.log(f"LLM non-stream response did not contain 'response' field: {json_data}", level='ERROR')
                yield {"success": False, "error": "LLM non-stream response did not contain 'response' field.", "done": True}
            return

        full_generated_content = "" # Accumulator for the complete generated text.
        buffer = b""
        try:
            for chunk in response.iter_content(chunk_size=1):
                if llm_state._is_generation_cancelled:
                    debug_console.log("LLM generation cancelled by user. Closing connection.", level='INFO')
                    response.close()
                    return

                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        try:
                            json_data = json.loads(line.decode('utf-8'))
                            if "response" in json_data:
                                chunk_text = json_data["response"]
                                full_generated_content += chunk_text
                                yield {"success": True, "chunk": chunk_text, "done": False}
                            
                            if json_data.get("done"):
                                debug_console.log("LLM stream finished successfully with 'done' signal.", level='SUCCESS')
                                yield {"success": True, "data": full_generated_content, "done": True}
                                return
                        except json.JSONDecodeError:
                            debug_console.log(f"Failed to decode JSON line from LLM stream: {line}", level='WARNING')
                            continue
        except requests.exceptions.RequestException as e:
            # This can happen if the connection is closed abruptly.
            if not llm_state._is_generation_cancelled:
                debug_console.log(f"RequestException during LLM stream: {e}", level='ERROR')
                yield {"success": False, "error": f"Request Error: {e}", "done": True}
            else:
                debug_console.log("RequestException caught after cancellation, which is expected.", level='INFO')
            return

    except requests.exceptions.ConnectionError:
        error_message = "Connection Error: Could not connect to the LLM API. Please ensure the backend server is running at " + LLM_API_URL
        debug_console.log(error_message, level='ERROR')
        yield {"success": False, "error": error_message, "done": True}
    except requests.exceptions.RequestException as e:
        error_message = f"Request Error during LLM API call: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        yield {"success": False, "error": error_message, "done": True}
    except Exception as e:
        error_message = f"An unexpected error occurred in the LLM API client: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        yield {"success": False, "error": error_message, "done": True}
