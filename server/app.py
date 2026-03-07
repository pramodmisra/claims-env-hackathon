"""
FastAPI Application for Insurance Claims Environment

This is the server entrypoint that creates the FastAPI app
and exposes the environment via HTTP/WebSocket.
"""

from openenv.core.env_server import create_fastapi_app

# Support both package import and direct import (for HF Spaces)
try:
    from ..models import ClaimsAction, ClaimsObservation
    from .claims_environment import ClaimsEnvironment
except ImportError:
    from models import ClaimsAction, ClaimsObservation
    from server.claims_environment import ClaimsEnvironment

# Create FastAPI app using OpenEnv helper
# Note: Pass the CLASS, not an instance (OpenEnv creates instances per session)
app = create_fastapi_app(ClaimsEnvironment, ClaimsAction, ClaimsObservation)


# Add custom endpoints for environment info
@app.get("/info")
async def get_info():
    """Return environment information."""
    return {
        "name": "Insurance Claims Processing Environment",
        "version": "1.0.0",
        "description": "RL environment for training LLMs to process insurance claims",
        "problem_statement": "3.1 - Professional Tasks (World Modeling)",
        "partner_theme": "Scaler AI Labs - Enterprise Workflows",
        "valid_actions": ClaimsEnvironment.VALID_ACTIONS,
        "action_costs": ClaimsEnvironment.ACTION_TIME_COSTS,
        "reward_structure": {
            "correct_decision": "+10",
            "wrong_decision": "-5",
            "fraud_caught": "+5",
            "fraud_missed": "-10",
            "query_cost": "-0.1 to -0.5",
            "efficiency_bonus": "+1 (if <= 4 steps)",
            "efficiency_penalty": "-0.2 per step over 8",
        },
    }


@app.get("/scenarios")
async def get_scenarios():
    """Return list of available scenarios (for debugging)."""
    try:
        from .mock_systems import CLAIM_SCENARIOS
    except ImportError:
        from server.mock_systems import CLAIM_SCENARIOS

    return {
        "total_scenarios": len(CLAIM_SCENARIOS),
        "scenarios": [
            {
                "claim_id": s.claim_id,
                "claim_type": s.claim_type,
                "complexity": s.complexity,
                "amount": s.claim_amount,
            }
            for s in CLAIM_SCENARIOS
        ],
    }
