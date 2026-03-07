"""
Insurance Claims Environment Client

Client for connecting to the Claims Processing environment.
Supports both async and sync usage patterns.
"""

from typing import Optional, Dict, Any
from dataclasses import asdict

from openenv.core import EnvClient
from openenv.core.env_client import StepResult
from .models import ClaimsAction, ClaimsObservation, ClaimsState


class ClaimsEnv(EnvClient[ClaimsAction, ClaimsObservation, ClaimsState]):
    """
    Client for the Insurance Claims Processing environment.

    Example usage (async):
        async with ClaimsEnv(base_url="https://your-space.hf.space") as env:
            obs = await env.reset()
            result = await env.step(ClaimsAction(action_type="query_policy"))

    Example usage (sync):
        with ClaimsEnv(base_url="https://your-space.hf.space").sync() as env:
            obs = env.reset()
            result = env.step(ClaimsAction(action_type="query_policy"))
    """

    def _step_payload(self, action: ClaimsAction) -> Dict[str, Any]:
        """Convert action to API payload."""
        return {
            "action_type": action.action_type,
            "claim_id": action.claim_id,
            "parameters": action.parameters,
        }

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[ClaimsObservation]:
        """Parse API response into StepResult."""
        obs_data = payload.get("observation", payload)

        observation = ClaimsObservation(
            claim_id=obs_data.get("claim_id", ""),
            claim_type=obs_data.get("claim_type", ""),
            claim_amount_requested=obs_data.get("claim_amount_requested", 0.0),
            claimant_name=obs_data.get("claimant_name", ""),
            incident_date=obs_data.get("incident_date", ""),
            description=obs_data.get("description", ""),
            system_response=obs_data.get("system_response", ""),
            action_success=obs_data.get("action_success", True),
            revealed_info=obs_data.get("revealed_info", {}),
            available_actions=obs_data.get("available_actions", []),
            time_elapsed_minutes=obs_data.get("time_elapsed_minutes", 0),
            queries_made=obs_data.get("queries_made", 0),
            is_terminal=obs_data.get("is_terminal", False),
            terminal_reason=obs_data.get("terminal_reason", ""),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=observation.is_terminal,
        )

    def _parse_state(self, payload: Dict[str, Any]) -> ClaimsState:
        """Parse state from API response."""
        return ClaimsState(
            episode_id=payload.get("episode_id", ""),
            claim_id=payload.get("claim_id", ""),
            claim_type=payload.get("claim_type", ""),
            claim_amount_requested=payload.get("claim_amount_requested", 0.0),
            actions_taken=payload.get("actions_taken", 0),
            queries_made=payload.get("queries_made", 0),
            time_elapsed_minutes=payload.get("time_elapsed_minutes", 0),
            total_reward=payload.get("total_reward", 0.0),
        )


# Convenience functions for common actions
def query_policy(claim_id: str = "") -> ClaimsAction:
    """Create a query_policy action."""
    return ClaimsAction(action_type="query_policy", claim_id=claim_id)


def query_claim_history(claim_id: str = "") -> ClaimsAction:
    """Create a query_claim_history action."""
    return ClaimsAction(action_type="query_claim_history", claim_id=claim_id)


def check_fraud(claim_id: str = "") -> ClaimsAction:
    """Create a check_fraud action."""
    return ClaimsAction(action_type="check_fraud", claim_id=claim_id)


def request_documents(doc_types: list, claim_id: str = "") -> ClaimsAction:
    """Create a request_documents action."""
    return ClaimsAction(
        action_type="request_documents",
        claim_id=claim_id,
        parameters={"doc_types": doc_types}
    )


def verify_coverage(damage_type: str, claim_id: str = "") -> ClaimsAction:
    """Create a verify_coverage action."""
    return ClaimsAction(
        action_type="verify_coverage",
        claim_id=claim_id,
        parameters={"damage_type": damage_type}
    )


def calculate_payout(amount: float, claim_id: str = "") -> ClaimsAction:
    """Create a calculate_payout action."""
    return ClaimsAction(
        action_type="calculate_payout",
        claim_id=claim_id,
        parameters={"amount": amount}
    )


def approve(payout: float, reason: str = "Claim approved", claim_id: str = "") -> ClaimsAction:
    """Create an approve action."""
    return ClaimsAction(
        action_type="approve",
        claim_id=claim_id,
        parameters={"payout": payout, "reason": reason}
    )


def deny(reason: str = "Claim denied", claim_id: str = "") -> ClaimsAction:
    """Create a deny action."""
    return ClaimsAction(
        action_type="deny",
        claim_id=claim_id,
        parameters={"reason": reason}
    )


def escalate(reason: str = "Requires senior review", claim_id: str = "") -> ClaimsAction:
    """Create an escalate action."""
    return ClaimsAction(
        action_type="escalate",
        claim_id=claim_id,
        parameters={"reason": reason}
    )
