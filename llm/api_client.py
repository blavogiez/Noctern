"""
LLM API client for Ollama and Google Gemini.
Handle model communication with connection pooling and response caching.
"""

import json
import ollama
import time
import threading
import hashlib
from functools import lru_cache
import google.generativeai as genai
from app import config as app_config
from utils import debug_console
from llm import state as llm_state
from metrics.manager import record_usage

# Configuration
DEFAULT_MODEL = "mistral"
_client = None
_model_cache = {}
_last_model_check = 0
MODEL_CACHE_TTL = 300  # 5 minutes

# Response cache
_response_cache = {}
_cache_timestamps = {}
_cache_hits = 0
_cache_misses = 0
CACHE_SIZE = 150
CACHE_TTL = 1800  # 30 minutes
MIN_CACHE_LENGTH = 50  # Only cache substantial responses

# Connection monitoring
_connection_healthy = True
_last_health_check = 0
HEALTH_CHECK_INTERVAL = 60  # Check every minute

def get_client():
    """Get or create Ollama client instance."""
    global _client, _connection_healthy, _last_health_check
    
    if _client is None:
        _client = ollama.Client()
        debug_console.log("Initialized Ollama client", level='INFO')
    
    # Check connection health periodically
    current_time = time.time()
    if current_time - _last_health_check > HEALTH_CHECK_INTERVAL:
        _check_connection()
        _last_health_check = current_time
    
    return _client

def _check_connection():
    """Check Ollama connection health."""
    global _connection_healthy
    
    try:
        client = _client or ollama.Client()
        client.list()
        if not _connection_healthy:
            debug_console.log("Ollama connection restored", level='SUCCESS')
        _connection_healthy = True
    except Exception as e:
        if _connection_healthy:
            debug_console.log(f"Ollama connection issue: {e}", level='WARNING')
        _connection_healthy = False

def is_connection_healthy():
    """Check if Ollama connection is working."""
    return _connection_healthy

@lru_cache(maxsize=1)
def _fetch_ollama_models():
    """Fetch available Ollama models with caching."""
    try:
        client = get_client()
        response = client.list()
        
        if hasattr(response, 'models') and response.models:
            models = [model.model for model in response.models]
            debug_console.log(f"Found {len(models)} Ollama models", level='INFO')
            return models
        return []
        
    except Exception as e:
        debug_console.log(f"Failed to get Ollama models: {e}", level='WARNING')
        return []

def get_available_models():
    """Get available models from Ollama and Gemini."""
    global _model_cache, _last_model_check
    current_time = time.time()
    
    # Use cached models if still valid
    if _model_cache and (current_time - _last_model_check) < MODEL_CACHE_TTL:
        return _model_cache.copy()
    
    model_names = []
    
    # Get Ollama models
    ollama_models = _fetch_ollama_models()
    model_names.extend(ollama_models)

    # Add Gemini models if API key available
    config = app_config.load_config()
    if config.get("gemini_api_key"):
        gemini_models = [
            # Gemini 2.5 Family (Latest)
            "gemini/gemini-2.5-pro",
            "gemini/gemini-2.5-flash", 
            "gemini/gemini-2.5-flash-lite",
            "gemini/gemini-2.5-pro-exp-01-28",
            "gemini/gemini-2.5-flash-exp-01-28",
            
            # Gemini 2.0 Family  
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-flash-lite",
            "gemini/gemini-2.0-pro",
            "gemini/gemini-2.0-flash-exp",
            "gemini/gemini-2.0-flash-thinking",
            
            # Gemini 1.5 Family (Legacy but still available)
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
            "gemini/gemini-1.5-flash-8b",
            "gemini/gemini-1.5-pro-latest",
            "gemini/gemini-1.5-flash-latest",
            "gemini/gemini-1.5-flash-8b-latest",
            
            # Classic models
            "gemini/gemini-pro"
        ]
        model_names.extend(gemini_models)
    
    # Cache results
    _model_cache = model_names.copy()
    _last_model_check = current_time
    
    return model_names if model_names else ["default"]

