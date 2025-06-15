import os
import pandas as pd
from typing import Dict, List, Union, Optional


def load_product_catalog(catalog_path: str) -> pd.DataFrame:
    """
    Load product catalog from CSV file.
    
    Args:
        catalog_path: Path to the CSV file containing product catalog
        
    Returns:
        DataFrame containing product information
    """
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Product catalog not found at: {catalog_path}")
    
    df = pd.read_csv(catalog_path)
    # Assuming the product code column might be named differently
    # Try to identify it or use the first column as the index
    code_column = next((col for col in df.columns if 'code' in col.lower()), df.columns[0])
    
    return df.set_index(code_column)


def load_emails(emails_dir: str) -> Dict[str, str]:
    """
    Load all email text files from a directory.
    
    Args:
        emails_dir: Directory containing email text files
        
    Returns:
        Dictionary mapping filename to email content
    """
    if not os.path.exists(emails_dir):
        raise FileNotFoundError(f"Emails directory not found at: {emails_dir}")
    
    emails = {}
    for filename in os.listdir(emails_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(emails_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    emails[filename] = file.read()
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return emails


def create_product_lookup(catalog_df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Create an efficient lookup dictionary from the product catalog DataFrame.
    
    Args:
        catalog_df: Product catalog DataFrame with product code as index
        
    Returns:
        Dictionary for quick product lookups by code
    """
    # Convert DataFrame to dictionary for faster lookups
    return catalog_df.to_dict(orient='index')


def load_data(catalog_path: str, emails_dir: Optional[str] = None) -> Dict:
    """
    Load all necessary data for the application.
    
    Args:
        catalog_path: Path to the product catalog CSV
        emails_dir: Optional path to directory containing emails
        
    Returns:
        Dictionary containing loaded data
    """
    result = {}
    
    # Load product catalog
    catalog_df = load_product_catalog(catalog_path)
    result['catalog_df'] = catalog_df
    result['product_lookup'] = create_product_lookup(catalog_df)
    
    # Load emails if directory is provided
    if emails_dir:
        result['emails'] = load_emails(emails_dir)
    
    return result



