"""
Insurance Claims Processing Environment

OpenEnv environment for training LLMs to process insurance claims.
Statement 3.1: Professional Tasks + Scaler AI Labs sub-theme.

Usage:
    from claims_env import ClaimsEnv, ClaimsAction, ClaimsObservation

    # Async usage
    async with ClaimsEnv(base_url="https://your-space.hf.space") as env:
        obs = await env.reset()
        result = await env.step(ClaimsAction(action_type="query_policy"))

    # Sync usage
    with ClaimsEnv(base_url="https://your-space.hf.space").sync() as env:
        obs = env.reset()
        result = env.step(ClaimsAction(action_type="query_policy"))
"""

from .models import ClaimsAction, ClaimsObservation, ClaimsState
from .client import (
    ClaimsEnv,
    query_policy,
    query_claim_history,
    check_fraud,
    request_documents,
    verify_coverage,
    calculate_payout,
    approve,
    deny,
    escalate,
)

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "ClaimsEnv",
    "ClaimsAction",
    "ClaimsObservation",
    "ClaimsState",
    # Action helpers
    "query_policy",
    "query_claim_history",
    "check_fraud",
    "request_documents",
    "verify_coverage",
    "calculate_payout",
    "approve",
    "deny",
    "escalate",
]