def _request_gemini_generation(prompt_text, model_name, stream=True, json_schema=None):
    """Send generation request to Google Gemini API with optional structured output."""
    config = app_config.load_config()
    api_key = config.get("gemini_api_key")
    if not api_key:
        yield {"success": False, "error": "Gemini API key not configured.", "done": True}
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    # Prepare generation config for structured output
    generation_config = {}
    if json_schema:
        generation_config["response_mime_type"] = "application/json"
        generation_config["response_schema"] = json_schema

    try:
        if stream:
            response = model.generate_content(
                prompt_text, 
                stream=True,
                generation_config=generation_config if json_schema else None
            )
            full_content = ""
            for chunk in response:
                if llm_state._is_generation_cancelled:
                    debug_console.log("Gemini generation cancelled", level='INFO')
                    return
                
                # Handle chunks that might not have text
                try:
                    chunk_text = chunk.text if hasattr(chunk, 'text') and chunk.text else ""
                    if chunk_text:
                        full_content += chunk_text
                        yield {"success": True, "chunk": chunk_text, "done": False}
                except Exception as chunk_error:
                    debug_console.log(f"Chunk processing error: {chunk_error}", level='WARNING')
                    # Check if response was blocked
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 1:
                            yield {"success": False, "error": "Content was filtered by safety settings. Try with different text or a different model.", "done": True}
                            return
                    continue
            
            # Record usage for streaming
            try:
                completion = model.generate_content(
                    prompt_text,
                    generation_config=generation_config if json_schema else None
                )
                input_tokens = completion.usage_metadata.prompt_token_count
                output_tokens = completion.usage_metadata.candidates_token_count
                record_usage(input_tokens, output_tokens)
            except:
                # Fallback if usage metadata fails
                record_usage(0, len(full_content.split()))

            yield {"success": True, "data": full_content, "done": True}

        else:
            response = model.generate_content(
                prompt_text,
                generation_config=generation_config if json_schema else None
            )
            
            # Check if response was blocked before accessing text
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 1:
                    yield {"success": False, "error": "Content was filtered by safety settings. Try with different text or a different model.", "done": True}
                    return
            
            # Try to get text safely
            try:
                response_text = response.text if hasattr(response, 'text') and response.text else ""
                if not response_text:
                    yield {"success": False, "error": "Empty response from Gemini. Content may have been filtered.", "done": True}
                    return
                
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                record_usage(input_tokens, output_tokens)
                yield {"success": True, "data": response_text, "done": True}
            except Exception as text_error:
                debug_console.log(f"Error accessing response text: {text_error}", level='ERROR')
                yield {"success": False, "error": "Failed to access response text. Content may have been filtered by safety settings.", "done": True}

    except Exception as e:
        error_message = f"Gemini API error: {str(e)}"
        debug_console.log(error_message, level='ERROR')
        yield {"success": False, "error": error_message, "done": True}

def request_llm_generation(prompt_text, model_name=DEFAULT_MODEL, stream=True):
    """Route generation request to appropriate provider based on model name."""
    if model_name.startswith("gemini/"):
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Using Gemini model: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream)
    else:
        debug_console.log(f"Using Ollama model: {model_name}", level='INFO')
        yield from _request_ollama_generation(prompt_text, model_name, stream)

def _request_ollama_generation(prompt_text, model_name=DEFAULT_MODEL, stream=True, json_format=False):
    """Generate text using Ollama with optional JSON format enforcement."""
    debug_console.log(f"Starting Ollama generation: {model_name}", level='INFO')
    
    try:
        client = get_client()
        options = get_task_options("general")
        
        # Add JSON format for structured output
        request_params = {
            "model": model_name,
            "prompt": prompt_text,
            "stream": stream,
            "options": options
        }
        
        if json_format:
            request_params["format"] = "json"
            debug_console.log("Using Ollama structured JSON output", level='INFO')
        
        if not stream:
            response = client.generate(**request_params)
            
            record_usage(
                response.get("prompt_eval_count", 0),
                response.get("eval_count", 0)
            )
            
            yield {"success": True, "data": response.get("response", ""), "done": True}
            return
        
        # Streaming generation
        full_content = ""
        
        for chunk in client.generate(**request_params):
            if llm_state._is_generation_cancelled:
                debug_console.log("Generation cancelled", level='INFO')
                return
            
            chunk_text = chunk.get("response", "")
            if chunk_text:
                full_content += chunk_text
                yield {"success": True, "chunk": chunk_text, "done": False}
            
            if chunk.get("done"):
                debug_console.log("Ollama generation completed", level='SUCCESS')
                
                record_usage(
                    chunk.get("prompt_eval_count", 0),
                    chunk.get("eval_count", 0)
                )
                
                yield {"success": True, "data": full_content, "done": True}
                return
                
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_msg = f"Ollama generation error: {str(e)}"
            debug_console.log(error_msg, level='ERROR')
            yield {"success": False, "error": error_msg, "done": True}

def get_task_options(task_type):
    """Get generation options for specific task types."""
    base_config = {
        "num_thread": -1,
        "num_ctx": 4096,
        "repeat_penalty": 1.1,
        "tfs_z": 1.0,
    }
    
    task_configs = {
        "completion": {
            "temperature": 0.3,
            "top_p": 0.8,
            "num_predict": 512,
            "top_k": 20,
        },
        "generation": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 1536,
            "top_k": 40,
        },
        "rephrase": {
            "temperature": 0.4,
            "top_p": 0.85,
            "num_predict": 1024,
            "top_k": 25,
        },
        "debug": {
            "temperature": 0.2,
            "top_p": 0.7,
            "num_predict": 2048,
            "top_k": 15,
        }
    }
    
    config = base_config.copy()
    if task_type in task_configs:
        config.update(task_configs[task_type])
    else:
        # Default settings
        config.update({
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 1024,
            "top_k": 40,
        })
    
    return config

