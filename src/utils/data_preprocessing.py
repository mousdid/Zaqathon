import re
from typing import Optional, List, Dict, Any


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text by replacing multiple consecutive whitespace 
    characters (spaces, tabs, newlines) with a single space.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace any whitespace character (\s) that appears one or more times (+)
    # with a single space
    normalized_text = re.sub(r'\s+', ' ', text)
    
    # Strip leading and trailing whitespace
    normalized_text = normalized_text.strip()
    
    return normalized_text


def clean_text(text: str) -> str:
    """
    Perform basic text cleaning operations including whitespace normalization.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize whitespace
    text = normalize_whitespace(text)
    
    return text



