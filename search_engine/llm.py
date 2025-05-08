"""
Hugging Face Inference API integration for the search engine project.
This module provides functions to interact with Hugging Face's Serverless Inference API
to enhance search results with LLM capabilities.
"""
import os
import json
import requests
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

load_dotenv()

# Get the Hugging Face API token from environment variables
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# Default model 
DEFAULT_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

def inference_request(
    prompt: str, 
    model_id: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    max_tokens: int = 256,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Send a request to the Hugging Face Inference API.
    
    Args:
        prompt: The text prompt to send to the model
        model_id: Hugging Face model ID (default: DEFAULT_MODEL from env)
        parameters: Additional parameters for the model
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (higher = more creative)
        
    Returns:
        The API response as a dictionary
    """
    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN not found in environment variables")
    
    # Use the provided model ID
    model = model_id or DEFAULT_MODEL
    
    # API endpoint for text generation
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    
    # Set up default parameters if none provided
    if parameters is None:
        parameters = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "return_full_text": False,  # Only return the generated text, not the prompt
        }
    
    # Prepare headers with authorization
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload - format may differ based on the specific model
    payload = {
        "inputs": prompt,
        "parameters": parameters
    }
    
    # Make the API request
    response = requests.post(API_URL, headers=headers, json=payload)
    
    # Check for errors
    response.raise_for_status()
    
    return response.json()

def generate_text(prompt: str, **kwargs) -> str:
    """
    Generate text using the Hugging Face Inference API.
    
    Args:
        prompt: The text prompt
        **kwargs: Additional arguments to pass to inference_request
        
    Returns:
        The generated text as a string
    """
    try:
        response = inference_request(prompt, **kwargs)
        
        # Handle different response formats from different models
        try:
            if isinstance(response, list) and len(response) > 0:
                first_item = response[0]  # type: ignore
                if isinstance(first_item, dict) and "generated_text" in first_item:
                    return first_item["generated_text"]
                return str(first_item)
            elif isinstance(response, dict) and "generated_text" in response:
                return response["generated_text"]
            else:
                return str(response)
        except (TypeError, IndexError, KeyError) as e:
            print(f"Error processing response: {str(e)}")
            return str(response)
            
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return f"Error: {str(e)}"

def enhance_search_results(query: str, results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """
    summarize the search results and key points related to the query
    
    Args:
        query: The user's search query
        results: List of search results
        **kwargs: Additional arguments to pass to generate_text
        
    Returns:
        results with LLM-generated insights
    """
    # Format the prompt with the query and search results
    result_texts = [f"Result {i+1}: {result.get('text', '')[:200]}..." 
                    for i, result in enumerate(results[:3])]
    results_str = "\n".join(result_texts)
    
    prompt = f"""
    User Search Query: {query}
    
    Top Search Results:
    {results_str}
    
    Please provide:
    A brief summary of these search results & key points related to the query
    """
    
    llm_response = generate_text(prompt, **kwargs)
    
    return {
        "original_query": query,
        "enhanced_response": llm_response,
        "search_results": results
    } 