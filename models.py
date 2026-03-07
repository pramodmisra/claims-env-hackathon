"""
Insurance Claims Processing Environment - Data Models

This module defines the Action, Observation, and State models for the
insurance claims processing environment. Designed for OpenEnv hackathon
Statement 3.1: Professional Tasks + Scaler AI Labs sub-theme.

Uses Pydantic models to match OpenEnv base classes.
"""

from typing import List, Dict, Optional, Any
from pydantic import Field
from openenv.core import Action, Observation, State


class ClaimsAction(Action):
    """
    Agent actions for insurance claims processing.

    The agent can perform various actions to gather information and make decisions.
    Each action simulates real enterprise workflow steps.
    """
    action_type: str = Field(description="One of the valid action types")
    claim_id: str = Field(default="", description="Claim ID being processed")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")

    # Valid action types:
    # - "query_policy": Look up policy details (coverage, limits, status)
    # - "query_claim_history": Check claimant's past claims
    # - "check_fraud": Run fraud detection analysis
    # - "request_documents": Request supporting documents (photos, reports)
    # - "verify_coverage": Check if damage type is covered
    # - "calculate_payout": Calculate the payout amount
    # - "approve": Approve the claim with specified amount
    # - "deny": Deny the claim with reason
    # - "escalate": Escalate to senior adjuster


class ClaimsObservation(Observation):
    """
    What the agent observes after each action.

    Implements partial observability - agent doesn't see everything at once.
    Must query systems to reveal information progressively.
    """
    # Current claim summary
    claim_id: str = Field(default="", description="Claim identifier")
    claim_type: str = Field(default="", description="Type of claim")
    claim_amount_requested: float = Field(default=0.0, description="Amount claimed")
    claimant_name: str = Field(default="", description="Name of claimant")
    incident_date: str = Field(default="", description="Date of incident")
    description: str = Field(default="", description="Claim description")

    # System response from last action
    system_response: str = Field(default="", description="Response from last action")
    action_success: bool = Field(default=True, description="Whether last action succeeded")

    # Revealed information (grows as agent queries)
    revealed_info: Dict[str, Any] = Field(default_factory=dict, description="Information revealed so far")

    # Available actions based on current state
    available_actions: List[str] = Field(default_factory=list, description="Valid next actions")

    # Processing metrics
    time_elapsed_minutes: int = Field(default=0, description="Simulated processing time")
    queries_made: int = Field(default=0, description="Number of queries made")

    # Terminal state info
    is_terminal: bool = Field(default=False, description="Whether episode is done")
    terminal_reason: str = Field(default="", description="Why episode ended")


class ClaimsState(State):
    """
    Full episode state (includes hidden ground truth for reward calculation).

    This state is used server-side for reward computation.
    The agent only sees ClaimsObservation.
    """
    # Visible state
    claim_id: str = Field(default="", description="Claim identifier")
    claim_type: str = Field(default="", description="Type of claim")
    claim_amount_requested: float = Field(default=0.0, description="Amount claimed")

    # Hidden ground truth (agent must discover through queries)
    true_verdict: str = Field(default="", description="Correct decision")
    correct_payout: float = Field(default=0.0, description="Correct payout amount")
    is_fraud: bool = Field(default=False, description="Whether claim is fraudulent")
    fraud_type: Optional[str] = Field(default=None, description="Type of fraud if applicable")

    # Policy details (hidden until queried)
    policy_coverage_limit: float = Field(default=0.0, description="Max coverage amount")
    policy_deductible: float = Field(default=0.0, description="Deductible amount")
    policy_status: str = Field(default="", description="Policy status")
    coverage_exclusions: List[str] = Field(default_factory=list, description="Excluded coverage types")

    # Claim complexity
    complexity: str = Field(default="standard", description="Claim complexity level")
    requires_documents: List[str] = Field(default_factory=list, description="Required documents")
    requires_escalation: bool = Field(default=False, description="Whether escalation is needed")

    # Episode tracking
    actions_taken: int = Field(default=0, description="Number of actions taken")
    queries_made: int = Field(default=0, description="Number of queries made")
    time_elapsed_minutes: int = Field(default=0, description="Simulated time elapsed")

    # Revealed information tracker
    policy_queried: bool = Field(default=False, description="Policy info queried")
    history_queried: bool = Field(default=False, description="Claim history queried")
    fraud_checked: bool = Field(default=False, description="Fraud check done")
    documents_requested: bool = Field(default=False, description="Documents requested")
    coverage_verified: bool = Field(default=False, description="Coverage verified")
    payout_calculated: bool = Field(default=False, description="Payout calculated")

    # Final decision tracking
    agent_decision: str = Field(default="", description="Agent's decision")
    agent_payout: float = Field(default=0.0, description="Agent's payout amount")
    decision_reason: str = Field(default="", description="Reason for decision")

    # Reward components (for analysis)
    correctness_reward: float = Field(default=0.0, description="Reward for correct decision")
    efficiency_reward: float = Field(default=0.0, description="Reward for efficiency")
    fraud_detection_reward: float = Field(default=0.0, description="Reward for fraud detection")
    total_reward: float = Field(default=0.0, description="Total episode reward")
