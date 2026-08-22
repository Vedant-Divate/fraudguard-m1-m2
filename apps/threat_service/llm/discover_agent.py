from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from pydantic import ValidationError
from shared.schemas.attack import AttackScenario, AttackCategory, RiskLevel, AttackParameters, Provenance
import json

class AgentState(TypedDict):
    category: str
    draft_json: Optional[str]
    validated_scenario: Optional[dict]
    error: Optional[str]

def generate_idea(state: AgentState):
    """Node 1: Mock LLM that returns a structured JSON string based on the category."""
    category = state["category"]
    
    # Hardcoded JSON response simulating an LLM
    mock_json = """
    {
      "attack_id": "MOCK_LLM_001",
      "description": "A simulated %s attack where fraudsters use coordinated networks to exploit system vulnerabilities.",
      "parameters": {
        "new_device": true,
        "velocity_multiplier": 5,
        "location_shift": true,
        "amount_anomaly_z": 2.5,
        "time_window_minutes": 20,
        "merchant_novelty": true
      },
      "features": ["velocity_spike", "new_device", "location_shift"]
    }
    """ % category
    
    return {"draft_json": mock_json, "error": None}

def validate_json(state: AgentState):
    """Node 2: Parse the JSON and validate it with Pydantic."""
    draft = state.get("draft_json", "")
    
    try:
        parsed = json.loads(draft)
        category_enum = AttackCategory(state["category"])
        
        scenario = AttackScenario(
            attack_id=parsed["attack_id"],
            category=category_enum,
            channel="CARD",
            risk_level=RiskLevel.HIGH,
            description=parsed["description"],
            parameters=AttackParameters(**parsed["parameters"]),
            features=parsed["features"],
            novelty_score=0.85,
            provenance=Provenance(source="llm_discovery")
        )
        
        return {"validated_scenario": scenario.model_dump(), "error": None}
        
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

# Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node("generate_idea", generate_idea)
workflow.add_node("validate_json", validate_json)

workflow.set_entry_point("generate_idea")
workflow.add_edge("generate_idea", "validate_json")
workflow.add_edge("validate_json", END)

discover_chain = workflow.compile()