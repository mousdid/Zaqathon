import os
import json
from typing import Dict, List, Optional, Any, Tuple

from src.utils.data_loader import load_emails
from src.utils.data_preprocessing import normalize_whitespace
from src.utils.prompt_template import get_email_parsing_prompt
from src.utils.config import get_llm, generate_completion


class EmailOrderAgent:
    """
    Agent that extracts purchase order information from emails.
    Focused solely on parsing email content to identify products, quantities, and delivery requirements.
    """
    
    def __init__(self, emails_dir: Optional[str] = None, 
                 temperature: float = 0.2, model: str = "gpt-4o"):
        """
        Initialize the email order agent.
        
        Args:
            emails_dir: Directory containing email text files
            temperature: LLM temperature setting
            model: LLM model to use
        """
        # Load emails if directory is provided
        self.emails = {}
        if emails_dir:
            self.emails = load_emails(emails_dir)
        
        # Initialize the LLM
        self.llm = get_llm(temperature=temperature, model=model)
    
    def load_emails_from_dir(self, emails_dir: str) -> Dict[str, str]:
        """
        Load emails from a directory.
        
        Args:
            emails_dir: Directory containing email text files
            
        Returns:
            Dictionary of email content by filename
        """
        self.emails = load_emails(emails_dir)
        return self.emails
    
    def extract_order_from_email(self, email_content: str) -> Dict[str, Any]:
        """
        Extract order information from email content using LLM.
        
        Args:
            email_content: The content of the email
            
        Returns:
            Dictionary containing extracted order information
        """
        # Clean the email content
        cleaned_email = normalize_whitespace(email_content)
        
        # Generate the prompt for email parsing
        prompt = get_email_parsing_prompt(cleaned_email)
        
        # Get the LLM response
        response = generate_completion(self.llm, prompt)
        
        # Parse the JSON response
        try:
            order_info = json.loads(response)
            return order_info
        except json.JSONDecodeError:
            # If the response isn't valid JSON, try to extract it
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    order_info = json.loads(response[json_start:json_end])
                    return order_info
                except:
                    pass
            
            # Return empty structure if parsing fails
            return {"products": [], "delivery": {}}
    
    def process_email(self, email_content: str) -> Dict[str, Any]:
        """
        Process an email to extract order information.
        
        Args:
            email_content: The content of the email
            
        Returns:
            Dictionary with extracted order information
        """
        # Extract order information
        order_info = self.extract_order_from_email(email_content)
        return order_info
    
    def process_all_emails(self) -> Dict[str, Dict[str, Any]]:
        """
        Process all loaded emails.
        
        Returns:
            Dictionary mapping email filenames to extracted order information
        """
        results = {}
        
        for filename, content in self.emails.items():
            results[filename] = self.process_email(content)
        
        return results