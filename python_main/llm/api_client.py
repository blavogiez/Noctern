"""
This module provides a client for interacting with a Large Language Model (LLM) API.
It is designed to send text generation requests and handle streaming responses,
providing real-time output as the LLM generates text.
"""

import json
import requests
from utils import debug_console

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate" # Default URL for the LLM API.
DEFAULT_LLM_MODEL = "mistral" # Default LLM model to be used if not specified in the request.

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
        # Send a POST request to the LLM API with the prompt and streaming enabled.
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": stream, # Enable streaming to receive real-time output.
                "options": {
                    "num_predict": 1024 # Maximum number of tokens to predict.
                }
            },
            stream=stream # Keep the connection open for streaming.
        )
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx).

        if not stream:
            json_data = response.json()
            if "response" in json_data:
                debug_console.log("LLM non-stream request successful.", level='SUCCESS')
                yield {"success": True, "data": json_data["response"], "done": True}
                return
            else:
                debug_console.log(f"LLM non-stream response did not contain 'response' field: {json_data}", level='ERROR')
                yield {"success": False, "error": "LLM non-stream response did not contain 'response' field.", "done": True}
                return

        full_generated_content = "" # Accumulator for the complete generated text.
        # Iterate over the response lines, decoding and parsing each as a JSON object.
        for line in response.iter_lines():
            if line:
                try:
                    json_data = json.loads(line.decode('utf-8'))
                    if "response" in json_data: # Check if the current chunk contains a 'response' field.
                        chunk = json_data["response"]
                        full_generated_content += chunk
                        yield {"success": True, "chunk": chunk, "done": False} # Yield the current text chunk.
                    
                    # Check if the 'done' flag is set, indicating the end of generation.
                    if json_data.get("done"):
                        debug_console.log("LLM stream finished successfully with 'done' signal.", level='SUCCESS')
                        yield {"success": True, "data": full_generated_content, "done": True} # Yield final data.
                        return
                except json.JSONDecodeError:
                    debug_console.log(f"Failed to decode JSON line from LLM stream: {line}", level='WARNING')
                    continue # Continue to the next line if JSON decoding fails.
        
        # This part is reached if the stream ends without a 'done' signal.
        debug_console.log("LLM stream ended unexpectedly without a 'done' signal.", level='ERROR')
        yield {"success": False, "error": "LLM stream ended unexpectedly without 'done' signal.", "done": True}

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
