import json
from typing import Dict, List, Optional, Any

from src.utils.data_loader import load_product_catalog, create_product_lookup
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
            temperature: LLM temperature setting for insight generation
            model: LLM model to use for insight generation
        """
        # Load the product catalog
        self.catalog_df = load_product_catalog(catalog_path)
        self.product_lookup = create_product_lookup(self.catalog_df)
        
        # Initialize LLM parameters
        self.temperature = temperature
        self.model = model
    
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
        
        return self._manual_product_verification(products)
    
    def _manual_product_verification(self, products: List[Dict]) -> Dict[str, Any]:
        """
        Manually verify products against the catalog.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Dictionary with verification results
        """
        verified_products = []
        missing_products = []
        total_price = 0
        
        for product in products:
            product_name = product.get('name')
            quantity = product.get('quantity', 1)
            
            # Check if the product exists in the Product_Name column (partial match)
            matching_products = self.catalog_df[self.catalog_df["Product_Name"].str.contains(product_name, case=False, na=False)]
            
            if not matching_products.empty:
                product_details = matching_products.iloc[0]
                available_in_stock = product_details["Available_in_Stock"]
                price = product_details["Price"]
                min_order_quantity = product_details["Min_Order_Quantity"]
                
                verified_products.append({
                    "name": product_name,
                    "found_in_catalog": True,
                    "quantity_requested": quantity,
                    "quantity_available": available_in_stock,
                    "minimum_order_quantity": min_order_quantity,
                    "quantity_valid": quantity >= min_order_quantity and quantity <= available_in_stock,
                    "price": price,
                    "product_code": product_details["Product_Code"],
                    "description": product_details["Description"]
                })
                
                total_price += price * quantity
            else:
                missing_products.append(product_name)
        
        return {
            "verified_products": verified_products,
            "missing_products": missing_products,
            "total_price": total_price,
            "insights": self._generate_manual_insights(verified_products, missing_products, total_price)
        }
    
    def _generate_manual_insights(self, verified_products, missing_products, total_price):
        """Generate basic insights."""
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
    
    def generate_extended_insights(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate additional insights about the order using LLM.
        
        Args:
            verification_results: Results from product verification
            
        Returns:
            String with extended insights
        """
        try:
            # Get the LLM client
            llm = get_llm(temperature=self.temperature, model=self.model)
            
            # Create a prompt for the LLM to generate insights
            prompt = f"""
            Analyze the following order verification results and provide business insights:
            
            {json.dumps(validation_results, indent=2)}
            
            Provide insights on:
            1. Order completeness and any issues
            2. Inventory implications
            3. Customer service recommendations
            4. Business value of this order
            
            Format your response as a concise bullet-point list with action items for each category.
            """
            
            # Get insights from LLM
            insights = generate_completion(llm, prompt)
            return insights
        except Exception as e:
            # If LLM fails, provide basic insights
            return f"Extended insights generation failed: {str(e)}\n\nBasic insights:\n{validation_results.get('insights', '')}"