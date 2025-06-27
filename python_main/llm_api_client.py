# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_api_client.py
"""
Client for interacting with the LLM (Large Language Model) API.

This module handles sending requests to the LLM backend and processing
the basic response structure.
"""
import json # Added: Import the json module
import requests

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate"
DEFAULT_LLM_MODEL = "mistral" # Default model to use if not specified

def request_llm_generation(prompt_text, model_name=DEFAULT_LLM_MODEL):
    """
    Sends a generation request to the LLM API.

    Args:
        prompt_text (str): The full prompt to send to the LLM.
        model_name (str): The name of the LLM model to use.

    Returns:
        dict: A dictionary with:
              {"success": True, "data": "LLM response text"} if successful.
              {"success": False, "error": "Error message"} if an error occurred.
        dict: A dictionary containing:
              - "success": bool indicating if the operation is successful so far.
              - "chunk": str, a piece of the generated text (only if success is True and not done).
              - "data": str, the full accumulated response (only if done is True and success is True).
              - "error": str, an error message (only if success is False).
              - "done": bool, indicating if the generation is complete.
    """
    try:
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": True,  # Changed to True for streaming
                "options": {
                    "num_predict": 1024 # A reasonable default for max tokens
                }
            },
            stream=True # Important for requests to stream the response
        )
        response.raise_for_status() # Raise an exception for HTTP errors (e.g., 404, 500)

        full_response_content = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_data = json.loads(line.decode('utf-8'))
                    if "response" in json_data:
                        chunk = json_data["response"]
                        full_response_content += chunk
                        yield {"success": True, "chunk": chunk, "done": False}
                    
                    if json_data.get("done"):
                        # This is the final message from the stream.
                        yield {"success": True, "data": full_response_content, "done": True}
                        return # Exit the generator
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON line from LLM stream: {line}")
                    continue
        # If the loop finishes without a "done": true message (e.g., connection dropped prematurely)
        yield {"success": False, "error": "LLM stream ended unexpectedly without 'done' signal.", "done": True}
    except requests.exceptions.ConnectionError:
        yield {"success": False, "error": "Connection Error: Could not connect to LLM API. Is the backend running?", "done": True}
    except requests.exceptions.RequestException as e:
        yield {"success": False, "error": f"Request Error: {str(e)}", "done": True}
    except Exception as e:
        yield {"success": False, "error": f"An unexpected error occurred: {str(e)}", "done": True}