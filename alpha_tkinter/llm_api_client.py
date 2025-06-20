# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_api_client.py
"""
Client for interacting with the LLM (Large Language Model) API.

This module handles sending requests to the LLM backend and processing
the basic response structure.
"""
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
    """
    try:
        response = requests.post(LLM_API_URL, json={
            "model": model_name,
            "prompt": prompt_text,
            "stream": False  # Assuming non-streaming responses for simplicity here
        })

        if response.status_code == 200:
            llm_response_data = response.json()
            return {"success": True, "data": llm_response_data.get("response", "").strip()}
        else:
            return {"success": False, "error": f"API Error Status {response.status_code}: {response.text[:200]}..."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection Error: Could not connect to LLM API. Is the backend running?"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}