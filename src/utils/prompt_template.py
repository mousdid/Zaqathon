from typing import Dict, List, Optional

# Template for email parsing to extract purchase information
EMAIL_PARSING_TEMPLATE = """
You are an AI assistant specialized in analyzing purchase request emails.

TASK: Extract the following information from the email below:
1. Product SKUs/Codes - Identify all product codes or SKUs mentioned
2. Quantities - For each product, identify the requested quantity
3. Delivery Requirements - Extract any delivery dates, addresses, or special handling instructions

EMAIL:
{email_content}

Respond in the following JSON format:
{{
  "products": [
    {{
      "sku": "product_code",
      "quantity": number,
      "unit": "unit_of_measure"
    }}
  ],
  "delivery": {{
    "date": "YYYY-MM-DD",
    "address": "delivery_address",
    "special_instructions": "any_special_handling"
  }}
}}

Only include fields if they are explicitly mentioned in the email. If information is missing, omit the field.
"""

# Template for product verification against catalog
PRODUCT_VERIFICATION_TEMPLATE = """
You are an AI assistant that verifies product information for an order.

TASK: For each product in the order, verify if it exists in the product catalog.

Products in order:
{order_products}

Product catalog information:
{catalog_info}

Respond in the following JSON format:
{{
  "verified_products": [
    {{
      "sku": "product_code",
      "found_in_catalog": true/false,
      "quantity": number,
      "quantity_available": number,
      "minimum_order_quantity": number,
      "quantity_valid": true/false,
      "price": number
    }}
  ],
  "missing_products": ["sku1", "sku2"],
  "total_price": number
}}
"""

# Template for generating solutions to order issues
SOLUTION_GENERATION_TEMPLATE = """
You are an AI assistant that helps solve problems with customer orders.

TASK: Analyze the order validation results and propose solutions for any issues found.

Order validation results:
{validation_results}

For each issue, propose practical solutions:

1. For missing products (SKUs that don't exist):
   - Suggest similar products that could substitute
   - Suggest how to correct possible typos in SKU numbers

2. For minimum order quantity issues:
   - Suggest increasing the order to meet minimum requirements
   - Suggest combining orders with future purchases
   - Suggest alternative smaller products that don't have MOQ issues

3. For inventory availability issues:
   - Suggest alternative products that are in stock
   - Suggest waiting time for restocking
   - Suggest partial fulfillment options

Be specific, practical and business-oriented in your suggestions.
Format your response as a clear, concise list of recommendations.
"""

def get_email_parsing_prompt(email_content: str) -> str:
    """
    Generate a prompt for parsing purchase information from email content.
    
    Args:
        email_content: The content of the email to parse
        
    Returns:
        Formatted prompt for the LLM
    """
    return EMAIL_PARSING_TEMPLATE.format(email_content=email_content)

def get_product_verification_prompt(order_products: List[Dict], catalog_info: str) -> str:
    """
    Generate a prompt for verifying products against the catalog.
    
    Args:
        order_products: List of product dictionaries extracted from the email
        catalog_info: Information about products in the catalog
        
    Returns:
        Formatted prompt for the LLM
    """
    # Format the order products into a readable string
    products_str = ""
    for prod in order_products:
        products_str += f"SKU: {prod.get('sku', 'Unknown')}, Quantity: {prod.get('quantity', 'Unknown')}\n"
    
    return PRODUCT_VERIFICATION_TEMPLATE.format(
        order_products=products_str,
        catalog_info=catalog_info
    )

def get_solution_generation_prompt(validation_results: Dict) -> str:
    """
    Generate a prompt for creating solutions to order issues.
    
    Args:
        validation_results: Results from product verification
        
    Returns:
        Formatted prompt for the LLM
    """
    return SOLUTION_GENERATION_TEMPLATE.format(
        validation_results=str(validation_results)
    )