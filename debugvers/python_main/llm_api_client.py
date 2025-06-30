import json
import requests
import debug_console

# Configuration for the LLM API endpoint.
LLM_API_URL = "http://localhost:11434/api/generate"
DEFAULT_LLM_MODEL = "mistral" # Default model to use if not specified

def request_llm_generation(prompt_text, model_name=DEFAULT_LLM_MODEL):
    """
    Sends a generation request to the LLM API and yields streaming chunks.
    """
    debug_console.log(f"Requesting LLM generation from model '{model_name}'. Prompt (start): '{prompt_text[:100]}...'", level='INFO')
    try:
        response = requests.post(
            LLM_API_URL,
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": True,
                "options": {
                    "num_predict": 1024
                }
            },
            stream=True
        )
        response.raise_for_status()

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
                        debug_console.log("LLM stream finished successfully.", level='SUCCESS')
                        yield {"success": True, "data": full_response_content, "done": True}
                        return
                except json.JSONDecodeError:
                    debug_console.log(f"Could not decode JSON line from LLM stream: {line}", level='WARNING')
                    continue
        
        debug_console.log("LLM stream ended unexpectedly without 'done' signal.", level='ERROR')
        yield {"success": False, "error": "LLM stream ended unexpectedly without 'done' signal.", "done": True}

    except requests.exceptions.ConnectionError:
        error_msg = "Connection Error: Could not connect to LLM API. Is the backend running at http://localhost:11434?"
        debug_console.log(error_msg, level='ERROR')
        yield {"success": False, "error": error_msg, "done": True}
    except requests.exceptions.RequestException as e:
        error_msg = f"Request Error: {str(e)}"
        debug_console.log(error_msg, level='ERROR')
        yield {"success": False, "error": error_msg, "done": True}
    except Exception as e:
        error_msg = f"An unexpected error occurred in LLM API client: {str(e)}"
        debug_console.log(error_msg, level='ERROR')
        yield {"success": False, "error": error_msg, "done": True}