"""
This module provides a client for interacting with a Large Language Model (LLM) API.
It is designed to send text generation requests and handle streaming responses,
providing real-time output as the LLM generates text.
"""

import json
import requests
from utils import debug_console
from llm import state as llm_state
from metrics.manager import record_usage

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
    This version has an improved cancellation mechanism.
    """
    debug_console.log(f"Initiating LLM generation request for model '{model_name}'. Stream: {stream}. Prompt (first 100 chars): '{prompt_text[:100]}...", level='INFO')
    
    response = None
    try:
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": stream,
                "options": { "num_predict": 1024 }
            },
            stream=stream,
            timeout=(3.1, 120)
        )
        response.raise_for_status()

        if not stream:
            # Non-streaming logic
            json_data = response.json()
            # Record usage
            input_tokens = json_data.get("prompt_eval_count", 0)
            output_tokens = json_data.get("eval_count", 0)
            record_usage(input_tokens, output_tokens)
            
            yield {"success": True, "data": json_data.get("response", ""), "done": True}
            return

        full_generated_content = ""
        buffer = b""
        # Using a small chunk_size to check for cancellation frequently
        for chunk in response.iter_content(chunk_size=128):
            # --- IMMEDIATE CANCELLATION CHECK ---
            # This is the core of the improved cancellation.
            # It checks the flag very frequently.
            if llm_state._is_generation_cancelled:
                debug_console.log("LLM generation cancelled by user flag. Aborting request.", level='INFO')
                # The 'finally' block will handle closing the response.
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
                            debug_console.log("LLM stream finished successfully.", level='SUCCESS')
                            # Record usage
                            input_tokens = json_data.get("prompt_eval_count", 0)
                            output_tokens = json_data.get("eval_count", 0)
                            record_usage(input_tokens, output_tokens)
                            
                            yield {"success": True, "data": full_generated_content, "done": True}
                            return
                    except json.JSONDecodeError:
                        debug_console.log(f"Failed to decode JSON line: {line}", level='WARNING')
                        continue
    
    except requests.exceptions.RequestException as e:
        # Don't show an error if the request failed because we cancelled it
        if not llm_state._is_generation_cancelled:
            error_message = f"Request Error during LLM API call: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_message = f"An unexpected error occurred in the LLM API client: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}
    finally:
        # Ensure the connection is always closed
        if response:
            response.close()
        debug_console.log("LLM API client connection closed.", level='INFO')