def _create_cache_key(prompt_text, model_name, task_type):
    """Create cache key for prompt, model and task combination."""
    content = f"{prompt_text}|{model_name}|{task_type}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def _get_cached_response(prompt_text, model_name, task_type):
    """Get cached response if available and not expired."""
    global _cache_hits, _cache_misses
    
    cache_key = _create_cache_key(prompt_text, model_name, task_type)
    
    if cache_key in _response_cache and cache_key in _cache_timestamps:
        # Check if cache entry is still valid
        if time.time() - _cache_timestamps[cache_key] < CACHE_TTL:
            _cache_hits += 1
            debug_console.log(f"Cache hit (total hits: {_cache_hits})", level='DEBUG')
            return _response_cache[cache_key]
        else:
            # Remove expired entry
            del _response_cache[cache_key]
            del _cache_timestamps[cache_key]
    
    _cache_misses += 1
    return None

def _cache_response(prompt_text, model_name, task_type, response_text):
    """Cache response if it meets minimum length requirement."""
    global _response_cache, _cache_timestamps
    
    # Only cache substantial responses
    if len(response_text.strip()) < MIN_CACHE_LENGTH:
        return
    
    cache_key = _create_cache_key(prompt_text, model_name, task_type)
    
    # Remove oldest entry if cache is full
    if len(_response_cache) >= CACHE_SIZE:
        oldest_key = min(_cache_timestamps.keys(), key=_cache_timestamps.get)
        del _response_cache[oldest_key]
        del _cache_timestamps[oldest_key]
    
    _response_cache[cache_key] = response_text
    _cache_timestamps[cache_key] = time.time()
    
    debug_console.log(f"Response cached (cache size: {len(_response_cache)})", level='DEBUG')

def get_cache_stats():
    """Get cache performance statistics."""
    total_requests = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total_requests * 100) if total_requests > 0 else 0
    return {
        "hits": _cache_hits,
        "misses": _cache_misses,
        "hit_rate": hit_rate,
        "cache_size": len(_response_cache)
    }

def generate_with_structured_output(prompt_text, json_schema, model_name=DEFAULT_MODEL, stream=True, task_type="general"):
    """Generate text with guaranteed structured JSON output."""
    debug_console.log(f"Starting structured output generation (task: {task_type})", level='INFO')
    
    if model_name.startswith("gemini/"):
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Using Gemini model with structured output: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream, json_schema)
    else:
        debug_console.log(f"Using Ollama model with JSON format: {model_name}", level='INFO')
        yield from _generate_ollama_with_profile(prompt_text, model_name, stream, task_type, json_format=True)

def generate_with_task_profile(prompt_text, model_name=DEFAULT_MODEL, stream=True, task_type="general"):
    """Generate text with task-specific settings and caching."""
    # Check cache for non-streaming requests
    if not stream:
        cached_response = _get_cached_response(prompt_text, model_name, task_type)
        if cached_response:
            debug_console.log("Using cached response", level='INFO')
            yield {"success": True, "data": cached_response, "done": True}
            return

    if model_name.startswith("gemini/"):
        actual_model_name = model_name.split('/')[-1]
        debug_console.log(f"Using Gemini model: {actual_model_name}", level='INFO')
        yield from _request_gemini_generation(prompt_text, actual_model_name, stream)
    else:
        debug_console.log(f"Using Ollama model: {model_name} (task: {task_type})", level='INFO')
        yield from _generate_ollama_with_profile(prompt_text, model_name, stream, task_type)

def _generate_ollama_with_profile(prompt_text, model_name, stream, task_type, json_format=False):
    """Generate text using Ollama with task-specific configuration."""
    try:
        client = get_client()
        options = get_task_options(task_type)
        
        # Prepare request parameters
        request_params = {
            "model": model_name,
            "prompt": prompt_text,
            "stream": stream,
            "options": options
        }
        
        if json_format:
            request_params["format"] = "json"
            debug_console.log("Using Ollama JSON format constraint", level='INFO')
        
        if not stream:
            response = client.generate(**request_params)
            
            record_usage(
                response.get("prompt_eval_count", 0),
                response.get("eval_count", 0)
            )
            
            response_text = response.get("response", "")
            
            # Cache the response
            _cache_response(prompt_text, model_name, task_type, response_text)
            
            yield {"success": True, "data": response_text, "done": True}
            return
        
        # Streaming with task profile
        full_content = ""
        
        for chunk in client.generate(**request_params):
            if llm_state._is_generation_cancelled:
                return
            
            chunk_text = chunk.get("response", "")
            if chunk_text:
                full_content += chunk_text
                yield {"success": True, "chunk": chunk_text, "done": False}
            
            if chunk.get("done"):
                record_usage(
                    chunk.get("prompt_eval_count", 0),
                    chunk.get("eval_count", 0)
                )
                
                # Cache the response
                _cache_response(prompt_text, model_name, task_type, full_content)
                
                yield {"success": True, "data": full_content, "done": True}
                return
                
    except Exception as e:
        if not llm_state._is_generation_cancelled:
            error_msg = f"Generation error: {str(e)}"
            debug_console.log(error_msg, level='ERROR')
            yield {"success": False, "error": error_msg, "done": True}