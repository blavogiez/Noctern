"""
This module provides a client for interacting with a Large Language Model (LLM) API.
It is designed to send text generation requests and handle streaming responses,
providing real-time output as the LLM generates text.
"""

import json
import requests
import google.generativeai as genai
from app import config as app_config
from utils import debug_console
from llm import state as llm_state
from metrics.manager import record_usage

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate" # Default URL for the LLM API.
MODELS_API_URL = "http://localhost:11434/api/tags" # URL to get the list of available models.
DEFAULT_LLM_MODEL = "mistral" # Default LLM model to be used if not specified in the request.

def get_available_models():
    """
    Fetches the list of available models from the local Ollama API
    and adds Google Gemini models if an API key is configured.

    Returns:
        list: A list of model names.
    """
    model_names = []
    # 1. Fetch local models from Ollama
    try:
        response = requests.get(MODELS_API_URL, timeout=2)
        response.raise_for_status()
        models_data = response.json()
        ollama_models = [model['name'] for model in models_data.get('models', [])]
        model_names.extend(ollama_models)
        debug_console.log(f"Successfully fetched Ollama models: {ollama_models}", level='INFO')
    except requests.exceptions.RequestException:
        debug_console.log("Could not connect to local Ollama API to fetch models. Skipping.", level='WARNING')
    except (KeyError, json.JSONDecodeError) as e:
        debug_console.log(f"Error parsing Ollama models response: {e}", level='ERROR')

    # 2. Add Google Gemini models if API key is set
    config = app_config.load_config()
    if config.get("gemini_api_key"):
        debug_console.log("Gemini API key found, adding Gemini models.", level='INFO')
        gemini_models = [
            # Latest models (2025)
            "gemini/gemini-2.5-pro-exp-01-28",
            "gemini/gemini-2.5-flash-exp-01-28",
            "gemini/gemini-2.5-flash-lite-exp-01-28",
            "gemini/gemini-2.0-flash-exp",
            "gemini/gemini-2.0-pro-exp",
            "gemini/gemini-2.0-flash-lite",
            
            # Gemini 2.0 models
            "gemini/gemini-2.0-flash",
            
            # Gemini 1.5 models
            "gemini/gemini-1.5-pro-latest",
            "gemini/gemini-1.5-pro-002",
            "gemini/gemini-1.5-pro-001",
            "gemini/gemini-1.5-flash-latest",
            "gemini/gemini-1.5-flash-002",
            "gemini/gemini-1.5-flash-001",
            "gemini/gemini-1.5-flash-8b-latest",
            "gemini/gemini-1.5-flash-8b-001",
            
            # Legacy models
            "gemini/gemini-1.0-pro-latest",
            "gemini/gemini-1.0-pro-002",
            "gemini/gemini-1.0-pro-001",
            "gemini/gemini-pro"
        ]
        model_names.extend(gemini_models)
    
    if not model_names:
        debug_console.log("No models available from any source.", level='ERROR')
        return ["default"]
        
    return model_names

def _request_gemini_generation(prompt_text, model_name, stream=True):
    """
    Sends a text generation request to the Google Gemini API.
    """
    config = app_config.load_config()
    api_key = config.get("gemini_api_key")
    if not api_key:
        yield {"success": False, "error": "Gemini API key not configured.", "done": True}
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    try:
        if stream:
            response = model.generate_content(prompt_text, stream=True)
            full_generated_content = ""
            for chunk in response:
                if llm_state._is_generation_cancelled:
                    debug_console.log("Gemini generation cancelled by user flag.", level='INFO')
                    response.prompt_feedback
                    return
                
                chunk_text = chunk.text
                full_generated_content += chunk_text
                yield {"success": True, "chunk": chunk_text, "done": False}
            
            # Record usage after stream is complete
            # Note: Token count from streaming is not directly available per chunk,
            # but we can estimate or use a final call if the API provides it.
            # For now, we will rely on the non-streaming implementation's way if possible
            # or make a separate call to count tokens if needed.
            # Let's assume for now the final response of the stream contains usage data.
            # HACK: As of google-generativeai 0.5.0, usage_metadata is not on streaming chunks.
            # We will make a non-streaming call to get the token count.
            # This is inefficient but necessary for now.
            completion = model.generate_content(prompt_text)
            input_tokens = completion.usage_metadata.prompt_token_count
            output_tokens = completion.usage_metadata.candidates_token_count
            record_usage(input_tokens, output_tokens)

            yield {"success": True, "data": full_generated_content, "done": True}

        else: # Non-streaming
            response = model.generate_content(prompt_text)
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            record_usage(input_tokens, output_tokens)
            yield {"success": True, "data": response.text, "done": True}

    except Exception as e:
        error_message = f"An error occurred with the Gemini API: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        yield {"success": False, "error": error_message, "done": True}


def request_llm_generation(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True):
    """
    Routes the text generation request to the appropriate provider (Ollama or Gemini)
    based on the model name.
    """
    if model_name.startswith("gemini/"):
        # Route to Gemini
        # The model name in the API doesn't have the 'gemini/' prefix
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Routing request to Google Gemini model: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream)
    else:
        # Route to Ollama (existing logic)
        debug_console.log(f"Routing request to Ollama model: {model_name}", level='INFO')
        yield from _request_ollama_generation(prompt_text, model_name, stream)

def _request_ollama_generation(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True):
    """
    Sends a text generation request to the configured Ollama LLM API endpoint.
    """
    debug_console.log(f"Initiating Ollama generation request for model '{model_name}'. Stream: {stream}. Prompt (first 100 chars): '{prompt_text[:100]}...", level='INFO')
    
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
            if llm_state._is_generation_cancelled:
                debug_console.log("Ollama generation cancelled by user flag. Aborting request.", level='INFO')
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
                            debug_console.log("Ollama stream finished successfully.", level='SUCCESS')
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
        if not llm_state._is_generation_cancelled:
            error_message = f"Request Error during Ollama API call: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_message = f"An unexpected error occurred in the Ollama API client: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}
    finally:
        if response:
            response.close()
        debug_console.log("Ollama API client connection closed.", level='INFO')

