"""
High-performance LLM API client using native ollama library and Google Gemini.
Optimized for speed and reliability with proper streaming support.
"""

import json
import ollama
import asyncio
import threading
import google.generativeai as genai
from app import config as app_config
from utils import debug_console
from llm import state as llm_state
from metrics.manager import record_usage

# Configuration
DEFAULT_LLM_MODEL = "mistral" # Default LLM model to be used if not specified in the request.
OLLAMA_CLIENT = None  # Global ollama client instance for connection reuse

def _get_ollama_client():
    """Get or create the global Ollama client instance for better performance."""
    global OLLAMA_CLIENT
    if OLLAMA_CLIENT is None:
        OLLAMA_CLIENT = ollama.Client()
        debug_console.log("Initialized high-performance Ollama client", level='INFO')
    return OLLAMA_CLIENT

def get_available_models():
    """
    Fetches the list of available models from Ollama using the native library
    and adds Google Gemini models if an API key is configured.
    
    Returns:
        list: A list of model names.
    """
    model_names = []
    
    # 1. Fetch local models from Ollama using native client
    try:
        client = _get_ollama_client()
        models_response = client.list()
        
        # Extract model names from the native ollama library response
        if hasattr(models_response, 'models') and models_response.models:
            # Native library returns ListResponse with model objects that have .model attribute
            ollama_models = [model.model for model in models_response.models]
        else:
            # Fallback for different response structures
            ollama_models = []
            
        model_names.extend(ollama_models)
        debug_console.log(f"Successfully fetched {len(ollama_models)} Ollama models via native client: {ollama_models}", level='INFO')
        
    except Exception as e:
        debug_console.log(f"Could not connect to Ollama via native client: {e}. Skipping.", level='WARNING')

    # 2. Add Google Gemini models if API key is set
    config = app_config.load_config()
    if config.get("gemini_api_key"):
        debug_console.log("Gemini API key found, adding Gemini models.", level='INFO')
        gemini_models = [
            # Current models
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
            # Token count unavailable from streaming chunks - use separate call
            # Make non-streaming call to get token count
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
        # Remove 'gemini/' prefix from model name for API
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Routing request to Google Gemini model: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream)
    else:
        # Route to Ollama (existing logic)
        debug_console.log(f"Routing request to Ollama model: {model_name}", level='INFO')
        yield from _request_ollama_generation(prompt_text, model_name, stream)

def _request_ollama_generation(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True):
    """
    High-performance Ollama generation using the native ollama library.
    Significantly faster than HTTP requests with optimized streaming.
    """
    debug_console.log(f"Initiating high-performance Ollama generation for model '{model_name}'. Stream: {stream}. Prompt length: {len(prompt_text)} chars", level='INFO')
    
    try:
        client = _get_ollama_client()
        
        # Optimized generation options for better performance
        options = {
            "num_predict": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,  # Increased context window
            "num_thread": -1,  # Use all available CPU threads
        }
        
        if not stream:
            # Non-streaming: Direct response, much faster
            response = client.generate(
                model=model_name,
                prompt=prompt_text,
                stream=False,
                options=options
            )
            
            # Record usage metrics
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)
            record_usage(input_tokens, output_tokens)
            
            yield {"success": True, "data": response.get("response", ""), "done": True}
            return
        
        # Streaming: Native ollama streaming is much more efficient
        full_generated_content = ""
        
        for chunk in client.generate(
            model=model_name,
            prompt=prompt_text,
            stream=True,
            options=options
        ):
            # Fast cancellation check
            if llm_state._is_generation_cancelled:
                debug_console.log("Ollama generation cancelled by user flag", level='INFO')
                return
            
            # Extract chunk text
            chunk_text = chunk.get("response", "")
            if chunk_text:
                full_generated_content += chunk_text
                yield {"success": True, "chunk": chunk_text, "done": False}
            
            # Check if generation is complete
            if chunk.get("done"):
                debug_console.log("High-performance Ollama stream completed successfully", level='SUCCESS')
                
                # Record usage metrics
                input_tokens = chunk.get("prompt_eval_count", 0)
                output_tokens = chunk.get("eval_count", 0)
                record_usage(input_tokens, output_tokens)
                
                yield {"success": True, "data": full_generated_content, "done": True}
                return
                
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_message = f"High-performance Ollama client error: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}

