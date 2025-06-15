import os
from typing import Dict, List, Any, Optional
import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

from src.utils.agents.email_agent import EmailOrderAgent
from src.utils.agents.lookup_agent import LookupAgent
from src.utils.data_loader import load_emails


# Define the state for the graph
class State(TypedDict):
    email_content: str
    email_filename: str
    order_info: Dict[str, Any]
    validation_results: Dict[str, Any]
    final_result: Dict[str, Any]
    errors: List[str]
    status: Literal["processing", "complete", "error"]


# Define the nodes in the graph
def extract_order(state: State, email_agent: EmailOrderAgent) -> State:
    """
    Extract order information from an email using the EmailOrderAgent.
    """
    try:
        order_info = email_agent.process_email(state["email_content"])
        return {**state, "order_info": order_info}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [str(e)], "status": "error"}


def validate_order(state: State, lookup_agent: LookupAgent) -> State:
    """
    Validate the extracted order against the product catalog using the LookupAgent.
    """
    try:
        validation_results = lookup_agent.verify_products(state["order_info"])
        return {**state, "validation_results": validation_results}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [str(e)], "status": "error"}


def generate_solutions(state: State, lookup_agent: LookupAgent) -> State:
    """
    Generate solutions for any issues found in the order using the LookupAgent.
    """
    try:
        solutions = lookup_agent.generate_extended_insights(state["validation_results"])
        validation_results = state["validation_results"]
        validation_results["solutions"] = solutions
        return {**state, "validation_results": validation_results}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [str(e)], "status": "error"}


def prepare_final_output(state: State) -> State:
    """
    Prepare the final output combining all results.
    """
    try:
        order_info = state["order_info"]
        validation_results = state["validation_results"]
        final_result = {
            "email_filename": state["email_filename"],
            "order": order_info,
            "validation": validation_results,
            "success": not validation_results.get("missing_products", []) and all(
                p.get("quantity_valid", True) for p in validation_results.get("verified_products", [])
            ),
            "summary": {
                "total_products_requested": len(order_info.get("products", [])),
                "products_found": len(validation_results.get("verified_products", [])),
                "products_missing": len(validation_results.get("missing_products", [])),
                "total_price": validation_results.get("total_price", 0),
                "has_delivery_info": bool(order_info.get("delivery", {})),
            },
        }
        return {**state, "final_result": final_result, "status": "complete"}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [str(e)], "status": "error"}


# Create and configure the graph
def create_processing_graph(email_agent: EmailOrderAgent, lookup_agent: LookupAgent) -> StateGraph:
    """
    Create the LangGraph workflow for order processing.
    """
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("extract_order", lambda state: extract_order(state, email_agent))
    workflow.add_node("validate_order", lambda state: validate_order(state, lookup_agent))
    workflow.add_node("generate_solutions", lambda state: generate_solutions(state, lookup_agent))
    workflow.add_node("prepare_final_output", prepare_final_output)

    # Define edges
    workflow.add_edge("extract_order", "validate_order")
    workflow.add_conditional_edges(
        "validate_order",
        lambda state: bool(state["validation_results"].get("missing_products", [])),
        {
            True: "generate_solutions",
            False: "prepare_final_output",
        },
    )
    workflow.add_edge("generate_solutions", "prepare_final_output")
    workflow.add_edge("prepare_final_output", END)

    # Set entry point
    workflow.set_entry_point("extract_order")

    return workflow.compile()


class OrderProcessingOrchestrator:
    """
    Orchestrates the workflow between EmailOrderAgent and LookupAgent
    to process orders from emails and validate them against a product catalog.
    """
    
    def __init__(self, catalog_path: str, emails_dir: Optional[str] = None,
                 temperature: float = 0.2, model: str = "gpt-4o"):
        """
        Initialize the orchestrator with needed agents.
        
        Args:
            catalog_path: Path to the product catalog CSV
            emails_dir: Directory containing email text files
            temperature: LLM temperature setting
            model: LLM model to use
        """
        # Initialize agents
        self.email_agent = EmailOrderAgent(emails_dir=emails_dir, temperature=temperature, model=model)
        self.lookup_agent = LookupAgent(catalog_path=catalog_path, temperature=temperature, model=model)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow for order processing.
        
        Returns:
            StateGraph object representing the workflow
        """
        workflow = StateGraph(State)
        
        # Define nodes (steps in the workflow)
        workflow.add_node("extract_order", lambda state: extract_order(state, self.email_agent))
        workflow.add_node("validate_order", lambda state: validate_order(state, self.lookup_agent))
        workflow.add_node("generate_solutions", lambda state: generate_solutions(state, self.lookup_agent))
        workflow.add_node("prepare_final_output", prepare_final_output)

        # Define edges (transitions between steps)
        workflow.add_edge("extract_order", "validate_order")
        workflow.add_conditional_edges(
            "validate_order",
            lambda state: bool(state["validation_results"].get("missing_products", [])),
            {
                True: "generate_solutions",
                False: "prepare_final_output",
            },
        )
        workflow.add_edge("generate_solutions", "prepare_final_output")
        workflow.add_edge("prepare_final_output", END)
        
        # Set the entry point
        workflow.set_entry_point("extract_order")
        
        return workflow.compile()
    
    def process_email(self, email_content: str, email_filename: str = "unknown.txt") -> Dict[str, Any]:
        """
        Process a single email through the workflow.
        
        Args:
            email_content: The content of the email
            email_filename: Name of the email file for reference
            
        Returns:
            Final processing result
        """
        graph = self._build_workflow()
        # Initialize the state
        initial_state = {
            "email_content": email_content,
            "email_filename": email_filename,
            "order_info": {},
            "validation_results": {},
            "final_result": {},
            "errors": [],
            "status": "processing",
        }
        
        # Run the workflow
        result=graph.invoke(initial_state)
        
        return result["final_result"]
    
    def process_all_emails(self, emails_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Process all emails in the specified directory.
        
        Args:
            emails_dir: Directory containing email text files
            
        Returns:
            Dictionary mapping email filenames to processing results
        """
        # Load emails if directory is provided
        if emails_dir:
            emails = load_emails(emails_dir)
        else:
            emails = self.email_agent.emails
        
        # Process each email
        results = {}
        for filename, content in emails.items():
            results[filename] = self.process_email(content, filename)
        
        return results


