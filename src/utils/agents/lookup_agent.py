import json
from typing import Dict, List, Optional, Any

from src.utils.data_loader import load_product_catalog, create_product_lookup
from src.utils.prompt_template import get_product_verification_prompt
from src.utils.config import get_llm, generate_completion


class LookupAgent:
    """
    Agent that verifies products against the catalog and generates insights.
    """
    
    def __init__(self, catalog_path: str, temperature: float = 0.2, model: str = "gpt-4o"):
        """
        Initialize the lookup agent.
        
        Args:
            catalog_path: Path to the product catalog CSV file
            temperature: LLM temperature setting
            model: LLM model to use
        """
        # Load the product catalog
        self.catalog_df = load_product_catalog(catalog_path)
        self.product_lookup = create_product_lookup(self.catalog_df)
        
        # Initialize the LLM
        self.llm = get_llm(temperature=temperature, model=model)
    
    def verify_products(self, order_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify products in the order against the product catalog and generate insights.
        
        Args:
            order_info: Dictionary containing order information extracted from email
            
        Returns:
            Dictionary with verification results and insights
        """
        products = order_info.get("products", [])
        if not products:
            return {
                "verified_products": [],
                "missing_products": [],
                "total_price": 0,
                "insights": "No products found in the order."
            }
        
        # Prepare catalog info for the prompt
        catalog_sample = self.catalog_df.head(5).to_string()
        catalog_info = f"Sample of catalog (showing 5 products):\n{catalog_sample}\n\nTotal products in catalog: {len(self.catalog_df)}"
        
        # Generate verification prompt
        prompt = get_product_verification_prompt(products, catalog_info)
        
        # Get the LLM response
        response = generate_completion(self.llm, prompt)
        
        # Parse the JSON response
        try:
            verification_results = json.loads(response)
            return verification_results
        except json.JSONDecodeError:
            # If the response isn't valid JSON, try to extract it
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    verification_results = json.loads(response[json_start:json_end])
                    return verification_results
                except:
                    pass
            
            # Manual verification as fallback
            return self._manual_product_verification(products)
    
    def _manual_product_verification(self, products: List[Dict]) -> Dict[str, Any]:
        """
        Manually verify products against the catalog without using LLM.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Dictionary with verification results
        """
        verified_products = []
        missing_products = []
        total_price = 0
        
        for product in products:
            sku = product.get('sku')
            quantity = product.get('quantity', 1)
            
            if sku in self.product_lookup:
                product_info = self.product_lookup[sku]
                price = product_info.get('price', 0)
                available = product_info.get('availability', 0)
                min_order = product_info.get('min_order_quantity', 1)
                
                verified_products.append({
                    "sku": sku,
                    "found_in_catalog": True,
                    "quantity": quantity,
                    "quantity_available": available,
                    "minimum_order_quantity": min_order,
                    "quantity_valid": quantity >= min_order and quantity <= available,
                    "price": price
                })
                
                total_price += price * quantity
            else:
                missing_products.append(sku)
        
        return {
            "verified_products": verified_products,
            "missing_products": missing_products,
            "total_price": total_price,
            "insights": self._generate_manual_insights(verified_products, missing_products, total_price)
        }
    
    def _generate_manual_insights(self, verified_products, missing_products, total_price):
        """Generate basic insights without using LLM."""
        insights = []
        
        if missing_products:
            insights.append(f"❌ {len(missing_products)} product(s) not found in catalog: {', '.join(missing_products)}")
        
        invalid_quantity = [p for p in verified_products if not p.get('quantity_valid')]
        if invalid_quantity:
            insights.append(f"⚠️ {len(invalid_quantity)} product(s) have invalid quantities")
        
        if verified_products and not missing_products and not invalid_quantity:
            insights.append("✅ All products verified successfully")
            
        insights.append(f"💰 Total order value: ${total_price:.2f}")
        
        return "\n".join(insights)
    
    def generate_extended_insights(self, verification_results: Dict[str, Any]) -> str:
        """
        Generate additional insights about the order using LLM.
        
        Args:
            verification_results: Results from product verification
            
        Returns:
            String with extended insights
        """
        # Create a prompt for the LLM to generate insights
        prompt = f"""
        Analyze the following order verification results and provide business insights:
        
        {json.dumps(verification_results, indent=2)}
        
        Provide insights on:
        1. Order completeness and any issues
        2. Inventory implications
        3. Customer service recommendations
        4. Business value of this order
        
        Format your response as a concise bullet-point list.
        """
        
        # Get insights from LLM
        insights = generate_completion(self.llm, prompt)
        return insights