def create_optimized_performance_profile(task_type="general"):
    """
    Create optimized performance profiles for different types of tasks.
    
    Args:
        task_type: "completion", "generation", "rephrase", "debug", or "general"
        
    Returns:
        dict: Optimized options for the specific task
    """
    base_options = {
        "num_thread": -1,  # Use all available CPU threads
        "num_ctx": 4096,   # Large context window
        "repeat_penalty": 1.1,
        "tfs_z": 1.0,
    }
    
    # Task-specific optimizations
    if task_type == "completion":
        return {
            **base_options,
            "temperature": 0.3,      # Lower for more focused completions
            "top_p": 0.8,           # Slightly more focused
            "num_predict": 512,     # Shorter responses for completions
            "top_k": 20,            # More focused token selection
        }
    elif task_type == "generation":
        return {
            **base_options,
            "temperature": 0.7,     # Balanced creativity
            "top_p": 0.9,          # Good diversity
            "num_predict": 1536,   # Longer responses for generation
            "top_k": 40,           # Balanced token selection
        }
    elif task_type == "rephrase":
        return {
            **base_options,
            "temperature": 0.4,     # Lower for consistent rephrasing
            "top_p": 0.85,         # Focused but not too narrow
            "num_predict": 1024,   # Medium length responses
            "top_k": 25,           # Focused token selection
        }
    elif task_type == "debug":
        return {
            **base_options,
            "temperature": 0.2,     # Very focused for debugging
            "top_p": 0.7,          # Narrow focus for accuracy
            "num_predict": 2048,   # Longer for detailed explanations
            "top_k": 15,           # Very focused token selection
        }
    else:  # general
        return {
            **base_options,
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 1024,
            "top_k": 40,
        }

def request_llm_generation_optimized(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True, task_type="general"):
    """
    Optimized version of request_llm_generation with performance profiles.
    
    Args:
        prompt_text: The prompt to send
        model_name: Model to use
        stream: Whether to stream the response
        task_type: Type of task for optimization ("completion", "generation", "rephrase", "debug", "general")
    """
    if model_name.startswith("gemini/"):
        # Route to Gemini (unchanged)
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Routing optimized request to Google Gemini model: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream)
    else:
        # Route to optimized Ollama
        debug_console.log(f"Routing optimized request to Ollama model: {model_name} (profile: {task_type})", level='INFO')
        yield from _request_ollama_generation_optimized(prompt_text, model_name, stream, task_type)

def _request_ollama_generation_optimized(prompt_text, model_name=DEFAULT_LLM_MODEL, stream=True, task_type="general"):
    """
    Ultra-optimized Ollama generation with task-specific performance profiles.
    """
    debug_console.log(f"Starting ultra-optimized Ollama generation (profile: {task_type}) for model '{model_name}'", level='INFO')
    
    try:
        client = _get_ollama_client()
        options = create_optimized_performance_profile(task_type)
        
        # Pre-check model availability for faster error handling
        try:
            # Quick model check - don't fetch full list for performance
            pass  # Skip for now to avoid overhead
        except:
            pass
        
        if not stream:
            # Non-streaming: Maximum performance
            response = client.generate(
                model=model_name,
                prompt=prompt_text,
                stream=False,
                options=options
            )
            
            # Record usage metrics
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)
            record_usage(input_tokens, output_tokens)
            
            yield {"success": True, "data": response.get("response", ""), "done": True}
            return
        
        # Streaming: Optimized for responsiveness
        full_generated_content = ""
        
        for chunk in client.generate(
            model=model_name,
            prompt=prompt_text,
            stream=True,
            options=options
        ):
            # Ultra-fast cancellation check
            if llm_state._is_generation_cancelled:
                debug_console.log("Ultra-optimized Ollama generation cancelled", level='INFO')
                return
            
            # Extract and yield chunk
            chunk_text = chunk.get("response", "")
            if chunk_text:
                full_generated_content += chunk_text
                yield {"success": True, "chunk": chunk_text, "done": False}
            
            # Check completion
            if chunk.get("done"):
                debug_console.log(f"Ultra-optimized Ollama stream completed (profile: {task_type})", level='SUCCESS')
                
                # Record usage metrics
                input_tokens = chunk.get("prompt_eval_count", 0)
                output_tokens = chunk.get("eval_count", 0)
                record_usage(input_tokens, output_tokens)
                
                yield {"success": True, "data": full_generated_content, "done": True}
                return
                
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_message = f"Ultra-optimized Ollama client error: {str(e)}"
            debug_console.log(error_message, level='ERROR')
            yield {"success": False, "error": error_message, "done": True}

