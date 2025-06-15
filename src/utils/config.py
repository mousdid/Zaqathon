import os
from typing import Optional
from openai import OpenAI

def read_api_key(key_name: str = "OPENAI_API_KEY") -> str:
    """
    Read the API key from the llm_keys.txt file.
    
    Args:
        key_name: Name of the API key to read
        
    Returns:
        API key as string
    """
    keys_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "llm_keys.txt")
    
    if not os.path.exists(keys_path):
        raise FileNotFoundError(f"API keys file not found at: {keys_path}")
    
    with open(keys_path, 'r') as file:
        for line in file:
            if line.strip() and '=' in line:
                name, value = line.strip().split('=', 1)
                if name == key_name:
                    return value
    
    raise ValueError(f"API key '{key_name}' not found in keys file")

def get_llm(temperature: float = 0.7, model: str = "gpt-4o") -> OpenAI:
    """
    Get a configured LLM client with the specified parameters.
    
    Args:
        temperature: Controls randomness in the model's responses (0.0 to 1.0)
        model: The model to use (e.g., "gpt-4o", "gpt-3.5-turbo")
        
    Returns:
        Configured OpenAI client ready to use for completions
    """
    api_key = read_api_key("OPENAI_API_KEY")
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Return the client
    # Note: The model and temperature will be used when making actual API calls
    # We'll store them as attributes on the client for convenience
    client.default_model = model
    client.default_temperature = temperature
    
    return client

def generate_completion(client: OpenAI, prompt: str, 
                        model: Optional[str] = None, 
                        temperature: Optional[float] = None) -> str:
    """
    Generate a completion using the provided OpenAI client.
    
    Args:
        client: The OpenAI client to use
        prompt: The input prompt for generation
        model: Optional model to override the default
        temperature: Optional temperature to override the default
        
    Returns:
        Generated text response
    """
    # Use provided parameters or fall back to defaults stored on the client
    model = model or client.default_model
    temperature = temperature or client.default_temperature
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    
    return response.choices[0].message.content