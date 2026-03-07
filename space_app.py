"""
HuggingFace Spaces Entry Point for Insurance Claims Environment

This is the main entry point for the HF Spaces deployment.
Run with: uvicorn space_app:app --host 0.0.0.0 --port 7860
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openenv.core.env_server import create_fastapi_app
from models import ClaimsAction, ClaimsObservation
from server.claims_environment import ClaimsEnvironment

# Create FastAPI app using OpenEnv helper
# Note: OpenEnv expects the class, not an instance
app = create_fastapi_app(ClaimsEnvironment, ClaimsAction, ClaimsObservation)

# Add CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom endpoints
@app.get("/")
async def root():
    """Root endpoint with environment info."""
    return {
        "name": "Insurance Claims Processing Environment",
        "version": "1.0.0",
        "hackathon": "OpenEnv Hackathon - Cerebral Valley",
        "problem_statement": "3.1 - Professional Tasks (World Modeling)",
        "partner_theme": "Scaler AI Labs - Enterprise Workflows",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
        }
    }


@app.get("/info")
async def get_info():
    """Return detailed environment information."""
    return {
        "name": "Insurance Claims Processing Environment",
        "version": "1.0.0",
        "description": "RL environment for training LLMs to process insurance claims",
        "problem_statement": "3.1 - Professional Tasks (World Modeling)",
        "partner_theme": "Scaler AI Labs - Enterprise Workflows",
        "features": [
            "Partial observability - agent must query to learn",
            "Multi-step decision making",
            "Fraud detection with Plaid verification",
            "Business rule enforcement",
            "Enterprise workflow complexity"
        ],
        "valid_actions": ClaimsEnvironment.VALID_ACTIONS,
        "action_costs": ClaimsEnvironment.ACTION_TIME_COSTS,
        "reward_structure": {
            "correct_decision": "+10",
            "wrong_decision": "-5",
            "fraud_caught": "+5",
            "fraud_missed": "-10",
            "plaid_discrepancy_found": "+2",
            "query_cost": "-0.1 to -0.5",
            "efficiency_bonus": "+1 (if <= 4 steps)",
            "efficiency_penalty": "-0.2 per step over 8",
        },
        "scenarios": 8,
        "scenario_types": [
            "Simple approval",
            "Partial approval (coverage limit)",
            "Staged accident fraud",
            "Coverage exclusion denial",
            "Complex escalation required",
            "Inflated claim fraud",
            "Liability claim",
            "Lapsed policy denial"
        ]
    }


@app.get("/scenarios")
async def get_scenarios():
    """Return list of available scenarios."""
    from server.mock_systems import CLAIM_SCENARIOS

    return {
        "total_scenarios": len(CLAIM_SCENARIOS),
        "scenarios": [
            {
                "index": i,
                "claim_id": s.claim_id,
                "claim_type": s.claim_type,
                "complexity": s.complexity,
                "amount": s.claim_amount,
                "is_fraud": s.is_fraud,
            }
            for i, s in enumerate(CLAIM_SCENARIOS)
        ],
    }


# Health check endpoint (required by HF Spaces)
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "environment": "claims_env"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
